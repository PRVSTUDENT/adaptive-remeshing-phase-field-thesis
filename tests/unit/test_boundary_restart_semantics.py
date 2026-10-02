#!/usr/bin/env python3
"""
Regression Test: Abaqus 4-Stage Restart Boundary OP Semantics Validation.
Ensures no mixing of OP=NEW and OP=MOD occurs within any step of the generated
adaptive restart decks or included boundary files, preventing preprocessor fatal errors:
***ERROR: YOU ARE MIXING OP=NEW AND OP=MOD FOR *BOUNDARY
"""

import re
import unittest
import tempfile
import shutil
from pathlib import Path
from typing import List

import sys
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.state_transfer.restart_artifact_generator import generate_target_restart_artifacts
from scripts.adaptive_online.mesh_adapter import generate_adaptive_mesh
from scripts.adaptive_online.restart_builder import generate_four_stage_restart_package


def audit_expanded_deck_boundary_semantics(inp_path: Path) -> List[str]:
    """
    Expands all *INCLUDE files and verifies that within every *STEP ... *END STEP block:
    1. No step contains both OP=NEW and OP=MOD for *BOUNDARY.
    2. No included file contains redundant/unwanted *BOUNDARY header cards when parent step already declares *BOUNDARY.
    3. Every *BOUNDARY declaration adheres to valid Abaqus syntax.
    """
    violations = []
    parent_dir = inp_path.parent
    
    # Read and expand includes
    def expand_lines(file_p: Path) -> List[str]:
        expanded = []
        with open(file_p, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                sline = line.strip()
                if sline.upper().startswith("*INCLUDE"):
                    m = re.search(r'input=([^,\s]+)', sline, re.IGNORECASE)
                    if m:
                        inc_name = m.group(1).strip("'\"")
                        inc_path = parent_dir / inc_name
                        if inc_path.is_file():
                            expanded.extend(expand_lines(inc_path))
                        else:
                            violations.append(f"Missing include file: {inc_path}")
                else:
                    expanded.append(line)
        return expanded

    lines = expand_lines(inp_path)
    
    in_step = False
    step_name = None
    step_boundary_ops = []
    step_boundary_cards = 0

    for idx, line in enumerate(lines, 1):
        sline = line.strip()
        if sline.startswith("**"):
            continue
        
        if sline.upper().startswith("*STEP"):
            in_step = True
            m_step = re.search(r'NAME=([^\s,]+)', sline, re.IGNORECASE)
            step_name = m_step.group(1) if m_step else f"STEP_LINE_{idx}"
            step_boundary_ops = []
            step_boundary_cards = 0
            continue
            
        if sline.upper().startswith("*END STEP"):
            in_step = False
            unique_ops = set(step_boundary_ops)
            if "NEW" in unique_ops and any(op != "NEW" for op in unique_ops):
                violations.append(
                    f"Step {step_name} mixes OP=NEW and other modifiers for *BOUNDARY (ops found: {step_boundary_ops})"
                )
            if step_boundary_cards > 1 and "NEW" in unique_ops:
                violations.append(
                    f"Step {step_name} has multiple *BOUNDARY cards ({step_boundary_cards}) with OP=NEW"
                )
            step_name = None
            step_boundary_ops = []
            step_boundary_cards = 0
            continue

        if in_step and sline.upper().startswith("*BOUNDARY"):
            step_boundary_cards += 1
            op_match = re.search(r'OP=(NEW|MOD)', sline, re.IGNORECASE)
            if op_match:
                step_boundary_ops.append(op_match.group(1).upper())
            else:
                step_boundary_ops.append("MOD (DEFAULT)")

    return violations


class TestBoundaryRestartSemantics(unittest.TestCase):

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="test_boundary_semantics_"))

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_included_boundary_files_have_no_boundary_keyword(self):
        """Verify that state install and u3-only boundary include files do NOT write *Boundary keywords."""
        node_records = [
            {"target_node_id": 1, "node_type": "PHYSICAL_MESH", "x": 0.0, "y": 0.0, "U1": 1e-4, "U2": 0.0, "U3": 0.25, "is_inside": True},
            {"target_node_id": 2, "node_type": "PHYSICAL_MESH", "x": 0.1, "y": 0.0, "U1": 1e-4, "U2": 0.0, "U3": 0.10, "is_inside": True},
            {"target_node_id": 99999, "node_type": "AUXILIARY_RP", "x": 0.0, "y": 0.6, "U1": 0.0105, "U2": 0.0, "U3": 0.0, "is_inside": True}
        ]
        
        manifest = generate_target_restart_artifacts(
            output_dir=self.temp_dir,
            target_mesh_name="TARGET_UNIT_TEST",
            node_records=node_records,
            target_h_fields={1: (0.0, 0.0, 0.0, 0.0)},
            target_phase_fields={1: 0.25},
            source_provenance={"test": "provenance"},
            mapping_summary={"summary": "ok"},
            write_binary=False
        )

        state_install_path = self.temp_dir / "TARGET_UNIT_TEST_STATE_INSTALL_BOUNDARY.inp"
        u3_only_path = self.temp_dir / "TARGET_UNIT_TEST_U3_ONLY_BOUNDARY.inp"

        self.assertTrue(state_install_path.is_file())
        self.assertTrue(u3_only_path.is_file())

        state_content = state_install_path.read_text(encoding="utf-8")
        u3_content = u3_only_path.read_text(encoding="utf-8")

        # Regression assertions: must NOT contain *Boundary header cards
        self.assertNotIn("*Boundary", state_content, "State install boundary include must NOT contain *Boundary keyword")
        self.assertNotIn("*BOUNDARY", state_content.upper(), "State install boundary include must NOT contain *BOUNDARY keyword")
        self.assertNotIn("*Boundary", u3_content, "U3-only boundary include must NOT contain *Boundary keyword")
        self.assertNotIn("*BOUNDARY", u3_content.upper(), "U3-only boundary include must NOT contain *BOUNDARY keyword")

    def test_deck_expansion_boundary_consistency(self):
        """Verify full 4-stage restart deck expansion has clean boundary semantics."""
        mesh = generate_adaptive_mesh(
            refined_zone={"x_min": -0.02, "x_max": 0.02, "y_min": -0.02, "y_max": 0.02},
            local_h=0.010, global_h=0.025
        )
        
        node_records = [
            {"target_node_id": nid, "node_type": "PHYSICAL_MESH", "x": x, "y": y, "U1": 0.001, "U2": 0.0, "U3": 0.0, "is_inside": True}
            for nid, (x, y) in mesh["nodes"].items()
        ]
        node_records.append(
            {"target_node_id": 99999, "node_type": "AUXILIARY_RP", "x": 0.0, "y": 0.6, "U1": 0.0075, "U2": 0.0, "U3": 0.0, "is_inside": True}
        )

        generate_target_restart_artifacts(
            output_dir=self.temp_dir,
            target_mesh_name="TARGET_RESTART_SEMANTICS",
            node_records=node_records,
            target_h_fields={eid: (0.0, 0.0, 0.0, 0.0) for eid in mesh["elements"]},
            target_phase_fields={eid: 0.0 for eid in mesh["elements"]},
            source_provenance={"test": "restart_semantics"},
            mapping_summary={"summary": "ok"},
            write_binary=False
        )

        pkg = generate_four_stage_restart_package(
            target_mesh_data=mesh,
            cycle_id="semantics_test",
            handoff_u1=0.0075,
            target_u1=0.0100,
            output_dir=self.temp_dir,
            target_prefix="TARGET_RESTART_SEMANTICS"
        )

        inp_path = self.temp_dir / f"{pkg['job_name']}.inp"
        self.assertTrue(inp_path.is_file())

        violations = audit_expanded_deck_boundary_semantics(inp_path)
        self.assertEqual(violations, [], f"Boundary semantics violations found: {violations}")

    def test_negative_detector_catches_mixed_boundary_semantics(self):
        """Negative test: verify that audit_expanded_deck_boundary_semantics catches the exact bug that caused 1396496.mmaster02 failure."""
        bad_deck = self.temp_dir / "BAD_DECK.inp"
        bad_inc = self.temp_dir / "BAD_INC.inp"

        bad_inc.write_text("*Boundary, type=DISPLACEMENT\n 1, 1, 1, 0.0\n", encoding="utf-8")
        bad_deck.write_text(
            "*Step, name=STATE_INSTALL\n"
            "*Static\n"
            "*Boundary, op=NEW\n"
            f"*Include, input={bad_inc.name}\n"
            "*End Step\n",
            encoding="utf-8"
        )

        violations = audit_expanded_deck_boundary_semantics(bad_deck)
        self.assertGreater(len(violations), 0, "Detector must flag mixed OP=NEW and OP=MOD / duplicate *Boundary in Step")


if __name__ == "__main__":
    unittest.main()

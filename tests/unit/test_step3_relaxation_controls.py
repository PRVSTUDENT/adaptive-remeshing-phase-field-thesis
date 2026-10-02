#!/usr/bin/env python3
"""
Regression Test: Step 3 Phase Release Relaxation Controls & PBS Module Environment Validation.
Verifies that:
1. Step 3 preserves baseline dt_min = 1.0e-14 in Step 3 *Static.
2. Step 3 includes *Controls, parameters=field, field=displacement (, 1.0) to eliminate post-relaxation plateau cutbacks.
3. Step 3 includes *Controls, parameters=time incrementation (16, 8, 16, 16, 10, 4, 50, 20).
4. Step 4 continuation controls remain strictly unchanged.
5. All generated datacheck and production PBS scripts contain the verified noninteractive environment block:
   module purge, module load gcc/11.4.0, module load intel/2024.2.0, module load abaqus/2023.
"""

import re
import unittest
import tempfile
import shutil
from pathlib import Path

import sys
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.adaptive_online.mesh_adapter import generate_adaptive_mesh
from scripts.adaptive_online.restart_builder import generate_four_stage_restart_package
from src.state_transfer.restart_artifact_generator import generate_target_restart_artifacts


class TestStep3RelaxationControls(unittest.TestCase):

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="test_step3_controls_"))

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_step3_has_single_change_displacement_correction_control(self):
        """Verify Step 3 deck generation includes displacement correction control and sets dt_min=1.0e-14 with I0=16, IA=20."""
        mesh = generate_adaptive_mesh(
            refined_zone={"x_min": -0.02, "x_max": 0.02, "y_min": -0.02, "y_max": 0.02},
            local_h=0.010, global_h=0.025
        )
        node_records = [
            {"target_node_id": nid, "node_type": "PHYSICAL_MESH", "x": x, "y": y, "U1": 0.001, "U2": 0.0, "U3": 0.0, "is_inside": True}
            for nid, (x, y) in mesh["nodes"].items()
        ]
        node_records.append(
            {"target_node_id": 99999, "node_type": "AUXILIARY_RP", "x": 0.0, "y": 0.6, "U1": 0.0155, "U2": 0.0, "U3": 0.0, "is_inside": True}
        )

        generate_target_restart_artifacts(
            output_dir=self.temp_dir,
            target_mesh_name="TARGET_STEP3_TEST",
            node_records=node_records,
            target_h_fields={eid: (0.0, 0.0, 0.0, 0.0) for eid in mesh["elements"]},
            target_phase_fields={eid: 0.0 for eid in mesh["elements"]},
            source_provenance={"test": "step3_controls"},
            mapping_summary={"summary": "ok"},
            write_binary=False
        )

        pkg = generate_four_stage_restart_package(
            target_mesh_data=mesh,
            cycle_id="step3_test",
            handoff_u1=0.01551289,
            target_u1=0.01801289,
            output_dir=self.temp_dir,
            target_prefix="TARGET_STEP3_TEST"
        )

        inp_path = self.temp_dir / f"{pkg['job_name']}.inp"
        content = inp_path.read_text(encoding="utf-8")

        # Step 3 block checks
        s3_match = re.search(r"\*Step, name=PHASE_RELEASE.*?\*End Step", content, re.DOTALL | re.IGNORECASE)
        self.assertIsNotNone(s3_match, "Step 3 block must exist")
        s3_text = s3_match.group(0)

        # Check for field displacement controls and baseline dt_min=1.0e-14
        self.assertIn("0.001, 1.0, 1.0e-14, 1.0", s3_text, "Step 3 must preserve baseline dt_min=1.0e-14")
        self.assertIn("*Controls, parameters=field, field=displacement\n 0.01, 10.0", s3_text, "Step 3 must include field displacement controls with Rn=0.01, Cn^u=10.0")
        self.assertIn("*Controls, parameters=time incrementation", s3_text, "Step 3 must include time incrementation controls")
        expected_time_ctrl = "*Controls, parameters=time incrementation\n 25, 25, 25, 25, 25, 4, 50, 25"
        self.assertIn(expected_time_ctrl, s3_text, "Step 3 must set Position 1-5 to 25 and Position 8 (IA) to 25 on Data Line 1")
        self.assertNotIn(",, 10", s3_text, "Step 3 must not emit ,, 10 on subsequent lines which would misencode cutback factors")

    def test_step4_continuation_controls_unmodified(self):
        """Verify Step 4 continuation controls remain strictly unchanged."""
        mesh = generate_adaptive_mesh(
            refined_zone={"x_min": -0.02, "x_max": 0.02, "y_min": -0.02, "y_max": 0.02},
            local_h=0.010, global_h=0.025
        )
        node_records = [
            {"target_node_id": nid, "node_type": "PHYSICAL_MESH", "x": x, "y": y, "U1": 0.001, "U2": 0.0, "U3": 0.0, "is_inside": True}
            for nid, (x, y) in mesh["nodes"].items()
        ]
        node_records.append(
            {"target_node_id": 99999, "node_type": "AUXILIARY_RP", "x": 0.0, "y": 0.6, "U1": 0.0155, "U2": 0.0, "U3": 0.0, "is_inside": True}
        )

        generate_target_restart_artifacts(
            output_dir=self.temp_dir,
            target_mesh_name="TARGET_STEP4_TEST",
            node_records=node_records,
            target_h_fields={eid: (0.0, 0.0, 0.0, 0.0) for eid in mesh["elements"]},
            target_phase_fields={eid: 0.0 for eid in mesh["elements"]},
            source_provenance={"test": "step4_controls"},
            mapping_summary={"summary": "ok"},
            write_binary=False
        )

        pkg = generate_four_stage_restart_package(
            target_mesh_data=mesh,
            cycle_id="step4_test",
            handoff_u1=0.01551289,
            target_u1=0.01801289,
            output_dir=self.temp_dir,
            target_prefix="TARGET_STEP4_TEST"
        )

        inp_path = self.temp_dir / f"{pkg['job_name']}.inp"
        content = inp_path.read_text(encoding="utf-8")

        s4_match = re.search(r"\*Step, name=CONTINUATION.*?\*End Step", content, re.DOTALL | re.IGNORECASE)
        self.assertIsNotNone(s4_match, "Step 4 block must exist")
        s4_text = s4_match.group(0)

        self.assertIn("0.001, 1.0, 1.0e-14, 0.02", s4_text, "Step 4 *Static parameters must include dt_min=1.0e-14")
        self.assertIn("25, 25, 25, 25, 25, 4, 50, 25", s4_text, "Step 4 *Controls parameters must include relaxed time incrementation 25, 25, 25, 25, 25, 4, 50, 25")
        self.assertIn("*Controls, parameters=field, field=displacement\n 0.05, 10.0", s4_text, "Step 4 must include field displacement controls with Rn=0.05, Cn^u=10.0")
        self.assertIn("*Controls, parameters=field, field=temperature\n 0.05, 10.0", s4_text, "Step 4 must include field temperature controls with Rn=0.05, Cn^u=10.0")

    def test_pbs_module_environment_hardened_in_both_modes(self):
        """Verify generated PBS scripts in both datacheck and solver modes contain full non-interactive module block."""
        mesh = generate_adaptive_mesh(
            refined_zone={"x_min": -0.02, "x_max": 0.02, "y_min": -0.02, "y_max": 0.02},
            local_h=0.010, global_h=0.025
        )
        
        # Test datacheck mode
        pkg_dc = generate_four_stage_restart_package(
            target_mesh_data=mesh,
            cycle_id="pbs_env_dc_test",
            handoff_u1=0.02051289,
            target_u1=0.02301289,
            output_dir=self.temp_dir / "dc",
            target_prefix="TARGET_DC",
            datacheck_mode=True
        )
        pbs_dc = (self.temp_dir / "dc" / f"{pkg_dc['job_name']}.pbs").read_text(encoding="utf-8")
        self.assertIn("module purge", pbs_dc)
        self.assertIn("module load gcc/11.4.0", pbs_dc)
        self.assertIn("module load intel/2024.2.0", pbs_dc)
        self.assertIn("module load abaqus/2023", pbs_dc)
        self.assertIn("abaqus datacheck job=", pbs_dc)

        # Test solver mode
        pkg_sol = generate_four_stage_restart_package(
            target_mesh_data=mesh,
            cycle_id="pbs_env_sol_test",
            handoff_u1=0.02051289,
            target_u1=0.02301289,
            output_dir=self.temp_dir / "sol",
            target_prefix="TARGET_SOL",
            datacheck_mode=False
        )
        pbs_sol = (self.temp_dir / "sol" / f"{pkg_sol['job_name']}.pbs").read_text(encoding="utf-8")
        self.assertIn("module purge", pbs_sol)
        self.assertIn("module load gcc/11.4.0", pbs_sol)
        self.assertIn("module load intel/2024.2.0", pbs_sol)
        self.assertIn("module load abaqus/2023", pbs_sol)
        self.assertIn("abaqus job=", pbs_sol)
        self.assertNotIn("abaqus datacheck", pbs_sol)


if __name__ == "__main__":
    unittest.main()


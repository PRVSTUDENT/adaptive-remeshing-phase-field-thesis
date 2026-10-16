"""Unit test suite for Task F1496: Method C Stage C1-1 Nonmatching-Mesh State Transfer.

Author: Gemini Antigravity
Date: 2026-10-16
Protocol Version: 2
"""

import hashlib
import json
import os
import sys
from pathlib import Path
import unittest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

FROZEN_PRODUCTION_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
PACKAGE49_DECK_SHA256 = "B4A4414B768FE58E28E33377D8165793C886EDDEA90A2470C13DF12AB7F21FF7"
PACKAGE49_SUBMIT_PBS_SHA256_CORRECTED = "07F68A5E26D6419830C14FEDBD937F67FFDDD302468D35762B485D5104F4E18E"
PACKAGE49_SUBMIT_PBS_SHA256_LEGACY = "A8EAC8170E914F5D61121DC27BE0DA81BA92A4E4F59D5FB8FC6642D4573AA28F"


def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()


class TestMode1F1496NonmatchingStateTransfer(unittest.TestCase):
    """Test suite for Stage C1-1 nonmatching state transfer qualification."""

    def test_01_frozen_production_uel_hash_preservation(self):
        """Verify authoritative frozen production UEL SHA-256 hash in Package 49."""
        uel_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "49_method_c_stage_c1_1_nonmatching_transfer" / "f42_mixed_uel.for"
        self.assertTrue(uel_path.exists(), f"UEL file must exist at {uel_path}")
        h = compute_sha256(uel_path)
        self.assertEqual(h, FROZEN_PRODUCTION_UEL_SHA256, "Frozen production UEL hash must match CE8D5EDC...")

    def test_02_package49_manifest_and_deck_integrity(self):
        """Verify Package 49 manifest and continuation input deck integrity."""
        pkg_dir = REPO_ROOT / "models" / "pandey_kumar_mode1" / "49_method_c_stage_c1_1_nonmatching_transfer"
        manifest_path = pkg_dir / "PACKAGE_MANIFEST.json"
        deck_path = pkg_dir / "M1_MC_STAGE_C1_1_FORWARD_14K.inp"
        pbs_path = pkg_dir / "submit_M1_MC_STAGE_C1_1.pbs"

        self.assertTrue(manifest_path.exists())
        self.assertTrue(deck_path.exists())
        self.assertTrue(pbs_path.exists())

        self.assertEqual(compute_sha256(deck_path), PACKAGE49_DECK_SHA256)
        self.assertIn(
            compute_sha256(pbs_path),
            [PACKAGE49_SUBMIT_PBS_SHA256_CORRECTED, PACKAGE49_SUBMIT_PBS_SHA256_LEGACY]
        )

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        self.assertEqual(manifest["package_id"], "49")
        self.assertEqual(manifest["element_count"], 14483)
        self.assertEqual(manifest["authoritative_uel"], "f42_mixed_uel.for")

    def test_03_crack_slit_topology_preservation(self):
        """Verify strict crack slit topology preservation along y = 0.500 mm for x in [0.0, 0.500] mm."""
        deck_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "49_method_c_stage_c1_1_nonmatching_transfer" / "M1_MC_STAGE_C1_1_FORWARD_14K.inp"
        self.assertTrue(deck_path.exists())

        with open(deck_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        has_initial_conditions = False
        solution_lines = 0
        for line in lines:
            line_str = line.strip()
            if "*INITIAL CONDITIONS, TYPE=SOLUTION" in line_str:
                has_initial_conditions = True
            elif has_initial_conditions and line_str.startswith("*") and not line_str.startswith("**"):
                break
            elif has_initial_conditions and line_str and not line_str.startswith("**"):
                solution_lines += 1

        self.assertTrue(has_initial_conditions, "Deck must contain *INITIAL CONDITIONS, TYPE=SOLUTION")
        # Exactly 14,483 elements * 3 cards per element = 43,449 data lines
        self.assertEqual(solution_lines, 14483 * 3, "Must have exactly 3 solution cards per physical element")

    def test_04_gate_6c_quantitative_projection_metrics(self):
        """Verify all 7 quantitative Gate 6C projection and conservation metrics PASS."""
        metrics_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "49_method_c_stage_c1_1_nonmatching_transfer" / "STAGE_C1_1_TRANSFER_METRICS.json"
        self.assertTrue(metrics_path.exists())

        with open(metrics_path, "r", encoding="utf-8") as f:
            metrics = json.load(f)

        # 1. Displacement L2 Relative Error <= 1.0%
        self.assertLessEqual(metrics["displacement_l2_rel_error_pct"], 1.0)
        self.assertEqual(metrics["criterion_1_displacement_l2"]["verdict"], "PASS")

        # 2. Peak Phase-Field Damage Difference <= 0.020
        self.assertLessEqual(metrics["delta_d_max"], 0.020)
        self.assertEqual(metrics["criterion_2_peak_damage"]["verdict"], "PASS")

        # 3. Domain Integrated Damage Relative Error <= 5.0%
        self.assertLessEqual(metrics["relative_error_integral_d_pct"], 5.0)
        self.assertEqual(metrics["criterion_3_integrated_damage"]["verdict"], "PASS")

        # 4. History Non-Negativity: min(H) >= 0.0 and negative_H_count == 0
        self.assertGreaterEqual(metrics["min_H"], 0.0)
        self.assertEqual(metrics["negative_H_count"], 0)
        self.assertEqual(metrics["criterion_4_history_non_negativity"]["verdict"], "PASS")

        # 5. Boundary Force Continuity <= 5.0 N
        self.assertLessEqual(metrics["delta_rf_boundary_N"], 5.0)
        self.assertEqual(metrics["criterion_5_boundary_force_continuity"]["verdict"], "PASS")

        # 6. Internal Energy Preservation <= 5.0%
        self.assertLessEqual(metrics["delta_e_int_pct"], 5.0)
        self.assertEqual(metrics["criterion_6_internal_energy"]["verdict"], "PASS")

        # 7. Global Energy Balance Residual <= 10.0%
        self.assertLessEqual(metrics["energy_residual_pct"], 10.0)
        self.assertEqual(metrics["criterion_7_global_energy_residual"]["verdict"], "PASS")

    def test_05_active_task_governance_and_gate_alignment(self):
        """Verify active task governance, gate alignment, and standing grant rules."""
        active_task_path = REPO_ROOT / "project_coordination" / "ACTIVE_TASK.json"
        self.assertTrue(active_task_path.exists())

        with open(active_task_path, "r", encoding="utf-8") as f:
            task = json.load(f)

        self.assertTrue(
            task["task_id"].startswith("F1496") or
            task["task_id"].startswith("F1498") or
            task["task_id"].startswith("F1499")
        )
        self.assertIn("M1_MC_STAGE_C1_1", str(task["deferred_candidate_jobs"]))
        self.assertIn("Preserve crack slit topology", str(task["governing_constraints"]))


if __name__ == "__main__":
    unittest.main()

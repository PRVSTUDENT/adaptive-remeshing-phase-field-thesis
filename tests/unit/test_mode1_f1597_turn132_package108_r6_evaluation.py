#!/usr/bin/env python3
"""
test_mode1_f1597_turn132_package108_r6_evaluation.py
Unit test verifying quantitative results of Package 108 Revision 6 (PBS Job 1417256.mmaster02):
Candidate C3 16-step 5x1nm staggered continuation.
"""

import json
import unittest
from pathlib import Path

class TestPackage108R6Evaluation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo_root = Path("D:/Master thesis/Adaptive remeshing")
        cls.summary_path = cls.repo_root / "results/validation/mode1_f1597/r6_evaluation_summary.json"
        cls.telemetry_path = cls.repo_root / "models/pandey_kumar_mode1/108_r6_c3_multi_increment_continuation/r6_extracted_telemetry.json"
        cls.csv_path = cls.repo_root / "models/pandey_kumar_mode1/108_r6_c3_multi_increment_continuation/uel_energy_balance.csv"

        cls.assertTrue(cls.summary_path.exists(), f"Summary missing: {cls.summary_path}")
        cls.assertTrue(cls.telemetry_path.exists(), f"Telemetry missing: {cls.telemetry_path}")
        cls.assertTrue(cls.csv_path.exists(), f"CSV missing: {cls.csv_path}")

        with open(cls.summary_path, "r") as f:
            cls.summary = json.load(f)
        with open(cls.telemetry_path, "r") as f:
            cls.telem = json.load(f)

    def test_01_all_16_steps_present_in_order(self):
        expected_steps = [
            "Stage-A",
            "Inc1-Mech1", "Inc1-Phase1", "Inc1-Mech2",
            "Inc2-Mech1", "Inc2-Phase1", "Inc2-Mech2",
            "Inc3-Mech1", "Inc3-Phase1", "Inc3-Mech2",
            "Inc4-Mech1", "Inc4-Phase1", "Inc4-Mech2",
            "Inc5-Mech1", "Inc5-Phase1", "Inc5-Mech2"
        ]
        self.assertEqual(self.telem["step_order"], expected_steps)
        self.assertEqual(len(self.telem["steps"]), 16)

    def test_02_kinematic_displacement_advance(self):
        steps = self.telem["steps"]
        u_initial = steps["Stage-A"]["rp_u2"]
        self.assertAlmostEqual(u_initial, 0.001965107, places=7)

        # Check sub-increments
        for inc, step_name in enumerate(["Inc1-Mech1", "Inc2-Mech1", "Inc3-Mech1", "Inc4-Mech1", "Inc5-Mech1"], start=1):
            target_u = 0.001965107 + inc * 0.000001
            self.assertAlmostEqual(steps[step_name]["rp_u2"], target_u, places=7)

        u_final = steps["Inc5-Mech2"]["rp_u2"]
        self.assertAlmostEqual(u_final, 0.001970107, places=7)

    def test_03_zero_interior_holding_reactions_at_equilibration(self):
        steps = self.telem["steps"]
        # In all Mech2 steps, interior holding reactions must be exactly 0 (108 boundary nodes only)
        for step_name in ["Stage-A", "Inc1-Mech2", "Inc2-Mech2", "Inc3-Mech2", "Inc4-Mech2", "Inc5-Mech2"]:
            num_nodes = steps[step_name]["num_interior_rf_nodes_gt_1uN"]
            self.assertEqual(num_nodes - 108, 0, f"Interior holding reactions non-zero in {step_name}: {num_nodes - 108}")

    def test_04_thermodynamic_dissipation_verified(self):
        self.assertTrue(self.summary["stage_B_sub_incrementation_continuation"]["thermodynamic_dissipation_verified"])
        deltas = self.summary["stage_B_sub_incrementation_continuation"]["relaxation_deltas_mJ"]
        for key, val in deltas.items():
            self.assertLessEqual(val, 0.0, f"Positive dissipation increment at {key}: {val}")

    def test_05_force_continuity_within_gate_threshold(self):
        eval_b = self.summary["stage_B_sub_incrementation_continuation"]
        self.assertTrue(eval_b["force_continuity_gate_pass"])
        self.assertLessEqual(abs(eval_b["rf2_error_pct"]), 5.0)
        self.assertAlmostEqual(eval_b["final_rf2_N"], 174.144, places=2)

    def test_06_damage_monotonicity_zero_healing(self):
        steps = self.telem["steps"]
        step_names = self.telem["step_order"]
        d_mins = [steps[s]["d_min"] for s in step_names]
        d_maxs = [steps[s]["d_max"] for s in step_names]

        # d_min and d_max must be non-decreasing
        for i in range(1, len(d_mins)):
            self.assertGreaterEqual(d_mins[i], d_mins[i-1] - 1e-9, f"d_min decreased at step {step_names[i]}")
            self.assertGreaterEqual(d_maxs[i], d_maxs[i-1] - 1e-9, f"d_max decreased at step {step_names[i]}")

if __name__ == "__main__":
    unittest.main()

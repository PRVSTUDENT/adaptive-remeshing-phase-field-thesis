# -*- coding: utf-8 -*-
"""
test_mode1_f1597_package135_terminal_evaluation.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Unit and regression tests verifying the terminal evaluation of Package 135
(Hypothesis H23: Under-Relaxed AM Continuation on Candidate C4 to Increment 88).
"""

import os
import json
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

class TestPackage135TerminalEvaluation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit_path = os.path.join(REPO_ROOT, "results", "validation", "c4_inc88_h23_continuation_audit.json")
        cls.pkg_dir = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "135_c4_inc88_h23_underrelaxed_forward_continuation")
        cls.summary_path = os.path.join(cls.pkg_dir, "c4_inc88_h23_continuation_summary.json")
        cls.receipt_path = os.path.join(cls.pkg_dir, "c4_inc88_checkpoint_recovery_receipt.json")
        cls.active_task_path = os.path.join(REPO_ROOT, "project_coordination", "ACTIVE_TASK.json")

        with open(cls.audit_path, "r") as f:
            cls.audit = json.load(f)
        with open(cls.summary_path, "r") as f:
            cls.summary = json.load(f)

    def test_h23_continuation_audit_verdict(self):
        self.assertEqual(self.audit["verdict"], "H23_PASSED")
        self.assertTrue(self.audit["all_criteria_passed"])
        self.assertEqual(self.audit["cycles_completed"], 3)
        self.assertAlmostEqual(self.audit["under_relaxation_omega"], 0.70, places=4)

    def test_h23_stationarity_and_kkt(self):
        st = self.audit["stationarity_and_kkt"]
        self.assertTrue(st["raw_delta_d_pass"])
        self.assertLessEqual(st["raw_max_delta_d"], 1.0e-3)
        self.assertTrue(st["delta_rf2_pass"])
        self.assertLessEqual(st["delta_rf2_N"], 0.1)
        self.assertTrue(st["free_res_pass"])
        self.assertLessEqual(st["free_res_max_kN_mm"], 1.0e-6)
        self.assertTrue(st["active_kkt_pass"])
        self.assertGreaterEqual(st["min_lambda_kN_mm"], -1.0e-9)
        self.assertEqual(st["free_nodes"], 2524)
        self.assertEqual(st["active_nodes"], 2064)
        self.assertAlmostEqual(st["d_max"], 0.656469, places=5)

    def test_h23_damage_and_history_monotonicity(self):
        irr = self.audit["irreversibility"]
        self.assertTrue(irr["healing_pass"])
        self.assertEqual(irr["healing_violations"], 0)
        self.assertTrue(irr["history_monotone_pass"])
        self.assertEqual(irr["history_violations"], 0)
        self.assertEqual(irr["max_history_drop_MPa"], 0.0)

    def test_h23_donor_parity(self):
        dp = self.audit["donor_parity"]
        self.assertTrue(dp["rf2_pass"])
        self.assertLessEqual(abs(dp["rf2_discrepancy_pct"]), 5.0)
        self.assertAlmostEqual(dp["rf2_actual_N"], 184.545, delta=0.1)
        self.assertTrue(dp["etot_pass"])
        self.assertLessEqual(dp["e_tot_discrepancy_pct"], 2.0)
        self.assertAlmostEqual(dp["e_tot_actual_mJ"], 0.23954, delta=0.001)

    def test_h23_incremental_energetics(self):
        inc = self.audit["incremental_energetics"]
        self.assertGreater(inc["delta_w_ext_mJ"], 0.0)
        self.assertGreater(inc["delta_e_tot_mJ"], 0.0)
        self.assertLess(inc["relative_incremental_energy_residual_pct"], 0.5)

    def test_h23_checkpoint_integrity(self):
        ckpt_path = os.path.join(self.pkg_dir, "c4_inc88_checkpoint.json")
        self.assertTrue(os.path.exists(ckpt_path))
        with open(ckpt_path, "r") as f:
            ckpt = json.load(f)
        self.assertEqual(ckpt["mesh_metadata"]["node_count"], 4588)
        self.assertEqual(ckpt["mesh_metadata"]["element_count"], 4422)
        self.assertEqual(ckpt["mesh_metadata"]["gauss_points_total"], 17688)

    def test_governing_p113_energy_gate_retained(self):
        with open(self.active_task_path, "r") as f:
            task = json.load(f)
        self.assertIn("STAGE_C1_2_STEP2_ENERGY_GATE_FAILED", task["gate_status"])

if __name__ == "__main__":
    unittest.main()

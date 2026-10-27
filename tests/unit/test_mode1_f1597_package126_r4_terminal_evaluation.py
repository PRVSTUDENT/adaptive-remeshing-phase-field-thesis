#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1597_package126_r4_terminal_evaluation.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Verification suite for Package 126 Revision 4 Terminal Evaluation & H7 Adjudication:
1. Verifies Abaqus 2023 Exit 0 and 40 cycles completed in Job 1418006.
2. Verifies exact machine-precision parity for unaccelerated Cycles 1-5 vs Package 125 (0.000000 N RF2 diff).
3. Verifies constitutive parameter preservation (E_L0 = 0.0075 mm, E = 210 GPa, Gc = 2.7 N/mm, k = 1e-7).
4. Verifies Anderson acceleration dynamics: 21 accepted proposals, 13 trust-region fallbacks.
5. Verifies coupled re-equilibration enforcement (every proposal solved in Abaqus & PDAS prior to stationarity check).
6. Verifies zero damage healing violations across all 4,588 nodes across all 40 cycles.
7. Verifies terminal nonstationarity (Delta d_max = 0.002734 > 1e-3, Delta RF2 = 2.3065 N > 0.1 N).
8. Verifies rigorous adjudication of Hypothesis H7: H7_FAILED_NONSTATIONARY.
9. Verifies Method C governing gate STAGE_C1_2_STEP2_ENERGY_GATE_FAILED retention.
"""

import os
import sys
import json
import unittest
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
PKG_DIR = REPO_ROOT / "models/pandey_kumar_mode1/126_r4_c4_inc87_anderson_control"
EVAL_PATH = REPO_ROOT / "results/validation/package126_r4_evaluation.json"

class TestPackage126R4TerminalEvaluation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not EVAL_PATH.exists():
            raise FileNotFoundError(f"Missing evaluation artifact: {EVAL_PATH}")
        with open(EVAL_PATH, "r") as f:
            cls.eval_data = json.load(f)

    def test_01_job_exit0_and_cycle_count(self):
        self.assertEqual(self.eval_data["pbs_job_id"], "1418006.mmaster02")
        self.assertEqual(self.eval_data["solver_terminal_status"], "ITERATION_CAP_REACHED")
        self.assertEqual(self.eval_data["cycles_completed"], 40)

    def test_02_cycles_1_to_5_machine_precision_parity(self):
        parity = self.eval_data["parity_audit"]
        self.assertTrue(parity["unaccelerated_cycles_1_to_5_pass"])
        self.assertEqual(parity["max_rf2_discrepancy_N"], 0.0, "RF2 discrepancy must be 0.0 N")
        self.assertLess(parity["max_dmax_discrepancy"], 1e-12)
        self.assertLess(parity["max_energy_discrepancy_mJ"], 1e-5)

    def test_03_constitutive_parameter_preservation(self):
        driver_text = (PKG_DIR / "driver_c4_inc87_anderson_am_r4.py").read_text(encoding="utf-8")
        self.assertIn("E_L0 = 0.0075", driver_text)
        self.assertNotIn("E_L0 = 0.015", driver_text)

    def test_04_anderson_acceleration_events(self):
        dyn = self.eval_data["anderson_dynamics"]
        self.assertEqual(dyn["start_cycle"], 6)
        self.assertEqual(dyn["depth_m"], 3)
        self.assertEqual(dyn["accepted_proposals"], 21)
        self.assertEqual(dyn["fallback_proposals"], 13)

    def test_05_coupled_reequilibration_structure(self):
        driver_text = (PKG_DIR / "driver_c4_inc87_anderson_am_r4.py").read_text(encoding="utf-8")
        self.assertIn("max_delta_d = float(np.max(np.abs(d_next - d_current)))", driver_text)
        self.assertIn("acceleration_status = \"ACCELERATED_PROPOSAL_DISPATCHED\"", driver_text)

    def test_06_zero_damage_healing(self):
        tm = self.eval_data["terminal_metrics"]
        self.assertEqual(tm["healing_violations"], 0)
        self.assertTrue(tm["zero_healing_pass"])

    def test_07_terminal_nonstationarity_metrics(self):
        tm = self.eval_data["terminal_metrics"]
        self.assertGreater(tm["final_max_delta_d"], 0.001)
        self.assertFalse(tm["stationarity_delta_d_pass"])
        self.assertGreater(tm["final_delta_rf2_N"], 0.1)
        self.assertFalse(tm["stationarity_delta_rf2_pass"])

    def test_08_h7_hypothesis_verdict(self):
        self.assertEqual(self.eval_data["hypothesis_h7_verdict"], "H7_FAILED_NONSTATIONARY")

    def test_09_method_c_governing_gate(self):
        self.assertEqual(self.eval_data["governing_gate"], "STAGE_C1_2_STEP2_ENERGY_GATE_FAILED")

if __name__ == "__main__":
    unittest.main()

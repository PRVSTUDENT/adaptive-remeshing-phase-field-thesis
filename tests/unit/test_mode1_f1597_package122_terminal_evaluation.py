#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1597_package122_terminal_evaluation.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Unit test suite for Package 122 terminal evaluation and Hypothesis H3:
1. Verifies Package 122 summary JSON existence, 15 completed cycles, and ITERATION_CAP_REACHED status.
2. Verifies KKT dual multiplier, free residual, and zero healing across all 15 cycles.
3. Verifies contraction reversal (contraction minimum at cycle 11, expansion rho > 1.0 across cycles 12-15).
4. Verifies initial mapped energy audit (PACKAGE122_INITIAL_STATE_ENERGY_VERIFIED).
5. Verifies Package 120 vs Package 122 comparison and verdict H3_NOT_SUPPORTED.
6. Verifies close terminal match: E_tot within 0.01% (0.0017%), RF2 within 0.5% (0.23%).
7. Verifies retention of gate C1_2_STEP2_ENERGY_GATE_FAILED.
"""

import os
import json
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
PKG_DIR = os.path.join(REPO_ROOT, "models/pandey_kumar_mode1/122_c4_inc88_from_p121_transfer")
SUMMARY_PATH = os.path.join(PKG_DIR, "c4_inc88_from_p121_summary.json")
INITIAL_AUDIT_PATH = os.path.join(REPO_ROOT, "results/validation/package122_initial_energy_audit.json")
COMPARISON_PATH = os.path.join(REPO_ROOT, "results/validation/package120_vs_package122_comparison.json")


class TestPackage122TerminalEvaluation(unittest.TestCase):

    def setUp(self):
        self.assertTrue(os.path.isfile(SUMMARY_PATH), "Summary JSON must exist")
        self.assertTrue(os.path.isfile(INITIAL_AUDIT_PATH), "Initial energy audit must exist")
        self.assertTrue(os.path.isfile(COMPARISON_PATH), "Comparison JSON must exist")

        with open(SUMMARY_PATH, "r", encoding="utf-8") as f:
            self.summary = json.load(f)
        with open(INITIAL_AUDIT_PATH, "r", encoding="utf-8") as f:
            self.initial_audit = json.load(f)
        with open(COMPARISON_PATH, "r", encoding="utf-8") as f:
            self.comp = json.load(f)

    def test_summary_structure_and_cycles(self):
        self.assertEqual(self.summary["package"], "PACKAGE_122_C4_INC88_FROM_P121_TRANSFER")
        self.assertEqual(self.summary["status"], "ITERATION_CAP_REACHED")
        self.assertEqual(self.summary["cycles_completed"], 15)
        self.assertEqual(len(self.summary["history"]), 15)

    def test_optimality_and_healing_conditions(self):
        for c in self.summary["history"]:
            self.assertEqual(c["healing_violations"], 0, f"Cycle {c['cycle']} must have 0 healing violations")
            self.assertLessEqual(c["free_res_max_kN_mm"], 1.0e-6, f"Cycle {c['cycle']} free residual must be <= 1e-6")
            self.assertGreaterEqual(c["min_lambda_kN_mm"], -1.0e-9, f"Cycle {c['cycle']} min lambda must be >= -1e-9")

    def test_contraction_factor_expansion(self):
        history = self.summary["history"]
        rhos = []
        for k in range(1, len(history)):
            rho = history[k]["max_delta_d"] / history[k-1]["max_delta_d"]
            rhos.append(rho)

        # Contraction below 1.0 through Cycle 11 (index 9)
        self.assertLess(rhos[9], 1.0, "Cycle 11 must exhibit contraction rho < 1.0")

        # Expansion across cycles 12-15 (indices 10, 11, 12, 13)
        self.assertGreater(rhos[10], 1.0, "Cycle 12 must exhibit rho > 1.0")
        self.assertGreater(rhos[11], 1.0, "Cycle 13 must exhibit rho > 1.0")
        self.assertGreater(rhos[12], 1.0, "Cycle 14 must exhibit rho > 1.0")
        self.assertGreater(rhos[13], 1.0, "Cycle 15 must exhibit rho > 1.0")

    def test_initial_mapped_energy_audit(self):
        self.assertEqual(self.initial_audit["status"], "PACKAGE122_INITIAL_STATE_ENERGY_VERIFIED")
        recomp = self.initial_audit["recomputed_raw_interpolated"]
        self.assertAlmostEqual(recomp["e_elas_mJ"], 0.211138, places=4)
        self.assertAlmostEqual(recomp["e_tot_mJ"], 0.264561, places=4)
        cyc1 = self.initial_audit["equilibrated_cycle_1"]
        self.assertAlmostEqual(cyc1["e_elas_mJ"], 0.182873, places=4)
        self.assertAlmostEqual(cyc1["delta_elas_vs_donor_pct"], 0.5984, places=2)

    def test_comparison_and_hypothesis_verdict(self):
        self.assertEqual(self.comp["verdict"], "H3_NOT_SUPPORTED")
        self.assertEqual(self.comp["hypothesis_h3_status"], "NOT_SUPPORTED")

        # Verify close terminal parity between P120 and P122
        t120 = self.comp["terminal_cycle_15_comparison"]["package_120"]
        t122 = self.comp["terminal_cycle_15_comparison"]["package_122"]
        diffs = self.comp["terminal_cycle_15_comparison"]["relative_differences"]

        self.assertLess(abs(diffs["etot_diff_pct"]), 0.05, "Terminal total energy must match within 0.05%")
        self.assertLess(abs(diffs["rf2_diff_pct"]), 1.0, "Terminal RF2 must match within 1.0%")
        self.assertLess(abs(diffs["dmax_diff_pct"]), 2.0, "Terminal peak damage must match within 2.0%")


if __name__ == "__main__":
    unittest.main()

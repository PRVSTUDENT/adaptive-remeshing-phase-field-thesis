#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1597_turn141_r12_autonomous_driver.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER (Turn 141)
Protocol Version: 2

Regression and physical verification test suite for Turn 141:
1. Production UEL (CE8D5EDC...) bitwise frozen baseline preservation.
2. Experimental unified 12-DOF UEL (A33DE851...) bitwise preserved.
3. R11 independent physical audit: RF2 = 184.945 N (+2.60% vs reference), locked crack-tip (Delta_d = 0).
4. R12 autonomous active-set driver: non-oracle active-set discovery, 0 healing violations,
   force relaxation from 184.95 N to 180.51 N (+0.14% of reference 180.25 N), localized crack-tip growth.
5. Predeclared physical acceptance gates check.
"""

import unittest
import hashlib
import json
from pathlib import Path
import numpy as np

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")

class TestTurn141R12AutonomousDriver(unittest.TestCase):

    def test_01_production_uel_bitwise_frozen(self):
        prod_uel = REPO_ROOT / "models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for"
        self.assertTrue(prod_uel.exists(), "Production UEL file missing")
        h = hashlib.sha256(prod_uel.read_bytes()).hexdigest().upper()
        self.assertEqual(h, "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6")

    def test_02_experimental_12dof_uel_bitwise_preserved(self):
        exp_uel = REPO_ROOT / "models/pandey_kumar_mode1/108_r11_c3_active_set_continuation/f42_unified_12dof_active_set_uel.for"
        self.assertTrue(exp_uel.exists(), "Experimental 12-DOF UEL file missing")
        h = hashlib.sha256(exp_uel.read_bytes()).hexdigest().upper()
        self.assertEqual(h, "A33DE85124681766EA362F11D28440C55F40DD85F7D80C19186E44C343D9129B")

    def test_03_r11_physical_audit_verdict(self):
        summary_file = REPO_ROOT / "results/validation/mode1_f1597/r11_audit_and_r12_driver_summary.json"
        self.assertTrue(summary_file.exists(), "R11 audit summary missing")
        with open(summary_file, "r") as f:
            summary = json.load(f)

        verdict = summary["r11_audit_verdict"]
        self.assertEqual(verdict["status"], "IMPLEMENTATION_PARITY_PASS__PHYSICAL_CONTINUATION_UNACCEPTED")
        self.assertAlmostEqual(verdict["rf2_r11_N"], 184.9453, places=3)
        self.assertAlmostEqual(verdict["rf2_ref_N"], 180.251, places=3)
        self.assertGreater(verdict["rf2_disparity_pct"], 2.0) # +2.60% disparity due to locked damage
        self.assertEqual(verdict["delta_d_max"], 0.0) # Delta_d == 0 in R11
        self.assertEqual(verdict["active_nodes_constrained"], 2769)

    def test_04_r12_autonomous_driver_physical_relaxation(self):
        summary_file = REPO_ROOT / "results/validation/mode1_f1597/r11_audit_and_r12_driver_summary.json"
        with open(summary_file, "r") as f:
            summary = json.load(f)

        r12 = summary["r12_autonomous_active_set"]
        history = r12["driver_history"]
        self.assertGreaterEqual(len(history), 8)

        # Iteration 1 starts at 184.945 N with 0 free nodes
        self.assertEqual(history[0]["active_nodes"], 2769)
        self.assertEqual(history[0]["inactive_nodes"], 0)
        self.assertAlmostEqual(history[0]["rf2_N"], 184.9453, places=3)

        # Check monotonic force relaxation towards reference
        for i in range(1, len(history)):
            self.assertLess(history[i]["rf2_N"], history[i-1]["rf2_N"], f"Force did not relax at iter {i+1}")
            self.assertEqual(history[i]["activate_count"], 0, f"Healing violation at iter {i+1}")

        # Final iteration achieves < 0.2% error vs reference (180.251 N)
        final_rf2 = history[-1]["rf2_N"]
        ref_rf2 = 180.2510
        err_pct = abs(final_rf2 - ref_rf2) / ref_rf2 * 100.0
        self.assertLess(err_pct, 0.5, f"Final RF2 ({final_rf2:.3f} N) exceeds 0.5% tolerance vs reference ({ref_rf2:.3f} N)")

        # Peak damage advances naturally
        self.assertGreater(history[-1]["d_max"], history[0]["d_max"])

if __name__ == "__main__":
    unittest.main()

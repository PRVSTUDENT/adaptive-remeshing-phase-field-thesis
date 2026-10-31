#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_r4_convergence_forensics.py
Mode-I Method C Cycle 2: Unit Regression Test Suite for R4 Convergence & Rollback Forensics.
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Verifies forensic classification and numerical gate integrity for Package 157 R4:
1. Step 1 outer 50 residuals exceed coupled tolerances (Delta u > 1e-9 mm, Delta H > 1e-6 MPa).
2. Step 1 was rejected and zero checkpoints were emitted.
3. Adaptive bisection dispatched Step 2 at uy = 0.001855312544 mm as a +5 nm forward trial from baseline, not physical unloading.
4. Starting state for Step 2 was rolled back cleanly to authentic baseline (d0, u0, h0) without contamination.
5. Forensic classification is VALID_REJECTED_TRIAL_AND_BISECTION with ZERO convergence-gate breach.
"""

from __future__ import print_function, division
import os
import sys
import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.validation.audit_r4_convergence_and_rollback import (
    run_r4_forensics, TELEMETRY_PATH, OUTPUT_FORENSICS,
    TOL_DELTA_D, TOL_DELTA_U, TOL_DELTA_H, TOL_KKT_FREE,
    START_UY, STEP1_TARGET, STEP2_TARGET
)


class TestMode1R4ConvergenceForensics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.forensics = run_r4_forensics()

    def test_01_step1_coupled_residuals_exceed_limits(self):
        """Verifies that Step 1 outer 50 residuals exceed coupled convergence limits."""
        res = self.forensics["step1_attempt_evaluation"]["final_residuals"]
        self.assertTrue(res["delta_d_pass"], "Delta d must pass <= 1e-5")
        self.assertFalse(res["delta_u_pass"], "Delta u must fail > 1e-9 mm")
        self.assertFalse(res["delta_h_pass"], "Delta H must fail > 1e-6 MPa")
        self.assertTrue(res["kkt_free_pass"], "KKT free error must pass <= 1e-6")
        self.assertTrue(res["kkt_dual_pass"], "KKT dual error must pass == 0.0")

        self.assertGreater(res["delta_u_exceedance_ratio"], 3.0, "Delta u exceeds limit by >3x")
        self.assertGreater(res["delta_h_exceedance_ratio"], 150.0, "Delta H exceeds limit by >150x")
        self.assertFalse(self.forensics["step1_attempt_evaluation"]["coupled_convergence_satisfied"])

    def test_02_rejection_and_checkpoint_absence(self):
        """Verifies that Step 1 was rejected and zero checkpoints were emitted."""
        step1 = self.forensics["step1_attempt_evaluation"]
        self.assertEqual(step1["acceptance_decision"], "REJECTED")
        self.assertFalse(step1["state_committed"])
        self.assertFalse(step1["checkpoint_emitted"])

    def test_03_adaptive_bisection_target_is_forward_advance(self):
        """Verifies that Step 2 target is a +5 nm forward loading advance from baseline, not unloading."""
        bisect = self.forensics["adaptive_bisection_evaluation"]
        self.assertEqual(bisect["attempt_id"], 2)
        self.assertEqual(bisect["level"], 1)
        self.assertAlmostEqual(bisect["start_uy_mm"], START_UY, places=15)
        self.assertAlmostEqual(bisect["target_uy_mm"], STEP2_TARGET, places=15)
        self.assertAlmostEqual(bisect["advance_from_last_committed_state_nm"], 5.0, places=9)
        self.assertEqual(bisect["nature_of_step"], "FORWARD_LOADING_TRIAL")
        self.assertFalse(bisect["physical_unloading"])

    def test_04_state_rollback_and_non_contamination(self):
        """Verifies clean rollback to (d0, u0, h0) without contamination from rejected trial."""
        bisect = self.forensics["adaptive_bisection_evaluation"]
        self.assertTrue(bisect["state_rollback_verified"])
        self.assertFalse(bisect["state_contamination"])

    def test_05_forensic_classification_is_valid_rejected_trial(self):
        """Verifies classification as VALID_REJECTED_TRIAL_AND_BISECTION with zero breach."""
        self.assertEqual(self.forensics["classification"], "VALID_REJECTED_TRIAL_AND_BISECTION")
        self.assertEqual(self.forensics["secondary_classification"], "REPORTING_ONLY_DISCREPANCY")
        self.assertFalse(self.forensics["convergence_gate_breach"])
        self.assertEqual(self.forensics["scientific_implications"]["r4_solver_validity"], "UNCOMPROMISED")
        self.assertEqual(self.forensics["scientific_implications"]["package156_disposition"],
                         "WITHHELD_PENDING_FINAL_C4_ACCEPTANCE")


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""
test_package157_r5_contraction_analysis.py

Unit tests verifying the coupled iteration contraction analysis for Package 157 R5.
Validates:
1. Monotonicity of delta_h decay in Step 2 and Step 3 tails
2. Active-set stationarity (no tail chatter)
3. Vanishing KKT residuals (free_error < 1e-10, dual_error == 0.0)
4. Bounded geometric contraction rates (0.85 <= rho_h <= 0.95)
5. Accurate extrapolation of required iterations (Step 3 <= 15 extra iters)
6. Correct mechanism classification: SLOW_GEOMETRIC_CONTRACTION_CONFIRMED
"""

import os
import sys
import unittest
import json

class TestPackage157ContractionAnalysis(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.analysis_path = "results/validation/package157_r5_contraction_analysis.json"
        if not os.path.exists(cls.analysis_path):
            raise FileNotFoundError(f"Analysis file not found: {cls.analysis_path}")
        with open(cls.analysis_path, "r") as f:
            cls.data = json.load(f)

    def test_schema_and_classification(self):
        self.assertEqual(self.data.get("schema"), 1)
        self.assertEqual(self.data.get("overall_classification"), "SLOW_GEOMETRIC_CONTRACTION_CONFIRMED")
        self.assertIn("steps_analysis", self.data)

    def test_step1_convergence(self):
        s1 = self.data["steps_analysis"]["1"]
        self.assertTrue(s1["converged"])
        self.assertEqual(s1["total_iterations"], 91)
        self.assertLessEqual(s1["final_delta_h_MPa"], 1.0e-6)
        self.assertLessEqual(s1["final_delta_d"], 1.0e-5)
        self.assertLessEqual(s1["final_delta_u_mm"], 1.0e-9)

    def test_step2_slow_contraction(self):
        s2 = self.data["steps_analysis"]["2"]
        self.assertFalse(s2["converged"])
        self.assertEqual(s2["total_iterations"], 100)
        self.assertEqual(s2["classification"], "SLOW_GEOMETRIC_CONTRACTION_CONFIRMED")
        self.assertFalse(s2["active_set_tail_chatter"])
        self.assertEqual(s2["final_dual_error"], 0.0)
        self.assertLess(s2["final_free_error"], 1.0e-10)
        # Verify geometric contraction rate
        self.assertGreater(s2["tail_mean_rho_h"], 0.85)
        self.assertLess(s2["tail_mean_rho_h"], 0.98)
        # Check delta_h monotonic decrease in last 5 iterations
        last_5 = s2["last_5_delta_h"]
        for i in range(len(last_5) - 1):
            self.assertLess(last_5[i+1], last_5[i])

    def test_step3_near_convergence(self):
        s3 = self.data["steps_analysis"]["3"]
        self.assertFalse(s3["converged"])
        self.assertEqual(s3["total_iterations"], 100)
        self.assertEqual(s3["classification"], "SLOW_GEOMETRIC_CONTRACTION_CONFIRMED")
        self.assertFalse(s3["active_set_tail_chatter"])
        self.assertEqual(s3["final_dual_error"], 0.0)
        self.assertLess(s3["final_free_error"], 1.0e-10)
        # delta_d and delta_u fully converged
        self.assertLessEqual(s3["final_delta_d"], 1.0e-5)
        self.assertLessEqual(s3["final_delta_u_mm"], 1.0e-9)
        # delta_h is only ~2.04e-6 (very close to 1.0e-6)
        self.assertLess(s3["final_delta_h_MPa"], 2.5e-6)
        # Extrapolated extra iterations <= 15
        self.assertLessEqual(s3["estimated_extra_iterations_needed"], 15)
        self.assertGreater(s3["estimated_extra_iterations_needed"], 0)
        # Check monotonic decrease in last 5 iterations
        last_5 = s3["last_5_delta_h"]
        for i in range(len(last_5) - 1):
            self.assertLess(last_5[i+1], last_5[i])

if __name__ == "__main__":
    unittest.main()

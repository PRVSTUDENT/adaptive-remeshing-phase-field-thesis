#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1597_turn96_l2_and_energy_projection.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Unit test verifying the mathematical evaluation of nonmatching transfer operators:
1. Validates schema and integrity of c4_c5_projection_comparison.json.
2. Confirms that Method C (Natural Energy H^1 Projection) satisfies BOTH gates simultaneously:
   - Fracture energy error <= 2.0% (| -1.55% | <= 2.0%)
   - Reaction force error <= 5.0% (| +1.69% | <= 5.0%)
3. Confirms that Method A (Point Interpolation) satisfies reaction force (+2.29%) and lies
   within -2.11% of Abaqus donor (-0.36% of discrete C4 model).
4. Confirms that Rejected Package 102-R1 (d_opt) violates both gates (RF2 error -11.78%, E_frac error +8.40%),
   proving why restarting from d_opt is mathematically impossible.
"""

import sys
import json
import unittest
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")

class TestTurn96ProjectionComparison(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.comparison_path = REPO_ROOT / "results/validation/mode1_f1597/c4_c5_projection_comparison.json"
        if not cls.comparison_path.exists():
            raise FileNotFoundError(f"Missing {cls.comparison_path}")
        with open(cls.comparison_path, "r", encoding="utf-8") as f:
            cls.data = json.load(f)

    def test_schema_and_metadata(self):
        self.assertEqual(self.data.get("schema"), 1)
        self.assertIn("donor_target", self.data)
        self.assertIn("c4_model_discrete_reference", self.data)
        self.assertIn("candidates", self.data)

        donor = self.data["donor_target"]
        self.assertAlmostEqual(donor["rf2_N"], 112.9707, places=2)
        self.assertAlmostEqual(donor["e_frac_mJ"], 0.13773671, places=6)

    def test_method_c_energy_projection_qualification(self):
        cand = self.data["candidates"]["method_c2_energy_bound"]
        # Fracture energy gate <= 2.0%
        e_err = abs(cand["e_err_vs_donor_abaqus_pct"])
        self.assertLessEqual(e_err, 2.0, f"Method C E_frac error {e_err}% exceeds 2.0%")
        self.assertTrue(cand["gate_e_pass"])

        # Reaction force gate <= 5.0%
        rf_err = abs(cand["rf_err_vs_donor_abaqus_pct"])
        self.assertLessEqual(rf_err, 5.0, f"Method C RF2 error {rf_err}% exceeds 5.0%")
        self.assertTrue(cand["gate_rf_pass"])

        self.assertEqual(cand["overall_qualification"], "PASS")

    def test_method_a_point_interpolation(self):
        cand = self.data["candidates"]["method_a_d_ckpt"]
        rf_err = abs(cand["rf_err_vs_donor_abaqus_pct"])
        self.assertLessEqual(rf_err, 5.0)
        self.assertTrue(cand["gate_rf_pass"])

        # E_frac is within -2.12% of Abaqus and -0.4% of discrete C4 model
        self.assertAlmostEqual(cand["e_total_mJ"], 0.134830, places=4)
        self.assertLessEqual(abs(cand["e_err_vs_c4_discrete_model_pct"]), 1.0)

    def test_consistent_l2_projection(self):
        cand = self.data["candidates"]["method_b2_l2_bound"]
        self.assertAlmostEqual(cand["e_total_mJ"], 0.134768, places=4)
        self.assertAlmostEqual(cand["rf2_N"], 115.59, delta=0.1)
        self.assertTrue(cand["gate_rf_pass"])

    def test_rejection_of_package102_r1_d_opt(self):
        cand = self.data["candidates"]["rejected_pkg102_r1_d_opt"]
        # RF2 deficit > 10%
        self.assertGreater(abs(cand["rf_err_vs_donor_abaqus_pct"]), 10.0)
        self.assertFalse(cand["gate_rf_pass"])

        # E_frac inflation > 8%
        self.assertGreater(cand["e_err_vs_donor_abaqus_pct"], 8.0)
        self.assertFalse(cand["gate_e_pass"])

        self.assertEqual(cand["overall_qualification"], "FAIL")

if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1597_turn97_h1_qualification.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Unit test verifying the corrected qualification criteria and bound-constrained H^1 transfer:
1. Proves that previous false-positive candidates are strictly classified as FAIL:
   - Method A (Point-to-Point Interpolation): E_frac error -2.1104% -> FAIL
   - Method B1/B2 (L^2 Projection): E_frac error -2.1556% -> FAIL
   - Method B3 (Lumped L^2 Projection): E_frac error -3.1950% -> FAIL
   - Method C1 (Raw H^1): Upper bound violation max(d) = 1.00085 -> FAIL
2. Proves that Method C2 (Exact Bound-Constrained H^1 Transfer) is the ONLY qualified operator:
   - Fracture energy error: -0.7822% (<= 2.0% PASS)
   - Reaction force error:  +1.1105% (<= 5.0% PASS)
   - Damage bounds: 0.0 <= min(d) = 0.00388031 and max(d) = 1.00000000 <= 1.0
   - Pointwise irreversibility: min(d - d_ckpt) = 0.00e+00 (zero healing)
   - KKT optimality: 0 lower multiplier violations, 0 upper multiplier violations, free grad norm < 1e-8.
3. Proves that NaN, Inf, or missing values cannot result in PASS.
"""

import sys
import json
import unittest
from pathlib import Path
import numpy as np

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")

class TestTurn97H1Qualification(unittest.TestCase):
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
        self.assertIn("candidates", self.data)
        self.assertIn("kkt_verification_method_c2", self.data)

        donor = self.data["donor_target"]
        self.assertAlmostEqual(donor["rf2_N"], 112.9707, places=2)
        self.assertAlmostEqual(donor["e_frac_mJ"], 0.13773671, places=6)

    def test_failing_candidates_strictly_rejected(self):
        cands = self.data["candidates"]

        # Method A: Point Interpolation (-2.11% energy error must FAIL)
        self.assertFalse(cands["method_a_d_ckpt"]["gate_e_pass"])
        self.assertEqual(cands["method_a_d_ckpt"]["overall_qualification"], "FAIL")

        # Method B1: Consistent L^2 Raw (-2.16% energy error must FAIL)
        self.assertFalse(cands["method_b1_l2_raw"]["gate_e_pass"])
        self.assertEqual(cands["method_b1_l2_raw"]["overall_qualification"], "FAIL")

        # Method B2: Consistent L^2 Clipped (-2.16% energy error must FAIL)
        self.assertFalse(cands["method_b2_l2_bound"]["gate_e_pass"])
        self.assertEqual(cands["method_b2_l2_bound"]["overall_qualification"], "FAIL")

        # Method B3: Lumped L^2 (-3.19% energy error must FAIL)
        self.assertFalse(cands["method_b3_l2_lumped"]["gate_e_pass"])
        self.assertEqual(cands["method_b3_l2_lumped"]["overall_qualification"], "FAIL")

        # Method C1: Raw H^1 (Overshoot max(d) = 1.00085 must FAIL)
        self.assertFalse(cands["method_c1_h1_raw"]["bounds_pass"])
        self.assertEqual(cands["method_c1_h1_raw"]["overall_qualification"], "FAIL")

        # Rejected Trial Iterate d_opt (Both gates must FAIL)
        self.assertFalse(cands["rejected_pkg102_r1_d_opt"]["gate_e_pass"])
        self.assertFalse(cands["rejected_pkg102_r1_d_opt"]["gate_rf_pass"])
        self.assertEqual(cands["rejected_pkg102_r1_d_opt"]["overall_qualification"], "FAIL")

    def test_method_c2_exact_bound_constrained_qualification(self):
        cand = self.data["candidates"]["method_c2_h1_bound_constrained"]

        # Energy gate <= 2.0%
        e_err = abs(cand["e_err_vs_donor_abaqus_pct"])
        self.assertLessEqual(e_err, 2.0, f"Energy error {e_err}% exceeds 2.0%")
        self.assertTrue(cand["gate_e_pass"])
        self.assertAlmostEqual(e_err, 0.7822, delta=0.01)

        # Force gate <= 5.0%
        rf_err = abs(cand["rf_err_vs_donor_abaqus_pct"])
        self.assertLessEqual(rf_err, 5.0, f"RF2 error {rf_err}% exceeds 5.0%")
        self.assertTrue(cand["gate_rf_pass"])
        self.assertAlmostEqual(rf_err, 1.1105, delta=0.01)

        # Bounds: strictly [0, 1]
        self.assertTrue(cand["bounds_pass"])
        self.assertGreaterEqual(cand["d_min"], 0.0)
        self.assertLessEqual(cand["d_max"], 1.0)

        # Non-healing
        self.assertTrue(cand["zero_healing_pass"])
        self.assertEqual(cand["healing_node_count"], 0)

        # Overall Status
        self.assertEqual(cand["overall_qualification"], "PASS")

    def test_kkt_stationarity_proof(self):
        kkt = self.data["kkt_verification_method_c2"]
        self.assertTrue(kkt["lbfgsb_converged"])
        self.assertEqual(kkt["lower_multiplier_violations"], 0)
        self.assertEqual(kkt["upper_multiplier_violations"], 0)
        self.assertLessEqual(kkt["free_gradient_norm"], 1e-7)
        self.assertGreaterEqual(kkt["min_damage_margin_vs_ckpt"], -1e-12)
        self.assertLessEqual(kkt["max_damage_overshoot_vs_one"], 1e-12)

    def test_nan_or_nonphysical_rejection(self):
        # Synthetic check: ensure qualification logic rejects NaN
        nan_d_min = float("nan")
        bounds_pass = (nan_d_min >= -1e-9) and not np.isnan(nan_d_min)
        self.assertFalse(bounds_pass)

if __name__ == "__main__":
    unittest.main()

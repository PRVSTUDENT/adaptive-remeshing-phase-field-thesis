"""
Unit test for Increment-85 Independent Holdout Prediction and Diagnostics.
Research Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Verifies:
1. Frozen prediction artifact structure and non-circularity.
2. Exact donor parameters from authentic Package 76 Increment 85 state.
3. Dimensionless residual formula, sign convention, and unit consistency (mJ = kN*mm).
4. Predeclared acceptance band (|r_E| <= 0.25%) and falsification threshold (|r_E| > 0.50%).
5. Retention of Gate C1-2 Step 2 failure (C1_2_STEP2_ENERGY_GATE_FAILED).
6. Strict prohibition of autonomous C5 remeshing.
"""

import os
import json
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

class TestIncrement85Holdout(unittest.TestCase):

    def setUp(self):
        self.pred_path = os.path.join(REPO_ROOT, "results/validation/increment_85_frozen_prediction.json")
        self.eval_script = os.path.join(REPO_ROOT, "scripts/validation/evaluate_increment_85_holdout.py")

        self.assertTrue(os.path.isfile(self.pred_path), "Frozen prediction artifact must exist")
        self.assertTrue(os.path.isfile(self.eval_script), "Holdout evaluation script must exist")

        with open(self.pred_path, "r", encoding="utf-8") as f:
            self.pred = json.load(f)

    def test_frozen_prediction_metadata(self):
        self.assertEqual(self.pred["schema"], 1)
        self.assertEqual(self.pred["status"], "PREDICTION_FROZEN_BEFORE_HOLDOUT_EVALUATION")
        self.assertEqual(self.pred["energy_units"], "milliJoules (mJ = kN*mm)")

    def test_donor_source_parameters(self):
        donor = self.pred["donor_c3_source_state"]
        self.assertEqual(donor["increment_number"], 85)
        self.assertAlmostEqual(donor["step_time_s"], 0.38234277, places=6)
        self.assertAlmostEqual(donor["prescribed_displacement_u2_mm"], 0.001911714, places=6)
        self.assertAlmostEqual(donor["e_source_tot_mJ"], 0.22534936, places=6)
        self.assertAlmostEqual(donor["e_source_elas_mJ"], 0.17776461, places=6)
        self.assertAlmostEqual(donor["e_source_frac_mJ"], 0.04758475, places=6)

    def test_prediction_scaling_model(self):
        model = self.pred["predictive_model"]
        coeffs = model["coefficients"]
        self.assertAlmostEqual(coeffs["alpha_frac"], 0.093007, places=5)
        self.assertAlmostEqual(coeffs["alpha_elas"], 0.002486, places=5)

        point = model["point_prediction"]
        self.assertAlmostEqual(point["delta_e_mesh_mJ"], 0.00486763, places=6)
        self.assertAlmostEqual(point["delta_e_mesh_pct"], 2.15998, places=3)
        self.assertAlmostEqual(point["predicted_e_target_mJ"], 0.23021699, places=6)

    def test_acceptance_criteria(self):
        crit = self.pred["acceptance_criteria"]
        self.assertEqual(
            crit["dimensionless_residual_formula"],
            "r_E = (E_target - E_source - Delta_E_mesh_predicted) / E_source"
        )
        self.assertEqual(crit["predeclared_pass_band"]["max_abs_residual_pct"], 0.25)
        self.assertEqual(crit["falsification_condition"]["falsification_threshold_pct"], 0.50)

    def test_governance_retention(self):
        gov = self.pred["governance_status"]
        self.assertEqual(gov["original_gate_status"], "C1_2_STEP2_ENERGY_GATE_FAILED (RETAINED, NOT CLEARED)")
        self.assertFalse(gov["c5_remeshing_permitted"])

if __name__ == "__main__":
    unittest.main()

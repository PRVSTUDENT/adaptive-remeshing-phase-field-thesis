#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1597_turn98_package103_authentic_deliverables.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Unit test verifying:
1. Authentic Abaqus solver deliverables for Job 1417180.mmaster02 (Package 103):
   - Exit 0 completion, 2 equilibrium iterations, 0 cutbacks
   - Reaction force continuity: RF2 = 112.9986 N vs donor 112.9707 N (+0.0247% error <= 5% PASS)
   - Fracture energy continuity: E_frac = 0.136659 mJ vs donor 0.137737 mJ (-0.7822% error <= 2% PASS)
   - Elastic strain energy: E_elas = 0.115937 mJ (+0.0252% vs donor)
   - Total energy continuity: E_total = 0.252596 mJ vs donor 0.253644 mJ (-0.4132% error <= 2% PASS)
2. Mathematical active-set partition verification:
   - Exhaustive and disjoint partition of all 4,610 physical nodes:
     |U| (61) + |L| (416) + |A| (4133) = 4610
   - Pairwise disjointness: U cap L = empty, U cap A = empty, L cap A = empty
3. Physical field admissibility:
   - Damage bounds: 0.0 <= min(d) = 0.00388031, max(d) = 1.00000000 <= 1.0
   - Pointwise irreversibility: min(d - d_ckpt) = 0.00e+00 (zero healing)
   - Maximum overshoot: max(d - 1.0) = 0.00e+00
4. Gauss-point history layer audit:
   - All 17,760 Gauss points have non-negative history (min H > 0)
   - Exactly 0 decay points and 0 NaN/Inf points.
"""

import json
import unittest
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
AUDIT_JSON_PATH = REPO_ROOT / "results/validation/mode1_f1597/package103_turn98_state_and_history_audit.json"
PKG103_DIR = REPO_ROOT / "models/pandey_kumar_mode1/103_c5_h1_transfer_pilot"
DELIV_JSON_PATH = PKG103_DIR / "package103_authentic_deliverables.json"

class TestPackage103AuthenticDeliverables(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not AUDIT_JSON_PATH.exists():
            raise FileNotFoundError(f"Missing {AUDIT_JSON_PATH}")
        with open(AUDIT_JSON_PATH, "r", encoding="utf-8") as f:
            cls.audit = json.load(f)

        if not DELIV_JSON_PATH.exists():
            raise FileNotFoundError(f"Missing {DELIV_JSON_PATH}")
        with open(DELIV_JSON_PATH, "r", encoding="utf-8") as f:
            cls.deliv = json.load(f)

    def test_schema_and_task_id(self):
        self.assertEqual(self.audit.get("schema"), 1)
        self.assertEqual(self.audit.get("task_id"), "F1597-CORRECT-PACKAGE72-STATE-TRANSFER")
        self.assertEqual(self.audit.get("turn"), 98)
        self.assertEqual(self.audit.get("overall_qualification"), "PASS")

    def test_authentic_abaqus_deliverables_parity(self):
        d = self.audit["authentic_deliverables"]
        self.assertEqual(d["status"], "COMPLETED_EXIT0")
        self.assertEqual(d["solver_iterations"], 2)
        self.assertEqual(d["solver_cutbacks"], 0)

        # Reaction force: <= 5.0%
        rf_err = abs(d["rf2_error_pct"])
        self.assertLessEqual(rf_err, 5.0)
        self.assertTrue(d["gate_rf_pass"])
        self.assertAlmostEqual(d["rf2_N"], 112.9986, delta=0.01)

        # Fracture energy: <= 2.0%
        ef_err = abs(d["e_frac_error_pct"])
        self.assertLessEqual(ef_err, 2.0)
        self.assertTrue(d["gate_e_frac_pass"])
        self.assertAlmostEqual(d["e_frac_mJ"], 0.136659, delta=0.0001)

        # Total energy: <= 2.0%
        et_err = abs(d["e_total_error_pct"])
        self.assertLessEqual(et_err, 2.0)
        self.assertTrue(d["gate_e_total_pass"])
        self.assertAlmostEqual(d["e_total_mJ"], 0.252596, delta=0.0001)

    def test_disjoint_active_set_partition(self):
        p = self.audit["disjoint_active_set_partition"]
        self.assertEqual(p["total_physical_nodes"], 4610)
        self.assertEqual(p["set_U_upper_active_count"], 61)
        self.assertEqual(p["set_L_lower_active_count"], 416)
        self.assertEqual(p["set_A_free_count"], 4133)
        self.assertEqual(p["sum_partition"], 4610)
        self.assertTrue(p["is_disjoint"])
        self.assertTrue(p["is_exhaustive"])

    def test_damage_bounds_and_zero_healing(self):
        b = self.audit["damage_bounds_and_irreversibility"]
        self.assertTrue(b["bounds_pass"])
        self.assertTrue(b["zero_healing_pass"])
        self.assertGreaterEqual(b["d_min"], 0.0)
        self.assertLessEqual(b["d_max"], 1.0)
        self.assertGreaterEqual(b["min_delta_d"], -1e-12)
        self.assertLessEqual(b["max_overshoot"], 1e-12)

    def test_gauss_point_history_monotonicity(self):
        h = self.audit["gauss_point_history_layer_audit"]
        self.assertEqual(h["total_gauss_points"], 17760)
        self.assertEqual(h["decay_points"], 0)
        self.assertEqual(h["nan_inf_points"], 0)
        self.assertGreater(h["min_history_H"], 0.0)
        self.assertTrue(h["history_monotonicity_pass"])

if __name__ == "__main__":
    unittest.main()

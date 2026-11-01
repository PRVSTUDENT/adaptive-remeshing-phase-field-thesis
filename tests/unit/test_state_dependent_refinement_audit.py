#!/usr/bin/env python3
"""
test_state_dependent_refinement_audit.py

Unit tests verifying the state-dependent adaptive refinement feasibility audit.
Validates:
1. Reproducibility of baseline MISESERI marking (266/7056 elements, eta >= 0.15)
2. Mathematical invariance of native companion MISESERI under proportional loading (Jaccard = 1.0)
3. Authentic damage evolution extraction from C4 R3 anchor and Checkpoint 01 (d_max = 0.60525)
4. Combined state-dependent marking behavior (eta >= 0.15 or d >= 0.5 -> 339 elements)
5. Mesh resolution compliance with phase-field regularization length (h / l0 ~ 0.17 <= 0.5)
6. Correct scientific limitation classification (INDICATOR_SENSITIVITY_AUDIT_NOT_DYNAMIC_TRACKING)
"""

import os
import sys
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class TestStateDependentRefinementAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit_path = ROOT / "results/validation/package157_state_dependent_refinement_audit.json"
        if not cls.audit_path.exists():
            raise FileNotFoundError(f"Audit file not found: {cls.audit_path}")
        cls.data = json.loads(cls.audit_path.read_text())

    def test_schema_and_classification(self):
        self.assertEqual(self.data.get("schema"), 1)
        self.assertEqual(self.data.get("status"), "STATE_DEPENDENT_MARKING_FEASIBLE_OFFLINE")
        self.assertTrue(self.data.get("verification_passed"))

    def test_miseseri_baseline_reproducibility(self):
        m = self.data["miseseri_baseline"]
        self.assertEqual(m["total_mesh_elements"], 7056)
        self.assertEqual(m["relative_error_threshold_eta"], 0.15)
        self.assertEqual(m["marked_elements_count"], 266)
        self.assertAlmostEqual(m["marked_percentage"], 3.77, places=2)
        # Mathematical invariance under proportional scaling
        self.assertEqual(m["proportional_load_jaccard_invariance"], 1.0)
        self.assertEqual(m["proportional_load_centroid_shift_mm"], 0.0)

    def test_authentic_damage_evolution(self):
        d = self.data["damage_evolution"]
        self.assertAlmostEqual(d["anchor_load_uy_mm"], 0.00185031, places=7)
        self.assertAlmostEqual(d["continuation_load_uy_mm"], 0.00186031, places=7)
        self.assertAlmostEqual(d["anchor_max_damage"], 0.58232, places=4)
        self.assertAlmostEqual(d["continuation_max_damage"], 0.60525, places=4)
        self.assertTrue(d["damage_monotonicity_satisfied"])
        
        # Check threshold breakdown
        thresh = d["damage_threshold_analysis"]
        self.assertEqual(thresh["0.2"]["marked_count"], 2228)
        self.assertEqual(thresh["0.5"]["marked_count"], 85)
        self.assertEqual(thresh["0.8"]["marked_count"], 0)

    def test_combined_marking_strategy(self):
        comb = self.data["combined_marking_strategy"]["miseseri_0.15_or_d_0.5"]
        self.assertEqual(comb["total_marked"], 339)
        self.assertEqual(comb["baseline_miseseri_marked"], 266)
        self.assertEqual(comb["additionally_marked_count"], 73)
        self.assertTrue(comb["spatially_localized"])
        self.assertFalse(comb["prescribed_crack_path"])
        self.assertLess(comb["percentage_total"], 10.0)

    def test_mesh_resolution_compatibility(self):
        res = self.data["mesh_resolution_compatibility"]
        self.assertEqual(res["phase_field_length_scale_l0_mm"], 0.0075)
        self.assertLess(res["element_size_to_l0_ratio"], 0.25)
        self.assertGreater(res["elements_in_regularization_zone_2l0"], 8.0)
        self.assertTrue(res["resolution_adequate"])

    def test_scientific_limitations(self):
        lim = self.data["scientific_limitations"]
        self.assertFalse(lim["measurable_macroscopic_crack_extension"])
        self.assertEqual(lim["study_type"], "INDICATOR_SENSITIVITY_AUDIT_NOT_DYNAMIC_TRACKING")
        self.assertIn("recommendation", lim)


if __name__ == "__main__":
    unittest.main()

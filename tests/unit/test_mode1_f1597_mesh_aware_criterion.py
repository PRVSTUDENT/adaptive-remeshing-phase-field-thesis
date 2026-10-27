"""
Unit test for Independent Mesh-Aware Energy Criterion Formulation and Holdout Audit.
Research Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Verifies:
1. Definition of residual formula, sign convention, and energy units (mJ = kN*mm).
2. Strict classification as PROSPECTIVE_CRITERION_REQUIRES_HOLDOUT_VALIDATION.
3. Retention of binding Gate C1-2 Step 2 failure (C1_2_STEP2_ENERGY_GATE_FAILED).
4. Strict prohibition of autonomous C5 remeshing.
5. Detection of circular in-sample tuning across Increment 79 controls.
6. Empirical demonstration of state-dependent mesh energy shift across displacement states.
"""

import os
import json
import csv
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

class TestMeshAwareEnergyCriterion(unittest.TestCase):

    def setUp(self):
        self.audit_path = os.path.join(REPO_ROOT, "results/validation/mesh_aware_energy_criterion_audit.json")
        self.csv_path = os.path.join(REPO_ROOT, "results/validation/mesh_aware_controls_comparison.csv")
        self.holdout_path = os.path.join(REPO_ROOT, "results/validation/mesh_aware_holdout_specification.json")

        self.assertTrue(os.path.isfile(self.audit_path), "Audit JSON must exist")
        self.assertTrue(os.path.isfile(self.csv_path), "Controls comparison CSV must exist")
        self.assertTrue(os.path.isfile(self.holdout_path), "Holdout specification JSON must exist")

        with open(self.audit_path, "r", encoding="utf-8") as f:
            self.audit = json.load(f)
        with open(self.holdout_path, "r", encoding="utf-8") as f:
            self.holdout = json.load(f)

    def test_units_and_formula_definition(self):
        # 1. Units
        self.assertEqual(self.audit["energy_units"], "milliJoules (mJ = kN*mm)")
        self.assertIn("milliJoules", self.holdout["formulation"]["energy_units"])

        # 2. Formula
        res_info = self.audit["residual_sign_convention"]
        self.assertEqual(res_info["formula"], "r_E = (E_target - E_source - Delta_E_mesh_independent) / E_source")

        # 3. Sign Convention
        self.assertIn("excess", res_info["positive_residual"].lower())
        self.assertIn("deficit", res_info["negative_residual"].lower())
        self.assertIn("alignment", res_info["zero_residual"].lower())

    def test_classification_and_governance_retention(self):
        # Must be strictly PROSPECTIVE_CRITERION_REQUIRES_HOLDOUT_VALIDATION
        expected_class = "PROSPECTIVE_CRITERION_REQUIRES_HOLDOUT_VALIDATION"
        self.assertEqual(self.audit["classification"], expected_class)
        self.assertEqual(self.holdout["governance_status"]["classification"], expected_class)

        # Gate C1-2 Step 2 must remain strictly FAILED
        gov = self.audit["governance_preservation"]
        self.assertEqual(gov["level_3_gate_status"], "C1_2_STEP2_ENERGY_GATE_FAILED")
        self.assertIn("FAIL", gov["package_113_status"])
        self.assertFalse(gov["retrospective_alteration_permitted"])
        self.assertFalse(gov["autonomous_c5_remeshing_permitted"])

        # Holdout spec must also retain blocked status
        self.assertFalse(self.holdout["governance_status"]["c5_remeshing_permitted"])
        self.assertIn("FAILED", self.holdout["governance_status"]["gate_c1_2_step2_status"])

    def test_circularity_and_correlation_detection(self):
        circ = self.audit["circularity_audit"]
        self.assertTrue(circ["circular_tuning_identified"])
        self.assertIn("Package 115", circ["circular_pair"])
        self.assertIn("Package 113", circ["circular_pair"])

        # Check controls
        controls = self.audit["controls_analyzed"]
        self.assertEqual(len(controls), 7, "Must analyze exactly 7 controls (P111 R2, 112, 113, 115, 116 R1, 117, 118)")

        inc79_controls = [c for c in controls if c["is_inc79_family"]]
        self.assertEqual(len(inc79_controls), 5, "Exactly 5 controls share Increment 79 physical state")

    def test_state_dependent_mesh_energy_shift(self):
        controls_by_id = {c["package_id"]: c for c in self.audit["controls_analyzed"]}

        p111 = controls_by_id["PACKAGE_111_R2"]
        p112 = controls_by_id["PACKAGE_112"]
        p113 = controls_by_id["PACKAGE_113"]
        p115 = controls_by_id["PACKAGE_115"]

        # Shift grows with crack localization: Frame 77 (~0.15%) < Inc 78 (~1.75%) < Inc 79 (~2.01-2.03%)
        self.assertLess(p111["pct_discrepancy_raw"], p112["pct_discrepancy_raw"])
        self.assertLess(p112["pct_discrepancy_raw"], p113["pct_discrepancy_raw"])
        self.assertAlmostEqual(p111["pct_discrepancy_raw"], 0.15036, places=3)
        self.assertAlmostEqual(p112["pct_discrepancy_raw"], 1.74995, places=3)
        self.assertAlmostEqual(p113["pct_discrepancy_raw"], 2.00808, places=3)

        # Applying Model 4 (P115-based shift) to P111 R2 yields large negative residual (-1.917%)
        self.assertLess(p111["r_E_model4_pct"], -1.5)

    def test_csv_artifact_integrity(self):
        with open(self.csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        self.assertEqual(len(rows), 7)
        pkg_ids = [r["package_id"] for r in rows]
        expected_pkgs = [
            "PACKAGE_111_R2", "PACKAGE_112", "PACKAGE_113",
            "PACKAGE_115", "PACKAGE_116_R1", "PACKAGE_117", "PACKAGE_118"
        ]
        self.assertEqual(pkg_ids, expected_pkgs)

if __name__ == "__main__":
    unittest.main()

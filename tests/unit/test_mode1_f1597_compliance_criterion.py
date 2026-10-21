"""Unit tests for F1597 compliance mismatch verification and remeshing acceptance criterion."""
import hashlib
import json
from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts/validation"))

from verify_mode1_f1597_compliance_criterion import evaluate_compliance_and_acceptance, TOLERANCES


class TestMode1F1597ComplianceCriterion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = evaluate_compliance_and_acceptance(REPO_ROOT)

    def test_schema_and_verification(self):
        res = self.result
        self.assertEqual(res["schema"], 1)
        self.assertEqual(res["status"], "PREPARATION_COMPLETE")
        self.assertTrue(res["verification_passed"])
        self.assertEqual(res["overall_transfer_qualification"], "FAIL")
        self.assertGreaterEqual(len(res["finding"].strip()), 20)
        self.assertIn("measurements", res)
        self.assertIn("acceptance_criteria", res)
        self.assertIn("evidence_sources", res)

    def test_undamaged_elastic_compliance_parity(self):
        m = self.result["measurements"]
        # Undamaged elastic discrepancy must be <= 5.0% (and empirically <= 2.0%)
        self.assertLessEqual(m["elastic_stiffness_discrepancy_pct"], TOLERANCES["elastic_compliance_threshold_pct"])
        self.assertLessEqual(m["elastic_stiffness_discrepancy_pct"], 2.0)
        self.assertAlmostEqual(m["donor_elastic_RF_N"], 389.37, delta=1.0)
        self.assertAlmostEqual(m["receiver_elastic_RF_N"], 393.91, delta=1.0)

    def test_damaged_stiffness_collapse(self):
        m = self.result["measurements"]
        # Damaged initial mapped stiffness discrepancy must exceed 50% (empirically ~67.2%)
        self.assertGreater(m["damaged_stiffness_discrepancy_pct"], 50.0)
        self.assertAlmostEqual(m["donor_damaged_RF_N"], 7.85, delta=0.1)
        self.assertAlmostEqual(m["receiver_damaged_RF_N"], 2.57, delta=0.1)

    def test_equilibrated_force_discontinuity(self):
        m = self.result["measurements"]
        # Equilibrated force error is -81.20% (FAIL against 5% threshold)
        self.assertGreater(abs(m["equilibrated_force_continuity_error_pct"]), TOLERANCES["force_continuity_threshold_pct"])
        self.assertAlmostEqual(m["receiver_equilibrated_RF_N"], 1.4757, delta=0.05)

    def test_spatial_damage_volume_expansion(self):
        m = self.result["measurements"]
        # Damage L2 integral expands by > 15% (empirically ~18.01%)
        self.assertGreater(m["damage_L2_expansion_pct"], 15.0)
        # Fracture energy jump exceeds 2.0% qualification threshold (empirically ~17.30%)
        self.assertGreater(abs(m["fracture_energy_error_pct"]), TOLERANCES["fracture_energy_threshold_pct"])

    def test_acceptance_criteria_structure_and_logic(self):
        crit = self.result["acceptance_criteria"]
        self.assertEqual(crit["criterion_1_elastic_compliance"]["status"], "PASS")
        self.assertEqual(crit["criterion_2_damaged_compliance"]["status"], "FAIL")
        self.assertEqual(crit["criterion_3_crack_band_sizing"]["status"], "FAIL")
        self.assertEqual(crit["criterion_4_refinement_band_width"]["status"], "PASS")
        self.assertEqual(crit["criterion_5_fracture_energy_preservation"]["status"], "FAIL")
        self.assertEqual(crit["criterion_6_force_continuity"]["status"], "FAIL")

    def test_evidence_sources_integrity(self):
        sources = self.result["evidence_sources"]
        self.assertGreaterEqual(len(sources), 5)
        for rel_path, expected_hash in sources.items():
            full_path = REPO_ROOT / rel_path
            self.assertTrue(full_path.is_file(), f"Missing evidence file: {rel_path}")
            hasher = hashlib.sha256()
            with open(full_path, "rb") as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)
            actual_hash = hasher.hexdigest().upper()
            self.assertEqual(actual_hash, expected_hash, f"Hash mismatch for {rel_path}")


if __name__ == "__main__":
    unittest.main()

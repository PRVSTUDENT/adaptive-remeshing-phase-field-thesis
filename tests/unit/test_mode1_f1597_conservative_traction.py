"""Unit tests for F1597 conservative nonmatching traction interface-transfer operator."""
import hashlib
import json
from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts/validation"))

from transfer_mode1_f1597_conservative_traction import evaluate_conservative_transfer, TOLERANCES


class TestMode1F1597ConservativeTraction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = evaluate_conservative_transfer(REPO_ROOT)

    def test_schema_and_verification(self):
        res = self.result
        self.assertEqual(res["schema"], 1)
        self.assertEqual(res["status"], "PREPARATION_COMPLETE")
        self.assertTrue(res["verification_passed"])
        self.assertGreaterEqual(len(res["finding"].strip()), 20)
        self.assertIn("measurements", res)
        self.assertIn("evidence_sources", res)

    def test_force_resultant_conservation(self):
        m = self.result["measurements"]
        # Acceptance criterion: Relative error <= 1 x 10^-8
        self.assertLessEqual(m["force_resultant_relative_error"], TOLERANCES["force_resultant_rel_error"])
        self.assertAlmostEqual(m["transferred_force_resultant_N"], m["donor_force_resultant_N"], places=7)

    def test_moment_balance_conservation(self):
        m = self.result["measurements"]
        # Acceptance criterion: Relative error <= 1 x 10^-8
        self.assertLessEqual(m["moment_balance_relative_error"], TOLERANCES["moment_balance_rel_error"])
        self.assertAlmostEqual(m["transferred_moment_N_mm"], m["donor_moment_N_mm"], places=7)

    def test_virtual_work_consistency(self):
        m = self.result["measurements"]
        # Acceptance criterion: Relative error <= 1 x 10^-8 on constant and linear compatible fields
        self.assertLessEqual(m["virtual_work_const_rel_error"], TOLERANCES["virtual_work_rel_error"])
        self.assertLessEqual(m["virtual_work_linear_rel_error"], TOLERANCES["virtual_work_rel_error"])

    def test_patch_tests(self):
        m = self.result["measurements"]
        self.assertLessEqual(m["patch_test_constant_rel_error"], TOLERANCES["force_resultant_rel_error"])
        self.assertLessEqual(m["patch_test_linear_rel_error"], TOLERANCES["force_resultant_rel_error"])

    def test_mechanical_residual(self):
        m = self.result["measurements"]
        # Acceptance criterion: Residual <= 1 x 10^-10 kN
        self.assertLessEqual(m["neumann_mechanical_residual_kN"], TOLERANCES["mechanical_residual_kN"])

    def test_physical_thresholds_offline_retention(self):
        m = self.result["measurements"]
        # Physical force continuity target: <= 5% (verified FAIL under Dirichlet BVP)
        self.assertGreater(abs(m["dirichlet_force_continuity_error_pct"]), TOLERANCES["force_continuity_target_pct"])
        # Physical fracture energy target: <= 2% (verified FAIL under mesh mapping)
        self.assertGreater(abs(m["fracture_energy_error_pct"]), TOLERANCES["fracture_energy_target_pct"])
        # Verifies the 3.34x compliance ratio discovery
        self.assertGreater(m["effective_stiffness_ratio_donor_vs_receiver"], 3.0)

    def test_evidence_sources_integrity(self):
        sources = self.result["evidence_sources"]
        self.assertGreaterEqual(len(sources), 5)
        for rel_path, expected_hash in sources.items():
            full_path = REPO_ROOT / rel_path
            self.assertTrue(full_path.is_file(), f"Missing evidence file: {rel_path}")
            self.assertLessEqual(full_path.stat().st_size, 16777216)
            actual_hash = hashlib.sha256(full_path.read_bytes()).hexdigest().upper()
            self.assertEqual(actual_hash, expected_hash, f"Hash mismatch for {rel_path}")


if __name__ == "__main__":
    unittest.main()

"""Unit tests for F1597 State-Transfer Contract and Nonmatching-Mesh Patch Test Suite."""
import hashlib
import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PRODUCTION_UEL_PATH = REPO_ROOT / "models/pandey_kumar_mode1/reproduction_package_gate6b_energy/f42_mixed_uel.for"
EXPECTED_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
CANDIDATE_DONOR_PATH = REPO_ROOT / "models/pandey_kumar_mode1/candidate_donor_h0025.inp"
EXPECTED_DONOR_SHA256 = "4C82B66BDA1D925C2BEA65CF765633897ACF4B0030E43C77647FA5E0D05A3179"
CANDIDATE_C2_PATH = REPO_ROOT / "models/pandey_kumar_mode1/candidate_crack_band_mesh_c2.inp"
EXPECTED_C2_SHA256 = "257FC6263D63721BDEEFE48A43CD504C79A92DF61C099CE9481984B625454901"
AUDIT_OUTPUT_PATH = REPO_ROOT / "results/validation/f1597_state_transfer_patch_test_audit.json"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()


class TestMode1F1597StateTransferPatchTest(unittest.TestCase):
    """Test suite for donor-to-receiver state-transfer contract and patch tests."""

    @classmethod
    def setUpClass(cls):
        import sys
        if str(REPO_ROOT) not in sys.path:
            sys.path.insert(0, str(REPO_ROOT))
        from scripts.validation.audit_f1597_state_transfer_patch_test import run_state_transfer_patch_tests
        cls.data = run_state_transfer_patch_tests(REPO_ROOT)

    def test_audit_execution_and_schema(self):
        """Verify that the patch test audit script produces a valid schema 1 artifact."""
        self.assertEqual(self.data["schema"], 1)
        self.assertEqual(self.data["task_id"], "F1597-CORRECT-PACKAGE72-STATE-TRANSFER")
        self.assertEqual(self.data["status"], "PREPARATION_COMPLETE")
        self.assertTrue(self.data["verification_passed"])
        self.assertEqual(self.data["classification"], "STATE_TRANSFER_CONTRACT_AND_PATCH_TEST_QUALIFIED")
        self.assertIn("state_transfer_contract", self.data)
        self.assertIn("patch_test_results", self.data)

    def test_patch_test_1_constant_field_exactness(self):
        """Verify exact reproduction of constant scalar and displacement fields (<= 1e-12)."""
        pt1 = self.data["patch_test_results"]["patch_test_1_constant_field"]
        self.assertTrue(pt1["passed"])
        self.assertLessEqual(pt1["scalar_max_error"], 1e-12)
        self.assertLessEqual(pt1["vector_max_error"], 1e-12)

    def test_patch_test_2_affine_field_exactness(self):
        """Verify exact reproduction of linear affine field on uncracked quads (<= 1e-11)."""
        pt2 = self.data["patch_test_results"]["patch_test_2_affine_field"]
        self.assertTrue(pt2["passed"])
        self.assertLessEqual(pt2["max_error"], 1e-11)

    def test_patch_test_3_slit_discontinuity_isolation(self):
        """Verify duplicate-node slit flank isolation and zero cross-slit leakage."""
        pt3 = self.data["patch_test_results"]["patch_test_3_slit_discontinuity"]
        self.assertTrue(pt3["passed"])
        self.assertLessEqual(pt3["upper_flank_max_error"], 1e-12)
        self.assertLessEqual(pt3["lower_flank_max_error"], 1e-12)
        self.assertAlmostEqual(pt3["cross_slit_jump_measured"], 0.70, places=12)

    def test_patch_test_4_bounds_and_irreversibility(self):
        """Verify that physical damage bounds [0, 1] and irreversibility (0 healing) are enforced."""
        pt4 = self.data["patch_test_results"]["patch_test_4_bounds_and_irreversibility"]
        self.assertTrue(pt4["passed"])
        self.assertTrue(pt4["bounds_satisfied"])
        self.assertEqual(pt4["healing_nodes"], 0)
        self.assertGreaterEqual(pt4["min_delta_d"], 0.0)

    def test_patch_test_5_at2_fracture_energy_conservation(self):
        """Verify AT2 fracture energy conservation between meshes within 2.0% tolerance."""
        pt5 = self.data["patch_test_results"]["patch_test_5_at2_fracture_energy"]
        self.assertTrue(pt5["passed"])
        self.assertLessEqual(pt5["relative_error_pct"], 2.0)
        self.assertGreater(pt5["gamma_donor_mJ"], 0.20)
        self.assertGreater(pt5["gamma_receiver_mJ"], 0.20)

    def test_production_uel_and_mesh_hashes(self):
        """Verify bitwise integrity of production UEL and both input decks."""
        self.assertTrue(PRODUCTION_UEL_PATH.exists())
        self.assertEqual(sha256_file(PRODUCTION_UEL_PATH), EXPECTED_UEL_SHA256)

        self.assertTrue(CANDIDATE_DONOR_PATH.exists())
        self.assertEqual(sha256_file(CANDIDATE_DONOR_PATH), EXPECTED_DONOR_SHA256)

        self.assertTrue(CANDIDATE_C2_PATH.exists())
        self.assertEqual(sha256_file(CANDIDATE_C2_PATH), EXPECTED_C2_SHA256)


if __name__ == "__main__":
    unittest.main()

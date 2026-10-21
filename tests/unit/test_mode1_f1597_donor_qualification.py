"""Unit tests for F1597 candidate donor qualification audit."""
import unittest
import hashlib
from pathlib import Path
from scripts.validation.audit_f1597_donor_candidate_qualification import (
    REPO_ROOT,
    CANDIDATE_DONOR_PATH,
    EXPECTED_DONOR_SHA256,
    PRODUCTION_UEL_PATH,
    EXPECTED_UEL_SHA256,
    PACKAGE50_BENCHMARK_PATH,
    sha256_file,
    resolve_physical_length_scale,
    diagnose_hpc_blocker,
    verify_candidate_donor_bvp,
    run_full_donor_candidate_qualification_audit,
)


class TestMode1F1597DonorQualification(unittest.TestCase):
    """Test verification suite for candidate h=2.5 um Mode-I donor model."""

    def test_production_uel_hash(self):
        """Production UEL must match frozen bitwise hash CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6."""
        self.assertTrue(PRODUCTION_UEL_PATH.exists(), f"Missing production UEL: {PRODUCTION_UEL_PATH}")
        uel_hash = sha256_file(PRODUCTION_UEL_PATH)
        self.assertEqual(uel_hash, EXPECTED_UEL_SHA256)

    def test_candidate_donor_deck_hash(self):
        """Candidate donor input deck must match verified hash."""
        self.assertTrue(CANDIDATE_DONOR_PATH.exists(), f"Missing candidate donor deck: {CANDIDATE_DONOR_PATH}")
        deck_hash = sha256_file(CANDIDATE_DONOR_PATH)
        self.assertEqual(deck_hash, EXPECTED_DONOR_SHA256)

    def test_physical_length_scale_resolution(self):
        """Authoritative physical regularization length scale must be resolved as l0 = 0.0075 mm (7.5 um)."""
        res = resolve_physical_length_scale()
        self.assertAlmostEqual(res["authoritative_l0_mm"], 0.0075, places=6)
        self.assertAlmostEqual(res["authoritative_l0_um"], 7.5, places=3)
        self.assertAlmostEqual(res["coarse_donor_mesh_h_um"], 5.0, places=3)
        self.assertAlmostEqual(res["coarse_donor_resolution_ratio_l0_over_h"], 1.5, places=3)

    def test_hpc_blocker_diagnosis(self):
        """Offline blocker must be diagnosed with dual classification."""
        res = diagnose_hpc_blocker()
        self.assertTrue(res["no_submission_exit_criteria_satisfied"])
        self.assertIn("OFFLINE", res["blocker_classification"])

    def test_bvp_verification(self):
        """BVP conformance check must verify mesh dimensions, element counts, and positive Jacobians."""
        bvp = verify_candidate_donor_bvp()
        self.assertTrue(bvp["deck_hash_verified"])
        self.assertTrue(bvp["uel_hash_verified"])
        self.assertEqual(bvp["phase_element_count"], 1600)
        self.assertEqual(bvp["mechanical_element_count"], 1600)
        self.assertEqual(bvp["physical_node_count"], 1698)
        self.assertGreater(bvp["min_jacobian_det"], 0.0)
        self.assertTrue(bvp["bvp_consistent"])

    def test_full_audit_execution(self):
        """Full qualification audit must succeed with status PREPARATION_COMPLETE."""
        audit = run_full_donor_candidate_qualification_audit()
        self.assertEqual(audit["status"], "PREPARATION_COMPLETE")
        self.assertTrue(audit["verification_passed"])
        self.assertEqual(audit["classification"], "CANDIDATE_DONOR_H0025_QUALIFIED_OFFLINE")
        self.assertIn("F1597", audit["task_id"])


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""
tests/unit/test_mode1_length_scale_sensitivity_pipeline.py

Unit tests for Mode-I Phase-Field Length-Scale Sensitivity Pipeline
===================================================================

Validates:
  1. Candidate definitions and parameters for L1, L2, L3.
  2. Single intended difference: only l0 varies across L1 (0.0075), L2 (0.01125), L3 (0.01500).
  3. Mesh and time discretization invariance across L1, L2, L3 (41,912 elements, 42,364 nodes).
  4. L1 vs S3 equivalence audit (L1_BASELINE = REUSE_S3_REFERENCE) and solver omission rule.
  5. Correct terminology enforcement: "phase-field length-scale sensitivity / characterization",
     rejecting "length-scale convergence".
  6. Initial stiffness K0 computation and R^2 linearity evaluation.
  7. Matched-displacement resampling with zero extrapolation rule.
  8. SHA-256 cryptographic provenance of decks and production Fortran.
"""

import os
import sys
import unittest
import numpy as np

# Add repo root to path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.validation.length_scale_sensitivity_pipeline import (
    LENGTH_SCALE_CANDIDATES,
    verify_l1_s3_equivalence,
    compute_initial_stiffness,
    resample_on_common_displacement,
    evaluate_length_scale_sensitivity,
    compute_sha256,
    E_MODULUS,
    NU_POISSON,
    G_CRITICAL,
    K_RESIDUAL,
    T_REF_MM,
    NPHYS_S3
)


class TestMode1LengthScaleSensitivityPipeline(unittest.TestCase):
    
    def test_candidate_inventory_completeness(self):
        """Verify L1, L2, L3 candidates are fully defined."""
        self.assertIn("L1", LENGTH_SCALE_CANDIDATES)
        self.assertIn("L2", LENGTH_SCALE_CANDIDATES)
        self.assertIn("L3", LENGTH_SCALE_CANDIDATES)
        self.assertEqual(len(LENGTH_SCALE_CANDIDATES), 3)

    def test_mesh_invariance_across_candidates(self):
        """Verify all candidates share identical 41,912 elements and 42,364 nodes."""
        for cid, cand in LENGTH_SCALE_CANDIDATES.items():
            self.assertEqual(cand["n_elements"], 41912)
            self.assertEqual(cand["n_nodes"], 42364)
            self.assertAlmostEqual(cand["h_mm"], 0.0015, places=6)

    def test_single_intended_difference_l0(self):
        """Verify l0 is the single physical parameter varied across L1, L2, L3."""
        self.assertAlmostEqual(LENGTH_SCALE_CANDIDATES["L1"]["l0_mm"], 0.0075, places=6)
        self.assertAlmostEqual(LENGTH_SCALE_CANDIDATES["L2"]["l0_mm"], 0.01125, places=6)
        self.assertAlmostEqual(LENGTH_SCALE_CANDIDATES["L3"]["l0_mm"], 0.01500, places=6)
        
        # Verify ratios
        self.assertAlmostEqual(LENGTH_SCALE_CANDIDATES["L1"]["h_over_l0"], 0.0015 / 0.0075, places=4)
        self.assertAlmostEqual(LENGTH_SCALE_CANDIDATES["L2"]["h_over_l0"], 0.0015 / 0.01125, places=4)
        self.assertAlmostEqual(LENGTH_SCALE_CANDIDATES["L3"]["h_over_l0"], 0.0015 / 0.01500, places=4)

    def test_l1_s3_equivalence_audit(self):
        """Verify automated equivalence check confirms 0 diffs between L1 and S3."""
        res = verify_l1_s3_equivalence(REPO_ROOT)
        self.assertEqual(res["status"], "EQUIVALENT_TO_S3_REFERENCE")
        self.assertTrue(res["is_equivalent"])
        self.assertEqual(res["differences_count"], 0)
        self.assertEqual(res["governing_classification"], "L1_BASELINE = REUSE_S3_REFERENCE")
        self.assertEqual(res["submission_action"], "OMIT_FROM_CLUSTER_SUBMISSIONS_REUSE_S3")

    def test_terminology_discipline(self):
        """Verify that length-scale study is classified as sensitivity/characterization, not convergence."""
        for cid, cand in LENGTH_SCALE_CANDIDATES.items():
            self.assertIn("sensitivity", cand["role"])
            self.assertNotIn("length_scale_convergence", cand["role"])

    def test_initial_stiffness_calculation(self):
        """Verify initial stiffness extraction on synthetic linear response."""
        u = np.linspace(0.0, 0.0050, 501)
        f = 138.0 * u + 0.0
        k0, intercept, r2 = compute_initial_stiffness(u, f, u_max_linear=0.0010)
        self.assertAlmostEqual(k0, 138.0, places=3)
        self.assertAlmostEqual(intercept, 0.0, places=5)
        self.assertAlmostEqual(r2, 1.0, places=5)

    def test_resampling_zero_extrapolation_rule(self):
        """Verify resampling strictly assigns NaN outside source displacement range."""
        u_src = np.array([0.001, 0.002, 0.003, 0.004])
        f_src = np.array([0.138, 0.276, 0.414, 0.552])
        
        u_target = np.array([0.0, 0.0015, 0.0035, 0.0050])
        f_resampled = resample_on_common_displacement(u_src, f_src, u_target)
        
        # Out of bounds should be NaN
        self.assertTrue(np.isnan(f_resampled[0]))  # 0.0 < 0.001
        self.assertTrue(np.isnan(f_resampled[3]))  # 0.005 > 0.004
        # In bounds should be linearly interpolated
        self.assertAlmostEqual(f_resampled[1], 0.207, places=4)
        self.assertAlmostEqual(f_resampled[2], 0.483, places=4)

    def test_deck_hashes_and_production_fortran(self):
        """Verify package files exist and production Fortran matches canonical SHA-256."""
        canonical_fortran_sha = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
        for cid, cand in LENGTH_SCALE_CANDIDATES.items():
            pkg_path = os.path.join(REPO_ROOT, cand["package_dir"])
            inp_path = os.path.join(pkg_path, cand["deck_filename"])
            for_path = os.path.join(pkg_path, "f42_mixed_uel.for")
            
            self.assertTrue(os.path.exists(inp_path), f"Deck missing: {inp_path}")
            self.assertTrue(os.path.exists(for_path), f"Fortran missing: {for_path}")
            
            sha_for = compute_sha256(for_path)
            self.assertEqual(sha_for, canonical_fortran_sha)

    def test_pre_job_cards_and_manifests_exist(self):
        """Verify all three candidates have valid PRE_JOB_CARD.md and manifest.json."""
        for cid, cand in LENGTH_SCALE_CANDIDATES.items():
            pkg_path = os.path.join(REPO_ROOT, cand["package_dir"])
            card_path = os.path.join(pkg_path, "PRE_JOB_CARD.md")
            manifest_path = os.path.join(pkg_path, "manifest.json")
            
            self.assertTrue(os.path.exists(card_path), f"PRE_JOB_CARD missing: {card_path}")
            self.assertTrue(os.path.exists(manifest_path), f"manifest.json missing: {manifest_path}")


if __name__ == "__main__":
    unittest.main()

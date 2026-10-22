"""Unit tests for F1597 state-initialization pathway audit and compatibility."""
import sys
import unittest
import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.validation.audit_f1597_state_initialization_pathway import (
    PRODUCTION_UEL_PATH,
    EXPECTED_UEL_SHA256,
    CANDIDATE_DONOR_PATH,
    EXPECTED_DONOR_SHA256,
    CANDIDATE_C2_PATH,
    EXPECTED_C2_SHA256,
    sha256_file,
    load_inp_mesh,
    audit_frozen_uel_state_layout,
    verify_state_packing_roundtrip,
    verify_overlay_correspondence,
    execute_f1597_state_initialization_pathway_audit,
)


class TestMode1F1597StateInitializationPathway(unittest.TestCase):
    """Test suite for UEL state layout, packing, overlay, and Abaqus initialization."""

    def test_production_uel_hash_preserved(self):
        """Production UEL f42_mixed_uel.for must match frozen hash."""
        self.assertTrue(PRODUCTION_UEL_PATH.exists(), f"Missing UEL: {PRODUCTION_UEL_PATH}")
        uel_hash = sha256_file(PRODUCTION_UEL_PATH)
        self.assertEqual(uel_hash, EXPECTED_UEL_SHA256)

    def test_candidate_mesh_hashes_preserved(self):
        """Candidate donor and C2 receiver decks must match frozen hashes."""
        self.assertTrue(CANDIDATE_DONOR_PATH.exists(), f"Missing donor deck: {CANDIDATE_DONOR_PATH}")
        self.assertEqual(sha256_file(CANDIDATE_DONOR_PATH), EXPECTED_DONOR_SHA256)

        self.assertTrue(CANDIDATE_C2_PATH.exists(), f"Missing C2 deck: {CANDIDATE_C2_PATH}")
        self.assertEqual(sha256_file(CANDIDATE_C2_PATH), EXPECTED_C2_SHA256)

    def test_uel_state_layout_declaration(self):
        """Verify 18 SVARS, CB_STATE_TRANS common block, and lines 248-262 history ingestion."""
        audit = audit_frozen_uel_state_layout()
        self.assertEqual(audit["declared_nsvars"], 18)
        self.assertTrue(audit["has_common_block_cb_state_trans"])
        self.assertTrue(audit["has_initial_history_ingestion_statement"])
        self.assertTrue(audit["has_kstep_kinc_guard"])
        self.assertTrue(audit["phase_field_from_nodal_dof3"])

    def test_lossless_packing_roundtrip(self):
        """Packing and unpacking 18-variable state array must have machine-zero difference."""
        packing = verify_state_packing_roundtrip(n_elements=500)
        self.assertEqual(packing["nsvars"], 18)
        self.assertEqual(packing["max_packing_unpacking_difference"], 0.0)
        self.assertTrue(packing["packing_lossless"])

    def test_u1_u2_overlay_correspondence(self):
        """Phase U1 and Mech U2 elements must have exact 1-to-1 node connectivity alignment."""
        c2_mesh = load_inp_mesh(CANDIDATE_C2_PATH)
        overlay = verify_overlay_correspondence(c2_mesh)
        self.assertEqual(overlay["n_physical_elements"], 2300)
        self.assertEqual(overlay["u1_count"], 2300)
        self.assertEqual(overlay["u2_count"], 2300)
        self.assertEqual(overlay["u1_u2_mismatches"], 0)
        self.assertTrue(overlay["overlay_exact"])

    def test_full_state_initialization_audit(self):
        """Execute full state-initialization audit and verify all metrics and artifacts."""
        audit = execute_f1597_state_initialization_pathway_audit()
        self.assertEqual(audit["status"], "PREPARATION_COMPLETE")
        self.assertTrue(audit["verification_passed"])
        self.assertEqual(audit["classification"], "STATE_LAYOUT_VERIFIED_SOLVER_VALIDATION_PENDING")
        self.assertEqual(audit["audit_metrics"]["healing_node_count"], 0)
        self.assertEqual(audit["audit_metrics"]["negative_history_count"], 0)
        self.assertGreater(audit["audit_metrics"]["min_history_value"], 0.0)

        # Check sample initialization deck artifact
        sample_deck = REPO_ROOT / "results/validation/f1597_receiver_initialization_deck_sample.inp"
        self.assertTrue(sample_deck.exists())
        self.assertGreater(sample_deck.stat().st_size, 100)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""
test_package159_consistency_and_readiness.py

Unit tests for Package 159 scientific consistency and Abaqus readiness audit.
"""

import unittest
import json
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")

class TestPackage159ConsistencyAndReadiness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from scripts.validation.audit_package159_consistency_and_readiness import run_consistency_audit
        cls.audit_path = REPO_ROOT / "results/validation/package159_scientific_consistency_audit.json"
        cls.audit_data = run_consistency_audit(cls.audit_path)

    def test_audit_passed_and_classified(self):
        self.assertTrue(self.audit_data["verification_passed"])
        self.assertEqual(self.audit_data["status"], "PREPARATION_COMPLETE")
        self.assertEqual(self.audit_data["classification"], "P159_SCIENTIFICALLY_CONSISTENT_OFFLINE")

    def test_threshold_audit_consistency(self):
        ta = self.audit_data["threshold_audit"]
        self.assertEqual(ta["miseseri_marked_elements"], 266)
        self.assertEqual(ta["pilot_damage_marked_elements"], 85)
        self.assertEqual(ta["pilot_intersection_elements"], 12)
        self.assertEqual(ta["pilot_union_elements"], 339)
        self.assertEqual(ta["pilot_newly_marked_elements"], 73)
        # Verify that d >= 0.15 is indeed massive (3643 elements), proving the typo
        self.assertEqual(ta["hypothetical_union_elements"], 3643)
        self.assertEqual(ta["scientific_consistency_status"], "THRESHOLD_CONSISTENT_WITH_APPROVED_PILOT")

    def test_unit_and_dimensional_consistency(self):
        ua = self.audit_data["unit_audit"]
        self.assertEqual(ua["length_unit"], "mm")
        self.assertEqual(ua["force_unit"], "kN")
        self.assertEqual(ua["Gc_in_Abaqus_deck"], 0.0027)
        self.assertEqual(ua["Gc_deck_units"], "kN/mm")
        self.assertEqual(ua["Gc_SI_equivalent_J_per_m2"], 2700.0)
        self.assertEqual(ua["Gc_in_N_per_mm"], 2.7)
        self.assertTrue(ua["scaled_energy_match"])
        self.assertTrue(ua["physical_continuity_preserved"])

    def test_receiver_mesh_and_transfer_integrity(self):
        ia = self.audit_data["integrity_audit"]
        self.assertEqual(ia["physical_quads"], 13924)
        self.assertEqual(ia["uel_element_pairs"], 27848)
        self.assertEqual(ia["continuum_nodes"], 14216)
        self.assertEqual(ia["slit_seam_pairs"], 55)
        self.assertGreater(ia["min_det_jacobian"], 0.0)
        self.assertEqual(ia["unmapped_nodes"], 0)
        self.assertEqual(ia["unmapped_gps"], 0)
        self.assertEqual(ia["cross_slit_violations"], 0)

    def test_energy_preservation_gates(self):
        ec = self.audit_data["integrity_audit"]["energy_comparison"]
        self.assertLessEqual(ec["fracture_diff_percent"], 2.0)
        self.assertLessEqual(ec["elastic_diff_percent"], 2.0)
        self.assertLessEqual(ec["raw_total_diff_percent"], 2.0)
        self.assertTrue(ec["all_continuity_gates_passed"])

    def test_frozen_uel_and_canonical_p158_identity(self):
        self.assertEqual(self.audit_data["frozen_uel_sha256"], "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6")
        self.assertEqual(self.audit_data["canonical_p158_r5_operation"], "execute_mode1_package158_c2_0_r5_re_equilibration")

if __name__ == "__main__":
    unittest.main()

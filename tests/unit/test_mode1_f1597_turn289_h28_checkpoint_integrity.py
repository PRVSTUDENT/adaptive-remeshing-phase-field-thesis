# -*- coding: utf-8 -*-
import json
import os
import unittest


class TestMode1F1597Turn289H28CheckpointIntegrity(unittest.TestCase):
    """Unit test suite verifying Hypothesis H28 checkpoint serialization and restorability."""

    @classmethod
    def setUpClass(cls):
        cls.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        cls.audit_path = os.path.join(
            cls.repo_root, "results", "validation", "h28_c4_inc89_exact_checkpoint_integrity.json"
        )
        cls.pkg_dir = os.path.join(
            cls.repo_root, "models", "pandey_kumar_mode1", "137_c4_donor_inc89_h27_exact_frame_continuation"
        )
        with open(cls.audit_path, "r") as f:
            cls.audit = json.load(f)

    def test_01_verdict_and_provenance(self):
        """Verify H28 verdict and authentic provenance from Package 137 Cycle 5."""
        self.assertEqual(self.audit["verdict"], "H28_CHECKPOINT_VERIFIED_RESTORABLE")
        prov = self.audit["checkpoint_provenance"]
        self.assertEqual(prov["source_package"], "137_c4_donor_inc89_h27_exact_frame_continuation")
        self.assertEqual(prov["source_job_id"], "1418548.mmaster02")
        self.assertEqual(prov["converged_cycle"], 5)
        self.assertAlmostEqual(prov["target_displacement_mm"], 0.001990107350, places=9)
        self.assertEqual(
            prov["frozen_uel_sha256"], "AB0A5A71335ECB445E91EC13A645E280FF3310B561A5E78ABA4A49C8E81DD8AC"
        )

    def test_02_array_dimensions_and_counts(self):
        """Verify exactly 4,588 nodes, 4,422 elements, and 17,688 Gauss points."""
        dims = self.audit["dimension_checks"]
        self.assertTrue(dims["all_counts_match"])
        self.assertEqual(dims["node_count"], 4588)
        self.assertEqual(dims["damage_count"], 4588)
        self.assertEqual(dims["element_count"], 4422)
        self.assertEqual(dims["total_gp_count"], 17688)

    def test_03_pointwise_damage_and_history_monotonicity(self):
        """Verify zero damage healing and zero driving history loss across all records."""
        mono = self.audit["monotonicity_results"]
        self.assertTrue(mono["pointwise_monotonicity_passed"])
        self.assertEqual(mono["d_healing_violations"], 0)
        self.assertEqual(mono["h_loss_violations"], 0)
        self.assertGreaterEqual(mono["d_min_growth"], 0.0)

    def test_04_d0_h0_column_separation_and_physical_bounds(self):
        """Verify distinct D0 and H0 columns and physical range compliance."""
        col = self.audit["column_separation_results"]
        self.assertTrue(col["separation_strictly_valid"])
        self.assertGreaterEqual(col["d_min"], 0.0)
        self.assertLessEqual(col["d_max"], 1.0)
        self.assertGreaterEqual(col["h_min_MPa"], 0.0)
        self.assertGreater(col["h_max_MPa"], 1.0)

    def test_05_lossless_round_trip_restoration(self):
        """Verify machine-precision restoration of displacements and damage."""
        res = self.audit["restoration_results"]
        self.assertTrue(res["lossless_round_trip_passed"])
        self.assertLessEqual(res["max_disp_restoration_error_mm"], 1.0e-12)
        self.assertLessEqual(res["max_damage_restoration_error"], 1.0e-12)
        self.assertEqual(res["restored_node_count"], 4588)
        self.assertEqual(res["restored_damage_count"], 4588)

    def test_06_negative_corruption_tests(self):
        """Verify detection of swapped columns, dropped records, and order integrity."""
        neg = self.audit["negative_tests"]
        self.assertTrue(neg["neg_test_column_swap_detected"])
        self.assertTrue(neg["neg_test_dropped_record_detected"])
        self.assertTrue(neg["neg_test_strict_integer_ordering_verified"])

    def test_07_donor_increment_90_reference_authentication(self):
        """Verify authentication of donor Increment-90 reference state."""
        ref = self.audit["donor_inc90_reference"]
        self.assertTrue(ref["reference_authenticated"])
        self.assertEqual(ref["increment"], 90)
        self.assertAlmostEqual(ref["displacement_mm"], 0.00201510731, places=8)
        self.assertAlmostEqual(ref["rf2_N"], 183.603957, places=4)
        self.assertAlmostEqual(ref["e_tot_mJ"], 0.24451600, places=5)

    def test_08_governing_milestone_invariance(self):
        """Verify that Stage C1-2 step 2 energy gate failure remains invariant."""
        gate = self.audit["governing_gate"]
        self.assertEqual(gate["milestone"], "STAGE_C1_2_STEP2_ENERGY_GATE_FAILED")
        self.assertEqual(gate["status"], "FAILED_INVARIANT")
        self.assertGreater(gate["p113_error_pct"], 2.0)


if __name__ == "__main__":
    unittest.main()

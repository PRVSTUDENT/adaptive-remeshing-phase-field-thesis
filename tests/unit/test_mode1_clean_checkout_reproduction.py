#!/usr/bin/env python3
"""
Unit test for clean-checkout reproduction contract verification.
Tests that the canonical configuration, input decks, frozen UEL, and archived metrics
can be verified deterministically from a clean checkout.
"""

import os
import unittest
from scripts.validation.verify_mode1_reproduction_contract import verify_reproduction_contract

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class TestMode1CleanCheckoutReproduction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.receipt = verify_reproduction_contract(WORKSPACE_ROOT)

    def test_overall_status_passed(self):
        self.assertEqual(self.receipt["overall_status"], "PASSED")

    def test_uel_integrity(self):
        uel_check = self.receipt["checks"]["uel_integrity"]
        self.assertTrue(uel_check["passed"])
        self.assertEqual(
            uel_check["actual_sha256"],
            "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6",
        )

    def test_all_deck_hashes(self):
        checks = self.receipt["checks"]
        self.assertTrue(checks["deck_hash_coarse_preanalysis"]["passed"])
        self.assertTrue(checks["deck_hash_adapted_fracture_mesh"]["passed"])
        self.assertTrue(checks["deck_hash_uniform_reference_s1"]["passed"])

    def test_geometry_and_topology(self):
        geom = self.receipt["checks"]["geometry_and_topology"]
        self.assertTrue(geom["passed"])
        self.assertEqual(geom["node_count"], 14647)
        self.assertAlmostEqual(geom["domain_x_range"][0], 0.0, places=4)
        self.assertAlmostEqual(geom["domain_x_range"][1], 1.0, places=4)
        self.assertAlmostEqual(geom["domain_y_range"][0], 0.0, places=4)
        self.assertAlmostEqual(geom["domain_y_range"][1], 1.0, places=4)
        self.assertGreater(geom["nodes_on_slit_y05"], 50)
        self.assertTrue(geom["has_N_BOTTOM"])
        self.assertTrue(geom["has_N_TOP"])
        self.assertTrue(geom["has_N_RP"])
        self.assertTrue(geom["has_UEL_JTYPE1"])
        self.assertTrue(geom["has_UEL_JTYPE2"])

    def test_parity_and_convergence_metrics(self):
        conv = self.receipt["checks"]["parity_and_convergence"]
        self.assertTrue(conv["passed"])
        self.assertTrue(conv["K0_pass"])
        self.assertTrue(conv["Fmax_pass"])
        self.assertTrue(conv["upeak_pass"])
        self.assertTrue(conv["horizon_pass"])
        self.assertTrue(conv["speedup_pass"])
        self.assertTrue(conv["coarse_dof_pass"])
        self.assertLessEqual(abs(conv["delta_K0_pct"]), 0.05)
        self.assertLessEqual(abs(conv["delta_Fmax_pct"]), 2.0)
        self.assertLessEqual(abs(conv["delta_upeak_pct"]), 2.5)
        self.assertGreaterEqual(conv["solver_speedup"], 1.5)
        self.assertGreaterEqual(conv["coarse_dof_reduction_pct"], 70.0)


if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-
"""
tests/unit/test_mode1_f1597_h34_mesh_aware_energy_consistency.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Unit regression test suite for Turn 299 Hypothesis H34 Independent Validation of
Mesh-Aware Energy Consistency.
Verifies:
1. Integrity of H34 audit artifact (schema, task ID, classification).
2. Primary classification H34_TRANSFER_ERROR_NOT_EXCLUDED and governance retention.
3. Authentic unrounded data consistency across Level 1, Level 2, Level 3 Direct, and Level 3 Sequential.
4. Total energy discrepancy between Sequential (P113) and Direct (P115) exceeds H33's truncation bound (46.27 nJ > 20.58 nJ, 2.25x).
5. Significant component-wise energy compensation (|Delta E_frac| ~ 1503.97 nJ, |Delta E_elas| ~ 1457.70 nJ, >70x truncation bound).
6. Non-comparability of physical reference states (1,640 vs 110 clamped nodes; d_max 0.4992 vs 0.5238; RF2 187.39 N vs 185.79 N).
"""

from __future__ import print_function, division
import os
import json
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))


class TestH34MeshAwareEnergyConsistency(unittest.TestCase):

    def setUp(self):
        self.audit_path = os.path.join(REPO_ROOT, "results/validation/h34_mesh_aware_energy_consistency_audit.json")
        self.assertTrue(os.path.exists(self.audit_path), "H34 audit artifact must exist: %s" % self.audit_path)
        with open(self.audit_path, "r") as f:
            self.data = json.load(f)

    def test_schema_and_classification(self):
        self.assertEqual(self.data["schema"], 1)
        self.assertEqual(self.data["task_id"], "F1597-CORRECT-PACKAGE72-STATE-TRANSFER")
        self.assertEqual(self.data["investigation"], "H34_INDEPENDENT_VALIDATION_OF_MESH_AWARE_ENERGY_CONSISTENCY")
        self.assertEqual(self.data["classification"], "H34_TRANSFER_ERROR_NOT_EXCLUDED")
        self.assertIn("H34_TRANSFER_ERROR_NOT_EXCLUDED", self.data["classification_candidates"])
        self.assertIn("H34_REFERENCE_STATES_NOT_COMPARABLE", self.data["classification_candidates"])

    def test_governing_gate_invariance(self):
        self.assertEqual(self.data["governing_gate_retained"], "STAGE_C1_2_STEP2_ENERGY_GATE_FAILED")
        self.assertEqual(self.data["p113_gate_valid_failure_retained"], "+2.00803158%")
        self.assertTrue(self.data["h24_reference_audit_pending_retained"])

    def test_authentic_unrounded_data(self):
        d = self.data["authentic_unrounded_data"]
        # Donor C3 (Package 76 Inc 79)
        self.assertAlmostEqual(d["level_1_c3_donor"]["rf2_N"], 186.067909, places=6)
        self.assertAlmostEqual(d["level_1_c3_donor"]["e_elas_mJ"], 0.17140369, places=7)
        self.assertAlmostEqual(d["level_1_c3_donor"]["e_frac_mJ"], 0.041044352, places=8)
        self.assertAlmostEqual(d["level_1_c3_donor"]["e_tot_mJ"], 0.21244805, places=7)

        # Level 3 Direct (Package 115)
        self.assertAlmostEqual(d["level_3_c4_direct"]["rf2_N"], 185.7885718, places=5)
        self.assertAlmostEqual(d["level_3_c4_direct"]["e_tot_mJ"], 0.216760345, places=7)
        self.assertAlmostEqual(d["level_3_c4_direct"]["e_frac_mJ"], 0.045619029, places=7)
        self.assertAlmostEqual(d["level_3_c4_direct"]["e_elas_mJ"], 0.171141315, places=7)
        self.assertEqual(d["level_3_c4_direct"]["clamped_nodes"], 110)

        # Level 3 Sequential (Package 113)
        self.assertAlmostEqual(d["level_3_c4_sequential"]["rf2_N"], 187.3914748, places=5)
        self.assertAlmostEqual(d["level_3_c4_sequential"]["e_tot_mJ"], 0.216714074, places=7)
        self.assertAlmostEqual(d["level_3_c4_sequential"]["e_frac_mJ"], 0.044115063, places=7)
        self.assertAlmostEqual(d["level_3_c4_sequential"]["e_elas_mJ"], 0.172599011, places=7)
        self.assertEqual(d["level_3_c4_sequential"]["clamped_nodes"], 1640)

    def test_total_energy_difference_exceeds_truncation_bound(self):
        comp = self.data["comparability_analysis"]["truncation_bound_validity"]
        delta_tot = comp["actual_total_energy_difference_nJ"]
        trunc_bound = comp["h33_truncation_bound_nJ"]

        self.assertAlmostEqual(delta_tot, 46.2706, places=2)
        self.assertAlmostEqual(trunc_bound, 20.5835, places=2)
        self.assertFalse(comp["is_total_difference_within_bound"])
        self.assertGreater(delta_tot, trunc_bound)
        self.assertGreater(delta_tot / trunc_bound, 2.0)

    def test_component_energy_compensation(self):
        comp = self.data["comparability_analysis"]["energy_component_compensation"]
        delta_elas = comp["delta_elas_nJ"]
        delta_frac = comp["delta_frac_nJ"]
        net_tot = comp["net_delta_tot_nJ"]

        # Component differences are ~1.5 uJ (~1500 nJ)
        self.assertAlmostEqual(delta_elas, 1457.6957, places=2)
        self.assertAlmostEqual(delta_frac, -1503.9663, places=2)
        self.assertAlmostEqual(net_tot, -46.2706, places=2)

        # Component differences exceed truncation bound by >70x
        trunc_bound = self.data["comparability_analysis"]["truncation_bound_validity"]["h33_truncation_bound_nJ"]
        self.assertGreater(abs(delta_frac) / trunc_bound, 70.0)
        self.assertGreater(abs(delta_elas) / trunc_bound, 70.0)

    def test_reference_states_not_comparable(self):
        comp = self.data["comparability_analysis"]
        self.assertFalse(comp["solutions_physically_identical"])

        # Clamped nodes difference
        clamped = comp["active_set_clamping_mismatch"]
        self.assertEqual(clamped["p113_clamped_nodes"], 1640)
        self.assertEqual(clamped["p115_clamped_nodes"], 110)
        self.assertEqual(clamped["delta_clamped_nodes"], 1530)

        # Peak damage difference
        crack = comp["crack_state_mismatch"]
        self.assertAlmostEqual(crack["p113_dmax"], 0.499220, places=5)
        self.assertAlmostEqual(crack["p115_dmax"], 0.523773, places=5)
        self.assertLess(crack["delta_dmax"], -0.02)


if __name__ == "__main__":
    unittest.main()

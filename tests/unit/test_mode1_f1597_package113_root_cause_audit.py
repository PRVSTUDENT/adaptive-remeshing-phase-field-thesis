# -*- coding: utf-8 -*-
from __future__ import print_function, division
import os
import sys
import json
import unittest

class TestPackage113RootCauseAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        cls.audit_path = os.path.join(cls.root, "results", "validation", "package113_energy_gate_root_cause_audit.json")
        cls.assertTrue(os.path.exists(cls.audit_path), "Audit file must exist: %s" % cls.audit_path)
        with open(cls.audit_path, "r") as f:
            cls.audit = json.load(f)

    def test_01_unrounded_discrepancy(self):
        decon = self.audit["energy_deconstruction"]
        donor_tot = decon["donor_tot_mJ"]
        rec_tot = decon["receiver_tot_mJ"]
        recomputed_pct = ((rec_tot - donor_tot) / donor_tot) * 100.0

        self.assertAlmostEqual(donor_tot, 0.21244805, places=7)
        self.assertAlmostEqual(rec_tot, 0.21671407393519804, places=9)
        self.assertAlmostEqual(recomputed_pct, 2.0080315800488817, places=6)
        self.assertAlmostEqual(decon["pct_diff_tot_unrounded"], 2.0080315800488817, places=6)

    def test_02_tolerance_exceedance(self):
        decon = self.audit["energy_deconstruction"]
        exceedance = decon["exceedance_pct_points"]
        self.assertGreater(exceedance, 0.0)
        self.assertAlmostEqual(exceedance, 0.008031580048881715, places=7)
        self.assertAlmostEqual(decon["exceedance_ppm"], 80.31580048881715, places=3)
        self.assertEqual(self.audit["governing_gate"], "STAGE_C1_2_STEP2_ENERGY_GATE_FAILED")

    def test_03_component_decomposition(self):
        decon = self.audit["energy_deconstruction"]
        pct_elas = decon["pct_diff_elas"]
        pct_frac = decon["pct_diff_frac"]
        share_frac = decon["share_of_excess_frac_pct"]

        # Elastic strain energy passes within 2%
        self.assertLess(pct_elas, 2.0)
        self.assertAlmostEqual(pct_elas, 0.6973716915991621, places=4)

        # Fracture energy drives majority of excess
        self.assertAlmostEqual(pct_frac, 7.481446223786578, places=4)
        self.assertGreater(share_frac, 70.0)
        self.assertAlmostEqual(share_frac, 71.98063511659883, places=3)

    def test_04_driver_code_integrity(self):
        drv = self.audit["driver_code_integrity"]
        self.assertTrue(drv["uses_dynamic_header_lookup"])
        self.assertFalse(drv["has_p134_hardcoded_d0_defect"])
        self.assertEqual(drv["verdict"], "DRIVER_CODE_INTEGRITY_VERIFIED_NO_INDEXING_DEFECT")
        self.assertEqual(drv["h_column_indices"], [5, 6, 7, 8])
        self.assertEqual(drv["d_column_indices"], [1, 2, 3, 4])

    def test_05_same_mesh_control(self):
        ctrl = self.audit["same_mesh_control_audit"]
        pct_diff = ctrl["pct_diff"]
        self.assertLess(abs(pct_diff), 0.01)
        self.assertAlmostEqual(pct_diff, 0.003056247954992523, places=5)
        self.assertEqual(ctrl["verdict"], "AM_ALGORITHM_CONSERVES_ENERGY_TO_0P003_PCT")

    def test_06_numerical_stationarity(self):
        stat = self.audit["numerical_stationarity_audit"]
        self.assertTrue(stat["stationarity_passed"])
        self.assertTrue(stat["load_drift_passed"])
        self.assertTrue(stat["healing_passed"])
        self.assertEqual(stat["healing_violations"], 0)
        self.assertLess(stat["final_delta_d_max"], 0.001000)
        self.assertLess(stat["load_drift_delta_rf2_N"], 0.100)

    def test_07_classification(self):
        self.assertEqual(self.audit["classification"], "P113_GATE_VALID_FAILURE")
        self.assertIn("P113_GATE_VALID_FAILURE", self.audit["classification_candidates"])
        self.assertEqual(self.audit["governing_gate"], "STAGE_C1_2_STEP2_ENERGY_GATE_FAILED")

if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-
"""
test_mode1_f1597_turn210_energy_budget.py
==========================================
Unit test suite verifying the independent finite-element energy budget audit,
component deconstruction, mathematical proof of discretization-driven AT2
fracture energy resolution, and strict gate classification.

Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
"""
import os
import sys
import json
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

class TestEnergyBudgetAudit(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.audit_path = os.path.join(REPO_ROOT, "results", "validation", "energy_budget_f1597_inc79.json")
        if not os.path.exists(cls.audit_path):
            raise unittest.SkipTest("energy_budget_f1597_inc79.json not found")
        with open(cls.audit_path, "r") as f:
            cls.data = json.load(f)

    def test_01_schema_and_task_identity(self):
        self.assertEqual(self.data["schema"], 1)
        self.assertEqual(self.data["task_id"], "F1597-CORRECT-PACKAGE72-STATE-TRANSFER")
        self.assertEqual(self.data["investigation"], "METHOD_C_C4_INC79_ENERGY_DISCREPANCY_DECONSTRUCTION")

    def test_02_donor_c3_energy_accuracy(self):
        donor = self.data["donor_energy_mJ"]
        self.assertEqual(donor["increment"], 79)
        self.assertAlmostEqual(donor["e_elas_mJ"], 0.17140369, places=7)
        self.assertAlmostEqual(donor["e_frac_mJ"], 0.041044352, places=7)
        self.assertAlmostEqual(donor["e_tot_mJ"], 0.21244805, places=7)

    def test_03_c4_solver_energy_and_discrepancy(self):
        c4_sol = self.data["solver_c4_energy_mJ"]
        self.assertAlmostEqual(c4_sol["e_elas_mJ"], 0.17259901, places=6)
        self.assertAlmostEqual(c4_sol["e_frac_mJ"], 0.04411506, places=6)
        self.assertAlmostEqual(c4_sol["e_tot_mJ"], 0.21671407, places=6)

        disc = self.data["energy_discrepancy_deconstruction"]
        self.assertAlmostEqual(disc["pct_diff_tot"], 2.0080315, places=4)
        self.assertGreater(disc["pct_diff_tot"], 2.000000)
        self.assertAlmostEqual(disc["pct_diff_elas"], 0.697371, places=3)
        self.assertAlmostEqual(disc["pct_diff_frac"], 7.481446, places=3)

    def test_04_energy_component_shares(self):
        disc = self.data["energy_discrepancy_deconstruction"]
        frac_share = disc["share_of_excess_frac_pct"]
        elas_share = disc["share_of_excess_elas_pct"]
        self.assertAlmostEqual(frac_share + elas_share, 100.0, places=2)
        self.assertGreater(frac_share, 70.0)
        self.assertLess(elas_share, 30.0)

    def test_05_falsifiable_hypothesis_verification(self):
        hyp = self.data["falsifiable_hypothesis_test"]
        self.assertEqual(hyp["test_result"], "SUPPORTED")
        ev = hyp["evidence"]
        self.assertTrue(ev["zero_healing_verified"])
        self.assertTrue(ev["mechanical_equilibrium_verified"])
        self.assertLess(ev["elastic_energy_continuity_pct"], 1.0)
        self.assertGreater(ev["fracture_energy_share_of_excess_pct"], 70.0)

    def test_06_classification_and_strict_gate_preservation(self):
        self.assertEqual(self.data["classification"], "ENERGY_DIFFERENCE_DISCRETIZATION_SUPPORTED")
        self.assertEqual(self.data["method_c_gate_status"], "C1_2_STEP2_ENERGY_GATE_FAILED")
        self.assertEqual(self.data["hpc_execution_recommendation"], "OFFLINE_AUDIT_SUFFICIENT_NO_ADDITIONAL_HPC_RUN_NEEDED")

    def test_07_package114_miseseri_companion_guard(self):
        miseseri = self.data["package114_miseseri_companion_status"]
        self.assertEqual(miseseri["role"], "QUALIFIED_COMPANION_CONTINUUM_DIAGNOSTIC")
        self.assertEqual(miseseri["marked_elements_above_threshold_eta_015"], 284)
        self.assertIn("not as a phase-field error estimator", miseseri["pointwise_limit"])

    def test_08_source_hashes_exist(self):
        hashes = self.data["source_hashes"]
        self.assertGreaterEqual(len(hashes), 5)
        for rel_path, h in hashes.items():
            full_p = os.path.join(REPO_ROOT, rel_path)
            self.assertTrue(os.path.exists(full_p), f"Source file {rel_path} does not exist")
            self.assertEqual(len(h), 64, f"Hash for {rel_path} is not SHA256")

if __name__ == "__main__":
    unittest.main()

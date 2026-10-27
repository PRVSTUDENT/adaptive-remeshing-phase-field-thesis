# -*- coding: utf-8 -*-
"""
test_discretization_aware_energy_baseline.py
============================================
Unit test suite verifying the governance review synthesis and formalization of the
discretization-aware energy baseline across Packages 76, 113, 114, and 115.

Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Turn: 216
RunId: 3036e9fb-5411-446e-85de-be737029aa01
"""
import os
import sys
import json
import hashlib
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()

class TestDiscretizationAwareEnergyBaseline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.gov_path = os.path.join(REPO_ROOT, "results", "validation", "governance_review_discretization_aware_energy_baseline.json")
        cls.prep_path = os.path.join(REPO_ROOT, "results", "validation", "preparation-3036e9fb-5411-446e-85de-be737029aa01.json")

        if not os.path.exists(cls.gov_path):
            raise unittest.SkipTest(f"Missing governance review artifact: {cls.gov_path}")
        if not os.path.exists(cls.prep_path):
            raise unittest.SkipTest(f"Missing preparation artifact: {cls.prep_path}")

        with open(cls.gov_path, "r") as f:
            cls.gov_data = json.load(f)
        with open(cls.prep_path, "r") as f:
            cls.prep_data = json.load(f)

    def test_01_schema_and_task_identity(self):
        self.assertEqual(self.gov_data["schema"], 1)
        self.assertEqual(self.gov_data["task_id"], "F1597-CORRECT-PACKAGE72-STATE-TRANSFER")
        self.assertEqual(self.gov_data["classification"], "GOVERNANCE_ENERGY_BASELINE_FORMALIZED")
        self.assertEqual(self.gov_data["method_c_gate_status"], "C1_2_STEP2_ENERGY_GATE_FAILED")
        self.assertEqual(self.gov_data["post_hoc_threshold_relaxation"], "REJECTED_BY_POLICY")

        self.assertEqual(self.prep_data["schema"], 1)
        self.assertEqual(self.prep_data["task_id"], "F1597-CORRECT-PACKAGE72-STATE-TRANSFER")
        self.assertEqual(self.prep_data["run_id"], "3036e9fb-5411-446e-85de-be737029aa01")
        self.assertEqual(self.prep_data["status"], "PREPARATION_COMPLETE")
        self.assertTrue(self.prep_data["verification_passed"])
        self.assertGreaterEqual(len(self.prep_data["finding"]), 20)

    def test_02_evidence_hashes_integrity(self):
        for rel_path, expected_hash in self.gov_data["evidence_sources"].items():
            abs_path = os.path.join(REPO_ROOT, rel_path.replace("/", os.sep))
            self.assertTrue(os.path.exists(abs_path), f"Evidence file not found: {abs_path}")
            actual_hash = sha256_file(abs_path)
            self.assertEqual(actual_hash, expected_hash, f"Hash mismatch for {rel_path}: {actual_hash} != {expected_hash}")

    def test_03_package_115_elastic_continuity(self):
        p115 = self.gov_data["predecessor_evidence"]["package_115_direct_transfer"]
        self.assertEqual(p115["job_id"], "1417751.mmaster02")
        self.assertEqual(p115["exit_code"], 0)
        self.assertEqual(p115["cycles"], 7)
        self.assertEqual(p115["healing_violations"], 0)

        # Elastic strain energy virtually identical (-0.153% difference)
        self.assertAlmostEqual(p115["e_elas_diff_pct"], -0.15307, places=3)
        self.assertLess(abs(p115["e_elas_diff_pct"]), 0.20)

        # Global reaction force RF2 continuity (-0.150% difference)
        self.assertAlmostEqual(p115["rf2_diff_pct"], -0.1501, places=3)
        self.assertLess(abs(p115["rf2_diff_pct"]), 0.20)

    def test_04_package_115_fracture_energy_dominance(self):
        p115 = self.gov_data["predecessor_evidence"]["package_115_direct_transfer"]
        # AT2 fracture energy accounts for > 100% of the net energy increase
        self.assertGreater(p115["frac_share_of_excess_pct"], 100.0)
        self.assertAlmostEqual(p115["frac_share_of_excess_pct"], 106.08, places=1)
        self.assertAlmostEqual(p115["e_tot_diff_pct"], 2.0298, places=3)

    def test_05_package_113_and_114_reconciliation(self):
        p113 = self.gov_data["predecessor_evidence"]["package_113_continuation"]
        self.assertEqual(p113["job_id"], "1417682.mmaster02")
        self.assertEqual(p113["exit_code"], 0)
        self.assertEqual(p113["healing_violations"], 0)
        self.assertAlmostEqual(p113["frac_share_of_excess_pct"], 71.98, places=1)
        self.assertEqual(p113["gate_status"], "C1_2_STEP2_ENERGY_GATE_FAILED")

        p114 = self.gov_data["predecessor_evidence"]["package_114_miseseri"]
        self.assertEqual(p114["job_id"], "1417689.mmaster02")
        self.assertEqual(p114["exit_code"], 0)
        self.assertEqual(p114["total_elements"], 4422)
        self.assertEqual(p114["marked_elements"], 284)

    def test_06_governance_baseline_recommendation(self):
        rec = self.gov_data["formalized_energy_baseline"]["governance_recommendation"]
        self.assertIn("C1_2_STEP2_ENERGY_GATE_FAILED", rec["retain_gate_status"])
        self.assertIn("READY_FOR_SUPERVISOR_GOVERNANCE_REVIEW", rec["readiness_for_downstream_remeshing"])

if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""
test_package159_driver_readiness.py

Unit tests for Package 159 driver readiness and active-set audit (Turn 438).
"""

import unittest
import json
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")

class TestPackage159DriverReadiness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from scripts.validation.audit_package159_driver_readiness import run_driver_audit
        cls.audit_path = REPO_ROOT / "results/validation/package159_driver_readiness_audit.json"
        cls.audit_data = run_driver_audit(cls.audit_path)

    def test_audit_passed_and_classified(self):
        self.assertTrue(self.audit_data["verification_passed"])
        self.assertEqual(self.audit_data["status"], "PREPARATION_COMPLETE")
        self.assertEqual(self.audit_data["classification"], "P159_CORRECTED_DRIVER_OFFLINE_VERIFIED")

    def test_driver_comparison_and_clamp_remedy(self):
        dc = self.audit_data["driver_comparison"]
        self.assertIn("prescribed = {n: self.d0[n] for n in active}", dc["r5_p159_clamp_remedy"])
        self.assertLess(dc["healing_unclamped_value"], -1e-6)
        self.assertGreaterEqual(dc["healing_clamped_value"], -1e-6)

    def test_checkpoint_safety_audit(self):
        cs = self.audit_data["checkpoint_safety_audit"]
        self.assertTrue(cs["immediate_commitment_verified"])
        self.assertTrue(cs["atomic_tmp_replace_verified"])
        self.assertTrue(cs["coupled_tolerance_enforced"])
        self.assertTrue(cs["no_commitment_on_failure"])
        self.assertEqual(cs["physical_gates_enforced"]["force_discrepancy_gate_pct"], 5.0)
        self.assertEqual(cs["physical_gates_enforced"]["energy_discrepancy_gate_pct"], 2.0)

    def test_p159_driver_candidate_integrity(self):
        cand = self.audit_data["package159_driver_candidate"]
        self.assertEqual(cand["physical_quads"], 13924)
        self.assertEqual(cand["continuum_nodes"], 14216)
        self.assertEqual(cand["integration_points"], 55696)
        self.assertTrue(cand["frozen_uel_preserved"])

    def test_walltime_scenarios(self):
        ws = self.audit_data["walltime_scenarios"]
        # Inner 1, 3, 10 must be feasible
        self.assertEqual(ws["inner_solves_1"]["feasibility_under_8h_ceiling"], "FEASIBLE")
        self.assertEqual(ws["inner_solves_3"]["feasibility_under_8h_ceiling"], "FEASIBLE")
        self.assertEqual(ws["inner_solves_10"]["feasibility_under_8h_ceiling"], "FEASIBLE")
        self.assertLess(ws["inner_solves_3"]["total_walltime_hours"], 2.0)
        # Inner 20 must exceed 8h ceiling
        self.assertEqual(ws["inner_solves_20"]["feasibility_under_8h_ceiling"], "WALLTIME_CEILING_EXCEEDED")
        self.assertGreater(ws["inner_solves_20"]["total_walltime_hours"], 8.0)

    def test_operation_blockers(self):
        ops = self.audit_data["operation_blocker_status"]
        self.assertEqual(ops["package158_r5"]["status"], "REVIEW_REQUIRED")
        self.assertEqual(ops["package157_r6"]["status"], "PREPARED_FOR_INDEPENDENT_REGISTRATION_REVIEW")
        self.assertEqual(ops["package159"]["status"], "ISOLATED_CANDIDATE_OFFLINE_VERIFIED")

if __name__ == "__main__":
    unittest.main()

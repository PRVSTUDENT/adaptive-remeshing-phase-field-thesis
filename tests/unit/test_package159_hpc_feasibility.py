#!/usr/bin/env python3
"""
test_package159_hpc_feasibility.py

Unit tests for Package 159 HPC feasibility and execution readiness audit.
"""

import unittest
import json
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")

class TestPackage159HPCFeasibility(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from scripts.validation.audit_package159_hpc_feasibility import run_feasibility_audit
        cls.audit_path = REPO_ROOT / "results/validation/package159_hpc_feasibility_analysis.json"
        cls.audit_data = run_feasibility_audit(cls.audit_path)

    def test_audit_passed_and_classified(self):
        self.assertTrue(self.audit_data["verification_passed"])
        self.assertEqual(self.audit_data["status"], "PREPARATION_COMPLETE")
        self.assertEqual(self.audit_data["classification"], "P159_SERIAL_WALLTIME_RISK")

    def test_telemetry_provenance(self):
        tp = self.audit_data["telemetry_provenance"]
        self.assertEqual(tp["job_id"], "1419174.mmaster02")
        self.assertEqual(tp["physical_quads"], 12544)
        self.assertEqual(tp["completed_outer_iterations"], 69)
        self.assertEqual(tp["measured_walltime_seconds"], 25200.0)
        self.assertAlmostEqual(tp["asymptotic_contraction_ratio_rho"], 0.8286, places=3)
        self.assertIn(tp["outer_iterations_to_delta_h_1e6"], (69, 70))

    def test_scaling_projection(self):
        ps = self.audit_data["package159_scaling"]
        self.assertEqual(ps["physical_quads"], 13924)
        self.assertEqual(ps["continuum_nodes"], 14216)
        self.assertAlmostEqual(ps["quad_increase_pct"], 11.0, delta=0.1)
        self.assertLess(ps["projected_memory_gb"], 4.0)
        self.assertGreater(ps["memory_headroom_vs_16gb"], 4.0)

    def test_walltime_regime_comparison(self):
        wf = self.audit_data["walltime_feasibility_analysis"]
        uncorr = wf["uncorrected_regime"]
        corr = wf["corrected_regime"]
        self.assertGreaterEqual(uncorr["total_projected_hours"], 7.9)
        self.assertEqual(uncorr["feasibility_status"], "EXCEEDS_8H_WALLTIME_CEILING")
        self.assertLess(corr["total_projected_hours"], 2.0)
        self.assertEqual(corr["feasibility_status"], "FEASIBLE_WITH_SUBSTANTIAL_HEADROOM")

    def test_operation_registrations(self):
        ops = self.audit_data["operation_registration_status"]
        self.assertEqual(ops["package158_r5"]["status"], "REVIEW_REQUIRED")
        self.assertEqual(ops["package157_r6"]["status"], "PREPARED_FOR_INDEPENDENT_REGISTRATION_REVIEW")
        self.assertEqual(ops["package159"]["status"], "NO_PREEXISTING_EXECUTION_OPERATION")

if __name__ == "__main__":
    unittest.main()

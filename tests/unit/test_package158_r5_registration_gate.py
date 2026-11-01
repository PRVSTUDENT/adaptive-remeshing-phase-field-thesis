#!/usr/bin/env python3
"""
test_package158_r5_registration_gate.py

Unit tests for Package 158 R5 registration gate and preflight audit (Turn 439).
"""

import unittest
import json
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")

class TestPackage158R5RegistrationGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from scripts.validation.audit_package158_r5_registration_gate import run_audit
        cls.audit_path = REPO_ROOT / "results/validation/package158_r5_registration_gate_audit.json"
        cls.audit_data = run_audit(cls.audit_path)

    def test_audit_passed_and_classified(self):
        self.assertTrue(self.audit_data["verification_passed"])
        self.assertEqual(self.audit_data["status"], "PREPARATION_COMPLETE")
        self.assertEqual(self.audit_data["classification"], "P158_R5_REGISTRATION_GATE_IDENTIFIED_PREFLIGHT_VERIFIED")

    def test_prerequisites_verified(self):
        prereqs = self.audit_data["prerequisites_verification"]
        self.assertTrue(prereqs["driver_verified"])
        self.assertTrue(prereqs["production_uel_verified"])
        self.assertTrue(prereqs["donor_displacement_verified"])
        self.assertEqual(prereqs["donor_holding_displacement_uy_mm"], 0.0018503125442191958)
        self.assertEqual(prereqs["resource_allocation"]["cpus"], 1)
        self.assertEqual(prereqs["resource_allocation"]["memory_gb"], 16)
        self.assertEqual(prereqs["resource_allocation"]["walltime_hours"], 8)
        self.assertEqual(prereqs["cluster_preflight"]["preflight_status"], "PASS")
        self.assertEqual(prereqs["cluster_preflight"]["datachecks_verified"], "PASS_BOTH")

    def test_registration_blocker_identified(self):
        diag = self.audit_data["registration_blocker_diagnosis"]
        self.assertEqual(diag["operation_id"], "execute_mode1_package158_c2_0_r5_re_equilibration")
        self.assertEqual(diag["current_registration_status"], "REVIEW_REQUIRED")
        self.assertEqual(diag["current_reviewed_by"], "gemini-antigravity")
        self.assertIn("Self-certification prohibition", diag["root_cause"])
        self.assertIn("maintainer agent Codex", diag["actionable_resolution_route"])

if __name__ == "__main__":
    unittest.main()

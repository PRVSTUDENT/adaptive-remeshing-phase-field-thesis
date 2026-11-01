#!/usr/bin/env python3
"""
Unit test for Turn 446: Package 157 R6 qualification audit and submission blocker analysis.
Verifies scientific independence from Package 158 R5, enforcement of registration gate,
technical prerequisite verification, and submission withholding.
"""

import json
import subprocess
import sys
import unittest
from pathlib import Path

class TestPackage157R6Turn446Qualification(unittest.TestCase):
    def setUp(self):
        self.repo_root = Path(__file__).resolve().parent.parent.parent
        self.audit_script = self.repo_root / "scripts/validation/audit_package157_r6_turn446.py"
        self.turn_id = "6572edcf-3b5f-4dc9-9c75-94e57266482d"

    def test_audit_execution(self):
        result = subprocess.run(
            [sys.executable, str(self.audit_script)],
            cwd=str(self.repo_root),
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0, f"Audit script failed: {result.stderr}")

        prep_path = self.repo_root / f"results/validation/preparation-{self.turn_id}.json"
        self.assertTrue(prep_path.is_file(), f"Missing preparation file: {prep_path}")

        prep_data = json.loads(prep_path.read_text(encoding="utf-8"))
        self.assertEqual(prep_data["schema"], 1)
        self.assertEqual(prep_data["status"], "PREPARATION_COMPLETE")
        self.assertTrue(prep_data["verification_passed"])
        self.assertGreaterEqual(len(prep_data["finding"]), 20)

        # Audit content check
        audit_path = self.repo_root / "results/validation/package157_r6_turn446_audit.json"
        self.assertTrue(audit_path.is_file(), f"Missing audit file: {audit_path}")
        audit = json.loads(audit_path.read_text(encoding="utf-8"))

        # 1. Scientific independence
        self.assertTrue(audit["scientific_independence"]["independent"])

        # 2. Registration gate
        self.assertFalse(audit["registration_gate"]["gate_passed"])
        self.assertEqual(audit["registration_gate"]["registration_status"], "PREPARED_FOR_INDEPENDENT_REGISTRATION_REVIEW")
        self.assertEqual(audit["registration_gate"]["event_status"], "DEFINITION_REVIEW_REQUIRED")

        # 3. Technical qualification
        self.assertTrue(audit["technical_qualification"]["manifest_valid"])
        self.assertTrue(audit["technical_qualification"]["checkpoint_valid"])
        self.assertTrue(audit["technical_qualification"]["resource_limits"]["limits_compliant"])
        self.assertFalse(audit["technical_qualification"]["datachecks_staged"])
        self.assertFalse(audit["technical_qualification"]["technical_preflight_ready"])

        # 4. Submission decision
        self.assertFalse(audit["submission_decision"]["pbs_submitted"])
        self.assertEqual(audit["submission_decision"]["decision"], "SUBMISSION_WITHHELD")

        # 5. Live job status
        self.assertEqual(audit["live_job_status"]["pbs_job_id"], "1419269.mmaster02")
        self.assertEqual(audit["live_job_status"]["scheduler_state"], "RUNNING")
        self.assertGreaterEqual(audit["live_job_status"]["outer_iterations_completed"], 30)

if __name__ == "__main__":
    unittest.main()

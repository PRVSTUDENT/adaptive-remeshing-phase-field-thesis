#!/usr/bin/env python3
"""Unit tests for Package 158 R5 independent maintainer review dispatch audit."""

import sys
import unittest
from pathlib import Path

WORKSPACE = Path("D:/Master thesis/Adaptive remeshing")
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))


class TestPackage158R5IndependentReviewDispatch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from scripts.validation.audit_package158_r5_independent_review_dispatch import run_audit
        out_file = WORKSPACE / "results" / "validation" / "package158_r5_independent_review_dispatch_audit.json"
        cls.audit = run_audit(out_file)

    def test_classification_is_blocked(self):
        self.assertEqual(self.audit["classification"], "INDEPENDENT_MAINTAINER_REGISTRATION_BLOCKED")
        self.assertTrue(self.audit["verification_passed"])

    def test_governance_anti_self_certification(self):
        gov = self.audit["governance_evaluation"]
        self.assertEqual(gov["author"], "gemini-antigravity")
        self.assertEqual(gov["required_maintainer"], "Codex-controller-maintenance")
        self.assertEqual(gov["registration_status"], "REVIEW_REQUIRED")
        self.assertEqual(gov["definition_review_status"], "DEFINITION_REVIEW_REQUIRED")
        self.assertTrue(gov["anti_self_certification_satisfied"])
        self.assertFalse(gov["direct_interagent_invocation_available"])
        self.assertTrue(gov["dispatch_routing_required"])

    def test_technical_readiness_uel_and_displacement(self):
        tech = self.audit["technical_readiness"]
        self.assertTrue(tech["uel_hash_valid"])
        self.assertEqual(tech["uel_sha256"], "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6")
        self.assertTrue(tech["donor_holding_displacement_verified"])
        self.assertTrue(tech["resource_limits_verified"])

    def test_finding_and_next_action(self):
        self.assertGreaterEqual(len(self.audit["finding"]), 20)
        self.assertIn("INDEPENDENT_MAINTAINER_REGISTRATION_BLOCKED", self.audit["finding"])
        self.assertIn("Codex-controller-maintenance", self.audit["next_required_action"])


if __name__ == "__main__":
    unittest.main()

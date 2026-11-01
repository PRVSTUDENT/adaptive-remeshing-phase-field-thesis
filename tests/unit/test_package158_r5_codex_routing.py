#!/usr/bin/env python3
"""Unit tests for Package 158 R5 Codex maintainer routing evaluation."""

import sys
import unittest
from pathlib import Path

WORKSPACE = Path("D:/Master thesis/Adaptive remeshing")
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))


class TestPackage158R5CodexRouting(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from scripts.validation.evaluate_package158_r5_codex_routing import run_evaluation
        out_file = WORKSPACE / "results" / "validation" / "package158_r5_codex_routing_evaluation.json"
        cls.eval_data = run_evaluation(out_file)

    def test_classification_and_verification(self):
        self.assertEqual(self.eval_data["classification"], "INDEPENDENT_REVIEW_DISPATCH_UNAVAILABLE")
        self.assertTrue(self.eval_data["verification_passed"])

    def test_dispatch_inspection_results(self):
        disp = self.eval_data["dispatch_inspection"]
        self.assertFalse(disp["codex_launcher_present"])
        self.assertFalse(disp["interagent_rpc_present"])
        self.assertFalse(disp["supported_internal_routing_available"])
        self.assertEqual(disp["dispatch_outcome"], "INDEPENDENT_REVIEW_DISPATCH_UNAVAILABLE")
        self.assertIn("agy.exe", disp["root_cause_blocker"])

    def test_target_operation_and_review_event(self):
        op = self.eval_data["target_operation"]
        self.assertEqual(op["operation_id"], "execute_mode1_package158_c2_0_r5_re_equilibration")
        self.assertEqual(op["registration_status"], "REVIEW_REQUIRED")
        self.assertEqual(op["definition_review_status"], "DEFINITION_REVIEW_REQUIRED")
        self.assertEqual(op["definition_sha256"], "A00D70991B40FF1140A125D713A9C89DFFB69923EEB33B503D6D0A4C338E3F22")
        self.assertEqual(op["review_event_sha256"], "5353E81E639B6CC84632DF3BF2127BD8E663712982A9585484E4DB6F0A8ED013")

    def test_technical_and_scientific_invariants(self):
        tech = self.eval_data["technical_and_scientific_invariants"]
        self.assertTrue(tech["uel_valid"])
        self.assertEqual(tech["uel_sha256"], "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6")
        self.assertEqual(tech["donor_holding_displacement_uy_mm"], 0.0018503125442191958)
        self.assertIn("d0[n]", tech["falsifiable_correction"])


if __name__ == "__main__":
    unittest.main()

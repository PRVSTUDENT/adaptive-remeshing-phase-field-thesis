#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_matched_history_energy_validation.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Turn: 423
Protocol Version: 2

Unit test suite verifying matched-history energy validation for Method C.
"""

import os
import sys
import json
import unittest
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
sys.path.insert(0, str(REPO_ROOT))

VERIFICATION_JSON = REPO_ROOT / "results/validation/matched_history_energy_validation.json"


class TestMatchedHistoryEnergyValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not VERIFICATION_JSON.exists():
            import scripts.validation.evaluate_matched_history_energy_validation as ev
            ev.evaluate_matched_history()
        with open(str(VERIFICATION_JSON), "r", encoding="utf-8") as f:
            cls.data = json.load(f)

    def test_schema_and_classification(self):
        self.assertEqual(self.data.get("schema"), 1)
        self.assertEqual(self.data.get("task_id"), "F1597-CORRECT-PACKAGE72-STATE-TRANSFER")
        self.assertEqual(self.data.get("turn"), 423)
        self.assertEqual(self.data.get("classification"), "MATCHED_HISTORY_REFERENCE_AVAILABLE")
        self.assertTrue(self.data.get("verification_passed"))

    def test_anchor_reaction_force_gate(self):
        anchor = self.data["anchor_evaluation"]
        disc = anchor["discrepancies"]
        self.assertTrue(disc["rf2_gate_pass"])
        self.assertLess(abs(disc["rf2_diff_pct"]), 5.0)
        self.assertAlmostEqual(disc["rf2_diff_pct"], -0.352, places=2)

    def test_anchor_total_energy_gate(self):
        anchor = self.data["anchor_evaluation"]
        disc = anchor["discrepancies"]
        self.assertTrue(disc["e_total_raw_gate_pass"])
        self.assertLess(abs(disc["e_total_diff_pct"]), 2.0)
        self.assertAlmostEqual(disc["e_total_diff_pct"], 0.130, places=2)

    def test_anchor_component_energies(self):
        anchor = self.data["anchor_evaluation"]
        disc = anchor["discrepancies"]
        self.assertLess(abs(disc["e_elastic_diff_pct"]), 1.0)
        self.assertLess(abs(disc["e_fracture_diff_pct"]), 3.0)

    def test_continuation_step1_gates(self):
        s1 = self.data["continuation_step1_evaluation"]
        disc = s1["discrepancies"]
        self.assertTrue(disc["rf2_gate_pass"])
        self.assertLess(abs(disc["rf2_diff_pct"]), 5.0)
        self.assertAlmostEqual(disc["rf2_diff_pct"], -0.491, places=2)

        self.assertTrue(disc["e_total_raw_gate_pass"])
        self.assertLess(abs(disc["e_total_diff_pct"]), 2.0)
        self.assertAlmostEqual(disc["e_total_diff_pct"], 0.129, places=2)

    def test_work_energy_closure(self):
        inc = self.data["incremental_energy_balance"]
        closure_err_pct = inc["closure_error_relative_pct"]
        self.assertLess(abs(closure_err_pct), 1.0)
        self.assertAlmostEqual(closure_err_pct, 0.520, places=2)

    def test_evidence_sources_hashes(self):
        sources = self.data.get("evidence_sources", {})
        self.assertIn("P146_ENERGY_CSV", sources)
        self.assertIn("P146_DAT_GZ", sources)
        self.assertIn("P146_STA", sources)
        self.assertIn("P146_INP", sources)
        self.assertIn("R3_ENDPOINT_JSON", sources)
        self.assertIn("R3_FULL_HISTORY_JSON", sources)
        for name, h in sources.items():
            self.assertEqual(len(h), 64)


if __name__ == "__main__":
    unittest.main()

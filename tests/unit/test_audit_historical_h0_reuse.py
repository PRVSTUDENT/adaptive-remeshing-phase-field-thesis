#!/usr/bin/env python3
"""
Unit Test Suite for Historical H0 Reuse Audit
Task: F43MODEREF-LINEAGE2
"""

import unittest
from pathlib import Path
from scripts.validation.audit_historical_h0_reuse import audit_h0_reuse, HISTORICAL_DECK_SHA256, HISTORICAL_SRC_SHA256

ROOT = Path(__file__).resolve().parents[2]


class TestAuditHistoricalH0Reuse(unittest.TestCase):

    def test_historical_h0_reuse_audit(self):
        res = audit_h0_reuse()

        self.assertEqual(res["historical_H0_deck_SHA"], HISTORICAL_DECK_SHA256)
        self.assertEqual(res["historical_H0_source_SHA"], HISTORICAL_SRC_SHA256)
        self.assertFalse(res["byte_identical"])
        self.assertTrue(res["scientifically_semantically_equivalent"])
        self.assertEqual(res["uel_source_difference_classification"], "scientifically_identical_implementation_change")
        self.assertTrue(res["historical_H0_reused_for_convergence"])
        self.assertFalse(res["M2REF_H0_requires_new_execution"])


if __name__ == "__main__":
    unittest.main()

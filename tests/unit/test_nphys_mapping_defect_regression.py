#!/usr/bin/env python3
"""Regression Test for Job 1386365 NPHYS History Producer-Consumer Mapping Defect.

Task: F43MODEREF8-NPHYSFIX-PREP1 (Section 10)

This test proves:
1. Defective Fixture (reproducing Job 1386365):
   - true NPHYS = 3930, declared NPHYS_VAL = 1 (default fallback when properties=4)
   - U2 p=1 (JELEM=3931) computes PHYSIDX = 3931 - 1 = 3930 (writes history into slot 3930)
   - U1 p=1 (JELEM=1) computes PHYSIDX = 1 (reads history from slot 1)
   - Notch tip element p=1 index match fails (write slot 3930 != read slot 1)
   - Validator fails closed.

2. Corrected Fixture (M2REF_H0_NPHYSFIX_REPRO):
   - true NPHYS = 3930, declared NPHYS_VAL = 3930 (properties=5 with 5th property 3930.0)
   - U2 p=1 (JELEM=3931) computes PHYSIDX = 3931 - 3930 = 1 (writes history into slot 1)
   - U1 p=1 (JELEM=1) computes PHYSIDX = 1 (reads history from slot 1) -> MATCH!
   - U2 p=1965 (JELEM=5895) computes PHYSIDX = 5895 - 3930 = 1965 (writes history into slot 1965)
   - U1 p=1965 (JELEM=1965) computes PHYSIDX = 1965 (reads history from slot 1965) -> MATCH!
   - U2 p=3930 (JELEM=7860) computes PHYSIDX = 7860 - 3930 = 3930 (writes history into slot 3930)
   - U1 p=3930 (JELEM=3930) computes PHYSIDX = 3930 (reads history from slot 3930) -> MATCH!
   - Validator passes cleanly.
"""

import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.validation.validate_nphys_producer_consumer_contract import audit_deck_nphys


class TestNPHYSProducerConsumerMappingDefect(unittest.TestCase):
    """Test suite for NPHYS history producer-consumer mapping defect regression."""

    def test_defective_h0_mapping_behavior(self):
        """Verify that defective NPHYS_VAL=1 mapping causes write/read mismatch and validator failure."""
        true_nphys = 3930
        defective_nphys_val = 1

        # Physical element p=1 (Notch tip)
        u1_p1_jelem = 1
        u2_p1_jelem = true_nphys + 1  # 3931

        u1_p1_read_slot = u1_p1_jelem  # 1
        u2_p1_write_slot = u2_p1_jelem - defective_nphys_val  # 3931 - 1 = 3930

        # Assert defective values match historical forensic observation
        self.assertEqual(u1_p1_read_slot, 1, "U1 p=1 must read slot 1")
        self.assertEqual(u2_p1_write_slot, 3930, "Defective U2 p=1 must write slot 3930")
        self.assertNotEqual(u1_p1_read_slot, u2_p1_write_slot, "Defective mapping must produce mismatch")

        # Test against historical defective deck M2REF_H0_EXACT_FRACFIX_REPRO.inp
        defective_deck = ROOT / "models/generated/mode_ii/verification_batch/M2REF_H0_EXACT_FRACFIX_REPRO/M2REF_H0_EXACT_FRACFIX_REPRO.inp"
        res = audit_deck_nphys(defective_deck, true_nphys)
        self.assertFalse(res["overall_pass"], "Defective deck must FAIL validator")
        self.assertFalse(res["p1_index_match"], "Defective deck must fail p=1 index match")

    def test_corrected_h0_mapping_behavior(self):
        """Verify that corrected NPHYS_VAL=3930 mapping ensures p->p index identity for p=1, 1965, 3930."""
        true_nphys = 3930
        corrected_nphys_val = 3930

        # p=1 (Notch tip)
        p1_u1_read = 1
        p1_u2_write = (true_nphys + 1) - corrected_nphys_val  # 3931 - 3930 = 1
        self.assertEqual(p1_u1_read, 1)
        self.assertEqual(p1_u2_write, 1)
        self.assertEqual(p1_u1_read, p1_u2_write)

        # p=1965 (Middle)
        p1965_u1_read = 1965
        p1965_u2_write = (true_nphys + 1965) - corrected_nphys_val  # 5895 - 3930 = 1965
        self.assertEqual(p1965_u1_read, 1965)
        self.assertEqual(p1965_u2_write, 1965)
        self.assertEqual(p1965_u1_read, p1965_u2_write)

        # p=3930 (Last element)
        p3930_u1_read = 3930
        p3930_u2_write = (true_nphys + 3930) - corrected_nphys_val  # 7860 - 3930 = 3930
        self.assertEqual(p3930_u1_read, 3930)
        self.assertEqual(p3930_u2_write, 3930)
        self.assertEqual(p3930_u1_read, p3930_u2_write)

        # Test against corrected deck M2REF_H0_NPHYSFIX_REPRO.inp
        corrected_deck = ROOT / "models/generated/mode_ii/verification_batch/M2REF_H0_NPHYSFIX_REPRO/M2REF_H0_NPHYSFIX_REPRO.inp"
        res = audit_deck_nphys(corrected_deck, true_nphys)
        self.assertTrue(res["overall_pass"], "Corrected deck must PASS validator")
        self.assertTrue(res["p1_index_match"], "Corrected deck must pass p=1 index match")
        self.assertTrue(res["pmid_index_match"], "Corrected deck must pass p=mid index match")
        self.assertTrue(res["plast_index_match"], "Corrected deck must pass p=last index match")


if __name__ == "__main__":
    unittest.main()

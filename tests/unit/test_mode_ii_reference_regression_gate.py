#!/usr/bin/env python3
"""Unit tests for validate_mode_ii_reference_regression_gate.py."""

import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.validation.validate_mode_ii_reference_regression_gate import (
    validate_fortran_subroutine,
    validate_deck_structure,
)


class TestReferenceRegressionGate(unittest.TestCase):

    def test_fortran_subroutine_repaired(self):
        """Verify repaired canonical f42_mixed_uel.for passes regression checks."""
        uel_path = ROOT / "models/generated/mode_ii/f42_mixed_element_uel/f42_mixed_uel.for"
        res = validate_fortran_subroutine(uel_path)
        self.assertTrue(res["valid"], f"Subroutine failed validation: {res['errors']}")
        self.assertEqual(len(res["errors"]), 0)

    def test_sdv_producer_ownership_separation(self):
        """Verify SDV14 is produced by Disp UEL and SDV15 is produced by Phase UEL."""
        uel_path = ROOT / "models/generated/mode_ii/f42_mixed_element_uel/f42_mixed_uel.for"
        text = uel_path.read_text(encoding="utf-8")
        
        # Type 1 / 3 Phase UEL must write SDV15
        self.assertIn("USRVAR(PHYSIDX,15,INPT)=PHASE", text)
        
        # Type 2 / 4 Disp UEL must write SDV14 and SDV16
        self.assertIn("USRVAR(PHYSIDX,14,INPT)=PHASE", text)
        self.assertIn("USRVAR(PHYSIDX,16,INPT)=USRVAR(PHYSIDX,13,INPT)", text)

    def test_verification_deck_variable_counts(self):
        """Verify verification deck UEL variable declarations match U1=8, U2=56."""
        deck_path = ROOT / "models/generated/mode_ii/verification_batch/M2REF_ONEEL_FRACFIX_VERIFY/M2REF_ONEEL_FRACFIX_VERIFY.inp"
        res = validate_deck_structure(deck_path)
        self.assertTrue(res["valid"], f"Verification deck failed: {res['errors']}")


if __name__ == "__main__":
    unittest.main()

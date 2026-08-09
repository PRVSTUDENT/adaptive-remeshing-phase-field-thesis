#!/usr/bin/env python3
"""Unit tests for validate_mode_ii_reference_regression_gate.py."""

import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.validation.validate_mode_ii_reference_regression_gate import (
    validate_fortran_subroutine,
)


class TestReferenceRegressionGate(unittest.TestCase):

    def test_fortran_subroutine_repaired(self):
        """Verify repaired canonical f42_mixed_uel.for passes regression checks."""
        uel_path = ROOT / "models/generated/mode_ii/f42_mixed_element_uel/f42_mixed_uel.for"
        res = validate_fortran_subroutine(uel_path)
        self.assertTrue(res["valid"], f"Subroutine failed validation: {res['errors']}")
        self.assertEqual(len(res["errors"]), 0)


if __name__ == "__main__":
    unittest.main()

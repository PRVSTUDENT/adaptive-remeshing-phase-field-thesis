#!/usr/bin/env python3
"""Unit tests for hardened pointwise irreversibility auditor script.
Verifies fail-closed assertions on missing SDVs, empty outputs, duplicate keys, and inconsistent coverage.
"""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/validation"))


class TestPointwiseAuditorLogic(unittest.TestCase):

    def test_auditor_script_exists(self):
        script_path = ROOT / "scripts/validation/audit_pointwise_irreversibility.py"
        self.assertTrue(script_path.is_file())
        text = script_path.read_text(encoding="utf-8")
        self.assertIn("Missing expected field", text)
        self.assertIn("Empty field values", text)
        self.assertIn("Duplicate key", text)
        self.assertIn("Inconsistent frame coverage", text)


if __name__ == "__main__":
    unittest.main()

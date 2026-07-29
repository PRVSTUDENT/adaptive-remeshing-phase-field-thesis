#!/usr/bin/env python3
"""Unit tests for Stage F4 batch orchestrator and static validators."""

import json
import tempfile
import unittest
from pathlib import Path

from scripts.model_generation.build_mode_ii_h2_u020_postpeak import build_package as build_h2
from scripts.model_generation.build_mode_ii_miseseri_corrected_pbs import build_package as build_miseseri
from scripts.validation.validate_mode_ii_h2_u020_postpeak_static import validate as validate_h2
from scripts.validation.validate_mode_ii_miseseri_corrected_pbs_static import validate as validate_miseseri


class TestStageF4BatchOrchestrator(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.h2_dir = Path(self.tmp_dir.name) / "h2_u020"
        self.miseseri_dir = Path(self.tmp_dir.name) / "miseseri_pbs"

        build_h2(self.h2_dir)
        build_miseseri(self.miseseri_dir)

    def tearDown(self) -> None:
        self.tmp_dir.cleanup()

    def test_h2_u020_static_validator_pass(self) -> None:
        res = validate_h2(self.h2_dir)
        self.assertTrue(res["passed"])
        self.assertEqual(res["classification"], "stage_f4_h2_u020_static_pass")

    def test_miseseri_corrected_pbs_static_validator_pass(self) -> None:
        res = validate_miseseri(self.miseseri_dir)
        self.assertTrue(res["passed"])
        self.assertEqual(res["classification"], "stage_f4_miseseri_pbs_static_pass")

    def test_h2_u020_endpoint_audit_verification(self) -> None:
        audit_file = self.h2_dir / "STEP_ENDPOINT_AUDIT.json"
        self.assertTrue(audit_file.is_file())
        audit = json.loads(audit_file.read_text(encoding="utf-8"))
        self.assertTrue(audit["pass"])
        self.assertEqual(audit["calculated_final_u1_mm"], 0.02)
        self.assertEqual(audit["expected_final_u1_mm"], 0.02)
        self.assertEqual(audit["absolute_mismatch_mm"], 0.0)


if __name__ == "__main__":
    unittest.main()

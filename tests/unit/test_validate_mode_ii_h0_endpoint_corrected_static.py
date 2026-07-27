#!/usr/bin/env python3
"""Unit tests for Mode-II H0 endpoint-corrected static validator."""

import tempfile
import unittest
from pathlib import Path

from scripts.model_generation.build_mode_ii_h0_endpoint_corrected_serial import build_package
from scripts.validation.validate_mode_ii_h0_endpoint_corrected_static import validate


class TestValidateModeIIH0EndpointCorrectedStatic(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.pkg_dir = Path(self.tmp_dir.name) / "pkg"
        build_package(self.pkg_dir)

    def tearDown(self) -> None:
        self.tmp_dir.cleanup()

    def test_static_validator_pass(self) -> None:
        result = validate(package_dir=self.pkg_dir)
        self.assertTrue(result["passed"])
        self.assertEqual(
            result["classification"],
            "stage_f_mode_ii_h0_endpoint_corrected_static_pass",
        )

    def test_static_validator_rejects_wrong_endpoint_time(self) -> None:
        deck_path = self.pkg_dir / "ModeII_H0_endpoint_corrected_serial.inp"
        text = deck_path.read_text(encoding="utf-8")
        # Tamper with Amp-2 time endpoint
        text = text.replace("0.2,            0.01", "0.5,            0.01")
        deck_path.write_text(text, encoding="utf-8")

        result = validate(package_dir=self.pkg_dir)
        self.assertFalse(result["passed"])
        self.assertEqual(
            result["classification"],
            "stage_f_mode_ii_h0_endpoint_corrected_static_fail",
        )

    def test_static_validator_rejects_wrong_target_displacement(self) -> None:
        deck_path = self.pkg_dir / "ModeII_H0_endpoint_corrected_serial.inp"
        text = deck_path.read_text(encoding="utf-8")
        # Tamper with target displacement
        text = text.replace("0.2,            0.01", "0.2,           0.007")
        deck_path.write_text(text, encoding="utf-8")

        result = validate(package_dir=self.pkg_dir)
        self.assertFalse(result["passed"])


if __name__ == "__main__":
    unittest.main()

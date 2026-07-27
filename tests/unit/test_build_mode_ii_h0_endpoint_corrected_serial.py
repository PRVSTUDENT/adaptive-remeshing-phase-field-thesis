#!/usr/bin/env python3
"""Unit tests for Mode-II H0 endpoint-corrected serial package generator."""

import tempfile
import unittest
from pathlib import Path

from scripts.model_generation.build_mode_ii_h0_endpoint_corrected_serial import (
    ENDPOINT_AUDIT_REVISION,
    EXPECTED_HISTORICAL_DECK_SHA256,
    EXPECTED_HISTORICAL_FORTRAN_SHA256,
    HISTORICAL_DIR,
    build_package,
    sha256_file,
)


class TestBuildModeIIH0EndpointCorrectedSerial(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.out_dir = Path(self.tmp_dir.name) / "h0_endpoint_corrected_serial"

    def tearDown(self) -> None:
        self.tmp_dir.cleanup()

    def test_build_package_success(self) -> None:
        manifest = build_package(self.out_dir)
        self.assertEqual(
            manifest["classification"],
            "stage_f_mode_ii_h0_endpoint_corrected_package_prepared",
        )
        self.assertTrue(manifest["source_byte_identical_to_historical"])
        self.assertEqual(manifest["endpoint_audit_revision"], ENDPOINT_AUDIT_REVISION)
        self.assertFalse(manifest["execution_authorized"])
        self.assertFalse(manifest["datacheck_authorized"])
        self.assertFalse(manifest["solver_authorized"])

    def test_generator_deterministic(self) -> None:
        dir1 = Path(self.tmp_dir.name) / "run1"
        dir2 = Path(self.tmp_dir.name) / "run2"
        build_package(dir1)
        build_package(dir2)

        deck1_sha = sha256_file(dir1 / "ModeII_H0_endpoint_corrected_serial.inp")
        deck2_sha = sha256_file(dir2 / "ModeII_H0_endpoint_corrected_serial.inp")
        for1_sha = sha256_file(dir1 / "ModeII_H0_endpoint_corrected_serial.for")
        for2_sha = sha256_file(dir2 / "ModeII_H0_endpoint_corrected_serial.for")

        self.assertEqual(deck1_sha, deck2_sha)
        self.assertEqual(for1_sha, for2_sha)

    def test_corrected_fortran_byte_identical(self) -> None:
        build_package(self.out_dir)
        hist_for = HISTORICAL_DIR / "ModeII_H0_serial.for"
        corr_for = self.out_dir / "ModeII_H0_endpoint_corrected_serial.for"
        self.assertEqual(hist_for.read_bytes(), corr_for.read_bytes())

    def test_only_approved_deck_change(self) -> None:
        build_package(self.out_dir)
        hist_deck = (HISTORICAL_DIR / "ModeII_H0_serial.inp").read_text(encoding="utf-8")
        corr_deck = (self.out_dir / "ModeII_H0_endpoint_corrected_serial.inp").read_text(
            encoding="utf-8"
        )
        hist_lines = hist_deck.splitlines()
        corr_lines = corr_deck.splitlines()
        self.assertEqual(len(hist_lines), len(corr_lines))
        diffs = [(i + 1, h, c) for i, (h, c) in enumerate(zip(hist_lines, corr_lines)) if h != c]
        self.assertEqual(len(diffs), 1)
        line_num, old_line, new_line = diffs[0]
        self.assertIn("0.5,            0.01", old_line)
        self.assertIn("0.2,            0.01", new_line)

    def test_amp2_endpoint_matches_step2_period(self) -> None:
        build_package(self.out_dir)
        deck_text = (self.out_dir / "ModeII_H0_endpoint_corrected_serial.inp").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "*Amplitude, name=Amp-2\n             0.,           0.005,             0.2,            0.01",
            deck_text,
        )
        self.assertIn("0.0001, 0.2,", deck_text)

    def test_final_displacement_equals_target(self) -> None:
        manifest = build_package(self.out_dir)
        self.assertEqual(manifest["final_target_u1_mm"], 0.010)

    def test_increment_count_product(self) -> None:
        manifest = build_package(self.out_dir)
        product = manifest["step2_direct_increment"] * manifest["step2_max_inc"]
        self.assertAlmostEqual(product, manifest["step2_period"])

    def test_no_mode_i_reintroduction(self) -> None:
        build_package(self.out_dir)
        deck_text = (self.out_dir / "ModeII_H0_endpoint_corrected_serial.inp").read_text(
            encoding="utf-8"
        )
        self.assertIn("top, 1, 1.", deck_text)
        self.assertIn("RP, 1, 1, 1.", deck_text)
        self.assertNotIn("RP, 2, 2, 1.", deck_text)

    def test_execution_flags_false_by_default(self) -> None:
        manifest = build_package(self.out_dir)
        self.assertFalse(manifest["execution_authorized"])
        self.assertFalse(manifest["datacheck_authorized"])
        self.assertFalse(manifest["solver_authorized"])
        self.assertFalse(manifest["automatic_retry_authorized"])

    def test_generator_rejects_historical_output_path(self) -> None:
        with self.assertRaises(ValueError):
            build_package(HISTORICAL_DIR)


if __name__ == "__main__":
    unittest.main()

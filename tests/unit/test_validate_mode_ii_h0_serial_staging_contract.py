#!/usr/bin/env python3
"""Unit tests reproducing M-090 and validating staging contract logic."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.validation.validate_mode_ii_h0_serial_staging_contract import validate_staging_contract

REAL_PKG_DIR = Path(__file__).resolve().parents[2] / "models" / "generated" / "mode_ii" / "h0_serial"


class TestValidateStagingContract(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        self.pkg_dir = self.root / "models" / "generated" / "mode_ii" / "h0_serial"
        self.pkg_dir.mkdir(parents=True, exist_ok=True)

        self.deck_file = self.pkg_dir / "ModeII_H0_serial.inp"
        self.source_file = self.pkg_dir / "ModeII_H0_serial.for"

        real_deck = REAL_PKG_DIR / "ModeII_H0_serial.inp"
        real_source = REAL_PKG_DIR / "ModeII_H0_serial.for"

        self.deck_file.write_bytes(real_deck.read_bytes())
        self.source_file.write_bytes(real_source.read_bytes())

        self.pbs_file = self.root / "02_mode_ii_h0_serial.pbs"
        self.extractor_file = self.root / "extract_molnar_single_notch.py"
        self.validator_file = self.root / "validate_mode_ii_h0_serial_results.py"

        self.pbs_file.write_text("#PBS script content\n", encoding="utf-8")
        self.extractor_file.write_text("# Extractor content\n", encoding="utf-8")
        self.validator_file.write_text("# Validator content\n", encoding="utf-8")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_passing_dual_deck_staging(self):
        res = validate_staging_contract(
            self.pkg_dir,
            self.pbs_file,
            self.extractor_file,
            self.validator_file,
        )
        self.assertEqual(res["classification"], "stage_f_mode_ii_h0_serial_staging_contract_pass")
        self.assertEqual(res["failures"], [])

    def test_old_m090_filename_mismatch_reproduction(self):
        """Simulates old M-090 bug where original deck file was missing in scratch."""

        def old_staging_logic(scratch: Path):
            # Old logic only created job_deck, omitting original_deck
            job_deck = scratch / "mode_ii_h0_serial.inp"
            job_deck.write_bytes(self.deck_file.read_bytes())

            # Old logic attempted to hash ModeII_H0_serial.inp -> missing!
            orig_deck = scratch / "ModeII_H0_serial.inp"
            deck_sha = ""
            if orig_deck.is_file():
                import hashlib

                deck_sha = hashlib.sha256(orig_deck.read_bytes()).hexdigest()
            return deck_sha

        with tempfile.TemporaryDirectory() as t:
            scratch_path = Path(t)
            deck_sha = old_staging_logic(scratch_path)
            self.assertEqual(deck_sha, "")  # Old logic produced empty hash -> M-090 failure!

    def test_missing_original_deck(self):
        self.deck_file.unlink()
        res = validate_staging_contract(
            self.pkg_dir,
            self.pbs_file,
            self.extractor_file,
            self.validator_file,
        )
        self.assertEqual(res["classification"], "stage_f_mode_ii_h0_serial_staging_contract_fail")
        self.assertTrue(any("frozen package deck missing" in f for f in res["failures"]))

    def test_missing_runtime_dependency(self):
        self.extractor_file.unlink()
        res = validate_staging_contract(
            self.pkg_dir,
            self.pbs_file,
            self.extractor_file,
            self.validator_file,
        )
        self.assertEqual(res["classification"], "stage_f_mode_ii_h0_serial_staging_contract_fail")
        self.assertTrue(any("extractor script missing" in f for f in res["failures"]))

    def test_wrong_frozen_deck_hash(self):
        self.deck_file.write_bytes(b"altered deck content")
        res = validate_staging_contract(
            self.pkg_dir,
            self.pbs_file,
            self.extractor_file,
            self.validator_file,
        )
        self.assertEqual(res["classification"], "stage_f_mode_ii_h0_serial_staging_contract_fail")
        self.assertTrue(any("package deck hash mismatch" in f for f in res["failures"]))

    def test_wrong_source_hash(self):
        self.source_file.write_bytes(b"altered source content")
        res = validate_staging_contract(
            self.pkg_dir,
            self.pbs_file,
            self.extractor_file,
            self.validator_file,
        )
        self.assertEqual(res["classification"], "stage_f_mode_ii_h0_serial_staging_contract_fail")
        self.assertTrue(any("package source hash mismatch" in f for f in res["failures"]))


if __name__ == "__main__":
    unittest.main()

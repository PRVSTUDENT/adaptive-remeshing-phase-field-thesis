#!/usr/bin/env python3
"""Unit tests reproducing M-090/M-091 and validating staging contract logic."""

from __future__ import annotations

import json
import tempfile
import unittest

from pathlib import Path

from scripts.validation.validate_mode_ii_h0_serial_staging_contract import validate_staging_contract
from scripts.validation.verify_mode_ii_h0_runtime_staging import verify_staging

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REAL_PKG_DIR = PROJECT_ROOT / "models" / "generated" / "mode_ii" / "h0_serial"
REAL_PBS_FILE = PROJECT_ROOT / "scripts" / "hpc" / "stage_f" / "02_mode_ii_h0_serial.pbs"
REAL_SUBMIT_FILE = PROJECT_ROOT / "scripts" / "hpc" / "stage_f" / "submit_mode_ii_h0_serial.sh"
REAL_EXTRACTOR_FILE = PROJECT_ROOT / "scripts" / "postprocessing" / "extract_molnar_single_notch.py"
REAL_VALIDATOR_FILE = PROJECT_ROOT / "scripts" / "validation" / "validate_mode_ii_h0_serial_results.py"
REAL_VERIFIER_FILE = PROJECT_ROOT / "scripts" / "validation" / "verify_mode_ii_h0_runtime_staging.py"


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
        self.verifier_file = self.root / "verify_mode_ii_h0_runtime_staging.py"

        self.pbs_file.write_text(REAL_PBS_FILE.read_text(encoding="utf-8"), encoding="utf-8")
        self.extractor_file.write_bytes(REAL_EXTRACTOR_FILE.read_bytes())
        self.validator_file.write_bytes(REAL_VALIDATOR_FILE.read_bytes())
        self.verifier_file.write_bytes(REAL_VERIFIER_FILE.read_bytes())

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_passing_dual_deck_staging(self):
        res = validate_staging_contract(
            self.pkg_dir,
            self.pbs_file,
            self.extractor_file,
            self.validator_file,
            self.verifier_file,
        )
        self.assertEqual(res["classification"], "stage_f_mode_ii_h0_serial_staging_contract_pass")
        self.assertEqual(res["failures"], [])

    def test_old_m090_filename_mismatch_reproduction(self):
        """Simulates old M-090 bug where original deck file was missing in scratch."""

        def old_staging_logic(scratch: Path):
            job_deck = scratch / "mode_ii_h0_serial.inp"
            job_deck.write_bytes(self.deck_file.read_bytes())

            orig_deck = scratch / "ModeII_H0_serial.inp"
            deck_sha = ""
            if orig_deck.is_file():
                import hashlib

                deck_sha = hashlib.sha256(orig_deck.read_bytes()).hexdigest()
            return deck_sha

        with tempfile.TemporaryDirectory() as t:
            scratch_path = Path(t)
            deck_sha = old_staging_logic(scratch_path)
            self.assertEqual(deck_sha, "")

    def test_m091_exact_key_mismatch_regression(self):
        """Reproduces M-091 inline Python KeyError vs new verifier success."""
        fields = [
            "project_revision",
            "deck_sha256",
            "source_sha256",
            "extractor_sha256",
            "validator_sha256",
            "pbs_script_sha256",
        ]
        login_data = {f: "a" * 64 if "sha256" in f else "rev1" for f in fields}
        runtime_data = dict(login_data)

        # 1. Old inline python logic raises KeyError
        matches = {}
        for field in fields:
            l_val = login_data.get(field)
            r_val = runtime_data.get(field)
            matches[field + "_match"] = l_val == r_val and l_val is not None

        with self.assertRaises(KeyError) as ctx:
            _ = matches["deck_hash_match"]
        self.assertIn("deck_hash_match", str(ctx.exception))

        # 2. New verifier succeeds on same data
        with tempfile.TemporaryDirectory() as t:
            tp = Path(t)
            lf = tp / "login.json"
            rf = tp / "runtime.json"
            of = tp / "out.json"
            valid_sha = "a" * 64
            login_data_valid = {
                "classification": "stage_f_mode_ii_h0_login_staging_complete",
                "project_revision": "rev1",
                "deck_sha256": valid_sha,
                "source_sha256": valid_sha,
                "extractor_sha256": valid_sha,
                "validator_sha256": valid_sha,
                "pbs_script_sha256": valid_sha,
                "staging_checker_sha256": valid_sha,
            }
            runtime_data_valid = dict(login_data_valid)
            runtime_data_valid["abaqus_deck_sha256"] = valid_sha

            lf.write_text(json.dumps(login_data_valid), encoding="utf-8")
            rf.write_text(json.dumps(runtime_data_valid), encoding="utf-8")

            rc, res = verify_staging(lf, rf, of)
            self.assertEqual(rc, 0)
            self.assertEqual(res["classification"], "stage_f_mode_ii_h0_runtime_staging_pass")
            self.assertTrue(res["deck_hash_match"])

    def test_pbs_contains_no_inline_manifest_comparison_dictionary(self):
        pbs_text = REAL_PBS_FILE.read_text(encoding="utf-8")
        self.assertNotIn('matches[field + "_match"]', pbs_text)
        self.assertNotIn('matches["deck_hash_match"]', pbs_text)

    def test_pbs_invokes_staged_verifier(self):
        pbs_text = REAL_PBS_FILE.read_text(encoding="utf-8")
        self.assertIn("verify_mode_ii_h0_runtime_staging.py", pbs_text)

    def test_wrapper_stages_and_hashes_verifier(self):
        submit_text = REAL_SUBMIT_FILE.read_text(encoding="utf-8")
        self.assertIn("verify_mode_ii_h0_runtime_staging.py", submit_text)
        self.assertIn("STAGING_CHECKER_SHA", submit_text)
        self.assertIn("staging_checker_sha256", submit_text)

    def test_missing_original_deck(self):
        self.deck_file.unlink()
        res = validate_staging_contract(
            self.pkg_dir,
            self.pbs_file,
            self.extractor_file,
            self.validator_file,
            self.verifier_file,
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
            self.verifier_file,
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
            self.verifier_file,
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
            self.verifier_file,
        )
        self.assertEqual(res["classification"], "stage_f_mode_ii_h0_serial_staging_contract_fail")
        self.assertTrue(any("package source hash mismatch" in f for f in res["failures"]))


if __name__ == "__main__":
    unittest.main()

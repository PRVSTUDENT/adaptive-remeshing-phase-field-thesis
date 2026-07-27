#!/usr/bin/env python3
"""Unit tests for verify_mode_ii_h0_runtime_staging.py."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.validation.verify_mode_ii_h0_runtime_staging import verify_staging

VALID_REV = "46cf420b995ff6b2f74fecfc10fb1bb4411feaac"
VALID_SHA_1 = "32a25380767bbb0e9e76eb55b3bb7a97d78bb75c4f86c7e8585aa2032ce2d33b"
VALID_SHA_2 = "5decf4b1f587019d6bdd904e8ceed22175c113e070e714777cb998da428e4d8c"
VALID_SHA_3 = "b81daedc0c4d018874d1f63c30ccd98e6548d2866b01ca5447f2b13be009db4a"
VALID_SHA_4 = "51a545733c29e79aca3040845bba8510dd002bc2fbeb84830d027760c64f1957"
VALID_SHA_5 = "87cea9cab66153ed8810cac468cc65390477100e305d635420fa9f2c12159f6d"
VALID_SHA_6 = "a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90"


def make_valid_login() -> dict:
    return {
        "classification": "stage_f_mode_ii_h0_login_staging_complete",
        "project_revision": VALID_REV,
        "deck_sha256": VALID_SHA_1,
        "source_sha256": VALID_SHA_2,
        "extractor_sha256": VALID_SHA_3,
        "validator_sha256": VALID_SHA_4,
        "pbs_script_sha256": VALID_SHA_5,
        "staging_checker_sha256": VALID_SHA_6,
        "compute_git_required": False,
    }


def make_valid_runtime() -> dict:
    return {
        "project_revision": VALID_REV,
        "job_name": "mode_ii_h0_serial",
        "cpus": 1,
        "mpi_ranks": 1,
        "omp_threads": 1,
        "mp_mode": "threads",
        "memory": "16 GB",
        "walltime": "04:00:00",
        "deck_sha256": VALID_SHA_1,
        "abaqus_deck_sha256": VALID_SHA_1,
        "source_sha256": VALID_SHA_2,
        "extractor_sha256": VALID_SHA_3,
        "validator_sha256": VALID_SHA_4,
        "pbs_script_sha256": VALID_SHA_5,
        "staging_checker_sha256": VALID_SHA_6,
    }


class TestVerifyModeIIH0RuntimeStaging(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.tmppath = Path(self.tmpdir.name)
        self.login_file = self.tmppath / "login_manifest.json"
        self.runtime_file = self.tmppath / "runtime_manifest.json"
        self.output_file = self.tmppath / "check_result.json"

    def tearDown(self) -> None:
        self.tmpdir.cleanup()

    def write_manifests(self, login_data: dict, runtime_data: dict) -> None:
        self.login_file.write_text(json.dumps(login_data, indent=2), encoding="utf-8")
        self.runtime_file.write_text(json.dumps(runtime_data, indent=2), encoding="utf-8")

    def test_complete_passing_manifests(self) -> None:
        self.write_manifests(make_valid_login(), make_valid_runtime())
        rc, res = verify_staging(self.login_file, self.runtime_file, self.output_file)
        self.assertEqual(rc, 0)
        self.assertEqual(res["classification"], "stage_f_mode_ii_h0_runtime_staging_pass")
        self.assertTrue(res["project_revision_match"])
        self.assertTrue(res["deck_hash_match"])
        self.assertTrue(res["source_hash_match"])
        self.assertTrue(res["extractor_hash_match"])
        self.assertTrue(res["validator_hash_match"])
        self.assertTrue(res["pbs_hash_match"])
        self.assertTrue(res["staging_checker_hash_match"])
        self.assertTrue(res["abaqus_deck_hash_match"])
        self.assertEqual(res["failures"], [])
        self.assertTrue(self.output_file.is_file())

    def test_deck_hash_mismatch(self) -> None:
        rt = make_valid_runtime()
        rt["deck_sha256"] = VALID_SHA_2
        rt["abaqus_deck_sha256"] = VALID_SHA_2
        self.write_manifests(make_valid_login(), rt)
        rc, res = verify_staging(self.login_file, self.runtime_file, self.output_file)
        self.assertEqual(rc, 1)
        self.assertFalse(res["deck_hash_match"])
        self.assertIn("deck_sha256 mismatch", res["failures"][0])

    def test_source_hash_mismatch(self) -> None:
        rt = make_valid_runtime()
        rt["source_sha256"] = VALID_SHA_1
        self.write_manifests(make_valid_login(), rt)
        rc, res = verify_staging(self.login_file, self.runtime_file, self.output_file)
        self.assertEqual(rc, 1)
        self.assertFalse(res["source_hash_match"])

    def test_extractor_hash_mismatch(self) -> None:
        rt = make_valid_runtime()
        rt["extractor_sha256"] = VALID_SHA_1
        self.write_manifests(make_valid_login(), rt)
        rc, res = verify_staging(self.login_file, self.runtime_file, self.output_file)
        self.assertEqual(rc, 1)
        self.assertFalse(res["extractor_hash_match"])

    def test_validator_hash_mismatch(self) -> None:
        rt = make_valid_runtime()
        rt["validator_sha256"] = VALID_SHA_1
        self.write_manifests(make_valid_login(), rt)
        rc, res = verify_staging(self.login_file, self.runtime_file, self.output_file)
        self.assertEqual(rc, 1)
        self.assertFalse(res["validator_hash_match"])

    def test_pbs_hash_mismatch(self) -> None:
        rt = make_valid_runtime()
        rt["pbs_script_sha256"] = VALID_SHA_1
        self.write_manifests(make_valid_login(), rt)
        rc, res = verify_staging(self.login_file, self.runtime_file, self.output_file)
        self.assertEqual(rc, 1)
        self.assertFalse(res["pbs_hash_match"])

    def test_staging_checker_hash_mismatch(self) -> None:
        rt = make_valid_runtime()
        rt["staging_checker_sha256"] = VALID_SHA_1
        self.write_manifests(make_valid_login(), rt)
        rc, res = verify_staging(self.login_file, self.runtime_file, self.output_file)
        self.assertEqual(rc, 1)
        self.assertFalse(res["staging_checker_hash_match"])

    def test_project_revision_mismatch(self) -> None:
        rt = make_valid_runtime()
        rt["project_revision"] = "1234567890abcdef1234567890abcdef12345678"
        self.write_manifests(make_valid_login(), rt)
        rc, res = verify_staging(self.login_file, self.runtime_file, self.output_file)
        self.assertEqual(rc, 1)
        self.assertFalse(res["project_revision_match"])

    def test_missing_required_field(self) -> None:
        lg = make_valid_login()
        del lg["staging_checker_sha256"]
        self.write_manifests(lg, make_valid_runtime())
        rc, res = verify_staging(self.login_file, self.runtime_file, self.output_file)
        self.assertEqual(rc, 1)
        self.assertIn("staging_checker_sha256", res["failures"][0])

    def test_empty_sha_value(self) -> None:
        lg = make_valid_login()
        lg["deck_sha256"] = ""
        rt = make_valid_runtime()
        rt["deck_sha256"] = ""
        self.write_manifests(lg, rt)
        rc, res = verify_staging(self.login_file, self.runtime_file, self.output_file)
        self.assertEqual(rc, 1)
        self.assertTrue(any("not a 64-char hex SHA256" in f for f in res["failures"]))

    def test_invalid_sha_length(self) -> None:
        lg = make_valid_login()
        lg["deck_sha256"] = "abc123"
        rt = make_valid_runtime()
        rt["deck_sha256"] = "abc123"
        self.write_manifests(lg, rt)
        rc, res = verify_staging(self.login_file, self.runtime_file, self.output_file)
        self.assertEqual(rc, 1)
        self.assertTrue(any("not a 64-char hex SHA256" in f for f in res["failures"]))

    def test_invalid_json(self) -> None:
        self.login_file.write_text("{bad json", encoding="utf-8")
        self.runtime_file.write_text(json.dumps(make_valid_runtime()), encoding="utf-8")
        rc, res = verify_staging(self.login_file, self.runtime_file, self.output_file)
        self.assertEqual(rc, 1)
        self.assertTrue(any("Failed to parse" in f for f in res["failures"]))

    def test_missing_login_manifest(self) -> None:
        self.runtime_file.write_text(json.dumps(make_valid_runtime()), encoding="utf-8")
        rc, res = verify_staging(self.login_file, self.runtime_file, self.output_file)
        self.assertEqual(rc, 1)
        self.assertTrue(any("does not exist" in f for f in res["failures"]))

    def test_missing_runtime_manifest(self) -> None:
        self.login_file.write_text(json.dumps(make_valid_login()), encoding="utf-8")
        rc, res = verify_staging(self.login_file, self.runtime_file, self.output_file)
        self.assertEqual(rc, 1)
        self.assertTrue(any("does not exist" in f for f in res["failures"]))

    def test_abaqus_deck_hash_mismatch(self) -> None:
        rt = make_valid_runtime()
        rt["abaqus_deck_sha256"] = VALID_SHA_2
        self.write_manifests(make_valid_login(), rt)
        rc, res = verify_staging(self.login_file, self.runtime_file, self.output_file)
        self.assertEqual(rc, 1)
        self.assertFalse(res["abaqus_deck_hash_match"])
        self.assertTrue(any("abaqus_deck_sha256 mismatch" in f for f in res["failures"]))

    def test_output_directory_missing_or_unwritable(self) -> None:
        self.write_manifests(make_valid_login(), make_valid_runtime())
        out_sub = self.tmppath / "nested" / "sub" / "output.json"
        rc, res = verify_staging(self.login_file, self.runtime_file, out_sub)
        self.assertEqual(rc, 0)
        self.assertTrue(out_sub.is_file())


if __name__ == "__main__":
    unittest.main()

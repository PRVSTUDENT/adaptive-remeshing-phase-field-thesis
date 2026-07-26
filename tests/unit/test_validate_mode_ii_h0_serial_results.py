#!/usr/bin/env python3
"""Unit tests for validate_mode_ii_h0_serial_results.py."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from scripts.validation.validate_mode_ii_h0_serial_results import validate_results


class TestValidateModeIISerialResults(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.ext_dir = self.root / "extracted"
        self.ext_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        self.temp_dir.cleanup()

    def _write_passing_fixture(self):
        # 1. extraction_manifest.json
        (self.ext_dir / "extraction_manifest.json").write_text(
            json.dumps({"classification": "stage_f_extraction_manifest_pass"}), encoding="utf-8"
        )

        # 2. rf1_u1_curve.csv
        with (self.ext_dir / "rf1_u1_curve.csv").open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["step", "frame", "step_time", "rp_u1", "rp_rf1", "max_sdv15", "max_sdv16"])
            w.writerow(["Step-1", "0", "0.0", "0.0", "0.0", "0.0", "0.0"])
            w.writerow(["Step-1", "1", "1.0", "0.010", "150.0", "0.95", "10.0"])

        # 3. energy_history.csv
        with (self.ext_dir / "energy_history.csv").open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["step", "step_time", "variable", "value"])
            w.writerow(["Step-1", "1.0", "ALLSE", "1.234"])

        # 4. irreversibility_summary.json
        (self.ext_dir / "irreversibility_summary.json").write_text(
            json.dumps(
                {
                    "phase_healing_violation_count": 0,
                    "worst_phase_decrease": 0.0,
                    "history_decrease_violation_count": 0,
                    "worst_history_decrease": 0.0,
                    "healing_tolerance": 1e-8,
                    "history_decrease_tolerance": 1e-10,
                }
            ),
            encoding="utf-8",
        )

        # 5. phase_bounds_summary.json
        (self.ext_dir / "phase_bounds_summary.json").write_text(
            json.dumps({"minimum_phase": 0.0, "maximum_phase": 0.95, "values_checked": 100}),
            encoding="utf-8",
        )

        # 6. crack path
        with (self.ext_dir / "crack_path_sdv15_ge_0p5.csv").open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["element", "phase_value"])
            w.writerow(["101", "0.95"])

        # 7. sta / dat / msg
        sta_path = self.root / "mode_ii_h0_serial.sta"
        sta_path.write_text("THE ANALYSIS HAS COMPLETED SUCCESSFULLY", encoding="utf-8")

        dat_path = self.root / "mode_ii_h0_serial.dat"
        dat_path.write_text("JOB TIME SUMMARY", encoding="utf-8")

        msg_path = self.root / "mode_ii_h0_serial.msg"
        msg_path.write_text("STEP 1 COMPLETED", encoding="utf-8")

        # 8. input hash check
        input_hash_check_path = self.root / "input_hash_check.txt"
        input_hash_check_path.write_text("ModeII_H0_serial.inp: OK\nModeII_H0_serial.for: OK\n", encoding="utf-8")

        # 9. login manifest
        login_manifest_path = self.root / "MODE_II_H0_LOGIN_MANIFEST.json"
        login_manifest_path.write_text(
            json.dumps(
                {
                    "project_revision": "rev123",
                    "deck_sha256": "32a25380767bbb0e9e76eb55b3bb7a97d78bb75c4f86c7e8585aa2032ce2d33b",
                    "source_sha256": "5decf4b1f587019d6bdd904e8ceed22175c113e070e714777cb998da428e4d8c",
                    "extractor_sha256": "ext123",
                    "validator_sha256": "val123",
                    "pbs_script_sha256": "pbs123",
                }
            ),
            encoding="utf-8",
        )

        # 10. runtime manifest
        runtime_manifest_path = self.root / "MODE_II_H0_RUNTIME_MANIFEST.json"
        runtime_manifest_path.write_text(
            json.dumps(
                {
                    "project_revision": "rev123",
                    "job_name": "mode_ii_h0_serial",
                    "cpus": 1,
                    "mpi_ranks": 1,
                    "omp_threads": 1,
                    "mp_mode": "threads",
                    "memory": "16 GB",
                    "walltime": "04:00:00",
                    "deck_sha256": "32a25380767bbb0e9e76eb55b3bb7a97d78bb75c4f86c7e8585aa2032ce2d33b",
                    "source_sha256": "5decf4b1f587019d6bdd904e8ceed22175c113e070e714777cb998da428e4d8c",
                    "extractor_sha256": "ext123",
                    "validator_sha256": "val123",
                    "pbs_script_sha256": "pbs123",
                }
            ),
            encoding="utf-8",
        )

        # 11. staging check
        staging_check_path = self.root / "MODE_II_H0_RUNTIME_STAGING_CHECK.json"
        staging_check_path.write_text(
            json.dumps(
                {
                    "classification": "stage_f_mode_ii_h0_runtime_staging_pass",
                    "project_revision_match": True,
                    "deck_hash_match": True,
                    "source_hash_match": True,
                    "extractor_hash_match": True,
                    "validator_hash_match": True,
                    "pbs_hash_match": True,
                    "failures": [],
                }
            ),
            encoding="utf-8",
        )

        return sta_path, dat_path, msg_path, runtime_manifest_path, login_manifest_path, staging_check_path, input_hash_check_path

    def test_complete_passing_fixture(self):
        sta, dat, msg, runtime_manifest, login_manifest, staging_check, input_hash = self._write_passing_fixture()
        res = validate_results(
            self.ext_dir,
            sta_path=sta,
            dat_path=dat,
            msg_path=msg,
            runtime_manifest_path=runtime_manifest,
            login_manifest_path=login_manifest,
            runtime_staging_check_path=staging_check,
            input_hash_check_path=input_hash,
        )
        self.assertEqual(res["classification"], "stage_f_mode_ii_h0_serial_baseline_characterized")
        self.assertEqual(res["failures"], [])

    def test_missing_sta_failure(self):
        sta, dat, msg, runtime, login, staging, input_hash = self._write_passing_fixture()
        sta.unlink()
        res = validate_results(self.ext_dir, sta_path=sta, dat_path=dat, msg_path=msg, runtime_manifest_path=runtime, login_manifest_path=login, runtime_staging_check_path=staging, input_hash_check_path=input_hash)
        self.assertTrue(any(".sta file is missing" in f for f in res["failures"]))

    def test_missing_dat_failure(self):
        sta, dat, msg, runtime, login, staging, input_hash = self._write_passing_fixture()
        dat.unlink()
        res = validate_results(self.ext_dir, sta_path=sta, dat_path=dat, msg_path=msg, runtime_manifest_path=runtime, login_manifest_path=login, runtime_staging_check_path=staging, input_hash_check_path=input_hash)
        self.assertTrue(any(".dat file is missing" in f for f in res["failures"]))

    def test_missing_msg_failure(self):
        sta, dat, msg, runtime, login, staging, input_hash = self._write_passing_fixture()
        msg.unlink()
        res = validate_results(self.ext_dir, sta_path=sta, dat_path=dat, msg_path=msg, runtime_manifest_path=runtime, login_manifest_path=login, runtime_staging_check_path=staging, input_hash_check_path=input_hash)
        self.assertTrue(any(".msg file is missing" in f for f in res["failures"]))

    def test_missing_input_hash_file_failure(self):
        sta, dat, msg, runtime, login, staging, input_hash = self._write_passing_fixture()
        input_hash.unlink()
        res = validate_results(self.ext_dir, sta_path=sta, dat_path=dat, msg_path=msg, runtime_manifest_path=runtime, login_manifest_path=login, runtime_staging_check_path=staging, input_hash_check_path=input_hash)
        self.assertTrue(any("input hash check file is missing" in f for f in res["failures"]))

    def test_input_hash_without_ok_lines_failure(self):
        sta, dat, msg, runtime, login, staging, input_hash = self._write_passing_fixture()
        input_hash.write_text("ModeII_H0_serial.inp: FAILED\n", encoding="utf-8")
        res = validate_results(self.ext_dir, sta_path=sta, dat_path=dat, msg_path=msg, runtime_manifest_path=runtime, login_manifest_path=login, runtime_staging_check_path=staging, input_hash_check_path=input_hash)
        self.assertTrue(any("input hash check missing" in f for f in res["failures"]))

    def test_missing_runtime_manifest_field_failure(self):
        sta, dat, msg, runtime, login, staging, input_hash = self._write_passing_fixture()
        data = json.loads(runtime.read_text(encoding="utf-8"))
        del data["walltime"]
        runtime.write_text(json.dumps(data), encoding="utf-8")
        res = validate_results(self.ext_dir, sta_path=sta, dat_path=dat, msg_path=msg, runtime_manifest_path=runtime, login_manifest_path=login, runtime_staging_check_path=staging, input_hash_check_path=input_hash)
        self.assertTrue(any("runtime manifest missing required field: walltime" in f for f in res["failures"]))

    def test_missing_login_manifest_field_failure(self):
        sta, dat, msg, runtime, login, staging, input_hash = self._write_passing_fixture()
        data = json.loads(login.read_text(encoding="utf-8"))
        del data["extractor_sha256"]
        login.write_text(json.dumps(data), encoding="utf-8")
        res = validate_results(self.ext_dir, sta_path=sta, dat_path=dat, msg_path=msg, runtime_manifest_path=runtime, login_manifest_path=login, runtime_staging_check_path=staging, input_hash_check_path=input_hash)
        self.assertTrue(any("login manifest missing required field: extractor_sha256" in f for f in res["failures"]))

    def test_extractor_hash_mismatch_failure(self):
        sta, dat, msg, runtime, login, staging, input_hash = self._write_passing_fixture()
        data = json.loads(runtime.read_text(encoding="utf-8"))
        data["extractor_sha256"] = "wrong_ext"
        runtime.write_text(json.dumps(data), encoding="utf-8")
        res = validate_results(self.ext_dir, sta_path=sta, dat_path=dat, msg_path=msg, runtime_manifest_path=runtime, login_manifest_path=login, runtime_staging_check_path=staging, input_hash_check_path=input_hash)
        self.assertTrue(any("manifest extractor_sha256 mismatch" in f for f in res["failures"]))

    def test_validator_hash_mismatch_failure(self):
        sta, dat, msg, runtime, login, staging, input_hash = self._write_passing_fixture()
        data = json.loads(runtime.read_text(encoding="utf-8"))
        data["validator_sha256"] = "wrong_val"
        runtime.write_text(json.dumps(data), encoding="utf-8")
        res = validate_results(self.ext_dir, sta_path=sta, dat_path=dat, msg_path=msg, runtime_manifest_path=runtime, login_manifest_path=login, runtime_staging_check_path=staging, input_hash_check_path=input_hash)
        self.assertTrue(any("manifest validator_sha256 mismatch" in f for f in res["failures"]))

    def test_pbs_hash_mismatch_failure(self):
        sta, dat, msg, runtime, login, staging, input_hash = self._write_passing_fixture()
        data = json.loads(runtime.read_text(encoding="utf-8"))
        data["pbs_script_sha256"] = "wrong_pbs"
        runtime.write_text(json.dumps(data), encoding="utf-8")
        res = validate_results(self.ext_dir, sta_path=sta, dat_path=dat, msg_path=msg, runtime_manifest_path=runtime, login_manifest_path=login, runtime_staging_check_path=staging, input_hash_check_path=input_hash)
        self.assertTrue(any("manifest pbs_script_sha256 mismatch" in f for f in res["failures"]))

    def test_revision_mismatch_failure(self):
        sta, dat, msg, runtime, login, staging, input_hash = self._write_passing_fixture()
        data = json.loads(runtime.read_text(encoding="utf-8"))
        data["project_revision"] = "rev999"
        runtime.write_text(json.dumps(data), encoding="utf-8")
        res = validate_results(self.ext_dir, sta_path=sta, dat_path=dat, msg_path=msg, runtime_manifest_path=runtime, login_manifest_path=login, runtime_staging_check_path=staging, input_hash_check_path=input_hash)
        self.assertTrue(any("manifest project_revision mismatch" in f for f in res["failures"]))

    def test_missing_staging_check_file_failure(self):
        sta, dat, msg, runtime, login, staging, input_hash = self._write_passing_fixture()
        staging.unlink()
        res = validate_results(self.ext_dir, sta_path=sta, dat_path=dat, msg_path=msg, runtime_manifest_path=runtime, login_manifest_path=login, runtime_staging_check_path=staging, input_hash_check_path=input_hash)
        self.assertTrue(any("runtime staging check file is missing" in f for f in res["failures"]))

    def test_staging_check_classification_failure(self):
        sta, dat, msg, runtime, login, staging, input_hash = self._write_passing_fixture()
        staging.write_text(json.dumps({"classification": "stage_f_mode_ii_h0_runtime_staging_fail"}), encoding="utf-8")
        res = validate_results(self.ext_dir, sta_path=sta, dat_path=dat, msg_path=msg, runtime_manifest_path=runtime, login_manifest_path=login, runtime_staging_check_path=staging, input_hash_check_path=input_hash)
        self.assertTrue(any("runtime staging check classification failure" in f for f in res["failures"]))

    def test_nan_minimum_phase_failure(self):
        sta, dat, msg, runtime, login, staging, input_hash = self._write_passing_fixture()
        (self.ext_dir / "phase_bounds_summary.json").write_text(
            json.dumps({"minimum_phase": "NaN", "maximum_phase": 0.95, "values_checked": 100}), encoding="utf-8"
        )
        res = validate_results(self.ext_dir, sta_path=sta, dat_path=dat, msg_path=msg, runtime_manifest_path=runtime, login_manifest_path=login, runtime_staging_check_path=staging, input_hash_check_path=input_hash)
        self.assertTrue(any("non-finite minimum_phase" in f for f in res["failures"]))

    def test_nan_maximum_phase_failure(self):
        sta, dat, msg, runtime, login, staging, input_hash = self._write_passing_fixture()
        (self.ext_dir / "phase_bounds_summary.json").write_text(
            json.dumps({"minimum_phase": 0.0, "maximum_phase": "NaN", "values_checked": 100}), encoding="utf-8"
        )
        res = validate_results(self.ext_dir, sta_path=sta, dat_path=dat, msg_path=msg, runtime_manifest_path=runtime, login_manifest_path=login, runtime_staging_check_path=staging, input_hash_check_path=input_hash)
        self.assertTrue(any("non-finite maximum_phase" in f for f in res["failures"]))

    def test_values_checked_zero_failure(self):
        sta, dat, msg, runtime, login, staging, input_hash = self._write_passing_fixture()
        (self.ext_dir / "phase_bounds_summary.json").write_text(
            json.dumps({"minimum_phase": 0.0, "maximum_phase": 0.95, "values_checked": 0}), encoding="utf-8"
        )
        res = validate_results(self.ext_dir, sta_path=sta, dat_path=dat, msg_path=msg, runtime_manifest_path=runtime, login_manifest_path=login, runtime_staging_check_path=staging, input_hash_check_path=input_hash)
        self.assertTrue(any("values_checked must be positive integer" in f for f in res["failures"]))

    def test_missing_irreversibility_key_failure(self):
        sta, dat, msg, runtime, login, staging, input_hash = self._write_passing_fixture()
        (self.ext_dir / "irreversibility_summary.json").write_text(
            json.dumps({"phase_healing_violation_count": 0}), encoding="utf-8"
        )
        res = validate_results(self.ext_dir, sta_path=sta, dat_path=dat, msg_path=msg, runtime_manifest_path=runtime, login_manifest_path=login, runtime_staging_check_path=staging, input_hash_check_path=input_hash)
        self.assertTrue(any("irreversibility_summary.json missing required field" in f for f in res["failures"]))


if __name__ == "__main__":
    unittest.main()

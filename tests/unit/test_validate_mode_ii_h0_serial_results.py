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

        # 8. runtime manifest
        runtime_manifest_path = self.root / "MODE_II_H0_RUNTIME_MANIFEST.json"
        runtime_manifest_path.write_text(
            json.dumps(
                {
                    "cpus": 1,
                    "mpi_ranks": 1,
                    "omp_threads": 1,
                    "mp_mode": "threads",
                    "deck_sha256": "32a25380767bbb0e9e76eb55b3bb7a97d78bb75c4f86c7e8585aa2032ce2d33b",
                    "source_sha256": "5decf4b1f587019d6bdd904e8ceed22175c113e070e714777cb998da428e4d8c",
                }
            ),
            encoding="utf-8",
        )

        return sta_path, dat_path, msg_path, runtime_manifest_path

    def test_complete_passing_fixture(self):
        sta, dat, msg, runtime_manifest = self._write_passing_fixture()
        res = validate_results(
            self.ext_dir,
            sta_path=sta,
            dat_path=dat,
            msg_path=msg,
            runtime_manifest_path=runtime_manifest,
        )
        self.assertEqual(res["classification"], "stage_f_mode_ii_h0_serial_baseline_characterized")
        self.assertEqual(res["failures"], [])

    def test_nan_rf_failure(self):
        sta, dat, msg, runtime_manifest = self._write_passing_fixture()
        with (self.ext_dir / "rf1_u1_curve.csv").open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["step", "frame", "step_time", "rp_u1", "rp_rf1", "max_sdv15", "max_sdv16"])
            w.writerow(["Step-1", "0", "0.0", "0.0", "NaN", "0.0", "0.0"])
            w.writerow(["Step-1", "1", "1.0", "0.010", "150.0", "0.95", "10.0"])
        res = validate_results(self.ext_dir, sta_path=sta, dat_path=dat, msg_path=msg, runtime_manifest_path=runtime_manifest)
        self.assertIn("stage_f_mode_ii_h0_serial_validation_fail", res["classification"])
        self.assertTrue(any("non-finite RF1" in fail for fail in res["failures"]))

    def test_final_displacement_failure(self):
        sta, dat, msg, runtime_manifest = self._write_passing_fixture()
        with (self.ext_dir / "rf1_u1_curve.csv").open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["step", "frame", "step_time", "rp_u1", "rp_rf1", "max_sdv15", "max_sdv16"])
            w.writerow(["Step-1", "0", "0.0", "0.0", "0.0", "0.0", "0.0"])
            w.writerow(["Step-1", "1", "1.0", "0.005", "150.0", "0.95", "10.0"])
        res = validate_results(self.ext_dir, sta_path=sta, dat_path=dat, msg_path=msg, runtime_manifest_path=runtime_manifest)
        self.assertTrue(any("final |U1|" in fail for fail in res["failures"]))

    def test_phase_healing_failure(self):
        sta, dat, msg, runtime_manifest = self._write_passing_fixture()
        (self.ext_dir / "irreversibility_summary.json").write_text(
            json.dumps({"phase_healing_violation_count": 2, "worst_phase_decrease": 0.05}),
            encoding="utf-8",
        )
        res = validate_results(self.ext_dir, sta_path=sta, dat_path=dat, msg_path=msg, runtime_manifest_path=runtime_manifest)
        self.assertTrue(any("phase healing violations" in fail for fail in res["failures"]))

    def test_history_decrease_failure(self):
        sta, dat, msg, runtime_manifest = self._write_passing_fixture()
        (self.ext_dir / "irreversibility_summary.json").write_text(
            json.dumps({"history_decrease_violation_count": 1, "worst_history_decrease": 0.01}),
            encoding="utf-8",
        )
        res = validate_results(self.ext_dir, sta_path=sta, dat_path=dat, msg_path=msg, runtime_manifest_path=runtime_manifest)
        self.assertTrue(any("history decrease violations" in fail for fail in res["failures"]))

    def test_missing_energies_failure(self):
        sta, dat, msg, runtime_manifest = self._write_passing_fixture()
        (self.ext_dir / "energy_history.csv").unlink()
        res = validate_results(self.ext_dir, sta_path=sta, dat_path=dat, msg_path=msg, runtime_manifest_path=runtime_manifest)
        self.assertTrue(any("missing energy_history.csv" in fail for fail in res["failures"]))

    def test_empty_crack_path_failure(self):
        sta, dat, msg, runtime_manifest = self._write_passing_fixture()
        with (self.ext_dir / "crack_path_sdv15_ge_0p5.csv").open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["element", "phase_value"])
        res = validate_results(self.ext_dir, sta_path=sta, dat_path=dat, msg_path=msg, runtime_manifest_path=runtime_manifest)
        self.assertTrue(any("crack-path CSV is empty" in fail for fail in res["failures"]))

    def test_wrong_deck_hash_failure(self):
        sta, dat, msg, runtime_manifest = self._write_passing_fixture()
        runtime_manifest.write_text(
            json.dumps(
                {
                    "cpus": 1,
                    "mpi_ranks": 1,
                    "omp_threads": 1,
                    "mp_mode": "threads",
                    "deck_sha256": "badhash",
                    "source_sha256": "5decf4b1f587019d6bdd904e8ceed22175c113e070e714777cb998da428e4d8c",
                }
            ),
            encoding="utf-8",
        )
        res = validate_results(self.ext_dir, sta_path=sta, dat_path=dat, msg_path=msg, runtime_manifest_path=runtime_manifest)
        self.assertTrue(any("deck hash mismatch" in fail for fail in res["failures"]))

    def test_wrong_cpu_thread_config_failure(self):
        sta, dat, msg, runtime_manifest = self._write_passing_fixture()
        runtime_manifest.write_text(
            json.dumps(
                {
                    "cpus": 4,
                    "mpi_ranks": 1,
                    "omp_threads": 4,
                    "mp_mode": "threads",
                    "deck_sha256": "32a25380767bbb0e9e76eb55b3bb7a97d78bb75c4f86c7e8585aa2032ce2d33b",
                    "source_sha256": "5decf4b1f587019d6bdd904e8ceed22175c113e070e714777cb998da428e4d8c",
                }
            ),
            encoding="utf-8",
        )
        res = validate_results(self.ext_dir, sta_path=sta, dat_path=dat, msg_path=msg, runtime_manifest_path=runtime_manifest)
        self.assertTrue(any("cpus/ranks/threads expected 1/1/1" in fail for fail in res["failures"]))


if __name__ == "__main__":
    unittest.main()

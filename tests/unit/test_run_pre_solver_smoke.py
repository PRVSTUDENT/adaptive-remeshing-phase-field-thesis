#!/usr/bin/env python3
"""Unit tests for run_pre_solver_smoke.py script."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from scripts.validation.run_pre_solver_smoke import run_pre_solver_smoke


class TestRunPreSolverSmoke(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.tmppath = Path(self.tmpdir.name)

        self.project_root = self.tmppath / "repo"
        self.stage_root = self.tmppath / "stage"
        self.scratch_root = self.tmppath / "scratch"
        self.evidence_root = self.tmppath / "evidence"

        self.project_root.mkdir(parents=True, exist_ok=True)
        self.stage_root.mkdir(parents=True, exist_ok=True)
        self.scratch_root.mkdir(parents=True, exist_ok=True)
        self.evidence_root.mkdir(parents=True, exist_ok=True)

        pkg = self.project_root / "models" / "generated" / "mode_ii" / "h0_serial"
        pkg.mkdir(parents=True, exist_ok=True)
        (pkg / "ModeII_H0_serial.inp").write_text("*Heading\n", encoding="utf-8")
        (pkg / "ModeII_H0_serial.for").write_text("C Fortran\n", encoding="utf-8")

        pbs_dir = self.project_root / "scripts" / "hpc" / "stage_f"
        pbs_dir.mkdir(parents=True, exist_ok=True)
        (pbs_dir / "02_mode_ii_h0_serial.pbs").write_text("#!/bin/bash\n", encoding="utf-8")

        post_dir = self.project_root / "scripts" / "postprocessing"
        post_dir.mkdir(parents=True, exist_ok=True)
        (post_dir / "extract_molnar_single_notch.py").write_text("# extractor\n", encoding="utf-8")

        val_dir = self.project_root / "scripts" / "validation"
        val_dir.mkdir(parents=True, exist_ok=True)
        (val_dir / "validate_mode_ii_h0_serial_results.py").write_text("# validator\n", encoding="utf-8")
        (val_dir / "verify_mode_ii_h0_runtime_staging.py").write_text("# verifier\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.tmpdir.cleanup()

    def make_valid_status(self) -> dict:
        return {
            "MODE_II_H0_SERIAL_ok": True,
            "classification": "stage_f_mode_ii_h0_pre_solver_smoke_pass",
            "failures": [],
            "job_id": "manual_f1_j1_r2_preflight",
            "scratch_run": str(self.scratch_root),
            "pre_solver_only": True,
            "module_environment_loaded": False,
            "abaqus_invoked": False,
            "extractor_invoked": False,
            "validator_invoked": False,
            "abaqus_return_code": None,
            "extractor_return_code": None,
            "validator_return_code": None,
            "source_commit": "rev1",
        }

    def make_valid_staging(self) -> dict:
        return {
            "classification": "stage_f_mode_ii_h0_runtime_staging_pass",
            "failures": [],
            "deck_hash_match": True,
            "source_hash_match": True,
            "extractor_hash_match": True,
            "validator_hash_match": True,
            "pbs_hash_match": True,
            "staging_checker_hash_match": True,
            "abaqus_deck_hash_match": True,
        }

    def mock_pbs_execution(
        self,
        returncode: int = 0,
        status_data: dict | None = None,
        staging_data: dict | None = None,
        create_smoke_marker: bool = True,
        create_serial_marker: bool = False,
        create_odb: bool = False,
    ):
        def side_effect(*args, **kwargs):
            if status_data is not None:
                status_file = self.scratch_root / "MODE_II_H0_SERIAL_STATUS.json"
                status_file.write_text(json.dumps(status_data, indent=2), encoding="utf-8")

            if staging_data is not None:
                staging_file = self.scratch_root / "MODE_II_H0_RUNTIME_STAGING_CHECK.json"
                staging_file.write_text(json.dumps(staging_data, indent=2), encoding="utf-8")

            if create_smoke_marker:
                (self.scratch_root / "MODE_II_H0_PRE_SOLVER_SMOKE.ok").touch()

            if create_serial_marker:
                (self.scratch_root / "MODE_II_H0_SERIAL.ok").touch()

            if create_odb:
                (self.scratch_root / "test.odb").write_bytes(b"dummy odb")

            res = MagicMock()
            res.returncode = returncode
            return res

        return side_effect

    @patch("subprocess.run")
    def test_successful_local_smoke(self, mock_run) -> None:
        mock_run.side_effect = self.mock_pbs_execution(
            returncode=0,
            status_data=self.make_valid_status(),
            staging_data=self.make_valid_staging(),
        )

        rc, summary = run_pre_solver_smoke(
            project_root=self.project_root,
            stage_root=self.stage_root,
            scratch_root=self.scratch_root,
            evidence_root=self.evidence_root,
            project_revision="rev1",
            allow_no_modules=True,
        )
        self.assertEqual(rc, 0)
        self.assertEqual(summary["classification"], "stage_f_mode_ii_h0_pre_solver_smoke_pass")
        self.assertTrue(summary["status_classification_pass"])
        self.assertTrue(summary["runtime_staging_classification_pass"])
        self.assertEqual(summary["failures"], [])

    @patch("subprocess.run")
    def test_pbs_nonzero_exit_fails(self, mock_run) -> None:
        mock_run.side_effect = self.mock_pbs_execution(
            returncode=5,
            status_data=self.make_valid_status(),
            staging_data=self.make_valid_staging(),
        )

        rc, summary = run_pre_solver_smoke(
            project_root=self.project_root,
            stage_root=self.stage_root,
            scratch_root=self.scratch_root,
            evidence_root=self.evidence_root,
            project_revision="rev1",
            allow_no_modules=True,
        )
        self.assertEqual(rc, 1)
        self.assertEqual(summary["classification"], "stage_f_mode_ii_h0_pre_solver_smoke_fail")
        self.assertTrue(any("nonzero exit code: 5" in f for f in summary["failures"]))

    @patch("subprocess.run")
    def test_missing_status_file_fails(self, mock_run) -> None:
        mock_run.side_effect = self.mock_pbs_execution(
            returncode=0,
            status_data=None,
            staging_data=self.make_valid_staging(),
        )

        rc, summary = run_pre_solver_smoke(
            project_root=self.project_root,
            stage_root=self.stage_root,
            scratch_root=self.scratch_root,
            evidence_root=self.evidence_root,
            project_revision="rev1",
            allow_no_modules=True,
        )
        self.assertEqual(rc, 1)
        self.assertTrue(any("Status file missing" in f for f in summary["failures"]))

    @patch("subprocess.run")
    def test_wrong_status_classification_fails(self, mock_run) -> None:
        st = self.make_valid_status()
        st["classification"] = "stage_f_mode_ii_h0_serial_env_fail"
        mock_run.side_effect = self.mock_pbs_execution(
            returncode=0,
            status_data=st,
            staging_data=self.make_valid_staging(),
        )

        rc, summary = run_pre_solver_smoke(
            project_root=self.project_root,
            stage_root=self.stage_root,
            scratch_root=self.scratch_root,
            evidence_root=self.evidence_root,
            project_revision="rev1",
            allow_no_modules=True,
        )
        self.assertEqual(rc, 1)
        self.assertTrue(any("Unexpected status classification" in f for f in summary["failures"]))

    @patch("subprocess.run")
    def test_missing_staging_check_file_fails(self, mock_run) -> None:
        mock_run.side_effect = self.mock_pbs_execution(
            returncode=0,
            status_data=self.make_valid_status(),
            staging_data=None,
        )

        rc, summary = run_pre_solver_smoke(
            project_root=self.project_root,
            stage_root=self.stage_root,
            scratch_root=self.scratch_root,
            evidence_root=self.evidence_root,
            project_revision="rev1",
            allow_no_modules=True,
        )
        self.assertEqual(rc, 1)
        self.assertTrue(any("Staging check file missing" in f for f in summary["failures"]))

    @patch("subprocess.run")
    def test_staging_check_failure_fails(self, mock_run) -> None:
        stg = self.make_valid_staging()
        stg["classification"] = "stage_f_mode_ii_h0_runtime_staging_fail"
        stg["failures"] = ["deck mismatch"]
        mock_run.side_effect = self.mock_pbs_execution(
            returncode=0,
            status_data=self.make_valid_status(),
            staging_data=stg,
        )

        rc, summary = run_pre_solver_smoke(
            project_root=self.project_root,
            stage_root=self.stage_root,
            scratch_root=self.scratch_root,
            evidence_root=self.evidence_root,
            project_revision="rev1",
            allow_no_modules=True,
        )
        self.assertEqual(rc, 1)
        self.assertTrue(any("Unexpected staging classification" in f for f in summary["failures"]))

    @patch("subprocess.run")
    def test_nonempty_staging_failures_fails(self, mock_run) -> None:
        stg = self.make_valid_staging()
        stg["failures"] = ["some error"]
        mock_run.side_effect = self.mock_pbs_execution(
            returncode=0,
            status_data=self.make_valid_status(),
            staging_data=stg,
        )

        rc, summary = run_pre_solver_smoke(
            project_root=self.project_root,
            stage_root=self.stage_root,
            scratch_root=self.scratch_root,
            evidence_root=self.evidence_root,
            project_revision="rev1",
            allow_no_modules=True,
        )
        self.assertEqual(rc, 1)
        self.assertTrue(any("Staging failure: some error" in f for f in summary["failures"]))

    @patch("subprocess.run")
    def test_abaqus_invoked_flag_causes_failure(self, mock_run) -> None:
        st = self.make_valid_status()
        st["abaqus_invoked"] = True
        mock_run.side_effect = self.mock_pbs_execution(
            returncode=0,
            status_data=st,
            staging_data=self.make_valid_staging(),
        )

        rc, summary = run_pre_solver_smoke(
            project_root=self.project_root,
            stage_root=self.stage_root,
            scratch_root=self.scratch_root,
            evidence_root=self.evidence_root,
            project_revision="rev1",
            allow_no_modules=True,
        )
        self.assertEqual(rc, 1)
        self.assertTrue(any("Abaqus was reported as invoked" in f for f in summary["failures"]))

    @patch("subprocess.run")
    def test_odb_presence_causes_failure(self, mock_run) -> None:
        mock_run.side_effect = self.mock_pbs_execution(
            returncode=0,
            status_data=self.make_valid_status(),
            staging_data=self.make_valid_staging(),
            create_odb=True,
        )

        rc, summary = run_pre_solver_smoke(
            project_root=self.project_root,
            stage_root=self.stage_root,
            scratch_root=self.scratch_root,
            evidence_root=self.evidence_root,
            project_revision="rev1",
            allow_no_modules=True,
        )
        self.assertEqual(rc, 1)
        self.assertTrue(any("Found 1 .odb files" in f for f in summary["failures"]))

    @patch("subprocess.run")
    def test_missing_smoke_marker_fails(self, mock_run) -> None:
        mock_run.side_effect = self.mock_pbs_execution(
            returncode=0,
            status_data=self.make_valid_status(),
            staging_data=self.make_valid_staging(),
            create_smoke_marker=False,
        )

        rc, summary = run_pre_solver_smoke(
            project_root=self.project_root,
            stage_root=self.stage_root,
            scratch_root=self.scratch_root,
            evidence_root=self.evidence_root,
            project_revision="rev1",
            allow_no_modules=True,
        )
        self.assertEqual(rc, 1)
        self.assertTrue(any("Smoke marker file missing" in f for f in summary["failures"]))

    @patch("subprocess.run")
    def test_full_solver_serial_marker_causes_failure(self, mock_run) -> None:
        mock_run.side_effect = self.mock_pbs_execution(
            returncode=0,
            status_data=self.make_valid_status(),
            staging_data=self.make_valid_staging(),
            create_serial_marker=True,
        )

        rc, summary = run_pre_solver_smoke(
            project_root=self.project_root,
            stage_root=self.stage_root,
            scratch_root=self.scratch_root,
            evidence_root=self.evidence_root,
            project_revision="rev1",
            allow_no_modules=True,
        )
        self.assertEqual(rc, 1)
        self.assertTrue(any("Full solver completion marker improperly created" in f for f in summary["failures"]))


if __name__ == "__main__":
    unittest.main()

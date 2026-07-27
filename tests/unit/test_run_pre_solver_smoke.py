#!/usr/bin/env python3
"""Unit tests for run_pre_solver_smoke.py script."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from scripts.validation.run_pre_solver_smoke import (
    main,
    run_pre_solver_smoke,
    sha256_file,
    verify_evidence_bundle,
)


class TestRunPreSolverSmoke(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.tmppath = Path(self.tmpdir.name)

        self.project_root = self.tmppath / "repo"
        self.stage_root = self.tmppath / "stage"
        self.scratch_root = self.tmppath / "scratch"
        self.evidence_root = self.tmppath / "evidence"
        self.bundle_dir = self.tmppath / "bundle"

        self.project_root.mkdir(parents=True, exist_ok=True)
        self.stage_root.mkdir(parents=True, exist_ok=True)
        self.scratch_root.mkdir(parents=True, exist_ok=True)
        self.evidence_root.mkdir(parents=True, exist_ok=True)
        self.bundle_dir.mkdir(parents=True, exist_ok=True)

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
            "classification": "stage_f_mode_ii_h0_pre_solver_smoke_pass",
            "pre_solver_smoke_ok": True,
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
        create_runtime_manifest: bool = True,
        create_smoke_marker: bool = True,
        create_serial_marker: bool = False,
        create_odb: bool = False,
        executables_text: str = "/syscomp/abaqus/2023/Commands/abaqus\n/usr/bin/python3\n",
        stdout_text: str = "pbs stdout mock log\n",
        stderr_text: str = "pbs stderr mock log\n",
    ):
        def side_effect(*args, **kwargs):
            if status_data is not None:
                status_file = self.scratch_root / "MODE_II_H0_SERIAL_STATUS.json"
                status_file.write_text(json.dumps(status_data, indent=2), encoding="utf-8")

            if staging_data is not None:
                staging_file = self.scratch_root / "MODE_II_H0_RUNTIME_STAGING_CHECK.json"
                staging_file.write_text(json.dumps(staging_data, indent=2), encoding="utf-8")

            if create_runtime_manifest:
                (self.scratch_root / "MODE_II_H0_RUNTIME_MANIFEST.json").write_text(
                    json.dumps({"classification": "stage_f_mode_ii_h0_runtime_manifest_complete"}),
                    encoding="utf-8",
                )

            if create_smoke_marker:
                (self.scratch_root / "MODE_II_H0_PRE_SOLVER_SMOKE.ok").write_text(
                    "PRE_SOLVER_SMOKE_OK\n", encoding="utf-8"
                )

            if create_serial_marker:
                (self.scratch_root / "MODE_II_H0_SERIAL.ok").touch()

            if create_odb:
                (self.scratch_root / "test.odb").write_bytes(b"dummy odb")

            (self.scratch_root / "executables.txt").write_text(executables_text, encoding="utf-8")

            res = MagicMock()
            res.returncode = returncode
            res.stdout = stdout_text
            res.stderr = stderr_text
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
            evidence_output_dir=self.bundle_dir,
        )
        self.assertEqual(rc, 0)
        self.assertEqual(summary["classification"], "stage_f_mode_ii_h0_pre_solver_smoke_pass")
        self.assertTrue(summary["status_classification_pass"])
        self.assertTrue(summary["pre_solver_smoke_ok"])
        self.assertTrue(summary["runtime_staging_classification_pass"])
        self.assertEqual(summary["failures"], [])

    @patch("subprocess.run")
    def test_smoke_status_has_no_serial_ok_field(self, mock_run) -> None:
        st = self.make_valid_status()
        st["MODE_II_H0_SERIAL_ok"] = True
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
        self.assertTrue(any("MODE_II_H0_SERIAL_ok is improperly present" in f for f in summary["failures"]))

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

    @patch("subprocess.run")
    def test_non_null_return_codes_cause_failure(self, mock_run) -> None:
        st = self.make_valid_status()
        st["abaqus_return_code"] = 0
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
        self.assertTrue(any("abaqus_return_code must be null" in f for f in summary["failures"]))

    @patch("subprocess.run")
    def test_bundle_manifest_generation_stdout_stderr_captured(self, mock_run) -> None:
        mock_run.side_effect = self.mock_pbs_execution(
            returncode=0,
            status_data=self.make_valid_status(),
            staging_data=self.make_valid_staging(),
            stdout_text="captured stdout content",
            stderr_text="captured stderr content",
        )

        rc, summary = run_pre_solver_smoke(
            project_root=self.project_root,
            stage_root=self.stage_root,
            scratch_root=self.scratch_root,
            evidence_root=self.evidence_root,
            project_revision="rev1",
            allow_no_modules=True,
            evidence_output_dir=self.bundle_dir,
        )
        self.assertEqual(rc, 0)
        self.assertEqual((self.bundle_dir / "stdout.log").read_text(encoding="utf-8"), "captured stdout content")
        self.assertEqual((self.bundle_dir / "stderr.log").read_text(encoding="utf-8"), "captured stderr content")

        manifest_path = self.bundle_dir / "EVIDENCE_BUNDLE_MANIFEST.json"
        self.assertTrue(manifest_path.is_file())
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["classification"], "stage_f_mode_ii_h0_pre_solver_smoke_evidence_complete")

        required_files = [
            "SMOKE_COMMAND.json",
            "SMOKE_SUMMARY.json",
            "MODE_II_H0_SERIAL_STATUS.json",
            "MODE_II_H0_RUNTIME_MANIFEST.json",
            "MODE_II_H0_RUNTIME_STAGING_CHECK.json",
            "MODE_II_H0_LOGIN_MANIFEST.json",
            "executables.txt",
            "stdout.log",
            "stderr.log",
            "file_inventory.json",
            "MODE_II_H0_PRE_SOLVER_SMOKE.ok",
        ]
        for rf in required_files:
            self.assertIn(rf, manifest["files"])

        cmd_path = self.bundle_dir / "SMOKE_COMMAND.json"
        cmd = json.loads(cmd_path.read_text(encoding="utf-8"))
        self.assertIn("requested_scratch_root", cmd)
        self.assertIn("resolved_scratch_root", cmd)

        inv_path = self.bundle_dir / "file_inventory.json"
        inv = json.loads(inv_path.read_text(encoding="utf-8"))
        self.assertEqual(inv["odb_file_count"], 0)

    @patch("subprocess.run")
    def test_verify_evidence_bundle_rejects_tampered_bundle(self, mock_run) -> None:
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
            evidence_output_dir=self.bundle_dir,
        )
        self.assertEqual(rc, 0)

        # Tamper with executables.txt after runner finished
        (self.bundle_dir / "executables.txt").write_text("tampered text", encoding="utf-8")

        # Verify using verify_evidence_bundle
        ver_rc, ver_result = verify_evidence_bundle(self.bundle_dir)
        self.assertNotEqual(ver_rc, 0)
        self.assertTrue(ver_result["failures"])
        self.assertEqual(ver_result["classification"], "stage_f_mode_ii_h0_pre_solver_smoke_evidence_fail")

    @patch("subprocess.run")
    def test_cluster_qualification_requires_modules_and_abaqus(self, mock_run) -> None:
        st = self.make_valid_status()
        st["module_environment_loaded"] = False
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
            allow_no_modules=False,  # Cluster qualification mode
        )
        self.assertEqual(rc, 1)
        self.assertTrue(
            any(
                "Cluster qualification requires module_environment_loaded = true" in f
                for f in summary["failures"]
            )
        )

    @patch("subprocess.run")
    def test_main_preserves_unresolved_cli_path_strings(self, mock_run) -> None:
        mock_run.side_effect = self.mock_pbs_execution(
            returncode=0,
            status_data=self.make_valid_status(),
            staging_data=self.make_valid_staging(),
        )
        raw_scratch = str(self.scratch_root)

        with patch(
            "sys.argv",
            [
                "run_pre_solver_smoke.py",
                "--project-root",
                str(self.project_root),
                "--scratch-root",
                raw_scratch,
                "--allow-no-modules",
                "--evidence-output-dir",
                str(self.bundle_dir),
            ],
        ):
            main_rc = main()
            self.assertEqual(main_rc, 0)

        cmd_path = self.bundle_dir / "SMOKE_COMMAND.json"
        cmd = json.loads(cmd_path.read_text(encoding="utf-8"))
        self.assertEqual(cmd["requested_scratch_root"], raw_scratch)

    @patch("subprocess.run")
    def test_missing_status_source_artifact_causes_nonzero_return(self, mock_run) -> None:
        mock_run.side_effect = self.mock_pbs_execution(
            returncode=0,
            status_data=None,  # Do not create status file
            staging_data=self.make_valid_staging(),
        )

        rc, summary = run_pre_solver_smoke(
            project_root=self.project_root,
            stage_root=self.stage_root,
            scratch_root=self.scratch_root,
            evidence_root=self.evidence_root,
            project_revision="rev1",
            allow_no_modules=True,
            evidence_output_dir=self.bundle_dir,
        )
        self.assertEqual(rc, 1)
        self.assertTrue(any("Status file missing" in f for f in summary["failures"]))

    @patch("subprocess.run")
    def test_missing_runtime_manifest_causes_nonzero_return(self, mock_run) -> None:
        mock_run.side_effect = self.mock_pbs_execution(
            returncode=0,
            status_data=self.make_valid_status(),
            staging_data=self.make_valid_staging(),
            create_runtime_manifest=False,
        )

        rc, summary = run_pre_solver_smoke(
            project_root=self.project_root,
            stage_root=self.stage_root,
            scratch_root=self.scratch_root,
            evidence_root=self.evidence_root,
            project_revision="rev1",
            allow_no_modules=True,
            evidence_output_dir=self.bundle_dir,
        )
        self.assertEqual(rc, 1)
        self.assertFalse((self.bundle_dir / "MODE_II_H0_RUNTIME_MANIFEST.json").exists())

    @patch("subprocess.run")
    def test_required_missing_file_is_not_replaced_by_empty_placeholder(self, mock_run) -> None:
        mock_run.side_effect = self.mock_pbs_execution(
            returncode=0,
            status_data=self.make_valid_status(),
            staging_data=self.make_valid_staging(),
            create_runtime_manifest=False,
        )

        rc, summary = run_pre_solver_smoke(
            project_root=self.project_root,
            stage_root=self.stage_root,
            scratch_root=self.scratch_root,
            evidence_root=self.evidence_root,
            project_revision="rev1",
            allow_no_modules=True,
            evidence_output_dir=self.bundle_dir,
        )
        self.assertEqual(rc, 1)
        missing_file = self.bundle_dir / "MODE_II_H0_RUNTIME_MANIFEST.json"
        self.assertFalse(missing_file.exists())

    @patch("subprocess.run")
    def test_verify_evidence_bundle_passes_valid_bundle(self, mock_run) -> None:
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
            evidence_output_dir=self.bundle_dir,
        )
        self.assertEqual(rc, 0)

        ver_rc, ver_result = verify_evidence_bundle(self.bundle_dir)
        self.assertEqual(ver_rc, 0)
        self.assertEqual(ver_result["classification"], "stage_f_mode_ii_h0_pre_solver_smoke_evidence_complete")
        self.assertEqual(ver_result["failures"], [])

    @patch("subprocess.run")
    def test_verify_evidence_bundle_rejects_absent_listed_file(self, mock_run) -> None:
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
            evidence_output_dir=self.bundle_dir,
        )
        self.assertEqual(rc, 0)

        os.remove(self.bundle_dir / "executables.txt")
        ver_rc, ver_result = verify_evidence_bundle(self.bundle_dir)
        self.assertEqual(ver_rc, 1)
        self.assertTrue(any("Listed bundle file missing from disk" in f for f in ver_result["failures"]))

    @patch("subprocess.run")
    def test_verify_evidence_bundle_rejects_unlisted_required_file(self, mock_run) -> None:
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
            evidence_output_dir=self.bundle_dir,
        )
        self.assertEqual(rc, 0)

        manifest_path = self.bundle_dir / "EVIDENCE_BUNDLE_MANIFEST.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        del manifest["files"]["MODE_II_H0_PRE_SOLVER_SMOKE.ok"]
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        ver_rc, ver_result = verify_evidence_bundle(self.bundle_dir)
        self.assertEqual(ver_rc, 1)
        self.assertTrue(any("Required bundle file missing from manifest" in f for f in ver_result["failures"]))

    @patch("subprocess.run")
    def test_verify_evidence_bundle_rejects_malformed_sha(self, mock_run) -> None:
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
            evidence_output_dir=self.bundle_dir,
        )
        self.assertEqual(rc, 0)

        manifest_path = self.bundle_dir / "EVIDENCE_BUNDLE_MANIFEST.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["files"]["executables.txt"] = "invalid_sha"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        ver_rc, ver_result = verify_evidence_bundle(self.bundle_dir)
        self.assertEqual(ver_rc, 1)
        self.assertTrue(any("Invalid SHA-256 format" in f for f in ver_result["failures"]))

    @patch("subprocess.run")
    def test_verify_evidence_bundle_rejects_nonempty_manifest_failures(self, mock_run) -> None:
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
            evidence_output_dir=self.bundle_dir,
        )
        self.assertEqual(rc, 0)

        manifest_path = self.bundle_dir / "EVIDENCE_BUNDLE_MANIFEST.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["failures"] = ["Staging check failed"]
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        ver_rc, ver_result = verify_evidence_bundle(self.bundle_dir)
        self.assertEqual(ver_rc, 1)
        self.assertTrue(any("Manifest contains non-empty failures" in f for f in ver_result["failures"]))

    @patch("subprocess.run")
    def test_pre_solver_marker_included_and_serial_marker_absence_recorded(self, mock_run) -> None:
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
            evidence_output_dir=self.bundle_dir,
        )
        self.assertEqual(rc, 0)
        self.assertTrue(summary["pre_solver_marker_present"])
        self.assertTrue(summary["serial_solver_marker_absent"])

        manifest_path = self.bundle_dir / "EVIDENCE_BUNDLE_MANIFEST.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertTrue(manifest["pre_solver_marker_present"])
        self.assertTrue(manifest["serial_solver_marker_absent"])
        self.assertIn("MODE_II_H0_PRE_SOLVER_SMOKE.ok", manifest["files"])
        self.assertNotIn("MODE_II_H0_SERIAL.ok", manifest["files"])


if __name__ == "__main__":
    unittest.main()

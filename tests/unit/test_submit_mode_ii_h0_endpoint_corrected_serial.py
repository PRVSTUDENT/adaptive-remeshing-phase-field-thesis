#!/usr/bin/env python3
"""Unit tests for submit_mode_ii_h0_endpoint_corrected_serial.sh guarded submission wrapper."""

from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest


def to_wsl_path(p: pathlib.Path) -> str:
    path_str = p.resolve().as_posix()
    if len(path_str) > 1 and path_str[1] == ":":
        drive = path_str[0].lower()
        return f"/mnt/{drive}{path_str[2:]}"
    return path_str


class TestSubmitModeIIH0EndpointCorrectedSerial(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp_dir.name)

        # Copy original package, configs, and scripts to mock repo
        self.pkg_dir = self.root / "models/generated/mode_ii/h0_endpoint_corrected_serial"
        self.pkg_dir.mkdir(parents=True, exist_ok=True)
        real_pkg = pathlib.Path("models/generated/mode_ii/h0_endpoint_corrected_serial")
        shutil.copy(real_pkg / "ModeII_H0_endpoint_corrected_serial.inp", self.pkg_dir / "ModeII_H0_endpoint_corrected_serial.inp")
        shutil.copy(real_pkg / "ModeII_H0_endpoint_corrected_serial.for", self.pkg_dir / "ModeII_H0_endpoint_corrected_serial.for")

        self.scripts_dir = self.root / "scripts/hpc/stage_f"
        self.scripts_dir.mkdir(parents=True, exist_ok=True)
        real_scripts = pathlib.Path("scripts/hpc/stage_f")
        shutil.copy(real_scripts / "04_mode_ii_h0_endpoint_corrected_serial.pbs", self.scripts_dir / "04_mode_ii_h0_endpoint_corrected_serial.pbs")
        shutil.copy(real_scripts / "submit_mode_ii_h0_endpoint_corrected_serial.sh", self.scripts_dir / "submit_mode_ii_h0_endpoint_corrected_serial.sh")

        # Copy required runtime scripts
        (self.root / "scripts/postprocessing").mkdir(parents=True, exist_ok=True)
        (self.root / "scripts/validation").mkdir(parents=True, exist_ok=True)
        (self.root / "configs/studies").mkdir(parents=True, exist_ok=True)

        shutil.copy(pathlib.Path("scripts/postprocessing/extract_molnar_single_notch.py"), self.root / "scripts/postprocessing/extract_molnar_single_notch.py")
        shutil.copy(pathlib.Path("scripts/validation/validate_mode_ii_h0_endpoint_corrected_results.py"), self.root / "scripts/validation/validate_mode_ii_h0_endpoint_corrected_results.py")
        shutil.copy(pathlib.Path("configs/studies/mode_ii_molnar_shear_endpoint_corrected.yaml"), self.root / "configs/studies/mode_ii_molnar_shear_endpoint_corrected.yaml")

        # Copy mock datacheck evidence
        self.evidence_dir = self.root / "runs/hpc/stage_f/mode_ii_h0_endpoint_corrected/replacement_r1/evidence/1379387.mmaster02"
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        dc_status = {
            "DATACHECK_ok": True,
            "abaqus_return_code": 0,
            "classification": "stage_f_mode_ii_h0_endpoint_corrected_datacheck_pass",
            "job_id": "1379387.mmaster02",
        }
        (self.evidence_dir / "MODE_II_H0_ENDPOINT_CORRECTED_DATACHECK_STATUS.json").write_text(
            json.dumps(dc_status, indent=2), encoding="utf-8"
        )
        (self.evidence_dir / "input_hash_check.txt").write_text(
            "ModeII_H0_endpoint_corrected_serial.inp: OK\nModeII_H0_endpoint_corrected_serial.for: OK\n", encoding="utf-8"
        )

        self.auth_dir = self.root / "runs/hpc/stage_f/mode_ii_h0_endpoint_corrected/replacement_r1"
        self.auth_dir.mkdir(parents=True, exist_ok=True)
        self.auth_file = self.auth_dir / "MODE_II_H0_ENDPOINT_CORRECTED_R1_AUTHORIZATION.json"

        # Initialize dummy git repo in tmp_dir
        subprocess.run(["git", "init"], cwd=self.root, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "test"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.root, check=True)
        subprocess.run(["git", "add", "."], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=self.root, capture_output=True, check=True)

        res = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.root, capture_output=True, text=True, check=True)
        self.current_rev = res.stdout.strip()

        self.write_auth(
            classification="stage_f_mode_ii_h0_endpoint_corrected_serial_solver_contract_prepared_unauthorized",
            solver_auth=False,
            used=0,
            approved=False,
            exec_auth=False,
            max_jobs=0,
            approved_rev=self.current_rev,
        )

    def tearDown(self) -> None:
        self.tmp_dir.cleanup()

    def write_auth(
        self,
        classification: str = "stage_f_mode_ii_h0_endpoint_corrected_serial_solver_contract_prepared_unauthorized",
        solver_auth: bool = False,
        used: int = 0,
        approved: bool = False,
        exec_auth: bool = False,
        max_jobs: int = 0,
        approved_rev: str = "",
        prep_rev: str = "f7e44ae6e7df7dcf1b7eb468eaa946b2eec9caae",
        dc_job: str = "1379387.mmaster02",
        dc_closeout_rev: str = "91d6fad0b972687380759c30a3a268515a733339",
        dc_status: str = "pass",
        retry_auth: bool = False,
        auto_retry_auth: bool = False,
        mpi_auth: bool = False,
        thread_auth: bool = False,
        hybrid_auth: bool = False,
        h1_auth: bool = False,
    ) -> None:
        auth_data = {
            "classification": classification,
            "solver_authorized": solver_auth,
            "solver_submissions_used": used,
            "maximum_solver_submissions": 1,
            "submission_approved": approved,
            "execution_authorized": exec_auth,
            "maximum_jobs_now": max_jobs,
            "approved_project_revision": "PENDING",
            "solver_contract_preparation_revision": prep_rev,
            "datacheck_job_id": dc_job,
            "datacheck_closeout_revision": dc_closeout_rev,
            "datacheck_result_status": dc_status,
            "automatic_retry_authorized": auto_retry_auth,
            "retry_authorized": retry_auth,
            "mpi_authorized": mpi_auth,
            "threaded_execution_authorized": thread_auth,
            "hybrid_authorized": hybrid_auth,
            "h1_authorized": h1_auth,
        }
        self.auth_file.write_text(json.dumps(auth_data, indent=2), encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=self.root, capture_output=True)
        subprocess.run(["git", "commit", "-m", "update auth"], cwd=self.root, capture_output=True)
        res = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.root, capture_output=True, text=True, check=True)
        self.current_rev = res.stdout.strip()

        auth_data["approved_project_revision"] = approved_rev or self.current_rev
        self.auth_file.write_text(json.dumps(auth_data, indent=2), encoding="utf-8")

    def run_wrapper(self, env_vars: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["AUTH_FILE"] = to_wsl_path(self.auth_file)
        env["SCRATCH_ROOT"] = to_wsl_path(self.root / "scratch")
        wsl_keys = ["AUTH_FILE", "SCRATCH_ROOT"]
        if env_vars:
            env.update(env_vars)
            for k in env_vars:
                wsl_keys.append(k)
        env["WSLENV"] = ":".join(wsl_keys)
        script_path = to_wsl_path(self.scripts_dir / "submit_mode_ii_h0_endpoint_corrected_serial.sh")
        proc = subprocess.run(
            ["bash", script_path],
            cwd=str(self.root),
            capture_output=True,
            text=True,
            env=env,
        )
        return proc

    def test_preflight_unauthorized_default(self):
        """Wrapper defaults to preflight PASS without calling qsub when submission is unapproved."""
        proc = self.run_wrapper()
        self.assertEqual(proc.returncode, 0)
        self.assertIn("Preflight check PASS (Submission NOT authorized)", proc.stdout)
        self.assertIn("solver_authorized: false", proc.stdout)

    def test_wrong_auth_classification(self):
        """Wrong authorization classification rejects submission."""
        self.write_auth(
            classification="stage_f_mode_ii_h0_endpoint_corrected_serial_solver_authorized",
            solver_auth=True, approved=True, exec_auth=True, max_jobs=1
        )
        proc = self.run_wrapper({"ALLOW_MODE_II_H0_ENDPOINT_CORRECTED_SOLVER_SUBMIT": "1"})
        self.assertEqual(proc.returncode, 0)
        self.assertIn("Preflight check PASS (Submission NOT authorized)", proc.stdout)

    def test_solver_authorized_false(self):
        """solver_authorized=False rejects submission."""
        self.write_auth(
            classification="stage_f_mode_ii_h0_endpoint_corrected_serial_solver_submission_approved",
            solver_auth=False, approved=True, exec_auth=True, max_jobs=1
        )
        proc = self.run_wrapper({"ALLOW_MODE_II_H0_ENDPOINT_CORRECTED_SOLVER_SUBMIT": "1"})
        self.assertEqual(proc.returncode, 0)
        self.assertIn("solver_authorized: false", proc.stdout)

    def test_submission_approved_false(self):
        """submission_approved=False rejects submission."""
        self.write_auth(
            classification="stage_f_mode_ii_h0_endpoint_corrected_serial_solver_submission_approved",
            solver_auth=True, approved=False, exec_auth=True, max_jobs=1
        )
        proc = self.run_wrapper({"ALLOW_MODE_II_H0_ENDPOINT_CORRECTED_SOLVER_SUBMIT": "1"})
        self.assertEqual(proc.returncode, 0)
        self.assertIn("submission_approved: false", proc.stdout)

    def test_execution_authorized_false(self):
        """execution_authorized=False rejects submission."""
        self.write_auth(
            classification="stage_f_mode_ii_h0_endpoint_corrected_serial_solver_submission_approved",
            solver_auth=True, approved=True, exec_auth=False, max_jobs=1
        )
        proc = self.run_wrapper({"ALLOW_MODE_II_H0_ENDPOINT_CORRECTED_SOLVER_SUBMIT": "1"})
        self.assertEqual(proc.returncode, 0)
        self.assertIn("execution_authorized: false", proc.stdout)

    def test_maximum_jobs_now_zero(self):
        """maximum_jobs_now=0 rejects submission."""
        self.write_auth(
            classification="stage_f_mode_ii_h0_endpoint_corrected_serial_solver_submission_approved",
            solver_auth=True, approved=True, exec_auth=True, max_jobs=0
        )
        proc = self.run_wrapper({"ALLOW_MODE_II_H0_ENDPOINT_CORRECTED_SOLVER_SUBMIT": "1"})
        self.assertEqual(proc.returncode, 0)
        self.assertIn("maximum_jobs_now: 0", proc.stdout)

    def test_missing_explicit_flag(self):
        """Even if fully authorized, missing ALLOW flag prevents submission."""
        self.write_auth(
            classification="stage_f_mode_ii_h0_endpoint_corrected_serial_solver_submission_approved",
            solver_auth=True, approved=True, exec_auth=True, max_jobs=1
        )
        proc = self.run_wrapper({"ALLOW_MODE_II_H0_ENDPOINT_CORRECTED_SOLVER_SUBMIT": "0"})
        self.assertEqual(proc.returncode, 0)
        self.assertIn("ALLOW_MODE_II_H0_ENDPOINT_CORRECTED_SOLVER_SUBMIT: 0", proc.stdout)

    def test_consumed_solver_counter(self):
        """solver_submissions_used >= 1 rejects submission."""
        self.write_auth(
            classification="stage_f_mode_ii_h0_endpoint_corrected_serial_solver_submission_approved",
            solver_auth=True, used=1, approved=True, exec_auth=True, max_jobs=1
        )
        proc = self.run_wrapper({"ALLOW_MODE_II_H0_ENDPOINT_CORRECTED_SOLVER_SUBMIT": "1"})
        self.assertEqual(proc.returncode, 0)
        self.assertIn("solver_submissions_used: 1", proc.stdout)

    def test_wrong_approved_revision(self):
        """Mismatched approved_project_revision rejects submission."""
        self.write_auth(
            classification="stage_f_mode_ii_h0_endpoint_corrected_serial_solver_submission_approved",
            solver_auth=True, approved=True, exec_auth=True, max_jobs=1,
            approved_rev="0000000000000000000000000000000000000000"
        )
        proc = self.run_wrapper({"ALLOW_MODE_II_H0_ENDPOINT_CORRECTED_SOLVER_SUBMIT": "1"})
        self.assertEqual(proc.returncode, 0)
        self.assertIn("approved_project_revision", proc.stdout)

    def test_dirty_tracked_repository(self):
        """Dirty tracked files cause wrapper failure (exit code 1)."""
        self.write_auth(
            classification="stage_f_mode_ii_h0_endpoint_corrected_serial_solver_submission_approved",
            solver_auth=True, approved=True, exec_auth=True, max_jobs=1
        )
        # Modify a tracked code file without committing
        (self.scripts_dir / "04_mode_ii_h0_endpoint_corrected_serial.pbs").write_text("# dirty\n", encoding="utf-8")
        proc = self.run_wrapper({"ALLOW_MODE_II_H0_ENDPOINT_CORRECTED_SOLVER_SUBMIT": "1"})
        self.assertEqual(proc.returncode, 1)
        self.assertIn("Tracked repository files are dirty", proc.stdout)

    def test_wrong_datacheck_job_id(self):
        """Mismatched datacheck_job_id rejects submission."""
        self.write_auth(
            classification="stage_f_mode_ii_h0_endpoint_corrected_serial_solver_submission_approved",
            solver_auth=True, approved=True, exec_auth=True, max_jobs=1,
            dc_job="wrong_job"
        )
        proc = self.run_wrapper({"ALLOW_MODE_II_H0_ENDPOINT_CORRECTED_SOLVER_SUBMIT": "1"})
        self.assertEqual(proc.returncode, 0)
        self.assertIn("datacheck_job_id: wrong_job", proc.stdout)

    def test_wrong_closeout_revision(self):
        """Mismatched datacheck_closeout_revision rejects submission."""
        self.write_auth(
            classification="stage_f_mode_ii_h0_endpoint_corrected_serial_solver_submission_approved",
            solver_auth=True, approved=True, exec_auth=True, max_jobs=1,
            dc_closeout_rev="0000000000000000000000000000000000000000"
        )
        proc = self.run_wrapper({"ALLOW_MODE_II_H0_ENDPOINT_CORRECTED_SOLVER_SUBMIT": "1"})
        self.assertEqual(proc.returncode, 0)
        self.assertIn("datacheck_closeout_revision", proc.stdout)

    def test_failed_datacheck_status(self):
        """datacheck_result_status!=pass rejects submission."""
        self.write_auth(
            classification="stage_f_mode_ii_h0_endpoint_corrected_serial_solver_submission_approved",
            solver_auth=True, approved=True, exec_auth=True, max_jobs=1,
            dc_status="fail"
        )
        proc = self.run_wrapper({"ALLOW_MODE_II_H0_ENDPOINT_CORRECTED_SOLVER_SUBMIT": "1"})
        self.assertEqual(proc.returncode, 0)
        self.assertIn("datacheck_result_status: fail", proc.stdout)

    def test_missing_datacheck_evidence(self):
        """Missing committed datacheck status JSON causes failure."""
        shutil.rmtree(self.evidence_dir)
        subprocess.run(["git", "add", "-A"], cwd=self.root, capture_output=True)
        subprocess.run(["git", "commit", "-m", "remove evidence"], cwd=self.root, capture_output=True)
        self.write_auth(
            classification="stage_f_mode_ii_h0_endpoint_corrected_serial_solver_submission_approved",
            solver_auth=True, approved=True, exec_auth=True, max_jobs=1
        )
        proc = self.run_wrapper({"ALLOW_MODE_II_H0_ENDPOINT_CORRECTED_SOLVER_SUBMIT": "1"})
        self.assertEqual(proc.returncode, 1)
        self.assertIn("Committed datacheck evidence missing", proc.stdout)

    def test_wrong_deck_hash(self):
        """Modified local input deck causes package hash mismatch failure."""
        (self.pkg_dir / "ModeII_H0_endpoint_corrected_serial.inp").write_text("*heading\nwrong deck\n", encoding="utf-8")
        subprocess.run(["git", "commit", "-am", "wrong deck"], cwd=self.root, capture_output=True)
        self.write_auth(
            classification="stage_f_mode_ii_h0_endpoint_corrected_serial_solver_submission_approved",
            solver_auth=True, approved=True, exec_auth=True, max_jobs=1
        )
        proc = self.run_wrapper({"ALLOW_MODE_II_H0_ENDPOINT_CORRECTED_SOLVER_SUBMIT": "1"})
        self.assertEqual(proc.returncode, 1)
        self.assertIn("Package hash mismatch", proc.stdout)

    def test_wrong_source_hash(self):
        """Modified local Fortran source causes package hash mismatch failure."""
        (self.pkg_dir / "ModeII_H0_endpoint_corrected_serial.for").write_text("C wrong source\n", encoding="utf-8")
        subprocess.run(["git", "commit", "-am", "wrong source"], cwd=self.root, capture_output=True)
        self.write_auth(
            classification="stage_f_mode_ii_h0_endpoint_corrected_serial_solver_submission_approved",
            solver_auth=True, approved=True, exec_auth=True, max_jobs=1
        )
        proc = self.run_wrapper({"ALLOW_MODE_II_H0_ENDPOINT_CORRECTED_SOLVER_SUBMIT": "1"})
        self.assertEqual(proc.returncode, 1)
        self.assertIn("Package hash mismatch", proc.stdout)

    def test_missing_extractor(self):
        """Missing runtime extractor script causes wrapper failure."""
        os.remove(self.root / "scripts/postprocessing/extract_molnar_single_notch.py")
        subprocess.run(["git", "commit", "-am", "remove extractor"], cwd=self.root, capture_output=True)
        self.write_auth(
            classification="stage_f_mode_ii_h0_endpoint_corrected_serial_solver_submission_approved",
            solver_auth=True, approved=True, exec_auth=True, max_jobs=1
        )
        proc = self.run_wrapper({"ALLOW_MODE_II_H0_ENDPOINT_CORRECTED_SOLVER_SUBMIT": "1"})
        self.assertEqual(proc.returncode, 1)
        self.assertIn("Required runtime scripts or configs missing locally", proc.stdout)

    def test_missing_validator(self):
        """Missing runtime validator script causes wrapper failure."""
        os.remove(self.root / "scripts/validation/validate_mode_ii_h0_endpoint_corrected_results.py")
        subprocess.run(["git", "commit", "-am", "remove validator"], cwd=self.root, capture_output=True)
        self.write_auth(
            classification="stage_f_mode_ii_h0_endpoint_corrected_serial_solver_submission_approved",
            solver_auth=True, approved=True, exec_auth=True, max_jobs=1
        )
        proc = self.run_wrapper({"ALLOW_MODE_II_H0_ENDPOINT_CORRECTED_SOLVER_SUBMIT": "1"})
        self.assertEqual(proc.returncode, 1)
        self.assertIn("Required runtime scripts or configs missing locally", proc.stdout)

    def test_missing_configuration(self):
        """Missing study configuration YAML causes wrapper failure."""
        os.remove(self.root / "configs/studies/mode_ii_molnar_shear_endpoint_corrected.yaml")
        subprocess.run(["git", "commit", "-am", "remove config"], cwd=self.root, capture_output=True)
        self.write_auth(
            classification="stage_f_mode_ii_h0_endpoint_corrected_serial_solver_submission_approved",
            solver_auth=True, approved=True, exec_auth=True, max_jobs=1
        )
        proc = self.run_wrapper({"ALLOW_MODE_II_H0_ENDPOINT_CORRECTED_SOLVER_SUBMIT": "1"})
        self.assertEqual(proc.returncode, 1)
        self.assertIn("Required runtime scripts or configs missing locally", proc.stdout)

    def test_prohibited_modes_rejected(self):
        """Prohibited execution modes (retry/mpi/threaded/hybrid/h1) cause explicit failure (exit 1)."""
        self.write_auth(
            classification="stage_f_mode_ii_h0_endpoint_corrected_serial_solver_submission_approved",
            solver_auth=True, approved=True, exec_auth=True, max_jobs=1, auto_retry_auth=True
        )
        proc = self.run_wrapper({"ALLOW_MODE_II_H0_ENDPOINT_CORRECTED_SOLVER_SUBMIT": "1"})
        self.assertEqual(proc.returncode, 1)
        self.assertIn("Prohibited execution modes authorized in auth JSON", proc.stdout)

    def test_retry_authorization_true(self):
        """retry_authorized=True causes explicit failure."""
        self.write_auth(
            classification="stage_f_mode_ii_h0_endpoint_corrected_serial_solver_submission_approved",
            solver_auth=True, approved=True, exec_auth=True, max_jobs=1, retry_auth=True
        )
        proc = self.run_wrapper({"ALLOW_MODE_II_H0_ENDPOINT_CORRECTED_SOLVER_SUBMIT": "1"})
        self.assertEqual(proc.returncode, 1)
        self.assertIn("Prohibited execution modes authorized in auth JSON", proc.stdout)

    def test_mpi_authorization_true(self):
        """mpi_authorized=True causes explicit failure."""
        self.write_auth(
            classification="stage_f_mode_ii_h0_endpoint_corrected_serial_solver_submission_approved",
            solver_auth=True, approved=True, exec_auth=True, max_jobs=1, mpi_auth=True
        )
        proc = self.run_wrapper({"ALLOW_MODE_II_H0_ENDPOINT_CORRECTED_SOLVER_SUBMIT": "1"})
        self.assertEqual(proc.returncode, 1)
        self.assertIn("Prohibited execution modes authorized in auth JSON", proc.stdout)

    def test_threaded_authorization_true(self):
        """threaded_execution_authorized=True causes explicit failure."""
        self.write_auth(
            classification="stage_f_mode_ii_h0_endpoint_corrected_serial_solver_submission_approved",
            solver_auth=True, approved=True, exec_auth=True, max_jobs=1, thread_auth=True
        )
        proc = self.run_wrapper({"ALLOW_MODE_II_H0_ENDPOINT_CORRECTED_SOLVER_SUBMIT": "1"})
        self.assertEqual(proc.returncode, 1)
        self.assertIn("Prohibited execution modes authorized in auth JSON", proc.stdout)

    def test_hybrid_authorization_true(self):
        """hybrid_authorized=True causes explicit failure."""
        self.write_auth(
            classification="stage_f_mode_ii_h0_endpoint_corrected_serial_solver_submission_approved",
            solver_auth=True, approved=True, exec_auth=True, max_jobs=1, hybrid_auth=True
        )
        proc = self.run_wrapper({"ALLOW_MODE_II_H0_ENDPOINT_CORRECTED_SOLVER_SUBMIT": "1"})
        self.assertEqual(proc.returncode, 1)
        self.assertIn("Prohibited execution modes authorized in auth JSON", proc.stdout)

    def test_valid_mocked_submission_invokes_qsub_once(self):
        """Fully authorized preflight with mocked qsub helper passes and invokes qsub once with all 4 env vars."""
        self.write_auth(
            classification="stage_f_mode_ii_h0_endpoint_corrected_serial_solver_submission_approved",
            solver_auth=True, approved=True, exec_auth=True, max_jobs=1
        )
        mock_qsub = self.root / "mock_qsub.sh"
        mock_qsub.write_bytes(b"#!/bin/bash\necho \"MOCK_QSUB_ARGS: $@\" >&2\necho \"123456.mmaster02\"\n")
        os.chmod(mock_qsub, 0o755)

        proc = self.run_wrapper({
            "ALLOW_MODE_II_H0_ENDPOINT_CORRECTED_SOLVER_SUBMIT": "1",
            "QSUB_HELPER": to_wsl_path(mock_qsub),
        })
        self.assertEqual(proc.returncode, 0)
        self.assertIn("Submitted serial solver PBS Job ID: 123456.mmaster02", proc.stdout)
        self.assertIn("PRESTAGED_ROOT=", proc.stdout)
        self.assertIn("LOGIN_MANIFEST_PATH=", proc.stdout)
        self.assertIn("PROJECT_REVISION=", proc.stdout)
        self.assertIn("PRESTAGED_RUNTIME_ROOT=", proc.stdout)

    def test_no_real_qsub_no_abaqus(self):
        """Preflight in unapproved state executes zero qsub commands and zero Abaqus executions."""
        proc = self.run_wrapper()
        self.assertEqual(proc.returncode, 0)
        self.assertNotIn("Submitted serial solver PBS Job ID", proc.stdout)


if __name__ == "__main__":
    unittest.main()

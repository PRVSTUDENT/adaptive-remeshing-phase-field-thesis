"""Unit tests for submit_mode_ii_h0_endpoint_corrected_datacheck.sh guarded submission wrapper."""

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


class TestSubmitModeIIH0EndpointCorrectedDatacheck(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp_dir.name)

        # Copy original package and scripts to mock repo
        self.pkg_dir = self.root / "models/generated/mode_ii/h0_endpoint_corrected_serial"
        self.pkg_dir.mkdir(parents=True, exist_ok=True)
        real_pkg = pathlib.Path("models/generated/mode_ii/h0_endpoint_corrected_serial")
        shutil.copy(real_pkg / "ModeII_H0_endpoint_corrected_serial.inp", self.pkg_dir / "ModeII_H0_endpoint_corrected_serial.inp")
        shutil.copy(real_pkg / "ModeII_H0_endpoint_corrected_serial.for", self.pkg_dir / "ModeII_H0_endpoint_corrected_serial.for")

        self.scripts_dir = self.root / "scripts/hpc/stage_f"
        self.scripts_dir.mkdir(parents=True, exist_ok=True)
        real_scripts = pathlib.Path("scripts/hpc/stage_f")
        shutil.copy(real_scripts / "03_mode_ii_h0_endpoint_corrected_datacheck.pbs", self.scripts_dir / "03_mode_ii_h0_endpoint_corrected_datacheck.pbs")
        shutil.copy(real_scripts / "submit_mode_ii_h0_endpoint_corrected_datacheck.sh", self.scripts_dir / "submit_mode_ii_h0_endpoint_corrected_datacheck.sh")

        self.auth_dir = self.root / "runs/hpc/stage_f/mode_ii_h0_endpoint_corrected/replacement_r1"
        self.auth_dir.mkdir(parents=True, exist_ok=True)
        self.auth_file = self.auth_dir / "MODE_II_H0_ENDPOINT_CORRECTED_R1_AUTHORIZATION.json"

        # Initialize dummy git repo in tmp_dir
        subprocess.run(["git", "init"], cwd=self.root, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "test"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.root, check=True)
        subprocess.run(["git", "add", "."], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=self.root, capture_output=True, check=True)

        self.write_auth(datacheck_auth=False, used=0, approved=False, max_jobs=0)

    def tearDown(self) -> None:
        self.tmp_dir.cleanup()

    def write_auth(
        self,
        datacheck_auth: bool = True,
        used: int = 0,
        approved: bool = True,
        max_jobs: int = 1,
        solver_auth: bool = False,
        retry_auth: bool = False,
        mpi_auth: bool = False,
        thread_auth: bool = False,
    ) -> None:
        auth_data = {
            "classification": "stage_f_mode_ii_h0_endpoint_corrected_datacheck_replacement_authorized",
            "datacheck_authorized": datacheck_auth,
            "datacheck_submissions_used": used,
            "submission_approved": approved,
            "maximum_jobs_now": max_jobs,
            "solver_authorized": solver_auth,
            "automatic_retry_authorized": retry_auth,
            "mpi_authorized": mpi_auth,
            "threaded_execution_authorized": thread_auth,
            "hybrid_authorized": False,
        }
        self.auth_file.write_text(json.dumps(auth_data, indent=2), encoding="utf-8")

    def run_wrapper(self, env_vars: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["AUTH_FILE"] = to_wsl_path(self.auth_file)
        env["SCRATCH_ROOT"] = to_wsl_path(self.root / "scratch")
        if env_vars:
            env.update(env_vars)
        wsl_keys = ["AUTH_FILE", "SCRATCH_ROOT"]
        for k in env_vars or {}:
            wsl_keys.append(k)
        env["WSLENV"] = ":".join(wsl_keys)
        script_path = to_wsl_path(self.scripts_dir / "submit_mode_ii_h0_endpoint_corrected_datacheck.sh")
        proc = subprocess.run(
            ["bash", script_path],
            cwd=str(self.root),
            capture_output=True,
            text=True,
            env=env,
        )
        return proc

    def test_submission_flag_absent_performs_no_qsub(self) -> None:
        self.write_auth(datacheck_auth=True, used=0, approved=True, max_jobs=1)
        proc = self.run_wrapper({"ALLOW_MODE_II_H0_ENDPOINT_CORRECTED_DATACHECK_SUBMIT": "0"})
        self.assertEqual(proc.returncode, 0)
        self.assertIn("Preflight check PASS (Submission NOT authorized)", proc.stdout)

    def test_authorization_false_fails(self) -> None:
        self.write_auth(datacheck_auth=False, used=0, approved=True, max_jobs=1)
        proc = self.run_wrapper({"ALLOW_MODE_II_H0_ENDPOINT_CORRECTED_DATACHECK_SUBMIT": "1"})
        self.assertEqual(proc.returncode, 0)
        self.assertIn("datacheck_authorized: false", proc.stdout)

    def test_authorization_consumed_fails(self) -> None:
        self.write_auth(datacheck_auth=True, used=1, approved=True, max_jobs=1)
        proc = self.run_wrapper({"ALLOW_MODE_II_H0_ENDPOINT_CORRECTED_DATACHECK_SUBMIT": "1"})
        self.assertEqual(proc.returncode, 0)
        self.assertIn("datacheck_submissions_used: 1", proc.stdout)

    def test_prohibited_solver_auth_fails(self) -> None:
        self.write_auth(datacheck_auth=True, used=0, approved=True, max_jobs=1, solver_auth=True)
        proc = self.run_wrapper({"ALLOW_MODE_II_H0_ENDPOINT_CORRECTED_DATACHECK_SUBMIT": "1"})
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("Prohibited execution modes authorized", proc.stdout)

    def test_wrong_deck_hash_fails(self) -> None:
        (self.pkg_dir / "ModeII_H0_endpoint_corrected_serial.inp").write_text("modified", encoding="utf-8")
        self.write_auth(datacheck_auth=True, used=0, approved=True, max_jobs=1)
        proc = self.run_wrapper({"ALLOW_MODE_II_H0_ENDPOINT_CORRECTED_DATACHECK_SUBMIT": "1"})
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("Package hash mismatch", proc.stdout)

    def test_valid_mocked_submission_invokes_qsub_with_required_variables(self) -> None:

        self.write_auth(datacheck_auth=True, used=0, approved=True, max_jobs=1)

        mock_qsub = self.root / "mock_qsub.sh"
        with open(mock_qsub, "w", newline="\n") as f:
            f.write("#!/bin/bash\necho \"MOCK QSUB CALLED WITH ARGS: $@\" >&2\necho \"999999.mmaster02\"\n")
        mock_qsub.chmod(0o755)

        proc = self.run_wrapper({
            "ALLOW_MODE_II_H0_ENDPOINT_CORRECTED_DATACHECK_SUBMIT": "1",
            "QSUB_HELPER": to_wsl_path(mock_qsub),
        })

        self.assertEqual(proc.returncode, 0, msg=f"Stderr: {proc.stderr}\nStdout: {proc.stdout}")
        self.assertIn("Submitted datacheck PBS Job ID: 999999.mmaster02", proc.stdout)
        self.assertIn("PRESTAGED_ROOT=", proc.stderr)
        self.assertIn("LOGIN_MANIFEST_PATH=", proc.stderr)
        self.assertIn("PROJECT_REVISION=", proc.stderr)


if __name__ == "__main__":
    unittest.main()

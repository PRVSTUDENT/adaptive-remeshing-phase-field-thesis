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

        self.auth_dir = self.root / "runs/hpc/stage_f/mode_ii_h0_endpoint_corrected/replacement_r1"
        self.auth_dir.mkdir(parents=True, exist_ok=True)
        self.auth_file = self.auth_dir / "MODE_II_H0_ENDPOINT_CORRECTED_R1_AUTHORIZATION.json"

        # Initialize dummy git repo in tmp_dir
        subprocess.run(["git", "init"], cwd=self.root, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "test"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.root, check=True)
        subprocess.run(["git", "add", "."], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=self.root, capture_output=True, check=True)

        self.write_auth(solver_auth=False, used=0, approved=False, max_jobs=0)

    def tearDown(self) -> None:
        self.tmp_dir.cleanup()

    def write_auth(
        self,
        solver_auth: bool = False,
        used: int = 0,
        approved: bool = False,
        max_jobs: int = 0,
        retry_auth: bool = False,
        mpi_auth: bool = False,
        thread_auth: bool = False,
    ) -> None:
        auth_data = {
            "classification": "stage_f_mode_ii_h0_endpoint_corrected_serial_solver_contract_remediation_required",
            "solver_authorized": solver_auth,
            "solver_submissions_used": used,
            "maximum_solver_submissions": 1,
            "submission_approved": approved,
            "maximum_jobs_now": max_jobs,
            "automatic_retry_authorized": retry_auth,
            "mpi_authorized": mpi_auth,
            "threaded_execution_authorized": thread_auth,
            "hybrid_authorized": False,
            "h1_authorized": False,
        }
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

    def test_explicit_flag_absent_rejects_submission(self):
        """Even if solver_authorized is true, missing ALLOW flag prevents qsub."""
        self.write_auth(solver_auth=True, used=0, approved=True, max_jobs=1)
        proc = self.run_wrapper({"ALLOW_MODE_II_H0_ENDPOINT_CORRECTED_SOLVER_SUBMIT": "0"})
        self.assertEqual(proc.returncode, 0)
        self.assertIn("Preflight check PASS (Submission NOT authorized)", proc.stdout)
        self.assertIn("ALLOW_MODE_II_H0_ENDPOINT_CORRECTED_SOLVER_SUBMIT: 0", proc.stdout)

    def test_prohibited_modes_rejected(self):
        """Prohibited modes (retry/mpi/threaded/hybrid) cause explicit failure (exit 1)."""
        self.write_auth(solver_auth=True, used=0, approved=True, max_jobs=1, retry_auth=True)
        proc = self.run_wrapper({"ALLOW_MODE_II_H0_ENDPOINT_CORRECTED_SOLVER_SUBMIT": "1"})
        self.assertEqual(proc.returncode, 1)
        self.assertIn("Prohibited execution modes authorized in auth JSON", proc.stdout)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""tests/unit/test_mode1_f1597_package148_r4_preflight.py

Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Preflight and qualification tests for Package 148 R4:
1. Validates all 14 package files exist.
2. Validates frozen UEL bitwise identity.
3. Validates staged notification helper hash.
4. Validates PBS wrapper directives and path consistency targeting R4.
5. Validates shell syntax (bash -n) for submit script and datacheck script.
6. Validates PACKAGE_MANIFEST and EXECUTION_MANIFEST consistency and updated runtime source bindings.
7. Validates that R4 does not reference R2 or R3 run directories.
8. Validates runtime driver binds DAT_DAMAGE_RECOVERY_TOL = 1e-8.
"""

import hashlib
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]
R4_DIR = ROOT / "models/pandey_kumar_mode1/148_c4_package148_state_transfer_r4"
PBS_FILE = R4_DIR / "submit_M1_C4_P148_R4.pbs"
CANONICAL_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
CANONICAL_HELPER_SHA256 = "41A1D403B0356B55EFA3BB1E67B4DD678E74664D501D838D9C01952C0C641F11"

REQUIRED_CONTRACT_DIRECTIVES = [
    '#PBS -q entry_imfdfkmq',
    '#PBS -m abe',
    '#PBS -M pr21vyci@mailserver.tu-freiberg.de',
    '#PBS -l select=1:ncpus=1:mem=16gb',
    '#PBS -l walltime=08:00:00',
    '#PBS -r n',
    'cd "${RUN_DIR}"',
    'notification_load_config',
    'command -v ifort',
    'module load gcc/11.4.0 intel/2024.2.0 abaqus/2023',
    'notification_install_terminal_trap',
    'notify_start',
]


def sha256_file(path):
    h = hashlib.sha256()
    with open(str(path), "rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest().upper()


class Package148R4PreflightTests(unittest.TestCase):
    def test_01_all_package_files_exist(self):
        expected_files = [
            "active_set_boundary_cards.inc",
            "d_lower_bounds.csv",
            "EXECUTION_MANIFEST.json",
            "f42_mixed_uel.for",
            "initial_conditions_solution.inc",
            "job_notifications.sh",
            "M1_C4_PACKAGE148_STATE_TRANSFER.inp",
            "nodal_displacements_initial.csv",
            "nodal_phase_field_initial.csv",
            "P148_MECHANICAL_DC.inp",
            "P148_PHASE_DC.inp",
            "PACKAGE_MANIFEST.json",
            "run_datacheck.sh",
            "submit_M1_C4_P148_R4.pbs",
        ]
        for fname in expected_files:
            fpath = R4_DIR / fname
            self.assertTrue(fpath.is_file(), f"Missing expected package file: {fname}")

    def test_02_production_uel_bitwise_frozen(self):
        uel_path = R4_DIR / "f42_mixed_uel.for"
        actual = sha256_file(uel_path)
        self.assertEqual(actual, CANONICAL_UEL_SHA256, "UEL is not bitwise frozen")

    def test_03_staged_notification_helper_verified(self):
        helper_path = R4_DIR / "job_notifications.sh"
        actual = sha256_file(helper_path)
        self.assertEqual(actual, CANONICAL_HELPER_SHA256, "Staged notification helper hash mismatch")

    def test_04_pbs_preflight_contract_directives(self):
        pbs_text = PBS_FILE.read_text(encoding="utf-8")
        for directive in REQUIRED_CONTRACT_DIRECTIVES:
            self.assertIn(directive, pbs_text, f"Missing required preflight directive: {directive}")
        self.assertIn("M1_C4_P148_R4", pbs_text)
        self.assertIn("mode1_c4_package148_state_transfer_r4", pbs_text)
        self.assertNotIn("mode1_c4_package148_state_transfer_r3", pbs_text)
        self.assertNotIn("mode1_c4_package148_state_transfer_r2", pbs_text)

    def test_05_pbs_shell_syntax(self):
        git_bash = Path(r"C:\Program Files\Git\usr\bin\bash.exe")
        bash_cmd = str(git_bash) if git_bash.is_file() else "bash"
        rel_pbs = str(PBS_FILE.relative_to(ROOT)).replace("\\", "/")
        proc = subprocess.run(
            [bash_cmd, "-n", rel_pbs],
            cwd=str(ROOT),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, f"bash -n failed on {rel_pbs}: {proc.stderr}")

    def test_06_datacheck_shell_syntax(self):
        git_bash = Path(r"C:\Program Files\Git\usr\bin\bash.exe")
        bash_cmd = str(git_bash) if git_bash.is_file() else "bash"
        dc_file = R4_DIR / "run_datacheck.sh"
        rel_dc = str(dc_file.relative_to(ROOT)).replace("\\", "/")
        proc = subprocess.run(
            [bash_cmd, "-n", rel_dc],
            cwd=str(ROOT),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, f"bash -n failed on {rel_dc}: {proc.stderr}")

    def test_07_package_manifest_integrity_and_runtime_bindings(self):
        pkg_manifest = json.loads((R4_DIR / "PACKAGE_MANIFEST.json").read_text(encoding="utf-8"))
        self.assertEqual(pkg_manifest.get("revision"), "R4")
        self.assertEqual(pkg_manifest.get("package"), 148)
        self.assertEqual(pkg_manifest.get("frozen_uel_sha256"), CANONICAL_UEL_SHA256)

        # Verify file hashes in manifest match disk
        for fname, expected_hash in pkg_manifest.get("files", {}).items():
            fpath = R4_DIR / fname
            self.assertTrue(fpath.is_file(), f"File in manifest missing on disk: {fname}")
            actual_hash = sha256_file(fpath)
            self.assertEqual(actual_hash, expected_hash, f"Hash mismatch for {fname}")

        # Verify runtime source hashes in manifest match actual source files in repo
        for rel_path, expected_hash in pkg_manifest.get("runtime_source_hashes", {}).items():
            src_path = ROOT / rel_path
            self.assertTrue(src_path.is_file(), f"Runtime source file missing: {rel_path}")
            actual_hash = sha256_file(src_path)
            self.assertEqual(actual_hash, expected_hash, f"Runtime source hash mismatch for {rel_path}")

    def test_08_execution_manifest_integrity(self):
        exec_manifest = json.loads((R4_DIR / "EXECUTION_MANIFEST.json").read_text(encoding="utf-8"))
        self.assertEqual(exec_manifest.get("batch_name"), "MODE1_PACKAGE148_R4_STATE_TRANSFER")
        self.assertEqual(exec_manifest.get("adapter"), "mode1-qualified-batch-v2")
        self.assertEqual(exec_manifest.get("technical_stage"), "C1-1")
        self.assertEqual(exec_manifest.get("remote_run_dir"), "/scratch9/pr21vyci/runs/mode1_c4_package148_state_transfer_r4")
        self.assertEqual(len(exec_manifest.get("jobs", [])), 1)
        job = exec_manifest["jobs"][0]
        self.assertEqual(job.get("id"), "M1_C4_P148_R4")
        self.assertEqual(job.get("pbs"), "submit_M1_C4_P148_R4.pbs")
        self.assertEqual(job.get("queue"), "entry_imfdfkmq")

    def test_09_driver_has_dat_tolerance(self):
        driver_text = (ROOT / "scripts/state_transfer/driver_package146_147_pdas_continuation.py").read_text(encoding="utf-8")
        self.assertIn("DAT_DAMAGE_RECOVERY_TOL = 1e-8", driver_text)


if __name__ == "__main__":
    unittest.main()

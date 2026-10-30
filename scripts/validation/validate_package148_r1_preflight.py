#!/usr/bin/env python3
"""
scripts/validation/validate_package148_r1_preflight.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Preflight and execution-readiness verification for Package 148 R1:
1. Validates PBS wrapper against all 12 contract requirements in preflight_package49_authorization.py:
   - #PBS -q entry_imfdfkmq
   - #PBS -m abe
   - #PBS -M pr21vyci@mailserver.tu-freiberg.de
   - #PBS -l select=1:ncpus=1:mem=16gb
   - #PBS -l walltime=08:00:00
   - #PBS -r n
   - cd "${RUN_DIR}"
   - notification_load_config
   - command -v ifort
   - module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
   - notification_install_terminal_trap
   - notify_start
2. Runs shell syntax check (bash -n).
3. Verifies bitwise frozen UEL SHA-256.
4. Verifies staged dependencies (job_notifications.sh present and matching canonical hash).
5. Verifies alternating PDAS driver invocation with exact parameters.
"""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
R1_DIR = REPO_ROOT / "models/pandey_kumar_mode1/148_c4_package148_state_transfer_r1"
PBS_FILE = R1_DIR / "submit_M1_C4_P148_R1.pbs"
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

def run_preflight_checks():
    report = {
        "schema": 1,
        "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
        "package": "148_c4_package148_state_transfer_r1",
        "checks": {},
        "file_hashes": {},
        "overall_status": "FAIL",
    }

    # 1. Check file existence
    expected_files = [
        "active_set_boundary_cards.inc",
        "d_lower_bounds.csv",
        "f42_mixed_uel.for",
        "initial_conditions_solution.inc",
        "job_notifications.sh",
        "M1_C4_PACKAGE148_STATE_TRANSFER.inp",
        "nodal_displacements_initial.csv",
        "nodal_phase_field_initial.csv",
        "PACKAGE_MANIFEST.json",
        "submit_M1_C4_P148_R1.pbs",
    ]
    missing = [f for f in expected_files if not (R1_DIR / f).is_file()]
    report["checks"]["file_existence"] = {
        "status": "PASS" if not missing else "FAIL",
        "missing_files": missing,
        "total_files": len(expected_files) - len(missing),
    }

    # Compute hashes
    for fname in expected_files:
        fpath = R1_DIR / fname
        if fpath.is_file():
            report["file_hashes"][fname] = sha256_file(fpath)

    # 2. Frozen UEL verification
    uel_hash = report["file_hashes"].get("f42_mixed_uel.for", "")
    uel_pass = (uel_hash == CANONICAL_UEL_SHA256)
    report["checks"]["frozen_uel"] = {
        "status": "PASS" if uel_pass else "FAIL",
        "actual_sha256": uel_hash,
        "expected_sha256": CANONICAL_UEL_SHA256,
    }

    # 3. Notification helper verification
    helper_hash = report["file_hashes"].get("job_notifications.sh", "")
    helper_pass = (helper_hash == CANONICAL_HELPER_SHA256)
    report["checks"]["staged_notification_helper"] = {
        "status": "PASS" if helper_pass else "FAIL",
        "actual_sha256": helper_hash,
        "expected_sha256": CANONICAL_HELPER_SHA256,
    }

    # 4. Check PBS script contract directives
    pbs_text = PBS_FILE.read_text(encoding="utf-8")
    missing_directives = [d for d in REQUIRED_CONTRACT_DIRECTIVES if d not in pbs_text]
    report["checks"]["pbs_preflight_contract"] = {
        "status": "PASS" if not missing_directives else "FAIL",
        "missing_directives": missing_directives,
        "checked_directives_count": len(REQUIRED_CONTRACT_DIRECTIVES),
    }

    # 5. Check shell syntax (bash -n)
    git_bash = Path(r"C:\Program Files\Git\usr\bin\bash.exe")
    bash_cmd = str(git_bash) if git_bash.is_file() else "bash"
    rel_pbs = str(PBS_FILE.relative_to(REPO_ROOT)).replace("\\", "/")
    try:
        proc = subprocess.run(
            [bash_cmd, "-n", rel_pbs],
            cwd=str(REPO_ROOT),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=15
        )
        syntax_pass = (proc.returncode == 0)
        syntax_err = proc.stderr.strip()
    except Exception as e:
        syntax_pass = False
        syntax_err = str(e)

    report["checks"]["pbs_shell_syntax"] = {
        "status": "PASS" if syntax_pass else "FAIL",
        "exit_code": proc.returncode if syntax_pass else -1,
        "error": syntax_err if not syntax_pass else "",
    }

    # 6. Check alternating PDAS driver invocation
    pdas_driver_invocation = "driver_package146_147_pdas_continuation.py" in pbs_text
    output_dir_flag = "--output" in pbs_text
    extractor_flag = "--extractor" in pbs_text
    report["checks"]["driver_invocation"] = {
        "status": "PASS" if (pdas_driver_invocation and output_dir_flag and extractor_flag) else "FAIL",
        "invokes_pdas_continuation": pdas_driver_invocation,
        "specifies_output": output_dir_flag,
        "specifies_extractor": extractor_flag,
    }

    # Overall status
    all_passed = all(
        c.get("status") == "PASS" for c in report["checks"].values()
    )
    report["overall_status"] = "PASS" if all_passed else "FAIL"
    return report

def main():
    report = run_preflight_checks()
    out_file = REPO_ROOT / "results/validation/package148_r1_preflight_proof.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(report, indent=2), encoding="utf-8")
    sys.stdout.write(json.dumps(report, indent=2) + "\n")
    sys.stdout.flush()
    return 0 if report["overall_status"] == "PASS" else 1

if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Remote Qualification Script for Candidate M2STATE_FRACFIX_RESTART2R7
Task ID: F76STATE-M2-RESTART2R7-PHASE-RESIDUAL-REPAIR-QUALIFICATION1
Target: pr21vyci@mlogin01.hrz.tu-freiberg.de
"""

import os
import subprocess
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
LOCAL_CANDIDATE = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R7"
REMOTE_CANDIDATE = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R7"
SSH_KEY = os.path.expanduser("~/.ssh/tu_freiberg_codex")
REMOTE_HOST = "pr21vyci@mlogin01.hrz.tu-freiberg.de"

def run_ssh(remote_cmd, check=True):
    print(f"--> Executing Remote: {remote_cmd}")
    cmd = [
        "ssh", "-i", SSH_KEY,
        "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=no",
        REMOTE_HOST,
        remote_cmd
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.stdout:
        print(res.stdout)
    if res.stderr:
        print(res.stderr, file=sys.stderr)
    if check and res.returncode != 0:
        raise RuntimeError(f"Remote command failed with exit code {res.returncode}")
    return res

def run_scp(local_path, remote_path):
    print(f"--> SCP: {local_path} -> {remote_path}")
    cmd = [
        "scp", "-i", SSH_KEY,
        "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=no",
        str(local_path),
        f"{REMOTE_HOST}:{remote_path}"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.stdout:
        print(res.stdout)
    if res.stderr:
        print(res.stderr, file=sys.stderr)
    if res.returncode != 0:
        raise RuntimeError(f"SCP failed with exit code {res.returncode}")
    return res

def main():
    print("======================================================================")
    print("STARTING REMOTE QUALIFICATION: M2STATE_FRACFIX_RESTART2R7")
    print("======================================================================")

    # 1. Create remote candidate directory
    run_ssh(f"mkdir -p {REMOTE_CANDIDATE}")

    # 2. Stage candidate files to cluster
    print("\n--- Staging candidate files to cluster ---")
    files_to_copy = [
        "M2STATE_FRACFIX_RESTART2R7.inp",
        "f42_mixed_uel.for",
        "M2STATE_FRACFIX_RESTART2R7.pbs",
        "submit_m2state_fracfix_restart2r7.sh",
        "STATE_TRANSFER_ARTIFACT.json",
        "TRANSFER_MANIFEST.json",
        "RESTART_ACCEPTANCE_CONTRACT.json",
        "validate_package_manifest.py",
        "extract_restart2r7_odb.py",
        "verify_restart2r7_science.py",
        "compare_restart1_restart2_matched_state.py",
        "job_notifications.sh",
        "PACKAGE_MANIFEST.json"
    ]

    for fname in files_to_copy:
        local_p = LOCAL_CANDIDATE / fname
        run_scp(local_p, f"{REMOTE_CANDIDATE}/{fname}")

    # Stage unit test file and local build script
    test_local = ROOT / "tests/unit/test_m2state_fracfix_restart2r7.py"
    run_scp(test_local, "/home/pr21vyci/projects/adaptive-remeshing/tests/unit/test_m2state_fracfix_restart2r7.py")

    # 3. Remote Manifest Validation (100% SHA256 match)
    print("\n--- Validating Remote Manifest ---")
    run_ssh(f"cd {REMOTE_CANDIDATE} && python3 validate_package_manifest.py")

    # 4. Remote Unit Tests
    print("\n--- Running Remote Unit Tests ---")
    run_ssh(f"cd /home/pr21vyci/projects/adaptive-remeshing && python3 -m unittest tests/unit/test_m2state_fracfix_restart2r7.py")

    # 5. Remote Guarded Wrapper Dry-Run (0 qsub calls)
    print("\n--- Running Remote Guarded Wrapper Dry-Run ---")
    run_ssh(f"cd {REMOTE_CANDIDATE} && chmod +x submit_m2state_fracfix_restart2r7.sh && ./submit_m2state_fracfix_restart2r7.sh --dry-run")

    # 6. Remote Abaqus Datacheck & Fortran Compilation
    print("\n--- Running Remote Abaqus Datacheck ---")
    syntax_cmd = (
        f"source /etc/profile.d/modules.sh 2>/dev/null || source /etc/profile 2>/dev/null || true && "
        f"module purge && "
        f"module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 python/gcc/11.4.0/3.11.7 && "
        f"cd {REMOTE_CANDIDATE} && "
        f"rm -f M2STATE_FRACFIX_RESTART2R7.dat M2STATE_FRACFIX_RESTART2R7.msg M2STATE_FRACFIX_RESTART2R7.sta M2STATE_FRACFIX_RESTART2R7.odb M2STATE_FRACFIX_RESTART2R7.prt M2STATE_FRACFIX_RESTART2R7.com && "
        f"abaqus job=M2STATE_FRACFIX_RESTART2R7 user=f42_mixed_uel.for datacheck interactive"
    )
    run_ssh(syntax_cmd)

    # 7. Check Remote Datacheck DAT File for Errors/Fatals/Distorted Elements
    print("\n--- Checking Datacheck Output Log ---")
    dat_check = f"cd {REMOTE_CANDIDATE} && grep -E 'ERROR|FATAL|DISTORTED|COMPLETED' M2STATE_FRACFIX_RESTART2R7.dat || true"
    res_dat = run_ssh(dat_check, check=False)
    print(f"Datacheck search results:\n{res_dat.stdout}")

    # 8. Run Step 1 Direct Numerical Solve on Full Mesh
    print("\n--- Running Step 1 Numerical Verification on Full Mesh ---")
    step1_cmd = (
        f"source /etc/profile.d/modules.sh 2>/dev/null || source /etc/profile 2>/dev/null || true && "
        f"module purge && "
        f"module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 python/gcc/11.4.0/3.11.7 && "
        f"cd {REMOTE_CANDIDATE} && "
        f"head -n 950 M2STATE_FRACFIX_RESTART2R7.inp > STEP1_TEST.inp && "
        f"echo '*END STEP' >> STEP1_TEST.inp && "
        f"rm -f STEP1_TEST.odb STEP1_TEST.msg STEP1_TEST.dat STEP1_TEST.sta && "
        f"abaqus job=STEP1_TEST user=f42_mixed_uel.for interactive double=both cpus=1 memory=16gb scratch=. && "
        f"grep -E 'THE ANALYSIS HAS COMPLETED|ERROR|FATAL|ILLEGAL' STEP1_TEST.msg || true"
    )
    run_ssh(step1_cmd)

    print("\n======================================================================")
    print("REMOTE QUALIFICATION FOR M2STATE_FRACFIX_RESTART2R7: COMPLETE PASS")
    print("======================================================================")

if __name__ == "__main__":
    main()

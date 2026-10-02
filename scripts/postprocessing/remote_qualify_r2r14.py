#!/usr/bin/env python3
"""
Remote Qualification Workflow for Candidate M2STATE_FRACFIX_RESTART2R14 on mlogin01
Task ID: F111STATE-M2-RESTART2-R2R14-CONTINUATION-PREP-AND-QUALIFICATION1
"""

import os
import sys
import subprocess
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
LOCAL_PKG_DIR = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R14"
REMOTE_PKG_DIR = "projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R14"
SSH_KEY = "C:/Users/pruth/.ssh/tu_freiberg_codex"
SSH_HOST = "pr21vyci@mlogin01.hrz.tu-freiberg.de"

def run_ssh(cmd, timeout=300):
    ssh_cmd = ["ssh", "-i", SSH_KEY, SSH_HOST, cmd]
    res = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=timeout)
    return res.returncode, res.stdout, res.stderr

def run_scp_to_remote(local_file, remote_dest):
    scp_cmd = ["scp", "-i", SSH_KEY, str(local_file), f"{SSH_HOST}:{remote_dest}"]
    res = subprocess.run(scp_cmd, capture_output=True, text=True)
    return res.returncode, res.stdout, res.stderr

def run_scp_from_remote(remote_file, local_dest):
    scp_cmd = ["scp", "-i", SSH_KEY, f"{SSH_HOST}:{remote_file}", str(local_dest)]
    res = subprocess.run(scp_cmd, capture_output=True, text=True)
    return res.returncode, res.stdout, res.stderr

def qualify():
    print("================================================================================")
    print("REMOTE SCIENTIFIC QUALIFICATION: M2STATE_FRACFIX_RESTART2R14")
    print("TASK ID: F111STATE-M2-RESTART2-R2R14-CONTINUATION-PREP-AND-QUALIFICATION1")
    print("================================================================================")
    
    # 1. Create remote directory
    print("\n--- 1. Creating Remote Candidate Directory ---")
    rc, out, err = run_ssh(f"mkdir -p {REMOTE_PKG_DIR}")
    print(f"Directory create exit: {rc}")

    # 2. Upload Package Files
    print("\n--- 2. Uploading Candidate Package Files ---")
    files_to_upload = [
        "M2STATE_FRACFIX_RESTART2R14.inp",
        "f42_mixed_uel.for",
        "M2STATE_FRACFIX_RESTART2R14.pbs",
        "submit_m2state_fracfix_restart2r14.sh",
        "validate_package_manifest.py",
        "job_notifications.sh",
        "STATE_TRANSFER_ARTIFACT.json",
        "TRANSFER_MANIFEST.json",
        "RESTART_ACCEPTANCE_CONTRACT.json",
        "PACKAGE_MANIFEST.json"
    ]
    for fn in files_to_upload:
        local_p = LOCAL_PKG_DIR / fn
        print(f"Uploading {fn} ({local_p.stat().st_size} bytes)...")
        rc, out, err = run_scp_to_remote(local_p, f"{REMOTE_PKG_DIR}/{fn}")
        if rc != 0:
            print(f"SCP Error: {err}")
            sys.exit(1)

    # 3. Verify Remote Manifest
    print("\n--- 3. Verifying Remote Package Manifest ---")
    rc, out, err = run_ssh(f"cd {REMOTE_PKG_DIR} && chmod +x submit_m2state_fracfix_restart2r14.sh && python3 validate_package_manifest.py")
    print(f"Exit code: {rc}")
    print(f"Output: {out.strip()}")
    if rc != 0:
        print(f"Error: {err}")
        sys.exit(1)

    # 4. Run Remote Datacheck
    print("\n--- 4. Running Remote Abaqus 2023 Datacheck ---")
    datacheck_cmd = (
        f"cd {REMOTE_PKG_DIR} && "
        "source /etc/profile.d/modules.sh 2>/dev/null || true; "
        "module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 python/gcc/11.4.0/3.11.7 && "
        "rm -f M2STATE_FRACFIX_RESTART2R14_DATACHECK.* || true && "
        "abaqus job=M2STATE_FRACFIX_RESTART2R14_DATACHECK user=f42_mixed_uel.for input=M2STATE_FRACFIX_RESTART2R14.inp datacheck double=both interactive cpus=1"
    )
    rc, out, err = run_ssh(datacheck_cmd, timeout=300)
    print(f"Datacheck exit: {rc}")
    print(f"Datacheck stdout:\n{out}")
    if rc != 0:
        print(f"Datacheck stderr:\n{err}")

    # 5. Run Step 1 PhaseInit Solve to qualify Step 1 reaction force and global force equilibrium
    print("\n--- 5. Generating and Running Remote Step 1 PhaseInit Solve ---")
    step1_inp_gen = (
        f"cd {REMOTE_PKG_DIR} && "
        "python3 -c '\n"
        "from pathlib import Path\n"
        "text = Path(\"M2STATE_FRACFIX_RESTART2R14.inp\").read_text()\n"
        "step2_idx = text.find(\"*STEP, NAME=Step-2-Continuation\")\n"
        "if step2_idx > 0:\n"
        "    step1_text = text[:step2_idx]\n"
        "    Path(\"M2STATE_FRACFIX_RESTART2R14_STEP1.inp\").write_text(step1_text)\n"
        "    print(\"Generated M2STATE_FRACFIX_RESTART2R14_STEP1.inp\")\n"
        "else:\n"
        "    print(\"ERROR: Step 2 marker not found\")\n"
        "'\n"
    )
    rc, out, err = run_ssh(step1_inp_gen)
    print(f"Step 1 INP generation: {out.strip()}")

    step1_solve_cmd = (
        f"cd {REMOTE_PKG_DIR} && "
        "source /etc/profile.d/modules.sh 2>/dev/null || true; "
        "module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 python/gcc/11.4.0/3.11.7 && "
        "rm -f M2STATE_FRACFIX_RESTART2R14_STEP1.lck || true && "
        "abaqus job=M2STATE_FRACFIX_RESTART2R14_STEP1 user=f42_mixed_uel.for input=M2STATE_FRACFIX_RESTART2R14_STEP1.inp double=both interactive cpus=1 memory=\"16000 mb\""
    )
    rc, out, err = run_ssh(step1_solve_cmd, timeout=300)
    print(f"Step 1 Solve exit: {rc}")
    print(f"Step 1 Solve stdout:\n{out}")

    # Download Step 1 DAT
    print("\n--- 6. Downloading and Auditing Step 1 DAT ---")
    run_scp_from_remote(f"{REMOTE_PKG_DIR}/M2STATE_FRACFIX_RESTART2R14_STEP1.dat", LOCAL_PKG_DIR / "M2STATE_FRACFIX_RESTART2R14_STEP1.dat")

    # 7. Test Guarded Wrapper Dry-Run
    print("\n--- 7. Testing Guarded Submission Wrapper Dry-Run ---")
    rc, out, err = run_ssh(f"cd {REMOTE_PKG_DIR} && ./submit_m2state_fracfix_restart2r14.sh --dry-run")
    print(f"Wrapper dry-run exit: {rc}")
    print(f"Output: {out.strip()}")

if __name__ == '__main__':
    qualify()

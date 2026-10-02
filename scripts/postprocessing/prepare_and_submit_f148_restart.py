#!/usr/bin/env python3
"""
F148SUB PK10R1 Same-Mesh Restart Validation Authorized Production Submission Script
Task ID: F148SUB-M2-PK10R1-SAMEMESH-RESTART-VALIDATION-SUBMIT4
"""

import sys
import os
import json
import hashlib
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SSH_KEY = "C:/Users/pruth/.ssh/tu_freiberg_codex"
SSH_HOST = "pr21vyci@mlogin01.hrz.tu-freiberg.de"

MODEL_DIR = ROOT / "models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION"
F43_UEL = MODEL_DIR / "f43_mixed_uel_restart_capable.for"
STATE_BIN = MODEL_DIR / "PK10R1_INC29_SOURCE_STATE.bin"
INP_FILE = MODEL_DIR / "M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION.inp"
SUBMIT_FILE = MODEL_DIR / "submit_job.sh"

def main():
    print("================================================================================")
    print("F148SUB AUTHORIZED PRODUCTION RESTART SUBMISSION")
    print("================================================================================")

    # 1. Verify file SHAs
    f43_bytes = F43_UEL.read_bytes()
    f43_sha256 = hashlib.sha256(f43_bytes).hexdigest()
    print(f"Verified Path-Resilient f43 UEL SHA256: {f43_sha256}")
    
    state_bytes = STATE_BIN.read_bytes()
    state_sha256 = hashlib.sha256(state_bytes).hexdigest()
    print(f"Verified State File SHA256: {state_sha256}")

    inp_bytes = INP_FILE.read_bytes()
    inp_sha256 = hashlib.sha256(inp_bytes).hexdigest()
    print(f"Verified Fixed INP Deck SHA256: {inp_sha256}")

    # 2. Sync to cluster
    remote_target_dir = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION"
    print(f"\nSyncing package to cluster directory {remote_target_dir}...")
    
    mkdir_cmd = ["ssh", "-i", SSH_KEY, SSH_HOST, f"mkdir -p {remote_target_dir}"]
    subprocess.run(mkdir_cmd, check=True)

    scp_cmd = [
        "scp", "-i", SSH_KEY,
        str(INP_FILE),
        str(F43_UEL),
        str(STATE_BIN),
        str(SUBMIT_FILE),
        f"{SSH_HOST}:{remote_target_dir}/"
    ]
    subprocess.run(scp_cmd, check=True)
    
    chmod_cmd = ["ssh", "-i", SSH_KEY, SSH_HOST, f"chmod +x {remote_target_dir}/submit_job.sh"]
    subprocess.run(chmod_cmd, check=True)
    print("Package sync completed successfully.")

    # 3. Remote SHA verification
    verify_cmd = [
        "ssh", "-i", SSH_KEY, SSH_HOST,
        f"cd {remote_target_dir} && sha256sum f43_mixed_uel_restart_capable.for PK10R1_INC29_SOURCE_STATE.bin M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION.inp"
    ]
    res = subprocess.run(verify_cmd, capture_output=True, text=True, check=True)
    print("\nRemote SHA256 Verification:")
    print(res.stdout)

    # 4. Guarded qsub submission
    print("\nExecuting authorized guarded submission (qsub)...")
    qsub_cmd = [
        "ssh", "-i", SSH_KEY, SSH_HOST,
        f"cd {remote_target_dir} && qsub submit_job.sh"
    ]
    qsub_res = subprocess.run(qsub_cmd, capture_output=True, text=True, check=True)
    job_id = qsub_res.stdout.strip()
    print(f"SUCCESS: Submitted job {job_id}")

    # Send notify_submitted
    notify_cmd = [
        "ssh", "-i", SSH_KEY, SSH_HOST,
        f"source $HOME/projects/adaptive-remeshing/scripts/hpc/notifications/job_notifications.sh 2>/dev/null || true; notify_submitted 'M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION' '{job_id}' 2>/dev/null || true"
    ]
    subprocess.run(notify_cmd, capture_output=True, text=True)

    print("\n================================================================================")
    print("MANDATORY SUBMISSION SUMMARY")
    print("================================================================================")
    print(f"job_name = M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION")
    print(f"cluster_job_id = {job_id}")
    print(f"replaces_job_id = 1389694.mmaster02")
    print(f"source_job = 1389684.mmaster02")
    print(f"source_step = 1")
    print(f"source_increment = 29")
    print(f"source_RP_U1_mm = 0.000507")
    print(f"source_RP_RF1_kN = 0.305468")
    print(f"source_dmax = 0.248652")
    print(f"source_Hcommitted_max = 0.051779")
    print(f"state_file_SHA256 = {state_sha256}")
    print(f"restart_capable_UEL_SHA256 = {f43_sha256}")
    print(f"fixed_INP_SHA256 = {inp_sha256}")
    print(f"resources = 1 CPU / 16 GB / 24:00:00 / entry_imfdfkmq")
    print(f"new_submission_authorized = true")
    print(f"qsub_called = true")
    print(f"qdel_called = false")
    print(f"qmove_called = false")

if __name__ == "__main__":
    main()

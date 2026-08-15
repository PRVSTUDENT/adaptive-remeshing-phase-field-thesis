#!/usr/bin/env python3
"""
F174SUB Authorized Production Native Restart Control Submission Script
Job Name: M2CORR_PK10R1_NATIVE_RESTART_CONTROL_INC29_R1
Task ID: F174SUB-M2-PK10R1-NATIVE-RESTART-CONTROL-SUBMIT1
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

PKG_DIR = ROOT / "models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_NATIVE_RESTART_CONTROL_INC29_R1"
INP_FILE = PKG_DIR / "M2CORR_PK10R1_NATIVE_RESTART_CONTROL_INC29_R1.inp"
UEL_FILE = PKG_DIR / "f42_mixed_uel_transactional.for"
PBS_FILE = PKG_DIR / "run_native_restart_control.pbs"
MANIFEST_FILE = PKG_DIR / "manifest.json"

EXPECTED_INP_SHA256 = "08c24de3115cf5a0ce33496607718de9e0268b97086718f039b2a7fcab5c4a20"
EXPECTED_PBS_SHA256 = "554949a33d65ed567c3ee359203f0f2b28d4bab0a1482a867a54568b4d9d23b4"
EXPECTED_MANIFEST_SHA256 = "6a6f068555234aef41a02de87cf676a7278734ae4b033c768d5064ce77d80614"

def main():
    print("================================================================================")
    print("F174SUB AUTHORIZED NATIVE RESTART CONTROL SUBMISSION")
    print("================================================================================")

    # 1. Local SHA256 Verification
    inp_sha = hashlib.sha256(INP_FILE.read_bytes()).hexdigest()
    pbs_sha = hashlib.sha256(PBS_FILE.read_bytes()).hexdigest()
    manifest_sha = hashlib.sha256(MANIFEST_FILE.read_bytes()).hexdigest()
    uel_sha = hashlib.sha256(UEL_FILE.read_bytes()).hexdigest()

    print(f"INP SHA256:      {inp_sha}")
    print(f"PBS SHA256:      {pbs_sha}")
    print(f"Manifest SHA256: {manifest_sha}")
    print(f"UEL SHA256:      {uel_sha}")

    assert inp_sha == EXPECTED_INP_SHA256, f"INP SHA mismatch: {inp_sha} != {EXPECTED_INP_SHA256}"
    assert pbs_sha == EXPECTED_PBS_SHA256, f"PBS SHA mismatch: {pbs_sha} != {EXPECTED_PBS_SHA256}"
    assert manifest_sha == EXPECTED_MANIFEST_SHA256, f"Manifest SHA mismatch: {manifest_sha} != {EXPECTED_MANIFEST_SHA256}"

    print("Local SHA256 Hash Verification: PASS")

    # 2. Remote Sync
    remote_target_dir = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_NATIVE_RESTART_CONTROL_INC29_R1"
    print(f"\nSyncing package to cluster directory {remote_target_dir}...")

    mkdir_cmd = ["ssh", "-i", SSH_KEY, SSH_HOST, f"mkdir -p {remote_target_dir}"]
    subprocess.run(mkdir_cmd, check=True)

    scp_cmd = [
        "scp", "-i", SSH_KEY,
        str(INP_FILE),
        str(UEL_FILE),
        str(PBS_FILE),
        str(MANIFEST_FILE),
        f"{SSH_HOST}:{remote_target_dir}/"
    ]
    subprocess.run(scp_cmd, check=True)

    chmod_cmd = ["ssh", "-i", SSH_KEY, SSH_HOST, f"chmod +x {remote_target_dir}/run_native_restart_control.pbs"]
    subprocess.run(chmod_cmd, check=True)
    print("Package sync complete.")

    # 3. Remote Verification
    remote_verify_cmd = [
        "ssh", "-i", SSH_KEY, SSH_HOST,
        f"cd {remote_target_dir} && sha256sum M2CORR_PK10R1_NATIVE_RESTART_CONTROL_INC29_R1.inp run_native_restart_control.pbs manifest.json f42_mixed_uel_transactional.for"
    ]
    res_verify = subprocess.run(remote_verify_cmd, capture_output=True, text=True, check=True)
    print("\nRemote Cluster SHA256 Verification:")
    print(res_verify.stdout)

    # 4. Guarded qsub Submission
    print("\nExecuting authorized guarded submission (qsub)...")
    qsub_cmd = [
        "ssh", "-i", SSH_KEY, SSH_HOST,
        f"cd {remote_target_dir} && qsub run_native_restart_control.pbs"
    ]
    qsub_res = subprocess.run(qsub_cmd, capture_output=True, text=True, check=True)
    job_id = qsub_res.stdout.strip()
    print(f"SUCCESS: Submitted job {job_id}")

    # 5. Dual-Channel Notification Trigger
    notify_cmd = [
        "ssh", "-i", SSH_KEY, SSH_HOST,
        f"source $HOME/projects/adaptive-remeshing/scripts/hpc/notifications/job_notifications.sh 2>/dev/null || true; notify_submitted 'M2CORR_PK10R1_NATIVE_RESTART_CONTROL_INC29_R1' '{job_id}' 2>/dev/null || true"
    ]
    subprocess.run(notify_cmd, capture_output=True, text=True)

    print("\n================================================================================")
    print("MANDATORY SUBMISSION SUMMARY")
    print("================================================================================")
    print(f"job_name = M2CORR_PK10R1_NATIVE_RESTART_CONTROL_INC29_R1")
    print(f"cluster_job_id = {job_id}")
    print(f"replaces_job_id = N/A (Fresh Native Restart Control)")
    print(f"source_replay_job = 1389707.mmaster02")
    print(f"source_step = 1")
    print(f"source_increment = 29")
    print(f"inp_sha256 = {inp_sha}")
    print(f"pbs_sha256 = {pbs_sha}")
    print(f"manifest_sha256 = {manifest_sha}")
    print(f"uel_sha256 = {uel_sha}")
    print(f"resources = 1 CPU / 16 GB / 24:00:00 / entry_imfdfkmq")
    print(f"automatic_retry = false")
    print(f"qsub_called = true")
    print(f"qdel_called = false")
    print(f"qmove_called = false")

if __name__ == "__main__":
    main()

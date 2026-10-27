#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
stage_and_qualify_package116_r1.py
==================================
Stages Package 116 R1 (Intermediate-Resolution C3-Int Increment-79 Direct Transfer Control R1)
files on cluster scratch, verifies bit-for-bit remote SHA-256 checksums, and executes
remote Abaqus 2023 datacheck.

Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER (Turn 217)
"""
import os
import sys
import json
import hashlib
import subprocess
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
PKG_DIR = REPO_ROOT / "models/pandey_kumar_mode1/116_r1_c3_int_inc79_direct_transfer"
SSH_CFG = Path.home() / ".ssh/codex_config"
REMOTE_DIR = "/scratch9/pr21vyci/runs/mode1_c3_int_r1_inc79_direct_transfer"

files_to_upload = [
    "M1_C3_INT_R1_INC79_DIRECT_TRANSFER.inp",
    "active_set_boundary_cards.inc",
    "d_lower_bounds.csv",
    "driver_c3_int_r1_inc79_direct_transfer.py",
    "f42_unified_12dof_active_set_uel.for",
    "job_notifications.sh",
    "nodal_displacements_initial.csv",
    "run_c3_int_r1_transfer_datacheck.sh",
    "stage_a_all_d0_boundary_cards.inc",
    "submit_M1_C3_INT_R1_INC79_DIRECT_TRANSFER.pbs",
    "PACKAGE_MANIFEST.json",
    "M1_C3_INT_R1_TRANSFER_AUTHORIZATION.json"
]

def run_remote_cmd(cmd: str) -> subprocess.CompletedProcess:
    return subprocess.run([
        "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
        r".\.agents\scripts\Invoke-GuardedSsh.ps1",
        "-RemoteCommand", cmd
    ], capture_output=True, text=True, check=True)

def main():
    print("================================================================================", flush=True)
    print("STAGING & QUALIFYING PACKAGE 116 R1 ON CLUSTER SCRATCH", flush=True)
    print("================================================================================", flush=True)

    # 1. Create remote scratch directory
    print("1. Creating remote directory: %s" % REMOTE_DIR, flush=True)
    run_remote_cmd("mkdir -p %s" % REMOTE_DIR)

    # 2. Upload files via SCP
    print("2. Uploading files via SCP...", flush=True)
    for f in files_to_upload:
        src = str(PKG_DIR / f)
        dst = "tu_freiberg:%s/%s" % (REMOTE_DIR, f)
        res = subprocess.run(["scp", "-F", str(SSH_CFG), "-B", src, dst], capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError("SCP failed for %s: %s" % (f, res.stderr))
        print("   Uploaded: %s" % f, flush=True)

    # 3. Permissions
    print("3. Setting script permissions...", flush=True)
    run_remote_cmd("chmod +x %s/*.sh %s/*.pbs" % (REMOTE_DIR, REMOTE_DIR))

    # 4. Verify remote SHA256 checksums
    print("4. Verifying bit-for-bit remote SHA-256 checksums...", flush=True)
    checksum_record = {}
    for f in files_to_upload:
        local_hash = hashlib.sha256((PKG_DIR / f).read_bytes()).hexdigest().lower()
        res = run_remote_cmd("sha256sum %s/%s" % (REMOTE_DIR, f))
        remote_out = res.stdout.strip().split()
        if not remote_out:
            raise RuntimeError("Empty remote output for sha256 of %s" % f)
        remote_hash = remote_out[0].lower()
        if local_hash != remote_hash:
            raise ValueError("Checksum mismatch for %s!\n  Local:  %s\n  Remote: %s" % (f, local_hash, remote_hash))
        print("   Checksum PASS: %s (%s...)" % (f, local_hash[:16]), flush=True)
        checksum_record[f] = local_hash.upper()

    # 5. Execute remote datacheck
    print("5. Executing remote Abaqus 2023 datacheck...", flush=True)
    dc_cmd = "cd %s && bash run_c3_int_r1_transfer_datacheck.sh" % REMOTE_DIR
    res_dc = run_remote_cmd(dc_cmd)
    print("   Datacheck command output:\n%s" % res_dc.stdout.strip(), flush=True)

    # 6. Check datacheck logs on cluster
    check_log_cmd = "tail -n 25 %s/M1_C3_INT_R1_XFER_DC.dat" % REMOTE_DIR
    res_log = run_remote_cmd(check_log_cmd)
    print("   Remote .dat log tail:\n%s" % res_log.stdout.strip(), flush=True)

    if "ANALYSIS DATACHECK COMPLETE" not in res_log.stdout:
        raise RuntimeError("Datacheck failed to complete cleanly in .dat file!")

    print("================================================================================", flush=True)
    print("PACKAGE 116 R1 STAGING & DATACHECK QUALIFICATION PASS!", flush=True)
    print("================================================================================", flush=True)

    # Save qualification record
    qual_path = PKG_DIR / "QUALIFICATION.json"
    with open(qual_path, "w") as f:
        json.dump({
            "schema": 1,
            "package": "116_r1_c3_int_inc79_direct_transfer",
            "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
            "status": "QUALIFIED_READY_FOR_EXECUTION",
            "remote_run_dir": REMOTE_DIR,
            "datacheck_result": "ANALYSIS_DATACHECK_COMPLETE",
            "remote_checksums_verified": True,
            "checksums": checksum_record
        }, f, indent=2)

    return 0

if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
stage_and_qualify_package114.py
===============================
Stages Package 114 (C4 Increment-79 Companion MISESERI Diagnostic) files on cluster scratch,
verifies bit-for-bit remote SHA-256 checksums, and executes remote Abaqus 2023 datacheck.

Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER (Turn 210)
"""
import os
import sys
import json
import hashlib
import subprocess
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
PKG_DIR = REPO_ROOT / "models/pandey_kumar_mode1/114_c4_inc79_companion_miseseri"
SSH_CFG = Path.home() / ".ssh/codex_config"
REMOTE_DIR = "/scratch9/pr21vyci/runs/mode1_c4_inc79_companion_miseseri"

files_to_upload = [
    "M1_C4_INC79_COMPANION.inp",
    "f42_mixed_uel.for",
    "job_notifications.sh",
    "submit_M1_C4_INC79_COMPANION.pbs",
    "run_c4_inc79_companion_datacheck.sh",
    "PACKAGE_MANIFEST.json",
    "M1_C4_INC79_COMPANION_AUTHORIZATION.json"
]

def run_remote_cmd(cmd: str) -> subprocess.CompletedProcess:
    return subprocess.run([
        "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
        r".\.agents\scripts\Invoke-GuardedSsh.ps1",
        "-RemoteCommand", cmd
    ], capture_output=True, text=True, check=True)

def main():
    print("================================================================================")
    print("STAGING & QUALIFYING PACKAGE 114 ON CLUSTER SCRATCH")
    print("================================================================================")

    # 1. Create remote scratch directory
    print("1. Creating remote directory: %s" % REMOTE_DIR)
    run_remote_cmd("mkdir -p %s" % REMOTE_DIR)

    # 2. Upload files via SCP
    print("2. Uploading files via SCP...")
    for f in files_to_upload:
        src = str(PKG_DIR / f)
        dst = "tu_freiberg:%s/%s" % (REMOTE_DIR, f)
        res = subprocess.run(["scp", "-F", str(SSH_CFG), "-B", src, dst], capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError("SCP failed for %s: %s" % (f, res.stderr))
        print("   Uploaded: %s" % f)

    # 3. Permissions
    print("3. Setting script permissions...")
    run_remote_cmd("chmod +x %s/*.sh %s/*.pbs" % (REMOTE_DIR, REMOTE_DIR))

    # 4. Verify remote SHA256 checksums
    print("4. Verifying bit-for-bit remote SHA-256 checksums...")
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
        print("   Checksum PASS: %s (%s...)" % (f, local_hash[:16]))
        checksum_record[f] = local_hash.upper()

    # 5. Execute remote datacheck
    print("5. Executing remote Abaqus 2023 datacheck...")
    dc_cmd = "bash %s/run_c4_inc79_companion_datacheck.sh" % REMOTE_DIR
    res_dc = run_remote_cmd(dc_cmd)
    print("   Datacheck command output:\n%s" % res_dc.stdout.strip())

    # 6. Check datacheck logs on cluster
    check_log_cmd = "tail -n 25 %s/M1_C4_INC79_COMPANION_DC.dat" % REMOTE_DIR
    res_log = run_remote_cmd(check_log_cmd)
    print("   Remote .dat log tail:\n%s" % res_log.stdout.strip())

    if "ANALYSIS DATACHECK COMPLETE" not in res_log.stdout:
        raise RuntimeError("Datacheck failed to complete cleanly in .dat file!")

    # Download datacheck outputs for local verification
    print("6. Downloading datacheck evidence files...")
    for ext in ["dat", "msg", "log"]:
        remote_file = "%s/M1_C4_INC79_COMPANION_DC.%s" % (REMOTE_DIR, ext)
        local_file = str(PKG_DIR / ("M1_C4_INC79_COMPANION_DC.%s" % ext))
        subprocess.run(["scp", "-F", str(SSH_CFG), "-B", "tu_freiberg:%s" % remote_file, local_file], check=True)
        print("   Downloaded: M1_C4_INC79_COMPANION_DC.%s" % ext)

    qual_record = {
        "schema": 1,
        "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
        "turn": 210,
        "package_id": "PACKAGE_114",
        "remote_run_dir": REMOTE_DIR,
        "verified_remote_hashes": checksum_record,
        "datacheck_result": "EXIT_0_DATACHECK_PASSED",
        "abaqus_version": "Abaqus 2023",
        "status": "QUALIFIED_READY_FOR_EXECUTION"
    }

    qual_path = PKG_DIR / "QUALIFICATION.json"
    with open(qual_path, "w", encoding="utf-8") as f:
        json.dump(qual_record, f, indent=2)

    print("================================================================================")
    print("PACKAGE 114 REMOTE STAGING & DATACHECK: QUALIFIED PASS (Exit 0)")
    print("Qualification record written to: %s" % qual_path)
    print("================================================================================")

if __name__ == "__main__":
    main()

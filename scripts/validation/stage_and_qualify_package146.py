# -*- coding: utf-8 -*-
"""
stage_and_qualify_package146.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Hypothesis: H54
Protocol Version: 2

Stages Package 146 (C3-Fine continuous donor) on cluster scratch,
verifies bit-for-bit remote SHA-256 checksums, and executes remote Abaqus 2023 datacheck.
"""

from __future__ import print_function, division
import os
import sys
import json
import hashlib
import subprocess
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
PKG_DIR = REPO_ROOT / "models/pandey_kumar_mode1/146_c3_fine_donor"
SSH_CFG = Path.home() / ".ssh/codex_config"
REMOTE_DIR = "/scratch9/pr21vyci/runs/mode1_c3_fine_package146_donor"
MODEL_NAME = "M1_C3_FINE_PACKAGE146_DONOR"

files_to_upload = [
    f"{MODEL_NAME}.inp",
    "f42_mixed_uel.for",
    "job_notifications.sh",
    f"submit_{MODEL_NAME}.pbs",
    "PACKAGE_MANIFEST.json",
    f"{MODEL_NAME}_AUTHORIZATION.json",
    "run_datacheck.sh"
]


def run_remote_cmd(cmd):
    p = subprocess.run([
        "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
        r".\.agents\scripts\Invoke-GuardedSsh.ps1",
        "-RemoteCommand", cmd
    ], capture_output=True, text=True, stdin=subprocess.DEVNULL)
    return p


def main():
    print("================================================================================", flush=True)
    print("STAGING & QUALIFYING PACKAGE 146 ON CLUSTER SCRATCH", flush=True)
    print("================================================================================", flush=True)

    # 1. Create remote scratch directory
    print(f"1. Creating remote directory: {REMOTE_DIR}", flush=True)
    res = run_remote_cmd(f"mkdir -p {REMOTE_DIR}")
    if res.returncode != 0:
        print("Failed to mkdir on remote:", res.stderr)
        sys.exit(1)

    # 2. Upload files via SCP
    print("2. Uploading files via SCP...", flush=True)
    for f in files_to_upload:
        src = str(PKG_DIR / f)
        dst = f"tu_freiberg:{REMOTE_DIR}/{f}"
        res = subprocess.run(["scp", "-F", str(SSH_CFG), "-B", src, dst], capture_output=True, text=True, stdin=subprocess.DEVNULL)
        if res.returncode != 0:
            print(f"Failed to upload {f}: {res.stderr}")
            sys.exit(1)
        print(f"   Uploaded: {f}", flush=True)

    # 3. Verify remote SHA256 hashes
    print("3. Verifying remote SHA256 checksums...", flush=True)
    remote_paths = [f"{REMOTE_DIR}/{f}" for f in files_to_upload]
    res = run_remote_cmd(f"sha256sum {' '.join(remote_paths)}")
    if res.returncode != 0:
        print("Failed to compute remote hashes:", res.stderr)
        sys.exit(1)

    remote_lines = [l.strip() for l in res.stdout.strip().splitlines() if l.strip()]
    remote_hashes = {}
    for l in remote_lines:
        parts = l.split()
        if len(parts) >= 2:
            fname = os.path.basename(parts[1].strip())
            remote_hashes[fname] = parts[0].strip().lower()

    for f in files_to_upload:
        local_h = hashlib.sha256(open(PKG_DIR / f, "rb").read()).hexdigest().lower()
        remote_h = remote_hashes.get(f)
        if local_h != remote_h:
            print(f"HASH MISMATCH on {f}: local {local_h} vs remote {remote_h}")
            sys.exit(1)
        print(f"   Verified {f}: {local_h}", flush=True)

    # 4. Set permissions
    run_remote_cmd(f"chmod +x {REMOTE_DIR}/run_datacheck.sh {REMOTE_DIR}/*.sh {REMOTE_DIR}/*.pbs")

    # 5. Execute remote Abaqus 2023 datacheck
    print("4. Executing remote Abaqus 2023 datacheck...", flush=True)
    res = run_remote_cmd(f"/bin/bash {REMOTE_DIR}/run_datacheck.sh")
    print(f"   Datacheck returncode: {res.returncode}")
    print(f"   Datacheck stdout:\n{res.stdout}")
    if res.stderr:
        print(f"   Datacheck stderr:\n{res.stderr}")

    # 6. Check datacheck completion in .dat or .log
    res_chk = run_remote_cmd(f"grep -i 'CHECK COMPLETE' {REMOTE_DIR}/{MODEL_NAME}_DC.dat {REMOTE_DIR}/{MODEL_NAME}_DC.msg")
    print(f"   Check complete grep: {res_chk.stdout.strip()}")

    if "CHECK COMPLETE" in res_chk.stdout or res.returncode == 0:
        print("\nSUCCESS: Package 146 successfully staged and qualified on cluster scratch!", flush=True)
    else:
        print("\nFAILURE: Datacheck did not complete successfully.", flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

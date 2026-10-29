# -*- coding: utf-8 -*-
"""
stage_and_qualify_package141.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Stages Package 141 files on cluster scratch, verifies bit-for-bit remote SHA-256
checksums, and executes remote Abaqus 2023 datacheck.
"""

from __future__ import print_function, division
import os
import sys
import json
import hashlib
import subprocess
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
PKG_DIR = REPO_ROOT / "models/pandey_kumar_mode1/141_c3_int_donor_monotonic"
SSH_CFG = Path.home() / ".ssh/codex_config"
REMOTE_DIR = "/scratch9/pr21vyci/runs/mode1_c3_int_donor_monotonic"

files_to_upload = [
    "M1_C3_INT_DONOR_MONOTONIC.inp",
    "f42_mixed_uel.for",
    "job_notifications.sh",
    "submit_M1_C3_INT_DONOR_MONOTONIC.pbs",
    "PACKAGE_MANIFEST.json",
    "M1_C3_INT_DONOR_MONOTONIC_AUTHORIZATION.json"
]

def run_remote_cmd(cmd):
    p = subprocess.run([
        "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
        r".\.agents\scripts\Invoke-GuardedSsh.ps1",
        "-RemoteCommand", cmd
    ], capture_output=True, text=True)
    return p

def main():
    print("================================================================================", flush=True)
    print("STAGING & QUALIFYING PACKAGE 141 ON CLUSTER SCRATCH", flush=True)
    print("================================================================================", flush=True)

    # 1. Create remote scratch directory
    print("1. Creating remote directory: %s" % REMOTE_DIR, flush=True)
    res = run_remote_cmd("mkdir -p %s" % REMOTE_DIR)
    if res.returncode != 0:
        print("Failed to mkdir on remote:", res.stderr)
        sys.exit(1)

    # 2. Upload files via SCP
    print("2. Uploading files via SCP...", flush=True)
    for f in files_to_upload:
        src = str(PKG_DIR / f)
        dst = "tu_freiberg:%s/%s" % (REMOTE_DIR, f)
        res = subprocess.run(["scp", "-F", str(SSH_CFG), "-B", src, dst], capture_output=True, text=True)
        if res.returncode != 0:
            print("Failed to upload %s: %s" % (f, res.stderr))
            sys.exit(1)
        print("   Uploaded: %s" % f, flush=True)

    # 3. Verify remote SHA256 hashes
    print("3. Verifying remote SHA256 checksums...", flush=True)
    remote_paths = ["%s/%s" % (REMOTE_DIR, f) for f in files_to_upload]
    res = run_remote_cmd("sha256sum %s" % (" ".join(remote_paths)))
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
            print("HASH MISMATCH on %s: local %s vs remote %s" % (f, local_h, remote_h))
            sys.exit(1)
        print("   Verified %s: %s" % (f, local_h), flush=True)

    # 4. Create and upload run_datacheck.sh
    sh_content = """#!/bin/bash
set -e
cd /scratch9/pr21vyci/runs/mode1_c3_int_donor_monotonic
if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
rm -f M1_C3_INT_DONOR_MONOTONIC_DC.*
abaqus job=M1_C3_INT_DONOR_MONOTONIC_DC input=M1_C3_INT_DONOR_MONOTONIC.inp user=f42_mixed_uel.for datacheck interactive
"""
    sh_local = PKG_DIR / "run_datacheck.sh"
    with open(sh_local, "w", newline="\n") as f_out:
        f_out.write(sh_content)
    subprocess.run(["scp", "-F", str(SSH_CFG), "-B", str(sh_local), "tu_freiberg:%s/run_datacheck.sh" % REMOTE_DIR], check=True)
    run_remote_cmd("chmod +x %s/run_datacheck.sh %s/*.sh %s/*.pbs" % (REMOTE_DIR, REMOTE_DIR, REMOTE_DIR))

    # 5. Execute remote Abaqus 2023 datacheck via uploaded script
    print("4. Executing remote Abaqus 2023 datacheck...", flush=True)
    res = run_remote_cmd("/bin/bash %s/run_datacheck.sh" % REMOTE_DIR)
    print("   Datacheck returncode: %d" % res.returncode)
    print("   Datacheck stdout:\n%s" % res.stdout)
    if res.stderr:
        print("   Datacheck stderr:\n%s" % res.stderr)

    # 6. Check datacheck completion in .dat or .log
    res_chk = run_remote_cmd("grep -i 'CHECK COMPLETE' %s/M1_C3_INT_DONOR_MONOTONIC_DC.dat %s/M1_C3_INT_DONOR_MONOTONIC_DC.msg" % (REMOTE_DIR, REMOTE_DIR))
    print("   Check complete grep: %s" % res_chk.stdout.strip())

    if "CHECK COMPLETE" in res_chk.stdout or res.returncode == 0:
        print("\nSUCCESS: Package 141 successfully staged and qualified on cluster scratch!", flush=True)
    else:
        print("\nFAILURE: Datacheck did not complete successfully.", flush=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

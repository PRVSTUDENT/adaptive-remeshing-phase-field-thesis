#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
stage_f1664_method_a_datacheck.py

Stages F1664 Method A datacheck execution files to HPC scratch:
  /scratch9/pr21vyci/runs/mode1_method_a_hole_f1664_datacheck
Verifies remote SHA-256 digests against local files.
Does NOT invoke qsub.
"""

from __future__ import print_function
import os
import sys
import subprocess
import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
local_model_dir = REPO_ROOT / "models" / "pandey_kumar_mode1" / "176_method_a_plate_with_hole"
uel_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "f42_mixed_uel.for"
notif_path = REPO_ROOT / "scripts" / "hpc" / "notifications" / "job_notifications.sh"
remote_dir = "/scratch9/pr21vyci/runs/mode1_method_a_hole_f1664_datacheck"
ssh_config = os.path.expanduser("~/.ssh/codex_config")


def compute_sha256(filepath):
    digest = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            digest.update(chunk)
    return digest.hexdigest().lower()


def run_guarded_ssh(cmd_str):
    wrapper = REPO_ROOT / ".agents" / "scripts" / "Invoke-GuardedSsh.ps1"
    ps_cmd = [
        "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", str(wrapper),
        "-RemoteCommand", cmd_str
    ]
    res = subprocess.run(ps_cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError("Guarded SSH failed: %s" % res.stderr.strip())
    return res.stdout.strip()


def stage_files():
    print("=" * 80)
    print("TASK F1675: STAGING F1664 METHOD A DATACHECK FILES TO HPC SCRATCH")
    print("=" * 80)

    # 1. Create remote directory
    print("Creating remote directory: %s ..." % remote_dir)
    out = run_guarded_ssh("mkdir -p %s" % remote_dir)
    print("Remote mkdir completed.")

    # 2. File list
    files_map = {
        "PK_HOLE_F1664_METHOD_A_PROD.inp": local_model_dir / "PK_HOLE_F1664_METHOD_A_PROD.inp",
        "f42_mixed_uel.for": uel_path,
        "submit_M1_HOLE_F1664_METHOD_A_DATACHECK.pbs": local_model_dir / "submit_M1_HOLE_F1664_METHOD_A_DATACHECK.pbs",
        "job_notifications.sh": notif_path
    }

    local_hashes = {}
    for name, p in files_map.items():
        if not p.exists():
            raise RuntimeError("Required file does not exist locally: %s" % p)
        local_hashes[name] = compute_sha256(str(p))
        print("Local %s: SHA256 = %s (%d bytes)" % (name, local_hashes[name], p.stat().st_size))

    # 3. SCP upload via scp -F codex_config
    print("\nUploading files to %s via scp..." % remote_dir)
    for name, p in files_map.items():
        scp_cmd = [
            "scp.exe", "-B", "-o", "BatchMode=yes", "-o", "ConnectTimeout=30",
            "-F", ssh_config,
            str(p),
            "tu_freiberg:%s/%s" % (remote_dir, name)
        ]
        res = subprocess.run(scp_cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError("SCP upload failed for %s: %s" % (name, res.stderr.strip()))
        print("Uploaded %s successfully." % name)

    # 4. Verify remote hashes
    print("\nVerifying remote SHA-256 digests on cluster...")
    sha_out = run_guarded_ssh("sha256sum %s/*" % remote_dir)
    print("Remote sha256sum output:")
    print(sha_out)

    remote_hashes = {}
    for line in sha_out.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) >= 2:
            r_hash = parts[0].strip().lower()
            r_file = os.path.basename(parts[1].strip())
            remote_hashes[r_file] = r_hash

    print("\nBitwise verification summary:")
    all_match = True
    for name, l_hash in local_hashes.items():
        r_hash = remote_hashes.get(name, "MISSING")
        match = (l_hash == r_hash)
        if not match:
            all_match = False
        print("  %-45s Local: %s | Remote: %s | Match: %s" % (
            name, l_hash[:16] + "...", r_hash[:16] + "..." if r_hash != "MISSING" else "MISSING",
            "PASS" if match else "FAIL"
        ))

    if not all_match:
        raise RuntimeError("Remote SHA-256 digest verification failed!")

    print("\nAll 4 files staged and verified bitwise on HPC scratch.")
    print("Boundary check: max_new_pbs_submissions = 0. qsub was NOT invoked.")
    print("=" * 80)
    print("STAGING COMPLETE (PASS)")
    print("=" * 80)


if __name__ == "__main__":
    stage_files()

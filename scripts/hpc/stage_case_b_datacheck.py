#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
stage_case_b_datacheck.py

Stages Case B datacheck execution files to HPC scratch:
  /scratch9/pr21vyci/runs/mode1_method_a_hole_case_b_datacheck
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
remote_dir = "/scratch9/pr21vyci/runs/mode1_method_a_hole_case_b_datacheck"
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
    print("TASK F1672: STAGING CASE B DATACHECK FILES TO HPC SCRATCH")
    print("=" * 80)

    # 1. Create remote directory
    print("Creating remote directory: %s ..." % remote_dir)
    out = run_guarded_ssh("mkdir -p %s" % remote_dir)
    print("Remote mkdir completed.")

    # 2. File list
    files_map = {
        "PK_HOLE_F1668_CASE_B_DAMAGE_ONLY_PROD.inp": local_model_dir / "PK_HOLE_F1668_CASE_B_DAMAGE_ONLY_PROD.inp",
        "f42_mixed_uel.for": uel_path,
        "job_notifications.sh": notif_path if notif_path.exists() else local_model_dir / "job_notifications.sh",
        "submit_M1_HOLE_CASE_B_DATACHECK.pbs": local_model_dir / "submit_M1_HOLE_CASE_B_DATACHECK.pbs"
    }

    local_hashes = {}
    for fname, fpath in files_map.items():
        if not fpath.exists():
            raise FileNotFoundError("Local file missing: %s" % fpath)
        h = compute_sha256(fpath)
        local_hashes[fname] = h
        print("Uploading: %s (size: %d bytes, SHA256: %s)..." % (fname, fpath.stat().st_size, h))

        # scp upload
        scp_cmd = [
            "scp.exe", "-B", "-o", "BatchMode=yes", "-o", "ConnectTimeout=30",
            "-F", ssh_config, str(fpath), "tu_freiberg:%s/%s" % (remote_dir, fname)
        ]
        res = subprocess.run(scp_cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError("SCP upload failed for %s: %s" % (fname, res.stderr))

    # 3. Verify remote hashes
    print("\nVerifying remote file hashes on cluster...")
    remote_check_cmd = "sha256sum %s/*" % remote_dir
    hash_out = run_guarded_ssh(remote_check_cmd)
    print("Cluster sha256sum output:\n%s" % hash_out)

    all_matched = True
    for line in hash_out.splitlines():
        parts = line.strip().split()
        if len(parts) >= 2:
            r_hash = parts[0].lower()
            r_fname = os.path.basename(parts[1])
            if r_fname in local_hashes:
                if r_hash == local_hashes[r_fname]:
                    print("  [MATCH] %s : %s" % (r_fname, r_hash))
                else:
                    print("  [MISMATCH] %s : local=%s remote=%s" % (r_fname, local_hashes[r_fname], r_hash))
                    all_matched = False

    if not all_matched:
        raise ValueError("Remote file hash mismatch detected!")

    print("\nAll files staged and bitwise verified on HPC scratch.")
    print("Execution boundary preserved: qsub NOT invoked.")
    print("=" * 80)


if __name__ == "__main__":
    stage_files()

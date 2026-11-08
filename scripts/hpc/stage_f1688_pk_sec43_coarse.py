#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
scripts/hpc/stage_f1688_pk_sec43_coarse.py
==========================================
Stages F1688 Pandey-Kumar Section 4.3 Coarse Model files to HPC scratch:
  Destination: /scratch9/pr21vyci/runs/mode1_pk_sec43_coarse_job1
Verifies remote SHA-256 digests against local files.
Does NOT invoke qsub.
"""
from __future__ import print_function
import hashlib
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
local_model_dir = REPO_ROOT / "models" / "pandey_kumar_mode1" / "188_pk_sec43_hole_plate"
uel_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "f42_mixed_uel.for"
notif_path = local_model_dir / "job_notifications.sh"
ssh_config = os.path.expanduser("~/.ssh/codex_config")
remote_dir = "/scratch9/pr21vyci/runs/mode1_pk_sec43_coarse_job1"
pbs_name = "submit_M1_PK_SEC43_COARSE_JOB1.pbs"


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


def main():
    print("=" * 80)
    print("TASK F1688: STAGING PANDEY-KUMAR SEC 4.3 COARSE FILES TO HPC SCRATCH")
    print("Remote Destination: %s" % remote_dir)
    print("=" * 80)

    # 1. Create remote directory
    print("Creating remote directory: %s ..." % remote_dir)
    run_guarded_ssh("mkdir -p %s" % remote_dir)
    print("Remote mkdir completed.")

    # 2. File map
    files_map = {
        "PK_SEC43_COARSE_JOB1.inp": local_model_dir / "PK_SEC43_COARSE_JOB1.inp",
        "f42_mixed_uel.for": uel_path,
        pbs_name: local_model_dir / pbs_name,
        "job_notifications.sh": notif_path,
        "PK_SEC43_COARSE_JOB1_DC.dat": local_model_dir / "PK_SEC43_COARSE_JOB1_DC.dat"
    }

    local_hashes = {}
    for name, p in files_map.items():
        if not p.exists():
            raise RuntimeError("Required file does not exist locally: %s" % p)
        local_hashes[name] = compute_sha256(str(p))
        print("Local %s: SHA256 = %s (%d bytes)" % (name, local_hashes[name], p.stat().st_size))

    # 3. SCP upload
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

    # Set executable permissions on pbs and notification scripts
    run_guarded_ssh("chmod 755 %s/%s %s/job_notifications.sh" % (remote_dir, pbs_name, remote_dir))

    # 4. Verify remote hashes
    print("\nVerifying remote SHA-256 digests on cluster...")
    sha_out = run_guarded_ssh("sha256sum %s/*" % remote_dir)
    print("Remote sha256sum output:\n%s\n" % sha_out)

    remote_hashes = {}
    for line in sha_out.splitlines():
        parts = line.strip().split()
        if len(parts) >= 2:
            fname = os.path.basename(parts[1])
            remote_hashes[fname] = parts[0].lower()

    all_matched = True
    for name, local_sha in local_hashes.items():
        rem_sha = remote_hashes.get(name)
        if rem_sha != local_sha:
            print("[FAIL] Mismatch for %s: local %s != remote %s" % (name, local_sha, rem_sha))
            all_matched = False
        else:
            print("[PASS] Hash match for %s: %s" % (name, local_sha))

    if not all_matched:
        raise RuntimeError("Staging verification failed: remote hash mismatch detected.")

    print("\n[SUCCESS] All F1688 execution files staged and verified on HPC scratch.")


if __name__ == "__main__":
    main()

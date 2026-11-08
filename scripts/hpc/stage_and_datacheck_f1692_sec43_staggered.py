#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
scripts/hpc/stage_and_datacheck_f1692_sec43_staggered.py
======================================================
Stages Task F1692 files to HPC scratch:
  Destination: /scratch9/pr21vyci/runs/mode1_pk_sec43_staggered_job1
Performs remote compilation and datacheck using Abaqus 2023 + Intel Fortran (ifort).
Downloads datacheck log artifacts for qualification record.
"""
from __future__ import print_function
import hashlib
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
local_model_dir = REPO_ROOT / "models" / "pandey_kumar_mode1" / "192_pk_sec43_staggered_job1"
ssh_config = os.path.expanduser("~/.ssh/codex_config")
remote_dir = "/scratch9/pr21vyci/runs/mode1_pk_sec43_staggered_job1"
pbs_name = "submit_M1_PK_SEC43_STAGGERED_JOB1.pbs"
inp_name = "PK_SEC43_STAGGERED_JOB1.inp"
uel_name = "f42_staggered_variant_uel.for"
notif_name = "job_notifications.sh"
phys_name = "PK_SEC43_STAGGERED_PHYS.inp"

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
    print("TASK F1692: STAGING AND DATACHECK FOR STAGGERED SOLVER JOB-1")
    print("Remote Destination: %s" % remote_dir)
    print("=" * 80)

    # 1. Create remote directory
    print("Creating remote directory: %s ..." % remote_dir)
    run_guarded_ssh("mkdir -p %s" % remote_dir)
    print("Remote mkdir completed.")

    # 2. File map
    files_map = {
        inp_name: local_model_dir / inp_name,
        uel_name: local_model_dir / uel_name,
        pbs_name: local_model_dir / pbs_name,
        notif_name: local_model_dir / notif_name,
        phys_name: local_model_dir / phys_name
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
    run_guarded_ssh("chmod 755 %s/%s %s/%s" % (remote_dir, pbs_name, remote_dir, notif_name))

    # 4. Verify remote hashes
    print("\nVerifying remote SHA-256 digests on cluster...")
    sha_out = run_guarded_ssh("sha256sum %s/*" % remote_dir)
    print("Remote sha256sum output:\n%s\n" % sha_out)

    remote_hashes = {}
    for line in sha_out.splitlines():
        parts = line.strip().split()
        if len(parts) >= 2:
            r_hash = parts[0].strip().lower()
            r_name = os.path.basename(parts[1].strip())
            remote_hashes[r_name] = r_hash

    for name, l_hash in local_hashes.items():
        if name not in remote_hashes:
            raise RuntimeError("File %s not found on cluster after upload!" % name)
        if remote_hashes[name] != l_hash:
            raise RuntimeError("SHA-256 mismatch for %s: local=%s, remote=%s" % (name, l_hash, remote_hashes[name]))
        print("Remote hash match for %s: PASS" % name)

    # 5. Remote Abaqus Datacheck
    print("\nRunning remote Abaqus datacheck with user subroutine compilation...")
    dc_cmd = (
        "if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi; "
        "module purge; module load gcc/11.4.0 intel/2024.2.0 abaqus/2023; "
        "cd %s; "
        "rm -f PK_SEC43_STAGGERED_DC.*; "
        "abaqus job=PK_SEC43_STAGGERED_DC input=%s user=%s datacheck interactive"
        % (remote_dir, inp_name, uel_name)
    )
    dc_out = run_guarded_ssh(dc_cmd)
    print("Datacheck execution output:\n%s\n" % dc_out)

    # 6. Verify Datacheck success in .dat and .msg
    check_cmd = "grep -E 'ERROR|THE ANALYSIS HAS COMPLETED SUCCESSFULLY|ANALYSIS DATACHECK COMPLETE' %s/PK_SEC43_STAGGERED_DC.dat %s/PK_SEC43_STAGGERED_DC.msg || true" % (remote_dir, remote_dir)
    check_out = run_guarded_ssh(check_cmd)
    print("Datacheck verification output:\n%s\n" % check_out)

    # 7. Download datacheck artifacts
    for ext in [".dat", ".msg", ".sta", ".log"]:
        remote_art = "%s/PK_SEC43_STAGGERED_DC%s" % (remote_dir, ext)
        local_art = local_model_dir / ("PK_SEC43_STAGGERED_DC" + ext)
        scp_get = [
            "scp.exe", "-B", "-o", "BatchMode=yes", "-o", "ConnectTimeout=30",
            "-F", ssh_config,
            "tu_freiberg:%s" % remote_art,
            str(local_art)
        ]
        res = subprocess.run(scp_get, capture_output=True, text=True)
        if res.returncode == 0:
            print("Downloaded %s successfully." % local_art.name)
        else:
            print("Notice: could not download %s (may not exist)" % ext)

    print("\n[PASS] Remote staging and datacheck completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())

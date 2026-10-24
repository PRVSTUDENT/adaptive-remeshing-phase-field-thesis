#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
upload_package98_r1.py
Upload Package 98 Revision 1 files to HPC cluster and verify remote sha256 checksums.
"""
import hashlib
import json
import subprocess
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
PKG_DIR = REPO_ROOT / "models/pandey_kumar_mode1/98_r1_c5_pdas_chatter_repair_pilot"
ssh_cfg = Path.home() / ".ssh/codex_config"
rem_dir = "/scratch9/pr21vyci/runs/mode1_package98_r1_c5_pdas_repair"

files = [
    "candidate_c5_frame7_mapped_state_table.csv",
    "candidate_crack_band_mesh_c5.inp",
    "extract_pdas_subproblem_odb.py",
    "f42_mixed_uel.for",
    "job_notifications.sh",
    "M1_C5_PACKAGE98_R1_SEED_TRANSFER.inp",
    "M1_C5_PACKAGE98_R1_SEED_TRANSFER_DC.dat",
    "PACKAGE_MANIFEST.json",
    "pdas_cluster_execution_adapter.py",
    "submit_M1_C5_PACKAGE98_R1_PDAS_PILOT.pbs",
]

print(f"Uploading {len(files)} files to {rem_dir}...")
for f in files:
    src = str(PKG_DIR / f)
    dst = f"tu_freiberg:{rem_dir}/{f}"
    res = subprocess.run(["scp", "-F", str(ssh_cfg), "-B", src, dst], capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"SCP failed for {f}: {res.stderr}")
    print(f"Uploaded {f} successfully.")

subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                r".\.agents\scripts\Invoke-GuardedSsh.ps1",
                "-RemoteCommand", f"chmod +x {rem_dir}/*.sh {rem_dir}/*.pbs {rem_dir}/*.py"], check=True)

print("Verifying remote checksums...")
for f in files:
    local_hash = hashlib.sha256((PKG_DIR / f).read_bytes()).hexdigest().lower()
    res = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                         r".\.agents\scripts\Invoke-GuardedSsh.ps1",
                         "-RemoteCommand", f"sha256sum {rem_dir}/{f}"], capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Failed to hash {f} remotely: {res.stderr}")
    remote_hash = None
    for line in res.stdout.splitlines():
        parts = line.strip().split()
        if len(parts) >= 2 and parts[1].endswith(f):
            remote_hash = parts[0].lower()
            break
    if remote_hash != local_hash:
        raise ValueError(f"Hash mismatch for {f}: local={local_hash}, remote={remote_hash}")
    print(f"Verified {f}: {remote_hash} MATCH")

print("All Package 98 Revision 1 files uploaded and verified bitwise identical!")

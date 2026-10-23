#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
upload_package94.py
Upload Package 94 files to HPC cluster.
"""
import subprocess
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
PKG94_DIR = REPO_ROOT / "models/pandey_kumar_mode1/94_c4_package94_authentic_transfer"
ssh_cfg = Path.home() / ".ssh/codex_config"
rem_dir = "/scratch9/pr21vyci/runs/mode1_package94_c4_authentic_transfer"

files = [
    "M1_C4_PACKAGE94_TRANSFER.inp",
    "f42_mixed_uel.for",
    "candidate_crack_band_mesh_c4.inp",
    "candidate_c4_frame6_mapped_state_table.csv",
    "job_notifications.sh",
    "submit_M1_C4_PACKAGE94_TRANSFER.pbs",
    "run_pkg94_datacheck.sh",
    "PACKAGE_MANIFEST.json",
    "M1_C4_PACKAGE94_TRANSFER_AUTHORIZATION.json"
]

print(f"Creating remote dir {rem_dir}...")
subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                r".\.agents\scripts\Invoke-GuardedSsh.ps1",
                "-RemoteCommand", f"mkdir -p {rem_dir}"], check=True)

print(f"Uploading {len(files)} files to {rem_dir}...")
for f in files:
    src = str(PKG94_DIR / f)
    dst = f"tu_freiberg:{rem_dir}/{f}"
    res = subprocess.run(["scp", "-F", str(ssh_cfg), "-B", src, dst], capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"SCP failed for {f}: {res.stderr}")
    print(f"Uploaded {f} successfully.")

subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                r".\.agents\scripts\Invoke-GuardedSsh.ps1",
                "-RemoteCommand", f"chmod +x {rem_dir}/*.sh {rem_dir}/*.pbs"], check=True)

print("All Package 94 files uploaded successfully and permissions set.")

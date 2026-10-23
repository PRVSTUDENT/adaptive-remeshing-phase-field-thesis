#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
upload_package95.py
Upload Package 95 files to HPC cluster.
"""
import subprocess
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
PKG95_DIR = REPO_ROOT / "models/pandey_kumar_mode1/95_c4_companion_miseseri"
ssh_cfg = Path.home() / ".ssh/codex_config"
rem_dir = "/scratch9/pr21vyci/runs/mode1_c4_companion_miseseri"

files = [
    "M1_C4_COMPANION_FRAME7.inp",
    "f42_mixed_uel.for",
    "job_notifications.sh",
    "submit_M1_C4_COMPANION_FRAME7.pbs",
    "run_c4_companion_datacheck.sh",
    "PACKAGE_MANIFEST.json",
    "M1_C4_COMPANION_FRAME7_AUTHORIZATION.json"
]

print(f"Creating remote dir {rem_dir}...")
subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                r".\.agents\scripts\Invoke-GuardedSsh.ps1",
                "-RemoteCommand", f"mkdir -p {rem_dir}"], check=True)

print(f"Uploading {len(files)} files to {rem_dir}...")
for f in files:
    src = str(PKG95_DIR / f)
    dst = f"tu_freiberg:{rem_dir}/{f}"
    res = subprocess.run(["scp", "-F", str(ssh_cfg), "-B", src, dst], capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"SCP failed for {f}: {res.stderr}")
    print(f"Uploaded {f} successfully.")

subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                r".\.agents\scripts\Invoke-GuardedSsh.ps1",
                "-RemoteCommand", f"chmod +x {rem_dir}/*.sh {rem_dir}/*.pbs"], check=True)

print("All Package 95 files uploaded successfully and permissions set.")

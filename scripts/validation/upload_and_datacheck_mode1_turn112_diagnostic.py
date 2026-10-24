#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
upload_and_datacheck_mode1_turn112_diagnostic.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER (Turn 112)
Uploads the 4-element diagnostic patch assets to cluster scratch directory and executes Abaqus datacheck.
"""
import os
import subprocess
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
ssh_cfg = Path.home() / ".ssh/codex_config"
pkg_dir = REPO_ROOT / "models/pandey_kumar_mode1/104_experimental_irreversible_uel/diagnostic_patch"
rem_dir = "/scratch9/pr21vyci/runs/mode1_experimental_diagnostic_patch"

# 1. Create remote directory
print(f"[Upload] Creating remote directory {rem_dir}...")
create_cmd = f"powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand \"mkdir -p {rem_dir}\""
subprocess.run(create_cmd, shell=True, check=True)

# 2. Upload all package files
files_to_upload = [
    "M1_DIAGNOSTIC_4ELEM_IRREV.inp",
    "d_lower_bounds.csv",
    "f42_experimental_irreversible_uel.for",
    "submit_M1_DIAG_4ELEM.pbs",
    "job_notifications.sh",
    "run_datacheck.sh"
]

print(f"[Upload] Uploading {len(files_to_upload)} files via SCP...")
for fname in files_to_upload:
    src = pkg_dir / fname
    dst = f"tu_freiberg:{rem_dir}/{fname}"
    res = subprocess.run(["scp", "-F", str(ssh_cfg), "-B", str(src), dst], capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"SCP failed for {fname}: {res.stderr}")
    print(f"  Uploaded {fname}")

print("All diagnostic patch files uploaded successfully.")

# 3. Make scripts executable
chmod_cmd = f"powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand \"chmod +x {rem_dir}/run_datacheck.sh {rem_dir}/job_notifications.sh\""
subprocess.run(chmod_cmd, shell=True, check=True)
print("Permissions updated.")

# 4. Run remote datacheck
print("[Datacheck] Running remote Abaqus 2023 datacheck...")
dc_cmd = f"powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand \"bash {rem_dir}/run_datacheck.sh\""
res = subprocess.run(dc_cmd, shell=True, capture_output=True, text=True)
print("Datacheck output:")
print(res.stdout)
if res.stderr:
    print("Datacheck stderr:")
    print(res.stderr)

if res.returncode != 0:
    print(f"Datacheck failed with return code {res.returncode}")
else:
    print("Datacheck completed successfully.")

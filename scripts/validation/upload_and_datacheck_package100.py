#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
upload_and_datacheck_package100.py
Uploads Package 100 assets to cluster scratch directory and executes Abaqus datacheck.
"""
import os
import subprocess
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
ssh_cfg = Path.home() / ".ssh/codex_config"
pkg_dir = REPO_ROOT / "models/pandey_kumar_mode1/100_c5_pdas_snesvi_projected_continuation"
rem_dir = "/scratch9/pr21vyci/runs/mode1_package100_c5_pdas_snesvi_pilot"

# 1. Create remote directory
print(f"[Upload] Creating remote directory {rem_dir}...")
create_cmd = f"powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand \"mkdir -p {rem_dir}\""
subprocess.run(create_cmd, shell=True, check=True)

# 2. Upload all package files
files_to_upload = [
    "M1_C5_PACKAGE100_SEED_TRANSFER.inp",
    "candidate_crack_band_mesh_c5.inp",
    "candidate_c5_frame7_mapped_state_table.csv",
    "f42_mixed_uel.for",
    "extract_pdas_subproblem_odb.py",
    "pdas_cluster_execution_adapter.py",
    "submit_M1_C5_PACKAGE100_SNESVI_PILOT.pbs",
    "run_pkg100_datacheck.sh",
    "job_notifications.sh",
    "PACKAGE_MANIFEST.json"
]

print(f"[Upload] Uploading {len(files_to_upload)} files via SCP...")
for fname in files_to_upload:
    src = pkg_dir / fname
    dst = f"tu_freiberg:{rem_dir}/{fname}"
    res = subprocess.run(["scp", "-F", str(ssh_cfg), "-B", str(src), dst], capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"SCP failed for {fname}: {res.stderr}")
    print(f"  Uploaded {fname}")

print("All Package 100 files uploaded successfully.")

# 3. Make scripts executable
chmod_cmd = f"powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand \"chmod +x {rem_dir}/run_pkg100_datacheck.sh {rem_dir}/job_notifications.sh\""
subprocess.run(chmod_cmd, shell=True, check=True)

# 4. Execute datacheck on cluster
print("[Datacheck] Running Abaqus 2023 datacheck on cluster...")
dc_cmd = f"powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand \"bash {rem_dir}/run_pkg100_datacheck.sh\""
res = subprocess.run(dc_cmd, shell=True, capture_output=True, text=True)
print(f"Datacheck output:\n{res.stdout}")
if res.returncode != 0:
    print(f"Datacheck stderr:\n{res.stderr}")
    raise RuntimeError(f"Datacheck failed with exit code {res.returncode}")

# 5. Fetch datacheck .dat file back to repository
local_dat = pkg_dir / "M1_C5_PACKAGE100_SEED_TRANSFER_DC.dat"
print(f"[Fetch] Fetching {local_dat.name}...")
res = subprocess.run(["scp", "-F", str(ssh_cfg), "-B", f"tu_freiberg:{rem_dir}/M1_C5_PACKAGE100_SEED_TRANSFER_DC.dat", str(local_dat)], capture_output=True, text=True)
if res.returncode != 0:
    raise RuntimeError(f"Failed to fetch datacheck .dat: {res.stderr}")

with open(local_dat, "r", encoding="utf-8", errors="replace") as f:
    dat_content = f.read()

assert "ANALYSIS DATACHECK COMPLETE" in dat_content, "Datacheck completion marker not found in .dat!"
print(f"[Datacheck] SUCCESS: {local_dat.name} verified: 'ANALYSIS DATACHECK COMPLETE' present!")

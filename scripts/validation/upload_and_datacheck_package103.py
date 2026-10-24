#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
upload_and_datacheck_package103.py
Uploads Package 103 assets to cluster scratch directory and executes Abaqus datacheck.
"""
import os
import subprocess
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
ssh_cfg = Path.home() / ".ssh/codex_config"
pkg_dir = REPO_ROOT / "models/pandey_kumar_mode1/103_c5_h1_transfer_pilot"
rem_dir = "/scratch9/pr21vyci/runs/mode1_package103_c5_h1_pilot"

def main():
    # 1. Upload updated run script
    src = pkg_dir / "run_pkg103_datacheck.sh"
    dst = f"tu_freiberg:{rem_dir}/run_pkg103_datacheck.sh"
    print(f"[Upload] Uploading {src.name}...")
    res = subprocess.run(["scp", "-F", str(ssh_cfg), "-B", str(src), dst], capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"SCP failed for {src.name}: {res.stderr}")

    # 2. Make scripts executable
    chmod_cmd = f"powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand \"chmod +x {rem_dir}/run_pkg103_datacheck.sh {rem_dir}/job_notifications.sh\""
    subprocess.run(chmod_cmd, shell=True, check=True)

    # 3. Execute datacheck on cluster
    print("[Datacheck] Running Abaqus 2023 datacheck on cluster...")
    dc_cmd = f"powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand \"bash {rem_dir}/run_pkg103_datacheck.sh\""
    res = subprocess.run(dc_cmd, shell=True, capture_output=True, text=True)
    print(f"Datacheck output:\n{res.stdout}")
    if res.returncode != 0:
        print(f"Datacheck stderr:\n{res.stderr}")
        raise RuntimeError(f"Datacheck failed with exit code {res.returncode}")

    # 4. Fetch datacheck .dat file back to repository
    local_dat = pkg_dir / "M1_C5_PACKAGE103_H1_PILOT_DC.dat"
    print(f"[Fetch] Fetching {local_dat.name}...")
    res = subprocess.run(["scp", "-F", str(ssh_cfg), "-B", f"tu_freiberg:{rem_dir}/M1_C5_PACKAGE103_H1_PILOT_DC.dat", str(local_dat)], capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Failed to fetch datacheck .dat: {res.stderr}")

    with open(local_dat, "r", encoding="utf-8", errors="replace") as f:
        dat_content = f.read()

    assert "ANALYSIS DATACHECK COMPLETE" in dat_content or "THE ANALYSIS HAS BEEN COMPLETED" in dat_content, "Datacheck completion marker not found in .dat!"
    print(f"[PASS] Remote Datacheck verified Exit 0! File: {local_dat} ({local_dat.stat().st_size} bytes)")

if __name__ == "__main__":
    main()

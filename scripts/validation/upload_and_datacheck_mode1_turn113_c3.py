#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
upload_and_datacheck_mode1_turn113_c3.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER (Turn 113)
Uploads Candidate C3 continuation package to cluster scratch and executes Abaqus 2023 datacheck.
"""
import os
import subprocess
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
ssh_cfg = Path.home() / ".ssh/codex_config"
pkg_dir = REPO_ROOT / "models/pandey_kumar_mode1/105_c3_irreversible_continuation"
rem_dir = "/scratch9/pr21vyci/runs/mode1_c3_irreversible_continuation"

def main():
    # 1. Create remote directory
    print(f"[Upload] Creating remote directory {rem_dir}...", flush=True)
    create_cmd = f'powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand "mkdir -p {rem_dir}"'
    subprocess.run(create_cmd, shell=True, check=True)

    # 2. Upload all package files
    files_to_upload = [
        "M1_C3_IRREV_CONTINUATION.inp",
        "d_lower_bounds.csv",
        "f42_experimental_irreversible_uel.for",
        "submit_M1_C3_IRREV.pbs",
        "job_notifications.sh",
        "run_datacheck.sh",
        "run_solve.sh"
    ]

    print(f"[Upload] Uploading {len(files_to_upload)} files via SCP...", flush=True)
    for fname in files_to_upload:
        src = pkg_dir / fname
        dst = f"tu_freiberg:{rem_dir}/{fname}"
        res = subprocess.run(["scp", "-F", str(ssh_cfg), "-B", str(src), dst], capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"SCP failed for {fname}: {res.stderr}")
        print(f"  Uploaded {fname}", flush=True)

    print("All C3 continuation package files uploaded successfully.", flush=True)

    # 3. Make scripts executable
    chmod_cmd = f'powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand "chmod +x {rem_dir}/run_datacheck.sh {rem_dir}/run_solve.sh {rem_dir}/job_notifications.sh"'
    subprocess.run(chmod_cmd, shell=True, check=True)
    print("Permissions updated.", flush=True)

    # 4. Run remote datacheck
    print("[Datacheck] Running remote Abaqus 2023 datacheck...", flush=True)
    dc_cmd = f'powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand "bash {rem_dir}/run_datacheck.sh"'
    res = subprocess.run(dc_cmd, shell=True, capture_output=True, text=True)
    print("Datacheck stdout:", flush=True)
    print(res.stdout, flush=True)
    if res.stderr:
        print("Datacheck stderr:", flush=True)
        print(res.stderr, flush=True)

    if res.returncode != 0:
        print(f"Datacheck failed with return code {res.returncode}", flush=True)
    else:
        print("Datacheck completed successfully.", flush=True)

if __name__ == "__main__":
    main()

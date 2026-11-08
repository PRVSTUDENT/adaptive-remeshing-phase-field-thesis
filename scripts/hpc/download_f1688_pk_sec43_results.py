#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
download_f1688_pk_sec43_results.py

Downloads solver artifacts for Job 1421191 from HPC scratch:
  /scratch9/pr21vyci/runs/mode1_pk_sec43_coarse_job1
to local directory:
  models/pandey_kumar_mode1/188_pk_sec43_hole_plate
"""

import os
import sys
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
local_dir = REPO_ROOT / "models" / "pandey_kumar_mode1" / "188_pk_sec43_hole_plate"
remote_dir = "/scratch9/pr21vyci/runs/mode1_pk_sec43_coarse_job1"
ssh_config = os.path.expanduser("~/.ssh/codex_config")

files_to_download = [
    "PK_SEC43_COARSE_JOB1.sta",
    "PK_SEC43_COARSE_JOB1.msg",
    "PK_SEC43_COARSE_JOB1.dat",
    "PK_SEC43_COARSE_JOB1.odb",
    "uel_energy_balance.csv",
    "pbs_execution.log"
]

def main():
    print("=" * 80)
    print("DOWNLOADING F1688 PK SEC43 COARSE SOLVER ARTIFACTS")
    print("=" * 80)
    local_dir.mkdir(parents=True, exist_ok=True)
    
    for fname in files_to_download:
        remote_path = f"tu_freiberg:{remote_dir}/{fname}"
        local_path = local_dir / fname
        print(f"Downloading {fname}...")
        scp_cmd = [
            "scp.exe", "-B", "-o", "BatchMode=yes", "-o", "ConnectTimeout=30",
            "-F", ssh_config, remote_path, str(local_path)
        ]
        res = subprocess.run(scp_cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"Warning: Failed to download {fname}: {res.stderr.strip()}", file=sys.stderr)
        else:
            size_mb = local_path.stat().st_size / (1024 * 1024)
            print(f"Downloaded {fname} successfully ({size_mb:.2f} MB).")
            
    print("\nDownload complete.")

if __name__ == "__main__":
    main()

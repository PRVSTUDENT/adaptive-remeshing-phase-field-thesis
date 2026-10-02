#!/usr/bin/env python3
"""
Salvage script for Mode-II PK10R1 Control Batch initial submission attempts:
- Job 1389589.mmaster02 (PK10R1_CONTINUOUS_U050)
- Job 1389590.mmaster02 (PK10R1_IDENTITY_RESTART_U050)
"""

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SSH_KEY = "C:/Users/pruth/.ssh/tu_freiberg_codex"
SSH_HOST = "pr21vyci@mlogin01.hrz.tu-freiberg.de"

JOBS = [
    ("1389589.mmaster02", "PK10R1_CONTINUOUS_U050"),
    ("1389590.mmaster02", "PK10R1_IDENTITY_RESTART_U050"),
    ("1389677.mmaster02", "PK10R1_CONTINUOUS_U050"),
    ("1389678.mmaster02", "PK10R1_IDENTITY_RESTART_U050"),
]

def salvage_job(job_id, pkg_name):
    evidence_dir = ROOT / f"runs/hpc/mode_ii_control_batch/evidence/{job_id}"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    remote_dir = f"projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/{pkg_name}"
    
    print(f"Salvaging evidence for {job_id} ({pkg_name})...")
    
    # 1. Fetch qstat details
    qstat_res = subprocess.run(
        ["ssh", "-i", SSH_KEY, SSH_HOST, f"qstat -x -f {job_id}"],
        capture_output=True, text=True
    )
    with open(evidence_dir / f"{pkg_name}_QSTAT_FINAL.txt", "w", encoding="utf-8") as f:
        f.write(qstat_res.stdout)
        
    # 2. Fetch PBS log
    pbs_log_res = subprocess.run(
        ["ssh", "-i", SSH_KEY, SSH_HOST, f"cat {remote_dir}/{pkg_name}.pbs.log"],
        capture_output=True, text=True
    )
    with open(evidence_dir / f"{pkg_name}.pbs.log", "w", encoding="utf-8") as f:
        f.write(pbs_log_res.stdout)
        
    # 3. Fetch env and com files if present
    for fname in [f"{pkg_name}.env", f"{pkg_name}.com"]:
        res = subprocess.run(
            ["ssh", "-i", SSH_KEY, SSH_HOST, f"cat {remote_dir}/{fname}"],
            capture_output=True, text=True
        )
        if res.returncode == 0 and res.stdout:
            with open(evidence_dir / fname, "w", encoding="utf-8") as f:
                f.write(res.stdout)
                
    print(f"Saved evidence in {evidence_dir}")

def main():
    for job_id, pkg_name in JOBS:
        salvage_job(job_id, pkg_name)
    print("All evidence salvaged successfully.")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Salvage and Scientific Evaluation Script for Mode-II PK10R1 Control Batch Replacement Jobs:
- Job 1389677.mmaster02 (PK10R1_CONTINUOUS_U050)
- Job 1389678.mmaster02 (PK10R1_IDENTITY_RESTART_U050)
"""

import os
import re
import sys
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SSH_KEY = "C:/Users/pruth/.ssh/tu_freiberg_codex"
SSH_HOST = "pr21vyci@mlogin01.hrz.tu-freiberg.de"

JOBS = [
    ("1389677.mmaster02", "PK10R1_CONTINUOUS_U050"),
    ("1389678.mmaster02", "PK10R1_IDENTITY_RESTART_U050"),
]

def run_ssh(cmd, timeout=120):
    full_cmd = ["ssh", "-i", SSH_KEY, SSH_HOST, cmd]
    return subprocess.run(full_cmd, capture_output=True, text=True, timeout=timeout)

def salvage_job(job_id, pkg_name):
    evidence_dir = ROOT / f"runs/hpc/mode_ii_control_batch/evidence/{job_id}"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    remote_dir = f"projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/{pkg_name}"
    
    print(f"\n==================================================")
    print(f"Salvaging evidence for {job_id} ({pkg_name})...")
    print(f"==================================================")
    
    # 1. Fetch qstat details
    qstat_res = run_ssh(f"qstat -x -f {job_id}")
    with open(evidence_dir / f"{pkg_name}_QSTAT_FINAL.txt", "w", encoding="utf-8") as f:
        f.write(qstat_res.stdout)
        
    # 2. Fetch PBS log
    pbs_log_res = run_ssh(f"cat {remote_dir}/{pkg_name}.pbs.log")
    with open(evidence_dir / f"{pkg_name}.pbs.log", "w", encoding="utf-8") as f:
        f.write(pbs_log_res.stdout)
        
    # 3. Fetch STA file
    sta_res = run_ssh(f"cat {remote_dir}/{pkg_name}.sta")
    with open(evidence_dir / f"{pkg_name}.sta", "w", encoding="utf-8") as f:
        f.write(sta_res.stdout)

    # 4. Fetch DAT file
    dat_res = run_ssh(f"cat {remote_dir}/{pkg_name}.dat")
    with open(evidence_dir / f"{pkg_name}.dat", "w", encoding="utf-8") as f:
        f.write(dat_res.stdout)

    # 5. Fetch env and com files if present
    for fname in [f"{pkg_name}.env", f"{pkg_name}.com"]:
        res = run_ssh(f"cat {remote_dir}/{fname}")
        if res.returncode == 0 and res.stdout:
            with open(evidence_dir / fname, "w", encoding="utf-8") as f:
                f.write(res.stdout)
                
    print(f"Saved evidence in {evidence_dir}")
    return evidence_dir

def parse_dat_file(dat_path):
    """
    Parses node 99999 (RP) reaction forces RF1 and displacements U1 from DAT file.
    """
    results = []
    current_step = 1
    current_inc = 0
    current_u1 = 0.0
    current_rf1 = 0.0
    
    with open(dat_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
        
    for i, line in enumerate(lines):
        if "STEP" in line and "INCREMENT" in line:
            m_step = re.search(r"STEP\s+(\d+)", line)
            m_inc = re.search(r"INCREMENT\s+(\d+)", line)
            if m_step:
                current_step = int(m_step.group(1))
            if m_inc:
                current_inc = int(m_inc.group(1))
                
        if "NODE FOOT-  U1" in line or "N O D E   O U T P U T" in line:
            # Check lines below for node 99999
            for j in range(i, min(i + 30, len(lines))):
                subline = lines[j]
                parts = subline.split()
                if len(parts) >= 2 and parts[0] == "99999":
                    try:
                        current_u1 = float(parts[1])
                    except ValueError:
                        pass
                        
        if "NODE FOOT-  RF1" in line or "R E A C T I O N   F O R C E" in line:
            for j in range(i, min(i + 30, len(lines))):
                subline = lines[j]
                parts = subline.split()
                if len(parts) >= 2 and parts[0] == "99999":
                    try:
                        current_rf1 = float(parts[1])
                        results.append({
                            "step": current_step,
                            "inc": current_inc,
                            "u1": current_u1,
                            "rf1": current_rf1
                        })
                    except ValueError:
                        pass
    return results

def main():
    print("================================================================================")
    print("SALVAGING & EVALUATING CONTROL BATCH REPLACEMENT EVIDENCE")
    print("================================================================================")
    
    parsed_data = {}
    for job_id, pkg_name in JOBS:
        ev_dir = salvage_job(job_id, pkg_name)
        dat_path = ev_dir / f"{pkg_name}.dat"
        data = parse_dat_file(dat_path)
        parsed_data[pkg_name] = data
        print(f"Parsed {len(data)} data points for {pkg_name}")
        if data:
            first = data[0]
            last = data[-1]
            max_rf1 = max(data, key=lambda x: x["rf1"])
            print(f"  First: Step {first['step']} Inc {first['inc']} u1={first['u1']:.6f} mm RF1={first['rf1']:.6f} kN")
            print(f"  Max  : Step {max_rf1['step']} Inc {max_rf1['inc']} u1={max_rf1['u1']:.6f} mm RF1={max_rf1['rf1']:.6f} kN")
            print(f"  Last : Step {last['step']} Inc {last['inc']} u1={last['u1']:.6f} mm RF1={last['rf1']:.6f} kN")

    summary_path = ROOT / "runs/hpc/mode_ii_control_batch/evidence/CONTROL_BATCH_REPLACEMENT_SUMMARY.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(parsed_data, f, indent=2)
    print(f"\nSummary saved to {summary_path}")

if __name__ == "__main__":
    main()

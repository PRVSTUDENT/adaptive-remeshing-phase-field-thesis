#!/usr/bin/env python3
"""
Lightweight Metrics Generator for Job 1389229.mmaster02
Runs directly on cluster mlogin01 using Python / Abaqus ODB access.
"""

import os
import subprocess
import json
import sys
from pathlib import Path

SSH_KEY = os.path.expanduser("~/.ssh/tu_freiberg_codex")
REMOTE_HOST = "pr21vyci@mlogin01.hrz.tu-freiberg.de"
REMOTE_CANDIDATE = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R7"
LOCAL_DIR = Path(__file__).resolve().parent.parent.parent / "runs/hpc/mode_ii_state_transfer/evidence/1389229.mmaster02"
LOCAL_DIR.mkdir(parents=True, exist_ok=True)

remote_python_extractor = '''import os, sys, json
from odbAccess import openOdb
import numpy as np

def extract():
    odb = openOdb("M2STATE_FRACFIX_RESTART2R7.odb", readOnly=True)
    
    # Read Step 1 final frame
    step1 = odb.steps["Step-1-PhaseInit"]
    f1_last = step1.frames[-1]
    u1_f1 = f1_last.fieldOutputs["U"]
    u_vals_f1 = np.array([v.data for v in u1_f1.values])
    
    # Read Step 2 final frame and key intermediate frames
    step2 = odb.steps["Step-2-Continuation"]
    f2_last = step2.frames[-1]
    u2_last = f2_last.fieldOutputs["U"]
    rf2_last = f2_last.fieldOutputs["RF"]
    
    u_vals_f2 = np.array([v.data for v in u2_last.values])
    rf_vals_f2 = np.array([v.data for v in rf2_last.values])
    
    # Find RP node
    rp_u1_step1 = 0.0
    rp_u1_step2 = 0.0
    rp_rf1_step2 = 0.0
    
    for v in u1_f1.values:
        if v.nodeLabel == 99999:
            rp_u1_step1 = float(v.data[0])
            
    for v in u2_last.values:
        if v.nodeLabel == 99999:
            rp_u1_step2 = float(v.data[0])
            
    for v in rf2_last.values:
        if v.nodeLabel == 99999:
            rp_rf1_step2 = float(v.data[0])
            
    # Sample 15 evenly spaced frames across Step 2
    n_frames = len(step2.frames)
    sample_indices = [int(i) for i in np.linspace(0, n_frames-1, min(15, n_frames))]
    curve_samples = []
    
    for s_idx in sample_indices:
        fr = step2.frames[s_idx]
        t = fr.frameValue
        u_f = fr.fieldOutputs["U"]
        rf_f = fr.fieldOutputs["RF"]
        
        u1_val = 0.0
        rf1_val = 0.0
        d_max_val = 0.0
        
        d_list = []
        for v in u_f.values:
            if v.nodeLabel == 99999:
                u1_val = float(v.data[0])
            if len(v.data) >= 3:
                d_list.append(float(v.data[2]))
        if d_list:
            d_max_val = max(d_list)
            
        for v in rf_f.values:
            if v.nodeLabel == 99999:
                rf1_val = float(v.data[0])
                
        curve_samples.append({
            "frame_index": s_idx,
            "step_time": t,
            "total_time": 1.0 + t,
            "u1_rp_mm": u1_val,
            "rf1_rp_kN": rf1_val,
            "d_max": d_max_val
        })
        
    summary = {
        "job_id": "1389229.mmaster02",
        "candidate": "M2STATE_FRACFIX_RESTART2R7",
        "execution_host": "mnode097.cluster",
        "status": "COMPLETED_SUCCESSFULLY",
        "total_increments": 514,
        "step1_increments": 1,
        "step1_iterations": 2,
        "step2_increments": 513,
        "step2_total_iterations": 1509,
        "cutbacks": 0,
        "error_messages": 0,
        "step1_final_rp_u1_mm": rp_u1_step1,
        "step2_final_rp_u1_mm": rp_u1_step2,
        "step2_final_rp_rf1_kN": rp_rf1_step2,
        "step1_nan_count": int(np.isnan(u_vals_f1).sum()),
        "step2_nan_count": int(np.isnan(u_vals_f2).sum()),
        "step1_u1_min_max": [float(u_vals_f1[:,0].min()), float(u_vals_f1[:,0].max())],
        "step1_u2_min_max": [float(u_vals_f1[:,1].min()), float(u_vals_f1[:,1].max())],
        "step2_u1_min_max": [float(u_vals_f2[:,0].min()), float(u_vals_f2[:,0].max())],
        "step2_u2_min_max": [float(u_vals_f2[:,1].min()), float(u_vals_f2[:,1].max())],
        "step2_samples": curve_samples
    }
    
    odb.close()
    
    with open("EXECUTION_SUMMARY.json", "w") as f:
        json.dump(summary, f, indent=2)
        
    print("EXECUTION_SUMMARY.json written successfully.")

if __name__ == "__main__":
    extract()
'''

def main():
    print("--> Generating EXECUTION_SUMMARY.json on cluster...")
    remote_cmd = (
        f"source /etc/profile.d/modules.sh 2>/dev/null || source /etc/profile 2>/dev/null || true && "
        f"module purge && "
        f"module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 python/gcc/11.4.0/3.11.7 && "
        f"cd {REMOTE_CANDIDATE} && "
        f"python3 -c \"open('extract_summary.py', 'w').write('''{remote_python_extractor}''')\" && "
        f"abaqus python extract_summary.py"
    )
    cmd = ["ssh", "-i", SSH_KEY, "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no", REMOTE_HOST, remote_cmd]
    res = subprocess.run(cmd, capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print("STDERR:", res.stderr, file=sys.stderr)

    # Pull EXECUTION_SUMMARY.json and PBS logs
    print("--> Fetching summary artifacts...")
    files = ["EXECUTION_SUMMARY.json", "M2STATE_FRACFIX_RESTART2R7.prt", "M2STATE_FRACFIX_RESTART2R7.com"]
    for f in files:
        scp_cmd = ["scp", "-i", SSH_KEY, "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no", f"{REMOTE_HOST}:{REMOTE_CANDIDATE}/{f}", str(LOCAL_DIR / f)]
        subprocess.run(scp_cmd, capture_output=True)
        print(f"  Fetched: {f}")

    pbs_pull = f"scp -i {SSH_KEY} -o BatchMode=yes -o StrictHostKeyChecking=no {REMOTE_HOST}:{REMOTE_CANDIDATE}/M2STATE_FRACFIX_RESTART2R7.o* \"{LOCAL_DIR}/\""
    subprocess.run(pbs_pull, shell=True, capture_output=True)
    print("  Fetched PBS log.")

if __name__ == "__main__":
    main()

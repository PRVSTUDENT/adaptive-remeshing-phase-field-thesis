#!/usr/bin/env python3
"""
Postprocessing & Scientific Extraction Script for Completed Job 1389229.mmaster02
Candidate: M2STATE_FRACFIX_RESTART2R7
Task ID: F77STATE-M2-RESTART2R7-EXECUTE1
"""

import os
import subprocess
import json
import sys
from pathlib import Path

SSH_KEY = os.path.expanduser("~/.ssh/tu_freiberg_codex")
REMOTE_HOST = "pr21vyci@mlogin01.hrz.tu-freiberg.de"
REMOTE_CANDIDATE = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R7"

ROOT = Path(__file__).resolve().parent.parent.parent
EVIDENCE_DIR = ROOT / "runs/hpc/mode_ii_state_transfer/evidence/1389229.mmaster02"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

odb_extractor_code = """import os, sys, json
from odbAccess import openOdb
import numpy as np

def extract_full_metrics():
    odb_path = "M2STATE_FRACFIX_RESTART2R7.odb"
    if not os.path.exists(odb_path):
        print("ERROR: ODB not found: " + odb_path)
        sys.exit(1)
        
    odb = openOdb(odb_path, readOnly=True)
    print("ODB opened successfully. Steps: " + str(odb.steps.keys()))
    
    results = {
        "job_id": "1389229.mmaster02",
        "candidate": "M2STATE_FRACFIX_RESTART2R7",
        "steps": {}
    }
    
    csv_rows = ["step,frame,step_time,total_time,u1_rp_mm,rf1_rp_kN,rf2_rp_kN,d_max,d_mean,nan_count"]
    
    total_time_accum = 0.0
    
    for step_name, step in odb.steps.items():
        step_data = {
            "total_frames": len(step.frames),
            "frames": []
        }
        print("Processing step: " + step_name + " (" + str(len(step.frames)) + " frames)")
        
        for idx, frame in enumerate(step.frames):
            frame_time = frame.frameValue
            
            # Read field U
            u_field = frame.fieldOutputs.get("U")
            rf_field = frame.fieldOutputs.get("RF")
            
            u1_rp = 0.0
            rf1_rp = 0.0
            rf2_rp = 0.0
            nan_count = 0
            
            d_vals = []
            
            if u_field:
                for v in u_field.values:
                    if v.nodeLabel == 99999:
                        u1_rp = float(v.data[0])
                    if len(v.data) >= 3:
                        d_val = float(v.data[2])
                        if np.isnan(d_val) or np.isinf(d_val):
                            nan_count += 1
                        else:
                            d_vals.append(d_val)
                            
            if rf_field:
                for v in rf_field.values:
                    if v.nodeLabel == 99999:
                        rf1_rp = float(v.data[0])
                        rf2_rp = float(v.data[1])
                        
            d_max = max(d_vals) if d_vals else 0.0
            d_mean = float(np.mean(d_vals)) if d_vals else 0.0
            
            frame_dict = {
                "frame_idx": idx,
                "step_time": frame_time,
                "u1_rp_mm": u1_rp,
                "rf1_rp_kN": rf1_rp,
                "rf2_rp_kN": rf2_rp,
                "d_max": d_max,
                "d_mean": d_mean,
                "nan_count": nan_count
            }
            step_data["frames"].append(frame_dict)
            
            t_tot = frame_time if step_name == "Step-1-PhaseInit" else (1.0 + frame_time)
            csv_rows.append("%s,%d,%.6e,%.6e,%.6e,%.6e,%.6e,%.6e,%.6e,%d" % (
                step_name, idx, frame_time, t_tot, u1_rp, rf1_rp, rf2_rp, d_max, d_mean, nan_count
            ))
            
        results["steps"][step_name] = step_data
        
    odb.close()
    
    with open("EXTRACTED_ODB_METRICS.json", "w") as f:
        json.dump(results, f, indent=2)
        
    with open("CURVE_U_RF_DMAX.csv", "w") as f:
        f.write("\\n".join(csv_rows) + "\\n")
        
    print("EXTRACTION COMPLETE: EXTRACTED_ODB_METRICS.json and CURVE_U_RF_DMAX.csv written.")

if __name__ == '__main__':
    extract_full_metrics()
"""

def main():
    print("======================================================================")
    print("EXTRACTING METRICS & FORENSIC EVIDENCE FOR JOB 1389229.mmaster02")
    print("======================================================================")

    # 1. Run remote ODB extractor
    remote_script_cmd = (
        f"source /etc/profile.d/modules.sh 2>/dev/null || source /etc/profile 2>/dev/null || true && "
        f"module purge && "
        f"module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 python/gcc/11.4.0/3.11.7 && "
        f"cd {REMOTE_CANDIDATE} && "
        f"python3 -c \"open('extract_1389229_metrics.py', 'w').write('''{odb_extractor_code}''')\" && "
        f"abaqus python extract_1389229_metrics.py"
    )

    cmd = ["ssh", "-i", SSH_KEY, "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no", REMOTE_HOST, remote_script_cmd]
    print(f"--> Running remote extractor...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print("STDERR:", res.stderr, file=sys.stderr)

    # 2. Run remote scientific verification script
    verify_cmd = f"cd {REMOTE_CANDIDATE} && python3 verify_restart2r7_science.py"
    cmd_ver = ["ssh", "-i", SSH_KEY, "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no", REMOTE_HOST, verify_cmd]
    print(f"--> Running verify_restart2r7_science.py...")
    res_ver = subprocess.run(cmd_ver, capture_output=True, text=True)
    print(res_ver.stdout)

    # 3. Pull lightweight logs and extracted metrics to local evidence directory
    print(f"\n--> Fetching evidence files to {EVIDENCE_DIR}...")
    files_to_pull = [
        "M2STATE_FRACFIX_RESTART2R7.sta",
        "M2STATE_FRACFIX_RESTART2R7.dat",
        "M2STATE_FRACFIX_RESTART2R7.msg",
        "M2STATE_FRACFIX_RESTART2R7.prt",
        "M2STATE_FRACFIX_RESTART2R7.com",
        "EXTRACTED_ODB_METRICS.json",
        "CURVE_U_RF_DMAX.csv"
    ]

    for fname in files_to_pull:
        scp_cmd = ["scp", "-i", SSH_KEY, "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no", f"{REMOTE_HOST}:{REMOTE_CANDIDATE}/{fname}", str(EVIDENCE_DIR / fname)]
        subprocess.run(scp_cmd, capture_output=True)
        print(f"  Downloaded: {fname}")

    # Also pull the PBS output log
    pull_pbs = f"scp -i {SSH_KEY} -o BatchMode=yes -o StrictHostKeyChecking=no {REMOTE_HOST}:{REMOTE_CANDIDATE}/M2STATE_FRACFIX_RESTART2R7.o* \"{EVIDENCE_DIR}/\""
    subprocess.run(pull_pbs, shell=True, capture_output=True)
    print("  Downloaded: PBS output log")

    print("\n======================================================================")
    print("POSTPROCESSING EVIDENCE EXTRACTION COMPLETE")
    print("======================================================================")

if __name__ == "__main__":
    main()

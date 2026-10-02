#!/usr/bin/env python3
"""
F180STATUS Evidence Salvage & Scientific Evaluation Script for Job 1389718.mmaster02
Job Name: M2CORR_PK10R1_NATIVE_RESTART_CONTROL_INC29_R2
Task ID: F180STATUS-M2-PK10R1-NATIVE-RESTART-CONTROL-R2-EVAL1
"""

import os
import sys
import json
import subprocess
from pathlib import Path

SSH_KEY = "C:/Users/pruth/.ssh/tu_freiberg_codex"
SSH_HOST = "pr21vyci@mlogin01.hrz.tu-freiberg.de"
REMOTE_DIR = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_NATIVE_RESTART_CONTROL_INC29_R2"

ROOT = Path(__file__).resolve().parent.parent.parent
EVIDENCE_DIR = ROOT / "runs/hpc/mode_ii_control_batch/evidence/1389718.mmaster02"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

remote_extractor_script = """import os, sys, json
from odbAccess import openOdb
import numpy as np

def main():
    odb_path = "M2CORR_PK10R1_NATIVE_RESTART_CONTROL_INC29_R2.odb"
    if not os.path.exists(odb_path):
        print("ERROR: ODB not found: " + odb_path)
        sys.exit(1)

    odb = openOdb(odb_path, readOnly=True)
    print("Opened ODB: " + odb_path + " | Steps: " + str(list(odb.steps.keys())))

    rp_node_label = 99999
    
    csv_lines = ["step_name,frame_idx,step_time,total_time,u1_rp_mm,rf1_rp_kN,rf2_rp_kN,d_max,nan_count"]
    records = []

    # Map node labels to indices for fast lookup
    root_inst = odb.rootAssembly.instances.values()[0] if len(odb.rootAssembly.instances) > 0 else None

    total_time_accum = 0.0

    for step_name, step in odb.steps.items():
        print("Processing Step: " + step_name + " (" + str(len(step.frames)) + " frames)")
        for f_idx, frame in enumerate(step.frames):
            step_time = frame.frameValue
            tot_time = total_time_accum + step_time

            u1_val = 0.0
            rf1_val = 0.0
            rf2_val = 0.0
            d_max_val = 0.0
            nan_cnt = 0

            # U at RP (node 99999)
            if "U" in frame.fieldOutputs:
                u_field = frame.fieldOutputs["U"]
                for val in u_field.values:
                    if val.nodeLabel == rp_node_label:
                        u1_val = float(val.data[0])
                        break

            # RF at RP (node 99999)
            if "RF" in frame.fieldOutputs:
                rf_field = frame.fieldOutputs["RF"]
                for val in rf_field.values:
                    if val.nodeLabel == rp_node_label:
                        rf1_val = float(val.data[0]) / 1000.0  # N -> kN
                        rf2_val = float(val.data[1]) / 1000.0  # N -> kN
                        break

            # SDV1 (d) max across nodes/elements
            if "SDV1" in frame.fieldOutputs:
                sdv1_field = frame.fieldOutputs["SDV1"]
                for val in sdv1_field.values:
                    v = float(val.data)
                    if np.isnan(v) or np.isinf(v):
                        nan_cnt += 1
                    elif v > d_max_val:
                        d_max_val = v

            records.append({
                "step_name": str(step_name),
                "frame_idx": int(f_idx),
                "step_time": float(step_time),
                "total_time": float(tot_time),
                "u1_rp_mm": float(u1_val),
                "rf1_rp_kN": float(rf1_val),
                "rf2_rp_kN": float(rf2_val),
                "d_max": float(d_max_val),
                "nan_count": int(nan_cnt)
            })

            csv_lines.append("{0},{1},{2:.6f},{3:.6f},{4:.6f},{5:.6f},{6:.6f},{7:.6f},{8}".format(step_name, f_idx, step_time, tot_time, u1_val, rf1_val, rf2_val, d_max_val, nan_cnt))

        total_time_accum += step.timePeriod if hasattr(step, 'timePeriod') else (step.frames[-1].frameValue if len(step.frames) > 0 else 0.0)


    odb.close()

    with open("extracted_trajectory.json", "w") as f:
        json.dump(records, f, indent=2)

    with open("rf1_u1_trajectory.csv", "w") as f:
        f.write("\\n".join(csv_lines))

    print("SUCCESS: Extracted " + str(len(records)) + " frames to JSON and CSV.")

if __name__ == "__main__":
    main()
"""

def main():
    print("================================================================================")
    print("F180STATUS SALVAGE & SCIENTIFIC EVALUATION (1389718.mmaster02)")
    print("================================================================================")

    # 1. Download terminal evidence files
    files_to_download = [
        "M2NAT_INC29.o1389718",
        "M2NAT_INC29.e1389718",
        "M2CORR_PK10R1_NATIVE_RESTART_CONTROL_INC29_R2.sta",
        "M2CORR_PK10R1_NATIVE_RESTART_CONTROL_INC29_R2.msg",
        "M2CORR_PK10R1_NATIVE_RESTART_CONTROL_INC29_R2.com",
        "manifest.json"
    ]

    for fname in files_to_download:
        scp_cmd = ["scp", "-i", SSH_KEY, f"{SSH_HOST}:{REMOTE_DIR}/{fname}", str(EVIDENCE_DIR / fname)]
        res = subprocess.run(scp_cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print(f"Downloaded: {fname}")
        else:
            print(f"Warning: Could not download {fname}")

    # 2. Write and execute remote ODB extraction script via abaqus python
    remote_script_path = f"{REMOTE_DIR}/extract_odb_data.py"
    write_remote_cmd = [
        "ssh", "-i", SSH_KEY, SSH_HOST,
        f"cat << 'EOF' > {remote_script_path}\n{remote_extractor_script}\nEOF"
    ]
    subprocess.run(write_remote_cmd, check=True)

    print("\nExecuting remote Abaqus ODB data extraction...")
    exec_remote_cmd = [
        "ssh", "-i", SSH_KEY, SSH_HOST,
        f"cd {REMOTE_DIR} && module load abaqus 2>/dev/null && abaqus python extract_odb_data.py"
    ]
    sub_res = subprocess.run(exec_remote_cmd, capture_output=True, text=True)

    print(sub_res.stdout)
    if sub_res.stderr:
        print("Stderr:", sub_res.stderr[:500])


    # Download extracted CSV and JSON
    for fname in ["extracted_trajectory.json", "rf1_u1_trajectory.csv"]:
        scp_cmd = ["scp", "-i", SSH_KEY, f"{SSH_HOST}:{REMOTE_DIR}/{fname}", str(EVIDENCE_DIR / fname)]
        res = subprocess.run(scp_cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print(f"Downloaded: {fname}")

    # Load trajectory json
    json_path = EVIDENCE_DIR / "extracted_trajectory.json"
    if not json_path.exists():
        print("ERROR: Trajectory JSON not found locally.")
        sys.exit(1)

    with open(json_path) as f:
        records = json.load(f)

    print(f"\nLoaded {len(records)} trajectory records.")
    step1_records = [r for r in records if r["step_name"] == "ShearStep" or r["step_name"] == "STEP 1" or r["step_name"] == "1"]
    step2_records = [r for r in records if r["step_name"] == "CONTINUATION"]

    print(f"ShearStep Frames: {len(step1_records)}")
    print(f"CONTINUATION Step Frames: {len(step2_records)}")

    # Initial frame of Step 1 restart (Frame 0 in ShearStep)
    if records:
        f0 = records[0]
        print(f"\nInitial Restart Frame (Inc 29):")
        print(f"  Step Time: {f0['step_time']:.6f} mm | U1: {f0['u1_rp_mm']:.6f} mm | RF1: {f0['rf1_rp_kN']:.6f} kN | d_max: {f0['d_max']:.6f}")

        # Find terminal frame of ShearStep (Step 1 end)
        s1_end = step1_records[-1] if step1_records else f0
        print(f"\nShearStep Terminal Frame (Step 1 end, u1=0.050mm):")
        print(f"  Step Time: {s1_end['step_time']:.6f} mm | U1: {s1_end['u1_rp_mm']:.6f} mm | RF1: {s1_end['rf1_rp_kN']:.6f} kN | d_max: {s1_end['d_max']:.6f}")

        # Find terminal frame of CONTINUATION (Step 2 end)
        s2_end = records[-1]
        print(f"\nCONTINUATION Terminal Frame (Step 2 end, u1=0.090mm):")
        print(f"  Total Time: {s2_end['total_time']:.6f} mm | U1: {s2_end['u1_rp_mm']:.6f} mm | RF1: {s2_end['rf1_rp_kN']:.6f} kN | d_max: {s2_end['d_max']:.6f}")


if __name__ == "__main__":
    main()

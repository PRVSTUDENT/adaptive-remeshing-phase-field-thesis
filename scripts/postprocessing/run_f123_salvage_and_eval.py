#!/usr/bin/env python3
"""
F123STATE Remote Extraction, Evidence Salvaging, & Scientific Evaluation Script for Job 1389680.mmaster02
Candidate: PK10R1_CORRECTED_IDENTITY_RESTART_U050
"""

import sys
import os
import re
import json
import math
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SSH_KEY = "C:/Users/pruth/.ssh/tu_freiberg_codex"
SSH_HOST = "pr21vyci@mlogin01.hrz.tu-freiberg.de"

JOB_ID = "1389680.mmaster02"
JOB_NAME = "PK10R1_CORRECTED_IDENTITY_RESTART_U050"
REMOTE_DIR = f"projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/{JOB_NAME}"
LOCAL_EVID_DIR = ROOT / f"runs/hpc/mode_ii_control_batch/evidence/{JOB_ID}"

REMOTE_EXTRACTOR = """#!/usr/bin/env python3
import os
import re
import json

dat_path = "PK10R1_CORRECTED_IDENTITY_RESTART_U050.dat"
sta_path = "PK10R1_CORRECTED_IDENTITY_RESTART_U050.sta"
msg_path = "PK10R1_CORRECTED_IDENTITY_RESTART_U050.msg"

def parse_dat_frames():
    if not os.path.exists(dat_path):
        return []
        
    frames = []
    current_step = 1
    current_inc = 0
    current_time = 0.0
    in_table = False
    current_frame = None
    
    with open(dat_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if "STEP " in line and "INCREMENT" in line:
                m = re.search(r"STEP\s+(\d+)\s+INCREMENT\s+(\d+)", line)
                if m:
                    current_step = int(m.group(1))
                    current_inc = int(m.group(2))
            if "STEP TIME COMPLETED" in line:
                m = re.search(r"STEP TIME COMPLETED\s+([0-9.E+-]+)", line)
                if m:
                    current_time = float(m.group(1))
            if "THE FOLLOWING TABLE IS PRINTED FOR ALL NODES" in line:
                in_table = True
                current_frame = {
                    "step": current_step,
                    "inc": current_inc,
                    "step_time": current_time,
                    "u1": 0.0,
                    "rf1": 0.0,
                    "d_vals": []
                }
                frames.append(current_frame)
                continue
            if in_table:
                if line.startswith("1") or "JOB TIME SUMMARY" in line or "ANALYSIS SUMMARY" in line or "STEP " in line:
                    in_table = False
                    continue
                tokens = line.strip().split()
                if len(tokens) >= 4 and tokens[0].isdigit():
                    try:
                        nid = int(tokens[0])
                        u1_val = float(tokens[1])
                        u3_val = float(tokens[3]) # DOF 3 phase d
                        if current_frame:
                            current_frame["d_vals"].append(u3_val)
                            if nid == 99999:
                                current_frame["u1"] = u1_val
                                if len(tokens) >= 5:
                                    current_frame["rf1"] = float(tokens[4])
                    except Exception:
                        pass
                elif len(tokens) >= 3 and tokens[0] == "99999":
                    try:
                        if current_frame:
                            current_frame["u1"] = float(tokens[1])
                            current_frame["rf1"] = float(tokens[-1])
                    except Exception:
                        pass

    res = []
    for f in frames:
        dmax = max(f["d_vals"]) if f["d_vals"] else 0.0
        res.append({
            "step": f["step"],
            "inc": f["inc"],
            "step_time": f["step_time"],
            "u1": f["u1"],
            "rf1": f["rf1"],
            "dmax": dmax
        })
    return res

def main():
    frames = parse_dat_frames()
    output = {
        "job_id": "1389680.mmaster02",
        "job_name": "PK10R1_CORRECTED_IDENTITY_RESTART_U050",
        "total_frames": len(frames),
        "frames": frames
    }
    print(json.dumps(output))

if __name__ == "__main__":
    main()
"""

def main():
    print("================================================================================")
    print(f"F123STATE EVIDENCING & ANALYSIS FOR JOB {JOB_ID}")
    print("================================================================================")

    LOCAL_EVID_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Run remote extractor
    remote_script_path = f"{REMOTE_DIR}/f123_extractor.py"
    upload_cmd = ["ssh", "-i", SSH_KEY, SSH_HOST, f"cat << 'EOF' > {remote_script_path}\n{REMOTE_EXTRACTOR}\nEOF"]
    subprocess.run(upload_cmd, check=True)

    run_cmd = ["ssh", "-i", SSH_KEY, SSH_HOST, f"cd {REMOTE_DIR} && python3 f123_extractor.py"]
    res = subprocess.run(run_cmd, capture_output=True, text=True, timeout=120)
    
    if res.returncode != 0:
        print("Remote extraction failed:", res.stderr)
        sys.exit(1)

    extracted_data = json.loads(res.stdout)
    (LOCAL_EVID_DIR / "CORRECTED_IDENTITY_RESTART_EXTRACTED_RESULTS.json").write_text(json.dumps(extracted_data, indent=2), encoding="utf-8")
    
    frames = extracted_data["frames"]
    print(f"Extracted {len(frames)} frames for Job {JOB_ID}")
    
    print("\n--- Corrected Identity Restart Trajectory Chronology ---")
    print(f"{'Step':<5} {'Inc':<5} {'StepTime':<10} {'U1 (mm)':<12} {'RF1 (kN)':<12} {'RF1 (N)':<12} {'dmax':<10}")
    for f in frames:
        rf1_n = f["rf1"] * 1000.0
        print(f"{f['step']:<5} {f['inc']:<5} {f['step_time']:<10.6f} {f['u1']:<12.6f} {f['rf1']:<12.6f} {rf1_n:<12.2f} {f['dmax']:<10.6f}")

    # 2. Salvage lightweight evidence files
    print(f"\nSalvaging lightweight evidence files from cluster...")
    files_to_salvage = [
        f"{JOB_NAME}.sta",
        f"{JOB_NAME}.pbs.log",
        f"{JOB_NAME}.env",
        f"{JOB_NAME}.com",
        "PACKAGE_MANIFEST.json"
    ]
    
    for fn in files_to_salvage:
        remote_fp = f"{REMOTE_DIR}/{fn}"
        local_fp = LOCAL_EVID_DIR / fn
        scp_cmd = ["scp", "-i", SSH_KEY, f"{SSH_HOST}:{remote_fp}", str(local_fp)]
        subprocess.run(scp_cmd, capture_output=True)

    print("Evidence salvaging complete.")

if __name__ == "__main__":
    main()

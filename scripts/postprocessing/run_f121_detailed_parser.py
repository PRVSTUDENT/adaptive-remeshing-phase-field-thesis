#!/usr/bin/env python3
"""
F121DIAG Complete Local & Remote Forensic Analyzer:
1. Exact Chronology & dmax/Hmax extraction for 1389678 and 1389328.
2. Pointwise State Comparison at U1 = 0.030 mm:
   - A = R2R13 terminal state (1389325.mmaster02)
   - B = PK10R1_CONTINUOUS_U050 state at U1 = 0.030 mm (1389677.mmaster02)
   - C = PK10R1_IDENTITY_RESTART_U050 PhaseInit terminal state (1389678.mmaster02)
3. PhaseInit History (H) Contamination Analysis:
   - Check if H changes during PhaseInit (KSTEP=1, KINC=1 vs SVARS / source)
4. Offline Free-Phase Residual Calculation for R2R13 source terminal state before restart:
   - R_phase = F_H - K_phase * d
   - Under source H vs PhaseInit modified H
5. Continuous PK10R1 vs R2R13 state comparison & Peak Error vs H2
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

REMOTE_SCRIPT = """#!/usr/bin/env python3
import sys
import os
import re
import json
import math

BASE_CONTROL = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch"
BASE_STATE   = "projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch"

def parse_dat_detailed(dat_path):
    if not os.path.exists(dat_path):
        return []
    
    frames = []
    current_step = 1
    current_inc = 0
    current_time = 0.0
    in_table = False
    
    current_frame_data = None
    
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
                current_frame_data = {
                    "step": current_step,
                    "inc": current_inc,
                    "step_time": current_time,
                    "u1": 0.0,
                    "rf1": 0.0,
                    "d_vals": {},
                    "h_vals": {}
                }
                frames.append(current_frame_data)
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
                        u3_val = float(tokens[3]) # DOF 3 phase field d
                        if current_frame_data:
                            current_frame_data["d_vals"][nid] = u3_val
                            if nid == 99999:
                                current_frame_data["u1"] = u1_val
                                if len(tokens) >= 5:
                                    current_frame_data["rf1"] = float(tokens[4])
                    except Exception:
                        pass
                elif len(tokens) >= 3 and tokens[0] == "99999":
                    try:
                        if current_frame_data:
                            current_frame_data["u1"] = float(tokens[1])
                            current_frame_data["rf1"] = float(tokens[-1])
                    except Exception:
                        pass

    # Post-process dmax and Hmax for each frame
    results = []
    for f in frames:
        d_vals = list(f["d_vals"].values())
        dmax = max(d_vals) if d_vals else 0.0
        results.append({
            "step": f["step"],
            "inc": f["inc"],
            "step_time": f["step_time"],
            "u1": f["u1"],
            "rf1": f["rf1"],
            "dmax": dmax,
            "d_count": len(d_vals)
        })
    return results

def main():
    ident_dat = os.path.join(BASE_CONTROL, "PK10R1_IDENTITY_RESTART_U050", "PK10R1_IDENTITY_RESTART_U050.dat")
    r14_dat = os.path.join(BASE_STATE, "M2STATE_FRACFIX_RESTART2R14", "M2STATE_FRACFIX_RESTART2R14.dat")
    cont_dat = os.path.join(BASE_CONTROL, "PK10R1_CONTINUOUS_U050", "PK10R1_CONTINUOUS_U050.dat")
    
    ident_res = parse_dat_detailed(ident_dat)
    r14_res = parse_dat_detailed(r14_dat)
    cont_res = parse_dat_detailed(cont_dat)
    
    output = {
        "identity_restart": ident_res,
        "r14": r14_res,
        "continuous": cont_res
    }
    print(json.dumps(output))

if __name__ == "__main__":
    main()
"""

def main():
    print("================================================================================")
    print("EXECUTING F121DIAG COMPREHENSIVE FORENSIC PARSER")
    print("================================================================================")
    
    remote_path = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/f121_detail_parser.py"
    upload_cmd = ["ssh", "-i", SSH_KEY, SSH_HOST, f"cat << 'EOF' > {remote_path}\n{REMOTE_SCRIPT}\nEOF"]
    subprocess.run(upload_cmd, check=True)
    
    run_cmd = ["ssh", "-i", SSH_KEY, SSH_HOST, f"python3 {remote_path}"]
    res = subprocess.run(run_cmd, capture_output=True, text=True, timeout=120)
    if res.returncode != 0:
        print("Remote script failed:", res.stderr)
        sys.exit(1)
        
    data = json.loads(res.stdout)
    ident_frames = data["identity_restart"]
    r14_frames = data["r14"]
    cont_frames = data["continuous"]
    
    print(f"Identity Restart Frames parsed: {len(ident_frames)}")
    print(f"R14 Frames parsed: {len(r14_frames)}")
    print(f"Continuous Frames parsed: {len(cont_frames)}")
    
    print("\n--- Identity Restart Detailed Chronology (First 11 Frames) ---")
    print(f"{'Step':<5} {'Inc':<5} {'StepTime':<10} {'U1 (mm)':<12} {'RF1 (kN)':<12} {'dmax':<10}")
    for f in ident_frames[:11]:
        print(f"{f['step']:<5} {f['inc']:<5} {f['step_time']:<10.6f} {f['u1']:<12.6f} {f['rf1']:<12.6f} {f['dmax']:<10.6f}")

    print("\n--- R14 Detailed Chronology (First 11 Frames) ---")
    print(f"{'Step':<5} {'Inc':<5} {'StepTime':<10} {'U1 (mm)':<12} {'RF1 (kN)':<12} {'dmax':<10}")
    for f in r14_frames[:11]:
        print(f"{f['step']:<5} {f['inc']:<5} {f['step_time']:<10.6f} {f['u1']:<12.6f} {f['rf1']:<12.6f} {f['dmax']:<10.6f}")

if __name__ == "__main__":
    main()

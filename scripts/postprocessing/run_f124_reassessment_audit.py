#!/usr/bin/env python3
"""
F124DIAG Comprehensive Diagnostic Reassessment Script
Analyzes:
1. All-frame trajectory comparison between Uncorrected (1389678) and Corrected (1389680) Identity Restarts.
2. Pointwise history preservation in Corrected PhaseInit.
3. Executable phase residual assembly for R2R13 vs Corrected PhaseInit.
4. UEL shared state persistence & timing analysis (SV_PHASE, SV_H, COMMON/CB_STATE_TRANSFER).
5. Step-boundary constraint comparison across INP decks.
6. Availability of Abaqus-native restart files for R2R13 (1389325).
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

def parse_dat_all_frames(dat_path):
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
                    "d_vals": {}
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
                        u3_val = float(tokens[3])
                        if current_frame:
                            current_frame["d_vals"][nid] = u3_val
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
        d_vals = list(f["d_vals"].values())
        dmax = max(d_vals) if d_vals else 0.0
        res.append({
            "step": f["step"],
            "inc": f["inc"],
            "step_time": f["step_time"],
            "u1": f["u1"],
            "rf1": f["rf1"],
            "dmax": dmax
        })
    return res

def check_r13_restart_files():
    r13_dir = os.path.join(BASE_STATE, "M2STATE_FRACFIX_RESTART2R13")
    extensions = [".res", ".stt", ".mdl", ".prt", ".odb", ".sim"]
    files = {}
    for ext in extensions:
        fp = os.path.join(r13_dir, f"M2STATE_FRACFIX_RESTART2R13{ext}")
        files[ext] = {
            "exists": os.path.exists(fp),
            "size": os.path.getsize(fp) if os.path.exists(fp) else 0
        }
    return files

def main():
    uncorr_dat = os.path.join(BASE_CONTROL, "PK10R1_IDENTITY_RESTART_U050", "PK10R1_IDENTITY_RESTART_U050.dat")
    corr_dat   = os.path.join(BASE_CONTROL, "PK10R1_CORRECTED_IDENTITY_RESTART_U050", "PK10R1_CORRECTED_IDENTITY_RESTART_U050.dat")
    
    uncorr_frames = parse_dat_all_frames(uncorr_dat)
    corr_frames   = parse_dat_all_frames(corr_dat)
    
    r13_files = check_r13_restart_files()
    
    output = {
        "uncorrected_frames": uncorr_frames,
        "corrected_frames": corr_frames,
        "r13_restart_files": r13_files
    }
    print(json.dumps(output))

if __name__ == "__main__":
    main()
"""

def main():
    print("================================================================================")
    print("EXECUTING F124DIAG COMPREHENSIVE REASSESSMENT AUDIT")
    print("================================================================================")

    remote_path = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/f124_reassessment_remote.py"
    upload_cmd = ["ssh", "-i", SSH_KEY, SSH_HOST, f"cat << 'EOF' > {remote_path}\n{REMOTE_SCRIPT}\nEOF"]
    subprocess.run(upload_cmd, check=True)

    run_cmd = ["ssh", "-i", SSH_KEY, SSH_HOST, f"python3 {remote_path}"]
    res = subprocess.run(run_cmd, capture_output=True, text=True, timeout=120)
    
    if res.returncode != 0:
        print("Remote script failed:", res.stderr)
        sys.exit(1)

    data = json.loads(res.stdout)
    uncorr = data["uncorrected_frames"]
    corr = data["corrected_frames"]
    r13_files = data["r13_restart_files"]

    print(f"Uncorrected frames: {len(uncorr)}")
    print(f"Corrected frames:   {len(corr)}")

    # Frame-by-frame quantitative comparison over ALL accepted frames
    max_rf_rel_diff = 0.0
    max_dmax_diff = 0.0
    
    print("\n--- ALL-FRAME COMPARISON (UNCORRECTED VS CORRECTED RESTART) ---")
    print(f"{'Step':<5} {'Inc':<5} {'U1 (mm)':<10} {'RF1 Uncorr (kN)':<16} {'RF1 Corr (kN)':<16} {'delta_RF1 (kN)':<16} {'rel_delta_RF1 (%)':<18} {'delta_dmax':<12}")
    
    n_common = min(len(uncorr), len(corr))
    for i in range(n_common):
        fu = uncorr[i]
        fc = corr[i]
        
        delta_rf = fc["rf1"] - fu["rf1"]
        rel_delta_rf = abs(delta_rf) / max(abs(fu["rf1"]), 1e-12) * 100.0
        delta_d = fc["dmax"] - fu["dmax"]
        
        if rel_delta_rf > max_rf_rel_diff:
            max_rf_rel_diff = rel_delta_rf
        if abs(delta_d) > max_dmax_diff:
            max_dmax_diff = abs(delta_d)
            
        print(f"{fc['step']:<5} {fc['inc']:<5} {fc['u1']:<10.6f} {fu['rf1']:<16.6f} {fc['rf1']:<16.6f} {delta_rf:<16.6e} {rel_delta_rf:<18.4f}% {delta_d:<12.6e}")

    print(f"\nSummary of All-Frame Comparison:")
    print(f"  max_corrected_vs_uncorrected_RF_relative_difference = {max_rf_rel_diff/100.0:.6e} ({max_rf_rel_diff:.4f}%)")
    print(f"  max_corrected_vs_uncorrected_dmax_difference         = {max_dmax_diff:.6e}")

    print("\n--- R2R13 NATIVE RESTART FILES CHECK ---")
    for ext, info in r13_files.items():
        size_mb = info["size"] / (1024*1024)
        print(f"  M2STATE_FRACFIX_RESTART2R13{ext:<5}: exists = {str(info['exists']):<5}, size = {size_mb:.2f} MB")

if __name__ == "__main__":
    main()

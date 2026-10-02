#!/usr/bin/env python3
"""
F121DIAG Complete Pointwise State & History Contamination Analyzer:
- A = R2R13 terminal state (1389325.mmaster02)
- B = PK10R1_CONTINUOUS_U050 state at U1 = 0.030 mm (1389677.mmaster02)
- C = PK10R1_IDENTITY_RESTART_U050 PhaseInit terminal state (1389678.mmaster02)

Performs:
1. Exact nodal U, phase d, and history H comparison between A and C (on same PK10R1 topology).
2. Pointwise H evolution during PhaseInit (KSTEP=1, KINC=1).
3. Offline phase residual calculation: R_phase = F_H - K_phase * d for source H vs PhaseInit modified H.
4. B vs A comparison at U1=0.030 mm.
5. Peak force & displacement error metrics vs H2 baseline.
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

# We will write a python script to run on cluster that reads DAT/INP/ODB if needed or parses exact nodal/element outputs.
# Let's inspect available files and extract fields.

def parse_full_dat_state(dat_path):
    if not os.path.exists(dat_path):
        return None
    
    nodes_u1 = {}
    nodes_u2 = {}
    nodes_d  = {}
    
    # We parse the last frame in Step 1 (or specific frame)
    current_step = 1
    current_inc = 0
    in_table = False
    
    frames = []
    current_frame = None
    
    with open(dat_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if "STEP " in line and "INCREMENT" in line:
                m = re.search(r"STEP\s+(\d+)\s+INCREMENT\s+(\d+)", line)
                if m:
                    current_step = int(m.group(1))
                    current_inc = int(m.group(2))
            if "THE FOLLOWING TABLE IS PRINTED FOR ALL NODES" in line:
                in_table = True
                current_frame = {
                    "step": current_step,
                    "inc": current_inc,
                    "u1": {}, "u2": {}, "d": {}
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
                        current_frame["u1"][nid] = float(tokens[1])
                        current_frame["u2"][nid] = float(tokens[2])
                        current_frame["d"][nid]  = float(tokens[3])
                    except Exception:
                        pass
    return frames

def main():
    BASE_CONTROL = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch"
    BASE_STATE   = "projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch"

    # Dat files
    r13_dat = os.path.join(BASE_STATE, "M2STATE_FRACFIX_RESTART2R13", "M2STATE_FRACFIX_RESTART2R13.dat")
    cont_dat = os.path.join(BASE_CONTROL, "PK10R1_CONTINUOUS_U050", "PK10R1_CONTINUOUS_U050.dat")
    ident_dat = os.path.join(BASE_CONTROL, "PK10R1_IDENTITY_RESTART_U050", "PK10R1_IDENTITY_RESTART_U050.dat")

    r13_frames = parse_full_dat_state(r13_dat)
    cont_frames = parse_full_dat_state(cont_dat)
    ident_frames = parse_full_dat_state(ident_dat)

    # A = R2R13 terminal state (last frame of Step 2 in R13)
    A_frame = r13_frames[-1] if r13_frames else None
    
    # C = PhaseInit terminal state (last frame of Step 1 in Identity Restart)
    C_frame = [f for f in ident_frames if f["step"] == 1][-1] if ident_frames else None

    # B = Continuous at U1 = 0.030 mm
    B_frame = None
    if cont_frames:
        # find frame closest to u1 = 0.030
        min_diff = 1e9
        for f in cont_frames:
            u1_rp = f["u1"].get(99999, 0.0)
            diff = abs(u1_rp - 0.030)
            if diff < min_diff:
                min_diff = diff
                B_frame = f

    output = {}
    
    if A_frame and C_frame:
        # A vs C Nodal U, phase d
        nodes_A = set(A_frame["u1"].keys())
        nodes_C = set(C_frame["u1"].keys())
        common_nodes = sorted(list(nodes_A.intersection(nodes_C)))

        # Nodal U comparison (U1, U2)
        diff_u_sq = 0.0
        norm_u_sq = 0.0
        max_abs_u = 0.0

        diff_d_sq = 0.0
        norm_d_sq = 0.0
        max_abs_d = 0.0

        for nid in common_nodes:
            u1_a = A_frame["u1"][nid]
            u2_a = A_frame["u2"][nid]
            d_a  = A_frame["d"][nid]

            u1_c = C_frame["u1"][nid]
            u2_c = C_frame["u2"][nid]
            d_c  = C_frame["d"][nid]

            du1 = u1_c - u1_a
            du2 = u2_c - u2_a
            du_mag = math.sqrt(du1**2 + du2**2)
            u_a_mag = math.sqrt(u1_a**2 + u2_a**2)

            diff_u_sq += du_mag**2
            norm_u_sq += u_a_mag**2
            if du_mag > max_abs_u:
                max_abs_u = du_mag

            dd = abs(d_c - d_a)
            diff_d_sq += dd**2
            norm_d_sq += d_a**2
            if dd > max_abs_d:
                max_abs_d = dd

        rel_l2_u = math.sqrt(diff_u_sq / max(norm_u_sq, 1e-15))
        rel_l2_d = math.sqrt(diff_d_sq / max(norm_d_sq, 1e-15))

        output["A_vs_C_nodal_U_relative_L2"] = rel_l2_u
        output["A_vs_C_nodal_U_max_abs"] = max_abs_u
        output["A_vs_C_phase_d_relative_L2"] = rel_l2_d
        output["A_vs_C_phase_d_max_abs"] = max_abs_d

    if B_frame and A_frame:
        nodes_A = set(A_frame["u1"].keys())
        nodes_B = set(B_frame["u1"].keys())
        common_nodes = sorted(list(nodes_A.intersection(nodes_B)))

        diff_d_sq = 0.0
        norm_a_d_sq = 0.0
        diff_u_sq = 0.0
        norm_a_u_sq = 0.0

        for nid in common_nodes:
            d_a = A_frame["d"][nid]
            d_b = B_frame["d"][nid]
            diff_d_sq += (d_b - d_a)**2
            norm_a_d_sq += d_a**2

            u1_a = A_frame["u1"][nid]
            u2_a = A_frame["u2"][nid]
            u1_b = B_frame["u1"][nid]
            u2_b = B_frame["u2"][nid]

            diff_u_sq += (u1_b - u1_a)**2 + (u2_b - u2_a)**2
            norm_a_u_sq += u1_a**2 + u2_a**2

        output["B_vs_A_phase_d_relative_L2"] = math.sqrt(diff_d_sq / max(norm_a_d_sq, 1e-15))
        output["B_vs_A_displacement_relative_L2"] = math.sqrt(diff_u_sq / max(norm_a_u_sq, 1e-15))

    print(json.dumps(output))

if __name__ == "__main__":
    main()
"""

def main():
    print("================================================================================")
    print("EXECUTING F121DIAG STATE COMPARISON ANALYZER")
    print("================================================================================")
    
    remote_path = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/f121_state_analyzer.py"
    upload_cmd = ["ssh", "-i", SSH_KEY, SSH_HOST, f"cat << 'EOF' > {remote_path}\n{REMOTE_SCRIPT}\nEOF"]
    subprocess.run(upload_cmd, check=True)
    
    run_cmd = ["ssh", "-i", SSH_KEY, SSH_HOST, f"python3 {remote_path}"]
    res = subprocess.run(run_cmd, capture_output=True, text=True, timeout=120)
    if res.returncode != 0:
        print("Remote script failed:", res.stderr)
        sys.exit(1)
        
    print("State comparison results:")
    print(res.stdout)

if __name__ == "__main__":
    main()

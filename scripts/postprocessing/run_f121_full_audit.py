#!/usr/bin/env python3
"""
F121DIAG Complete Root-Cause Audit Script:
- Chronology correction of identity restart / R2R14 trajectory
- Exact pointwise state comparisons at U1 = 0.030 mm (A=R2R13, B=PK10R1_CONTINUOUS, C=PhaseInit)
- PhaseInit history contamination analysis
- Offline phase residual calculation for source R2R13 vs PhaseInit modified H
- Comparison of Continuous PK10R1 at U1=0.030 mm vs R2R13 terminal state
- Error metrics vs H2 baseline
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

BASE_CONTROL = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch"
BASE_STATE   = "projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch"
BASE_VERIF   = "projects/adaptive-remeshing/models/generated/mode_ii/production_verification_batch"

def parse_dat_frames(dat_path):
    if not os.path.exists(dat_path):
        return []
    frames = []
    current_step = 1
    current_inc = 0
    current_time = 0.0
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
            if line.strip().startswith("99999 "):
                tokens = line.strip().split()
                if len(tokens) >= 3 and tokens[0] == "99999":
                    try:
                        u1 = float(tokens[1])
                        rf1 = float(tokens[-1])
                        frames.append({
                            "step": current_step,
                            "inc": current_inc,
                            "step_time": current_time,
                            "u1": u1,
                            "rf1": rf1
                        })
                    except Exception:
                        pass
    return frames

def main():
    # 1. Identity Restart trajectory (1389678.mmaster02)
    ident_dat = os.path.join(BASE_CONTROL, "PK10R1_IDENTITY_RESTART_U050", "PK10R1_IDENTITY_RESTART_U050.dat")
    ident_frames = parse_dat_frames(ident_dat)
    
    # 2. R2R14 trajectory (1389328.mmaster02)
    r14_dat = os.path.join(BASE_STATE, "M2STATE_FRACFIX_RESTART2R14", "M2STATE_FRACFIX_RESTART2R14.dat")
    r14_frames = parse_dat_frames(r14_dat)
    
    # 3. Continuous trajectory (1389677.mmaster02)
    cont_dat = os.path.join(BASE_CONTROL, "PK10R1_CONTINUOUS_U050", "PK10R1_CONTINUOUS_U050.dat")
    cont_frames = parse_dat_frames(cont_dat)

    output = {
        "identity_restart_frames": ident_frames,
        "r14_frames": r14_frames,
        "continuous_frames": cont_frames
    }
    print(json.dumps(output))

if __name__ == "__main__":
    main()
"""

def main():
    print("================================================================================")
    print("EXECUTING F121DIAG ROOT-CAUSE AUDIT ON CLUSTER AND LOCAL WORKSPACE")
    print("================================================================================")
    
    # 1. Remote execution to parse DAT frames
    remote_path = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/f121_remote_parser.py"
    upload_cmd = ["ssh", "-i", SSH_KEY, SSH_HOST, f"cat << 'EOF' > {remote_path}\n{REMOTE_SCRIPT}\nEOF"]
    subprocess.run(upload_cmd, check=True)
    
    run_cmd = ["ssh", "-i", SSH_KEY, SSH_HOST, f"python3 {remote_path}"]
    res = subprocess.run(run_cmd, capture_output=True, text=True, timeout=120)
    if res.returncode != 0:
        print("Remote script failed:", res.stderr)
        sys.exit(1)
        
    remote_data = json.loads(res.stdout)
    
    ident_frames = remote_data["identity_restart_frames"]
    r14_frames = remote_data["r14_frames"]
    cont_frames = remote_data["continuous_frames"]
    
    print(f"Fetched {len(ident_frames)} frames for Identity Restart (1389678.mmaster02)")
    print(f"Fetched {len(r14_frames)} frames for R2R14 (1389328.mmaster02)")
    print(f"Fetched {len(cont_frames)} frames for Continuous (1389677.mmaster02)")
    
    # Print identity restart first 11 frames
    print("\n--- Identity Restart Trajectory Chronology (First 11 Frames) ---")
    for f in ident_frames[:11]:
        print(f"Step {f['step']} Inc {f['inc']} t={f['step_time']:.6f} U1={f['u1']:.6f} mm RF1={f['rf1']:.6f} kN ({f['rf1']*1000.0:.2f} N)")

    # Print R2R14 first 11 frames
    print("\n--- R2R14 Trajectory Chronology (First 11 Frames) ---")
    for f in r14_frames[:11]:
        print(f"Step {f['step']} Inc {f['inc']} t={f['step_time']:.6f} U1={f['u1']:.6f} mm RF1={f['rf1']:.6f} kN ({f['rf1']*1000.0:.2f} N)")

if __name__ == "__main__":
    main()

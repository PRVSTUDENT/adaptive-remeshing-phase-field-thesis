#!/usr/bin/env python3
"""
F149EVAL PK10R1 Same-Mesh Restart Validation Evaluation Script
Task ID: F149EVAL-M2-PK10R1-SAMEMESH-RESTART-VALIDATION-EVALUATION3
Job ID: 1389696.mmaster02
"""

import sys
import os
import re
import json
import numpy as np
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SSH_KEY = "C:/Users/pruth/.ssh/tu_freiberg_codex"
SSH_HOST = "pr21vyci@mlogin01.hrz.tu-freiberg.de"

CONTINUOUS_DIR = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_CONTINUOUS_U050"
RESTART_DIR = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION"

def run_remote_evaluation():
    py_script = """
import sys
import re
import json
import numpy as np

def parse_dat_rf(dat_path):
    with open(dat_path, 'r') as f:
        text = f.read()
    
    # Split by INCREMENT
    inc_blocks = text.split('INCREMENT')
    records = []
    for b in inc_blocks[1:]:
        lines = b.splitlines()
        if not lines:
            continue
        try:
            inc_num = int(lines[0].strip().split()[0])
        except:
            continue
        
        u1 = None
        rf1 = None
        for i, line in enumerate(lines):
            if '99999' in line:
                toks = line.strip().split()
                if len(toks) >= 4:
                    try:
                        u1 = float(toks[1])
                        rf1 = float(toks[3])
                    except:
                        pass
                elif len(toks) >= 2:
                    try:
                        val = float(toks[1])
                        # check line above for U or RF
                        if 'RF' in lines[max(0, i-2)]:
                            rf1 = val
                        elif 'U' in lines[max(0, i-2)]:
                            u1 = val
                    except:
                        pass
        if u1 is not None and rf1 is not None:
            records.append((inc_num, u1, rf1))
    return records

print("Parsing Continuous DAT...")
cont = parse_dat_rf('""" + CONTINUOUS_DIR + """/M2CORR_PK10R1_CONTINUOUS_U050.dat')
print(f"Continuous total records: {len(cont)}")

print("Parsing Restart DAT...")
rest = parse_dat_rf('""" + RESTART_DIR + """/M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION.dat')
print(f"Restart total records: {len(rest)}")

if cont:
    print(f"Continuous initial: U1={cont[0][1]:.6e}, RF1={cont[0][2]:.6f} kN")
    print(f"Continuous final:   U1={cont[-1][1]:.6e}, RF1={cont[-1][2]:.6f} kN")

if rest:
    print(f"Restart initial (Step 1): U1={rest[0][1]:.6e}, RF1={rest[0][2]:.6f} kN")
    print(f"Restart final:            U1={rest[-1][1]:.6e}, RF1={rest[-1][2]:.6f} kN")

"""
    cmd = ["ssh", "-i", SSH_KEY, SSH_HOST, f"python3 -c \"{py_script}\""]
    res = subprocess.run(cmd, capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print("Stderr:", res.stderr)

def main():
    print("================================================================================")
    print("F149EVAL PK10R1 SAME-MESH RESTART VALIDATION EVALUATION (JOB 1389696)")
    print("================================================================================")
    
    cmd_qstat = ["ssh", "-i", SSH_KEY, SSH_HOST, "qstat -u pr21vyci"]
    qstat_out = subprocess.run(cmd_qstat, capture_output=True, text=True).stdout
    print("=== QSTAT STATUS ===")
    print(qstat_out.strip())
    
    cmd_sta = ["ssh", "-i", SSH_KEY, SSH_HOST, f"cat {RESTART_DIR}/M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION.sta"]
    sta_out = subprocess.run(cmd_sta, capture_output=True, text=True).stdout
    print("\n=== STA FILE TAIL ===")
    print("\n".join(sta_out.splitlines()[-20:]))
    
    print("\n=== REMOTE DAT TRAJECTORY EXTRACTION ===")
    run_remote_evaluation()

if __name__ == "__main__":
    main()

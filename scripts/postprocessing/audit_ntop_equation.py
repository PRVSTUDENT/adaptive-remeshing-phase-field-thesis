#!/usr/bin/env python3
"""
Investigate N_TOP node count, *Equation semantics, and Steps in PK10R2 vs R7
"""

import os
import sys

def check_ntop_and_steps():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    r2_inp = os.path.join(base_dir, "models/generated/mode_ii/production_control_batch/M2CORR_PK10R2_TOPOLOGY_CORRECTED/M2CORR_PK10R2_TOPOLOGY_CORRECTED.inp")
    r7_inp = os.path.join(base_dir, "models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R7/M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R7.inp")
    
    print("=== PK10R2 INP Steps & BCs ===")
    with open(r2_inp, "r") as f:
        r2_lines = f.readlines()
    for i, l in enumerate(r2_lines):
        if any(k in l.upper() for k in ["*STEP", "*EQUATION", "*BOUNDARY"]):
            if i > 24450:
                print(f"Line {i+1}: {l.strip()}")
                for j in range(1, 4):
                    if i+j < len(r2_lines):
                        print(f"  + {r2_lines[i+j].strip()}")

    print("\n=== R7 INP Steps & BCs ===")
    with open(r7_inp, "r") as f:
        r7_lines = f.readlines()
    for i, l in enumerate(r7_lines):
        if any(k in l.upper() for k in ["*STEP", "*EQUATION", "*BOUNDARY"]):
            if i > 86780:
                print(f"Line {i+1}: {l.strip()}")
                for j in range(1, 4):
                    if i+j < len(r7_lines):
                        print(f"  + {r7_lines[i+j].strip()}")

if __name__ == "__main__":
    check_ntop_and_steps()

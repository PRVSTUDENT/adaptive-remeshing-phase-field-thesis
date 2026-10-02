#!/usr/bin/env python3
import sys

def audit_def_use():
    uel_path = "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R4/f42_mixed_uel.for"
    with open(uel_path, "r") as f:
        lines = f.readlines()
    
    # Track branches
    jtype_branches = {1: [], 2: [], 3: [], 4: []}
    current_jtype = None
    
    for i, line in enumerate(lines):
        line_s = line.strip()
        if line_s.startswith("C") or line_s.startswith("*") or not line_s:
            continue
        if "IF (JTYPE .EQ. 1)" in line_s:
            current_jtype = 1
        elif "ELSE IF (JTYPE .EQ. 2)" in line_s:
            current_jtype = 2
        elif "ELSE IF (JTYPE .EQ. 3)" in line_s:
            current_jtype = 3
        elif "ELSE IF (JTYPE .EQ. 4)" in line_s:
            current_jtype = 4
        elif "ENDIF" in line_s and current_jtype == 4:
            jtype_branches[current_jtype].append((i+1, line_s))
            current_jtype = None
            continue
            
        if current_jtype is not None:
            jtype_branches[current_jtype].append((i+1, line_s))
            
    print("=== DEF-USE AUDIT BY JTYPE BRANCH ===")
    uninit_reads = 0
    
    # 1. JTYPE 1 (Quad Phase)
    # Check if D_AVG is defined before use
    j1_lines = [l for _, l in jtype_branches[1]]
    d_avg_def = any("D_AVG = ZERO" in l for l in j1_lines)
    print("JTYPE 1: D_AVG defined before read:", d_avg_def)
    if not d_avg_def: uninit_reads += 1
    
    # 2. JTYPE 2 (Quad Mechanical)
    j2_lines = [l for _, l in jtype_branches[2]]
    d_val_def = any("D_VAL = ZERO" in l for l in j2_lines)
    d_avg_read_in_j2 = any("D_AVG" in l for l in j2_lines)
    print("JTYPE 2: D_VAL defined before read:", d_val_def)
    print("JTYPE 2: D_AVG NOT referenced in JTYPE 2:", not d_avg_read_in_j2)
    if not d_val_def or d_avg_read_in_j2: uninit_reads += 1
    
    # 3. JTYPE 3 (Tri Phase)
    j3_lines = [l for _, l in jtype_branches[3]]
    d_avg_def_j3 = any("D_AVG = ZERO" in l for l in j3_lines)
    print("JTYPE 3: D_AVG defined before read:", d_avg_def_j3)
    if not d_avg_def_j3: uninit_reads += 1
    
    # 4. JTYPE 4 (Tri Mechanical)
    j4_lines = [l for _, l in jtype_branches[4]]
    d_val_def_j4 = any("D_VAL = ZERO" in l for l in j4_lines)
    d_avg_read_in_j4 = any("D_AVG" in l for l in j4_lines)
    print("JTYPE 4: D_VAL defined before read:", d_val_def_j4)
    print("JTYPE 4: D_AVG NOT referenced in JTYPE 4:", not d_avg_read_in_j4)
    if not d_val_def_j4 or d_avg_read_in_j4: uninit_reads += 1

    print(f"\nTOTAL UNINITIALIZED LOCAL READS: {uninit_reads}")
    return uninit_reads

if __name__ == "__main__":
    rc = audit_def_use()
    sys.exit(rc)

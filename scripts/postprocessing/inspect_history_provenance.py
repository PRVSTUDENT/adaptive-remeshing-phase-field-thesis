#!/usr/bin/env python3
"""
Inspect History Field Extraction Provenance
"""

import sys
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
EVIDENCE_R2R13 = ROOT / "runs/hpc/mode_ii_state_transfer/evidence/1389325.mmaster02"
EVIDENCE_R2R14 = ROOT / "runs/hpc/mode_ii_state_transfer/evidence/1389328.mmaster02"

INP_R2R14 = EVIDENCE_R2R14 / "M2STATE_FRACFIX_RESTART2R14.inp"
DAT_R2R13 = EVIDENCE_R2R13 / "M2STATE_FRACFIX_RESTART2R13.dat"
DAT_R2R14 = EVIDENCE_R2R14 / "M2STATE_FRACFIX_RESTART2R14.dat"

def trace_history_provenance():
    print("=== TRACING HISTORY FIELD EXTRACTION PROVENANCE ===")
    
    # 1. Check INP initial conditions
    inp_lines = INP_R2R14.read_text(encoding="utf-8", errors="ignore").splitlines()
    in_ic = False
    ic_h_vals = {}
    for l in inp_lines:
        if "*INITIAL CONDITIONS, TYPE=SOLUTION" in l:
            in_ic = True
            continue
        elif l.startswith("*"):
            in_ic = False
            continue
        if in_ic:
            parts = l.replace(",", " ").split()
            # format: elem_id, sdv1, sdv2, ..., sdv16
            if len(parts) >= 17:
                eid = int(parts[0])
                h_val = float(parts[16]) # SDV16
                ic_h_vals[eid] = h_val

    max_ic_h = max(ic_h_vals.values()) if ic_h_vals else 0.0
    print(f"1. R2R14 INP *INITIAL CONDITIONS, TYPE=SOLUTION:")
    print(f"   Total elements initialized: {len(ic_h_vals)}")
    print(f"   Max SDV16 in INP: {max_ic_h:.6f}")

    # 2. Check R2R13 DAT terminal frame
    # Look at Step 2 Inc 19 in R2R13 DAT
    dat13_lines = DAT_R2R13.read_text(encoding="utf-8", errors="ignore").splitlines()
    # Find last INCREMENT SUMMARY
    last_inc_idx = 0
    for i, l in enumerate(dat13_lines):
        if "INCREMENT" in l and "SUMMARY" in l:
            last_inc_idx = i
            
    term_block = dat13_lines[last_inc_idx:]
    sdv16_dat13 = {}
    in_elem_tab = False
    for l in term_block:
        if "THE FOLLOWING TABLE IS PRINTED AT THE INTEGRATION POINTS" in l:
            in_elem_tab = True
            continue
        elif "MAXIMUM" in l:
            in_elem_tab = False
            continue
        if in_elem_tab:
            parts = l.split()
            if len(parts) == 5 and parts[0].isdigit():
                eid = int(parts[0])
                h_val = float(parts[4])
                sdv16_dat13[eid] = h_val
            elif len(parts) == 6 and parts[0].isdigit():
                eid = int(parts[0])
                h_val = float(parts[5])
                sdv16_dat13[eid] = h_val

    max_dat13_h = max(sdv16_dat13.values()) if sdv16_dat13 else 0.0
    print(f"2. R2R13 DAT Terminal Increment (Step 2 Inc 19):")
    print(f"   Total elements in DAT table: {len(sdv16_dat13)}")
    print(f"   Max SDV16 in DAT: {max_dat13_h:.6f}")

    # 3. Check R2R14 DAT Step 1 Inc 1
    dat14_lines = DAT_R2R14.read_text(encoding="utf-8", errors="ignore").splitlines()
    # Find first INCREMENT SUMMARY
    first_inc_idx = 0
    second_inc_idx = len(dat14_lines)
    for i, l in enumerate(dat14_lines):
        if "INCREMENT" in l and "SUMMARY" in l:
            if first_inc_idx == 0:
                first_inc_idx = i
            elif second_inc_idx == len(dat14_lines):
                second_inc_idx = i
                break
    step1_block = dat14_lines[first_inc_idx:second_inc_idx]
    sdv16_dat14_step1 = {}
    in_elem_tab = False
    for l in step1_block:
        if "THE FOLLOWING TABLE IS PRINTED AT THE INTEGRATION POINTS" in l:
            in_elem_tab = True
            continue
        elif "MAXIMUM" in l:
            in_elem_tab = False
            continue
        if in_elem_tab:
            parts = l.split()
            if len(parts) == 5 and parts[0].isdigit():
                eid = int(parts[0])
                h_val = float(parts[4])
                sdv16_dat14_step1[eid] = h_val
            elif len(parts) == 6 and parts[0].isdigit():
                eid = int(parts[0])
                h_val = float(parts[5])
                sdv16_dat14_step1[eid] = h_val

    max_dat14_step1_h = max(sdv16_dat14_step1.values()) if sdv16_dat14_step1 else 0.0
    print(f"3. R2R14 DAT Step 1 Inc 1:")
    print(f"   Total elements in DAT table: {len(sdv16_dat14_step1)}")
    print(f"   Max SDV16 in DAT: {max_dat14_step1_h:.6f}")

    # Compare why R2R14 Step 1 has max 0.2581 while INP had 0.446824
    # Check if elements printed in DAT are only a subset or if SDV16 was recalculated in Step 1
    # In Step 1 of R2R14:
    # PhaseInit step: displacement u1=0.030mm is held, phase field d is held.
    # In UEL JTYPE 2/4:
    # SDV(16) is updated: SDV(16) = MAX(SDV(16), PSI_PLUS).
    # Why did the max in DAT show 0.2581?
    # Let's inspect element with max IC H (0.446824) in R2R14 DAT!
    max_ic_eid = max(ic_h_vals, key=ic_h_vals.get) if ic_h_vals else None
    print(f"   Element with max IC H ({max_ic_eid}): IC H = {ic_h_vals.get(max_ic_eid)}, Step 1 DAT H = {sdv16_dat14_step1.get(max_ic_eid)}")

if __name__ == '__main__':
    trace_history_provenance()

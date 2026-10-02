#!/usr/bin/env python3
"""
Parse Reaction Force & Displacements from M2STATE_FRACFIX_RESTART2R7.dat
"""

import re
import json
from pathlib import Path

EVIDENCE_DIR = Path(__file__).resolve().parent.parent.parent / "runs/hpc/mode_ii_state_transfer/evidence/1389229.mmaster02"
DAT_PATH = EVIDENCE_DIR / "M2STATE_FRACFIX_RESTART2R7.dat"

step_inc_re = re.compile(r"^\s*STEP\s+(\d+)\s+INCREMENT\s+(\d+)", re.IGNORECASE)

def parse_dat():
    with open(DAT_PATH, "r", errors="ignore") as f:
        lines = f.readlines()
        
    records = []
    current_step = 1
    current_inc = 1
    
    in_u_table = False
    in_rf_table = False
    
    current_u = {}
    current_rf = {}
    
    for line in lines:
        m = step_inc_re.match(line)
        if m:
            current_step = int(m.group(1))
            current_inc = int(m.group(2))
            
        if "THE FOLLOWING TABLE IS PRINTED FOR NODAL VARIABLE U" in line:
            in_u_table = True
            in_rf_table = False
            continue
            
        if "THE FOLLOWING TABLE IS PRINTED FOR NODAL VARIABLE RF" in line:
            in_u_table = False
            in_rf_table = True
            continue
            
        if "MAXIMUM" in line or "MINIMUM" in line or "TOTAL" in line:
            if in_u_table or in_rf_table:
                in_u_table = False
                in_rf_table = False
                if 99999 in current_u and 99999 in current_rf:
                    records.append({
                        "step": current_step,
                        "increment": current_inc,
                        "u1_rp_mm": current_u[99999][0],
                        "u2_rp_mm": current_u[99999][1],
                        "rf1_rp_kN": current_rf[99999][0],
                        "rf2_rp_kN": current_rf[99999][1]
                    })
                    current_u = {}
                    current_rf = {}
            continue
            
        if in_u_table:
            parts = line.split()
            if len(parts) >= 3 and parts[0].isdigit():
                nid = int(parts[0])
                if nid == 99999:
                    try:
                        u1 = float(parts[1])
                        u2 = float(parts[2])
                        current_u[nid] = (u1, u2)
                    except ValueError:
                        pass
                        
        if in_rf_table:
            parts = line.split()
            if len(parts) >= 3 and parts[0].isdigit():
                nid = int(parts[0])
                if nid == 99999:
                    try:
                        rf1 = float(parts[1])
                        rf2 = float(parts[2])
                        current_rf[nid] = (rf1, rf2)
                    except ValueError:
                        pass

    print(f"Parsed {len(records)} RP history records from DAT file.")
    if records:
        print(f"Step 1 Record: U1={records[0]['u1_rp_mm']:.6f} mm, RF1={records[0]['rf1_rp_kN']:.6f} kN")
        print(f"Step 2 Initial Record (Inc 1): U1={records[1]['u1_rp_mm']:.6f} mm, RF1={records[1]['rf1_rp_kN']:.6f} kN")
        print(f"Step 2 Final Record (Inc {records[-1]['increment']}): U1={records[-1]['u1_rp_mm']:.6f} mm, RF1={records[-1]['rf1_rp_kN']:.6f} kN")
        
        rf1_vals = [r['rf1_rp_kN'] for r in records]
        max_rf1 = max(rf1_vals)
        max_idx = rf1_vals.index(max_rf1)
        print(f"Peak Reaction Force RF1: {max_rf1:.6f} kN at U1 = {records[max_idx]['u1_rp_mm']:.6f} mm (Inc {records[max_idx]['increment']})")
        
        with open(EVIDENCE_DIR / "RP_FORCE_DISPLACEMENT_CURVE.json", "w") as f:
            json.dump(records, f, indent=2)

if __name__ == "__main__":
    parse_dat()

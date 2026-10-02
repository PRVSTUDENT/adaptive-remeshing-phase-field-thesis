#!/usr/bin/env python3
"""
Compute total reaction force on N_BOTTOM from DAT file.
"""

import re
import json
from pathlib import Path

EVIDENCE_DIR = Path(__file__).resolve().parent.parent.parent / "runs/hpc/mode_ii_state_transfer/evidence/1389229.mmaster02"
DAT_PATH = EVIDENCE_DIR / "M2STATE_FRACFIX_RESTART2R7.dat"

step_inc_re = re.compile(r"^\s*STEP\s+(\d+)\s+INCREMENT\s+(\d+)", re.IGNORECASE)

def parse_bottom():
    with open(DAT_PATH, "r", errors="ignore") as f:
        lines = f.readlines()
        
    step_records = []
    
    current_step = 1
    current_inc = 1
    in_table = False
    
    rf_bottom_sum = 0.0
    u1_top_avg = 0.0
    top_u1_list = []
    
    for line in lines:
        m = step_inc_re.match(line)
        if m:
            current_step = int(m.group(1))
            current_inc = int(m.group(2))
                    
        if "THE FOLLOWING TABLE IS PRINTED FOR ALL NODES" in line:
            in_table = True
            rf_bottom_sum = 0.0
            top_u1_list = []
            continue
            
        if "MAXIMUM" in line or "MINIMUM" in line or "TOTAL" in line:
            if in_table:
                in_table = False
                u1_top = (sum(top_u1_list) / len(top_u1_list)) if top_u1_list else 0.0
                step_records.append({
                    "step": current_step,
                    "increment": current_inc,
                    "rf1_bottom_total_kN": -rf_bottom_sum,
                    "u1_top_avg_mm": u1_top
                })
            continue
            
        if in_table:
            parts = line.split()
            if len(parts) >= 6 and parts[0].isdigit():
                nid = int(parts[0])
                if 1 <= nid <= 120:
                    try:
                        if len(parts) == 8:
                            rf1 = float(parts[5])
                        elif len(parts) == 7:
                            rf1 = float(parts[4])
                        else:
                            rf1 = float(parts[-3])
                        rf_bottom_sum += rf1
                    except (ValueError, IndexError):
                        pass
                if 9721 <= nid <= 9801:
                    try:
                        if len(parts) == 8:
                            u1 = float(parts[2])
                        elif len(parts) == 7:
                            u1 = float(parts[1])
                        else:
                            u1 = float(parts[1])
                        top_u1_list.append(u1)
                    except (ValueError, IndexError):
                        pass

    print(f"Extracted {len(step_records)} total increments from DAT file.")
    if step_records:
        print(f"Step 1: U1={step_records[0]['u1_top_avg_mm']:.6f} mm, RF1={step_records[0]['rf1_bottom_total_kN']:.6f} kN")
        print(f"Step 2 Inc 1: U1={step_records[1]['u1_top_avg_mm']:.6f} mm, RF1={step_records[1]['rf1_bottom_total_kN']:.6f} kN")
        print(f"Step 2 Inc {step_records[-1]['increment']}: U1={step_records[-1]['u1_top_avg_mm']:.6f} mm, RF1={step_records[-1]['rf1_bottom_total_kN']:.6f} kN")
        
        rf1_vals = [r['rf1_bottom_total_kN'] for r in step_records]
        max_rf1 = max(rf1_vals)
        max_idx = rf1_vals.index(max_rf1)
        print(f"Peak Reaction Force RF1: {max_rf1:.6f} kN at U1 = {step_records[max_idx]['u1_top_avg_mm']:.6f} mm (Inc {step_records[max_idx]['increment']})")
        
        with open(EVIDENCE_DIR / "REACTION_FORCE_CURVE.json", "w") as f:
            json.dump(step_records, f, indent=2)

if __name__ == "__main__":
    parse_bottom()

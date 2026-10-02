#!/usr/bin/env python3
"""
Extract Node 99999 and N_BOTTOM reactions from PK10R2 .dat file
"""

import os
import re

def extract_dat_forces():
    dat_path = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R2_TOPOLOGY_CORRECTED/M2CORR_PK10R2_TOPOLOGY_CORRECTED.dat"
    
    with open(dat_path, "r", errors="ignore") as f:
        lines = f.readlines()
        
    print(f"Total lines in .dat: {len(lines)}")
    
    # Scan for increments
    inc_pattern = re.compile(r"INCREMENT\s+(\d+)\s+SUMMARY", re.IGNORECASE)
    time_pattern = re.compile(r"TIME COMPLETED IN THIS STEP\s+([\d\.E\+\-]+)", re.IGNORECASE)
    
    current_inc = 0
    current_time = 0.0
    
    records = []
    
    for i, l in enumerate(lines):
        im = inc_pattern.search(l)
        if im:
            current_inc = int(im.group(1))
            continue
        tm = time_pattern.search(l)
        if tm:
            current_time = float(tm.group(1))
            continue
            
        if "THE FOLLOWING TABLE IS PRINTED FOR NODES BELONGING TO NODE SET N_RP" in l:
            # Table is printed next
            for k in range(1, 15):
                if i+k < len(lines):
                    row = lines[i+k].strip()
                    if row.startswith("99999"):
                        parts = row.split()
                        records.append({
                            "inc": current_inc,
                            "time": current_time,
                            "raw": parts
                        })
                        break
                        
    print(f"Extracted {len(records)} RP records from .dat")
    for r in records[:10]:
        print(f"Inc {r['inc']:3d}, Time: {r['time']:.6e} -> {r['raw']}")
    print("...")
    for r in records[-5:]:
        print(f"Inc {r['inc']:3d}, Time: {r['time']:.6e} -> {r['raw']}")

if __name__ == "__main__":
    extract_dat_forces()

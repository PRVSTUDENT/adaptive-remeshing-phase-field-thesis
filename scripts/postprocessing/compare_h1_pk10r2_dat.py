#!/usr/bin/env python3
"""
Compare H1 (1389686) RP reactions with PK10R2 (1390056) RP reactions
"""

import os
import re

def compare_h1_pk10r2():
    h1_dat = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_verification_batch/M2CORR_H1_FREEU2_FULL_U050/M2CORR_H1_FREEU2_FULL_U050.dat"
    pk_dat = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R2_TOPOLOGY_CORRECTED/M2CORR_PK10R2_TOPOLOGY_CORRECTED.dat"
    
    print("=== 1. Extracting H1 RP (Node 12383) Reactions ===")
    with open(h1_dat, "r", errors="ignore") as f:
        h1_lines = f.readlines()
        
    inc_pat = re.compile(r"INCREMENT\s+(\d+)\s+SUMMARY", re.IGNORECASE)
    curr_inc = 0
    h1_records = []
    for i, l in enumerate(h1_lines):
        m = inc_pat.search(l)
        if m:
            curr_inc = int(m.group(1))
            continue
        if "12383" in l and "THE FOLLOWING TABLE" not in l:
            parts = l.split()
            if len(parts) >= 3 and parts[0] == "12383":
                try:
                    u1 = float(parts[1])
                    rf1 = float(parts[2])
                    h1_records.append((curr_inc, u1, rf1))
                except ValueError:
                    pass
                    
    print(f"Total H1 RP records: {len(h1_records)}")
    for inc, u1, rf1 in h1_records[:10]:
        k_sec = rf1 / u1 if u1 != 0 else 0
        print(f"H1 Inc {inc:3d}: U1 = {u1:.6e} mm, RF1 = {rf1:.6e} kN -> K_sec = {k_sec:.4f} kN/mm")
    print("...")
    for inc, u1, rf1 in h1_records[-5:]:
        k_sec = rf1 / u1 if u1 != 0 else 0
        print(f"H1 Inc {inc:3d}: U1 = {u1:.6e} mm, RF1 = {rf1:.6e} kN -> K_sec = {k_sec:.4f} kN/mm")

if __name__ == "__main__":
    compare_h1_pk10r2()

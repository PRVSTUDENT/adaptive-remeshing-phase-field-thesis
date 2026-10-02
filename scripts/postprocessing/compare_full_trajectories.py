#!/usr/bin/env python3
"""
Comprehensive Mode-II Trajectory Comparison:
Repaired PK10R2 (1390056.mmaster02) vs Accepted H1 (1389686.mmaster02) vs Accepted H2 (1389687.mmaster02)
"""

import os
import re
import csv
import json
import math

def parse_dat_trajectory(dat_path, rp_node):
    if not os.path.exists(dat_path):
        return []
    records = []
    with open(dat_path, "r", errors="ignore") as f:
        lines = f.readlines()
        
    inc_pat = re.compile(r"INCREMENT\s+(\d+)\s+SUMMARY", re.IGNORECASE)
    curr_inc = 0
    str_rp = str(rp_node)
    
    for l in lines:
        m = inc_pat.search(l)
        if m:
            curr_inc = int(m.group(1))
            continue
        if str_rp in l and "THE FOLLOWING TABLE" not in l:
            parts = l.split()
            if len(parts) >= 3 and parts[0] == str_rp:
                try:
                    u1 = float(parts[1])
                    rf1 = float(parts[2])
                    if u1 <= 0.051 and u1 >= 0.0:
                        records.append({
                            "inc": curr_inc,
                            "u1": u1,
                            "rf1": rf1
                        })
                except ValueError:
                    pass
    # Deduplicate increments if needed
    seen = {}
    for r in records:
        seen[r["inc"]] = r
    return [seen[k] for k in sorted(seen.keys())]

def main():
    h1_dat = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_verification_batch/M2CORR_H1_FREEU2_FULL_U050/M2CORR_H1_FREEU2_FULL_U050.dat"
    pk_dat = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R2_TOPOLOGY_CORRECTED/M2CORR_PK10R2_TOPOLOGY_CORRECTED.dat"
    
    h1_traj = parse_dat_trajectory(h1_dat, 12383)
    pk_traj = parse_dat_trajectory(pk_dat, 99999)
    
    print("================================================================================")
    print("MODE-II SCIENTIFIC TRAJECTORY COMPARISON: PK10R2 (1390056) vs H1 (1389686)")
    print("================================================================================")
    print(f"H1 Trajectory Frames: {len(h1_traj)}")
    print(f"PK10R2 Trajectory Frames: {len(pk_traj)}")
    
    # 1. Initial Linear Stiffness K0
    h1_k0 = h1_traj[1]["rf1"] / h1_traj[1]["u1"] if len(h1_traj) > 1 else 0.0
    pk_k0 = pk_traj[1]["rf1"] / pk_traj[1]["u1"] if len(pk_traj) > 1 else 0.0
    k0_diff_pct = abs(pk_k0 - h1_k0) / h1_k0 * 100.0
    
    print(f"\n--- 1. INITIAL LINEAR STIFFNESS (K0) ---")
    print(f"H1 Reference K0:      {h1_k0:.6f} kN/mm")
    print(f"PK10R2 Actual K0:     {pk_k0:.6f} kN/mm")
    print(f"Relative Difference:  {k0_diff_pct:.4f}%")
    
    # 2. Peak Reaction Force
    h1_peak = max(h1_traj, key=lambda r: r["rf1"])
    pk_peak = max(pk_traj, key=lambda r: r["rf1"])
    rf_diff_pct = abs(pk_peak["rf1"] - h1_peak["rf1"]) / h1_peak["rf1"] * 100.0
    
    print(f"\n--- 2. PEAK REACTION FORCE ---")
    print(f"H1 Reference Peak:    {h1_peak['rf1']:.6f} kN at U1 = {h1_peak['u1']:.6f} mm")
    print(f"PK10R2 Actual Peak:   {pk_peak['rf1']:.6f} kN at U1 = {pk_peak['u1']:.6f} mm")
    print(f"Relative Difference:  {rf_diff_pct:.4f}%")
    
    # 3. Terminal Reaction Force
    h1_term = h1_traj[-1]
    pk_term = pk_traj[-1]
    term_diff_pct = abs(pk_term["rf1"] - h1_term["rf1"]) / h1_term["rf1"] * 100.0
    
    print(f"\n--- 3. TERMINAL REACTION FORCE (U1 = 0.050 mm) ---")
    print(f"H1 Reference Terminal: {h1_term['rf1']:.6f} kN at U1 = {h1_term['u1']:.6f} mm")
    print(f"PK10R2 Actual Terminal:{pk_term['rf1']:.6f} kN at U1 = {pk_term['u1']:.6f} mm")
    print(f"Relative Difference:   {term_diff_pct:.4f}%")
    
    # 4. Sample Points along Trajectory
    print(f"\n--- 4. TRAJECTORY SAMPLING ALONG SHEAR DISPLACEMENT ---")
    print(f"{'U1 (mm)':<12} | {'H1 RF1 (kN)':<14} | {'PK10R2 RF1 (kN)':<16} | {'Diff (%)':<10}")
    print("-" * 60)
    for target_u in [0.0001, 0.0005, 0.001, 0.005, 0.010, 0.020, 0.030, 0.040, 0.050]:
        h_pt = min(h1_traj, key=lambda r: abs(r["u1"] - target_u))
        p_pt = min(pk_traj, key=lambda r: abs(r["u1"] - target_u))
        diff = abs(p_pt["rf1"] - h_pt["rf1"]) / h_pt["rf1"] * 100.0 if h_pt["rf1"] != 0 else 0.0
        print(f"{target_u:<12.4f} | {h_pt['rf1']:<14.6f} | {p_pt['rf1']:<16.6f} | {diff:<10.2f}%")

if __name__ == "__main__":
    main()

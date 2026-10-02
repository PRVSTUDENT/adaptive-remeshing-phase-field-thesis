#!/usr/bin/env python3
"""
Accurately parse all increments and extract max SDV13 (H) and max SDV14 (d) across all elements.
"""

import sys
import os
import re

def scan_dat_max(dat_path):
    print("Scanning %s ..." % dat_path)
    inc_summary = {}
    current_inc = 0
    current_time = 0.0
    
    max_h_inc = 0.0
    max_d_inc = 0.0
    max_h_elem = 0
    max_d_elem = 0
    
    with open(dat_path, 'r') as f:
        for line in f:
            if "INCREMENT" in line and "SUMMARY" not in line:
                # Store previous inc if exists
                if current_inc > 0:
                    inc_summary[current_inc] = {
                        "time": current_time,
                        "max_H": max_h_inc,
                        "max_d": max_d_inc,
                        "max_H_elem": max_h_elem,
                        "max_d_elem": max_d_elem
                    }
                m = re.search(r"INCREMENT\s+(\d+)", line)
                if m:
                    current_inc = int(m.group(1))
                    max_h_inc = 0.0
                    max_d_inc = 0.0
                    max_h_elem = 0
                    max_d_elem = 0
            elif "STEP TIME COMPLETED" in line:
                m = re.search(r"STEP TIME COMPLETED\s+([\d\.E\+\-]+)", line)
                if m:
                    current_time = float(m.group(1))
            else:
                parts = line.split()
                if len(parts) >= 6:
                    try:
                        elem = int(parts[0])
                        pt = int(parts[1])
                        s13 = float(parts[2])
                        s14 = float(parts[3])
                        if s13 > max_h_inc:
                            max_h_inc = s13
                            max_h_elem = elem
                        if s14 > max_d_inc:
                            max_d_inc = s14
                            max_d_elem = elem
                    except ValueError:
                        pass
                        
        if current_inc > 0:
            inc_summary[current_inc] = {
                "time": current_time,
                "max_H": max_h_inc,
                "max_d": max_d_inc,
                "max_H_elem": max_h_elem,
                "max_d_elem": max_d_elem
            }
            
    return inc_summary

if __name__ == "__main__":
    p_r3 = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R3_REFINED_TIP/M2CORR_PK10R3_REFINED_TIP.dat"
    if not os.path.exists(p_r3):
        p_r3 = "D:/Master thesis/Adaptive remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R3_REFINED_TIP/M2CORR_PK10R3_REFINED_TIP.dat"
        
    s3 = scan_dat_max(p_r3)
    print("Found %d increments in PK10R3" % len(s3))
    
    targets = [0.005, 0.010, 0.0125, 0.020, 0.035, 0.050]
    print("\n--- PK10R3 REFINED TIP (1390098) FIELD EVOLUTION ---")
    for td in targets:
        best_inc = min(s3.keys(), key=lambda k: abs(s3[k]["time"] - td))
        d = s3[best_inc]
        print("U1 = %.4f mm | Inc %3d (t = %.6f) | max(H) = %.6f kN/mm^2 (elem %d) | max(d) = %.6f (elem %d)" % (
            td, best_inc, d["time"], d["max_H"], d["max_H_elem"], d["max_d"], d["max_d_elem"]))
            
    p_r2 = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R2_TOPOLOGY_CORRECTED/M2CORR_PK10R2_TOPOLOGY_CORRECTED.dat"
    if not os.path.exists(p_r2):
        p_r2 = "D:/Master thesis/Adaptive remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R2_TOPOLOGY_CORRECTED/M2CORR_PK10R2_TOPOLOGY_CORRECTED.dat"
    s2 = scan_dat_max(p_r2)
    print("\n--- PK10R2 (1390056) FIELD EVOLUTION ---")
    for td in targets:
        best_inc = min(s2.keys(), key=lambda k: abs(s2[k]["time"] - td))
        d = s2[best_inc]
        print("U1 = %.4f mm | Inc %3d (t = %.6f) | max(H) = %.6f kN/mm^2 (elem %d) | max(d) = %.6f (elem %d)" % (
            td, best_inc, d["time"], d["max_H"], d["max_H_elem"], d["max_d"], d["max_d_elem"]))

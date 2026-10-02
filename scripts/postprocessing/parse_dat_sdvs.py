#!/usr/bin/env python3
"""
Parse SDV field history from Abaqus .dat file for PK10R3 and PK10R2.
"""

import os
import re

def parse_dat_sdvs(dat_path):
    print("Parsing: %s" % dat_path)
    if not os.path.exists(dat_path):
        print("Error: %s does not exist" % dat_path)
        return {}
        
    inc_data = {}
    current_inc = None
    current_time = None
    
    with open(dat_path, 'r') as f:
        reading_sdv = False
        
        for line in f:
            line_str = line.strip()
            
            # Increment header
            if "INCREMENT" in line_str and "SUMMARY" not in line_str:
                m = re.search(r"INCREMENT\s+(\d+)", line_str)
                if m:
                    current_inc = int(m.group(1))
                    if current_inc not in inc_data:
                        inc_data[current_inc] = {
                            "time": 0.0,
                            "max_sdv13": 0.0,
                            "max_sdv14": 0.0,
                            "max_sdv15": 0.0,
                            "max_sdv16": 0.0
                        }
            
            if "STEP TIME COMPLETED" in line_str:
                m = re.search(r"STEP TIME COMPLETED\s+([\d\.E\+\-]+)", line_str)
                if m and current_inc is not None:
                    current_time = float(m.group(1))
                    inc_data[current_inc]["time"] = current_time
                    
            if "ELEMENT  PT" in line_str and ("SDV13" in line_str or "SDV" in line_str):
                reading_sdv = True
                continue
                
            if reading_sdv:
                if line_str == "" or "MAXIMUM" in line_str or "MINIMUM" in line_str:
                    if line_str == "":
                        reading_sdv = False
                    continue
                    
                parts = line_str.split()
                if len(parts) >= 6:
                    try:
                        elem = int(parts[0])
                        pt = int(parts[1])
                        s13 = float(parts[2])
                        s14 = float(parts[3])
                        s15 = float(parts[4])
                        s16 = float(parts[5])
                        
                        if s13 > inc_data[current_inc]["max_sdv13"]:
                            inc_data[current_inc]["max_sdv13"] = s13
                        if s14 > inc_data[current_inc]["max_sdv14"]:
                            inc_data[current_inc]["max_sdv14"] = s14
                        if s15 > inc_data[current_inc]["max_sdv15"]:
                            inc_data[current_inc]["max_sdv15"] = s15
                        if s16 > inc_data[current_inc]["max_sdv16"]:
                            inc_data[current_inc]["max_sdv16"] = s16
                    except ValueError:
                        pass
                        
    return inc_data

if __name__ == "__main__":
    p_r3 = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R3_REFINED_TIP/M2CORR_PK10R3_REFINED_TIP.dat"
    p_r2 = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R2_TOPOLOGY_CORRECTED/M2CORR_PK10R2_TOPOLOGY_CORRECTED.dat"
    
    r3_data = parse_dat_sdvs(p_r3)
    print("PK10R3 total increments parsed: %d" % len(r3_data))
    
    targets = [0.005, 0.010, 0.0125, 0.020, 0.035, 0.050]
    print("\n--- PK10R3 MATCHED DISPLACEMENT SDV SUMMARY ---")
    for td in targets:
        best_inc = min(r3_data.keys(), key=lambda k: abs(r3_data[k]["time"] - td))
        d = r3_data[best_inc]
        print("Target U1 = %.4f mm | Inc %3d (t = %.6f mm) | max(H/SDV13) = %.6f kN/mm^2 | max(d/SDV14) = %.6f" % (
            td, best_inc, d['time'], d['max_sdv13'], d['max_sdv14']))
        
    r2_data = parse_dat_sdvs(p_r2)
    print("\nPK10R2 total increments parsed: %d" % len(r2_data))
    print("\n--- PK10R2 MATCHED DISPLACEMENT SDV SUMMARY ---")
    for td in targets:
        best_inc = min(r2_data.keys(), key=lambda k: abs(r2_data[k]["time"] - td))
        d = r2_data[best_inc]
        print("Target U1 = %.4f mm | Inc %3d (t = %.6f mm) | max(H/SDV13) = %.6f kN/mm^2 | max(d/SDV14) = %.6f" % (
            td, best_inc, d['time'], d['max_sdv13'], d['max_sdv14']))

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Parse DAT file to extract true global extrema of SDV14 (d), SDV15 (degradation), SDV16 (H)
across all 8836 physical quad elements at all increments of Step 4.
"""

import os
import sys
import json
import re

ROOT = "/home/pr21vyci/projects/adaptive-remeshing"
if not os.path.exists(ROOT):
    ROOT = "D:/Master thesis/Adaptive remeshing"

dat_path = os.path.join(ROOT, "models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL.dat")

def parse_full_dat_sdv():
    print("Parsing full DAT file: %s" % dat_path)
    
    increment_extrema = []
    
    current_inc = 0
    current_time = 0.0
    
    in_element_table = False
    
    cur_inc_d_max = 0.0
    cur_inc_d_max_elem = None
    cur_inc_h_max = 0.0
    cur_inc_h_max_elem = None
    
    inc_re = re.compile(r"INCREMENT\s+(\d+)\s+SUMMARY")
    time_re = re.compile(r"STEP TIME COMPLETED\s+([\d\.E\+\-]+)")
    elem_header_re = re.compile(r"ELEMENT\s+PT\s+FOOT-")
    
    with open(dat_path, 'r') as f:
        for line_num, line in enumerate(f):
            if "INCREMENT" in line and "SUMMARY" in line:
                m = inc_re.search(line)
                if m:
                    # Save previous increment if exists
                    if current_inc > 0:
                        increment_extrema.append({
                            "increment": current_inc,
                            "step_time": current_time,
                            "d_max": cur_inc_d_max,
                            "d_max_elem": cur_inc_d_max_elem,
                            "h_max": cur_inc_h_max,
                            "h_max_elem": cur_inc_h_max_elem
                        })
                    current_inc = int(m.group(1))
                    cur_inc_d_max = 0.0
                    cur_inc_d_max_elem = None
                    cur_inc_h_max = 0.0
                    cur_inc_h_max_elem = None
                    in_element_table = False
                    
            if "STEP TIME COMPLETED" in line:
                m_t = time_re.search(line)
                if m_t:
                    current_time = float(m_t.group(1))
                    
            if "ELEMENT  PT FOOT-" in line:
                in_element_table = True
                continue
                
            if in_element_table:
                parts = line.split()
                if len(parts) >= 4:
                    try:
                        elem_id = int(parts[0])
                        # Mechanical element IDs are 8837..17672
                        if 8837 <= elem_id <= 17672:
                            sdv14 = float(parts[2]) # d_avg
                            sdv16 = float(parts[4]) if len(parts) >= 5 else 0.0 # HIST
                            if sdv14 > cur_inc_d_max:
                                cur_inc_d_max = sdv14
                                cur_inc_d_max_elem = elem_id
                            if sdv16 > cur_inc_h_max:
                                cur_inc_h_max = sdv16
                                cur_inc_h_max_elem = elem_id
                    except ValueError:
                        # End of table
                        if "THE TOTAL FORCE" in line or "NODE OUTPUT" in line:
                            in_element_table = False
                            
    # Append last
    if current_inc > 0:
        increment_extrema.append({
            "increment": current_inc,
            "step_time": current_time,
            "d_max": cur_inc_d_max,
            "d_max_elem": cur_inc_d_max_elem,
            "h_max": cur_inc_h_max,
            "h_max_elem": cur_inc_h_max_elem
        })
        
    print("\nParsed %d increments from Step 4." % len(increment_extrema))
    print("\n--- SAMPLE EXTRACTED INCREMENTS ---")
    print("%-8s %-14s %-14s %-12s %-14s %-12s" % ("Inc", "Step Time", "d_max", "Elem", "H_max", "Elem"))
    print("-" * 76)
    for res in increment_extrema[:10] + increment_extrema[::25] + [increment_extrema[-1]]:
        print("%-8d %-14.6f %-14.6f %-12d %-14.6f %-12d" % (
            res["increment"], res["step_time"], res["d_max"], res["d_max_elem"] if res["d_max_elem"] else 0,
            res["h_max"], res["h_max_elem"] if res["h_max_elem"] else 0))
            
    out_json = os.path.join(ROOT, "docs/studies/stage_d_dat_sdv_extrema.json")
    with open(out_json, "w") as fp:
        json.dump(increment_extrema, fp, indent=2)
    print("\nSaved full extrema history to %s" % out_json)

if __name__ == "__main__":
    parse_full_dat_sdv()

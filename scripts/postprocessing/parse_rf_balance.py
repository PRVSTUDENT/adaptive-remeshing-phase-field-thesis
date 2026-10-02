#!/usr/bin/env python3
"""
Reaction force balance parser from DAT file.
Sums RF1 across N_BOTTOM and N_TOP across all increments.
"""
import sys
import os
import re

def parse_rf_balance(dat_path, inp_path):
    # 1. Parse N_BOTTOM and N_TOP node sets from inp
    n_bottom = set()
    n_top = set()
    with open(inp_path, "r") as f:
        in_set = None
        for line in f:
            line_s = line.strip()
            if line_s.startswith("*NSET"):
                if "NSET=N_BOTTOM" in line_s: in_set = "BOTTOM"
                elif "NSET=N_TOP" in line_s: in_set = "TOP"
                else: in_set = None
                continue
            if line_s.startswith("*"):
                in_set = None
                continue
            if in_set == "BOTTOM" and line_s:
                n_bottom.update([int(p.strip()) for p in line_s.split(",") if p.strip()])
            elif in_set == "TOP" and line_s:
                n_top.update([int(p.strip()) for p in line_s.split(",") if p.strip()])
                
    print("N_BOTTOM: %d nodes, N_TOP: %d nodes" % (len(n_bottom), len(n_top)))
    
    # 2. Parse DAT file for tables of U, RF
    with open(dat_path, "r") as f:
        lines = f.readlines()
        
    print("Total lines in DAT: %d" % len(lines))
    
    # Extract framewise RF sums
    current_step = None
    current_inc = None
    current_time = None
    
    # We will accumulate RF1 for bottom and top per (step, inc)
    step_inc_rf = {} # (step, inc) -> {'time': t, 'bottom_rf1': sum, 'top_rf1': sum, 'rp_rf1': val}
    
    i = 0
    in_table = False
    while i < len(lines):
        line = lines[i]
        if "STEP " in line and "INCREMENT" in line:
            m = re.search(r"STEP\s+(\d+)\s+INCREMENT\s+(\d+)", line)
            if m:
                current_step = int(m.group(1))
                current_inc = int(m.group(2))
        if "STEP TIME COMPLETED" in line:
            m = re.search(r"STEP TIME COMPLETED\s+([0-9.E+-]+)", line)
            if m:
                current_time = float(m.group(1))
                key = (current_step, current_inc, current_time)
                if key not in step_inc_rf:
                    step_inc_rf[key] = {"bottom_rf1": 0.0, "top_rf1": 0.0, "rp_rf1": 0.0}
                    
        tokens = line.strip().split()
        if len(tokens) >= 3 and tokens[0].isdigit():
            nid = int(tokens[0])
            # Check if RF1 is present (column 4 or 3)
            # Table columns: NODE FOOT- NOTE U1 U2 RF1 RF2
            try:
                if len(tokens) == 5:
                    u1 = float(tokens[1])
                    u2 = float(tokens[2])
                    rf1 = float(tokens[3])
                    rf2 = float(tokens[4])
                elif len(tokens) == 6:
                    u1 = float(tokens[2])
                    u2 = float(tokens[3])
                    rf1 = float(tokens[4])
                    rf2 = float(tokens[5])
                else:
                    rf1 = 0.0
                    
                key = (current_step, current_inc, current_time)
                if key in step_inc_rf:
                    if nid in n_bottom:
                        step_inc_rf[key]["bottom_rf1"] += rf1
                    if nid in n_top:
                        step_inc_rf[key]["top_rf1"] += rf1
                    if nid == 99999:
                        step_inc_rf[key]["rp_rf1"] = rf1
            except:
                pass
                
        i += 1
        
    print("\n--- REACTION FORCE HISTORY ACROSS ACCEPTED STATES ---")
    for (s, inc, t), data in sorted(step_inc_rf.items()):
        print("Step %s Inc %s (t=%.4e): RP RF1 = %.6e, N_BOTTOM RF1 = %.6e, N_TOP RF1 = %.6e" % (
            s, inc, t if t is not None else 0.0, data["rp_rf1"], data["bottom_rf1"], data["top_rf1"]
        ))

if __name__ == "__main__":
    parse_rf_balance("M2STATE_FRACFIX_RESTART2R6.dat", "M2STATE_FRACFIX_RESTART2R6.inp")

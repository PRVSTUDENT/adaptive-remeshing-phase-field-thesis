#!/usr/bin/env python3
"""
Reaction force parser from M2STATE_FRACFIX_RESTART2R6.dat.
"""
import sys
import os
import re

def parse_rf(dat_path):
    with open(dat_path, "r") as f:
        lines = f.readlines()
        
    print("Total lines in DAT: %d" % len(lines))
    
    current_step = None
    current_inc = None
    current_time = None
    
    rf_records = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        if "STEP" in line and "INCREMENT" in line:
            m = re.search(r"STEP\s+(\d+)\s+INCREMENT\s+(\d+)", line)
            if m:
                current_step = int(m.group(1))
                current_inc = int(m.group(2))
        if "STEP TIME COMPLETED" in line:
            m = re.search(r"STEP TIME COMPLETED\s+([0-9.E+-]+)", line)
            if m:
                current_time = float(m.group(1))
                
        if "THE FOLLOWING TABLE IS PRINTED FOR NODES BELONGING TO NODE SET" in line or "N O D E   O U T P U T" in line:
            # Look ahead for node 99999 or sum of bottom nodes
            pass
            
        if "99999" in line:
            # Check if line contains U and RF
            tokens = line.strip().split()
            if tokens and tokens[0] == "99999":
                rf_records.append((current_step, current_inc, current_time, line.strip()))
                
        i += 1
        
    print("\n--- RP (NODE 99999) PRINTOUTS IN DAT FILE ---")
    for r in rf_records:
        print("Step %s Inc %s (t=%s): %s" % (r[0], r[1], r[2], r[3]))

if __name__ == "__main__":
    dat_p = "runs/hpc/mode_ii_state_transfer/evidence/1389226.mmaster02/M2STATE_FRACFIX_RESTART2R6.dat"
    if not os.path.exists(dat_p):
        dat_p = "M2STATE_FRACFIX_RESTART2R6.dat"
    parse_rf(dat_p)

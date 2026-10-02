#!/usr/bin/env python3
"""
Inspect tables and printouts in M2STATE_FRACFIX_RESTART2R6.dat.
"""
import os
import sys

def parse_dat(dat_path):
    with open(dat_path, "r", errors="ignore") as f:
        lines = f.readlines()
        
    print(f"Total lines in dat: {len(lines)}")
    
    # Search for key sections
    for i, line in enumerate(lines):
        if "INCREMENT" in line or "STEP " in line or "NODE TABLE" in line or "N O D E   O U T P U T" in line or "TABLE IS PRINTED" in line:
            print(f"{i+1:7d}: {line.strip()}")

if __name__ == "__main__":
    p = sys.argv[1] if len(sys.argv) > 1 else "runs/hpc/mode_ii_state_transfer/evidence/1389226.mmaster02/M2STATE_FRACFIX_RESTART2R6.dat"
    parse_dat(p)

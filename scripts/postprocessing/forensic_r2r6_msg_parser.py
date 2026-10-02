#!/usr/bin/env python3
"""
Deep Abaqus MSG parser for Step 2 Increment 5 attempts.
Extracts:
- Attempt start, dt, start time, target time
- Equilibrium iteration sequence
- Severe discontinuity / equilibrium iterations
- Residuals (force, flux, displacement, phase)
- Largest residual force and node/element
- Largest displacement / phase correction and node
- Convergence check messages and reason for cutback
"""
import os
import sys
import re
import json

def parse_abaqus_msg(msg_path):
    with open(msg_path, "r", errors="ignore") as f:
        lines = f.readlines()
        
    print(f"Total lines: {len(lines)}")
    
    # We want Step 2 Increments 1-5
    # Let's find all lines where Abaqus prints iteration information
    # Filter out [STATE_TRACE], [H_STARTUP_TRACE], [FORCE_TRACE], etc.
    
    clean_lines = []
    for idx, line in enumerate(lines):
        # Exclude UEL diagnostic lines to see solver convergence tables
        if line.startswith("[") or "PHYS=" in line or "STATE_TRACE" in line or "H_STARTUP_TRACE" in line or "FORCE_TRACE" in line:
            continue
        clean_lines.append((idx + 1, line))
        
    print(f"Total clean Abaqus solver lines: {len(clean_lines)}")
    
    # Save clean lines to a file for easy inspection
    with open("M2STATE_FRACFIX_RESTART2R6_clean_solver.msg", "w") as out:
        for lnum, line in clean_lines:
            out.write(f"{lnum:7d}: {line}")
            
    print("Clean solver message file written: M2STATE_FRACFIX_RESTART2R6_clean_solver.msg")
    
    # Let's inspect Step 2 Increment 5 in clean lines
    inc5_clean = []
    recording = False
    for lnum, line in clean_lines:
        if "INCREMENT     5 STARTS" in line:
            recording = True
        if recording:
            inc5_clean.append((lnum, line))
            
    print(f"Total clean solver lines in Step 2 Inc 5: {len(inc5_clean)}")
    for lnum, line in inc5_clean:
        print(f"{lnum:7d}: {line.rstrip()}")

if __name__ == "__main__":
    msg_path = sys.argv[1] if len(sys.argv) > 1 else "M2STATE_FRACFIX_RESTART2R6.msg"
    parse_abaqus_msg(msg_path)

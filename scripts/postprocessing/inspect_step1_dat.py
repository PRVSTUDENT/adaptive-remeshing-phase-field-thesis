#!/usr/bin/env python3
"""
Inspect exact Step 1 printed tables in M2STATE_FRACFIX_RESTART2R5.dat.
"""
from pathlib import Path

def inspect_step1_dat():
    root = Path(__file__).resolve().parent.parent.parent
    dat_path = root / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R5/M2STATE_FRACFIX_RESTART2R5.dat"
    
    with open(dat_path, "r", errors="ignore") as f:
        lines = f.readlines()
        
    print(f"Total lines in dat: {len(lines)}")
    
    # Find STEP 1 summary and table
    step1_idx = None
    step2_idx = None
    for i, line in enumerate(lines):
        if "STEP 1" in line and "INCREMENT" in line:
            step1_idx = i
        elif "STEP 2" in line and "INCREMENT" in line and step2_idx is None:
            step2_idx = i
            
    print(f"Step 1 found at line {step1_idx}, Step 2 found at line {step2_idx}")
    
    if step1_idx:
        print("\n--- STEP 1 TABLE (Lines %d..%d) ---" % (step1_idx, min(step1_idx + 100, len(lines))))
        for l in lines[step1_idx:step1_idx + 100]:
            print(l.rstrip())

if __name__ == "__main__":
    inspect_step1_dat()

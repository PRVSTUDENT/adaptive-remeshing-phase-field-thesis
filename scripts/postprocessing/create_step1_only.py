#!/usr/bin/env python3
"""
Diagnostic run of M2STATE_FRACFIX_RESTART2R5 Step 1 to pinpoint exact difference.
"""
from pathlib import Path

def diagnose_step1():
    root = Path(__file__).resolve().parent.parent.parent
    base_dir = root / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R5"
    inp_path = base_dir / "M2STATE_FRACFIX_RESTART2R5.inp"
    
    with open(inp_path, "r", errors="ignore") as f:
        lines = f.readlines()
        
    # Cut after Step 1
    step1_lines = []
    in_step2 = False
    for line in lines:
        if "*STEP, NAME=Step-2-Continuation" in line:
            in_step2 = True
            break
        step1_lines.append(line)
        
    out_path = Path("/home/pr21vyci/test_r2r5_step1_only.inp")
    print(f"Total Step 1 lines: {len(step1_lines)}")

if __name__ == "__main__":
    diagnose_step1()

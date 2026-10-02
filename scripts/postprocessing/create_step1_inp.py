#!/usr/bin/env python3
from pathlib import Path

def create_step1_inp():
    inp_path = Path("/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R5/M2STATE_FRACFIX_RESTART2R5.inp")
    
    with open(inp_path, "r", errors="ignore") as f:
        lines = f.readlines()
        
    step1_lines = []
    for line in lines:
        if "*STEP, NAME=Step-2-Continuation" in line:
            break
        step1_lines.append(line)
        
    with open("/home/pr21vyci/test_r2r5_step1.inp", "w") as f:
        f.writelines(step1_lines)
        
    print(f"Created /home/pr21vyci/test_r2r5_step1.inp with {len(step1_lines)} lines")

if __name__ == "__main__":
    create_step1_inp()

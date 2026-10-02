#!/usr/bin/env python3
"""
Inspect Boundary Conditions across R2R13 and R2R14
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
INP_R2R13 = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R13/M2STATE_FRACFIX_RESTART2R13.inp"
INP_R2R14 = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R14/M2STATE_FRACFIX_RESTART2R14.inp"

def inspect_bcs(inp_path, title):
    print(f"\n=== BOUNDARY CONDITIONS IN {title} ({inp_path.name}) ===")
    lines = inp_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    in_step = False
    step_num = 0
    in_bc = False
    
    for l in lines:
        if l.upper().startswith("*STEP"):
            in_step = True
            step_num += 1
            print(f"\n--- STEP {step_num} ---")
        elif l.upper().startswith("*END STEP"):
            in_step = False
        elif l.upper().startswith("*BOUNDARY"):
            in_bc = True
            print(f"  {l}")
        elif in_bc and l.startswith("*"):
            in_bc = False
        elif in_bc:
            # print first 5 lines of BCs
            print(f"    {l}")

if __name__ == '__main__':
    inspect_bcs(INP_R2R13, "R2R13")
    inspect_bcs(INP_R2R14, "R2R14")

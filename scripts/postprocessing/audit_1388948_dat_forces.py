import re
import json
from pathlib import Path

p_dat = Path("runs/hpc/mode_ii_state_transfer/1388948.mmaster02/M2STATE_FRACFIX_RESTART1R1R6R2.dat")
step_inc_re = re.compile(r"^\s*STEP\s+(\d+)\s+INCREMENT\s+(\d+)", re.IGNORECASE)
inc_summary_re = re.compile(r"^\s*INCREMENT\s+(\d+)\s+SUMMARY", re.IGNORECASE)

def audit_1388948():
    with open(p_dat, "r", errors="ignore") as f:
        lines = f.readlines()
        
    print("Total lines in 1388948 DAT:", len(lines))
    in_table = False
    step2_inc13_table = []
    
    current_step = 0
    current_inc = 0
    for line in lines:
        m1 = step_inc_re.match(line)
        if m1:
            current_step = int(m1.group(1))
            current_inc = int(m1.group(2))
        m2 = inc_summary_re.match(line)
        if m2:
            current_inc = int(m2.group(1))
            
        if current_step == 2 and current_inc == 13:
            if "THE FOLLOWING TABLE IS PRINTED FOR ALL NODES" in line:
                in_table = True
                continue
            if in_table:
                if "MAXIMUM" in line or "MINIMUM" in line or "TOTAL" in line:
                    in_table = False
                else:
                    step2_inc13_table.append(line.rstrip())
                    
    print(f"Step 2 Inc 13 lines: {len(step2_inc13_table)}")
    for l in step2_inc13_table[:10]:
        print("  ", l)
    for l in step2_inc13_table[-10:]:
        print("  ", l)

if __name__ == "__main__":
    audit_1388948()

import re
import json
from pathlib import Path

DAT_PATH = Path("runs/hpc/mode_ii_state_transfer/evidence/1389229.mmaster02/M2STATE_FRACFIX_RESTART2R7.dat")
step_inc_re = re.compile(r"^\s*STEP\s+(\d+)\s+INCREMENT\s+(\d+)", re.IGNORECASE)

def parse_u3():
    with open(DAT_PATH, "r", errors="ignore") as f:
        lines = f.readlines()
        
    step1_u3 = {}
    step2_final_u3 = {}
    
    current_step = 1
    current_inc = 1
    in_table = False
    
    current_table = {}
    
    for line in lines:
        m = step_inc_re.match(line)
        if m:
            current_step = int(m.group(1))
            current_inc = int(m.group(2))
            
        if "THE FOLLOWING TABLE IS PRINTED FOR ALL NODES" in line:
            in_table = True
            current_table = {}
            continue
            
        if "MAXIMUM" in line or "MINIMUM" in line or "TOTAL" in line:
            if in_table:
                in_table = False
                if current_step == 1 and current_inc == 1:
                    step1_u3 = dict(current_table)
                if current_step == 2 and current_inc == 513:
                    step2_final_u3 = dict(current_table)
            continue
            
        if in_table:
            parts = line.split()
            if len(parts) >= 5 and parts[0].isdigit():
                nid = int(parts[0])
                if 1 <= nid <= 9801:
                    try:
                        if len(parts) == 8: # NODE footnote U1 U2 U3 RF1 RF2 RF3
                            u3 = float(parts[4])
                        elif len(parts) == 7: # NODE U1 U2 U3 RF1 RF2 RF3
                            u3 = float(parts[3])
                        else:
                            u3 = float(parts[3])
                        current_table[nid] = u3
                    except (ValueError, IndexError):
                        pass

    print(f"Step 1 physical nodes with U3: {len(step1_u3)}")
    if step1_u3:
        u3_vals = list(step1_u3.values())
        print(f"Step 1 U3 min={min(u3_vals):.6f}, max={max(u3_vals):.6f}, mean={sum(u3_vals)/len(u3_vals):.6f}")
        print(f"Step 1 nodes with U3 > 0.05: {sum(1 for u in u3_vals if u > 0.05)}")
        print(f"Step 1 nodes with U3 > 0.10: {sum(1 for u in u3_vals if u > 0.10)}")
        
    print(f"Step 2 Final physical nodes with U3: {len(step2_final_u3)}")
    if step2_final_u3:
        u3_vals2 = list(step2_final_u3.values())
        print(f"Step 2 Final U3 min={min(u3_vals2):.6f}, max={max(u3_vals2):.6f}, mean={sum(u3_vals2)/len(u3_vals2):.6f}")
        print(f"Step 2 Final nodes with U3 > 0.05: {sum(1 for u in u3_vals2 if u > 0.05)}")
        print(f"Step 2 Final nodes with U3 > 0.10: {sum(1 for u in u3_vals2 if u > 0.10)}")

if __name__ == "__main__":
    parse_u3()

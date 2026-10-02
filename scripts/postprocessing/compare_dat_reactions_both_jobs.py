import re
import json
from pathlib import Path

step_inc_re = re.compile(r"^\s*STEP\s+(\d+)\s+INCREMENT\s+(\d+)", re.IGNORECASE)

def parse_dat_file(dat_path, bottom_range, top_range):
    with open(dat_path, "r", errors="ignore") as f:
        lines = f.readlines()
        
    records = []
    current_step = 1
    current_inc = 1
    in_table = False
    
    rf1_bottom_sum = 0.0
    rf2_bottom_sum = 0.0
    top_u1_list = []
    rp_u1 = None
    rp_rf1 = None
    
    for line in lines:
        m = step_inc_re.match(line)
        if m:
            current_step = int(m.group(1))
            current_inc = int(m.group(2))
            
        if "THE FOLLOWING TABLE IS PRINTED FOR ALL NODES" in line:
            in_table = True
            rf1_bottom_sum = 0.0
            rf2_bottom_sum = 0.0
            top_u1_list = []
            rp_u1 = None
            rp_rf1 = None
            continue
            
        if "MAXIMUM" in line or "MINIMUM" in line or "TOTAL" in line:
            if in_table:
                in_table = False
                u1_top = (sum(top_u1_list) / len(top_u1_list)) if top_u1_list else (rp_u1 if rp_u1 is not None else 0.0)
                records.append({
                    "step": current_step,
                    "increment": current_inc,
                    "rf1_bottom_total": -rf1_bottom_sum,
                    "rf2_bottom_total": -rf2_bottom_sum,
                    "u1_top_avg": u1_top,
                    "rp_u1": rp_u1,
                    "rp_rf1": rp_rf1
                })
            continue
            
        if in_table:
            parts = line.split()
            if len(parts) >= 6 and parts[0].isdigit():
                nid = int(parts[0])
                if bottom_range[0] <= nid <= bottom_range[1]:
                    try:
                        if len(parts) == 8:
                            rf1 = float(parts[5])
                            rf2 = float(parts[6])
                        elif len(parts) == 7:
                            rf1 = float(parts[4])
                            rf2 = float(parts[5])
                        else:
                            rf1 = float(parts[-3])
                            rf2 = float(parts[-2])
                        rf1_bottom_sum += rf1
                        rf2_bottom_sum += rf2
                    except (ValueError, IndexError):
                        pass
                if top_range[0] <= nid <= top_range[1]:
                    try:
                        if len(parts) == 8:
                            u1 = float(parts[2])
                        elif len(parts) == 7:
                            u1 = float(parts[1])
                        else:
                            u1 = float(parts[1])
                        top_u1_list.append(u1)
                    except (ValueError, IndexError):
                        pass
                if nid == 99999:
                    try:
                        if len(parts) == 8:
                            rp_u1 = float(parts[2])
                            rp_rf1 = float(parts[5])
                        elif len(parts) == 7:
                            rp_u1 = float(parts[1])
                            rp_rf1 = float(parts[4])
                        else:
                            rp_u1 = float(parts[1])
                            rp_rf1 = float(parts[-3])
                    except (ValueError, IndexError):
                        pass

    return records

def main():
    root = Path(__file__).resolve().parent.parent.parent
    
    # 1388948 (Restart1)
    dat_1388948 = root / "runs/hpc/mode_ii_state_transfer/1388948.mmaster02/M2STATE_FRACFIX_RESTART1R1R6R2.dat"
    # 1389229 (Restart2)
    dat_1389229 = root / "runs/hpc/mode_ii_state_transfer/evidence/1389229.mmaster02/M2STATE_FRACFIX_RESTART2R7.dat"
    
    # In 1388948 (4998 physical nodes, mesh 49x99 or similar):
    # Let's inspect bottom node set and top node set in 1388948 inp
    rec1 = parse_dat_file(dat_1388948, (1, 60), (4939, 4998))
    print(f"Parsed {len(rec1)} increments from 1388948 DAT.")
    for r in rec1:
        print(f"  1388948 Step {r['step']} Inc {r['increment']}: U1={r['u1_top_avg']:.6f}, RF1_bottom={r['rf1_bottom_total']:.6f}, RP_RF1={r['rp_rf1']}")
        
    print("\n" + "="*50 + "\n")
    
    # In 1389229 (9801 physical nodes):
    rec2 = parse_dat_file(dat_1389229, (1, 120), (9721, 9801))
    print(f"Parsed {len(rec2)} increments from 1389229 DAT.")
    print("Sample 1389229 increments:")
    for i in [0, 1, 13, 20, 50, 100, 200, 300, 400, 500, -1]:
        if i < len(rec2):
            r = rec2[i]
            print(f"  1389229 Step {r['step']} Inc {r['increment']}: U1={r['u1_top_avg']:.6f}, RF1_bottom={r['rf1_bottom_total']:.6f}")

if __name__ == "__main__":
    main()

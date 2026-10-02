import re
import json
from pathlib import Path

DAT_PATH = Path("runs/hpc/mode_ii_state_transfer/evidence/1389229.mmaster02/M2STATE_FRACFIX_RESTART2R7.dat")
step_inc_re = re.compile(r"^\s*STEP\s+(\d+)\s+INCREMENT\s+(\d+)", re.IGNORECASE)
inc_summary_re = re.compile(r"^\s*INCREMENT\s+(\d+)\s+SUMMARY", re.IGNORECASE)

def parse_all_frames():
    with open(DAT_PATH, "r", errors="ignore") as f:
        lines = f.readlines()
        
    frames = []
    
    current_step = 1
    current_inc = 1
    in_table = False
    
    current_u3 = {}
    current_rf1_bottom = 0.0
    current_u1_top = []
    
    for line in lines:
        m1 = step_inc_re.match(line)
        if m1:
            current_step = int(m1.group(1))
            current_inc = int(m1.group(2))
            
        m2 = inc_summary_re.match(line)
        if m2:
            current_inc = int(m2.group(1))
                    
        if "THE FOLLOWING TABLE IS PRINTED FOR ALL NODES" in line:
            in_table = True
            current_u3 = {}
            current_rf1_bottom = 0.0
            current_u1_top = []
            continue
            
        if "MAXIMUM" in line or "MINIMUM" in line or "TOTAL" in line:
            if in_table:
                in_table = False
                u3_vals = list(current_u3.values())
                d_max = max(u3_vals) if u3_vals else 0.0
                d_min = min(u3_vals) if u3_vals else 0.0
                d_mean = sum(u3_vals)/len(u3_vals) if u3_vals else 0.0
                d_gt01 = sum(1 for d in u3_vals if d > 0.1)
                d_gt05 = sum(1 for d in u3_vals if d > 0.5)
                d_gt09 = sum(1 for d in u3_vals if d > 0.9)
                
                d_max_node = None
                for nid, d in current_u3.items():
                    if d == d_max:
                        d_max_node = nid
                        break
                        
                u1_top_avg = sum(current_u1_top)/len(current_u1_top) if current_u1_top else 0.0
                
                frames.append({
                    "step": current_step,
                    "increment": current_inc,
                    "u1_top_avg": u1_top_avg,
                    "rf1_bottom_kN": -current_rf1_bottom,
                    "d_max": d_max,
                    "d_min": d_min,
                    "d_mean": d_mean,
                    "d_gt01_count": d_gt01,
                    "d_gt05_count": d_gt05,
                    "d_gt09_count": d_gt09,
                    "d_max_node": d_max_node
                })
            continue
            
        if in_table:
            parts = line.split()
            if len(parts) >= 5 and parts[0].isdigit():
                nid = int(parts[0])
                # N_BOTTOM: 1..120
                if 1 <= nid <= 120:
                    try:
                        if len(parts) == 8:
                            rf1 = float(parts[5])
                        elif len(parts) == 7:
                            rf1 = float(parts[4])
                        else:
                            rf1 = float(parts[-3])
                        current_rf1_bottom += rf1
                    except (ValueError, IndexError):
                        pass
                        
                # N_TOP: 9721..9801
                if 9721 <= nid <= 9801:
                    try:
                        if len(parts) == 8:
                            u1 = float(parts[2])
                        elif len(parts) == 7:
                            u1 = float(parts[1])
                        else:
                            u1 = float(parts[1])
                        current_u1_top.append(u1)
                    except (ValueError, IndexError):
                        pass
                        
                # Phase field U3 for physical nodes 1..9801
                if 1 <= nid <= 9801:
                    try:
                        if len(parts) == 8:
                            u3 = float(parts[4])
                        elif len(parts) == 7:
                            u3 = float(parts[3])
                        else:
                            u3 = float(parts[3])
                        current_u3[nid] = u3
                    except (ValueError, IndexError):
                        pass

    print(f"Extracted {len(frames)} total frames from DAT file.")
    if frames:
        f0 = frames[0]
        f_last = frames[-1]
        print(f"Step 1: U1={f0['u1_top_avg']:.6f} mm, RF1={f0['rf1_bottom_kN']:.6f} kN, dmax={f0['d_max']:.6f}, dmean={f0['d_mean']:.6f}, d>0.1={f0['d_gt01_count']}, d>0.5={f0['d_gt05_count']}, node={f0['d_max_node']}")
        print(f"Terminal: U1={f_last['u1_top_avg']:.6f} mm, RF1={f_last['rf1_bottom_kN']:.6f} kN, dmax={f_last['d_max']:.6f}, dmean={f_last['d_mean']:.6f}, d>0.1={f_last['d_gt01_count']}, d>0.5={f_last['d_gt05_count']}, node={f_last['d_max_node']}")
        
        rf1_list = [f['rf1_bottom_kN'] for f in frames]
        max_rf1 = max(rf1_list)
        max_idx = rf1_list.index(max_rf1)
        print(f"Peak RF1: {max_rf1:.6f} kN at U1 = {frames[max_idx]['u1_top_avg']:.6f} mm (Inc {frames[max_idx]['increment']})")
        
        dmax_list = [f['d_max'] for f in frames]
        max_d = max(dmax_list)
        max_d_idx = dmax_list.index(max_d)
        print(f"Peak d_max: {max_d:.6f} at U1 = {frames[max_d_idx]['u1_top_avg']:.6f} mm (Inc {frames[max_d_idx]['increment']})")
        
        with open("runs/hpc/mode_ii_state_transfer/evidence/1389229.mmaster02/COMPLETE_DAT_TRAJECTORY.json", "w") as f:
            json.dump(frames, f, indent=2)

if __name__ == "__main__":
    parse_all_frames()

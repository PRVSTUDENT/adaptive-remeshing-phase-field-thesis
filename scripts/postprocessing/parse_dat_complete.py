#!/usr/bin/env python3
"""
Complete DAT file table parser for:
- Frame by frame nodal U1, U2, U3 (phase field d)
- Reaction forces RF1, RF2, RF3 on N_BOTTOM and RP (node 99999)
- Exact d_min, d_max, d_mean, counts >0.1, >0.5, >0.9, location of d_max
- Framewise delta d, irreversibility checks
"""
import sys
import os
import re
import json

def parse_dat(dat_path, inp_path):
    # 1. Parse node sets and coordinates from inp
    nodes = {} # nid -> (x,y)
    n_bottom = set()
    n_top = set()
    with open(inp_path, "r") as f:
        in_nodes = False
        in_set = None
        for line in f:
            line_s = line.strip()
            if line_s.startswith("*NODE"):
                in_nodes = True
                continue
            if line_s.startswith("*NSET"):
                in_nodes = False
                if "NSET=N_BOTTOM" in line_s: in_set = "BOTTOM"
                elif "NSET=N_TOP" in line_s: in_set = "TOP"
                else: in_set = None
                continue
            if line_s.startswith("*"):
                in_nodes = False
                in_set = None
                continue
            if in_nodes and line_s:
                parts = [p.strip() for p in line_s.split(",")]
                if len(parts) >= 3:
                    nodes[int(parts[0])] = (float(parts[1]), float(parts[2]))
            elif in_set == "BOTTOM" and line_s:
                n_bottom.update([int(p.strip()) for p in line_s.split(",") if p.strip()])
            elif in_set == "TOP" and line_s:
                n_top.update([int(p.strip()) for p in line_s.split(",") if p.strip()])
                
    print("Parsed %d nodes, N_BOTTOM: %d nodes, N_TOP: %d nodes" % (len(nodes), len(n_bottom), len(n_top)))
    
    # 2. Parse DAT line by line
    with open(dat_path, "r") as f:
        lines = f.readlines()
        
    print("Total lines in DAT: %d" % len(lines))
    
    frames = [] # list of dicts
    current_frame = None
    
    current_step = None
    current_inc = None
    current_time = None
    
    in_table = False
    
    for i, line in enumerate(lines):
        if "STEP " in line and "INCREMENT" in line:
            m = re.search(r"STEP\s+(\d+)\s+INCREMENT\s+(\d+)", line)
            if m:
                current_step = int(m.group(1))
                current_inc = int(m.group(2))
        if "STEP TIME COMPLETED" in line:
            m = re.search(r"STEP TIME COMPLETED\s+([0-9.E+-]+)", line)
            if m:
                current_time = float(m.group(1))
                
        if "THE FOLLOWING TABLE IS PRINTED FOR ALL NODES" in line:
            in_table = True
            current_frame = {
                "step": current_step,
                "increment": current_inc,
                "step_time": current_time,
                "u1": {},
                "u2": {},
                "u3": {}, # phase d
                "rf1": {},
                "rf2": {},
                "rf3": {}
            }
            frames.append(current_frame)
            continue
            
        if in_table:
            # Check if table ended
            if line.startswith("1") or "JOB TIME SUMMARY" in line or "ANALYSIS SUMMARY" in line or "STEP " in line:
                in_table = False
                continue
            tokens = line.strip().split()
            if len(tokens) >= 7 and tokens[0].isdigit():
                try:
                    nid = int(tokens[0])
                    u1 = float(tokens[1])
                    u2 = float(tokens[2])
                    u3 = float(tokens[3])
                    rf1 = float(tokens[4])
                    rf2 = float(tokens[5])
                    rf3 = float(tokens[6])
                    current_frame["u1"][nid] = u1
                    current_frame["u2"][nid] = u2
                    current_frame["u3"][nid] = u3
                    current_frame["rf1"][nid] = rf1
                    current_frame["rf2"][nid] = rf2
                    current_frame["rf3"][nid] = rf3
                except:
                    pass
                    
    print("\nParsed %d accepted frame tables from DAT file" % len(frames))
    
    # Process frames
    processed_frames = []
    prev_d = None
    
    for f_idx, fr in enumerate(frames):
        s = fr["step"]
        inc = fr["increment"]
        t = fr["step_time"]
        
        # Nodal phase U3
        d_dict = fr["u3"]
        d_vals = list(d_dict.values())
        
        d_min = min(d_vals) if d_vals else 0.0
        d_max = max(d_vals) if d_vals else 0.0
        d_mean = (sum(d_vals)/float(len(d_vals))) if d_vals else 0.0
        d_gt_0p1 = sum(1 for v in d_vals if v > 0.1)
        d_gt_0p5 = sum(1 for v in d_vals if v > 0.5)
        d_gt_0p9 = sum(1 for v in d_vals if v > 0.9)
        
        # Find node with d_max
        max_nid = None
        for nid, val in d_dict.items():
            if val == d_max:
                max_nid = nid
                break
        max_coords = nodes.get(max_nid, (0.0, 0.0))
        
        # Irreversibility check
        max_neg_delta_d = 0.0
        irrev_violations = 0
        if prev_d is not None:
            for nid, val in d_dict.items():
                if nid in prev_d:
                    delta_d = val - prev_d[nid]
                    if delta_d < -1e-12:
                        irrev_violations += 1
                        if delta_d < max_neg_delta_d:
                            max_neg_delta_d = delta_d
        prev_d = d_dict
        
        # Reaction forces
        rp_rf1 = fr["rf1"].get(99999, 0.0)
        rp_u1 = fr["u1"].get(99999, 0.0)
        
        bottom_rf1 = sum(fr["rf1"].get(nid, 0.0) for nid in n_bottom)
        bottom_rf2 = sum(fr["rf2"].get(nid, 0.0) for nid in n_bottom)
        top_rf1 = sum(fr["rf1"].get(nid, 0.0) for nid in n_top)
        
        p_frame = {
            "step": s,
            "increment": inc,
            "step_time": t,
            "rp_u1_mm": rp_u1,
            "rp_rf1_N": rp_rf1,
            "rp_rf1_kN": rp_rf1 / 1000.0, # In N -> kN or in kN
            "bottom_rf1_N": bottom_rf1,
            "bottom_rf1_kN": bottom_rf1 / 1000.0,
            "d_min": d_min,
            "d_max": d_max,
            "d_mean": d_mean,
            "number_d_gt_0p1": d_gt_0p1,
            "number_d_gt_0p5": d_gt_0p5,
            "number_d_gt_0p9": d_gt_0p9,
            "location_of_dmax": {
                "node_label": max_nid,
                "coordinates": list(max_coords)
            },
            "max_negative_delta_d": max_neg_delta_d,
            "phase_irreversibility_violation_count": irrev_violations
        }
        processed_frames.append(p_frame)
        
        print("\n--- Step %d Inc %d (t=%.6e) ---" % (s, inc, t if t is not None else 0.0))
        print("  RP U1: %.8f mm, RP RF1: %.6f (Bottom sum RF1: %.6f)" % (rp_u1, rp_rf1, bottom_rf1))
        print("  Phase d: min=%.6f, max=%.6f (Node %s at %s), mean=%.6f" % (d_min, d_max, max_nid, str(max_coords), d_mean))
        print("  Counts: d>0.1: %d, d>0.5: %d, d>0.9: %d" % (d_gt_0p1, d_gt_0p5, d_gt_0p9))
        print("  Max negative delta d: %.3e (violations: %d)" % (max_neg_delta_d, irrev_violations))
        
    with open("ACCEPTED_FRAMES_FORENSIC.json", "w") as out:
        json.dump(processed_frames, out, indent=2)
    print("\nSaved ACCEPTED_FRAMES_FORENSIC.json")

if __name__ == "__main__":
    parse_dat("M2STATE_FRACFIX_RESTART2R6.dat", "M2STATE_FRACFIX_RESTART2R6.inp")

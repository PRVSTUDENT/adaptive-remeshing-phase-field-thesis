#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Extract Mode-II Adaptive crack path and field profiles from Abaqus ODB."""
import sys
import os
import math
import json
import csv

def extract_odb_damage(odb_path, out_dir):
    print("Opening ODB: %s" % odb_path)
    from odbAccess import openOdb
    odb = openOdb(path=odb_path, readOnly=True)
    
    # Check root assembly and instances
    root = odb.rootAssembly
    inst_name = root.instances.keys()[0]
    inst = root.instances[inst_name]
    print("Instance name: %s, total elements: %d, nodes: %d" % (inst_name, len(inst.elements), len(inst.nodes)))
    
    # Pre-compute element centroids from node coordinates
    node_coords = {}
    for node in inst.nodes:
        node_coords[node.label] = (node.coordinates[0], node.coordinates[1])
        
    elem_centroids = {}
    elem_types = {}
    for elem in inst.elements:
        conn = elem.connectivity
        xs = [node_coords[nl][0] for nl in conn]
        ys = [node_coords[nl][1] for nl in conn]
        elem_centroids[elem.label] = (sum(xs)/float(len(xs)), sum(ys)/float(len(ys)))
        elem_types[elem.label] = elem.type
        
    print("Centroids computed for %d elements." % len(elem_centroids))
    
    step = odb.steps[odb.steps.keys()[0]]
    n_frames = len(step.frames)
    print("Total frames in Step 1: %d" % n_frames)
    
    # Frames to extract: peak, intermediate, and final
    # Extract last frame first
    last_frame = step.frames[-1]
    time_val = last_frame.frameValue
    print("Extracting last frame %d at time %.6f" % (last_frame.frameId, time_val))
    
    # Check field outputs
    sdv_field = None
    if "SDV" in last_frame.fieldOutputs:
        sdv_field = last_frame.fieldOutputs["SDV"]
    elif "SDV14" in last_frame.fieldOutputs:
        sdv_field = last_frame.fieldOutputs["SDV14"]
    else:
        print("Available fields:", last_frame.fieldOutputs.keys())
        
    # Extract SDV values
    # In companion CPE4/CPE3 elements, SDV14 is damage d
    # Companion element labels start at N_phys + N_phys + 1 = 2*7865 + 1 = 15731 to 23595
    damage_rows = []
    if sdv_field is not None:
        for val in sdv_field.values:
            elabel = val.elementLabel
            # check if it's companion element
            if elabel > 15730:
                # get SDV14 (in SDV array, index 13 if 0-based, or check data length)
                d_val = 0.0
                if hasattr(val.data, '__getitem__'):
                    if len(val.data) >= 14:
                        d_val = float(val.data[13]) # SDV14
                    elif len(val.data) >= 1:
                        d_val = float(val.data[0])
                else:
                    d_val = float(val.data)
                    
                cx, cy = elem_centroids.get(elabel, (0.0, 0.0))
                orig_label = elabel - 2 * 7865
                damage_rows.append({
                    "comp_elem": elabel,
                    "orig_elem": orig_label,
                    "type": elem_types.get(elabel, "UNKNOWN"),
                    "x": cx,
                    "y": cy,
                    "sdv14": d_val
                })
                
    print("Extracted %d companion element damage entries." % len(damage_rows))
    
    # Save full damage CSV
    csv_path = os.path.join(out_dir, "adaptive_companion_damage_final.csv")
    with open(csv_path, "w") as f:
        w = csv.DictWriter(f, fieldnames=["comp_elem", "orig_elem", "type", "x", "y", "sdv14"])
        w.writeheader()
        for r in damage_rows:
            w.writerow(r)
            
    # Filter damaged elements d >= 0.5
    dmg_05 = [r for r in damage_rows if r["sdv14"] >= 0.5]
    print("Elements with d >= 0.5: %d" % len(dmg_05))
    
    # Compute binned centerline
    bins = {}
    bin_size = 0.02
    for r in dmg_05:
        # only look ahead of notch x >= -0.01
        if r["x"] >= -0.01:
            b_idx = int(round(r["x"] / bin_size))
            bins.setdefault(b_idx, []).append((r["x"], r["y"], r["sdv14"]))
            
    centerline = []
    for b_idx in sorted(bins.keys()):
        pts = bins[b_idx]
        sum_w = sum(p[2] for p in pts)
        if sum_w > 0:
            avg_x = sum(p[0] * p[2] for p in pts) / sum_w
            avg_y = sum(p[1] * p[2] for p in pts) / sum_w
            centerline.append((avg_x, avg_y, len(pts)))
            
    # Compute initial kink angle over x in [0.0, 0.15]
    kink_pts = [p for p in centerline if 0.0 <= p[0] <= 0.15]
    theta_kink_deg = None
    if len(kink_pts) >= 2:
        # Linear regression y = m*x + c
        n = len(kink_pts)
        mx = sum(p[0] for p in kink_pts) / n
        my = sum(p[1] for p in kink_pts) / n
        sxx = sum((p[0] - mx)**2 for p in kink_pts)
        sxy = sum((p[0] - mx)*(p[1] - my) for p in kink_pts)
        if sxx > 1e-12:
            slope = sxy / sxx
            theta_kink_deg = math.degrees(math.atan(slope))
            
    # Tip point (furthest +x with d >= 0.5)
    tip_x, tip_y, chord_deg = None, None, None
    if dmg_05:
        tip_elem = max(dmg_05, key=lambda p: p["x"])
        tip_x = tip_elem["x"]
        tip_y = tip_elem["y"]
        if tip_x > 1e-6:
            chord_deg = math.degrees(math.atan2(tip_y, tip_x))
            
    result = {
        "n_frames": n_frames,
        "final_time": time_val,
        "n_elements": len(damage_rows),
        "n_damaged_d05": len(dmg_05),
        "theta_kink_deg": theta_kink_deg,
        "theta_chord_deg": chord_deg,
        "tip_x_mm": tip_x,
        "tip_y_mm": tip_y,
        "centerline": centerline
    }
    
    res_path = os.path.join(out_dir, "adaptive_crack_path_summary.json")
    with open(res_path, "w") as f:
        json.dump(result, f, indent=2)
        
    print("Crack path extraction summary:")
    print(json.dumps(result, indent=2))
    odb.close()
    return result

if __name__ == "__main__":
    odb_p = sys.argv[1] if len(sys.argv) > 1 else "/scratch/pr21vyci/runs_mode2/04_adaptive_miseseri/M2_adapt_prod.odb"
    out_d = sys.argv[2] if len(sys.argv) > 2 else "/scratch/pr21vyci/runs_mode2/04_adaptive_miseseri/"
    extract_odb_damage(odb_p, out_d)

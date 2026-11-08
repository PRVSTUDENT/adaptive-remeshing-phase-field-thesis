# -*- coding: utf-8 -*-
"""
scripts/remeshing/extract_all_frames_coarse.py
=============================================
Task F1682: Complete ODB Frame Extraction for Coarse Donor Model
- Reads PK_HOLE_COARSE_JOB1.odb (494 MB, Job 1421063.mmaster02)
- Iterates across all 389 stored frames (51 in Step-1, 338 in Step-2)
- Extracts frame metadata, reference displacement U2, reaction force RF2
- Evaluates damage field SDV1 across all 2,906 physical elements
- Computes complete damage statistics (max, min, mean, threshold counts)
- Tracks crack tip location and distance to hole boundary
- Outputs structured frame telemetry CSV and summary JSON
"""
from __future__ import print_function
import os
import sys
import json
import csv
import math
import time

try:
    from odbAccess import openOdb
    from abaqusConstants import *
except ImportError as e:
    print("Error importing odbAccess: %s" % e)
    sys.exit(1)

def run_extraction():
    odb_path = "models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_COARSE_JOB1.odb"
    out_csv = "results/validation/f1682_coarse_all_frames_progression.csv"
    out_json = "results/validation/f1682_coarse_odb_inventory.json"
    full_field_csv = "results/validation/f1682_coarse_final_full_damage_field.csv"
    
    os.makedirs("results/validation", exist_ok=True)
    
    if not os.path.exists(odb_path):
        print("ODB file not found: %s" % odb_path)
        sys.exit(1)
        
    t0 = time.time()
    print("================================================================================")
    print("TASK F1682: ALL-FRAME EXTRACTION FOR COARSE DONOR ODB")
    print("ODB: %s (%.2f MB)" % (odb_path, os.path.getsize(odb_path) / (1024.0*1024.0)))
    print("================================================================================")
    
    odb = openOdb(path=odb_path, readOnly=True)
    root = odb.rootAssembly
    
    # Identify instance and elements
    inst_name = list(root.instances.keys())[0]
    inst = root.instances[inst_name]
    n_total_elems = len(inst.elements)
    print("Instance: '%s' with %d total elements" % (inst_name, n_total_elems))
    
    # Layered model: 3 layers -> physical elements = n_total_elems / 3
    # For PK_HOLE_COARSE_JOB1: 2,906 physical elements, 8,718 total elements
    n_phys = n_total_elems // 3
    umat_offset = 2 * n_phys
    print("Physical elements: %d (Companion visualizer layer offset: %d)" % (n_phys, umat_offset))
    
    # Pre-build centroid map for physical elements from instance geometry
    elem_centroids = {}
    node_coords = {}
    for n in inst.nodes:
        node_coords[n.label] = (n.coordinates[0], n.coordinates[1])
        
    for e in inst.elements:
        if 1 <= e.label <= n_phys:
            conn = e.connectivity
            pts = [node_coords[nid] for nid in conn if nid in node_coords]
            if pts:
                cx = sum(p[0] for p in pts) / float(len(pts))
                cy = sum(p[1] for p in pts) / float(len(pts))
                elem_centroids[e.label] = (cx, cy)
    print("Computed centroids for %d physical elements" % len(elem_centroids))
    
    hole_c = (0.65, 0.65)
    hole_r = 0.10
    notch_tip = (0.50, 0.50)
    
    field_history = []
    total_frames_processed = 0
    final_frame_damage = {}
    
    csv_headers = [
        "step_name", "frame_idx", "inc_num", "step_time", "total_time",
        "u2_top", "rf2_top",
        "d_max", "d_min", "d_mean",
        "cnt_ge_010", "cnt_ge_025", "cnt_ge_050", "cnt_ge_080", "cnt_ge_095",
        "tip_x", "tip_y", "dist_to_hole_perimeter"
    ]
    
    f_csv = open(out_csv, "w")
    writer = csv.writer(f_csv)
    writer.writerow(csv_headers)
    
    step_cumulative_time = 0.0
    
    for sname in ["Step-1", "Step-2"]:
        if sname not in odb.steps:
            print("Step '%s' not found, skipping." % sname)
            continue
        step = odb.steps[sname]
        n_frames = len(step.frames)
        print("\n--- Processing Step '%s': %d frames ---" % (sname, n_frames))
        
        for fidx, frame in enumerate(step.frames):
            inc_num = frame.incrementNumber
            step_time = float(frame.frameValue)
            total_time = step_cumulative_time + step_time
            
            # 1. Reference point U2 and RF2
            u2_top = 0.0
            rf2_top = 0.0
            if 'U' in frame.fieldOutputs:
                u_field = frame.fieldOutputs['U']
                for v in u_field.values:
                    if v.nodeLabel == 999999 or (hasattr(v, 'node') and v.node.label == 999999):
                        u2_top = float(v.data[1])
                        break
            if 'RF' in frame.fieldOutputs:
                rf_field = frame.fieldOutputs['RF']
                for v in rf_field.values:
                    if v.nodeLabel == 999999 or (hasattr(v, 'node') and v.node.label == 999999):
                        rf2_top = float(v.data[1])
                        break
                        
            # 2. Extract damage SDV1 across all physical elements
            d_vals = {}
            if 'SDV1' in frame.fieldOutputs:
                sdv_field = frame.fieldOutputs['SDV1']
                for v in sdv_field.values:
                    el_label = v.elementLabel
                    if umat_offset < el_label <= umat_offset + n_phys:
                        phys_id = el_label - umat_offset
                        val = float(v.data)
                        if phys_id not in d_vals or val > d_vals[phys_id]:
                            d_vals[phys_id] = val
                            
            if not d_vals:
                # Fallback if SDV1 is under layered element directly
                if 'SDV1' in frame.fieldOutputs:
                    for v in frame.fieldOutputs['SDV1'].values:
                        if 1 <= v.elementLabel <= n_phys:
                            d_vals[v.elementLabel] = float(v.data)
                            
            # If final frame of Step 2, store full field
            if sname == "Step-2" and fidx == n_frames - 1:
                final_frame_damage = dict(d_vals)
                
            # Compute statistics
            if d_vals:
                vals_list = list(d_vals.values())
                d_max = max(vals_list)
                d_min = min(vals_list)
                d_mean = sum(vals_list) / float(len(vals_list))
                
                c010 = sum(1 for d in vals_list if d >= 0.10)
                c025 = sum(1 for d in vals_list if d >= 0.25)
                c050 = sum(1 for d in vals_list if d >= 0.50)
                c080 = sum(1 for d in vals_list if d >= 0.80)
                c095 = sum(1 for d in vals_list if d >= 0.95)
                
                # Track advancing crack tip among damaged elements (d >= 0.50)
                max_eid = max(d_vals, key=d_vals.get) if d_vals else 0
                cx, cy = 0.50, 0.50
                max_x = 0.50
                for eid, d in d_vals.items():
                    if d >= 0.50 and eid in elem_centroids:
                        ex, ey = elem_centroids[eid]
                        if ex > max_x:
                            max_x = ex
                            cx = ex
                            cy = ey
                d_to_hole = math.hypot(cx - hole_c[0], cy - hole_c[1]) - hole_r
            else:
                d_max, d_min, d_mean = 0.0, 0.0, 0.0
                c010, c025, c050, c080, c095 = 0, 0, 0, 0, 0
                cx, cy = 0.50, 0.50
                d_to_hole = math.hypot(cx - hole_c[0], cy - hole_c[1]) - hole_r
                
            row = [
                sname, fidx, inc_num, round(step_time, 7), round(total_time, 7),
                round(u2_top, 7), round(rf2_top, 6),
                round(d_max, 6), round(d_min, 8), round(d_mean, 6),
                c010, c025, c050, c080, c095,
                round(cx, 5), round(cy, 5), round(d_to_hole, 5)
            ]
            writer.writerow(row)
            
            if fidx % 50 == 0 or fidx == n_frames - 1:
                print("  Frame %3d (Inc %3d): u2=%.5f mm, RF2=%.4f kN, d_max=%.4f (e%d at %.3f,%.3f, dist_hole=%.4f mm), broken(d>=0.8)=%d" % (
                    fidx, inc_num, u2_top, rf2_top, d_max, max_eid if d_vals else 0, cx, cy, d_to_hole, c080
                ))
                
            total_frames_processed += 1
            
        step_cumulative_time += getattr(step, 'timePeriod', getattr(step, 'totalTime', 1.0))
        
    f_csv.close()
    print("\n[Extraction Complete] Processed %d frames. Saved progression to: %s" % (total_frames_processed, out_csv))
    
    # Save full-field damage for final state
    if final_frame_damage:
        with open(full_field_csv, "w") as ff:
            ff_writer = csv.writer(ff)
            ff_writer.writerow(["phys_elem_id", "cx", "cy", "damage"])
            for eid in sorted(final_frame_damage.keys()):
                cx, cy = elem_centroids.get(eid, (0.0, 0.0))
                ff_writer.writerow([eid, round(cx, 6), round(cy, 6), round(final_frame_damage[eid], 6)])
        print("Saved complete final full-field damage (%d elements) to: %s" % (len(final_frame_damage), full_field_csv))
        
    # Summary JSON
    summary_data = {
        "odb_path": odb_path,
        "n_physical_elements": n_phys,
        "n_total_layered_elements": n_total_elems,
        "total_frames_extracted": total_frames_processed,
        "step1_frames": len(odb.steps["Step-1"].frames) if "Step-1" in odb.steps else 0,
        "step2_frames": len(odb.steps["Step-2"].frames) if "Step-2" in odb.steps else 0,
        "final_step": "Step-2",
        "final_damage_stats": {
            "d_max": max(final_frame_damage.values()) if final_frame_damage else 0.0,
            "broken_elements_d_ge_08": sum(1 for d in final_frame_damage.values() if d >= 0.80) if final_frame_damage else 0,
            "total_damaged_d_ge_01": sum(1 for d in final_frame_damage.values() if d >= 0.10) if final_frame_damage else 0,
            "total_intact_d_lt_01": sum(1 for d in final_frame_damage.values() if d < 0.10) if final_frame_damage else 0
        }
    }
    with open(out_json, "w") as jf:
        json.dump(summary_data, jf, indent=4)
    print("Saved summary metadata to: %s" % out_json)
    
    odb.close()
    print("Total runtime: %.2f seconds." % (time.time() - t0))

if __name__ == '__main__':
    run_extraction()

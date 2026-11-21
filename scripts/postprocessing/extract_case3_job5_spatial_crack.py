# -*- coding: utf-8 -*-
"""
scripts/postprocessing/extract_case3_job5_spatial_crack.py
==========================================================
Extracts spatial crack-tip position, crack extension from notch root,
and damage localization metrics across all frames of Job 5 ODB
for Method C Case 3 Cycle 4.
"""
from __future__ import print_function, division
import sys
import os
import json
import math

def extract_spatial_crack(odb_path, phys_mesh_path, out_json_path):
    from odbAccess import openOdb
    print("Opening ODB:", odb_path)
    odb = openOdb(odb_path, readOnly=True)
    
    # 1. Read node coordinates and element connectivity from physical mesh
    node_coords = {}
    elem_nodes = {}
    elem_centroids = {}
    
    print("Reading physical mesh from:", phys_mesh_path)
    with open(phys_mesh_path, "r") as f:
        in_nodes = False
        in_elems = False
        for line in f:
            line = line.strip()
            if not line or line.startswith("**"):
                continue
            if line.startswith("*NODE"):
                in_nodes = True
                in_elems = False
                continue
            elif line.startswith("*ELEMENT"):
                in_nodes = False
                in_elems = True
                continue
            elif line.startswith("*"):
                in_nodes = False
                in_elems = False
                continue
                
            if in_nodes:
                parts = [p.strip() for p in line.split(",")]
                nid = int(parts[0])
                node_coords[nid] = (float(parts[1]), float(parts[2]))
            elif in_elems:
                parts = [p.strip() for p in line.split(",")]
                eid = int(parts[0])
                nids = [int(p) for p in parts[1:] if p]
                elem_nodes[eid] = nids
                
    for eid, nids in elem_nodes.items():
        xs = [node_coords[nid][0] for nid in nids if nid in node_coords]
        ys = [node_coords[nid][1] for nid in nids if nid in node_coords]
        if xs and ys:
            elem_centroids[eid] = (sum(xs) / len(xs), sum(ys) / len(ys))
            
    print("Loaded %d nodes, %d physical elements with centroids." % (len(node_coords), len(elem_centroids)))
    
    num_phys = len(elem_centroids)  # 64653
    offset_layer3 = 2 * num_phys    # 129306
    
    # Notch root reference coordinates in Case 3
    x_notch_root = 10.0
    y_notch_root = 70.0
    
    # Central void coordinates
    hole_center_x = 36.5
    hole_center_y = 51.0
    hole_radius = 10.0
    
    thresholds = [0.2, 0.4, 0.5, 0.6, 0.8, 0.9, 0.95]
    
    results = {
        "benchmark": "Pandey & Kumar (2025) Section 4.3 - Case 3 Cycle 4",
        "job": "PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5",
        "notch_root": [x_notch_root, y_notch_root],
        "hole_center": [hole_center_x, hole_center_y],
        "hole_radius": hole_radius,
        "thresholds": thresholds,
        "num_physical_elements": num_phys,
        "steps": {}
    }
    
    for sname in odb.steps.keys():
        step = odb.steps[sname]
        step_data = []
        print("\nProcessing Step: %s (%d frames)" % (sname, len(step.frames)))
        
        for f_idx, f in enumerate(step.frames):
            t = float(f.frameValue)
            desc = str(f.description)
            
            # RP observables
            u2_rp = 0.0
            rf2_rp = 0.0
            if 'U' in f.fieldOutputs:
                for v in f.fieldOutputs['U'].values:
                    if v.nodeLabel == 999999:
                        u2_rp = float(v.data[1])
                        break
            if 'RF' in f.fieldOutputs:
                for v in f.fieldOutputs['RF'].values:
                    if v.nodeLabel == 999999:
                        rf2_rp = float(v.data[1])
                        break
                        
            # Element damage extraction from SDV1 (companion layer 3)
            elem_max_d = {}  # phys_eid -> max damage over its GPs
            if 'SDV1' in f.fieldOutputs:
                for v in f.fieldOutputs['SDV1'].values:
                    eid = v.elementLabel
                    phys_eid = eid - offset_layer3 if eid > offset_layer3 else eid
                    if phys_eid in elem_centroids:
                        val = float(v.data)
                        if phys_eid not in elem_max_d or val > elem_max_d[phys_eid]:
                            elem_max_d[phys_eid] = val
            
            peak_d = max(elem_max_d.values()) if elem_max_d else 0.0
            peak_eid = max(elem_max_d, key=elem_max_d.get) if elem_max_d else None
            peak_coord = elem_centroids.get(peak_eid, (x_notch_root, y_notch_root))
            
            # Spatial crack tip detection for each threshold
            thresh_metrics = {}
            for th in thresholds:
                damaged_eids = [eid for eid, d in elem_max_d.items() if d >= th]
                if damaged_eids:
                    xs = [elem_centroids[eid][0] for eid in damaged_eids]
                    ys = [elem_centroids[eid][1] for eid in damaged_eids]
                    
                    max_x = max(xs)
                    tip_eids = [eid for eid in damaged_eids if abs(elem_centroids[eid][0] - max_x) < 1e-4]
                    tip_y = elem_centroids[tip_eids[0]][1] if tip_eids else y_notch_root
                    
                    delta_a_x = max_x - x_notch_root
                    delta_a_euclid = math.sqrt((max_x - x_notch_root)**2 + (tip_y - y_notch_root)**2)
                    
                    # Distance to central circular hole perimeter
                    dist_to_center = math.sqrt((max_x - hole_center_x)**2 + (tip_y - hole_center_y)**2)
                    dist_to_hole = max(0.0, dist_to_center - hole_radius)
                    hole_penetrated = (dist_to_center <= hole_radius)
                    
                    thresh_metrics["d_ge_%.2f" % th] = {
                        "count_elements": len(damaged_eids),
                        "tip_x": max_x,
                        "tip_y": tip_y,
                        "delta_a_x_mm": delta_a_x,
                        "delta_a_euclid_mm": delta_a_euclid,
                        "dist_to_hole_mm": dist_to_hole,
                        "hole_penetrated": hole_penetrated
                    }
                else:
                    thresh_metrics["d_ge_%.2f" % th] = {
                        "count_elements": 0,
                        "tip_x": x_notch_root,
                        "tip_y": y_notch_root,
                        "delta_a_x_mm": 0.0,
                        "delta_a_euclid_mm": 0.0,
                        "dist_to_hole_mm": math.sqrt((x_notch_root - hole_center_x)**2 + (y_notch_root - hole_center_y)**2) - hole_radius,
                        "hole_penetrated": False
                    }
                    
            frame_res = {
                "frame_index": f_idx,
                "step_time": t,
                "description": desc,
                "u2_rp_mm": u2_rp,
                "rf2_rp_kn": rf2_rp,
                "peak_damage": peak_d,
                "peak_damage_eid": peak_eid,
                "peak_damage_coord": peak_coord,
                "spatial_metrics": thresh_metrics
            }
            step_data.append(frame_res)
            
            # Print summary for important frames
            d95 = thresh_metrics["d_ge_0.95"]
            d50 = thresh_metrics["d_ge_0.50"]
            print("Frame %2d (t=%.4e, u2=%.5f mm): RF2=%.4f kN, d_max=%.4f | tip(d>=0.95)=(%.3f, %.3f), Da_x=%.3f mm, dist_hole=%.3f mm | tip(d>=0.50)=(%.3f, %.3f)" % (
                f_idx, t, u2_rp, rf2_rp, peak_d,
                d95["tip_x"], d95["tip_y"], d95["delta_a_x_mm"], d95["dist_to_hole_mm"],
                d50["tip_x"], d50["tip_y"]
            ))
            
        results["steps"][sname] = step_data
        
    odb.close()
    
    with open(out_json_path, "w") as f:
        json.dump(results, f, indent=2)
    print("\nSaved spatial crack analysis to:", out_json_path)

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: abaqus python extract_case3_job5_spatial_crack.py <odb_path> <phys_mesh_path> <out_json_path>")
        sys.exit(1)
    extract_spatial_crack(sys.argv[1], sys.argv[2], sys.argv[3])

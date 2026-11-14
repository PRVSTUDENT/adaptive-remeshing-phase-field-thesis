#!/usr/bin/env python3
"""
scripts/remeshing/evaluate_f1735_spatial_crack.py
Evaluates spatial damage localization, crack trajectory, and hole interaction
for Task F1735 Case 2 Adapted-Mesh Fracture Simulation.
"""

import csv
import json
import math
import numpy as np

def evaluate_spatial_crack():
    mesh_inp = "models/pandey_kumar_mode1/224_f1734_case2_distal_refinement/PK_F1728_CASE_2_ADAPT_PHYS.inp"
    sdv_csv = "results/validation/f1735_case2_final_frame_sdv.csv"
    summary_json = "results/validation/f1735_case2_odb_summary.json"
    
    # 1. Parse nodes from physical mesh INP
    nodes = {}
    elements = {}
    
    with open(mesh_inp, 'r') as f:
        reading_nodes = False
        reading_elements = False
        for line in f:
            line_str = line.strip()
            if not line_str or line_str.startswith('**'):
                continue
            line_upper = line_str.upper()
            if line_upper.startswith('*NODE'):
                reading_nodes = True
                reading_elements = False
                continue
            elif line_upper.startswith('*ELEMENT') and not line_upper.startswith('*ELEMENT OUTPUT'):
                reading_nodes = False
                reading_elements = True
                continue
            elif line_upper.startswith('*'):
                reading_nodes = False
                reading_elements = False
                continue
                
            if reading_nodes:
                parts = [p.strip() for p in line_str.split(',')]
                try:
                    nid = int(parts[0])
                    x = float(parts[1])
                    y = float(parts[2])
                    nodes[nid] = (x, y)
                except ValueError:
                    pass
                
            elif reading_elements:
                parts = [p.strip() for p in line_str.split(',')]
                try:
                    eid = int(parts[0])
                    conn = [int(p) for p in parts[1:]]
                    elements[eid] = conn
                except ValueError:
                    pass
                
    print(f"Loaded {len(nodes)} nodes and {len(elements)} physical elements.")
    
    # Compute element centroids
    centroids = {}
    for eid, conn in elements.items():
        cx = sum(nodes[nid][0] for nid in conn) / len(conn)
        cy = sum(nodes[nid][1] for nid in conn) / len(conn)
        centroids[eid] = (cx, cy)
        
    # 2. Read final frame SDV CSV
    damage = {}
    history = {}
    with open(sdv_csv, 'r') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            eid = int(row[0])
            d_val = float(row[1])
            h_val = float(row[2])
            damage[eid] = d_val
            history[eid] = h_val
            
    print(f"Loaded damage and history for {len(damage)} elements.")
    
    # 3. Benchmark coordinates
    NOTCH_TIP = (0.50, 0.50)
    HOLE_CENTER = (0.65, 0.65)
    HOLE_RADIUS = 0.10
    HOLE_FLANK = (0.65, 0.55)
    
    # 4. Statistical distribution of damage
    d_vals = list(damage.values())
    max_d = max(d_vals)
    min_d = min(d_vals)
    
    elems_ge_050 = [eid for eid, d in damage.items() if d >= 0.50]
    elems_ge_075 = [eid for eid, d in damage.items() if d >= 0.75]
    elems_ge_090 = [eid for eid, d in damage.items() if d >= 0.90]
    elems_ge_095 = [eid for eid, d in damage.items() if d >= 0.95]
    
    # Spatial extent of damaged elements
    def elem_metrics(eid):
        cx, cy = centroids[eid]
        dist_notch = math.sqrt((cx - NOTCH_TIP[0])**2 + (cy - NOTCH_TIP[1])**2)
        dist_hole_center = math.sqrt((cx - HOLE_CENTER[0])**2 + (cy - HOLE_CENTER[1])**2)
        dist_hole_boundary = dist_hole_center - HOLE_RADIUS
        dist_hole_flank = math.sqrt((cx - HOLE_FLANK[0])**2 + (cy - HOLE_FLANK[1])**2)
        return {
            "element_id": eid,
            "centroid": (round(cx, 6), round(cy, 6)),
            "damage_d": round(damage[eid], 6),
            "history_h": round(history[eid], 6),
            "dist_notch_mm": round(dist_notch, 6),
            "dist_hole_boundary_mm": round(dist_hole_boundary, 6),
            "dist_hole_flank_mm": round(dist_hole_flank, 6)
        }
        
    data_095 = [elem_metrics(eid) for eid in elems_ge_095]
    data_075 = [elem_metrics(eid) for eid in elems_ge_075]
    data_050 = [elem_metrics(eid) for eid in elems_ge_050]
    
    max_reach_095 = max(e['dist_notch_mm'] for e in data_095) if data_095 else 0.0
    min_dist_hole_095 = min(e['dist_hole_boundary_mm'] for e in data_095) if data_095 else 999.0
    
    max_reach_075 = max(e['dist_notch_mm'] for e in data_075) if data_075 else 0.0
    min_dist_hole_075 = min(e['dist_hole_boundary_mm'] for e in data_075) if data_075 else 999.0
    
    max_reach_050 = max(e['dist_notch_mm'] for e in data_050) if data_050 else 0.0
    min_dist_hole_050 = min(e['dist_hole_boundary_mm'] for e in data_050) if data_050 else 999.0
    
    # Crack tip element (furthest damaged element)
    tip_elem_095 = max(data_095, key=lambda e: e['dist_notch_mm']) if data_095 else None
    tip_elem_075 = max(data_075, key=lambda e: e['dist_notch_mm']) if data_075 else None
    
    # 5. Read summary JSON for frame history
    summary_data = {}
    if summary_json:
        try:
            with open(summary_json, 'r') as f:
                summary_data = json.load(f)
        except Exception as e:
            print(f"Could not read summary json: {e}")
            
    # Check bounds and irreversibility across sampled frames
    sampled_frames = summary_data.get('sampled_frames_history', [])
    bounds_pass = summary_data.get('global_damage_bounds', {}).get('bounds_satisfied', False)
    irrev_pass = summary_data.get('global_damage_irreversibility', {}).get('irreversibility_satisfied', False)
    
    results = {
        "global_damage_bounds": {
            "min_d": min_d,
            "max_d": max_d,
            "lower_bound_violations": summary_data.get('global_damage_bounds', {}).get('lower_bound_violations_count', 0),
            "upper_bound_violations": summary_data.get('global_damage_bounds', {}).get('upper_bound_violations_count', 0),
            "bounds_satisfied": bounds_pass
        },
        "global_irreversibility": {
            "min_delta_d": summary_data.get('global_damage_irreversibility', {}).get('min_delta_d', 0.0),
            "irreversibility_violations": summary_data.get('global_damage_irreversibility', {}).get('irreversibility_violations_count', 0),
            "irreversibility_satisfied": irrev_pass
        },
        "global_history_monotonicity": {
            "min_delta_h": summary_data.get('global_history_monotonicity', {}).get('min_delta_h', 0.0),
            "monotonicity_violations": summary_data.get('global_history_monotonicity', {}).get('monotonicity_violations_count', 0),
            "monotonicity_satisfied": summary_data.get('global_history_monotonicity', {}).get('monotonicity_satisfied', True)
        },
        "damage_population": {
            "total_physical_elements": len(elements),
            "count_d_ge_050": len(elems_ge_050),
            "count_d_ge_075": len(elems_ge_075),
            "count_d_ge_090": len(elems_ge_090),
            "count_d_ge_095": len(elems_ge_095)
        },
        "crack_trajectory_and_geometry": {
            "max_reach_095_mm": max_reach_095,
            "min_dist_to_hole_boundary_095_mm": min_dist_hole_095,
            "max_reach_075_mm": max_reach_075,
            "min_dist_to_hole_boundary_075_mm": min_dist_hole_075,
            "max_reach_050_mm": max_reach_050,
            "min_dist_to_hole_boundary_050_mm": min_dist_hole_050,
            "crack_tip_element_095": tip_elem_095,
            "crack_tip_element_075": tip_elem_075,
            "ligament_bridged_095": (min_dist_hole_095 <= 0.005),
            "ligament_bridged_075": (min_dist_hole_075 <= 0.005),
            "ligament_bridged_050": (min_dist_hole_050 <= 0.005)
        },
        "sampled_frames_progression": sampled_frames
    }
    
    out_file = "results/validation/f1735_case2_spatial_crack_audit.json"
    with open(out_file, 'w') as f:
        json.dump(results, f, indent=2)
        
    print(json.dumps(results, indent=2))
    return results

if __name__ == "__main__":
    evaluate_spatial_crack()

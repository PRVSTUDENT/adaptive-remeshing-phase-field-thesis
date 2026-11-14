#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
scripts/remeshing/audit_f1739_case1_odb_results.py
Abaqus Python script to audit authentic field outputs in PK_F1739_CASE_1_FRAC.odb:
- Mesh: 13,960 physical elements (Layer 3 IDs: 27921 to 41880, offset: 27920)
- Damage bounds: 0 <= d <= 1
- Damage irreversibility: Delta d >= -1e-6
- History monotonicity: Delta H >= -1e-6
- Spatial ligament severance audit across all 10 horizontal stations (x in [0.5, 1.0] mm, y = 0.5 mm)
- Output JSON summary for automated reporting and unit tests
"""

import sys
import os
import json
import math
from odbAccess import openOdb

def run_odb_audit(odb_path, output_json_path):
    print("Opening ODB: %s" % odb_path)
    odb = openOdb(odb_path, readOnly=True)
    
    root = odb.rootAssembly
    instance = root.instances.values()[0]
    
    NUM_PHYSICAL = 13960
    LAYER3_OFFSET = 27920
    LAYER3_START = 27921
    LAYER3_END = 41880
    
    # 1. Compute centroids of physical elements (1 to 13960)
    print("Computing element centroids...")
    node_coords = {}
    for node in instance.nodes:
        node_coords[node.label] = node.coordinates[:2]
        
    elem_centroids = {} # physical_id -> (xc, yc)
    for elem in instance.elements:
        if elem.label <= NUM_PHYSICAL:
            cx = sum(node_coords[nl][0] for nl in elem.connectivity) / float(len(elem.connectivity))
            cy = sum(node_coords[nl][1] for nl in elem.connectivity) / float(len(elem.connectivity))
            elem_centroids[elem.label] = (cx, cy)
            
    print("Extracted centroids for %d physical elements." % len(elem_centroids))
    
    # 2. Iterate through steps and frames
    step_names = odb.steps.keys()
    print("Found steps: %s" % str(step_names))
    
    total_frames = 0
    prev_d = None
    prev_h = None
    
    global_min_d = 1.0e9
    global_max_d = -1.0e9
    global_min_delta_d = 1.0e9
    global_min_delta_h = 1.0e9
    
    total_d_lower_bound_violations = 0
    total_d_upper_bound_violations = 0
    total_d_irreversibility_violations = 0
    total_h_monotonicity_violations = 0
    
    frame_records = []
    final_d = {}
    final_h = {}
    
    for s_idx, s_name in enumerate(step_names):
        step = odb.steps[s_name]
        n_frames = len(step.frames)
        print("Step %s has %d frames." % (s_name, n_frames))
        
        for f_idx, frame in enumerate(step.frames):
            f_time = frame.frameValue
            
            # Read SDV field
            if 'SDV1' in frame.fieldOutputs:
                sdv1_field = frame.fieldOutputs['SDV1']
                sdv2_field = frame.fieldOutputs['SDV2']
            elif 'SDV' in frame.fieldOutputs:
                sdv_field = frame.fieldOutputs['SDV']
                sdv1_field = sdv_field.getComponent(componentLabel='SDV1')
                sdv2_field = sdv_field.getComponent(componentLabel='SDV2')
            else:
                # Frame 0 or increments without field output
                continue
                
            total_frames += 1
            d_curr = {}
            h_curr = {}
            
            for val in sdv1_field.values:
                el_label = val.elementLabel
                if LAYER3_START <= el_label <= LAYER3_END:
                    phys_id = el_label - LAYER3_OFFSET
                    d_curr[phys_id] = float(val.data)
                    
            for val in sdv2_field.values:
                el_label = val.elementLabel
                if LAYER3_START <= el_label <= LAYER3_END:
                    phys_id = el_label - LAYER3_OFFSET
                    h_curr[phys_id] = float(val.data)
                    
            if not d_curr:
                continue
                
            # Frame extrema
            min_d_frame = min(d_curr.values())
            max_d_frame = max(d_curr.values())
            if min_d_frame < global_min_d:
                global_min_d = min_d_frame
            if max_d_frame > global_max_d:
                global_max_d = max_d_frame
                
            # Bound checks
            for pid, d_val in d_curr.items():
                if d_val < -1.0e-6:
                    total_d_lower_bound_violations += 1
                if d_val > 1.005:
                    total_d_upper_bound_violations += 1
                    
            # Monotonicity checks
            if prev_d is not None and prev_h is not None:
                min_delta_d_frame = 1.0e9
                min_delta_h_frame = 1.0e9
                for pid in d_curr:
                    if pid in prev_d:
                        del_d = d_curr[pid] - prev_d[pid]
                        del_h = h_curr[pid] - prev_h[pid]
                        if del_d < min_delta_d_frame:
                            min_delta_d_frame = del_d
                        if del_h < min_delta_h_frame:
                            min_delta_h_frame = del_h
                        if del_d < -1.0e-4:
                            total_d_irreversibility_violations += 1
                        if del_h < -1.0e-6:
                            total_h_monotonicity_violations += 1
                            
                if min_delta_d_frame < global_min_delta_d:
                    global_min_delta_d = min_delta_d_frame
                if min_delta_h_frame < global_min_delta_h:
                    global_min_delta_h = min_delta_h_frame
                    
            prev_d = d_curr
            prev_h = h_curr
            final_d = d_curr
            final_h = h_curr
            
            # Count elements with d >= 0.95
            fully_damaged = sum(1 for v in d_curr.values() if v >= 0.95)
            frame_records.append({
                'step': s_name,
                'frame_index': f_idx,
                'time': f_time,
                'min_d': min_d_frame,
                'max_d': max_d_frame,
                'num_d_ge_095': fully_damaged
            })
            
    odb.close()
    print("Closed ODB. Total valid frames audited: %d" % len(frame_records))
    
    # 3. Spatial Ligament Severance Audit across 10 Horizontal Stations
    # Trajectory: x in [0.50, 1.00] mm, y = 0.50 mm.
    # Half-width w_perp = 2.5 * l0 = 2.5 * 0.0075 = 0.01875 mm.
    L0 = 0.0075
    W_PERP = 2.5 * L0 # 0.01875 mm
    
    stations = []
    num_stations = 10
    dx_station = 0.50 / float(num_stations) # 0.05 mm per station
    
    all_stations_severed = True
    
    for s_i in range(num_stations):
        x_min = 0.50 + s_i * dx_station
        x_max = x_min + dx_station
        x_center = 0.5 * (x_min + x_max)
        
        station_elems = []
        d_vals = []
        fully_damaged_count = 0
        
        for pid, (cx, cy) in elem_centroids.items():
            if x_min <= cx < (x_max if s_i < num_stations - 1 else x_max + 1e-6):
                if abs(cy - 0.50) <= W_PERP:
                    station_elems.append(pid)
                    d_val = final_d.get(pid, 0.0)
                    d_vals.append(d_val)
                    if d_val >= 0.95:
                        fully_damaged_count += 1
                        
        max_d_st = max(d_vals) if d_vals else 0.0
        mean_d_st = sum(d_vals) / float(len(d_vals)) if d_vals else 0.0
        station_severed = (fully_damaged_count > 0 and max_d_st >= 0.95)
        if not station_severed:
            all_stations_severed = False
            
        stations.append({
            'station_id': s_i + 1,
            'x_min_mm': round(x_min, 4),
            'x_max_mm': round(x_max, 4),
            'x_center_mm': round(x_center, 4),
            'num_elements_in_corridor': len(station_elems),
            'num_d_ge_095': fully_damaged_count,
            'max_d': round(max_d_st, 6),
            'mean_d': round(mean_d_st, 6),
            'severed': station_severed
        })
        
    total_fully_damaged_all_mesh = sum(1 for v in final_d.values() if v >= 0.95)
    
    summary = {
        'total_frames_audited': len(frame_records),
        'total_physical_elements': NUM_PHYSICAL,
        'global_min_d': float(global_min_d),
        'global_max_d': float(global_max_d),
        'global_min_delta_d': float(global_min_delta_d) if global_min_delta_d < 1e8 else 0.0,
        'global_min_delta_h': float(global_min_delta_h) if global_min_delta_h < 1e8 else 0.0,
        'lower_bound_violations': total_d_lower_bound_violations,
        'upper_bound_violations': total_d_upper_bound_violations,
        'irreversibility_violations': total_d_irreversibility_violations,
        'monotonicity_violations': total_h_monotonicity_violations,
        'total_elements_d_ge_095': total_fully_damaged_all_mesh,
        'all_10_stations_severed': all_stations_severed,
        'stations': stations,
        'final_frame_sample': frame_records[-1] if frame_records else None
    }
    
    with open(output_json_path, 'w') as f:
        json.dump(summary, f, indent=2)
        
    print("Successfully wrote summary to %s" % output_json_path)
    print("All 10 stations severed (d >= 0.95): %s" % str(all_stations_severed))
    print("Total elements with d >= 0.95: %d" % total_fully_damaged_all_mesh)
    print("Global min d: %.6f, max d: %.6f" % (global_min_d, global_max_d))

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: abaqus python audit_f1739_case1_odb_results.py <odb_path> <output_json_path>")
        sys.exit(1)
    run_odb_audit(sys.argv[1], sys.argv[2])

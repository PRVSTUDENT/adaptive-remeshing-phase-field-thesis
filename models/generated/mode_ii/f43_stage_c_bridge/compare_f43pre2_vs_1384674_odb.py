#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ODB Extraction and Scientific Comparison Script for F43PRE2_GEOM (1385392) vs F43PRE1 (1384674).
Designed to run read-only under Abaqus Python: abaqus python compare_f43pre2_vs_1384674_odb.py
"""

import sys
import os
import math
import json
from odbAccess import openOdb

def percentile(N, percent):
    if not N:
        return 0.0
    k = (len(N) - 1) * percent
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return N[int(k)]
    d0 = N[int(f)] * (c - k)
    d1 = N[int(c)] * (k - f)
    return d0 + d1

def compute_stats(values):
    if not values:
        return {
            "min": 0.0, "max": 0.0, "mean": 0.0, "median": 0.0,
            "std": 0.0, "p90": 0.0, "p95": 0.0, "p99": 0.0,
            "count": 0, "finite": 0, "nan_inf": 0, "zero_count": 0, "nonzero_fraction": 0.0
        }
    finite_vals = [v for v in values if not math.isnan(v) and not math.isinf(v)]
    nan_inf_count = len(values) - len(finite_vals)
    if not finite_vals:
        return {
            "min": 0.0, "max": 0.0, "mean": 0.0, "median": 0.0,
            "std": 0.0, "p90": 0.0, "p95": 0.0, "p99": 0.0,
            "count": len(values), "finite": 0, "nan_inf": nan_inf_count, "zero_count": 0, "nonzero_fraction": 0.0
        }
    
    sorted_v = sorted(finite_vals)
    n = len(sorted_v)
    mean_val = sum(sorted_v) / float(n)
    var_val = sum((x - mean_val) ** 2 for x in sorted_v) / float(n)
    std_val = math.sqrt(var_val)
    zero_cnt = sum(1 for x in sorted_v if abs(x) < 1e-12)
    nonzero_frac = (n - zero_cnt) / float(n)

    return {
        "min": sorted_v[0],
        "max": sorted_v[-1],
        "mean": mean_val,
        "median": percentile(sorted_v, 0.50),
        "std": std_val,
        "p90": percentile(sorted_v, 0.90),
        "p95": percentile(sorted_v, 0.95),
        "p99": percentile(sorted_v, 0.99),
        "count": len(values),
        "finite": n,
        "nan_inf": nan_inf_count,
        "zero_count": zero_cnt,
        "nonzero_fraction": nonzero_frac
    }

def extract_odb_data(odb_path, label):
    print("Opening ODB read-only: " + odb_path)
    odb = openOdb(odb_path, readOnly=True)
    
    inventory = {
        "step_names": list(odb.steps.keys()),
        "instance_names": list(odb.rootAssembly.instances.keys()),
        "assembly_node_sets": list(odb.rootAssembly.nodeSets.keys()),
        "assembly_element_sets": list(odb.rootAssembly.elementSets.keys())
    }
    
    step_name = odb.steps.keys()[0]
    step = odb.steps[step_name]
    inventory["frame_count"] = len(step.frames)
    inventory["frame_times"] = [f.frameValue for f in step.frames]
    
    inst_name = odb.rootAssembly.instances.keys()[0]
    inst = odb.rootAssembly.instances[inst_name]
    
    # Extract Node Coordinates for element centroid calculation
    node_coords = {}
    for node in inst.nodes:
        node_coords[node.label] = (node.coordinates[0], node.coordinates[1])
        
    # Element Topology & Centroids
    elem_centroids = {}
    elem_topologies = {}
    for elem in inst.elements:
        top = elem.type
        elem_topologies[elem.label] = top
        pts = [node_coords[nl] for nl in elem.connectivity]
        xc = sum(p[0] for p in pts) / float(len(pts))
        yc = sum(p[1] for p in pts) / float(len(pts))
        elem_centroids[elem.label] = (xc, yc)
        
    # History & RF/U curve across frames
    rf_u_history = []
    for f_idx, frame in enumerate(step.frames):
        u1_max = 0.0
        rf1_total = 0.0
        
        # Check node field output for U and RF
        if 'U' in frame.fieldOutputs:
            u_field = frame.fieldOutputs['U']
            for v in u_field.values:
                # Top boundary node at y=0.5
                n_coord = node_coords.get(v.nodeLabel, (0, 0))
                if abs(n_coord[1] - 0.5) < 1e-4:
                    if abs(v.data[0]) > abs(u1_max):
                        u1_max = v.data[0]
                        
        if 'RF' in frame.fieldOutputs:
            rf_field = frame.fieldOutputs['RF']
            for v in rf_field.values:
                n_coord = node_coords.get(v.nodeLabel, (0, 0))
                if abs(n_coord[1] - 0.5) < 1e-4:
                    rf1_total += v.data[0]
                    
        rf_u_history.append({"frame": f_idx, "time": frame.frameValue, "U1": u1_max, "RF1": rf1_total})
        
    # Last Frame Field Extraction
    last_frame = step.frames[-1]
    available_fields = list(last_frame.fieldOutputs.keys())
    inventory["available_fields"] = available_fields
    
    # Extract MISESERI, MISESAVG, EVOL, S
    miseseri_dict = {}
    misesavg_dict = {}
    evol_dict = {}
    s_mises_dict = {}
    
    if 'MISESERI' in last_frame.fieldOutputs:
        f_m = last_frame.fieldOutputs['MISESERI']
        for val in f_m.values:
            e_label = val.elementLabel
            if e_label:
                miseseri_dict[e_label] = val.data
                
    if 'MISESAVG' in last_frame.fieldOutputs:
        f_ma = last_frame.fieldOutputs['MISESAVG']
        for val in f_ma.values:
            e_label = val.elementLabel
            if e_label:
                misesavg_dict[e_label] = val.data
                
    if 'EVOL' in last_frame.fieldOutputs:
        f_ev = last_frame.fieldOutputs['EVOL']
        for val in f_ev.values:
            e_label = val.elementLabel
            if e_label:
                evol_dict[e_label] = val.data
                
    if 'S' in last_frame.fieldOutputs:
        f_s = last_frame.fieldOutputs['S']
        for val in f_s.values:
            e_label = val.elementLabel
            if e_label:
                # Average integration point stress for element
                s_mises = val.mises if hasattr(val, 'mises') and val.mises is not None else 0.0
                if e_label not in s_mises_dict:
                    s_mises_dict[e_label] = []
                s_mises_dict[e_label].append(s_mises)
                
    # Average element S_mises
    for el in s_mises_dict:
        vals = s_mises_dict[el]
        s_mises_dict[el] = sum(vals) / float(len(vals))
        
    odb.close()
    
    return {
        "label": label,
        "path": odb_path,
        "inventory": inventory,
        "rf_u_history": rf_u_history,
        "elem_centroids": elem_centroids,
        "elem_topologies": elem_topologies,
        "miseseri": miseseri_dict,
        "misesavg": misesavg_dict,
        "evol": evol_dict,
        "s_mises": s_mises_dict
    }

def main():
    if len(sys.argv) < 3:
        print("Usage: abaqus python compare_f43pre2_vs_1384674_odb.py <odb_new_path> <odb_old_path> [out_dir]")
        sys.exit(1)
        
    new_odb_path = sys.argv[1]
    old_odb_path = sys.argv[2]
    out_dir = sys.argv[3] if len(sys.argv) > 3 else "."
    
    new_data = extract_odb_data(new_odb_path, "F43PRE2_1385392")
    old_data = extract_odb_data(old_odb_path, "F43PRE1_1384674")
    
    # 1. Save CSVs for RF1-U1 history
    csv_new_path = os.path.join(out_dir, "F43PRE2_1385392_RF1_U1.csv")
    with open(csv_new_path, "w") as f:
        f.write("Frame,Time,U1_mm,RF1_N\n")
        for row in new_data["rf_u_history"]:
            f.write("{},{},{},{}\n".format(row["frame"], row["time"], row["U1"], row["RF1"]))
            
    csv_old_path = os.path.join(out_dir, "F43PRE1_1384674_RF1_U1.csv")
    with open(csv_old_path, "w") as f:
        f.write("Frame,Time,U1_mm,RF1_N\n")
        for row in old_data["rf_u_history"]:
            f.write("{},{},{},{}\n".format(row["frame"], row["time"], row["U1"], row["RF1"]))
            
    # 2. Global Load-Displacement Metrics
    new_final_u1 = new_data["rf_u_history"][-1]["U1"]
    new_final_rf1 = new_data["rf_u_history"][-1]["RF1"]
    old_final_u1 = old_data["rf_u_history"][-1]["U1"]
    old_final_rf1 = old_data["rf_u_history"][-1]["RF1"]
    
    rf1_rel_err_pct = (abs(new_final_rf1 - old_final_rf1) / abs(old_final_rf1)) * 100.0 if old_final_rf1 != 0 else 0.0
    
    new_k_eff = new_final_rf1 / new_final_u1 if new_final_u1 != 0 else 0.0
    old_k_eff = old_final_rf1 / old_final_u1 if old_final_u1 != 0 else 0.0
    k_rel_err_pct = (abs(new_k_eff - old_k_eff) / abs(old_k_eff)) * 100.0 if old_k_eff != 0 else 0.0
    
    # 3. MISESERI Activity & Statistics
    new_m_stats = compute_stats(list(new_data["miseseri"].values()))
    old_m_stats = compute_stats(list(old_data["miseseri"].values()))
    
    new_ma_stats = compute_stats(list(new_data["misesavg"].values()))
    old_ma_stats = compute_stats(list(old_data["misesavg"].values()))
    
    # Max location & crack tip distance (l0 = 0.015 mm)
    l0 = 0.015
    new_max_elem = None
    new_max_val = -1e9
    for el, val in new_data["miseseri"].items():
        if val > new_max_val:
            new_max_val = val
            new_max_elem = el
    new_max_loc = new_data["elem_centroids"].get(new_max_elem, (0, 0)) if new_max_elem else (0, 0)
    new_max_dist = math.sqrt(new_max_loc[0]**2 + new_max_loc[1]**2)
    
    old_max_elem = None
    old_max_val = -1e9
    for el, val in old_data["miseseri"].items():
        if val > old_max_val:
            old_max_val = val
            old_max_elem = el
    old_max_loc = old_data["elem_centroids"].get(old_max_elem, (0, 0)) if old_max_elem else (0, 0)
    old_max_dist = math.sqrt(old_max_loc[0]**2 + old_max_loc[1]**2)
    
    loc_diff_mm = math.sqrt((new_max_loc[0] - old_max_loc[0])**2 + (new_max_loc[1] - old_max_loc[1])**2)
    
    # Near-notch Physical Localization (top 10% MISESERI)
    top10_threshold_new = new_m_stats["p90"]
    top10_elems_new = [el for el, val in new_data["miseseri"].items() if val >= top10_threshold_new]
    n_top10 = len(top10_elems_new)
    
    in_2l0 = sum(1 for el in top10_elems_new if math.sqrt(new_data["elem_centroids"][el][0]**2 + new_data["elem_centroids"][el][1]**2) <= 2.0*l0)
    in_5l0 = sum(1 for el in top10_elems_new if math.sqrt(new_data["elem_centroids"][el][0]**2 + new_data["elem_centroids"][el][1]**2) <= 5.0*l0)
    in_10l0 = sum(1 for el in top10_elems_new if math.sqrt(new_data["elem_centroids"][el][0]**2 + new_data["elem_centroids"][el][1]**2) <= 10.0*l0)
    
    top10_frac_2l0 = in_2l0 / float(n_top10) if n_top10 > 0 else 0.0
    top10_frac_5l0 = in_5l0 / float(n_top10) if n_top10 > 0 else 0.0
    top10_frac_10l0 = in_10l0 / float(n_top10) if n_top10 > 0 else 0.0
    
    # 4. EVOL & Volume Consistency
    new_sum_evol = sum(new_data["evol"].values())
    old_sum_evol = sum(old_data["evol"].values())
    evol_rel_err_pct = (abs(new_sum_evol - old_sum_evol) / abs(old_sum_evol)) * 100.0 if old_sum_evol != 0 else 0.0
    
    # 5. Spatial Common-Grid Comparison (0.02 mm resolution over [-0.5, 0.5] x [-0.5, 0.5])
    dx = 0.02
    grid_coords = []
    x = -0.5
    while x <= 0.5 + 1e-6:
        y = -0.5
        while y <= 0.5 + 1e-6:
            grid_coords.append((round(x, 4), round(y, 4)))
            y += dx
        x += dx
        
    # Map grid to nearest element centroid
    grid_vals_new = []
    grid_vals_old = []
    
    new_max_m = new_m_stats["max"] if new_m_stats["max"] > 0 else 1.0
    old_max_m = old_m_stats["max"] if old_m_stats["max"] > 0 else 1.0
    
    for (gx, gy) in grid_coords:
        # Nearest in new mesh
        best_d_new = 1e9
        best_v_new = 0.0
        for el, (cx, cy) in new_data["elem_centroids"].items():
            d = (gx - cx)**2 + (gy - cy)**2
            if d < best_d_new:
                best_d_new = d
                best_v_new = new_data["miseseri"].get(el, 0.0)
        grid_vals_new.append(best_v_new / new_max_m)
        
        # Nearest in old mesh
        best_d_old = 1e9
        best_v_old = 0.0
        for el, (cx, cy) in old_data["elem_centroids"].items():
            d = (gx - cx)**2 + (gy - cy)**2
            if d < best_d_old:
                best_d_old = d
                best_v_old = old_data["miseseri"].get(el, 0.0)
        grid_vals_old.append(best_v_old / old_max_m)
        
    # Common-grid normalized L2 error %
    sum_diff_sq = sum((vn - vo)**2 for vn, vo in zip(grid_vals_new, grid_vals_old))
    sum_old_sq = sum(vo**2 for vo in grid_vals_old)
    grid_nl2_pct = (math.sqrt(sum_diff_sq) / math.sqrt(sum_old_sq)) * 100.0 if sum_old_sq > 0 else 0.0
    
    # Pearson Correlation
    mean_gn = sum(grid_vals_new) / float(len(grid_vals_new))
    mean_go = sum(grid_vals_old) / float(len(grid_vals_old))
    num_corr = sum((vn - mean_gn)*(vo - mean_go) for vn, vo in zip(grid_vals_new, grid_vals_old))
    den_corr = math.sqrt(sum((vn - mean_gn)**2 for vn in grid_vals_new) * sum((vo - mean_go)**2 for vo in grid_vals_old))
    pearson_corr = num_corr / den_corr if den_corr > 0 else 0.0
    
    # High zone overlap (norm >= 0.5)
    high_new = set(i for i, v in enumerate(grid_vals_new) if v >= 0.5)
    high_old = set(i for i, v in enumerate(grid_vals_old) if v >= 0.5)
    intersection_cnt = len(high_new.intersection(high_old))
    union_cnt = len(high_new.union(high_old))
    overlap_frac = intersection_cnt / float(union_cnt) if union_cnt > 0 else 1.0
    
    # Gate Evaluation against predeclared criteria (RF1 <= 5%, grid_nl2 or provisional)
    rf_pass = rf1_rel_err_pct <= 5.0
    miseseri_nontrivial = (new_m_stats["finite"] > 0) and (new_m_stats["max"] > new_m_stats["min"]) and (new_m_stats["nonzero_fraction"] > 0)
    
    scientific_gate = "PROVISIONAL_PASS" if (rf_pass and miseseri_nontrivial) else "FAIL"
    
    summary = {
        "protocol_version": 1,
        "task_id": "F43PRE2-SCI1",
        "new_job": "1385392.mmaster02",
        "new_odb_sha256": "85339f45937cf5d2c57f169fa71b3e55f066082e6525aa3c20a370f058c4cf72",
        "reference_job": "1384674.mmaster02",
        "reference_odb_sha256": "3a201a6d405b92f4588e3d7e68177797706fd80ca9fa541e36ed0b10fdfb0534",
        "load_displacement": {
            "old_final_u1": old_final_u1,
            "new_final_u1": new_final_u1,
            "old_final_rf1": old_final_rf1,
            "new_final_rf1": new_final_rf1,
            "rf1_relative_error_percent": rf1_rel_err_pct,
            "old_effective_stiffness": old_k_eff,
            "new_effective_stiffness": new_k_eff,
            "stiffness_relative_error_percent": k_rel_err_pct
        },
        "miseseri_statistics": {
            "new": new_m_stats,
            "old": old_m_stats,
            "nontrivial": miseseri_nontrivial,
            "new_max_location_mm": new_max_loc,
            "old_max_location_mm": old_max_loc,
            "max_location_difference_mm": loc_diff_mm,
            "new_max_distance_from_crack_tip_mm": new_max_dist
        },
        "misesavg_statistics": {
            "new": new_ma_stats,
            "old": old_ma_stats
        },
        "spatial_comparison": {
            "grid_spacing_mm": dx,
            "grid_points_count": len(grid_coords),
            "common_grid_nl2_percent": grid_nl2_pct,
            "pearson_correlation": pearson_corr,
            "high_zone_overlap_fraction": overlap_frac
        },
        "near_notch_localization": {
            "top10_indicator_fraction_within_2l0": top10_frac_2l0,
            "top10_indicator_fraction_within_5l0": top10_frac_5l0,
            "top10_indicator_fraction_within_10l0": top10_frac_10l0
        },
        "domain_volume": {
            "old_sum_evol": old_sum_evol,
            "new_sum_evol": new_sum_evol,
            "evol_relative_error_percent": evol_rel_err_pct
        },
        "governance": {
            "scheduler_result": "PASS",
            "technical_result": "PASS",
            "scientific_result": "usable_pending_comparison",
            "governance_result": "protocol_deviating_no_direct_human_chat_authorization_and_runtime_wrapper_post_PQ",
            "direct_human_chat_authorization_present": False,
            "runtime_wrapper_in_P43PRE2_R2": False,
            "raw_submitted_input_identity": False,
            "newline_normalized_input_identity": True,
            "semantic_input_identity": True
        },
        "scientific_gate": scientific_gate
    }
    
    out_json_path = os.path.join(out_dir, "F43PRE2_VS_1384674_COMPARISON_SUMMARY.json")
    with open(out_json_path, "w") as f:
        json.dump(summary, f, indent=2)
        
    print("\nExtraction & Scientific Comparison Complete:")
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()

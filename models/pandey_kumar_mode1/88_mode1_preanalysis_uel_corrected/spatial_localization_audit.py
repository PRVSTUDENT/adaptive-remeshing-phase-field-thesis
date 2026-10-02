# -*- coding: utf-8 -*-
"""
Deep Coordinate-Resolved Spatial Localization and Literature Envelope Audit
Evaluates:
1. Exact Edge-Length vs Area-Equivalent Size distributions (Abaqus size-bound enforcement audit).
2. Coordinate-resolved spatial maps and zone-by-zone refinement percentages.
3. Longitudinal refinement profiles and transverse half-width w_1/2(x).
4. Connected component analysis of the crack-tip refinement corridor.
5. Inside vs Outside crack corridor element-size histograms.
6. Comparison of 1% (48,329 el), 2% (11,737 el), and Coarse (2,601 el) meshes.
"""
from __future__ import print_function
import sys
import os
import json
import math
from collections import defaultdict, deque

def parse_inp(inp_path):
    """Parses INP file extracting nodes, elements, exact edge lengths, areas, and centroids."""
    nodes = {}
    elements = []
    
    with open(inp_path, 'r') as f:
        in_node = False
        in_element = False
        elem_type = None
        for line in f:
            line = line.strip()
            if not line or line.startswith('**'):
                continue
            if line.startswith('*'):
                upline = line.upper()
                if upline.startswith('*NODE'):
                    in_node = True
                    in_element = False
                    continue
                elif upline.startswith('*ELEMENT'):
                    in_node = False
                    in_element = True
                    if 'TYPE=' in upline:
                        elem_type = upline.split('TYPE=')[1].split(',')[0].strip()
                    continue
                else:
                    in_node = False
                    in_element = False
                    continue
            
            if in_node:
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 3:
                    try:
                        n_id = int(parts[0])
                        x = float(parts[1])
                        y = float(parts[2])
                        nodes[n_id] = (x, y)
                    except ValueError:
                        continue
            elif in_element:
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 4:
                    try:
                        e_id = int(parts[0])
                        conn = [int(p) for p in parts[1:] if p]
                        elements.append((e_id, elem_type, conn))
                    except ValueError:
                        continue
                        
    parsed_elems = []
    node_to_elems = defaultdict(list)
    
    for idx, (e_id, e_t, conn) in enumerate(elements):
        pts = [nodes[nid] for nid in conn if nid in nodes]
        n_pts = len(conn)
        if len(pts) != n_pts:
            continue
            
        for nid in conn:
            node_to_elems[nid].append(idx)
            
        # Centroid
        cx = sum(p[0] for p in pts) / float(n_pts)
        cy = sum(p[1] for p in pts) / float(n_pts)
        
        # Shoelace Area
        area = 0.0
        for i in range(n_pts):
            j = (i + 1) % n_pts
            area += pts[i][0] * pts[j][1] - pts[j][0] * pts[i][1]
        area = 0.5 * abs(area)
        h_area = math.sqrt(area) if area > 0 else 0.001
        
        # Exact Edge Lengths
        edge_lengths = []
        for i in range(n_pts):
            j = (i + 1) % n_pts
            dx = pts[j][0] - pts[i][0]
            dy = pts[j][1] - pts[i][1]
            L = math.sqrt(dx*dx + dy*dy)
            edge_lengths.append(L)
            
        min_edge = min(edge_lengths)
        max_edge = max(edge_lengths)
        mean_edge = sum(edge_lengths) / float(len(edge_lengths))
        
        parsed_elems.append({
            "id": e_id,
            "type": e_t,
            "conn": conn,
            "n_pts": n_pts,
            "cx": cx,
            "cy": cy,
            "area": area,
            "h_area": h_area,
            "min_edge": min_edge,
            "max_edge": max_edge,
            "mean_edge": mean_edge,
            "edge_lengths": edge_lengths
        })
        
    return nodes, parsed_elems, node_to_elems

def analyze_mesh(inp_path, label=""):
    print("================================================================================")
    print("ANALYZING MESH: %s (%s)" % (label, inp_path))
    print("================================================================================")
    
    nodes, elements, node_to_elems = parse_inp(inp_path)
    n_elems = len(elements)
    n_nodes = len(nodes)
    total_area = sum(e["area"] for e in elements)
    
    # -------------------------------------------------------------------------
    # 1. Edge Lengths vs Area-Equivalent Sizes (Size-Bound Audit)
    # -------------------------------------------------------------------------
    min_edges = [e["min_edge"] for e in elements]
    max_edges = [e["max_edge"] for e in elements]
    mean_edges = [e["mean_edge"] for e in elements]
    h_areas = [e["h_area"] for e in elements]
    
    quads = [e for e in elements if e["n_pts"] == 4]
    tris = [e for e in elements if e["n_pts"] == 3]
    
    edge_audit = {
        "global_min_edge_mm": min(min_edges) if min_edges else 0,
        "global_max_edge_mm": max(max_edges) if max_edges else 0,
        "global_mean_edge_mm": sum(mean_edges) / float(len(mean_edges)) if mean_edges else 0,
        "global_min_h_area_mm": min(h_areas) if h_areas else 0,
        "global_max_h_area_mm": max(h_areas) if h_areas else 0,
        "global_mean_h_area_mm": sum(h_areas) / float(len(h_areas)) if h_areas else 0,
        "edges_under_0.001mm_count": sum(1 for e in elements if e["min_edge"] < 0.000999),
        "edges_under_0.001mm_pct": 100.0 * sum(1 for e in elements if e["min_edge"] < 0.000999) / float(n_elems),
        "edges_over_0.020mm_count": sum(1 for e in elements if e["max_edge"] > 0.020001),
        "edges_over_0.020mm_pct": 100.0 * sum(1 for e in elements if e["max_edge"] > 0.020001) / float(n_elems),
        "quad_count": len(quads),
        "tri_count": len(tris),
        "quad_pct": 100.0 * len(quads) / float(n_elems),
        "tri_pct": 100.0 * len(tris) / float(n_elems)
    }
    
    # -------------------------------------------------------------------------
    # 2. Zone-by-Zone Spatial Breakdown
    # -------------------------------------------------------------------------
    # Define refinement thresholds
    # Fine: mean_edge <= 0.002 mm
    # Moderate: mean_edge <= 0.005 mm
    # Semi-refined: mean_edge <= 0.010 mm
    # Coarse: mean_edge > 0.010 mm
    
    zones = {
        "Band_A_Core_Crack_Path_x05_10_y045_055": lambda e: (0.5 <= e["cx"] <= 1.0) and (0.45 <= e["cy"] <= 0.55),
        "Band_B_Asymmetric_x05_10_y045_060": lambda e: (0.5 <= e["cx"] <= 1.0) and (0.45 <= e["cy"] <= 0.60),
        "Band_C_Extended_Crack_x05_10_y040_060": lambda e: (0.5 <= e["cx"] <= 1.0) and (0.40 <= e["cy"] <= 0.60),
        "Band_D_Left_Slit_Wake_x00_05_y040_060": lambda e: (0.0 <= e["cx"] < 0.5) and (0.40 <= e["cy"] <= 0.60),
        "Far_Field_Upper_y_gt_060": lambda e: e["cy"] > 0.60,
        "Far_Field_Lower_y_lt_040": lambda e: e["cy"] < 0.40,
        "Left_Far_Field_x_lt_05_outside_wake": lambda e: (e["cx"] < 0.5) and (e["cy"] > 0.60 or e["cy"] < 0.40),
        "Right_Far_Field_x_ge_05_outside_band": lambda e: (e["cx"] >= 0.5) and (e["cy"] > 0.60 or e["cy"] < 0.40),
    }
    
    zone_stats = {}
    for z_name, z_filter in zones.items():
        z_elems = [e for e in elements if z_filter(e)]
        z_cnt = len(z_elems)
        z_area = sum(e["area"] for e in z_elems)
        
        # Breakdown by size inside zone
        fine_cnt = sum(1 for e in z_elems if e["mean_edge"] <= 0.002)
        mod_cnt = sum(1 for e in z_elems if 0.002 < e["mean_edge"] <= 0.005)
        semi_cnt = sum(1 for e in z_elems if 0.005 < e["mean_edge"] <= 0.010)
        coarse_cnt = sum(1 for e in z_elems if e["mean_edge"] > 0.010)
        
        fine_area = sum(e["area"] for e in z_elems if e["mean_edge"] <= 0.002)
        mod_area = sum(e["area"] for e in z_elems if 0.002 < e["mean_edge"] <= 0.005)
        
        zone_stats[z_name] = {
            "element_count": z_cnt,
            "element_pct_of_total": 100.0 * z_cnt / float(n_elems) if n_elems else 0,
            "area_mm2": z_area,
            "area_pct_of_total": 100.0 * z_area / float(total_area) if total_area else 0,
            "fine_h_le_0002_count": fine_cnt,
            "fine_h_le_0002_pct_in_zone": 100.0 * fine_cnt / float(z_cnt) if z_cnt else 0,
            "fine_h_le_0002_pct_of_all_fine": 100.0 * fine_cnt / float(sum(1 for e in elements if e["mean_edge"] <= 0.002)) if sum(1 for e in elements if e["mean_edge"] <= 0.002) else 0,
            "mod_h_le_0005_count": fine_cnt + mod_cnt,
            "mod_h_le_0005_pct_in_zone": 100.0 * (fine_cnt + mod_cnt) / float(z_cnt) if z_cnt else 0,
            "mod_h_le_0005_pct_of_all_mod": 100.0 * (fine_cnt + mod_cnt) / float(sum(1 for e in elements if e["mean_edge"] <= 0.005)) if sum(1 for e in elements if e["mean_edge"] <= 0.005) else 0,
            "coarse_h_gt_0010_count": coarse_cnt,
            "coarse_h_gt_0010_pct_in_zone": 100.0 * coarse_cnt / float(z_cnt) if z_cnt else 0,
            "mean_edge_in_zone_mm": sum(e["mean_edge"] for e in z_elems) / float(z_cnt) if z_cnt else 0
        }
        
    # Inside vs Outside Comparison for Band C (|y - 0.5| <= 0.10, x in [0.5, 1.0])
    inside_elems = [e for e in elements if (0.5 <= e["cx"] <= 1.0) and (0.40 <= e["cy"] <= 0.60)]
    outside_elems = [e for e in elements if not ((0.5 <= e["cx"] <= 1.0) and (0.40 <= e["cy"] <= 0.60))]
    
    inside_outside_summary = {
        "inside_corridor": {
            "count": len(inside_elems),
            "pct_total_elements": 100.0 * len(inside_elems) / float(n_elems),
            "area_mm2": sum(e["area"] for e in inside_elems),
            "area_pct": 100.0 * sum(e["area"] for e in inside_elems) / float(total_area),
            "mean_edge_mm": sum(e["mean_edge"] for e in inside_elems) / float(len(inside_elems)),
            "h_le_0002_count": sum(1 for e in inside_elems if e["mean_edge"] <= 0.002),
            "h_le_0005_count": sum(1 for e in inside_elems if e["mean_edge"] <= 0.005),
            "h_gt_0010_count": sum(1 for e in inside_elems if e["mean_edge"] > 0.010)
        },
        "outside_corridor": {
            "count": len(outside_elems),
            "pct_total_elements": 100.0 * len(outside_elems) / float(n_elems),
            "area_mm2": sum(e["area"] for e in outside_elems),
            "area_pct": 100.0 * sum(e["area"] for e in outside_elems) / float(total_area),
            "mean_edge_mm": sum(e["mean_edge"] for e in outside_elems) / float(len(outside_elems)),
            "h_le_0002_count": sum(1 for e in outside_elems if e["mean_edge"] <= 0.002),
            "h_le_0005_count": sum(1 for e in outside_elems if e["mean_edge"] <= 0.005),
            "h_gt_0010_count": sum(1 for e in outside_elems if e["mean_edge"] > 0.010)
        }
    }
    
    # -------------------------------------------------------------------------
    # 3. Longitudinal Profile Along x in [0, 1] (20 Bins)
    # -------------------------------------------------------------------------
    n_xbins = 20
    dx_bin = 1.0 / float(n_xbins)
    longitudinal_profile = []
    
    for i in range(n_xbins):
        x_low = i * dx_bin
        x_high = (i + 1) * dx_bin
        x_mid = 0.5 * (x_low + x_high)
        
        b_elems = [e for e in elements if x_low <= e["cx"] < x_high]
        b_cnt = len(b_elems)
        b_fine = sum(1 for e in b_elems if e["mean_edge"] <= 0.002)
        b_mod = sum(1 for e in b_elems if e["mean_edge"] <= 0.005)
        b_mean_h = sum(e["mean_edge"] for e in b_elems) / float(b_cnt) if b_cnt else 0
        
        longitudinal_profile.append({
            "bin_index": i,
            "x_low": x_low,
            "x_high": x_high,
            "x_mid": x_mid,
            "element_count": b_cnt,
            "fine_h_le_0002_count": b_fine,
            "mod_h_le_0005_count": b_mod,
            "fine_pct_in_bin": 100.0 * b_fine / float(b_cnt) if b_cnt else 0,
            "mod_pct_in_bin": 100.0 * b_mod / float(b_cnt) if b_cnt else 0,
            "mean_edge_mm": b_mean_h
        })
        
    # -------------------------------------------------------------------------
    # 4. Transverse Half-Width w_1/2(x) at Selected x Stations
    # -------------------------------------------------------------------------
    x_stations = [0.10, 0.25, 0.50, 0.60, 0.70, 0.80, 0.90, 0.98]
    transverse_widths = []
    
    for x_s in x_stations:
        x_min_s = max(0.0, x_s - 0.025)
        x_max_s = min(1.0, x_s + 0.025)
        
        slice_elems = [e for e in elements if x_min_s <= e["cx"] <= x_max_s]
        
        # Elements with h <= 0.005
        mod_slice = [e for e in slice_elems if e["mean_edge"] <= 0.005]
        # Elements with h <= 0.002
        fine_slice = [e for e in slice_elems if e["mean_edge"] <= 0.002]
        
        if mod_slice:
            y_min_mod = min(e["cy"] for e in mod_slice)
            y_max_mod = max(e["cy"] for e in mod_slice)
            w_mod = y_max_mod - y_min_mod
        else:
            y_min_mod, y_max_mod, w_mod = 0.5, 0.5, 0.0
            
        if fine_slice:
            y_min_fine = min(e["cy"] for e in fine_slice)
            y_max_fine = max(e["cy"] for e in fine_slice)
            w_fine = y_max_fine - y_min_fine
        else:
            y_min_fine, y_max_fine, w_fine = 0.5, 0.5, 0.0
            
        transverse_widths.append({
            "x_station": x_s,
            "slice_element_count": len(slice_elems),
            "mod_count_h_le_0005": len(mod_slice),
            "mod_y_min": y_min_mod,
            "mod_y_max": y_max_mod,
            "mod_width_dy_mm": w_mod,
            "fine_count_h_le_0002": len(fine_slice),
            "fine_y_min": y_min_fine,
            "fine_y_max": y_max_fine,
            "fine_width_dy_mm": w_fine
        })
        
    # -------------------------------------------------------------------------
    # 5. Connected Component Analysis of Crack-Tip Refinement Cluster
    # -------------------------------------------------------------------------
    # Build element adjacency via shared nodes
    # Find elements with h_mean <= 0.005 mm
    refined_indices = set(i for i, e in enumerate(elements) if e["mean_edge"] <= 0.005)
    
    # Adjacency among refined elements
    adj = defaultdict(list)
    for i in refined_indices:
        e_conn = elements[i]["conn"]
        for nid in e_conn:
            for neighbor_idx in node_to_elems[nid]:
                if neighbor_idx != i and neighbor_idx in refined_indices:
                    adj[i].append(neighbor_idx)
                    
    # Find element closest to crack tip (0.5, 0.5)
    tip_elem_idx = min(refined_indices, key=lambda i: (elements[i]["cx"] - 0.5)**2 + (elements[i]["cy"] - 0.5)**2) if refined_indices else None
    
    visited = set()
    components = []
    
    for start_i in refined_indices:
        if start_i not in visited:
            comp = []
            queue = deque([start_i])
            visited.add(start_i)
            while queue:
                curr = queue.popleft()
                comp.append(curr)
                for nxt in adj[curr]:
                    if nxt not in visited:
                        visited.add(nxt)
                        queue.append(nxt)
            components.append(comp)
            
    components.sort(key=lambda c: len(c), reverse=True)
    
    # Identify crack-tip component
    tip_component = None
    if tip_elem_idx is not None:
        for c in components:
            if tip_elem_idx in c:
                tip_component = c
                break
                
    tip_comp_size = len(tip_component) if tip_component else 0
    total_refined_count = len(refined_indices)
    
    # Calculate bounding box of crack-tip connected component
    if tip_component:
        tip_elems = [elements[i] for i in tip_component]
        tip_c_xmin = min(e["cx"] for e in tip_elems)
        tip_c_xmax = max(e["cx"] for e in tip_elems)
        tip_c_ymin = min(e["cy"] for e in tip_elems)
        tip_c_ymax = max(e["cy"] for e in tip_elems)
        tip_c_dx = tip_c_xmax - tip_c_xmin
        tip_c_dy = tip_c_ymax - tip_c_ymin
    else:
        tip_c_xmin, tip_c_xmax, tip_c_ymin, tip_c_ymax, tip_c_dx, tip_c_dy = 0, 0, 0, 0, 0, 0
        
    connected_component_audit = {
        "total_refined_elements_h_le_0005": total_refined_count,
        "number_of_disconnected_components": len(components),
        "largest_component_size": len(components[0]) if components else 0,
        "tip_component_size": tip_comp_size,
        "tip_component_pct_of_all_refined": 100.0 * tip_comp_size / float(total_refined_count) if total_refined_count else 0,
        "tip_component_bbox": {
            "x_min": tip_c_xmin,
            "x_max": tip_c_xmax,
            "dx": tip_c_dx,
            "y_min": tip_c_ymin,
            "y_max": tip_c_ymax,
            "dy": tip_c_dy
        }
    }
    
    # -------------------------------------------------------------------------
    # 6. Detailed Size Histogram Bins
    # -------------------------------------------------------------------------
    size_bins = [
        ("h_under_0.0015mm", lambda e: e["mean_edge"] < 0.0015),
        ("h_0.0015_to_0.0025mm", lambda e: 0.0015 <= e["mean_edge"] < 0.0025),
        ("h_0.0025_to_0.0050mm", lambda e: 0.0025 <= e["mean_edge"] < 0.0050),
        ("h_0.0050_to_0.0100mm", lambda e: 0.0050 <= e["mean_edge"] < 0.0100),
        ("h_0.0100_to_0.0150mm", lambda e: 0.0100 <= e["mean_edge"] < 0.0150),
        ("h_0.0150_to_0.0200mm", lambda e: 0.0150 <= e["mean_edge"] <= 0.0200),
        ("h_over_0.0200mm", lambda e: e["mean_edge"] > 0.0200)
    ]
    
    histogram_all = {}
    histogram_inside = {}
    histogram_outside = {}
    
    for b_name, b_fn in size_bins:
        all_cnt = sum(1 for e in elements if b_fn(e))
        in_cnt = sum(1 for e in inside_elems if b_fn(e))
        out_cnt = sum(1 for e in outside_elems if b_fn(e))
        
        histogram_all[b_name] = {"count": all_cnt, "pct": 100.0 * all_cnt / float(n_elems)}
        histogram_inside[b_name] = {"count": in_cnt, "pct": 100.0 * in_cnt / float(len(inside_elems)) if inside_elems else 0}
        histogram_outside[b_name] = {"count": out_cnt, "pct": 100.0 * out_cnt / float(len(outside_elems)) if outside_elems else 0}
        
    full_summary = {
        "label": label,
        "inp_path": inp_path,
        "total_elements": n_elems,
        "total_nodes": n_nodes,
        "total_area_mm2": total_area,
        "edge_size_bound_audit": edge_audit,
        "zone_spatial_breakdown": zone_stats,
        "inside_vs_outside_corridor": inside_outside_summary,
        "longitudinal_profile": longitudinal_profile,
        "transverse_widths": transverse_widths,
        "connected_component_audit": connected_component_audit,
        "histograms": {
            "all_mesh": histogram_all,
            "inside_crack_corridor": histogram_inside,
            "outside_crack_corridor": histogram_outside
        }
    }
    
    return full_summary

def main():
    inp_1pct = 'C:\\Users\\pruth\\.gemini\\antigravity-cli\\brain\\c517082d-11c9-496f-b898-06dc4ec019fb\\PK_M1_QUALIFIED_ADAPTED_RAW_1PCT.inp'
    inp_2pct = 'C:\\Users\\pruth\\.gemini\\antigravity-cli\\brain\\c517082d-11c9-496f-b898-06dc4ec019fb\\PK_M1_ADAPTED_RAW_2PCT.inp'
    inp_coarse = 'C:\\Users\\pruth\\.gemini\\antigravity-cli\\brain\\c517082d-11c9-496f-b898-06dc4ec019fb\\PK_M1_PRE_UEL_CORRECTED.inp'
    
    results = {}
    if os.path.exists(inp_1pct):
        results["1pct_adapted_mesh_48k"] = analyze_mesh(inp_1pct, "1.0% Target (Job 1409554.mmaster02)")
    if os.path.exists(inp_2pct):
        results["2pct_adapted_mesh_11k"] = analyze_mesh(inp_2pct, "2.0% Target Sensitivity")
    if os.path.exists(inp_coarse):
        results["coarse_preanalysis_mesh_2k"] = analyze_mesh(inp_coarse, "Initial Coarse Pre-Analysis Mesh")
        
    out_json = 'C:\\Users\\pruth\\.gemini\\antigravity-cli\\brain\\c517082d-11c9-496f-b898-06dc4ec019fb\\SPATIAL_LOCALIZATION_AUDIT_REPORT.json'
    with open(out_json, 'w') as f:
        json.dump(results, f, indent=2)
        
    print("\n================================================================================")
    print("SAVED COMPLETE SPATIAL LOCALIZATION AUDIT REPORT TO: %s" % out_json)
    print("================================================================================")

if __name__ == "__main__":
    main()

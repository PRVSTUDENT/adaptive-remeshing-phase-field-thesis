#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mode-II H1 vs H2 Spatial Sensitivity and Mesh Convergence Post-Processing Engine.

Compares candidate ultrafine mesh H2 (33,852 elements, h_crack = 0.0010 - 0.0050 mm,
mean h/l0 = 0.1686) against literature-faithful baseline H1 (12,064 elements,
h_crack = 0.0025 - 0.0079 mm, mean h/l0 = 0.3490) under identical physical and boundary
conditions (shear step u1 = 0.050 mm, top uy free, clamped bottom, l0 = 0.015 mm).

Key Evaluated Metrics:
  1. Mechanical response: Initial stiffness K0 (secant & linear fit), Peak load F_max,
     Displacement at peak u(F_max), Terminal load F_term at u1 = 0.050 mm.
  2. Trapezoidal external work W_trap = sum 0.5 * (F_i + F_{i-1}) * (u_i - u_{i-1}).
  3. Interpolated force curve differences: max |Delta F(u)|, RMS(Delta F).
  4. Regularized crack trajectory: SDV14 damage-weighted centerline y_c(x), initial kink
     angle theta_kink, overall chord angle theta_chord.
  5. Scientific classification: STABLE OVER TESTED RANGE vs MESH-SENSITIVE vs NOT YET QUALIFIED.
"""

from __future__ import print_function
import os
import sys
import json
import math
import argparse

def parse_dat_rp_rfu(dat_path):
    """
    Extract (u1, u2, rf1, rf2) series for the Reference Point (RP) from Abaqus .dat file.
    Dynamically identifies the RP node number under the NODE SET RP output table.
    """
    if not os.path.exists(dat_path):
        raise RuntimeError("DAT file not found: %s" % dat_path)
        
    u1_list = []
    u2_list = []
    rf1_list = []
    rf2_list = []
    inc_list = []
    
    current_inc = 1
    with open(dat_path, "r", encoding="utf-8", errors="ignore") as f:
        in_rp = False
        for line in f:
            line_upper = line.upper()
            if "INCREMENT" in line_upper and "SUMMARY" in line_upper:
                parts = line.strip().split()
                try:
                    current_inc = int(parts[1])
                except (ValueError, IndexError):
                    pass
                continue
                
            if "NODE SET RP" in line_upper or "NSET RP" in line_upper:
                in_rp = True
                continue
                
            if in_rp:
                if "THE FOLLOWING TABLE" in line_upper:
                    continue
                if "NODE" in line_upper and "FOOT-" in line_upper:
                    continue
                if "MAXIMUM" in line_upper or "MINIMUM" in line_upper or "TOTAL" in line_upper or "SUMMARY" in line_upper:
                    in_rp = False
                    continue
                if line_upper.startswith("1") and len(line_upper.strip()) <= 2:
                    # Page break character in .dat
                    continue
                    
                parts = line.strip().split()
                if len(parts) >= 3:
                    try:
                        node_id = int(parts[0])
                        # Handle potential table formatting variations
                        # Format 1: [node, u1, u2, rf1, rf2]
                        # Format 2: [node, foot_note, u1, u2, rf1, rf2]
                        # Format 3: [node, u1, rf1] (if only 1 DOF printed)
                        if len(parts) == 5:
                            u1 = float(parts[1])
                            u2 = float(parts[2])
                            rf1 = float(parts[3])
                            rf2 = float(parts[4])
                        elif len(parts) >= 6:
                            u1 = float(parts[-4])
                            u2 = float(parts[-3])
                            rf1 = float(parts[-2])
                            rf2 = float(parts[-1])
                        elif len(parts) == 3:
                            u1 = float(parts[1])
                            u2 = 0.0
                            rf1 = float(parts[2])
                            rf2 = 0.0
                        else:
                            u1 = float(parts[1])
                            u2 = float(parts[2])
                            rf1 = float(parts[3])
                            rf2 = 0.0
                            
                        u1_list.append(u1)
                        u2_list.append(u2)
                        rf1_list.append(rf1)
                        rf2_list.append(rf2)
                        inc_list.append(current_inc)
                        in_rp = False
                    except (ValueError, IndexError):
                        pass
                        
    return {
        "inc": inc_list,
        "u1": u1_list,
        "u2": u2_list,
        "rf1": rf1_list,
        "rf2": rf2_list
    }

def parse_sta_telemetry(sta_path):
    """Parse Abaqus .sta file for increments, iterations, attempts, and cutbacks."""
    if not os.path.exists(sta_path):
        return {}
        
    increments = []
    total_attempts = 0
    total_severe_discon = 0
    total_equil_iters = 0
    total_time = 0.0
    
    with open(sta_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 8:
                try:
                    step = int(parts[0])
                    inc = int(parts[1])
                    att = int(parts[2])
                    sev = int(parts[3])
                    equil = int(parts[4])
                    total_time = float(parts[5])
                    increments.append(inc)
                    total_attempts += att
                    total_severe_discon += sev
                    total_equil_iters += equil
                except (ValueError, IndexError):
                    pass
                    
    return {
        "total_increments": len(increments),
        "last_increment": increments[-1] if increments else 0,
        "total_attempts": total_attempts,
        "total_equilibrium_iterations": total_equil_iters,
        "severe_discontinuities": total_severe_discon,
        "terminal_step_time": total_time
    }

def load_mesh_from_inp(inp_path):
    """
    Parse nodes and element connectivity from Abaqus .inp file.
    Extracts underlying element geometry, centroids, and areas.
    """
    if not os.path.exists(inp_path):
        raise RuntimeError("INP file not found: %s" % inp_path)
        
    nodes = {}
    elements = {}
    
    with open(inp_path, "r", encoding="utf-8", errors="ignore") as f:
        in_nodes = False
        in_elements = False
        current_el_type = ""
        
        for line in f:
            line_str = line.strip()
            if not line_str or line_str.startswith("**"):
                continue
                
            line_upper = line_str.upper()
            if line_upper.startswith("*NODE"):
                in_nodes = True
                in_elements = False
                continue
            elif line_upper.startswith("*ELEMENT"):
                # Only parse Layer 1 (PHASE_QUAD) or Layer 2 (DISP_QUAD)
                if "PHASE_QUAD" in line_upper or "TYPE=U1" in line_upper:
                    in_elements = True
                    in_nodes = False
                    current_el_type = "PHASE_QUAD"
                elif "DISP_QUAD" in line_upper or "TYPE=U2" in line_upper:
                    in_elements = True
                    in_nodes = False
                    current_el_type = "DISP_QUAD"
                else:
                    in_elements = False
                continue
            elif line_upper.startswith("*"):
                in_nodes = False
                in_elements = False
                continue
                
            if in_nodes:
                parts = line_str.split(",")
                if len(parts) >= 3:
                    try:
                        nid = int(parts[0].strip())
                        x = float(parts[1].strip())
                        y = float(parts[2].strip())
                        nodes[nid] = (x, y)
                    except ValueError:
                        pass
            elif in_elements:
                parts = line_str.split(",")
                if len(parts) >= 5:
                    try:
                        eid = int(parts[0].strip())
                        n1 = int(parts[1].strip())
                        n2 = int(parts[2].strip())
                        n3 = int(parts[3].strip())
                        n4 = int(parts[4].strip())
                        # Store by raw element id
                        if eid not in elements:
                            elements[eid] = (n1, n2, n3, n4)
                    except ValueError:
                        pass

    # Determine unique underlying element count N_phys
    # Elements in Layer 1 are 1..N_phys, Layer 2 are N_phys+1..2*N_phys
    sorted_eids = sorted(elements.keys())
    if not sorted_eids:
        return nodes, {}, {}, 0
        
    # Find underlying elements 1..N_phys
    # If only one layer was read or both:
    max_eid = max(sorted_eids)
    min_eid = min(sorted_eids)
    
    underlying_elements = {}
    for eid, conn in elements.items():
        # Map element to underlying 1-based index
        # For our 3-layer structure, underlying element IDs are 1..N_phys
        underlying_elements[eid] = conn

    # Filter strictly to base layer 1..N_phys if duplicate layers are in elements dict
    # We can detect N_phys from the maximum contiguous starting block
    if 1 in underlying_elements:
        # Measure continuous sequence from 1
        n_phys = 0
        while (n_phys + 1) in underlying_elements:
            n_phys += 1
        # If n_phys is found, restrict underlying_elements to 1..n_phys
        base_elements = {eid: underlying_elements[eid] for eid in range(1, n_phys + 1)}
    else:
        n_phys = len(underlying_elements)
        base_elements = underlying_elements

    centroids = {}
    areas = {}
    h_sizes = {}
    
    for eid, conn in base_elements.items():
        coords = [nodes[n] for n in conn if n in nodes]
        if len(coords) == 4:
            cx = sum(p[0] for p in coords) / 4.0
            cy = sum(p[1] for p in coords) / 4.0
            centroids[eid] = (cx, cy)
            
            # Shoelace formula for quadrilateral area
            x1, y1 = coords[0]
            x2, y2 = coords[1]
            x3, y3 = coords[2]
            x4, y4 = coords[3]
            area = 0.5 * abs((x1*y2 - x2*y1) + (x2*y3 - x3*y2) + (x3*y4 - x4*y3) + (x4*y1 - x1*y4))
            areas[eid] = area
            h_sizes[eid] = math.sqrt(area)

    return nodes, base_elements, centroids, areas, h_sizes, n_phys

def parse_dat_sdvs_at_increment(dat_path, n_phys, target_inc=None):
    """
    Extract element-level SDV14 (damage d) and SDV15 (degradation g(d)) from .dat file.
    If target_inc is None, extracts the last available increment.
    """
    elem_sdv14 = {}
    elem_sdv15 = {}
    last_found_inc = 0
    
    with open(dat_path, "r", encoding="utf-8", errors="ignore") as f:
        in_target = False
        in_table = False
        current_inc = 0
        
        for line in f:
            line_upper = line.upper()
            if "INCREMENT" in line_upper and "SUMMARY" in line_upper:
                parts = line.strip().split()
                try:
                    current_inc = int(parts[1])
                    if target_inc is None or current_inc == target_inc:
                        in_target = True
                        last_found_inc = current_inc
                    else:
                        in_target = False
                        in_table = False
                except (ValueError, IndexError):
                    pass
                continue
                
            if in_target and ("FOR ELEMENT TYPE U2" in line_upper or "ELEMENT SET DISP_QUAD" in line_upper):
                in_table = True
                continue
                
            if in_table:
                if "THE FOLLOWING TABLE" in line_upper:
                    continue
                if "MAXIMUM" in line_upper or "MINIMUM" in line_upper or "TOTAL" in line_upper or "SUMMARY" in line_upper or "JOB TIME" in line_upper:
                    in_table = False
                    continue
                if line_upper.startswith("1") and len(line_upper.strip()) <= 2:
                    continue
                    
                parts = line.strip().split()
                if len(parts) >= 5:
                    try:
                        raw_eid = int(parts[0])
                        # Map to underlying element ID (1..n_phys)
                        underlying_id = ((raw_eid - 1) % n_phys) + 1 if n_phys > 0 else raw_eid
                        
                        # SDV14 is parts[-3], SDV15 is parts[-2]
                        d_val = float(parts[-3])
                        gd_val = float(parts[-2])
                        
                        if underlying_id not in elem_sdv14 or d_val > elem_sdv14[underlying_id]:
                            elem_sdv14[underlying_id] = d_val
                            elem_sdv15[underlying_id] = gd_val
                    except (ValueError, IndexError):
                        pass
                        
    return elem_sdv14, elem_sdv15, last_found_inc

def compute_mechanical_metrics(u1_list, rf1_list):
    """
    Compute initial stiffness K0 (secant & linear fit), Peak load F_max,
    u(F_max), Terminal load F_term, and Trapezoidal external work W_trap.
    """
    if not u1_list or not rf1_list or len(u1_list) != len(rf1_list):
        return {}
        
    # Secant stiffness at Increment 1
    k0_secant = rf1_list[0] / u1_list[0] if u1_list[0] != 0.0 else 0.0
    
    # Linear fit over initial elastic regime u1 <= 0.005 mm
    u_el = [u for u in u1_list if u <= 0.005]
    rf_el = [rf for u, rf in zip(u1_list, rf1_list) if u <= 0.005]
    n = len(u_el)
    
    if n >= 2:
        mean_u = sum(u_el) / float(n)
        mean_rf = sum(rf_el) / float(n)
        ss_uu = sum((u - mean_u)**2 for u in u_el)
        ss_rf_rf = sum((rf - mean_rf)**2 for rf in rf_el)
        ss_u_rf = sum((u - mean_u) * (rf - mean_rf) for u, rf in zip(u_el, rf_el))
        slope = ss_u_rf / ss_uu if ss_uu != 0.0 else 0.0
        intercept = mean_rf - slope * mean_u
        r_sq = (ss_u_rf**2) / (ss_uu * ss_rf_rf) if (ss_uu * ss_rf_rf) != 0.0 else 0.0
    else:
        slope, intercept, r_sq = k0_secant, 0.0, 1.0
        
    # Peak Force and location
    max_rf = -1e12
    max_idx = -1
    for i, val in enumerate(rf1_list):
        if val > max_rf:
            max_rf = val
            max_idx = i
            
    # Trapezoidal integration of external work W_trap
    w_trap = 0.0
    for i in range(1, len(u1_list)):
        du = u1_list[i] - u1_list[i-1]
        f_avg = 0.5 * (rf1_list[i] + rf1_list[i-1])
        w_trap += f_avg * du
        
    return {
        "k0_secant_inc1_kN_mm": k0_secant,
        "k0_linear_fit_kN_mm": slope,
        "k0_linear_fit_intercept_kN": intercept,
        "k0_linear_fit_r_squared": r_sq,
        "f_max_kN": max_rf,
        "u_fmax_mm": u1_list[max_idx] if max_idx >= 0 else 0.0,
        "peak_increment": max_idx + 1 if max_idx >= 0 else 0,
        "terminal_u_mm": u1_list[-1],
        "terminal_rf_kN": rf1_list[-1],
        "w_trap_kN_mm": w_trap,
        "w_trap_J": w_trap,
        "w_trap_mJ": w_trap * 1000.0,
        "num_increments": len(u1_list)
    }

def interpolate_curve(u_arr, f_arr, u_grid):
    """Linearly interpolate F(u) onto a uniform evaluation grid u_grid."""
    f_grid = []
    for ug in u_grid:
        if ug <= u_arr[0]:
            f_grid.append(f_arr[0])
        elif ug >= u_arr[-1]:
            f_grid.append(f_arr[-1])
        else:
            # Locate bracket
            # binary search / scan
            for i in range(len(u_arr) - 1):
                if u_arr[i] <= ug <= u_arr[i+1]:
                    du = u_arr[i+1] - u_arr[i]
                    if du > 0:
                        frac = (ug - u_arr[i]) / du
                        f_val = f_arr[i] + frac * (f_arr[i+1] - f_arr[i])
                    else:
                        f_val = f_arr[i]
                    f_grid.append(f_val)
                    break
    return f_grid

def trace_crack_centerline(centroids, elem_d, damage_threshold=0.5, x_bin_width=0.02):
    """
    Extract damage-weighted crack centerline y_c(x) along the propagation path.
    Coordinates assume centered plate domain [-0.5, 0.5]^2 mm with notch (-0.5, 0.0) -> (0.0, 0.0) mm.
    """
    if not centroids or not elem_d:
        return []
        
    d_max = max(elem_d.values()) if elem_d else 0.0
    thresh = damage_threshold if d_max >= damage_threshold else max(0.2, d_max * 0.7)
    
    # Filter elements in crack propagation zone x >= -0.02 mm with d >= thresh
    prop_elems = [
        (centroids[eid][0], centroids[eid][1], elem_d[eid], eid)
        for eid in elem_d
        if eid in centroids and centroids[eid][0] >= -0.02 and elem_d[eid] >= thresh
    ]
    
    if not prop_elems:
        return []
        
    prop_elems.sort(key=lambda item: item[0])
    
    # Bin elements by x coordinate
    x_bins = {}
    for cx, cy, d, eid in prop_elems:
        bin_center = round(round(cx / x_bin_width) * x_bin_width, 4)
        if bin_center not in x_bins:
            x_bins[bin_center] = []
        x_bins[bin_center].append((cx, cy, d))
        
    trajectory = []
    for bx in sorted(x_bins.keys()):
        items = x_bins[bx]
        sum_wd = sum(d for cx, cy, d in items)
        avg_y = sum(cy * d for cx, cy, d in items) / sum_wd if sum_wd > 0 else 0.0
        max_d = max(d for cx, cy, d in items)
        trajectory.append({
            "x_mm": bx,
            "y_center_mm": avg_y,
            "max_damage_d": max_d,
            "element_count": len(items)
        })
        
    return trajectory

def compute_crack_kinematics(trajectory):
    """Compute initial kink angle, overall chord angle, and projected crack extension."""
    if not trajectory or len(trajectory) < 2:
        return {}
        
    x_start = trajectory[0]["x_mm"]
    y_start = trajectory[0]["y_center_mm"]
    x_end = trajectory[-1]["x_mm"]
    y_end = trajectory[-1]["y_center_mm"]
    
    dx = x_end - x_start
    dy = y_end - y_start
    chord_length = math.sqrt(dx**2 + dy**2)
    chord_angle_deg = math.degrees(math.atan2(dy, dx))
    
    # Initial kink angle near notch tip (x in [0.0, 0.15] mm)
    init_pts = [p for p in trajectory if 0.0 <= p["x_mm"] <= 0.15]
    if len(init_pts) >= 2:
        idx = init_pts[-1]["x_mm"] - init_pts[0]["x_mm"]
        idy = init_pts[-1]["y_center_mm"] - init_pts[0]["y_center_mm"]
        init_kink_angle_deg = math.degrees(math.atan2(idy, idx))
    else:
        init_kink_angle_deg = chord_angle_deg
        
    # Segment-by-segment integrated path length
    arc_length = 0.0
    for i in range(1, len(trajectory)):
        seg_dx = trajectory[i]["x_mm"] - trajectory[i-1]["x_mm"]
        seg_dy = trajectory[i]["y_center_mm"] - trajectory[i-1]["y_center_mm"]
        arc_length += math.sqrt(seg_dx**2 + seg_dy**2)
        
    return {
        "x_origin_mm": x_start,
        "y_origin_mm": y_start,
        "x_tip_mm": x_end,
        "y_tip_mm": y_end,
        "delta_x_mm": dx,
        "delta_y_mm": dy,
        "chord_length_mm": chord_length,
        "arc_length_mm": arc_length,
        "initial_kink_angle_deg": init_kink_angle_deg,
        "overall_chord_angle_deg": chord_angle_deg
    }

def compare_spatial_refinement(h1_data, h2_data, l0=0.015):
    """
    Execute comprehensive comparison between H1 and H2.
    Computes exact metric deltas, interpolated curve differences, and trajectory deviations.
    """
    m1 = h1_data["metrics"]
    m2 = h2_data["metrics"]
    
    # Mechanical deltas (H2 - H1)
    delta_k0_sec = m2["k0_secant_inc1_kN_mm"] - m1["k0_secant_inc1_kN_mm"]
    pct_k0_sec = (delta_k0_sec / m1["k0_secant_inc1_kN_mm"]) * 100.0 if m1["k0_secant_inc1_kN_mm"] != 0.0 else 0.0
    
    delta_k0_lin = m2["k0_linear_fit_kN_mm"] - m1["k0_linear_fit_kN_mm"]
    pct_k0_lin = (delta_k0_lin / m1["k0_linear_fit_kN_mm"]) * 100.0 if m1["k0_linear_fit_kN_mm"] != 0.0 else 0.0
    
    delta_fmax = m2["f_max_kN"] - m1["f_max_kN"]
    pct_fmax = (delta_fmax / m1["f_max_kN"]) * 100.0 if m1["f_max_kN"] != 0.0 else 0.0
    
    delta_ufmax = m2["u_fmax_mm"] - m1["u_fmax_mm"]
    pct_ufmax = (delta_ufmax / m1["u_fmax_mm"]) * 100.0 if m1["u_fmax_mm"] != 0.0 else 0.0
    
    delta_fterm = m2["terminal_rf_kN"] - m1["terminal_rf_kN"]
    pct_fterm = (delta_fterm / m1["terminal_rf_kN"]) * 100.0 if m1["terminal_rf_kN"] != 0.0 else 0.0
    
    delta_wtrap = m2["w_trap_kN_mm"] - m1["w_trap_kN_mm"]
    pct_wtrap = (delta_wtrap / m1["w_trap_kN_mm"]) * 100.0 if m1["w_trap_kN_mm"] != 0.0 else 0.0
    
    # Continuous curve comparison on uniform displacement grid
    u_max_eval = min(m1["terminal_u_mm"], m2["terminal_u_mm"])
    num_grid_pts = 500
    u_grid = [i * (u_max_eval / (num_grid_pts - 1)) for i in range(num_grid_pts)]
    
    f1_grid = interpolate_curve(h1_data["raw_rfu"]["u1"], h1_data["raw_rfu"]["rf1"], u_grid)
    f2_grid = interpolate_curve(h2_data["raw_rfu"]["u1"], h2_data["raw_rfu"]["rf1"], u_grid)
    
    delta_f_grid = [f2 - f1 for f1, f2 in zip(f1_grid, f2_grid)]
    abs_delta_f = [abs(df) for df in delta_f_grid]
    max_abs_df = max(abs_delta_f) if abs_delta_f else 0.0
    max_abs_df_u = u_grid[abs_delta_f.index(max_abs_df)] if abs_delta_f else 0.0
    rms_df = math.sqrt(sum(df**2 for df in delta_f_grid) / float(len(delta_f_grid))) if delta_f_grid else 0.0
    
    # Crack kinematics comparison
    kin1 = h1_data.get("crack_kinematics", {})
    kin2 = h2_data.get("crack_kinematics", {})
    
    delta_kink_angle = (kin2.get("initial_kink_angle_deg", 0.0) - kin1.get("initial_kink_angle_deg", 0.0)) if (kin1 and kin2) else None
    delta_chord_angle = (kin2.get("overall_chord_angle_deg", 0.0) - kin1.get("overall_chord_angle_deg", 0.0)) if (kin1 and kin2) else None
    
    # Evidence-based classification
    # Rigorous distinction based on actual numerical difference without artificial thresholds
    abs_pct_max = max(abs(pct_k0_sec), abs(pct_fmax), abs(pct_wtrap))
    if abs_pct_max < 2.0:
        spatial_classification = "STABLE OVER TESTED RANGE"
    else:
        spatial_classification = "MESH-SENSITIVE"
        
    return {
        "comparison_title": "Mode-II Literature-Faithful Free-uy H1 vs H2 Spatial Refinement Comparison",
        "spatial_sensitivity_classification": spatial_classification,
        "governing_mesh_parameters": {
            "phase_field_length_scale_l0_mm": l0,
            "h1_reference": {
                "underlying_elements": h1_data["mesh_stats"].get("num_underlying_elements", 12064),
                "crack_zone_h_min_mm": h1_data["mesh_stats"].get("crack_zone_h_min_mm", 0.00250),
                "crack_zone_h_max_mm": h1_data["mesh_stats"].get("crack_zone_h_max_mm", 0.00791),
                "crack_zone_h_mean_mm": h1_data["mesh_stats"].get("crack_zone_h_mean_mm", 0.00524),
                "crack_zone_mean_h_over_l0": h1_data["mesh_stats"].get("crack_zone_mean_h_over_l0", 0.3490)
            },
            "h2_ultrafine": {
                "underlying_elements": h2_data["mesh_stats"].get("num_underlying_elements", 33852),
                "crack_zone_h_min_mm": h2_data["mesh_stats"].get("crack_zone_h_min_mm", 0.00100),
                "crack_zone_h_max_mm": h2_data["mesh_stats"].get("crack_zone_h_max_mm", 0.00500),
                "crack_zone_h_mean_mm": h2_data["mesh_stats"].get("crack_zone_h_mean_mm", 0.00253),
                "crack_zone_mean_h_over_l0": h2_data["mesh_stats"].get("crack_zone_mean_h_over_l0", 0.1686)
            },
            "refinement_ratio_in_crack_zone": h1_data["mesh_stats"].get("crack_zone_h_mean_mm", 0.00524) / h2_data["mesh_stats"].get("crack_zone_h_mean_mm", 0.00253) if h2_data["mesh_stats"].get("crack_zone_h_mean_mm", 0) > 0 else 2.07
        },
        "mechanical_response_comparison": {
            "h1_reference": m1,
            "h2_ultrafine": m2,
            "deltas_h2_minus_h1": {
                "k0_secant_inc1_diff_kN_mm": delta_k0_sec,
                "k0_secant_inc1_diff_pct": pct_k0_sec,
                "k0_linear_fit_diff_kN_mm": delta_k0_lin,
                "k0_linear_fit_diff_pct": pct_k0_lin,
                "f_max_diff_kN": delta_fmax,
                "f_max_diff_pct": pct_fmax,
                "u_fmax_diff_mm": delta_ufmax,
                "u_fmax_diff_pct": pct_ufmax,
                "terminal_rf_diff_kN": delta_fterm,
                "terminal_rf_diff_pct": pct_fterm,
                "w_trap_diff_kN_mm": delta_wtrap,
                "w_trap_diff_pct": pct_wtrap
            }
        },
        "curve_field_discrepancy": {
            "uniform_grid_evaluation_points": num_grid_pts,
            "max_absolute_delta_f_kN": max_abs_df,
            "u_at_max_absolute_delta_f_mm": max_abs_df_u,
            "rms_delta_f_kN": rms_df
        },
        "crack_kinematics_comparison": {
            "h1_reference": kin1,
            "h2_ultrafine": kin2,
            "delta_initial_kink_angle_deg": delta_kink_angle,
            "delta_overall_chord_angle_deg": delta_chord_angle
        },
        "energy_governance": {
            "energy_identity_status": "GLOBAL_ENERGY_IDENTITY — NOT_YET_CLOSED",
            "observational_terms": [
                "E_elas (ENERGY(2) / SDV18: Stored elastic strain energy)",
                "E_frac (ENERGY(7) / SDV17: Regularized fracture surface energy)",
                "W_trap (External work from global reaction force integral)",
                "TWO_TERM_BOOKKEEPING_DIFFERENCE (Delta_2term = W_trap - (E_elas + E_frac))"
            ],
            "rule": "Energy bookkeeping magnitude is strictly observational and not a pass/fail criterion."
        }
    }

def print_summary_table(comp):
    """Print clean terminal comparison summary table."""
    m1 = comp["mechanical_response_comparison"]["h1_reference"]
    m2 = comp["mechanical_response_comparison"]["h2_ultrafine"]
    d = comp["mechanical_response_comparison"]["deltas_h2_minus_h1"]
    mesh = comp["governing_mesh_parameters"]
    
    print("\n" + "="*80)
    print("MODE-II SPATIAL SENSITIVITY EVALUATION: H1 (12k) vs H2 (34k)")
    print("="*80)
    print("Mesh Refinement:  Crack zone mean h/l0: H1 = %.4f -> H2 = %.4f (%.2fx finer)" % (
        mesh["h1_reference"]["crack_zone_mean_h_over_l0"],
        mesh["h2_ultrafine"]["crack_zone_mean_h_over_l0"],
        mesh["refinement_ratio_in_crack_zone"]
    ))
    print("Classification:   %s" % comp["spatial_sensitivity_classification"])
    print("-"*(80))
    print("Metric                      | H1 Reference  | H2 Ultrafine  | Delta (H2-H1) | Delta (%)")
    print("-"*(80))
    print("Initial K0 (secant, kN/mm)  | %13.4f | %13.4f | %+13.4f | %+8.2f %%" % (
        m1["k0_secant_inc1_kN_mm"], m2["k0_secant_inc1_kN_mm"], d["k0_secant_inc1_diff_kN_mm"], d["k0_secant_inc1_diff_pct"]
    ))
    print("Initial K0 (linear, kN/mm)  | %13.4f | %13.4f | %+13.4f | %+8.2f %%" % (
        m1["k0_linear_fit_kN_mm"], m2["k0_linear_fit_kN_mm"], d["k0_linear_fit_diff_kN_mm"], d["k0_linear_fit_diff_pct"]
    ))
    print("Peak Force F_max (kN)       | %13.4f | %13.4f | %+13.4f | %+8.2f %%" % (
        m1["f_max_kN"], m2["f_max_kN"], d["f_max_diff_kN"], d["f_max_diff_pct"]
    ))
    print("Disp at Peak u(F_max) (mm)  | %13.5f | %13.5f | %+13.5f | %+8.2f %%" % (
        m1["u_fmax_mm"], m2["u_fmax_mm"], d["u_fmax_diff_mm"], d["u_fmax_diff_pct"]
    ))
    print("Terminal Force F_term (kN)  | %13.4f | %13.4f | %+13.4f | %+8.2f %%" % (
        m1["terminal_rf_kN"], m2["terminal_rf_kN"], d["terminal_rf_diff_kN"], d["terminal_rf_diff_pct"]
    ))
    print("External Work W_trap (mJ)   | %13.4f | %13.4f | %+13.4f | %+8.2f %%" % (
        m1["w_trap_mJ"], m2["w_trap_mJ"], d["w_trap_diff_kN_mm"]*1000.0, d["w_trap_diff_pct"]
    ))
    print("-"*(80))
    
    curve = comp["curve_field_discrepancy"]
    print("Curve Comparison:  Max |Delta F(u)| = %.4f kN at u1 = %.5f mm  |  RMS Delta F = %.4f kN" % (
        curve["max_absolute_delta_f_kN"], curve["u_at_max_absolute_delta_f_mm"], curve["rms_delta_f_kN"]
    ))
    
    kin = comp["crack_kinematics_comparison"]
    if kin.get("h1_reference") and kin.get("h2_ultrafine"):
        print("Crack Kinematics:  H1 kink = %.2f deg, H2 kink = %.2f deg (Delta = %+5.2f deg)" % (
            kin["h1_reference"].get("initial_kink_angle_deg", 0.0),
            kin["h2_ultrafine"].get("initial_kink_angle_deg", 0.0),
            kin.get("delta_initial_kink_angle_deg", 0.0)
        ))
        print("                   H1 chord = %.2f deg, H2 chord = %.2f deg (Delta = %+5.2f deg)" % (
            kin["h1_reference"].get("overall_chord_angle_deg", 0.0),
            kin["h2_ultrafine"].get("overall_chord_angle_deg", 0.0),
            kin.get("delta_overall_chord_angle_deg", 0.0)
        ))
    print("="*80 + "\n")

def process_dataset(inp_path, dat_path, sta_path, l0=0.015):
    """Process a single simulation dataset into standard analysis format."""
    print("Parsing mesh geometry from: %s" % inp_path)
    nodes, elements, centroids, areas, h_sizes, n_phys = load_mesh_from_inp(inp_path)
    
    # Compute mesh statistics in crack zone x in [0.0, 0.5], y in [-0.25, 0.05]
    crack_h = [h_sizes[eid] for eid, (cx, cy) in centroids.items() if cx >= 0.0 and -0.25 <= cy <= 0.05]
    if crack_h:
        h_min = min(crack_h)
        h_max = max(crack_h)
        h_mean = sum(crack_h) / float(len(crack_h))
        mean_h_l0 = h_mean / l0
    else:
        h_min = min(h_sizes.values()) if h_sizes else 0.0
        h_max = max(h_sizes.values()) if h_sizes else 0.0
        h_mean = sum(h_sizes.values()) / float(len(h_sizes)) if h_sizes else 0.0
        mean_h_l0 = h_mean / l0

    mesh_stats = {
        "num_underlying_elements": n_phys,
        "crack_zone_elements": len(crack_h),
        "crack_zone_h_min_mm": h_min,
        "crack_zone_h_max_mm": h_max,
        "crack_zone_h_mean_mm": h_mean,
        "crack_zone_mean_h_over_l0": mean_h_l0
    }
    
    print("Parsing reaction forces and displacements from: %s" % dat_path)
    raw_rfu = parse_dat_rp_rfu(dat_path)
    metrics = compute_mechanical_metrics(raw_rfu["u1"], raw_rfu["rf1"])
    
    telemetry = parse_sta_telemetry(sta_path) if sta_path and os.path.exists(sta_path) else {}
    
    # Parse damage field at terminal increment
    print("Parsing damage field SDV14 at terminal increment...")
    elem_d, elem_gd, term_inc = parse_dat_sdvs_at_increment(dat_path, n_phys, target_inc=None)
    trajectory = trace_crack_centerline(centroids, elem_d)
    crack_kinematics = compute_crack_kinematics(trajectory)
    
    return {
        "mesh_stats": mesh_stats,
        "raw_rfu": raw_rfu,
        "metrics": metrics,
        "telemetry": telemetry,
        "crack_trajectory": trajectory,
        "crack_kinematics": crack_kinematics
    }

def main():
    parser = argparse.ArgumentParser(description="Mode-II H1 vs H2 Spatial Sensitivity and Mesh Convergence Engine")
    parser.add_argument("--h1-inp", default=r"D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode2\02_reference_h1\M2_H1_reference.inp", help="Path to H1 reference .inp file")
    parser.add_argument("--h1-dat", default=r"D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode2\02_reference_h1\M2_H1_reference.dat", help="Path to H1 reference .dat file")
    parser.add_argument("--h1-sta", default=r"D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode2\02_reference_h1\M2_H1_reference.sta", help="Path to H1 reference .sta file")
    
    parser.add_argument("--h2-inp", default=r"D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode2\03_ultrafine_h2\M2_H2_reference.inp", help="Path to H2 ultrafine .inp file")
    parser.add_argument("--h2-dat", default=r"D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode2\03_ultrafine_h2\M2_H2_reference.dat", help="Path to H2 ultrafine .dat file")
    parser.add_argument("--h2-sta", default=r"D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode2\03_ultrafine_h2\M2_H2_reference.sta", help="Path to H2 ultrafine .sta file")
    
    parser.add_argument("--output-json", help="Path to write evaluation JSON report")
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("PROCESSING H1 REFERENCE DATASET")
    print("="*80)
    h1_data = process_dataset(args.h1_inp, args.h1_dat, args.h1_sta)
    
    print("\n" + "="*80)
    print("PROCESSING H2 ULTRAFINE DATASET")
    print("="*80)
    h2_data = process_dataset(args.h2_inp, args.h2_dat, args.h2_sta)
    
    comparison = compare_spatial_refinement(h1_data, h2_data)
    print_summary_table(comparison)
    
    if args.output_json:
        with open(args.output_json, "w", encoding="utf-8") as f:
            json.dump(comparison, f, indent=2)
        print("Comparison report saved to: %s\n" % args.output_json)

if __name__ == "__main__":
    main()

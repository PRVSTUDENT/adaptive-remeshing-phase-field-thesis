#!/usr/bin/env python3
"""
Stage 15C: Mode-II Independent Cross-Mode Localization and Native Remesh Sweep Evaluator
Governing Reference: Pandey & Kumar (2025) CMES, Section 4.2, Figs. 6(b), 12(b).

Evaluates:
1. Raw Pre-adaptive MISESERI Field localization against published Fig. 6(b) path.
2. Native adaptiveRemesh candidates (errorTarget in {1.0%, 2.0%, 3.0%, 5.0%}).
3. Selection of optimal production candidate.
4. Generates structured JSON and Markdown reports.
"""

from __future__ import print_function
import os
import sys
import math
import json

DIGITIZED_FIG6B = [
    (0.495, 0.514), (0.540, 0.460), (0.600, 0.380),
    (0.680, 0.280), (0.760, 0.180), (0.840, 0.080), (0.930, 0.000)
]

DIGITIZED_FIG12B = [
    (0.500, 0.500), (0.535, 0.430), (0.585, 0.340),
    (0.650, 0.235), (0.725, 0.140), (0.800, 0.060), (0.868, 0.000)
]

def parse_inp_mesh(inp_path):
    """Parse node and element coordinates from raw INP deck."""
    nodes = {}
    quads = {}
    tris = {}
    
    in_nodes = False
    in_elems = False
    elem_type = 'QUAD'
    
    if not os.path.exists(inp_path):
        return None
        
    with open(inp_path, 'r') as f:
        for line in f:
            l = line.strip()
            if not l or l.startswith('**'):
                continue
            if l.startswith('*'):
                in_nodes = False
                in_elems = False
                upper = l.upper()
                if upper.startswith('*NODE'):
                    in_nodes = True
                elif upper.startswith('*ELEMENT'):
                    in_elems = True
                    if 'CPS4' in upper or 'CPE4' in upper or 'QUAD' in upper:
                        elem_type = 'QUAD'
                    elif 'CPS3' in upper or 'CPE3' in upper or 'TRI' in upper:
                        elem_type = 'TRI'
                    else:
                        elem_type = 'QUAD'
                continue
                
            if in_nodes:
                parts = [p.strip() for p in l.split(',') if p.strip()]
                if len(parts) >= 3:
                    try:
                        nid = int(parts[0])
                        x = float(parts[1])
                        y = float(parts[2])
                        nodes[nid] = (x, y)
                    except ValueError:
                        pass
                        
            if in_elems:
                parts = [p.strip() for p in l.split(',') if p.strip()]
                if len(parts) >= 4:
                    try:
                        int_parts = [int(p) for p in parts]
                        eid = int_parts[0]
                        conn = int_parts[1:]
                        if elem_type == 'QUAD' or len(conn) == 4:
                            quads[eid] = tuple(conn[:4])
                        else:
                            tris[eid] = tuple(conn[:3])
                    except ValueError:
                        pass

    # Compute element centroids and approximate size h = sqrt(area)
    elements_data = []
    for eid, conn in quads.items():
        pts = [nodes[n] for n in conn if n in nodes]
        if len(pts) == 4:
            xc = sum(p[0] for p in pts) / 4.0
            yc = sum(p[1] for p in pts) / 4.0
            x = [p[0] for p in pts]
            y = [p[1] for p in pts]
            area = 0.5 * abs((x[0]*y[1] + x[1]*y[2] + x[2]*y[3] + x[3]*y[0]) - 
                             (y[0]*x[1] + y[1]*x[2] + y[2]*x[3] + y[3]*x[0]))
            h = math.sqrt(max(area, 1e-12))
            elements_data.append({'eid': eid, 'type': 'QUAD', 'xc': xc, 'yc': yc, 'h': h, 'area': area})

    for eid, conn in tris.items():
        pts = [nodes[n] for n in conn if n in nodes]
        if len(pts) == 3:
            xc = sum(p[0] for p in pts) / 3.0
            yc = sum(p[1] for p in pts) / 3.0
            x = [p[0] for p in pts]
            y = [p[1] for p in pts]
            area = 0.5 * abs((x[0]*y[1] + x[1]*y[2] + x[2]*y[0]) - 
                             (y[0]*x[1] + y[1]*x[2] + y[2]*x[0]))
            h = math.sqrt(max(area, 1e-12))
            elements_data.append({'eid': eid, 'type': 'TRI', 'xc': xc, 'yc': yc, 'h': h, 'area': area})

    n_total = len(elements_data)
    h_min = min(e['h'] for e in elements_data) if elements_data else 0.0
    h_max = max(e['h'] for e in elements_data) if elements_data else 0.0
    fine_elems = [e for e in elements_data if e['h'] <= 0.008]
    
    # Corridor centerline by y-bins
    y_bins = [0.05 * i for i in range(11)]
    centerline_pts = []
    for y_val in y_bins:
        band = [e for e in fine_elems if abs(e['yc'] - y_val) <= 0.035 and e['xc'] >= 0.45]
        if band:
            mean_x = sum(e['xc'] for e in band) / float(len(band))
            centerline_pts.append((mean_x, y_val))
            
    if len(centerline_pts) >= 2:
        start_pt = max(centerline_pts, key=lambda pt: pt[1])
        end_pt = min(centerline_pts, key=lambda pt: pt[1])
        dx = end_pt[0] - start_pt[0]
        dy = end_pt[1] - start_pt[1]
        chord_angle_deg = math.degrees(math.atan2(dy, dx))
        end_x = end_pt[0]
    else:
        chord_angle_deg = 0.0
        end_x = 0.5

    spurious_upper = [e for e in fine_elems if e['yc'] > 0.55 and 0.10 < e['xc'] < 0.90]
    has_spurious = len(spurious_upper) > 50

    if -58.0 <= chord_angle_deg <= -42.0 and 0.80 <= end_x <= 0.98 and not has_spurious:
        verdict = "MODE2_LOCALIZATION_CONSISTENT_WITH_PUBLISHED_PATH"
    elif not has_spurious and end_x > 0.70:
        verdict = "MODE2_LOCALIZATION_ACCEPTABLE_MARGINAL_DEVIATION"
    else:
        verdict = "MODE2_LOCALIZATION_DIVERGENT"

    return {
        'total_elements': n_total,
        'quad_count': len(quads),
        'tri_count': len(tris),
        'total_nodes': len(nodes),
        'min_element_size_mm': h_min,
        'max_element_size_mm': h_max,
        'fine_element_count': len(fine_elems),
        'fine_fraction_pct': len(fine_elems) / float(n_total) * 100.0 if n_total > 0 else 0.0,
        'corridor_chord_angle_deg': chord_angle_deg,
        'corridor_end_x_at_y0': end_x,
        'has_spurious_branches': has_spurious,
        'verdict': verdict,
        'centerline_points': centerline_pts
    }

def evaluate_mode2_stage15c(base_dir="."):
    report = {
        "title": "Mode-II Stage 15C Corrected Pre-Analysis and Native Remesh Sweep Evaluation",
        "reference": "Pandey & Kumar (2025) CMES, Section 4.2",
        "candidates": {},
        "selection": {}
    }
    
    et_list = [1.0, 2.0, 3.0, 5.0]
    for et in et_list:
        raw_inp = os.path.join(base_dir, "MODE2_ADAPTED_RAW_%dPCT.inp" % int(et))
        metrics = parse_inp_mesh(raw_inp)
        if metrics:
            metrics['error_target_pct'] = et
            report["candidates"]["ET_%.0fPCT" % et] = metrics

    return report

# -*- coding: utf-8 -*-
"""
scripts/validation/audit_f1703_exact_line_intersection.py
=========================================================
Task F1703: Exact Polygon-Line Intersection Connectivity Audit
Standardizes canonical and authentic crack trajectories:
  - Primary: (10.0, 70.0) -> (26.5, 51.0) [L1 = 25.1645 mm]
  - Secondary (Horizontal): (46.5, 51.0) -> (65.0, 51.0) [L2 = 18.5000 mm]
  - Secondary (Authentic Job 1421286): (46.50, 50.73) -> (65.00, 52.25) [L2_act = 18.5623 mm]

Computes exact interval unions, covered lengths, maximum uncovered gaps,
and longest connected refined segments for h <= l0 and h <= l0/2 across
all candidate meshes.
"""

from __future__ import print_function
import os
import sys
import math
import json
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
L0 = 0.285          # mm
L0_HALF = L0 / 2.0    # 0.1425 mm

TRAJECTORIES = {
    "primary": {
        "name": "Canonical Primary Notch-to-Hole Corridor",
        "start": (10.0, 70.0),
        "end": (26.5, 51.0),
        "length_mm": math.hypot(26.5 - 10.0, 51.0 - 70.0) # 25.16446 mm
    },
    "secondary_horizontal": {
        "name": "Canonical Secondary Hole-to-Right-Edge (Horizontal)",
        "start": (46.5, 51.0),
        "end": (65.0, 51.0),
        "length_mm": 18.50000 # 18.50000 mm
    },
    "secondary_actual": {
        "name": "Authentic Secondary Crack Trajectory (Job 1421286 Linear Fit)",
        "start": (46.50, 50.73),
        "end": (65.00, 52.25),
        "length_mm": math.hypot(65.00 - 46.50, 52.25 - 50.73) # 18.56233 mm
    }
}

def parse_mesh(inp_path):
    nodes = {}
    elements = {}
    in_nodes = False
    in_elements = False

    with open(inp_path, "r") as f:
        for line in f:
            line_str = line.strip()
            if not line_str or line_str.startswith("**"):
                continue
            upper = line_str.upper()
            if upper.startswith("*NODE") and not any(k in upper for k in ["PRINT", "FILE", "OUTPUT"]):
                in_nodes = True
                in_elements = False
                continue
            elif upper.startswith("*ELEMENT") and "OUTPUT" not in upper:
                in_nodes = False
                in_elements = True
                continue
            elif line_str.startswith("*"):
                in_nodes = False
                in_elements = False
                continue

            if in_nodes:
                try:
                    parts = [p.strip() for p in line_str.split(",")]
                    nodes[int(parts[0])] = (float(parts[1]), float(parts[2]))
                except (ValueError, IndexError):
                    continue
            elif in_elements:
                try:
                    parts = [p.strip() for p in line_str.split(",")]
                    eid = int(parts[0])
                    conn = [int(p) for p in parts[1:] if p]
                    elements[eid] = conn
                except (ValueError, IndexError):
                    continue
    return nodes, elements

def line_segment_intersection(p0, p1, q0, q1):
    dp = (p1[0] - p0[0], p1[1] - p0[1])
    dq = (q1[0] - q0[0], q1[1] - q0[1])
    denom = dp[0] * dq[1] - dp[1] * dq[0]
    if abs(denom) < 1e-12:
        return None
    qp = (q0[0] - p0[0], q0[1] - p0[1])
    t = (qp[0] * dq[1] - qp[1] * dq[0]) / denom
    u = (qp[0] * dp[1] - qp[1] * dp[0]) / denom
    if 0.0 <= t <= 1.0 and 0.0 <= u <= 1.0:
        return t
    return None

def point_in_polygon(pt, poly):
    x, y = pt
    n = len(poly)
    inside = False
    p1x, p1y = poly[0]
    for i in range(n + 1):
        p2x, p2y = poly[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside

def clip_segment_to_polygon(p0, p1, poly):
    t_vals = []
    if point_in_polygon(p0, poly):
        t_vals.append(0.0)
    if point_in_polygon(p1, poly):
        t_vals.append(1.0)
    n = len(poly)
    for i in range(n):
        q0 = poly[i]
        q1 = poly[(i + 1) % n]
        t = line_segment_intersection(p0, p1, q0, q1)
        if t is not None:
            t_vals.append(t)
    if not t_vals:
        return []
    t_vals = sorted(list(set([round(t, 9) for t in t_vals])))
    valid_intervals = []
    for i in range(len(t_vals) - 1):
        t_start = t_vals[i]
        t_end = t_vals[i + 1]
        if t_end - t_start < 1e-8:
            continue
        t_mid = 0.5 * (t_start + t_end)
        mid_pt = (p0[0] + t_mid * (p1[0] - p0[0]), p0[1] + t_mid * (p1[1] - p0[1]))
        if point_in_polygon(mid_pt, poly):
            valid_intervals.append((t_start, t_end))
    return valid_intervals

def union_intervals(intervals):
    if not intervals:
        return []
    sorted_int = sorted(intervals, key=lambda x: x[0])
    merged = [list(sorted_int[0])]
    for cur in sorted_int[1:]:
        prev = merged[-1]
        if cur[0] <= prev[1] + 1e-7:
            prev[1] = max(prev[1], cur[1])
        else:
            merged.append(list(cur))
    return [(m[0], m[1]) for m in merged]

def evaluate_mesh(inp_path, mesh_name="Adapted_Mesh"):
    print("Auditing %s from %s..." % (mesh_name, inp_path))
    nodes, elements = parse_mesh(inp_path)
    print("  Loaded %d nodes, %d elements" % (len(nodes), len(elements)))

    elem_poly = {}
    elem_h = {}
    elem_centroid = {}
    quad_count = 0
    tri_count = 0

    for eid, conn in elements.items():
        pts = [nodes[nid] for nid in conn if nid in nodes]
        if len(pts) != len(conn):
            continue
        poly_x = [pt[0] for pt in pts]
        poly_y = [pt[1] for pt in pts]
        n_pts = len(pts)
        if n_pts == 4:
            quad_count += 1
        elif n_pts == 3:
            tri_count += 1
        area = 0.5 * abs(sum([poly_x[i]*poly_y[(i+1)%n_pts] - poly_y[i]*poly_x[(i+1)%n_pts] for i in range(n_pts)]))
        h_eq = math.sqrt(area)
        cx = sum(poly_x) / float(n_pts)
        cy = sum(poly_y) / float(n_pts)

        elem_poly[eid] = pts
        elem_h[eid] = h_eq
        elem_centroid[eid] = (cx, cy)

    mesh_summary = {
        "mesh_name": mesh_name,
        "inp_path": inp_path,
        "total_nodes": len(nodes),
        "total_elements": len(elements),
        "quad_elements": quad_count,
        "tri_elements": tri_count,
        "quad_fraction_pct": round(100.0 * quad_count / float(len(elements)), 2) if elements else 0.0,
        "trajectories": {}
    }

    for traj_key, traj_info in TRAJECTORIES.items():
        p_start = traj_info["start"]
        p_end = traj_info["end"]
        L_tot = traj_info["length_mm"]

        intervals_all = []
        intervals_l0 = []
        intervals_l0_half = []
        intersecting_elements = set()

        for eid, poly in elem_poly.items():
            intervals = clip_segment_to_polygon(p_start, p_end, poly)
            if intervals:
                intersecting_elements.add(eid)
                h_val = elem_h[eid]
                for (t0, t1) in intervals:
                    s0 = t0 * L_tot
                    s1 = t1 * L_tot
                    intervals_all.append((s0, s1))
                    if h_val <= L0:
                        intervals_l0.append((s0, s1))
                    if h_val <= L0_HALF:
                        intervals_l0_half.append((s0, s1))

        corridor_half_w = 2.0 * L0
        dx = p_end[0] - p_start[0]
        dy = p_end[1] - p_start[1]
        line_len_sq = dx*dx + dy*dy
        corridor_elements = []

        for eid, (cx, cy) in elem_centroid.items():
            t = max(0.0, min(1.0, ((cx - p_start[0])*dx + (cy - p_start[1])*dy) / line_len_sq))
            proj_x = p_start[0] + t * dx
            proj_y = p_start[1] + t * dy
            dist = math.hypot(cx - proj_x, cy - proj_y)
            if dist <= corridor_half_w:
                corridor_elements.append(eid)

        corr_h = [elem_h[eid] for eid in corridor_elements]
        corr_n = len(corr_h)
        c_l0 = sum(1 for h in corr_h if h <= L0)
        c_half = sum(1 for h in corr_h if h <= L0_HALF)

        corridor_2d_metrics = {
            "corridor_half_width_mm": corridor_half_w,
            "total_elements_in_band": corr_n,
            "elements_le_l0": c_l0,
            "fraction_le_l0_pct": round(100.0 * c_l0 / float(corr_n), 2) if corr_n > 0 else 0.0,
            "elements_le_l0_half": c_half,
            "fraction_le_l0_half_pct": round(100.0 * c_half / float(corr_n), 2) if corr_n > 0 else 0.0,
            "h_min_mm": round(min(corr_h), 4) if corr_h else 0.0,
            "h_median_mm": round(float(np.median(corr_h)), 4) if corr_h else 0.0,
            "h_max_mm": round(max(corr_h), 4) if corr_h else 0.0
        }

        def process_intervals(int_list, total_len):
            merged = union_intervals(int_list)
            if not merged:
                return {
                    "element_count": 0,
                    "covered_length_mm": 0.0,
                    "coverage_pct": 0.0,
                    "longest_connected_segment_mm": 0.0,
                    "max_uncovered_gap_mm": round(total_len, 4),
                    "num_gaps": 1
                }
            cov_len = sum([s1 - s0 for (s0, s1) in merged])
            longest_seg = max([s1 - s0 for (s0, s1) in merged])
            gaps = []
            if merged[0][0] > 1e-4:
                gaps.append(merged[0][0])
            for i in range(len(merged) - 1):
                gap = merged[i+1][0] - merged[i][1]
                if gap > 1e-4:
                    gaps.append(gap)
            if total_len - merged[-1][1] > 1e-4:
                gaps.append(total_len - merged[-1][1])
            max_gap = max(gaps) if gaps else 0.0
            return {
                "element_count": len(int_list),
                "covered_length_mm": round(cov_len, 4),
                "coverage_pct": round(100.0 * cov_len / total_len, 2),
                "longest_connected_segment_mm": round(longest_seg, 4),
                "max_uncovered_gap_mm": round(max_gap, 4),
                "num_gaps": len(gaps)
            }

        l0_stats = process_intervals(intervals_l0, L_tot)
        l0_half_stats = process_intervals(intervals_l0_half, L_tot)

        mesh_summary["trajectories"][traj_key] = {
            "trajectory_name": traj_info["name"],
            "total_length_mm": round(L_tot, 4),
            "exact_centerline_intersection": {
                "total_intersecting_elements": len(intersecting_elements),
                "h_le_l0": l0_stats,
                "h_le_l0_half": l0_half_stats
            },
            "2d_corridor_element_counts": corridor_2d_metrics
        }

    return mesh_summary

if __name__ == "__main__":
    test_files = [
        ("F1702_Baseline", os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "202_pk_sec43_continuous_recovery", "PK_SEC43_F1702_HISTORY_AWARE_ADAPT.inp")),
        ("F1703_Official", os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "203_pk_sec43_secondary_complete", "PK_SEC43_F1703_SECONDARY_COMPLETE_ADAPT.inp")),
    ]
    results = {}
    for name, path in test_files:
        if os.path.exists(path):
            results[name] = evaluate_mesh(path, name)
        else:
            print("File not found:", path)

    out_json = os.path.join(REPO_ROOT, "results", "validation", "f1703_secondary_complete_connectivity_audit.json")
    with open(out_json, "w") as f:
        json.dump(results, f, indent=2)
    print("Saved comparison to", out_json)

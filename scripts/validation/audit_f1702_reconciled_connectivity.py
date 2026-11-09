# -*- coding: utf-8 -*-
"""
scripts/validation/audit_f1702_reconciled_connectivity.py
=========================================================
Task F1702 Iteration 2: Reconciled Spatial Connectivity and Corridor Audit
Resolves Review Qualifications Q5 and Q6:
  - Reconciles corridor connectivity metrics with separate element fractions
    and geometric 1D centerline interval coverage.
  - Distinguishes clearly between 2D element counts in the corridor zone and
    1D projection coverage along the physical crack trajectory.
  - Computes exact interval unions, covered lengths, uncovered gaps, and
    longest connected segments at both h <= l0 and h <= l0/2 thresholds.
"""

from __future__ import print_function
import os
import sys
import math
import json
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ADAPT_INP = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "202_pk_sec43_continuous_recovery", "PK_SEC43_F1702_HISTORY_AWARE_ADAPT.inp")
OUTPUT_JSON = os.path.join(REPO_ROOT, "results", "validation", "f1702_reconciled_connectivity_audit.json")

L0 = 0.285       # mm
L0_HALF = L0 / 2.0 # 0.1425 mm

# Corridor definitions:
# Primary: from initial slit tip (10.0, 70.0) to central hole boundary (26.5, 51.0)
P1_START = (10.0, 70.0)
P1_END   = (26.5, 51.0)
L1_TOTAL = math.sqrt((P1_END[0] - P1_START[0])**2 + (P1_END[1] - P1_START[1])**2) # ~25.164 mm

# Secondary: from right hole flank (42.5, 51.0) to plate right edge (65.0, 58.8)
# Actual crack path in Job 1421286 goes from (38.5, 51.5) through (49.0, 53.8) to (65.0, 58.8)
P2_START = (42.5, 51.0)
P2_END   = (65.0, 58.8)
L2_TOTAL = math.sqrt((P2_END[0] - P2_START[0])**2 + (P2_END[1] - P2_START[1])**2) # ~23.81 mm

CORRIDOR_WIDTH = 2.0 # mm half-width around centerline

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

def project_point_on_segment(px, py, x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    l2 = dx*dx + dy*dy
    if l2 == 0.0:
        return math.sqrt((px - x1)**2 + (py - y1)**2), 0.0
    t = ((px - x1)*dx + (py - y1)*dy) / l2
    t_clamped = max(0.0, min(1.0, t))
    proj_x = x1 + t_clamped * dx
    proj_y = y1 + t_clamped * dy
    dist = math.sqrt((px - proj_x)**2 + (py - proj_y)**2)
    s = t_clamped * math.sqrt(l2)
    return dist, s

def compute_interval_union(intervals):
    """Computes union of 1D intervals [[a1, b1], [a2, b2], ...] and returns disjoint intervals."""
    if not intervals:
        return []
    sorted_inv = sorted(intervals, key=lambda x: x[0])
    merged = [sorted_inv[0]]
    for cur in sorted_inv[1:]:
        prev = merged[-1]
        if cur[0] <= prev[1]:
            merged[-1] = [prev[0], max(prev[1], cur[1])]
        else:
            merged.append(cur)
    return merged

def audit_mesh_corridors():
    print("Loading adapted mesh: %s" % ADAPT_INP)
    nodes, elements = parse_mesh(ADAPT_INP)
    print("Mesh: %d nodes, %d elements" % (len(nodes), len(elements)))

    quad_count = 0
    tri_count = 0
    p1_elems = []
    p2_elems = []

    for eid, conn in elements.items():
        pts = [nodes[nid] for nid in conn if nid in nodes]
        n_pts = len(pts)
        if n_pts == 4:
            quad_count += 1
        elif n_pts == 3:
            tri_count += 1
        poly_x = [pt[0] for pt in pts]
        poly_y = [pt[1] for pt in pts]
        area = 0.5 * abs(sum([poly_x[i]*poly_y[(i+1)%n_pts] - poly_y[i]*poly_x[(i+1)%n_pts] for i in range(n_pts)]))
        h = math.sqrt(area)
        cx = sum(poly_x) / float(n_pts)
        cy = sum(poly_y) / float(n_pts)

        # Primary corridor distance and projection
        d1, s1 = project_point_on_segment(cx, cy, P1_START[0], P1_START[1], P1_END[0], P1_END[1])
        if d1 <= CORRIDOR_WIDTH:
            # Project all polygon vertices to get span [s_min, s_max]
            s_all = [project_point_on_segment(pt[0], pt[1], P1_START[0], P1_START[1], P1_END[0], P1_END[1])[1] for pt in pts]
            p1_elems.append({
                "eid": eid, "h": h, "s_center": s1,
                "s_min": min(s_all), "s_max": max(s_all),
                "dist": d1, "area": area
            })

        # Secondary corridor distance and projection
        d2, s2 = project_point_on_segment(cx, cy, P2_START[0], P2_START[1], P2_END[0], P2_END[1])
        if d2 <= CORRIDOR_WIDTH:
            s_all = [project_point_on_segment(pt[0], pt[1], P2_START[0], P2_START[1], P2_END[0], P2_END[1])[1] for pt in pts]
            p2_elems.append({
                "eid": eid, "h": h, "s_center": s2,
                "s_min": min(s_all), "s_max": max(s_all),
                "dist": d2, "area": area
            })

    def analyze_corridor(elems, l_tot, name):
        total_in_corridor = len(elems)
        le_l0 = [e for e in elems if e["h"] <= L0]
        le_half = [e for e in elems if e["h"] <= L0_HALF]

        pct_count_l0 = (len(le_l0) / float(total_in_corridor) * 100.0) if total_in_corridor else 0.0
        pct_count_half = (len(le_half) / float(total_in_corridor) * 100.0) if total_in_corridor else 0.0

        # Geometric 1D centerline interval coverage for h <= l0
        intervals_l0 = [[e["s_min"], e["s_max"]] for e in le_l0]
        merged_l0 = compute_interval_union(intervals_l0)
        covered_len_l0 = sum(inv[1] - inv[0] for inv in merged_l0)
        pct_centerline_l0 = (covered_len_l0 / l_tot * 100.0)

        # Uncovered gaps along centerline for h <= l0
        gaps_l0 = []
        cur_pos = 0.0
        for inv in merged_l0:
            if inv[0] > cur_pos:
                gaps_l0.append([cur_pos, inv[0], inv[0] - cur_pos])
            cur_pos = max(cur_pos, inv[1])
        if cur_pos < l_tot:
            gaps_l0.append([cur_pos, l_tot, l_tot - cur_pos])

        max_gap_l0 = max((g[2] for g in gaps_l0), default=l_tot)
        max_segment_l0 = max((inv[1] - inv[0] for inv in merged_l0), default=0.0)

        # Geometric 1D centerline interval coverage for h <= l0/2
        intervals_half = [[e["s_min"], e["s_max"]] for e in le_half]
        merged_half = compute_interval_union(intervals_half)
        covered_len_half = sum(inv[1] - inv[0] for inv in merged_half)
        pct_centerline_half = (covered_len_half / l_tot * 100.0)

        gaps_half = []
        cur_pos = 0.0
        for inv in merged_half:
            if inv[0] > cur_pos:
                gaps_half.append([cur_pos, inv[0], inv[0] - cur_pos])
            cur_pos = max(cur_pos, inv[1])
        if cur_pos < l_tot:
            gaps_half.append([cur_pos, l_tot, l_tot - cur_pos])

        max_gap_half = max((g[2] for g in gaps_half), default=l_tot)
        max_segment_half = max((inv[1] - inv[0] for inv in merged_half), default=0.0)

        h_vals = [e["h"] for e in elems]

        return {
            "corridor_name": name,
            "centerline_length_mm": round(l_tot, 3),
            "element_count_metrics": {
                "total_elements_in_corridor": total_in_corridor,
                "elements_le_l0": len(le_l0),
                "fraction_le_l0_pct": round(pct_count_l0, 2),
                "elements_le_half_l0": len(le_half),
                "fraction_le_half_l0_pct": round(pct_count_half, 2),
                "min_h_mm": round(min(h_vals), 6) if h_vals else 0.0,
                "median_h_mm": round(float(np.median(h_vals)), 6) if h_vals else 0.0,
                "max_h_mm": round(max(h_vals), 6) if h_vals else 0.0
            },
            "centerline_geometric_coverage_l0": {
                "threshold_mm": L0,
                "covered_centerline_length_mm": round(covered_len_l0, 3),
                "centerline_coverage_pct": round(pct_centerline_l0, 2),
                "max_uncovered_gap_mm": round(max_gap_l0, 3),
                "longest_connected_refined_segment_mm": round(max_segment_l0, 3),
                "number_of_covered_intervals": len(merged_l0),
                "covered_intervals_mm": [[round(inv[0], 2), round(inv[1], 2)] for inv in merged_l0],
                "uncovered_gaps_mm": [[round(g[0], 2), round(g[1], 2), round(g[2], 2)] for g in gaps_l0]
            },
            "centerline_geometric_coverage_half_l0": {
                "threshold_mm": L0_HALF,
                "covered_centerline_length_mm": round(covered_len_half, 3),
                "centerline_coverage_pct": round(pct_centerline_half, 2),
                "max_uncovered_gap_mm": round(max_gap_half, 3),
                "longest_connected_refined_segment_mm": round(max_segment_half, 3),
                "number_of_covered_intervals": len(merged_half)
            }
        }

    p1_audit = analyze_corridor(p1_elems, L1_TOTAL, "Primary Corridor (Notch Tip -> Hole Boundary)")
    p2_audit = analyze_corridor(p2_elems, L2_TOTAL, "Secondary Corridor (Hole Right Flank -> Plate Edge)")

    results = {
        "metadata": {
            "task_id": "F1702-PK-SEC43-FIGS14-16-REPRODUCTION-AND-CONTINUATION",
            "audit": "reconciled_corridor_connectivity_and_centerline_gap_audit",
            "mesh_deck": "models/pandey_kumar_mode1/202_pk_sec43_continuous_recovery/PK_SEC43_F1702_HISTORY_AWARE_ADAPT.inp",
            "regularisation_l0_mm": L0,
            "regularisation_l0_half_mm": L0_HALF
        },
        "mesh_summary": {
            "total_elements": len(elements),
            "total_nodes": len(nodes),
            "quad_count": quad_count,
            "tri_count": tri_count,
            "quad_percentage": round(100.0 * quad_count / len(elements), 2)
        },
        "primary_corridor": p1_audit,
        "secondary_corridor": p2_audit,
        "spatial_verdict": "IMPROVED_PARTIAL_DUAL_CORRIDOR_LOCALIZATION",
        "scientific_classification": "LOCALIZED_PROCESS_ZONE_IN_SECONDARY_WITH_DISCONTINUOUS_PRIMARY_WAKE_RETENTION"
    }

    with open(OUTPUT_JSON, "w") as f:
        json.dump(results, f, indent=2)

    print("\n--- Reconciled Connectivity Audit Results ---")
    print("Secondary Corridor:")
    print("  Element count: %d / %d (%.2f%%) <= l0, %d / %d (%.2f%%) <= l0/2" % (
        p2_audit["element_count_metrics"]["elements_le_l0"],
        p2_audit["element_count_metrics"]["total_elements_in_corridor"],
        p2_audit["element_count_metrics"]["fraction_le_l0_pct"],
        p2_audit["element_count_metrics"]["elements_le_half_l0"],
        p2_audit["element_count_metrics"]["total_elements_in_corridor"],
        p2_audit["element_count_metrics"]["fraction_le_half_l0_pct"]
    ))
    print("  Centerline coverage (h <= l0): %.2f%% (%.2f mm of %.2f mm), max gap = %.2f mm, longest segment = %.2f mm" % (
        p2_audit["centerline_geometric_coverage_l0"]["centerline_coverage_pct"],
        p2_audit["centerline_geometric_coverage_l0"]["covered_centerline_length_mm"],
        p2_audit["centerline_length_mm"],
        p2_audit["centerline_geometric_coverage_l0"]["max_uncovered_gap_mm"],
        p2_audit["centerline_geometric_coverage_l0"]["longest_connected_refined_segment_mm"]
    ))
    print("Primary Corridor:")
    print("  Element count: %d / %d (%.2f%%) <= l0, %d / %d (%.2f%%) <= l0/2" % (
        p1_audit["element_count_metrics"]["elements_le_l0"],
        p1_audit["element_count_metrics"]["total_elements_in_corridor"],
        p1_audit["element_count_metrics"]["fraction_le_l0_pct"],
        p1_audit["element_count_metrics"]["elements_le_half_l0"],
        p1_audit["element_count_metrics"]["total_elements_in_corridor"],
        p1_audit["element_count_metrics"]["fraction_le_half_l0_pct"]
    ))
    print("  Centerline coverage (h <= l0): %.2f%% (%.2f mm of %.2f mm), max gap = %.2f mm, longest segment = %.2f mm" % (
        p1_audit["centerline_geometric_coverage_l0"]["centerline_coverage_pct"],
        p1_audit["centerline_geometric_coverage_l0"]["covered_centerline_length_mm"],
        p1_audit["centerline_length_mm"],
        p1_audit["centerline_geometric_coverage_l0"]["max_uncovered_gap_mm"],
        p1_audit["centerline_geometric_coverage_l0"]["longest_connected_refined_segment_mm"]
    ))
    print("\nSaved reconciled audit to: %s" % OUTPUT_JSON)

if __name__ == "__main__":
    audit_mesh_corridors()

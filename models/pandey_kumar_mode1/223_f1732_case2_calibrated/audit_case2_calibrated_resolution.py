# -*- coding: utf-8 -*-
"""
audit_case2_calibrated_resolution.py
====================================
Independent, reproducible spatial-resolution audit of the Case 2 Off-Axis Hole calibrated adapted mesh
(PK_F1728_CASE_2_ADAPT_PHYS.inp) generated under Task F1732 with error_target = 3.80%.

Features:
  - Total physical elements, nodes, quad/tri fractions (%).
  - Minimum signed Jacobian det(J) across 2x2 Gauss integration points (100% strictly positive required).
  - Mutually exclusive spatial partition (P1: Notch Root, P2: Primary Corridor excl. Notch,
    P3: Hole Boundary excl. Corridor, P4: Far-Field Bulk) summing to exactly 100% of elements.
  - Overlapping diagnostic windows (W1: Notch Root, W2: Primary Corridor, W3: Hole Boundary Ring,
    W4: Uncracked Ligament) explicitly disclosed per Finding F1731-R04.
  - Along-path trajectory discretization evaluating continuous spatial coverage of h <= l0/2 = 3.75 um
    along the oblique notch-to-hole crack trajectory per Finding F1731-R06.
  - Generates f1732_case2_ligament_spatial_audit.json.
"""

import os
import sys
import json
import math

L0_MM = 0.0075
L0_HALF = L0_MM / 2.0
L0_THIRD = L0_MM / 3.0

HOLE_X = 0.65
HOLE_Y = 0.65
HOLE_R = 0.10

def parse_inp_mesh(inp_path):
    nodes = {}
    quad_elems = {}
    tri_elems = {}

    in_nodes = False
    in_elements = False
    elem_type = None

    with open(inp_path, "r") as f:
        for line in f:
            l = line.strip()
            if not l:
                continue
            if l.startswith("*"):
                u = l.upper()
                if u.startswith("*NODE"):
                    in_nodes = True
                    in_elements = False
                    continue
                elif u.startswith("*ELEMENT"):
                    in_nodes = False
                    in_elements = True
                    if "CPS4" in u or "CPE4" in u or "QUAD" in u:
                        elem_type = "QUAD"
                    elif "CPS3" in u or "CPE3" in u or "TRI" in u:
                        elem_type = "TRI"
                    else:
                        elem_type = "QUAD"
                    continue
                elif u.startswith("*") and not u.startswith("**"):
                    in_nodes = False
                    in_elements = False
                    continue
                elif u.startswith("**"):
                    continue

            if in_nodes:
                parts = [p.strip() for p in l.split(",") if p.strip()]
                if len(parts) >= 3:
                    try:
                        nid = int(parts[0])
                        x = float(parts[1])
                        y = float(parts[2])
                        nodes[nid] = (x, y)
                    except ValueError:
                        pass

            elif in_elements:
                parts = [p.strip() for p in l.split(",") if p.strip()]
                if len(parts) >= 4:
                    try:
                        eid = int(parts[0])
                        conn = [int(p) for p in parts[1:]]
                        if len(conn) >= 4 and elem_type == "QUAD":
                            quad_elems[eid] = tuple(conn[:4])
                        elif len(conn) >= 3:
                            tri_elems[eid] = tuple(conn[:3])
                    except ValueError:
                        pass

    return nodes, quad_elems, tri_elems

def compute_element_metrics(nodes, quad_elems, tri_elems):
    elements_data = []

    for eid, conn in quad_elems.items():
        pts = [nodes[nid] for nid in conn if nid in nodes]
        if len(pts) != 4:
            continue
        x = [p[0] for p in pts]
        y = [p[1] for p in pts]
        area = 0.5 * abs((x[0]*y[1] - x[1]*y[0]) +
                         (x[1]*y[2] - x[2]*y[1]) +
                         (x[2]*y[3] - x[3]*y[2]) +
                         (x[3]*y[0] - x[0]*y[3]))
        cx = sum(x) / 4.0
        cy = sum(y) / 4.0

        edges = [
            math.hypot(x[1]-x[0], y[1]-y[0]),
            math.hypot(x[2]-x[1], y[2]-y[1]),
            math.hypot(x[3]-x[2], y[3]-y[2]),
            math.hypot(x[0]-x[3], y[0]-y[3])
        ]
        max_edge = max(edges)
        min_edge = max(min(edges), 1e-12)
        h_area = math.sqrt(area)

        gp = 1.0 / math.sqrt(3.0)
        gauss_pts = [(-gp, -gp), (gp, -gp), (gp, gp), (-gp, gp)]
        min_det_j = 1e9
        for xi, eta in gauss_pts:
            dN_dxi = [
                -0.25 * (1.0 - eta),
                 0.25 * (1.0 - eta),
                 0.25 * (1.0 + eta),
                -0.25 * (1.0 + eta)
            ]
            dN_deta = [
                -0.25 * (1.0 - xi),
                -0.25 * (1.0 + xi),
                 0.25 * (1.0 + xi),
                 0.25 * (1.0 - xi)
            ]
            j11 = sum(dN_dxi[i] * x[i] for i in range(4))
            j12 = sum(dN_dxi[i] * y[i] for i in range(4))
            j21 = sum(dN_deta[i] * x[i] for i in range(4))
            j22 = sum(dN_deta[i] * y[i] for i in range(4))
            det_j = j11 * j22 - j12 * j21
            if det_j < min_det_j:
                min_det_j = det_j

        elements_data.append({
            "eid": eid,
            "type": "QUAD",
            "cx": cx,
            "cy": cy,
            "area": area,
            "h_area": h_area,
            "max_edge": max_edge,
            "aspect_ratio": max_edge / min_edge,
            "min_det_j": min_det_j
        })

    for eid, conn in tri_elems.items():
        pts = [nodes[nid] for nid in conn if nid in nodes]
        if len(pts) != 3:
            continue
        x = [p[0] for p in pts]
        y = [p[1] for p in pts]
        area = 0.5 * abs((x[0]*(y[1]-y[2]) + x[1]*(y[2]-y[0]) + x[2]*(y[0]-y[1])))
        cx = sum(x) / 3.0
        cy = sum(y) / 3.0

        edges = [
            math.hypot(x[1]-x[0], y[1]-y[0]),
            math.hypot(x[2]-x[1], y[2]-y[1]),
            math.hypot(x[0]-x[2], y[0]-y[2])
        ]
        max_edge = max(edges)
        min_edge = max(min(edges), 1e-12)
        h_area = math.sqrt(area)

        det_j = (x[1]-x[0])*(y[2]-y[0]) - (y[1]-y[0])*(x[2]-x[0])

        elements_data.append({
            "eid": eid,
            "type": "TRI",
            "cx": cx,
            "cy": cy,
            "area": area,
            "h_area": h_area,
            "max_edge": max_edge,
            "aspect_ratio": max_edge / min_edge,
            "min_det_j": det_j
        })

    return elements_data

def evaluate_subset_stats(elems):
    count = len(elems)
    if count == 0:
        return {"count": 0}
    h_vals = [e["h_area"] for e in elems]
    h_edges = [e["max_edge"] for e in elems]

    n_le_l0 = sum(1 for h in h_vals if h <= L0_MM)
    n_le_l0_half = sum(1 for h in h_vals if h <= L0_HALF)
    n_le_l0_third = sum(1 for h in h_vals if h <= L0_THIRD)

    mean_h = sum(h_vals) / float(count)
    min_h = min(h_vals)
    max_h = max(h_vals)

    return {
        "count": count,
        "mean_h_area_mm": mean_h,
        "mean_h_area_um": mean_h * 1000.0,
        "min_h_area_mm": min_h,
        "min_h_area_um": min_h * 1000.0,
        "max_h_area_mm": max_h,
        "max_h_area_um": max_h * 1000.0,
        "mean_max_edge_um": (sum(h_edges) / float(count)) * 1000.0,
        "n_le_l0": n_le_l0,
        "pct_le_l0": 100.0 * n_le_l0 / float(count),
        "n_le_l0_half": n_le_l0_half,
        "pct_le_l0_half": 100.0 * n_le_l0_half / float(count),
        "n_le_l0_third": n_le_l0_third,
        "pct_le_l0_third": 100.0 * n_le_l0_third / float(count)
    }

def audit_mesh(inp_path, out_json_path):
    print("=== Spatial Resolution Audit for Case 2 Calibrated Mesh (Task F1732) ===")
    print("Mesh INP:   %s" % inp_path)
    print("Output JSON:%s" % out_json_path)

    if not os.path.isfile(inp_path):
        print("ERROR: Mesh INP file does not exist: %s" % inp_path)
        sys.exit(1)

    nodes, quad_elems, tri_elems = parse_inp_mesh(inp_path)
    total_elements = len(quad_elems) + len(tri_elems)
    total_nodes = len(nodes)
    print("Total Nodes: %d" % total_nodes)
    print("Total Physical Elements: %d (Quads: %d, Tris: %d)" % (total_elements, len(quad_elems), len(tri_elems)))

    if total_elements == 0:
        print("ERROR: No physical elements parsed!")
        sys.exit(1)

    elements_data = compute_element_metrics(nodes, quad_elems, tri_elems)

    # 1. Global Jacobian and Quality Audit
    min_det_j = min(e["min_det_j"] for e in elements_data)
    non_pos_j = sum(1 for e in elements_data if e["min_det_j"] <= 0.0)
    quad_pct = 100.0 * len(quad_elems) / float(total_elements)
    tri_pct = 100.0 * len(tri_elems) / float(total_elements)
    aspect_ratios = [e["aspect_ratio"] for e in elements_data]
    mean_ar = sum(aspect_ratios) / float(total_elements)
    max_ar = max(aspect_ratios)

    print("Quad Fraction: %.2f%% (Target >= 90.0%%)" % quad_pct)
    print("Min det(J):    %.6e (%s)" % (min_det_j, "PASS" if non_pos_j == 0 else "FAIL"))
    print("Mean Aspect Ratio: %.2f, Max: %.2f" % (mean_ar, max_ar))

    # 2. Mutually Exclusive Spatial Partition (Sum equals 100% of elements)
    # P1: Notch tip root
    # P2: Primary oblique corridor excl. notch tip
    # P3: Hole boundary ring excl. corridor
    # P4: Far-field bulk (all remaining elements)
    p1_notch = []
    p2_corridor_excl = []
    p3_hole_ring_excl = []
    p4_bulk = []

    for e in elements_data:
        cx, cy = e["cx"], e["cy"]
        dist_hole_center = math.hypot(cx - HOLE_X, cy - HOLE_Y)
        dist_hole_perimeter = abs(dist_hole_center - HOLE_R)

        is_notch = (0.50 <= cx <= 0.53 and 0.49 <= cy <= 0.51)
        is_corridor = (0.50 <= cx <= 0.65 and 0.47 <= cy <= 0.60)
        is_hole_ring = (dist_hole_perimeter <= 3.0 * L0_MM)

        if is_notch:
            p1_notch.append(e)
        elif is_corridor:
            p2_corridor_excl.append(e)
        elif is_hole_ring:
            p3_hole_ring_excl.append(e)
        else:
            p4_bulk.append(e)

    partition_counts = [len(p1_notch), len(p2_corridor_excl), len(p3_hole_ring_excl), len(p4_bulk)]
    sum_partition = sum(partition_counts)
    assert sum_partition == total_elements, "Partition sum (%d) != total elements (%d)!" % (sum_partition, total_elements)
    print("Mutually Exclusive Partition: P1=%d, P2=%d, P3=%d, P4=%d (Sum = %d / %d, 100.0%%)" % (
        len(p1_notch), len(p2_corridor_excl), len(p3_hole_ring_excl), len(p4_bulk), sum_partition, total_elements
    ))

    # 3. Overlapping Diagnostic Windows (per Finding F1731-R04)
    w1_notch = [e for e in elements_data if (0.50 <= e["cx"] <= 0.53 and 0.49 <= e["cy"] <= 0.51)]
    w2_corridor = [e for e in elements_data if (0.50 <= e["cx"] <= 0.65 and 0.47 <= e["cy"] <= 0.60)]
    w3_hole_ring = [e for e in elements_data if (abs(math.hypot(e["cx"] - HOLE_X, e["cy"] - HOLE_Y) - HOLE_R) <= 3.0 * L0_MM)]
    w4_ligament = [e for e in elements_data if (0.53 <= e["cx"] <= 0.65 and 0.50 <= e["cy"] <= 0.60)]

    # 4. Along-Path Trajectory Discretization (Finding F1731-R06)
    # Oblique trajectory from (0.50, 0.50) to (0.65, 0.55). Parametric station s in [0, 1].
    # Segment stations: 10 bins along s, width delta_s = 0.10.
    trajectory_stations = []
    x0, y0 = 0.50, 0.50
    x1, y1 = 0.65, 0.55
    dx = x1 - x0
    dy = y1 - y0
    traj_len = math.hypot(dx, dy)

    for i in range(10):
        s_min = i * 0.10
        s_max = (i + 1) * 0.10
        bin_elems = []
        for e in elements_data:
            # Project (cx, cy) onto line segment
            vx = e["cx"] - x0
            vy = e["cy"] - y0
            proj = (vx * dx + vy * dy) / (traj_len * traj_len)
            perp_dist = abs(vx * dy - vy * dx) / traj_len
            if s_min <= proj <= s_max and perp_dist <= 2.5 * L0_MM:
                bin_elems.append(e)

        station_stat = evaluate_subset_stats(bin_elems)
        station_stat["station_index"] = i + 1
        station_stat["s_range"] = [round(s_min, 2), round(s_max, 2)]
        station_stat["center_coord"] = [round(x0 + (s_min + 0.05)*dx, 4), round(y0 + (s_min + 0.05)*dy, 4)]
        trajectory_stations.append(station_stat)

    # 5. Global Metrics
    global_stat = evaluate_subset_stats(elements_data)

    results = {
        "mesh_inp": os.path.basename(inp_path),
        "total_nodes": total_nodes,
        "total_elements": total_elements,
        "quad_elements": len(quad_elems),
        "tri_elements": len(tri_elems),
        "quad_fraction_pct": quad_pct,
        "tri_fraction_pct": tri_pct,
        "min_signed_jacobian": min_det_j,
        "non_positive_jacobians": non_pos_j,
        "mean_aspect_ratio": mean_ar,
        "max_aspect_ratio": max_ar,
        "global_resolution": global_stat,
        "mutually_exclusive_partition": {
            "P1_NOTCH_ROOT": evaluate_subset_stats(p1_notch),
            "P2_PRIMARY_CORRIDOR_EXCL_NOTCH": evaluate_subset_stats(p2_corridor_excl),
            "P3_HOLE_RING_EXCL_CORRIDOR": evaluate_subset_stats(p3_hole_ring_excl),
            "P4_FAR_FIELD_BULK": evaluate_subset_stats(p4_bulk)
        },
        "overlapping_diagnostic_windows": {
            "W1_FULL_NOTCH_ROOT": evaluate_subset_stats(w1_notch),
            "W2_FULL_PRIMARY_CORRIDOR": evaluate_subset_stats(w2_corridor),
            "W3_FULL_HOLE_RING": evaluate_subset_stats(w3_hole_ring),
            "W4_UNCRACKED_LIGAMENT": evaluate_subset_stats(w4_ligament)
        },
        "along_path_trajectory_stations": trajectory_stations
    }

    with open(out_json_path, "w") as f:
        json.dump(results, f, indent=2)

    print("Audit JSON successfully written: %s" % out_json_path)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python audit_case2_calibrated_resolution.py <input.inp> <output.json>")
        sys.exit(1)
    audit_mesh(sys.argv[1], sys.argv[2])

# -*- coding: utf-8 -*-
"""
audit_case2_ligament_resolution.py
===================================
Independent, reproducible spatial-resolution audit of the Case 2 Off-Axis Hole adapted mesh
(PK_F1728_CASE_2_ADAPT_PHYS.inp) along the primary oblique crack corridor (notch tip to hole),
the hole boundary ligament, the secondary uncracked right-flank ligament, and the far-field bulk.

Evaluates:
  - Total physical elements and nodes
  - Quad fraction (%) and Triangle fraction (%)
  - Minimum signed Jacobian det(J) and Jacobian validity (PASS/FAIL)
  - Element sizing: h_area = sqrt(Area) and h_max_edge across all elements
  - Spatial resolution tests against physical thresholds:
      h <= l0     = 0.00750 mm (7.50 um)
      h <= l0/2   = 0.00375 mm (3.75 um)
      h <= l0/3   = 0.00250 mm (2.50 um)
  - Region-specific statistics:
      * Notch root core: x in [0.50, 0.53], y in [0.49, 0.51]
      * Primary oblique corridor: notch tip (0.50, 0.50) to hole perimeter (0.65, 0.55)
      * Hole boundary ring: distance to hole perimeter <= 3 * l0 (0.0225 mm)
      * Secondary right-flank corridor: x in [0.75, 1.00], y in [0.60, 0.70]
      * Far-field bulk: all other elements
  - Outputs structured JSON receipt to f1731_case2_ligament_spatial_audit.json.
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
        # Shoelace formula
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

        # 2x2 Gauss Jacobian for quad
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

        # Constant Jacobian for 3-node triangle: 2 * Area
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

def classify_spatial_region(cx, cy):
    # 1. Notch tip root
    if 0.50 <= cx <= 0.53 and 0.49 <= cy <= 0.51:
        return "NOTCH_ROOT"

    # 2. Distance to hole perimeter
    dist_hole_center = math.hypot(cx - HOLE_X, cy - HOLE_Y)
    dist_hole_perimeter = abs(dist_hole_center - HOLE_R)
    if dist_hole_perimeter <= 3.0 * L0_MM:
        return "HOLE_BOUNDARY_RING"

    # 3. Primary oblique ligament (connecting notch tip (0.50, 0.50) to hole perimeter)
    # Line connecting (0.50, 0.50) to (0.65, 0.55): dy/dx = 0.05 / 0.15 = 1/3
    if 0.50 <= cx <= 0.65 and 0.47 <= cy <= 0.60:
        return "PRIMARY_OBLIQUE_LIGAMENT"

    # 4. Secondary right-flank uncracked ligament
    if 0.75 <= cx <= 1.00 and 0.58 <= cy <= 0.72:
        return "SECONDARY_RIGHT_LIGAMENT"

    return "FAR_FIELD_BULK"

def audit_mesh(inp_path, out_json_path):
    print("=== Spatial Resolution Audit for Case 2 Adapted Mesh ===")
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

    # Global Jacobian and Quality Audit
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

    # Regional Classification and Resolution Metrics
    regions = {
        "NOTCH_ROOT": [],
        "PRIMARY_OBLIQUE_LIGAMENT": [],
        "HOLE_BOUNDARY_RING": [],
        "SECONDARY_RIGHT_LIGAMENT": [],
        "FAR_FIELD_BULK": []
    }

    for e in elements_data:
        r = classify_spatial_region(e["cx"], e["cy"])
        regions[r].append(e)

    region_stats = {}
    for rname, r_elems in regions.items():
        count = len(r_elems)
        if count == 0:
            region_stats[rname] = {"count": 0}
            continue

        h_vals = [e["h_area"] for e in r_elems]
        h_edges = [e["max_edge"] for e in r_elems]

        n_le_l0 = sum(1 for h in h_vals if h <= L0_MM)
        n_le_l0_half = sum(1 for h in h_vals if h <= L0_HALF)
        n_le_l0_third = sum(1 for h in h_vals if h <= L0_THIRD)

        mean_h = sum(h_vals) / float(count)
        min_h = min(h_vals)
        max_h = max(h_vals)

        region_stats[rname] = {
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
        print("  Region %-26s: N=%5d, Mean h=%.2f um, Min=%.2f um, %%<=l0/2: %.1f%%" % (
            rname, count, mean_h * 1000.0, min_h * 1000.0, 100.0 * n_le_l0_half / float(count)
        ))

    # Overall Global Metrics
    all_h = [e["h_area"] for e in elements_data]
    global_n_le_l0 = sum(1 for h in all_h if h <= L0_MM)
    global_n_le_l0_half = sum(1 for h in all_h if h <= L0_HALF)
    global_n_le_l0_third = sum(1 for h in all_h if h <= L0_THIRD)

    summary = {
        "mesh_path": os.path.basename(inp_path),
        "total_physical_elements": total_elements,
        "total_nodes": total_nodes,
        "quad_elements": len(quad_elems),
        "tri_elements": len(tri_elems),
        "quad_fraction_pct": quad_pct,
        "tri_fraction_pct": tri_pct,
        "min_signed_jacobian": min_det_j,
        "non_positive_jacobians": non_pos_j,
        "jacobian_valid": (non_pos_j == 0),
        "mean_aspect_ratio": mean_ar,
        "max_aspect_ratio": max_ar,
        "l0_mm": L0_MM,
        "l0_half_mm": L0_HALF,
        "l0_third_mm": L0_THIRD,
        "global_resolution": {
            "mean_h_area_um": (sum(all_h) / float(total_elements)) * 1000.0,
            "min_h_area_um": min(all_h) * 1000.0,
            "max_h_area_um": max(all_h) * 1000.0,
            "pct_le_l0": 100.0 * global_n_le_l0 / float(total_elements),
            "pct_le_l0_half": 100.0 * global_n_le_l0_half / float(total_elements),
            "pct_le_l0_third": 100.0 * global_n_le_l0_third / float(total_elements)
        },
        "regions": region_stats,
        "resolution_verdict": {
            "notch_root_resolved_l0_third": (region_stats["NOTCH_ROOT"]["min_h_area_mm"] <= L0_THIRD) if "NOTCH_ROOT" in region_stats and region_stats["NOTCH_ROOT"]["count"] > 0 else False,
            "primary_corridor_mean_h_um": region_stats["PRIMARY_OBLIQUE_LIGAMENT"]["mean_h_area_um"] if "PRIMARY_OBLIQUE_LIGAMENT" in region_stats and region_stats["PRIMARY_OBLIQUE_LIGAMENT"]["count"] > 0 else None,
            "primary_corridor_resolved_l0_half": (region_stats["PRIMARY_OBLIQUE_LIGAMENT"]["pct_le_l0_half"] >= 50.0) if "PRIMARY_OBLIQUE_LIGAMENT" in region_stats and region_stats["PRIMARY_OBLIQUE_LIGAMENT"]["count"] > 0 else False,
            "hole_boundary_resolved_l0": (region_stats["HOLE_BOUNDARY_RING"]["pct_le_l0"] >= 50.0) if "HOLE_BOUNDARY_RING" in region_stats and region_stats["HOLE_BOUNDARY_RING"]["count"] > 0 else False,
            "far_field_mean_h_um": region_stats["FAR_FIELD_BULK"]["mean_h_area_um"] if "FAR_FIELD_BULK" in region_stats and region_stats["FAR_FIELD_BULK"]["count"] > 0 else None
        }
    }

    with open(out_json_path, "w") as f:
        json.dump(summary, f, indent=2)
    print("Summary written to: %s" % out_json_path)
    return summary

if __name__ == "__main__":
    if len(sys.argv) < 2:
        inp = "PK_F1728_CASE_2_ADAPT_PHYS.inp"
        out_j = "f1731_case2_ligament_spatial_audit.json"
    else:
        inp = sys.argv[1]
        out_j = sys.argv[2] if len(sys.argv) > 2 else "f1731_case2_ligament_spatial_audit.json"
    audit_mesh(inp, out_j)

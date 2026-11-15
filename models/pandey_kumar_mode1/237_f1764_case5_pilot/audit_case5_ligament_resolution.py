# -*- coding: utf-8 -*-
"""
models/pandey_kumar_mode1/237_f1764_case5_pilot/audit_case5_ligament_resolution.py
================================================================================
Spatial Resolution & FE Mesh Quality Audit for Task F1764:
Case 5: Pandey & Kumar (2025) Section 4.6 Plate with Seven Holes (1x1 mm).

Evaluates:
1. Overall FE topology, element and node counts, quad percentage (Gate G1 & G2).
2. Signed isoparametric integration-point Jacobians (det(J) > 0) (Gate G3).
3. Maximum and mean aspect ratio (Gate G4).
4. Upper active fracture corridor (connecting h1 -> h4 -> h2 -> h5 -> h3) (Gate G5).
5. Lower shielded hole 6 (h6) resolution (Gate G6).
6. Lower shielded hole 7 (h7) resolution (Gate G7).
7. Far-field bulk coarsening control (Gate G8).
"""
import os
import sys
import math
import json


def parse_inp_mesh(inp_path):
    """Parses an Abaqus physical .inp mesh into nodes, elements, and element types."""
    nodes = {}
    elements = {}
    elem_types = {}

    in_nodes = False
    in_elements = False
    current_elem_type = 'CPE4'

    with open(inp_path, "r") as f:
        for line in f:
            line_str = line.strip()
            if not line_str or line_str.startswith("**"):
                continue

            if line_str.startswith("*"):
                in_nodes = False
                in_elements = False
                upper = line_str.upper()
                if upper.startswith("*NODE") and not any(upper.startswith(x) for x in ["*NODE OUTPUT", "*NODE PRINT", "*NODE FILE"]):
                    in_nodes = True
                elif upper.startswith("*ELEMENT") and not any(upper.startswith(x) for x in ["*ELEMENT OUTPUT", "*ELEMENT PRINT", "*ELEMENT FILE"]):
                    in_elements = True
                    if "CPE4" in upper or "CPS4" in upper or "QUAD" in upper:
                        current_elem_type = "CPE4"
                    elif "CPE3" in upper or "CPS3" in upper or "TRI" in upper:
                        current_elem_type = "CPE3"
                    else:
                        current_elem_type = "CPE4"
                continue

            parts = [p.strip() for p in line_str.split(",") if p.strip()]
            if in_nodes:
                if len(parts) >= 3:
                    try:
                        nid = int(parts[0])
                        nodes[nid] = (float(parts[1]), float(parts[2]))
                    except ValueError:
                        pass
            elif in_elements:
                if len(parts) >= 4:
                    try:
                        eid = int(parts[0])
                        conn = tuple(int(p) for p in parts[1:])
                        elements[eid] = conn
                        elem_types[eid] = current_elem_type
                    except ValueError:
                        pass

    return nodes, elements, elem_types


def dist_to_segments(px, py, segs):
    """Computes minimum Euclidean distance from point (px, py) to a polyline."""
    min_d = 1e9
    for (x1, y1), (x2, y2) in segs:
        dx, dy = x2 - x1, y2 - y1
        l2 = dx*dx + dy*dy
        t = max(0.0, min(1.0, ((px - x1)*dx + (py - y1)*dy) / l2)) if l2 > 0 else 0.0
        d = math.hypot(px - (x1 + t*dx), py - (y1 + t*dy))
        if d < min_d:
            min_d = d
    return min_d


def compute_case5_metrics(nodes, elements, elem_types, l0=0.008):
    """Computes comprehensive mesh quality and spatial metrics for Seven-Hole Plate."""
    l0_um = l0 * 1000.0  # 8.0 um
    half_l0_um = l0_um / 2.0  # 4.0 um

    total_elements = len(elements)
    total_nodes = len(nodes)
    quad_count = sum(1 for conn in elements.values() if len(conn) == 4)
    tri_count = sum(1 for conn in elements.values() if len(conn) == 3)
    quad_pct = round(100.0 * quad_count / max(total_elements, 1), 2)

    min_det_j = 1e9
    negative_j_count = 0
    max_ar = 0.0
    sum_ar = 0.0

    # Active upper fracture corridor segments connecting h1 -> h4 -> h2 -> h5 -> h3:
    upper_segments = [
        ((0.15, 0.40), (0.30, 0.60)),
        ((0.30, 0.60), (0.50, 0.55)),
        ((0.50, 0.55), (0.70, 0.60)),
        ((0.70, 0.60), (0.85, 0.50))
    ]

    elements_data = []

    for eid, conn in elements.items():
        pts = [nodes[nid] for nid in conn]
        n_pts = len(pts)

        if n_pts == 4:
            # 4-node quad: Surveyor formula for area
            area = 0.5 * abs(
                (pts[0][0]*pts[1][1] - pts[1][0]*pts[0][1]) +
                (pts[1][0]*pts[2][1] - pts[2][0]*pts[1][1]) +
                (pts[2][0]*pts[3][1] - pts[3][0]*pts[2][1]) +
                (pts[3][0]*pts[0][1] - pts[0][0]*pts[3][1])
            )
            cx = sum(p[0] for p in pts) / 4.0
            cy = sum(p[1] for p in pts) / 4.0

            edges = [
                math.hypot(pts[1][0] - pts[0][0], pts[1][1] - pts[0][1]),
                math.hypot(pts[2][0] - pts[1][0], pts[2][1] - pts[1][1]),
                math.hypot(pts[3][0] - pts[2][0], pts[3][1] - pts[2][1]),
                math.hypot(pts[0][0] - pts[3][0], pts[0][1] - pts[3][1])
            ]
            ar = max(edges) / max(min(edges), 1e-12)

            # 2x2 Gauss integration Jacobian check
            gp = 1.0 / math.sqrt(3.0)
            gauss_pts = [(-gp, -gp), (gp, -gp), (gp, gp), (-gp, gp)]
            elem_min_j = 1e9
            for xi, eta in gauss_pts:
                # Shape function derivatives
                dN_dxi = [
                    -0.25*(1.0 - eta),  0.25*(1.0 - eta),
                     0.25*(1.0 + eta), -0.25*(1.0 + eta)
                ]
                dN_deta = [
                    -0.25*(1.0 - xi),  -0.25*(1.0 + xi),
                     0.25*(1.0 + xi),   0.25*(1.0 - xi)
                ]
                j11 = sum(dN_dxi[i] * pts[i][0] for i in range(4))
                j12 = sum(dN_dxi[i] * pts[i][1] for i in range(4))
                j21 = sum(dN_deta[i] * pts[i][0] for i in range(4))
                j22 = sum(dN_deta[i] * pts[i][1] for i in range(4))
                det_j = j11*j22 - j12*j21
                if det_j < elem_min_j:
                    elem_min_j = det_j

            if elem_min_j < min_det_j:
                min_det_j = elem_min_j
            if elem_min_j <= 0.0:
                negative_j_count += 1

        elif n_pts == 3:
            # 3-node tri
            area = 0.5 * abs(
                pts[0][0]*(pts[1][1] - pts[2][1]) +
                pts[1][0]*(pts[2][1] - pts[0][1]) +
                pts[2][0]*(pts[0][1] - pts[1][1])
            )
            cx = sum(p[0] for p in pts) / 3.0
            cy = sum(p[1] for p in pts) / 3.0

            edges = [
                math.hypot(pts[1][0] - pts[0][0], pts[1][1] - pts[0][1]),
                math.hypot(pts[2][0] - pts[1][0], pts[2][1] - pts[1][1]),
                math.hypot(pts[0][0] - pts[2][0], pts[0][1] - pts[2][1])
            ]
            ar = max(edges) / max(min(edges), 1e-12)

            det_j = (pts[1][0] - pts[0][0])*(pts[2][1] - pts[0][1]) - (pts[2][0] - pts[0][0])*(pts[1][1] - pts[0][1])
            if det_j < min_det_j:
                min_det_j = det_j
            if det_j <= 0.0:
                negative_j_count += 1

        else:
            continue

        h_e = math.sqrt(area) * 1000.0  # um
        if ar > max_ar:
            max_ar = ar
        sum_ar += ar

        elements_data.append({
            "eid": eid, "type": "quad" if n_pts == 4 else "tri",
            "cx": cx, "cy": cy, "area_mm2": area, "h_um": h_e, "ar": ar
        })

    mean_ar = sum_ar / max(total_elements, 1)

    # Classify elements into regions:
    # 1. Upper corridor: distance to upper segments <= 0.040 mm
    # 2. Lower hole 6: proximity to boundary of h6 (cx=0.40, cy=0.35, r=0.05) <= 0.024 mm (3*l0)
    # 3. Lower hole 7: proximity to boundary of h7 (cx=0.65, cy=0.35, r=0.05) <= 0.024 mm (3*l0)
    # 4. Bulk far-field: remaining elements
    upper_corridor = []
    lower_h6 = []
    lower_h7 = []
    bulk = []

    for d in elements_data:
        cx, cy = d["cx"], d["cy"]
        dist_upper = dist_to_segments(cx, cy, upper_segments)
        d_h6 = abs(math.hypot(cx - 0.40, cy - 0.35) - 0.05)
        d_h7 = abs(math.hypot(cx - 0.65, cy - 0.35) - 0.05)

        if dist_upper <= 0.040:
            upper_corridor.append(d)
        elif d_h6 <= 0.024:
            lower_h6.append(d)
        elif d_h7 <= 0.024:
            lower_h7.append(d)
        else:
            bulk.append(d)

    def stats_for_group(group):
        if not group:
            return {
                "count": 0, "min_h_um": 0.0, "max_h_um": 0.0, "mean_h_um": 0.0,
                "frac_count_le_l0": 0.0, "frac_count_le_half_l0": 0.0,
                "frac_area_le_l0": 0.0, "frac_area_le_half_l0": 0.0,
                "total_area_mm2": 0.0
            }
        tot_area = sum(d["area_mm2"] for d in group)
        h_vals = [d["h_um"] for d in group]
        count_le_l0 = sum(1 for h in h_vals if h <= l0_um)
        count_le_half_l0 = sum(1 for h in h_vals if h <= half_l0_um)
        area_le_l0 = sum(d["area_mm2"] for d in group if d["h_um"] <= l0_um)
        area_le_half_l0 = sum(d["area_mm2"] for d in group if d["h_um"] <= half_l0_um)

        return {
            "count": len(group),
            "min_h_um": round(min(h_vals), 3),
            "max_h_um": round(max(h_vals), 3),
            "mean_h_um": round(sum(h_vals) / len(group), 3),
            "frac_count_le_l0": round(count_le_l0 / len(group), 4),
            "frac_count_le_half_l0": round(count_le_half_l0 / len(group), 4),
            "frac_area_le_l0": round(area_le_l0 / max(tot_area, 1e-12), 4),
            "frac_area_le_half_l0": round(area_le_half_l0 / max(tot_area, 1e-12), 4),
            "total_area_mm2": round(tot_area, 6)
        }

    return {
        "total_elements": total_elements,
        "total_nodes": total_nodes,
        "quad_elements": quad_count,
        "tri_elements": tri_count,
        "quad_percentage": quad_pct,
        "min_det_jacobian": min_det_j,
        "negative_jacobians": negative_j_count,
        "jacobian_valid": (negative_j_count == 0 and min_det_j > 0.0),
        "max_aspect_ratio": round(max_ar, 3),
        "mean_aspect_ratio": round(mean_ar, 3),
        "global_mesh": stats_for_group(elements_data),
        "upper_corridor": stats_for_group(upper_corridor),
        "lower_h6": stats_for_group(lower_h6),
        "lower_h7": stats_for_group(lower_h7),
        "bulk_far_field": stats_for_group(bulk)
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python audit_case5_ligament_resolution.py <input_mesh.inp> [output_audit.json]")
        sys.exit(1)

    inp_path = os.path.abspath(sys.argv[1])
    out_json = os.path.abspath(sys.argv[2]) if len(sys.argv) >= 3 else None

    if not os.path.exists(inp_path):
        print("Error: Input mesh file does not exist: %s" % inp_path)
        sys.exit(1)

    nodes, elements, elem_types = parse_inp_mesh(inp_path)
    metrics = compute_case5_metrics(nodes, elements, elem_types, l0=0.008)

    print("=== Case 5 Spatial Resolution & Mesh Quality Audit ===")
    print("Mesh: %s" % inp_path)
    print("Total Elements: %d (Quads: %d [%.2f%%], Tris: %d)" % (
        metrics["total_elements"], metrics["quad_elements"], metrics["quad_percentage"], metrics["tri_elements"]
    ))
    print("Total Nodes: %d" % metrics["total_nodes"])
    print("Min Signed det(J): %.3e (Negative Jacobians: %d)" % (
        metrics["min_det_jacobian"], metrics["negative_jacobians"]
    ))
    print("Max Aspect Ratio: %.3f (Mean: %.3f)" % (
        metrics["max_aspect_ratio"], metrics["mean_aspect_ratio"]
    ))
    print("\n--- Upper Fracture Corridor (h1 -> h4 -> h2 -> h5 -> h3) ---")
    uc = metrics["upper_corridor"]
    print("  Count: %d | Mean h: %.2f um | Range: [%.2f, %.2f] um" % (
        uc["count"], uc["mean_h_um"], uc["min_h_um"], uc["max_h_um"]
    ))
    print("  Count <= l0: %.1f%% | Area <= l0: %.1f%%" % (
        uc["frac_count_le_l0"] * 100.0, uc["frac_area_le_l0"] * 100.0
    ))
    print("\n--- Lower Shielded Hole 6 (h6) ---")
    h6 = metrics["lower_h6"]
    print("  Count: %d | Mean h: %.2f um | Count <= l0: %.1f%%" % (
        h6["count"], h6["mean_h_um"], h6["frac_count_le_l0"] * 100.0
    ))
    print("\n--- Lower Shielded Hole 7 (h7) ---")
    h7 = metrics["lower_h7"]
    print("  Count: %d | Mean h: %.2f um | Count <= l0: %.1f%%" % (
        h7["count"], h7["mean_h_um"], h7["frac_count_le_l0"] * 100.0
    ))
    print("\n--- Bulk Far-Field ---")
    bf = metrics["bulk_far_field"]
    print("  Count: %d | Mean h: %.2f um | Area <= l0: %.1f%%" % (
        bf["count"], bf["mean_h_um"], bf["frac_area_le_l0"] * 100.0
    ))

    if out_json:
        os.makedirs(os.path.dirname(out_json), exist_ok=True)
        with open(out_json, "w") as f:
            json.dump(metrics, f, indent=2)
        print("\nAudit receipt saved to: %s" % out_json)


if __name__ == '__main__':
    main()

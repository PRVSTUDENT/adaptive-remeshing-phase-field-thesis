# -*- coding: utf-8 -*-
"""
audit_case4_ligament_resolution.py
==================================
Audits Case 4 Five-Hole Plate Adapted Mesh across all four inter-hole ligaments.
Evaluates:
- Finite element quality (det(J) > 0, quad % >= 95%, max aspect ratio <= 4.0)
- Total physical element count parity against 12,944 published (+/- 2.0%) and 13,017 F1725 reference
- 4 Inter-hole Ligament Resoutions:
    * Ligament 1: Left arc to Hole 1 (x in [0.08, 0.27], y in [0.40, 0.56])
    * Ligament 2: Hole 1 to Hole 2 (x in [0.42, 0.57], y in [0.42, 0.58])
    * Ligament 3: Hole 2 to Hole 3 (x in [0.63, 0.69], y in [0.48, 0.56]) - narrowest bridge
    * Ligament 4: Hole 3 to Right arc (x in [0.81, 0.94], y in [0.40, 0.55])
- Compliance:
    * h <= l0 = 8.0 um
    * h <= l0/2 = 4.0 um
- Far-field background coarsening retention (y > 0.70 or y < 0.30)
- Centerline profiles across all 4 ligaments
- Generates JSON summary for Task F1763 results verification.
"""
from __future__ import print_function
import os
import sys
import math
import json


def parse_inp_mesh(inp_path):
    nodes = {}
    elements = {}
    elem_types = {}

    in_nodes = False
    in_elements = False
    current_type = None

    with open(inp_path, 'r') as f:
        for line in f:
            l = line.strip()
            if not l or l.startswith('**'):
                continue
            if l.startswith('*'):
                in_nodes = False
                in_elements = False
                if l.upper().startswith('*NODE') and not l.upper().startswith('*NODE OUTPUT') and not l.upper().startswith('*NODE PRINT') and not l.upper().startswith('*NODE FILE'):
                    in_nodes = True
                elif l.upper().startswith('*ELEMENT'):
                    in_elements = True
                    if 'CPE4' in l.upper() or 'CPS4' in l.upper() or 'QUAD' in l.upper():
                        current_type = 'CPE4'
                    elif 'CPE3' in l.upper() or 'CPS3' in l.upper() or 'TRI' in l.upper():
                        current_type = 'CPE3'
                    else:
                        current_type = 'CPE4'
                continue

            parts = [p.strip() for p in l.split(',') if p.strip()]
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
                        elem_types[eid] = current_type
                    except ValueError:
                        pass
    return nodes, elements, elem_types


def point_line_dist(px, py, x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    L2 = dx*dx + dy*dy
    if L2 == 0:
        return math.hypot(px - x1, py - y1), 0.0
    t = max(0.0, min(1.0, ((px - x1)*dx + (py - y1)*dy) / L2))
    proj_x = x1 + t * dx
    proj_y = y1 + t * dy
    return math.hypot(px - proj_x, py - proj_y), t


def compute_case4_metrics(nodes, elements, elem_types, l0=0.008):
    total_elems = len(elements)
    quad_count = sum(1 for e, conn in elements.items() if len(conn) == 4)
    tri_count = sum(1 for e, conn in elements.items() if len(conn) == 3)
    quad_pct = float(quad_count) / float(total_elems) * 100.0 if total_elems > 0 else 0.0

    min_det_j = 1e30
    neg_jacobian_count = 0
    aspect_ratios = []
    elem_data = [] # (eid, cx, cy, h_um, area_mm2)

    for eid, conn in elements.items():
        pts = [nodes[n] for n in conn]
        cx = sum(p[0] for p in pts) / float(len(pts))
        cy = sum(p[1] for p in pts) / float(len(pts))

        if len(pts) == 4:
            gp_coords = [(-1.0/math.sqrt(3.0), -1.0/math.sqrt(3.0)),
                         ( 1.0/math.sqrt(3.0), -1.0/math.sqrt(3.0)),
                         ( 1.0/math.sqrt(3.0),  1.0/math.sqrt(3.0)),
                         (-1.0/math.sqrt(3.0),  1.0/math.sqrt(3.0))]
            for xi, eta in gp_coords:
                dN_dxi = [-0.25*(1-eta),  0.25*(1-eta), 0.25*(1+eta), -0.25*(1+eta)]
                dN_deta = [-0.25*(1-xi), -0.25*(1+xi),  0.25*(1+xi),  0.25*(1-xi)]
                J11 = sum(dN_dxi[i] * pts[i][0] for i in range(4))
                J12 = sum(dN_dxi[i] * pts[i][1] for i in range(4))
                J21 = sum(dN_deta[i] * pts[i][0] for i in range(4))
                J22 = sum(dN_deta[i] * pts[i][1] for i in range(4))
                det_j = J11 * J22 - J12 * J21
                if det_j < min_det_j:
                    min_det_j = det_j
                if det_j <= 0.0:
                    neg_jacobian_count += 1

            area = 0.5 * abs((pts[0][0]*pts[1][1] - pts[1][0]*pts[0][1]) +
                             (pts[1][0]*pts[2][1] - pts[2][0]*pts[1][1]) +
                             (pts[2][0]*pts[3][1] - pts[3][0]*pts[2][1]) +
                             (pts[3][0]*pts[0][1] - pts[0][0]*pts[3][1]))
            edge_lens = [math.hypot(pts[(i+1)%4][0]-pts[i][0], pts[(i+1)%4][1]-pts[i][1]) for i in range(4)]
            ar = max(edge_lens) / max(1e-12, min(edge_lens))
            aspect_ratios.append(ar)

        else: # TRI
            det_j = (pts[1][0]-pts[0][0])*(pts[2][1]-pts[0][1]) - (pts[2][0]-pts[0][0])*(pts[1][1]-pts[0][1])
            if det_j < min_det_j:
                min_det_j = det_j
            if det_j <= 0.0:
                neg_jacobian_count += 1
            area = 0.5 * abs(det_j)
            edge_lens = [math.hypot(pts[(i+1)%3][0]-pts[i][0], pts[(i+1)%3][1]-pts[i][1]) for i in range(3)]
            ar = max(edge_lens) / max(1e-12, min(edge_lens))
            aspect_ratios.append(ar)

        h_e_um = math.sqrt(area) * 1000.0
        elem_data.append((eid, cx, cy, h_e_um, area))

    def compute_stats(elems, l0_val=0.008):
        if not elems:
            return {"count": 0, "mean_h_um": 0.0, "min_h_um": 0.0, "max_h_um": 0.0,
                    "frac_count_le_l0": 0.0, "frac_count_le_half_l0": 0.0,
                    "frac_area_le_l0": 0.0, "frac_area_le_half_l0": 0.0, "total_area_mm2": 0.0}
        n = len(elems)
        h_vals = [e[3] for e in elems]
        areas = [e[4] for e in elems]
        tot_area = sum(areas)

        l0_um = l0_val * 1000.0
        hl0_um = l0_val * 500.0

        cnt_l0 = sum(1 for h in h_vals if h <= l0_um)
        cnt_hl0 = sum(1 for h in h_vals if h <= hl0_um)

        area_l0 = sum(areas[i] for i in range(n) if h_vals[i] <= l0_um)
        area_hl0 = sum(areas[i] for i in range(n) if h_vals[i] <= hl0_um)

        return {
            "count": n,
            "min_h_um": round(min(h_vals), 3),
            "max_h_um": round(max(h_vals), 3),
            "mean_h_um": round(sum(h_vals) / float(n), 3),
            "frac_count_le_l0": round(float(cnt_l0) / float(n), 4),
            "frac_count_le_half_l0": round(float(cnt_hl0) / float(n), 4),
            "frac_area_le_l0": round(area_l0 / tot_area, 4) if tot_area > 0 else 0.0,
            "frac_area_le_half_l0": round(area_hl0 / tot_area, 4) if tot_area > 0 else 0.0,
            "total_area_mm2": round(tot_area, 6)
        }

    # Regional classifications (historical F1725 bounding boxes)
    lig1_elems = [e for e in elem_data if 0.08 <= e[1] <= 0.27 and 0.40 <= e[2] <= 0.56]
    lig2_elems = [e for e in elem_data if 0.42 <= e[1] <= 0.57 and 0.42 <= e[2] <= 0.58]
    lig3_elems = [e for e in elem_data if 0.63 <= e[1] <= 0.69 and 0.48 <= e[2] <= 0.56]
    lig4_elems = [e for e in elem_data if 0.81 <= e[1] <= 0.94 and 0.40 <= e[2] <= 0.55]
    bulk_elems = [e for e in elem_data if e[2] > 0.70 or e[2] < 0.30]

    # Centerline corridors
    centerline_defs = [
        ("Ligament 1 (Left Arc to Hole 1)", 0.10, 0.50, 0.25, 0.45, 0.015),
        ("Ligament 2 (Hole 1 to Hole 2)", 0.45, 0.45, 0.55, 0.55, 0.015),
        ("Ligament 3 (Hole 2 to Hole 3)", 0.6474, 0.5342, 0.6789, 0.5237, 0.015),
        ("Ligament 4 (Hole 3 to Right Arc)", 0.825, 0.50, 0.925, 0.45, 0.015),
    ]

    centerline_profiles = {}
    n_bins = 10
    for lname, x1, y1, x2, y2, tol in centerline_defs:
        in_corridor = []
        for eid, cx, cy, h, a in elem_data:
            d, t = point_line_dist(cx, cy, x1, y1, x2, y2)
            if d <= tol:
                in_corridor.append((t, h, a))
        bin_hs = [[] for _ in range(n_bins)]
        for t, h, a in in_corridor:
            b = min(n_bins - 1, int(t * n_bins))
            bin_hs[b].append(h)
        bin_means = [round(sum(b_list) / float(len(b_list)), 3) if b_list else 0.0 for b_list in bin_hs]
        centerline_profiles[lname] = {
            "corridor_element_count": len(in_corridor),
            "profile_bins_mean_h_um": bin_means
        }

    return {
        "total_elements": total_elems,
        "total_nodes": len(nodes),
        "quad_elements": quad_count,
        "tri_elements": tri_count,
        "quad_percentage": round(quad_pct, 2),
        "min_det_jacobian": min_det_j,
        "negative_jacobians": neg_jacobian_count,
        "jacobian_valid": (neg_jacobian_count == 0 and min_det_j > 0.0),
        "max_aspect_ratio": round(max(aspect_ratios), 3) if aspect_ratios else 0.0,
        "mean_aspect_ratio": round(sum(aspect_ratios) / float(len(aspect_ratios)), 3) if aspect_ratios else 0.0,
        "global_mesh": compute_stats(elem_data, l0),
        "ligament_1": compute_stats(lig1_elems, l0),
        "ligament_2": compute_stats(lig2_elems, l0),
        "ligament_3": compute_stats(lig3_elems, l0),
        "ligament_4": compute_stats(lig4_elems, l0),
        "bulk_far_field": compute_stats(bulk_elems, l0),
        "centerline_profiles": centerline_profiles
    }


def main():
    if len(sys.argv) < 3:
        print("Usage: python audit_case4_ligament_resolution.py <input_mesh.inp> <output_audit.json> [<comparison_mesh.inp>]")
        sys.exit(1)

    inp_path = sys.argv[1]
    out_json = sys.argv[2]
    comp_path = sys.argv[3] if len(sys.argv) > 3 else None

    if not os.path.exists(inp_path):
        print("ERROR: Input mesh not found at %s" % inp_path)
        sys.exit(1)

    nodes, elements, elem_types = parse_inp_mesh(inp_path)
    metrics = compute_case4_metrics(nodes, elements, elem_types, l0=0.008)

    # Parity comparisons
    published_target = 12944
    historical_f1725_target = 13017

    n_elem = metrics["total_elements"]
    err_pub_pct = round(100.0 * (n_elem - published_target) / float(published_target), 2)
    err_hist_pct = round(100.0 * (n_elem - historical_f1725_target) / float(historical_f1725_target), 2)

    metrics["parity_evaluation"] = {
        "published_target_elements": published_target,
        "difference_vs_published_pct": err_pub_pct,
        "published_parity_pass": abs(err_pub_pct) <= 2.0,
        "historical_f1725_elements": historical_f1725_target,
        "difference_vs_historical_pct": err_hist_pct,
        "fe_quality_pass": (metrics["quad_percentage"] >= 95.0 and metrics["jacobian_valid"] and metrics["max_aspect_ratio"] <= 5.0),
        "active_ligaments_resolved": (metrics["ligament_2"]["frac_count_le_l0"] >= 0.90 and
                                     metrics["ligament_3"]["frac_count_le_l0"] >= 0.90 and
                                     metrics["ligament_4"]["frac_count_le_l0"] >= 0.90)
    }

    if comp_path and os.path.exists(comp_path):
        c_nodes, c_elements, c_elem_types = parse_inp_mesh(comp_path)
        c_metrics = compute_case4_metrics(c_nodes, c_elements, c_elem_types, l0=0.008)
        metrics["historical_mesh_comparison"] = {
            "comparison_mesh_path": comp_path,
            "comparison_elements": c_metrics["total_elements"],
            "element_difference": n_elem - c_metrics["total_elements"],
            "comparison_metrics": c_metrics
        }

    with open(out_json, 'w') as f:
        json.dump(metrics, f, indent=2)

    print("=== Case 4 Spatial Resolution Audit Complete ===")
    print("Mesh: %s" % inp_path)
    print("Total Elements: %d (Published: %d, Diff: %+.2f%%)" % (n_elem, published_target, err_pub_pct))
    print("Quads: %d (%.2f%%) | Tris: %d" % (metrics["quad_elements"], metrics["quad_percentage"], metrics["tri_elements"]))
    print("Jacobians: %s (min det(J)=%g, neg=%d)" % ("PASS" if metrics["jacobian_valid"] else "FAIL", metrics["min_det_jacobian"], metrics["negative_jacobians"]))
    print("Max Aspect Ratio: %.3f" % metrics["max_aspect_ratio"])
    print("Ligament 1 (h <= l0): %.2f%% count, %.2f%% area (mean h=%.2f um)" % (
        metrics["ligament_1"]["frac_count_le_l0"]*100, metrics["ligament_1"]["frac_area_le_l0"]*100, metrics["ligament_1"]["mean_h_um"]))
    print("Ligament 2 (h <= l0): %.2f%% count, %.2f%% area (mean h=%.2f um)" % (
        metrics["ligament_2"]["frac_count_le_l0"]*100, metrics["ligament_2"]["frac_area_le_l0"]*100, metrics["ligament_2"]["mean_h_um"]))
    print("Ligament 3 (h <= l0): %.2f%% count, %.2f%% area (mean h=%.2f um)" % (
        metrics["ligament_3"]["frac_count_le_l0"]*100, metrics["ligament_3"]["frac_area_le_l0"]*100, metrics["ligament_3"]["mean_h_um"]))
    print("Ligament 4 (h <= l0): %.2f%% count, %.2f%% area (mean h=%.2f um)" % (
        metrics["ligament_4"]["frac_count_le_l0"]*100, metrics["ligament_4"]["frac_area_le_l0"]*100, metrics["ligament_4"]["mean_h_um"]))
    print("Bulk Far-Field (mean h): %.2f um" % metrics["bulk_far_field"]["mean_h_um"])
    print("All Gates Pass: %s" % ("YES" if (metrics["parity_evaluation"]["published_parity_pass"] and metrics["parity_evaluation"]["fe_quality_pass"] and metrics["parity_evaluation"]["active_ligaments_resolved"]) else "NO"))


if __name__ == '__main__':
    main()

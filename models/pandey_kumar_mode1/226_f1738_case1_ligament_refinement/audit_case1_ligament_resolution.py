# -*- coding: utf-8 -*-
"""
audit_case1_ligament_resolution.py
==================================
Audits Case 1 Mode-I Adapted Mesh along the 10 horizontal ligament stations.
Evaluates:
- Finite element quality (det(J) > 0, quad % >= 95%, max aspect ratio < 5.0)
- Station-by-station resolution:
    * Count-weighted compliance (h <= l0 = 7.5 um and h <= l0/2 = 3.75 um)
    * Area-weighted compliance (h <= l0 and h <= l0/2)
    * Mean h, Min h, Max h per station
- Dual-element adjacency cluster analysis for connected noncompliant elements
- Transverse coarse barrier detection (has_transverse_coarse_barrier)
- Generates JSON summary for qualification report.
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


def point_to_segment_distance(px, py, x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    L2 = dx*dx + dy*dy
    if L2 == 0:
        return math.hypot(px - x1, py - y1), 0.0
    t = max(0.0, min(1.0, ((px - x1)*dx + (py - y1)*dy) / L2))
    proj_x = x1 + t * dx
    proj_y = y1 + t * dy
    return math.hypot(px - proj_x, py - proj_y), t


def compute_mesh_quality(nodes, elements, elem_types, l0=0.0075, w_perp_factor=2.5):
    total_elems = len(elements)
    quad_count = sum(1 for e, conn in elements.items() if len(conn) == 4)
    tri_count = sum(1 for e, conn in elements.items() if len(conn) == 3)
    quad_pct = float(quad_count) / float(total_elems) * 100.0 if total_elems > 0 else 0.0

    min_det_j = 1e30
    neg_jacobian_count = 0
    aspect_ratios = []
    elem_sizes = []

    w_perp = w_perp_factor * l0
    w_perp_um = w_perp * 1000.0
    stations = [[] for _ in range(10)]

    # Adjacency tracking
    edge_to_elements = {}
    corridor_elements = {}

    for eid, conn in elements.items():
        pts = [nodes[n] for n in conn]
        cx = sum(p[0] for p in pts) / float(len(pts))
        cy = sum(p[1] for p in pts) / float(len(pts))

        if len(pts) == 4:
            # 4 Gauss points for CPE4
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
            edges = [tuple(sorted((conn[i], conn[(i+1)%4]))) for i in range(4)]

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
            edges = [tuple(sorted((conn[i], conn[(i+1)%3]))) for i in range(3)]

        h_e = math.sqrt(area) * 1000.0 # in um
        elem_sizes.append(h_e)

        dist, t = point_to_segment_distance(cx, cy, 0.5, 0.5, 1.0, 0.5)
        if dist <= w_perp and 0.5 <= cx <= 1.0:
            st_idx = min(9, int(t * 10))
            signed_perp_um = (cy - 0.5) * 1000.0
            elem_info = {
                "eid": eid,
                "cx": cx,
                "cy": cy,
                "area_mm2": area,
                "h_um": h_e,
                "proj_s": t,
                "signed_perp_um": signed_perp_um,
                "edges": edges,
                "is_noncompliant": bool(h_e > l0 * 1000.0)
            }
            stations[st_idx].append(elem_info)
            corridor_elements[eid] = elem_info
            for edge in edges:
                edge_to_elements.setdefault(edge, []).append(eid)

    # Station metrics
    station_metrics = []
    all_stations_le_l0 = True
    total_corridor_area = sum(e["area_mm2"] for e in corridor_elements.values())
    total_corridor_compliant_area_l0 = sum(e["area_mm2"] for e in corridor_elements.values() if e["h_um"] <= l0 * 1000.0)
    total_corridor_compliant_area_half = sum(e["area_mm2"] for e in corridor_elements.values() if e["h_um"] <= (l0/2.0) * 1000.0)

    for s_idx in range(10):
        x_start = 0.5 + 0.05 * s_idx
        x_end = 0.5 + 0.05 * (s_idx + 1)
        e_list = stations[s_idx]
        if e_list:
            h_vals = [e["h_um"] for e in e_list]
            areas = [e["area_mm2"] for e in e_list]
            st_total_area = sum(areas)
            mean_h = sum(h_vals) / len(h_vals)
            min_h = min(h_vals)
            max_h = max(h_vals)
            count_pct_le_l0 = sum(1 for h in h_vals if h <= l0 * 1000.0) / float(len(h_vals)) * 100.0
            count_pct_le_half = sum(1 for h in h_vals if h <= (l0/2.0) * 1000.0) / float(len(h_vals)) * 100.0
            area_pct_le_l0 = sum(e["area_mm2"] for e in e_list if e["h_um"] <= l0 * 1000.0) / st_total_area * 100.0
            area_pct_le_half = sum(e["area_mm2"] for e in e_list if e["h_um"] <= (l0/2.0) * 1000.0) / st_total_area * 100.0
            if mean_h > l0 * 1000.0:
                all_stations_le_l0 = False
        else:
            mean_h = min_h = max_h = 0.0
            count_pct_le_l0 = count_pct_le_half = 0.0
            area_pct_le_l0 = area_pct_le_half = 0.0
            all_stations_le_l0 = False

        station_metrics.append({
            "station": s_idx + 1,
            "x_interval": [round(x_start, 3), round(x_end, 3)],
            "count": len(e_list),
            "mean_h_um": round(mean_h, 3),
            "min_h_um": round(min_h, 3),
            "max_h_um": round(max_h, 3),
            "count_pct_le_l0": round(count_pct_le_l0, 2),
            "count_pct_le_half": round(count_pct_le_half, 2),
            "area_pct_le_l0": round(area_pct_le_l0, 2),
            "area_pct_le_half": round(area_pct_le_half, 2)
        })

    # Connected Coarse Cluster & Transverse Barrier Analysis (h > l0 = 7.5 um)
    coarse_elements = {eid: e for eid, e in corridor_elements.items() if e["is_noncompliant"]}
    visited = set()
    clusters = []

    for eid in coarse_elements:
        if eid in visited:
            continue
        cluster = []
        queue = [eid]
        visited.add(eid)
        while queue:
            curr = queue.pop(0)
            cluster.append(curr)
            for edge in coarse_elements[curr]["edges"]:
                for nbr in edge_to_elements.get(edge, []):
                    if nbr in coarse_elements and nbr not in visited:
                        visited.add(nbr)
                        queue.append(nbr)

        c_elems = [coarse_elements[e] for e in cluster]
        projs = [e["proj_s"] for e in c_elems]
        signed_perps = [e["signed_perp_um"] for e in c_elems]
        s_min_c = min(projs)
        s_max_c = max(projs)
        long_span_um = (s_max_c - s_min_c) * 500.0
        long_span_l0 = long_span_um / (l0 * 1000.0)
        min_signed_perp = min(signed_perps)
        max_signed_perp = max(signed_perps)
        trans_span_um = max_signed_perp - min_signed_perp
        is_transverse_barrier = bool(min_signed_perp < -0.5 * w_perp_um and max_signed_perp > 0.5 * w_perp_um)

        clusters.append({
            "element_count": len(cluster),
            "longitudinal_span_um": round(long_span_um, 2),
            "longitudinal_span_l0": round(long_span_l0, 2),
            "transverse_span_um": round(trans_span_um, 2),
            "is_transverse_barrier": is_transverse_barrier
        })

    has_transverse_coarse_barrier = any(c["is_transverse_barrier"] for c in clusters)
    max_contiguous_coarse_span_um = max([c["longitudinal_span_um"] for c in clusters]) if clusters else 0.0

    overall_area_compliance_l0 = (total_corridor_compliant_area_l0 / total_corridor_area * 100.0) if total_corridor_area > 0 else 0.0
    overall_area_compliance_half = (total_corridor_compliant_area_half / total_corridor_area * 100.0) if total_corridor_area > 0 else 0.0

    audit_summary = {
        "benchmark": "Pandey & Kumar (2025) Section 4.1 Mode-I Edge-Cracked Plate",
        "methodology": "METHOD_A_NATIVE_REMESHING_WITH_DESIGNATED_ADAPTIVE_DOMAIN",
        "adaptation_domain": "Designated prospective fracture corridor x in [0.5, 1.0], y in [0.48, 0.52] mm",
        "total_elements": total_elems,
        "quad_count": quad_count,
        "tri_count": tri_count,
        "quad_percentage": round(quad_pct, 2),
        "min_det_j": float(min_det_j),
        "negative_jacobian_count": neg_jacobian_count,
        "max_aspect_ratio": round(max(aspect_ratios), 3) if aspect_ratios else 0.0,
        "h_min_um": round(min(elem_sizes), 3) if elem_sizes else 0.0,
        "h_max_um": round(max(elem_sizes), 3) if elem_sizes else 0.0,
        "all_stations_mean_le_l0": all_stations_le_l0,
        "overall_area_compliance_pct_l0": round(overall_area_compliance_l0, 2),
        "overall_area_compliance_pct_half_l0": round(overall_area_compliance_half, 2),
        "has_transverse_coarse_barrier": has_transverse_coarse_barrier,
        "max_contiguous_coarse_span_um": round(max_contiguous_coarse_span_um, 2),
        "coarse_clusters_count": len(clusters),
        "station_metrics": station_metrics
    }
    return audit_summary


if __name__ == "__main__":
    inp_path = sys.argv[1] if len(sys.argv) > 1 else "PK_F1738_CASE_1_ADAPT_PHYS.inp"
    out_json = sys.argv[2] if len(sys.argv) > 2 else "f1738_case1_ligament_spatial_audit.json"

    print("Auditing physical mesh: %s" % inp_path)
    nodes, elements, elem_types = parse_inp_mesh(inp_path)
    summary = compute_mesh_quality(nodes, elements, elem_types)

    print("\n=== SPATIAL RESOLUTION AUDIT SUMMARY ===")
    print("Methodology:       %s" % summary["methodology"])
    print("Total Elements:    %d (Quads: %d / %.2f%%, Tris: %d)" % (
        summary["total_elements"], summary["quad_count"], summary["quad_percentage"], summary["tri_count"]
    ))
    print("Min det(J):        %.3e (Negative: %d)" % (summary["min_det_j"], summary["negative_jacobian_count"]))
    print("Max Aspect Ratio:  %.3f" % summary["max_aspect_ratio"])
    print("Min h:             %.3f um" % summary["h_min_um"])
    print("Max h:             %.3f um" % summary["h_max_um"])
    print("All Stations Mean <= l0:   %s" % summary["all_stations_mean_le_l0"])
    print("Overall Area Compliance <= l0:    %.2f%%" % summary["overall_area_compliance_pct_l0"])
    print("Overall Area Compliance <= l0/2:  %.2f%%" % summary["overall_area_compliance_pct_half_l0"])
    print("Has Transverse Coarse Barrier:   %s" % summary["has_transverse_coarse_barrier"])
    print("Max Coarse Span:                 %.2f um" % summary["max_contiguous_coarse_span_um"])

    print("\n--- 10 Horizontal Ligament Stations ---")
    for st in summary["station_metrics"]:
        print("  Station %2d (x in [%.2f, %.2f]): %4d elems | mean h = %5.2f um | max h = %5.2f um | count <= l0: %5.1f%% | area <= l0: %5.1f%% | area <= l0/2: %5.1f%%" % (
            st["station"], st["x_interval"][0], st["x_interval"][1],
            st["count"], st["mean_h_um"], st["max_h_um"],
            st["count_pct_le_l0"], st["area_pct_le_l0"], st["area_pct_le_half"]
        ))

    with open(out_json, "w") as f:
        json.dump(summary, f, indent=2)
    print("\nSaved spatial audit JSON: %s" % out_json)

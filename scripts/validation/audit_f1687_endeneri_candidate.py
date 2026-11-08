"""
scripts/validation/audit_f1687_endeneri_candidate.py
===================================================
Task F1687 Stage B: Audits PK_HOLE_ENDENERI_TERM_PHYS.inp under exact canonical
h_equiv = sqrt(Area) metric pipeline against authentic crack centerlines.
"""

import os
import sys
import json
import math
import numpy as np

def parse_inp_mesh(inp_path):
    nodes = {}
    elements = {}
    elem_types = {}

    in_nodes = False
    in_elements = False
    current_type = None

    with open(inp_path, "r") as fp:
        for line in fp:
            line = line.strip()
            if not line or line.startswith("**"):
                continue

            if line.startswith("*"):
                in_nodes = False
                in_elements = False
                upline = line.upper()
                if upline.startswith("*NODE"):
                    in_nodes = True
                elif upline.startswith("*ELEMENT"):
                    if "CPE4" in upline or "CPS4" in upline:
                        in_elements = True
                        current_type = "QUAD"
                    elif "CPE3" in upline or "CPS3" in upline:
                        in_elements = True
                        current_type = "TRI"
                    else:
                        current_type = None
                continue

            parts = [p.strip() for p in line.split(",") if p.strip()]
            if in_nodes:
                if len(parts) >= 3:
                    try:
                        nid = int(parts[0])
                        x = float(parts[1])
                        y = float(parts[2])
                        nodes[nid] = (x, y)
                    except ValueError:
                        pass
            elif in_elements and current_type:
                try:
                    eid = int(parts[0])
                    conn = [int(p) for p in parts[1:]]
                    elements[eid] = conn
                    elem_types[eid] = current_type
                except ValueError:
                    pass

    return nodes, elements, elem_types

def compute_jacobian_and_aspect(pts):
    n = len(pts)
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += pts[i][0] * pts[j][1] - pts[j][0] * pts[i][1]
    area = 0.5 * abs(area)

    edges = []
    for i in range(n):
        j = (i + 1) % n
        edges.append(math.hypot(pts[j][0] - pts[i][0], pts[j][1] - pts[i][1]))
    max_edge = max(edges)
    min_edge = min(edges)
    aspect_ratio = (max_edge / min_edge) if min_edge > 0 else 100.0

    if n == 4:
        corner_jacs = []
        for i in range(4):
            p_prev = pts[(i - 1) % 4]
            p_curr = pts[i]
            p_next = pts[(i + 1) % 4]
            v1 = (p_next[0] - p_curr[0], p_next[1] - p_curr[1])
            v2 = (p_prev[0] - p_curr[0], p_prev[1] - p_curr[1])
            cross = v1[0] * v2[1] - v1[1] * v2[0]
            l1 = math.hypot(v1[0], v1[1])
            l2 = math.hypot(v2[0], v2[1])
            if l1 * l2 > 0:
                corner_jacs.append(abs(cross) / (l1 * l2))
            else:
                corner_jacs.append(0.0)
        scaled_jac = min(corner_jacs)
    elif n == 3:
        p0, p1, p2 = pts
        v1 = (p1[0] - p0[0], p1[1] - p0[1])
        v2 = (p2[0] - p0[0], p2[1] - p0[1])
        cross = abs(v1[0] * v2[1] - v1[1] * v2[0])
        l1 = math.hypot(v1[0], v1[1])
        l2 = math.hypot(v2[0], v2[1])
        scaled_jac = (cross / (l1 * l2)) if (l1 * l2 > 0) else 0.0
    else:
        scaled_jac = 1.0

    return area, max_edge, scaled_jac, aspect_ratio

def compute_point_to_polyline_dist(px, py, polyline):
    min_dist = float("inf")
    for i in range(len(polyline) - 1):
        x1, y1 = polyline[i]
        x2, y2 = polyline[i+1]
        dx = x2 - x1
        dy = y2 - y1
        l2 = dx*dx + dy*dy
        if l2 == 0.0:
            d = math.hypot(px - x1, py - y1)
        else:
            t = max(0.0, min(1.0, ((px - x1)*dx + (py - y1)*dy) / l2))
            proj_x = x1 + t * dx
            proj_y = y1 + t * dy
            d = math.hypot(px - proj_x, py - proj_y)
        if d < min_dist:
            min_dist = d
    return min_dist

def main():
    inp_path = "models/pandey_kumar_mode1/176_method_a_plate_with_hole/candidates/PK_HOLE_ENDENERI_TERM_PHYS.inp"
    centerline_path = "results/validation/f1684_crack_path_centerlines.json"
    with open(centerline_path, "r") as fp:
        cl_data = json.load(fp)
    primary_cl = cl_data["primary"]["points"]
    secondary_cl = cl_data["secondary"]["points"]

    print("=" * 90)
    print("TASK F1687 STAGE B: ENDENERI TERMINAL-FRAME CONTROL MESH AUDIT")
    print("Mesh Deck:", inp_path)
    print("=" * 90)

    nodes, elements, elem_types = parse_inp_mesh(inp_path)
    n_elems = len(elements)
    n_nodes = len(nodes)
    n_quads = sum(1 for t in elem_types.values() if t == "QUAD")
    n_tris = sum(1 for t in elem_types.values() if t == "TRI")

    centroids = []
    areas = []
    h_equivs = []
    h_edges = []
    scaled_jacs = []
    aspect_ratios = []

    for eid, conn in sorted(elements.items()):
        pts = [nodes[nid] for nid in conn]
        cx = sum(p[0] for p in pts) / float(len(pts))
        cy = sum(p[1] for p in pts) / float(len(pts))
        centroids.append((cx, cy))

        area, max_edge, s_jac, asp = compute_jacobian_and_aspect(pts)
        areas.append(area)
        h_equivs.append(math.sqrt(area) * 1000.0) # um
        h_edges.append(max_edge * 1000.0) # um
        scaled_jacs.append(s_jac)
        aspect_ratios.append(asp)

    cents = np.array(centroids)
    h_equivs = np.array(h_equivs)
    h_edges = np.array(h_edges)
    areas = np.array(areas)
    scaled_jacs = np.array(scaled_jacs)
    aspect_ratios = np.array(aspect_ratios)

    total_area_mm2 = float(np.sum(areas))

    # Crack path distances (um)
    d_prim_um = np.array([compute_point_to_polyline_dist(c[0], c[1], primary_cl) * 1000.0 for c in cents])
    d_sec_um = np.array([compute_point_to_polyline_dist(c[0], c[1], secondary_cl) * 1000.0 for c in cents])
    d_min_um = np.minimum(d_prim_um, d_sec_um)

    l0_um = 7.50
    h_half_l0_um = 3.75
    h_third_l0_um = 2.50

    is_fine = h_equivs <= h_half_l0_um
    n_fine = int(np.sum(is_fine))

    in_prim_15 = d_prim_um <= 15.0
    in_sec_15 = d_sec_um <= 15.0
    in_any_15 = d_min_um <= 15.0

    fine_out_corridor = is_fine & (~in_any_15)
    waste_area_mm2 = float(np.sum(areas[fine_out_corridor]))
    total_fine_area_mm2 = float(np.sum(areas[is_fine]))
    waste_pct_rel = (waste_area_mm2 / total_fine_area_mm2 * 100.0) if total_fine_area_mm2 > 0 else 0.0
    waste_pct_domain = (waste_area_mm2 / total_area_mm2 * 100.0)

    # Transverse widths
    if n_fine > 0:
        fine_dists = d_min_um[is_fine]
        w50 = float(np.percentile(fine_dists, 50.0))
        w90 = float(np.percentile(fine_dists, 90.0))
    else:
        w50, w90 = 0.0, 0.0

    # Primary corridor (dist <= 15 um)
    h_prim_eq = h_equivs[in_prim_15]
    prim_n = len(h_prim_eq)
    prim_med_eq = float(np.median(h_prim_eq)) if prim_n > 0 else 0.0
    prim_pct_half_eq = float(np.sum(h_prim_eq <= h_half_l0_um) / float(prim_n) * 100.0) if prim_n > 0 else 0.0
    prim_pct_third_eq = float(np.sum(h_prim_eq <= h_third_l0_um) / float(prim_n) * 100.0) if prim_n > 0 else 0.0
    prim_pct_l0_eq = float(np.sum(h_prim_eq <= l0_um) / float(prim_n) * 100.0) if prim_n > 0 else 0.0
    prim_max_eq = float(np.max(h_prim_eq)) if prim_n > 0 else 0.0
    prim_min_eq = float(np.min(h_prim_eq)) if prim_n > 0 else 0.0

    # Secondary corridor (dist <= 15 um)
    h_sec_eq = h_equivs[in_sec_15]
    sec_n = len(h_sec_eq)
    sec_med_eq = float(np.median(h_sec_eq)) if sec_n > 0 else 0.0
    sec_pct_half_eq = float(np.sum(h_sec_eq <= h_half_l0_um) / float(sec_n) * 100.0) if sec_n > 0 else 0.0
    sec_pct_third_eq = float(np.sum(h_sec_eq <= h_third_l0_um) / float(sec_n) * 100.0) if sec_n > 0 else 0.0
    sec_pct_l0_eq = float(np.sum(h_sec_eq <= l0_um) / float(sec_n) * 100.0) if sec_n > 0 else 0.0
    sec_max_eq = float(np.max(h_sec_eq)) if sec_n > 0 else 0.0
    sec_min_eq = float(np.min(h_sec_eq)) if sec_n > 0 else 0.0

    # Criteria evaluation
    crit1_prim = (prim_med_eq <= h_third_l0_um) and (prim_pct_half_eq >= 75.0)
    crit2_sec = (sec_med_eq <= h_third_l0_um) and (sec_pct_half_eq >= 80.0)
    crit3_scale = (prim_max_eq <= l0_um) and (sec_max_eq <= l0_um)
    crit4_selectivity = (w90 <= 50.0) and (waste_pct_rel <= 70.0)
    overall_pass = crit1_prim and crit2_sec and crit3_scale and crit4_selectivity

    min_jac = float(np.min(scaled_jacs))
    max_asp = float(np.max(aspect_ratios))

    summary = {
        "candidate_name": "PK_HOLE_ENDENERI_TERM_PHYS",
        "description": "Terminal Frame ENDENERI Control (Frame 337, errorTarget=5.0%)",
        "total_elements": n_elems,
        "n_quads": n_quads,
        "n_tris": n_tris,
        "total_nodes": n_nodes,
        "total_dofs": 3 * n_nodes,
        "total_area_mm2": total_area_mm2,
        "min_scaled_jacobian": min_jac,
        "max_aspect_ratio": max_asp,
        "n_fine_elements": n_fine,
        "fine_area_mm2": total_fine_area_mm2,
        "waste_area_mm2": waste_area_mm2,
        "waste_pct_rel": waste_pct_rel,
        "waste_pct_domain": waste_pct_domain,
        "w50_um": w50,
        "w90_um": w90,
        "primary_corridor": {
            "n_elements": prim_n,
            "min_h_equiv_um": prim_min_eq,
            "med_h_equiv_um": prim_med_eq,
            "max_h_equiv_um": prim_max_eq,
            "pct_le_half_l0": prim_pct_half_eq,
            "pct_le_third_l0": prim_pct_third_eq,
            "pct_le_l0": prim_pct_l0_eq,
            "criterion_pass": crit1_prim
        },
        "secondary_corridor": {
            "n_elements": sec_n,
            "min_h_equiv_um": sec_min_eq,
            "med_h_equiv_um": sec_med_eq,
            "max_h_equiv_um": sec_max_eq,
            "pct_le_half_l0": sec_pct_half_eq,
            "pct_le_third_l0": sec_pct_third_eq,
            "pct_le_l0": sec_pct_l0_eq,
            "criterion_pass": crit2_sec
        },
        "criterion_3_scale_enclosure": crit3_scale,
        "criterion_4_selectivity": crit4_selectivity,
        "overall_pass": overall_pass,
        "h1_hypothesis_verdict": "PASS" if overall_pass else "FALSIFIED"
    }

    out_json = "results/validation/f1687_endeneri_candidate_audit.json"
    with open(out_json, "w") as fp:
        json.dump(summary, fp, indent=2)
    print(f"Audit saved to {out_json}")

    csv_path = "results/validation/f1687_endeneri_candidate_summary.csv"
    with open(csv_path, "w") as fp:
        fp.write("candidate,n_elems,dofs,waste_mm2,waste_rel_pct,w50_um,w90_um,prim_h_med_um,prim_pct_half,sec_h_med_um,sec_pct_half,min_jac,max_asp,crit1,crit2,crit3,crit4,overall_pass,h1_verdict\n")
        fp.write(f"PK_HOLE_ENDENERI_TERM_PHYS,{n_elems},{3*n_nodes},{waste_area_mm2:.6f},{waste_pct_rel:.2f},{w50:.2f},{w90:.2f},{prim_med_eq:.3f},{prim_pct_half_eq:.1f},{sec_med_eq:.3f},{sec_pct_half_eq:.1f},{min_jac:.4f},{max_asp:.2f},{crit1_prim},{crit2_sec},{crit3_scale},{crit4_selectivity},{overall_pass},{summary['h1_hypothesis_verdict']}\n")
    print(f"Summary CSV saved to {csv_path}")

    print("\n" + "=" * 90)
    print("STAGE B: ENDENERI TERMINAL-FRAME CONTROL RESULTS")
    print("=" * 90)
    print(f"Total Physical Elements: {n_elems} ({n_quads} quads, {n_tris} tris)")
    print(f"Total DOFs:              {3 * n_nodes}")
    print(f"Refinement Widths:       W50 = {w50:.2f} um, W90 = {w90:.2f} um")
    print(f"Fine-Element Waste:      Area = {waste_area_mm2:.6f} mm2, Relative Waste = {waste_pct_rel:.2f}%")
    print(f"Primary Corridor:        n = {prim_n}, median = {prim_med_eq:.3f} um, % <= l0/2 = {prim_pct_half_eq:.1f}%, max = {prim_max_eq:.3f} um (Crit 1: {crit1_prim})")
    print(f"Secondary Corridor:      n = {sec_n}, median = {sec_med_eq:.3f} um, % <= l0/2 = {sec_pct_half_eq:.1f}%, max = {sec_max_eq:.3f} um (Crit 2: {crit2_sec})")
    print(f"Scale Enclosure (Crit 3): {crit3_scale}")
    print(f"Selectivity Gate (Crit 4): {crit4_selectivity}")
    print(f"OVERALL PASS:            {overall_pass}")
    print(f"H1 HYPOTHESIS VERDICT:   {summary['h1_hypothesis_verdict']}")
    print("=" * 90)

if __name__ == "__main__":
    main()

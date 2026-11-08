"""
scripts/validation/audit_f1687_stage_a_criterion3.py
==================================================
Audits Criterion 3 (Scale Enclosure: h_equiv <= l0 = 7.50 um) along both
primary and secondary crack corridors (dist <= 15.0 um) for Candidates
E05 (baseline), E10 (primary recommended), and E12 (aggressive alternative).
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

    return nodes, elements

def compute_element_metrics(nodes, elements):
    centroids = []
    h_equivs = []
    h_edges = []
    areas = []
    for eid, conn in sorted(elements.items()):
        pts = [nodes[nid] for nid in conn]
        n_pts = len(pts)
        cx = sum(p[0] for p in pts) / float(n_pts)
        cy = sum(p[1] for p in pts) / float(n_pts)
        centroids.append((cx, cy))

        # Polygon area (Shoelace)
        area = 0.0
        for i in range(n_pts):
            j = (i + 1) % n_pts
            area += pts[i][0] * pts[j][1] - pts[j][0] * pts[i][1]
        area = 0.5 * abs(area)
        areas.append(area)
        h_eq = math.sqrt(area) * 1000.0 # um
        h_equivs.append(h_eq)

        # Edges
        max_edge = 0.0
        for i in range(n_pts):
            j = (i + 1) % n_pts
            edge_len = math.hypot(pts[j][0] - pts[i][0], pts[j][1] - pts[i][1])
            if edge_len > max_edge:
                max_edge = edge_len
        h_edges.append(max_edge * 1000.0) # um

    return np.array(centroids), np.array(h_equivs), np.array(h_edges), np.array(areas)

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
    centerline_path = "results/validation/f1684_crack_path_centerlines.json"
    with open(centerline_path, "r") as fp:
        cl_data = json.load(fp)
    primary_cl = cl_data["primary"]["points"]
    secondary_cl = cl_data["secondary"]["points"]

    decks = [
        ("PK_HOLE_SEL_E05_PHYS", "models/pandey_kumar_mode1/176_method_a_plate_with_hole/candidates/PK_HOLE_SEL_E05_PHYS.inp"),
        ("PK_HOLE_SEL_E08_PHYS", "models/pandey_kumar_mode1/176_method_a_plate_with_hole/candidates/PK_HOLE_SEL_E08_PHYS.inp"),
        ("PK_HOLE_SEL_E10_PHYS", "models/pandey_kumar_mode1/176_method_a_plate_with_hole/candidates/PK_HOLE_SEL_E10_PHYS.inp"),
        ("PK_HOLE_SEL_E12_PHYS", "models/pandey_kumar_mode1/176_method_a_plate_with_hole/candidates/PK_HOLE_SEL_E12_PHYS.inp"),
        ("PK_HOLE_SEL_E15_PHYS", "models/pandey_kumar_mode1/176_method_a_plate_with_hole/candidates/PK_HOLE_SEL_E15_PHYS.inp"),
    ]

    results = {}
    l0_um = 7.50
    half_l0_um = 3.75
    third_l0_um = 2.50

    print("=" * 100)
    print("STAGE A: VERIFICATION OF CRITERION 3 (SCALE ENCLOSURE h <= l0 = 7.50 um) ALONG CORRIDORS (dist <= 15 um)")
    print("=" * 100)

    for name, path in decks:
        nodes, elements = parse_inp_mesh(path)
        cents, h_equivs, h_edges, areas = compute_element_metrics(nodes, elements)

        d_prim_um = np.array([compute_point_to_polyline_dist(c[0], c[1], primary_cl) * 1000.0 for c in cents])
        d_sec_um = np.array([compute_point_to_polyline_dist(c[0], c[1], secondary_cl) * 1000.0 for c in cents])

        in_prim = d_prim_um <= 15.0
        in_sec = d_sec_um <= 15.0
        in_either = in_prim | in_sec

        h_prim_eq = h_equivs[in_prim]
        h_sec_eq = h_equivs[in_sec]
        h_either_eq = h_equivs[in_either]

        # Primary statistics
        prim_n = len(h_prim_eq)
        prim_max_eq = float(np.max(h_prim_eq)) if prim_n > 0 else 0.0
        prim_min_eq = float(np.min(h_prim_eq)) if prim_n > 0 else 0.0
        prim_med_eq = float(np.median(h_prim_eq)) if prim_n > 0 else 0.0
        prim_n_le_l0 = int(np.sum(h_prim_eq <= l0_um))
        prim_pct_le_l0 = (prim_n_le_l0 / prim_n * 100.0) if prim_n > 0 else 0.0
        prim_n_gt_l0 = prim_n - prim_n_le_l0

        # Secondary statistics
        sec_n = len(h_sec_eq)
        sec_max_eq = float(np.max(h_sec_eq)) if sec_n > 0 else 0.0
        sec_min_eq = float(np.min(h_sec_eq)) if sec_n > 0 else 0.0
        sec_med_eq = float(np.median(h_sec_eq)) if sec_n > 0 else 0.0
        sec_n_le_l0 = int(np.sum(h_sec_eq <= l0_um))
        sec_pct_le_l0 = (sec_n_le_l0 / sec_n * 100.0) if sec_n > 0 else 0.0
        sec_n_gt_l0 = sec_n - sec_n_le_l0

        # Either corridor
        either_n = len(h_either_eq)
        either_max_eq = float(np.max(h_either_eq)) if either_n > 0 else 0.0
        either_pct_le_l0 = (float(np.sum(h_either_eq <= l0_um)) / either_n * 100.0) if either_n > 0 else 0.0

        results[name] = {
            "total_elements": len(elements),
            "primary_corridor": {
                "n_elements": prim_n,
                "min_h_equiv_um": prim_min_eq,
                "med_h_equiv_um": prim_med_eq,
                "max_h_equiv_um": prim_max_eq,
                "pct_le_l0": prim_pct_le_l0,
                "n_gt_l0": prim_n_gt_l0,
                "criterion_3_pass": (prim_n_gt_l0 == 0)
            },
            "secondary_corridor": {
                "n_elements": sec_n,
                "min_h_equiv_um": sec_min_eq,
                "med_h_equiv_um": sec_med_eq,
                "max_h_equiv_um": sec_max_eq,
                "pct_le_l0": sec_pct_le_l0,
                "n_gt_l0": sec_n_gt_l0,
                "criterion_3_pass": (sec_n_gt_l0 == 0)
            },
            "either_corridor": {
                "n_elements": either_n,
                "max_h_equiv_um": either_max_eq,
                "pct_le_l0": either_pct_le_l0,
                "criterion_3_pass": (either_max_eq <= l0_um)
            }
        }

        print(f"\nCandidate: {name} ({len(elements)} total physical elements)")
        print(f"  Primary Corridor (dist <= 15 um, {prim_n} elements):")
        print(f"    min(h_equiv) = {prim_min_eq:.3f} um, median = {prim_med_eq:.3f} um, max = {prim_max_eq:.3f} um")
        print(f"    elements <= l0 (7.50 um): {prim_n_le_l0}/{prim_n} ({prim_pct_le_l0:.2f}%), elements > 7.50 um: {prim_n_gt_l0}")
        print(f"    Criterion 3 Primary Pass: {prim_n_gt_l0 == 0}")
        print(f"  Secondary Corridor (dist <= 15 um, {sec_n} elements):")
        print(f"    min(h_equiv) = {sec_min_eq:.3f} um, median = {sec_med_eq:.3f} um, max = {sec_max_eq:.3f} um")
        print(f"    elements <= l0 (7.50 um): {sec_n_le_l0}/{sec_n} ({sec_pct_le_l0:.2f}%), elements > 7.50 um: {sec_n_gt_l0}")
        print(f"    Criterion 3 Secondary Pass: {sec_n_gt_l0 == 0}")
        print(f"  Global Corridor Enclosure: max(h_equiv) = {either_max_eq:.3f} um <= 7.50 um -> {either_max_eq <= l0_um}")

    out_json = "results/validation/f1687_stage_a_criterion3_audit.json"
    with open(out_json, "w") as fp:
        json.dump(results, fp, indent=2)
    print(f"\nAudit saved to {out_json}")

if __name__ == "__main__":
    main()

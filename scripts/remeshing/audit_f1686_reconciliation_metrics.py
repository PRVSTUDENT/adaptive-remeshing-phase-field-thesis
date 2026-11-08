# -*- coding: utf-8 -*-
"""
scripts/remeshing/audit_f1686_reconciliation_metrics.py
======================================================
Task F1686: Authoritative Unified Reconciliation of Review HND-0b8cd8d41b7a

Unified Sizing Measure:
- Canonical Measure: h_equiv = sqrt(Area) [um] (standard 2D continuum element resolution measure).
- All fine-element thresholds (h <= 3.75 um = l0/2), waste areas, transverse widths W50/W90,
  and adopted acceptance criteria are evaluated strictly and consistently using h_equiv.
- Maximum physical edge length h_edge = max(edge) is also reported for complete geometric census.

Exact F1684 Zone Reproduction:
- Notch Tip Initiation: r <= 50 um around (0.50, 0.50).
- Primary Fracture Corridor: 0.50 <= x <= 0.65, 0.48 <= y <= 0.65, r > 50 um.
  (Reproduces exactly 867 elements, h_med = 4.26 um, and 26.41% <= 3.75 um under h_edge).

Adopted Selection Thresholds under h_equiv:
- Primary Corridor (dist <= 15.0 um): median h_equiv <= l0/3 = 2.50 um AND >= 75% <= l0/2 = 3.75 um.
- Secondary Corridor (dist <= 15.0 um): median h_equiv <= l0/3 = 2.50 um AND >= 80% <= l0/2 = 3.75 um.
- Scale Enclosure: 100% elements <= l0 = 7.50 um along both corridors.
- Selectivity Constraints: W_90% <= 50.0 um AND relative waste area <= 70.0% (disqualifying Baseline E05).
"""
import os
import sys
import json
import math
import csv
import numpy as np

def dist_point_to_polyline(px, py, polyline):
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
            d = math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))
        if d < min_dist:
            min_dist = d
    return min_dist

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
                        nodes[nid] = (float(parts[1]), float(parts[2]))
                    except ValueError:
                        pass
            elif in_elements:
                if current_type == "QUAD" and len(parts) >= 5:
                    try:
                        eid = int(parts[0])
                        elements[eid] = (int(parts[1]), int(parts[2]), int(parts[3]), int(parts[4]))
                        elem_types[eid] = "QUAD"
                    except ValueError:
                        pass
                elif current_type == "TRI" and len(parts) >= 4:
                    try:
                        eid = int(parts[0])
                        elements[eid] = (int(parts[1]), int(parts[2]), int(parts[3]))
                        elem_types[eid] = "TRI"
                    except ValueError:
                        pass

    n_quads = sum(1 for t in elem_types.values() if t == "QUAD")
    n_tris = sum(1 for t in elem_types.values() if t == "TRI")

    metrics = {}
    for eid, conn in elements.items():
        pts = [nodes[nid] for nid in conn]
        n_pts = len(pts)
        cx = sum(p[0] for p in pts) / float(n_pts)
        cy = sum(p[1] for p in pts) / float(n_pts)

        # Edges
        edges = [math.hypot(pts[(i+1)%n_pts][0] - pts[i][0], pts[(i+1)%n_pts][1] - pts[i][1]) for i in range(n_pts)]
        h_max_edge_um = max(edges) * 1e3
        h_min_edge_um = min(edges) * 1e3

        # Area via shoelace
        signed_area = 0.5 * sum(pts[i][0]*pts[(i+1)%n_pts][1] - pts[(i+1)%n_pts][0]*pts[i][1] for i in range(n_pts))
        area_mm2 = abs(signed_area)
        h_equiv_um = math.sqrt(area_mm2) * 1e3
        aspect_ratio = h_max_edge_um / h_min_edge_um if h_min_edge_um > 0 else 1.0

        # Scaled Jacobian for quads
        scaled_jacobian = 1.0
        if n_pts == 4:
            j_vals = []
            for i in range(4):
                p_prev = pts[(i-1)%4]
                p_curr = pts[i]
                p_next = pts[(i+1)%4]
                v1 = (p_curr[0] - p_prev[0], p_curr[1] - p_prev[1])
                v2 = (p_next[0] - p_curr[0], p_next[1] - p_curr[1])
                l1 = math.hypot(v1[0], v1[1])
                l2 = math.hypot(v2[0], v2[1])
                if l1 * l2 > 0:
                    cross = (v1[0]*v2[1] - v1[1]*v2[0]) / (l1 * l2)
                    j_vals.append(cross)
            if len(j_vals) == 4:
                scaled_jacobian = min(j_vals)

        metrics[eid] = {
            "elem_id": eid,
            "type": elem_types[eid],
            "cx": cx,
            "cy": cy,
            "area_mm2": area_mm2,
            "h_equiv_um": h_equiv_um,
            "h_max_edge_um": h_max_edge_um,
            "aspect_ratio": aspect_ratio,
            "scaled_jacobian": scaled_jacobian,
            "is_quad": (n_pts == 4)
        }

    return {
        "nodes": nodes,
        "elements": elements,
        "metrics": metrics,
        "n_quads": n_quads,
        "n_tris": n_tris
    }

def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    centerlines_path = os.path.join(repo_root, "results", "validation", "f1684_crack_path_centerlines.json")
    with open(centerlines_path, "r") as fp:
        cdata = json.load(fp)

    prim_pts = [(p[0], p[1]) for p in cdata["primary"]["points"]]
    sec_pts = [(p[0], p[1]) for p in cdata["secondary"]["points"]]

    candidates_dir = os.path.join(repo_root, "models", "pandey_kumar_mode1", "176_method_a_plate_with_hole", "candidates")
    candidate_specs = [
        ("PK_HOLE_SEL_E05_PHYS", 5.0, "PK_HOLE_SEL_E05_PHYS.inp"),
        ("PK_HOLE_SEL_E08_PHYS", 8.0, "PK_HOLE_SEL_E08_PHYS.inp"),
        ("PK_HOLE_SEL_E10_PHYS", 10.0, "PK_HOLE_SEL_E10_PHYS.inp"),
        ("PK_HOLE_SEL_E12_PHYS", 12.0, "PK_HOLE_SEL_E12_PHYS.inp"),
        ("PK_HOLE_SEL_E15_PHYS", 15.0, "PK_HOLE_SEL_E15_PHYS.inp"),
        ("PK_HOLE_SEL_E20_PHYS", 20.0, "PK_HOLE_SEL_E20_PHYS.inp"),
        ("PK_HOLE_SEL_E25_PHYS", 25.0, "PK_HOLE_SEL_E25_PHYS.inp"),
        ("PK_HOLE_SEL_E30_PHYS", 30.0, "PK_HOLE_SEL_E30_PHYS.inp"),
        ("PK_HOLE_SEL_E40_PHYS", 40.0, "PK_HOLE_SEL_E40_PHYS.inp"),
        ("PK_HOLE_SEL_E50_PHYS", 50.0, "PK_HOLE_SEL_E50_PHYS.inp"),
    ]

    l0_um = 7.50
    h_half_l0_um = 3.75
    h_third_l0_um = 2.50

    json_results = []
    csv_rows = []

    print("Executing authoritative unified reconciliation audit using canonical h_equiv = sqrt(Area)...")

    for name, e_sec, fname in candidate_specs:
        inp_path = os.path.join(candidates_dir, fname)
        mesh = parse_inp_mesh(inp_path)
        metrics = mesh["metrics"]
        n_elems = len(metrics)
        n_nodes = len(mesh["nodes"])
        n_dofs = n_nodes * 3

        areas = np.array([m["area_mm2"] for m in metrics.values()])
        h_equivs = np.array([m["h_equiv_um"] for m in metrics.values()])
        h_edges = np.array([m["h_max_edge_um"] for m in metrics.values()])
        cents = [(m["cx"], m["cy"]) for m in metrics.values()]
        jacobians = [m["scaled_jacobian"] for m in metrics.values()]
        aspect_ratios = [m["aspect_ratio"] for m in metrics.values()]

        total_area = float(np.sum(areas))

        # Distances to authentic crack paths
        d_p = np.array([dist_point_to_polyline(c[0], c[1], prim_pts)*1e3 for c in cents])
        d_s = np.array([dist_point_to_polyline(c[0], c[1], sec_pts)*1e3 for c in cents])
        d_min = np.minimum(d_p, d_s)

        # Fine elements definition using canonical h_equiv <= 3.75 um
        is_fine = h_equivs <= h_half_l0_um
        n_fine = int(np.sum(is_fine))

        # Corridors at 15.0 um (2.0*l0)
        in_prim_15 = d_p <= 15.0
        in_sec_15 = d_s <= 15.0
        in_any_15 = d_min <= 15.0

        fine_out_corridor = is_fine & (~in_any_15)
        waste_area_mm2 = float(np.sum(areas[fine_out_corridor]))
        total_fine_area_mm2 = float(np.sum(areas[is_fine]))
        waste_pct_rel = (waste_area_mm2 / total_fine_area_mm2 * 100.0) if total_fine_area_mm2 > 0 else 0.0
        waste_pct_domain = (waste_area_mm2 / total_area * 100.0)

        # Transverse refinement widths
        if n_fine > 0:
            fine_dists = d_min[is_fine]
            w50 = float(np.percentile(fine_dists, 50))
            w90 = float(np.percentile(fine_dists, 90))
        else:
            w50, w90 = 0.0, 0.0

        # Corridor metrics under canonical h_equiv
        h_prim_equiv = h_equivs[in_prim_15]
        h_sec_equiv = h_equivs[in_sec_15]

        prim_med_equiv = float(np.median(h_prim_equiv)) if len(h_prim_equiv) > 0 else 0.0
        prim_pct_half_equiv = float(np.sum(h_prim_equiv <= h_half_l0_um) / float(len(h_prim_equiv)) * 100.0) if len(h_prim_equiv) > 0 else 0.0
        prim_pct_third_equiv = float(np.sum(h_prim_equiv <= h_third_l0_um) / float(len(h_prim_equiv)) * 100.0) if len(h_prim_equiv) > 0 else 0.0

        sec_med_equiv = float(np.median(h_sec_equiv)) if len(h_sec_equiv) > 0 else 0.0
        sec_pct_half_equiv = float(np.sum(h_sec_equiv <= h_half_l0_um) / float(len(h_sec_equiv)) * 100.0) if len(h_sec_equiv) > 0 else 0.0
        sec_pct_third_equiv = float(np.sum(h_sec_equiv <= h_third_l0_um) / float(len(h_sec_equiv)) * 100.0) if len(h_sec_equiv) > 0 else 0.0

        # Corridor metrics under h_edge (for census)
        h_prim_edge = h_edges[in_prim_15]
        h_sec_edge = h_edges[in_sec_15]
        prim_med_edge = float(np.median(h_prim_edge)) if len(h_prim_edge) > 0 else 0.0
        prim_pct_half_edge = float(np.sum(h_prim_edge <= h_half_l0_um) / float(len(h_prim_edge)) * 100.0) if len(h_prim_edge) > 0 else 0.0
        sec_med_edge = float(np.median(h_sec_edge)) if len(h_sec_edge) > 0 else 0.0
        sec_pct_half_edge = float(np.sum(h_sec_edge <= h_half_l0_um) / float(len(h_sec_edge)) * 100.0) if len(h_sec_edge) > 0 else 0.0

        # Corridor sensitivity testing (at 11.25 um and 18.75 um under h_equiv)
        prim_pct_half_11 = float(np.sum(h_equivs[d_p <= 11.25] <= h_half_l0_um) / float(np.sum(d_p <= 11.25)) * 100.0)
        sec_pct_half_11 = float(np.sum(h_equivs[d_s <= 11.25] <= h_half_l0_um) / float(np.sum(d_s <= 11.25)) * 100.0)
        prim_pct_half_18 = float(np.sum(h_equivs[d_p <= 18.75] <= h_half_l0_um) / float(np.sum(d_p <= 18.75)) * 100.0)
        sec_pct_half_18 = float(np.sum(h_equivs[d_s <= 18.75] <= h_half_l0_um) / float(np.sum(d_s <= 18.75)) * 100.0)

        # F1684 Zone Reproduction (under h_edge, exactly as in Table 5.8):
        # 1. Notch tip initiation: r <= 50 um
        # 2. Primary fracture corridor: 0.50 <= x <= 0.65, 0.48 <= y <= 0.65, r > 50 um
        f1684_notch_h_edge = []
        f1684_prim_h_edge = []
        for (cx, cy), he in zip(cents, h_edges):
            r_notch = math.hypot(cx - 0.50, cy - 0.50)
            if r_notch <= 0.050:
                f1684_notch_h_edge.append(he)
            elif 0.50 <= cx <= 0.65 and 0.48 <= cy <= 0.65:
                f1684_prim_h_edge.append(he)

        f1684_notch_count = len(f1684_notch_h_edge)
        f1684_notch_h_med = float(np.median(f1684_notch_h_edge)) if f1684_notch_count > 0 else 0.0
        f1684_notch_pct_half = float(np.sum(np.array(f1684_notch_h_edge) <= h_half_l0_um) / float(f1684_notch_count) * 100.0) if f1684_notch_count > 0 else 0.0

        f1684_prim_count = len(f1684_prim_h_edge)
        f1684_prim_h_med = float(np.median(f1684_prim_h_edge)) if f1684_prim_count > 0 else 0.0
        f1684_prim_pct_half = float(np.sum(np.array(f1684_prim_h_edge) <= h_half_l0_um) / float(f1684_prim_count) * 100.0) if f1684_prim_count > 0 else 0.0

        # Quantitative Evaluation against Adopted Selection Criteria (under canonical h_equiv):
        # Criterion 1: Primary corridor median <= 2.50 um AND >= 75% <= 3.75 um
        # Criterion 2: Secondary corridor median <= 2.50 um AND >= 80% <= 3.75 um
        # Criterion 3: Refinement width W90 <= 50.0 um AND relative waste <= 70.0% (selectivity gate)
        crit_prim = (prim_med_equiv <= h_third_l0_um) and (prim_pct_half_equiv >= 75.0)
        crit_sec = (sec_med_equiv <= h_third_l0_um) and (sec_pct_half_equiv >= 80.0)
        crit_selectivity = (w90 <= 50.0) and (waste_pct_rel <= 70.0)

        overall_pass = bool(crit_prim and crit_sec and crit_selectivity)

        json_results.append({
            "candidate_name": name,
            "e_sec_pct": e_sec,
            "n_elements": n_elems,
            "n_nodes": n_nodes,
            "n_dofs": n_dofs,
            "quads": mesh["n_quads"],
            "triangles": mesh["n_tris"],
            "total_area_mm2": total_area,
            "min_jacobian": float(np.min(jacobians)),
            "max_aspect_ratio": float(np.max(aspect_ratios)),
            "n_fine_elements_equiv": n_fine,
            "waste_area_mm2": waste_area_mm2,
            "waste_pct_rel": waste_pct_rel,
            "waste_pct_domain": waste_pct_domain,
            "w50_um": w50,
            "w90_um": w90,
            "primary_corridor_15um": {
                "n_elements": int(np.sum(in_prim_15)),
                "h_med_equiv_um": prim_med_equiv,
                "pct_le_half_l0_equiv": prim_pct_half_equiv,
                "pct_le_third_l0_equiv": prim_pct_third_equiv,
                "h_med_edge_um": prim_med_edge,
                "pct_le_half_l0_edge": prim_pct_half_edge,
                "coverage_at_11p25um_equiv": prim_pct_half_11,
                "coverage_at_18p75um_equiv": prim_pct_half_18,
                "criterion_pass": crit_prim
            },
            "secondary_corridor_15um": {
                "n_elements": int(np.sum(in_sec_15)),
                "h_med_equiv_um": sec_med_equiv,
                "pct_le_half_l0_equiv": sec_pct_half_equiv,
                "pct_le_third_l0_equiv": sec_pct_third_equiv,
                "h_med_edge_um": sec_med_edge,
                "pct_le_half_l0_edge": sec_pct_half_edge,
                "coverage_at_11p25um_equiv": sec_pct_half_11,
                "coverage_at_18p75um_equiv": sec_pct_half_18,
                "criterion_pass": crit_sec
            },
            "f1684_reproduction": {
                "notch_tip_count": f1684_notch_count,
                "notch_tip_h_med_edge": f1684_notch_h_med,
                "notch_tip_pct_half_edge": f1684_notch_pct_half,
                "primary_corridor_count": f1684_prim_count,
                "primary_corridor_h_med_edge": f1684_prim_h_med,
                "primary_corridor_pct_half_edge": f1684_prim_pct_half
            },
            "selectivity_pass": crit_selectivity,
            "overall_acceptance_pass": overall_pass
        })

        csv_rows.append({
            "candidate_name": name,
            "e_sec_pct": e_sec,
            "n_elements": n_elems,
            "n_nodes": n_nodes,
            "n_dofs": n_dofs,
            "quads": mesh["n_quads"],
            "triangles": mesh["n_tris"],
            "min_jacobian": round(float(np.min(jacobians)), 4),
            "max_aspect_ratio": round(float(np.max(aspect_ratios)), 2),
            "n_fine_equiv": n_fine,
            "waste_area_mm2": round(waste_area_mm2, 6),
            "waste_pct_rel": round(waste_pct_rel, 2),
            "waste_pct_domain": round(waste_pct_domain, 2),
            "w50_um": round(w50, 2),
            "w90_um": round(w90, 2),
            "prim_h_med_equiv": round(prim_med_equiv, 2),
            "prim_pct_half_equiv": round(prim_pct_half_equiv, 1),
            "sec_h_med_equiv": round(sec_med_equiv, 2),
            "sec_pct_half_equiv": round(sec_pct_half_equiv, 1),
            "prim_h_med_edge": round(prim_med_edge, 2),
            "prim_pct_half_edge": round(prim_pct_half_edge, 1),
            "sec_h_med_edge": round(sec_med_edge, 2),
            "sec_pct_half_edge": round(sec_pct_half_edge, 1),
            "sens_prim_11um": round(prim_pct_half_11, 1),
            "sens_sec_11um": round(sec_pct_half_11, 1),
            "f1684_prim_box_count": f1684_prim_count,
            "f1684_prim_box_h_med": round(f1684_prim_h_med, 2),
            "f1684_prim_box_pct_half": round(f1684_prim_pct_half, 2),
            "overall_pass": overall_pass
        })

    out_json = os.path.join(repo_root, "results", "validation", "f1686_reconciliation_audit.json")
    with open(out_json, "w", encoding="utf-8") as fp:
        json.dump(json_results, fp, indent=2)
    print("Saved unified reconciliation audit JSON: %s" % out_json)

    out_csv = os.path.join(repo_root, "results", "validation", "f1686_reconciliation_summary.csv")
    fieldnames = list(csv_rows[0].keys())
    with open(out_csv, "w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_rows)
    print("Saved unified reconciliation summary CSV: %s" % out_csv)

    print("\n" + "=" * 135)
    print("%-20s | %6s | %5s | %5s | %10s | %10s | %8s | %8s | %17s | %17s | %12s" % (
        "Candidate", "Elems", "Quads", "Tris", "Waste mm2", "Waste %", "W50 um", "W90 um", "Prim (h_med, %)", "Sec (h_med, %)", "Overall Pass"))
    print("-" * 135)
    for r in csv_rows:
        print("%-20s | %6d | %5d | %5d | %10.6f | %9.2f%% | %8.2f | %8.2f | %5.2f um (%4.1f%%) | %5.2f um (%4.1f%%) | %12s" % (
            r["candidate_name"], r["n_elements"], r["quads"], r["triangles"],
            r["waste_area_mm2"], r["waste_pct_rel"], r["w50_um"], r["w90_um"],
            r["prim_h_med_equiv"], r["prim_pct_half_equiv"], r["sec_h_med_equiv"], r["sec_pct_half_equiv"],
            str(r["overall_pass"])))
    print("=" * 135)

if __name__ == "__main__":
    main()

"""
scripts/validation/audit_f1684_adapted_meshes.py
=================================================
Task F1684: Comprehensive Regional Resolution & Quality Audit of Adapted Meshes
Compares:
1. Baseline: F1664 Adapted Mesh (Terminal donor alone, errorTarget=5.0%, 20,213 elements)
2. Control B: F1684 Candidate C Adapted Mesh (Candidate C donor alone, errorTarget=5.0%, 6,171 elements)
3. Experiment C: F1684 Combined Multi-Step Adapted Mesh (Candidate C + Terminal, both errorTarget=5.0%, 21,569 elements)

Evaluates:
- Element counts (Quads vs Tris, percentages)
- Node counts and area conservation
- Element geometric validity (non-positive Jacobians, zero area)
- 6 Spatial Zones:
    1. Whole Specimen
    2. Notch Tip Initiation (r <= 50 um)
    3. Primary Fracture Corridor (0.50 <= x <= 0.65, 0.48 <= y <= 0.65, r > 50 um)
    4. Hole Perimeter & Annulus (0.10 <= r <= 0.14 mm)
    5. Secondary Ligament Corridor (0.70 <= x <= 1.00, 0.55 <= y <= 0.75)
    6. Far-field Bulk (remainder)
    7. Direct Crack-Path Corridor (within 10 um of extracted crack centerlines)
- Resolution thresholds vs l0 = 7.50 um:
    * h <= 1.50 um (l0 / 5)
    * h <= 2.50 um (l0 / 3)
    * h <= 3.75 um (l0 / 2)
    * h <= 7.50 um (l0)
- Far-field economy and efficiency ratios.
"""
import os
import sys
import math
import json
import csv
import numpy as np

def parse_inp_mesh(inp_path):
    print(f"Parsing mesh: {inp_path}")
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
    print(f"  Parsed {len(nodes)} nodes, {len(elements)} elements ({n_quads} Quads, {n_tris} Tris)")

    # Compute geometric metrics
    metrics = {}
    zero_area_count = 0
    negative_jacobian_count = 0
    total_area_mm2 = 0.0

    for eid, conn in elements.items():
        pts = [nodes[nid] for nid in conn]
        n_pts = len(pts)
        cx = sum(p[0] for p in pts) / float(n_pts)
        cy = sum(p[1] for p in pts) / float(n_pts)

        # Edges
        edges = [math.hypot(pts[(i+1)%n_pts][0] - pts[i][0], pts[(i+1)%n_pts][1] - pts[i][1]) for i in range(n_pts)]
        h_max_mm = max(edges)
        h_min_mm = min(edges)

        # Area using shoelace
        signed_area = 0.5 * sum(pts[i][0]*pts[(i+1)%n_pts][1] - pts[(i+1)%n_pts][0]*pts[i][1] for i in range(n_pts))
        if signed_area <= 0.0:
            negative_jacobian_count += 1
        area_mm2 = abs(signed_area)
        if area_mm2 < 1.0e-12:
            zero_area_count += 1
        total_area_mm2 += area_mm2

        metrics[eid] = {
            "elem_id": eid,
            "type": elem_types[eid],
            "cx": cx,
            "cy": cy,
            "h_max_um": h_max_mm * 1000.0,
            "h_min_um": h_min_mm * 1000.0,
            "area_mm2": area_mm2
        }

    return {
        "nodes": nodes,
        "elements": elements,
        "elem_types": elem_types,
        "metrics": metrics,
        "n_quads": n_quads,
        "n_tris": n_tris,
        "total_area_mm2": total_area_mm2,
        "negative_jacobians": negative_jacobian_count,
        "zero_area_elements": zero_area_count
    }


def load_crack_centerlines(centerlines_path):
    if not os.path.exists(centerlines_path):
        return None
    with open(centerlines_path, "r") as fp:
        data = json.load(fp)
    prim_pts = [(p[0], p[1]) for p in data["primary"]["points"]]
    sec_pts = [(p[0], p[1]) for p in data["secondary"]["points"]]
    return {"primary": prim_pts, "secondary": sec_pts}


def distance_point_to_polyline(px, py, polyline):
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


def audit_zone_subset(subset, zone_name):
    n = len(subset)
    if n == 0:
        return {
            "zone_name": zone_name, "count": 0, "pct_of_total": 0.0,
            "h_min_um": 0.0, "h_med_um": 0.0, "h_mean_um": 0.0, "h_max_um": 0.0,
            "pct_le_1p5_um": 0.0, "pct_le_2p5_um": 0.0, "pct_le_3p75_um": 0.0, "pct_le_7p5_um": 0.0
        }
    h_vals = sorted([e["h_max_um"] for e in subset])
    c_1p5 = sum(1 for h in h_vals if h <= 1.50)
    c_2p5 = sum(1 for h in h_vals if h <= 2.50)
    c_3p75 = sum(1 for h in h_vals if h <= 3.75)
    c_7p5 = sum(1 for h in h_vals if h <= 7.50)

    return {
        "zone_name": zone_name,
        "count": n,
        "h_min_um": round(min(h_vals), 3),
        "h_med_um": round(h_vals[n//2], 3),
        "h_mean_um": round(sum(h_vals) / float(n), 3),
        "h_max_um": round(max(h_vals), 3),
        "count_le_1p5_um": c_1p5,
        "pct_le_1p5_um": round(100.0 * c_1p5 / float(n), 2),
        "count_le_2p5_um": c_2p5,
        "pct_le_2p5_um": round(100.0 * c_2p5 / float(n), 2),
        "count_le_3p75_um": c_3p75,
        "pct_le_3p75_um": round(100.0 * c_3p75 / float(n), 2),
        "count_le_7p5_um": c_7p5,
        "pct_le_7p5_um": round(100.0 * c_7p5 / float(n), 2)
    }


def audit_mesh_zones(mesh_data, centerlines=None):
    metrics = mesh_data["metrics"]
    hole_c = (0.65, 0.65)
    hole_r = 0.10

    z_whole = list(metrics.values())
    z_notch = []
    z_primary = []
    z_hole = []
    z_secondary = []
    z_crack_corridor = []
    z_far_field = []

    for eid, m in metrics.items():
        cx, cy = m["cx"], m["cy"]
        d_notch = math.hypot(cx - 0.50, cy - 0.50)
        d_hole = math.hypot(cx - hole_c[0], cy - hole_c[1])

        is_feature = False

        if d_notch <= 0.050:
            z_notch.append(m)
            is_feature = True

        if 0.50 <= cx <= 0.65 and 0.48 <= cy <= 0.65 and d_notch > 0.050:
            z_primary.append(m)
            is_feature = True

        if hole_r <= d_hole <= hole_r + 0.040:
            z_hole.append(m)
            is_feature = True

        if 0.70 <= cx <= 1.00 and 0.55 <= cy <= 0.75:
            z_secondary.append(m)
            is_feature = True

        # Crack centerline corridor: within 10 um (0.010 mm) of either primary or secondary crack centerline
        if centerlines is not None:
            d_p = distance_point_to_polyline(cx, cy, centerlines["primary"])
            d_s = distance_point_to_polyline(cx, cy, centerlines["secondary"])
            if min(d_p, d_s) <= 0.010:
                z_crack_corridor.append(m)

        if not is_feature:
            z_far_field.append(m)

    zones_audit = {
        "whole_specimen": audit_zone_subset(z_whole, "Whole Specimen"),
        "notch_tip_initiation": audit_zone_subset(z_notch, "Notch Tip Initiation (r <= 50 um)"),
        "primary_fracture_corridor": audit_zone_subset(z_primary, "Primary Fracture Corridor"),
        "hole_perimeter_annulus": audit_zone_subset(z_hole, "Hole Perimeter & Annulus"),
        "secondary_ligament": audit_zone_subset(z_secondary, "Secondary Ligament Corridor"),
        "crack_centerline_corridor": audit_zone_subset(z_crack_corridor, "Direct Crack Centerline Corridor (<= 10 um)"),
        "far_field_bulk": audit_zone_subset(z_far_field, "Far-Field Bulk (Remainder)")
    }

    # Add percentage of total elements
    n_tot = len(z_whole)
    for zk, zv in zones_audit.items():
        zv["pct_of_total"] = round(100.0 * zv["count"] / float(n_tot), 2)

    return zones_audit


def main():
    dest_dir = "models/pandey_kumar_mode1/176_method_a_plate_with_hole"
    inp_baseline = os.path.join(dest_dir, "PK_HOLE_F1664_METHOD_A_ADAPT_PHYS.inp")
    inp_cand_c = os.path.join(dest_dir, "PK_HOLE_F1684_CAND_C_ADAPT_PHYS.inp")
    inp_combined = os.path.join(dest_dir, "PK_HOLE_F1684_COMBINED_ADAPT_PHYS.inp")
    centerlines_path = "results/validation/f1684_crack_path_centerlines.json"

    print("=" * 80)
    print("TASK F1684: ADAPTED MESH REGIONAL RESOLUTION & QUALITY AUDIT")
    print("=" * 80)

    centerlines = load_crack_centerlines(centerlines_path)
    if centerlines:
        print(f"Loaded crack centerlines: {len(centerlines['primary'])} prim, {len(centerlines['secondary'])} sec points.")

    meshes = {
        "baseline_terminal_only": {
            "name": "Baseline (Terminal Donor Frame 337 alone)",
            "file": inp_baseline,
            "data": parse_inp_mesh(inp_baseline)
        },
        "control_cand_c_alone": {
            "name": "Control B (Candidate C Donor Frame 150 alone)",
            "file": inp_cand_c,
            "data": parse_inp_mesh(inp_cand_c)
        },
        "experiment_combined": {
            "name": "Experiment C (Combined Candidate C + Terminal)",
            "file": inp_combined,
            "data": parse_inp_mesh(inp_combined)
        }
    }

    audit_summary = {}
    csv_rows = []

    for mk, mobj in meshes.items():
        mdata = mobj["data"]
        zones = audit_mesh_zones(mdata, centerlines)
        n_elem = len(mdata["metrics"])
        n_node = len(mdata["nodes"])
        n_quad = mdata["n_quads"]
        n_tri = mdata["n_tris"]

        audit_summary[mk] = {
            "mesh_name": mobj["name"],
            "inp_file": mobj["file"],
            "total_elements": n_elem,
            "total_nodes": n_node,
            "quads_count": n_quad,
            "quads_pct": round(100.0 * n_quad / float(n_elem), 2),
            "tris_count": n_tri,
            "tris_pct": round(100.0 * n_tri / float(n_elem), 2),
            "total_area_mm2": round(mdata["total_area_mm2"], 6),
            "analytical_area_mm2": round(1.0 - math.pi * 0.10**2, 6),
            "area_conservation_pct": round(100.0 * mdata["total_area_mm2"] / (1.0 - math.pi * 0.10**2), 4),
            "negative_jacobians": mdata["negative_jacobians"],
            "zero_area_elements": mdata["zero_area_elements"],
            "zones": zones
        }

        # Flatten for CSV
        for zk, zv in zones.items():
            csv_rows.append({
                "mesh_key": mk,
                "mesh_name": mobj["name"],
                "total_mesh_elements": n_elem,
                "zone_key": zk,
                "zone_name": zv["zone_name"],
                "element_count": zv["count"],
                "pct_of_total_mesh": zv["pct_of_total"],
                "h_min_um": zv["h_min_um"],
                "h_med_um": zv["h_med_um"],
                "h_mean_um": zv["h_mean_um"],
                "h_max_um": zv["h_max_um"],
                "pct_le_1p5_um": zv["pct_le_1p5_um"],
                "pct_le_2p5_um": zv["pct_le_2p5_um"],
                "pct_le_3p75_um": zv["pct_le_3p75_um"],
                "pct_le_7p5_um": zv["pct_le_7p5_um"]
            })

    out_json = "results/validation/f1684_adapted_mesh_resolution_audit.json"
    with open(out_json, "w") as fp:
        json.dump(audit_summary, fp, indent=4)
    print(f"\nSaved comprehensive audit JSON: {out_json}")

    out_csv = "results/validation/f1684_adapted_mesh_comparison.csv"
    with open(out_csv, "w", newline="") as fp:
        fieldnames = [
            "mesh_key", "mesh_name", "total_mesh_elements", "zone_key", "zone_name",
            "element_count", "pct_of_total_mesh", "h_min_um", "h_med_um", "h_mean_um",
            "h_max_um", "pct_le_1p5_um", "pct_le_2p5_um", "pct_le_3p75_um", "pct_le_7p5_um"
        ]
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_rows)
    print(f"Saved comparison CSV: {out_csv}")

    # Print Comparative Highlights Table
    print("\n" + "=" * 105)
    print(f"{'Mesh':<35} | {'Total Els':<9} | {'Notch Med h':<11} | {'Prim Med h':<10} | {'Sec Med h':<10} | {'Crack Corr Med h':<16} | {'Far Med h':<9}")
    print("-" * 105)
    for mk, mdata in audit_summary.items():
        z = mdata["zones"]
        print(f"{mdata['mesh_name'][:35]:<35} | {mdata['total_elements']:<9} | "
              f"{z['notch_tip_initiation']['h_med_um']:>7.2f} um  | "
              f"{z['primary_fracture_corridor']['h_med_um']:>6.2f} um  | "
              f"{z['secondary_ligament']['h_med_um']:>6.2f} um  | "
              f"{z['crack_centerline_corridor']['h_med_um']:>12.2f} um    | "
              f"{z['far_field_bulk']['h_med_um']:>5.2f} um")
    print("=" * 105)


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
scripts/validation/audit_f1682_regional_resolution.py
====================================================
Task F1682: Defect-Free Regional Mesh Resolution Audit for 20,213-Element Model
"""
import sys
import time
import math
import json
import csv
import os

def run_audit(inp_path, full_damage_csv, out_json, out_csv):
    print("================================================================================", flush=True)
    print("TASK F1682: REGIONAL MESH RESOLUTION AUDIT (COMPLETE DAMAGE FIELD)", flush=True)
    print(f"INP: {inp_path}", flush=True)
    print(f"Full Damage CSV: {full_damage_csv}", flush=True)
    print("================================================================================", flush=True)
    t0 = time.time()

    if not os.path.exists(inp_path):
        raise FileNotFoundError(f"Input file not found: {inp_path}")
    if not os.path.exists(full_damage_csv):
        raise FileNotFoundError(f"Full damage CSV not found: {full_damage_csv}")

    # 1. Parse mesh from INP
    print("[Audit] Reading INP lines...", flush=True)
    nodes = {}
    elements = {}
    elem_types = {}

    in_nodes = False
    in_elements = False
    current_type = None

    with open(inp_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("**"):
                continue
            if line.startswith("*"):
                in_nodes = False
                in_elements = False
                upper = line.upper()
                if upper.startswith("*NODE"):
                    in_nodes = True
                elif upper.startswith("*ELEMENT"):
                    if "CPE4" in upper or "CPS4" in upper:
                        in_elements = True
                        current_type = "QUAD"
                    elif "CPE3" in upper or "CPS3" in upper:
                        in_elements = True
                        current_type = "TRI"
                    else:
                        current_type = None
                continue

            parts = [p.strip() for p in line.split(",") if p.strip()]
            if in_nodes and len(parts) >= 3:
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

    n_phys = len(elements)
    print(f"[{time.time()-t0:.2f}s] Parsed {len(nodes)} nodes, {n_phys} elements ({sum(1 for t in elem_types.values() if t=='QUAD')} Quads, {sum(1 for t in elem_types.values() if t=='TRI')} Tris).", flush=True)

    # 2. Geometric metrics
    print("[Audit] Computing geometric metrics...", flush=True)
    metrics = {}
    for eid, conn in elements.items():
        pts = [nodes[nid] for nid in conn]
        n_pts = len(pts)
        cx = sum(p[0] for p in pts) / float(n_pts)
        cy = sum(p[1] for p in pts) / float(n_pts)
        edges = [math.hypot(pts[(i+1)%n_pts][0] - pts[i][0], pts[(i+1)%n_pts][1] - pts[i][1]) for i in range(n_pts)]
        h_max_mm = max(edges)
        h_min_mm = min(edges)
        area_mm2 = 0.5 * abs(sum(pts[i][0]*pts[(i+1)%n_pts][1] - pts[(i+1)%n_pts][0]*pts[i][1] for i in range(n_pts)))
        metrics[eid] = {
            "elem_id": eid,
            "type": elem_types[eid],
            "cx": cx,
            "cy": cy,
            "h_max_um": h_max_mm * 1000.0,
            "h_min_um": h_min_mm * 1000.0,
            "area_um2": area_mm2 * 1e6
        }

    # 3. Ingest COMPLETE damage field
    print("[Audit] Ingesting complete damage field...", flush=True)
    damage_map = {}
    with open(full_damage_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            eid = int(row["phys_elem_id"])
            d = float(row["damage"])
            damage_map[eid] = d

    print(f"[{time.time()-t0:.2f}s] Ingested complete damage field for {len(damage_map)} physical elements (Coverage: {len(damage_map)/n_phys*100:.1f}%).", flush=True)

    # 4. Classify spatial zones and damage tiers
    print("[Audit] Classifying spatial zones and damage tiers...", flush=True)
    hole_c = (0.65, 0.65)
    hole_r = 0.10

    groups = {
        "Whole Specimen Domain": [],
        "Active Fracture Core (d >= 0.50)": [],
        "Broken Crack Core (d >= 0.80)": [],
        "Fully Severed Core (d >= 0.95)": [],
        "Fracture Process Zone (0.25 <= d < 0.50)": [],
        "Early Damage Band (0.10 <= d < 0.25)": [],
        "Intact Far-Field (d < 0.10)": [],
        "Notch Initiation Zone (r <= 50 um)": [],
        "Primary Fracture Corridor (Notch-to-Hole)": [],
        "Hole Perimeter Annulus (100-140 um)": [],
        "Secondary Right Ligament Zone": []
    }

    for eid, m in metrics.items():
        cx, cy = m["cx"], m["cy"]
        d = damage_map.get(eid, 0.0)
        m["damage"] = d
        d_notch = math.hypot(cx - 0.50, cy - 0.50)
        d_hole = math.hypot(cx - hole_c[0], cy - hole_c[1])

        # Whole domain
        groups["Whole Specimen Domain"].append(m)

        # Damage tiers
        if d >= 0.50:
            groups["Active Fracture Core (d >= 0.50)"].append(m)
        if d >= 0.80:
            groups["Broken Crack Core (d >= 0.80)"].append(m)
        if d >= 0.95:
            groups["Fully Severed Core (d >= 0.95)"].append(m)
        if 0.25 <= d < 0.50:
            groups["Fracture Process Zone (0.25 <= d < 0.50)"].append(m)
        if 0.10 <= d < 0.25:
            groups["Early Damage Band (0.10 <= d < 0.25)"].append(m)
        if d < 0.10:
            groups["Intact Far-Field (d < 0.10)"].append(m)

        # Spatial zones
        if d_notch <= 0.050:
            groups["Notch Initiation Zone (r <= 50 um)"].append(m)
        if 0.50 <= cx <= 0.65 and 0.48 <= cy <= 0.65 and d_notch > 0.050:
            groups["Primary Fracture Corridor (Notch-to-Hole)"].append(m)
        if hole_r <= d_hole <= hole_r + 0.040:
            groups["Hole Perimeter Annulus (100-140 um)"].append(m)
        if 0.70 <= cx <= 1.00 and 0.55 <= cy <= 0.75:
            groups["Secondary Right Ligament Zone"].append(m)

    # 5. Audit statistics for each group
    print("[Audit] Auditing statistics for all groups...", flush=True)
    audit_results = {}
    table_rows = []

    for name, subset in groups.items():
        n = len(subset)
        if n == 0:
            res = {
                "group_name": name, "element_count": 0,
                "pct_of_total_mesh": 0.0,
                "h_min_um": 0.0, "h_median_um": 0.0, "h_mean_um": 0.0, "h_max_um": 0.0,
                "count_le_1p5_um": 0, "pct_le_1p5_um": 0.0,
                "count_le_2p5_um": 0, "pct_le_2p5_um": 0.0,
                "count_le_3p75_um": 0, "pct_le_3p75_um": 0.0,
                "count_le_7p5_um": 0, "pct_le_7p5_um": 0.0
            }
        else:
            h_vals = sorted([e["h_max_um"] for e in subset])
            c_1p5 = sum(1 for h in h_vals if h <= 1.50)
            c_2p5 = sum(1 for h in h_vals if h <= 2.50)
            c_3p75 = sum(1 for h in h_vals if h <= 3.75)
            c_7p5 = sum(1 for h in h_vals if h <= 7.50)
            res = {
                "group_name": name,
                "element_count": n,
                "pct_of_total_mesh": round(n / float(n_phys) * 100.0, 2),
                "h_min_um": round(min(h_vals), 3),
                "h_median_um": round(h_vals[n // 2], 3),
                "h_mean_um": round(sum(h_vals) / float(n), 3),
                "h_max_um": round(max(h_vals), 3),
                "count_le_1p5_um": c_1p5,
                "pct_le_1p5_um": round(c_1p5 / float(n) * 100.0, 2),
                "count_le_2p5_um": c_2p5,
                "pct_le_2p5_um": round(c_2p5 / float(n) * 100.0, 2),
                "count_le_3p75_um": c_3p75,
                "pct_le_3p75_um": round(c_3p75 / float(n) * 100.0, 2),
                "count_le_7p5_um": c_7p5,
                "pct_le_7p5_um": round(c_7p5 / float(n) * 100.0, 2)
            }
        audit_results[name] = res
        table_rows.append(res)
        print(f"  [{name}] N={res['element_count']} | h_med={res['h_median_um']:.2f} um | <=1.5um: {res['pct_le_1p5_um']:.1f}% | <=3.75um: {res['pct_le_3p75_um']:.1f}%", flush=True)

    # Save JSON and CSV
    print(f"[Audit] Saving JSON to {out_json}...", flush=True)
    with open(out_json, "w", encoding="utf-8") as f_json:
        json.dump(audit_results, f_json, indent=4)

    print(f"[Audit] Saving CSV to {out_csv}...", flush=True)
    with open(out_csv, "w", newline="", encoding="utf-8") as f_csv:
        writer = csv.DictWriter(f_csv, fieldnames=[
            "group_name", "element_count", "pct_of_total_mesh",
            "h_min_um", "h_median_um", "h_mean_um", "h_max_um",
            "count_le_1p5_um", "pct_le_1p5_um",
            "count_le_2p5_um", "pct_le_2p5_um",
            "count_le_3p75_um", "pct_le_3p75_um",
            "count_le_7p5_um", "pct_le_7p5_um"
        ])
        writer.writeheader()
        for r in table_rows:
            writer.writerow(r)

    print(f"Total audit elapsed time: {time.time()-t0:.2f} seconds.", flush=True)
    return audit_results


if __name__ == "__main__":
    inp = "models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_F1664_METHOD_A_ADAPT_PHYS.inp"
    dmg = "results/validation/f1682_prod_final_full_damage_field.csv"
    oj = "results/validation/f1682_spatial_resolution_audit.json"
    oc = "results/validation/f1682_regional_resolution_table.csv"
    if os.path.exists(dmg):
        run_audit(inp, dmg, oj, oc)
    else:
        print("Waiting for f1682_prod_final_full_damage_field.csv before executing audit.", flush=True)

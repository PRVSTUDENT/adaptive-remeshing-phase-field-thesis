# -*- coding: utf-8 -*-
"""
scripts/remeshing/evaluate_stage_c_candidates.py
Task F1686 - Stage C/D: Evaluates all generated candidate meshes against the crack corridors:
- Primary corridor resolution & coverage (h <= 3.75 um)
- Secondary corridor resolution & coverage (h <= 3.75 um)
- Out-of-corridor fine-element waste metric (%)
- Transverse refinement half-widths W50 and W90 (um)
- Element count reduction vs. 21,569 baseline
"""
import os
import glob
import json
import math
import numpy as np
from shapely.geometry import Point, LineString

def parse_inp_mesh(inp_path):
    nodes = {}
    elements = {}
    in_nodes = False
    in_elems = False

    with open(inp_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            line_upper = line.upper()
            if line_upper.startswith('*NODE'):
                in_nodes = True
                in_elems = False
                continue
            elif line_upper.startswith('*ELEMENT'):
                in_nodes = False
                in_elems = True
                continue
            elif line_upper.startswith('*'):
                in_nodes = False
                in_elems = False
                continue

            if in_nodes:
                parts = [p.strip() for p in line.split(',')]
                try:
                    nid = int(parts[0])
                    x = float(parts[1])
                    y = float(parts[2])
                    nodes[nid] = (x, y)
                except (ValueError, IndexError):
                    pass
            elif in_elems:
                parts = [p.strip() for p in line.split(',')]
                try:
                    eid = int(parts[0])
                    conn = [int(p) for p in parts[1:]]
                    elements[eid] = conn
                except (ValueError, IndexError):
                    pass
    return nodes, elements

def compute_element_geometry(nodes, conn):
    pts = [nodes[nid] for nid in conn]
    n = len(pts)
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += pts[i][0] * pts[j][1] - pts[j][0] * pts[i][1]
    area = abs(area) * 0.5
    cx = sum(p[0] for p in pts) / n
    cy = sum(p[1] for p in pts) / n
    return area, (cx, cy)

def evaluate_mesh(mesh_name, inp_path, primary_line, secondary_line):
    nodes, elements = parse_inp_mesh(inp_path)
    n_elems = len(elements)
    n_nodes = len(nodes)

    quads = 0
    tris = 0
    areas = []
    h_sizes = []
    centroids = []

    for eid, conn in elements.items():
        if len(conn) == 4:
            quads += 1
        elif len(conn) == 3:
            tris += 1
        a, c = compute_element_geometry(nodes, conn)
        areas.append(a)
        h_sizes.append(math.sqrt(a) * 1e3)  # um
        centroids.append(c)

    total_area = sum(areas)
    h_sizes = np.array(h_sizes)
    l0_um = 7.50
    h_target_um = l0_um / 2.0  # 3.75 um

    # Corridor evaluations
    prim_dists = np.array([primary_line.distance(Point(c)) * 1e3 for c in centroids])
    sec_dists = np.array([secondary_line.distance(Point(c)) * 1e3 for c in centroids])
    min_dists = np.minimum(prim_dists, sec_dists)

    in_prim_corridor = prim_dists <= 15.0
    in_sec_corridor = sec_dists <= 15.0

    # Fine elements: h <= 3.75 um
    is_fine = h_sizes <= h_target_um
    fine_indices = np.where(is_fine)[0]
    n_fine = len(fine_indices)

    if n_fine > 0:
        fine_areas = np.array(areas)[fine_indices]
        fine_min_dists = min_dists[fine_indices]

        fine_out_corridor = fine_min_dists > 15.0
        waste_area = np.sum(fine_areas[fine_out_corridor])
        total_fine_area = np.sum(fine_areas)
        waste_pct = (waste_area / total_fine_area * 100.0) if total_fine_area > 0 else 0.0

        sorted_dists = np.sort(fine_min_dists)
        w50 = np.percentile(sorted_dists, 50)
        w90 = np.percentile(sorted_dists, 90)
    else:
        waste_pct = 0.0
        w50 = 0.0
        w90 = 0.0

    # Primary corridor stats
    h_prim = h_sizes[in_prim_corridor]
    prim_pct_l0 = (np.sum(h_prim <= l0_um) / len(h_prim) * 100.0) if len(h_prim) > 0 else 0.0
    prim_pct_half_l0 = (np.sum(h_prim <= h_target_um) / len(h_prim) * 100.0) if len(h_prim) > 0 else 0.0
    prim_h_med = np.median(h_prim) if len(h_prim) > 0 else 0.0

    # Secondary corridor stats
    h_sec = h_sizes[in_sec_corridor]
    sec_pct_l0 = (np.sum(h_sec <= l0_um) / len(h_sec) * 100.0) if len(h_sec) > 0 else 0.0
    sec_pct_half_l0 = (np.sum(h_sec <= h_target_um) / len(h_sec) * 100.0) if len(h_sec) > 0 else 0.0
    sec_h_med = np.median(h_sec) if len(h_sec) > 0 else 0.0

    return {
        "candidate_name": mesh_name,
        "input_deck": os.path.basename(inp_path),
        "n_elements": n_elems,
        "n_nodes": n_nodes,
        "quads": quads,
        "triangles": tris,
        "total_area_mm2": float(total_area),
        "h_min_um": float(np.min(h_sizes)),
        "h_median_um": float(np.median(h_sizes)),
        "h_max_um": float(np.max(h_sizes)),
        "n_fine_elements": int(n_fine),
        "waste_area_pct": float(waste_pct),
        "w50_um": float(w50),
        "w90_um": float(w90),
        "primary_corridor": {
            "n_elements": int(len(h_prim)),
            "h_med_um": float(prim_h_med),
            "pct_le_l0": float(prim_pct_l0),
            "pct_le_half_l0": float(prim_pct_half_l0)
        },
        "secondary_corridor": {
            "n_elements": int(len(h_sec)),
            "h_med_um": float(sec_h_med),
            "pct_le_l0": float(sec_pct_l0),
            "pct_le_half_l0": float(sec_pct_half_l0)
        }
    }

def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    # Load centerlines
    centerlines_path = os.path.join(repo_root, "results", "validation", "f1684_crack_path_centerlines.json")
    with open(centerlines_path, 'r') as f:
        cl_data = json.load(f)

    prim_pts = [(p[0], p[1]) for p in cl_data['primary']['points']]
    sec_pts = [(p[0], p[1]) for p in cl_data['secondary']['points']]
    prim_line = LineString(prim_pts)
    sec_line = LineString(sec_pts)

    cand_dir = os.path.join(repo_root, "models", "pandey_kumar_mode1", "176_method_a_plate_with_hole", "candidates")
    inp_files = sorted(glob.glob(os.path.join(cand_dir, "PK_HOLE_SEL_E*.inp")))

    if not inp_files:
        print("No candidate inp files found in: %s" % cand_dir)
        return

    print("=" * 110)
    print("TASK F1686 - STAGE C/D: CANDIDATE MESH SELECTIVITY & CORRIDOR COVERAGE EVALUATION")
    print("=" * 110)
    print("Candidate Name        | Elements | Quads/Tris  | Fine (h<=3.75) | Waste % | W50 (um) | W90 (um) | Prim h_med (<=l0/2) | Sec h_med (<=l0/2)")
    print("-" * 110)

    results = []
    for p in inp_files:
        base = os.path.splitext(os.path.basename(p))[0]
        res = evaluate_mesh(base, p, prim_line, sec_line)
        results.append(res)
        print("%-21s | %8d | %5d/%-5d | %14d | %6.2f%% | %8.2f | %8.2f | %5.2f um (%4.1f%%)   | %5.2f um (%4.1f%%)" % (
            res["candidate_name"], res["n_elements"], res["quads"], res["triangles"],
            res["n_fine_elements"], res["waste_area_pct"], res["w50_um"], res["w90_um"],
            res["primary_corridor"]["h_med_um"], res["primary_corridor"]["pct_le_half_l0"],
            res["secondary_corridor"]["h_med_um"], res["secondary_corridor"]["pct_le_half_l0"]
        ))

    out_json = os.path.join(repo_root, "results", "validation", "f1686_stage_c_candidate_evaluation.json")
    with open(out_json, 'w') as f:
        json.dump(results, f, indent=2)

    print("\nSaved Candidate Evaluation to: %s" % out_json)

if __name__ == '__main__':
    main()

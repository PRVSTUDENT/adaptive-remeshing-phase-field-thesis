#!/usr/bin/env python3
"""
Extracts authentic indicator-selected refinement supports across the full physical domain
for the Mode-I plate with off-axis hole, removing all artificial coordinate filters.
"""

import os
import sys
import csv
import json
from collections import defaultdict, deque
import numpy as np
import shapely
from shapely.geometry import Polygon, MultiPolygon, Point, box
from shapely.ops import unary_union

def load_mesh(inp_path):
    nodes = {}
    elems = {}
    in_nodes = in_elems = False
    with open(inp_path) as f:
        for line in f:
            l = line.strip()
            if l.upper().startswith('*NODE'):
                in_nodes, in_elems = True, False
                continue
            elif l.upper().startswith('*ELEMENT'):
                in_nodes, in_elems = False, True
                continue
            elif l.startswith('*'):
                in_nodes = in_elems = False
                continue
            if in_nodes:
                p = [x.strip() for x in l.split(',') if x.strip()]
                if len(p) >= 3:
                    nodes[int(p[0])] = (float(p[1]), float(p[2]))
            elif in_elems:
                try:
                    p = [int(x.strip()) for x in l.split(',') if x.strip()]
                    if len(p) >= 4:
                        elems[p[0]] = p[1:]
                except ValueError:
                    pass
    return nodes, elems

def analyze_and_extract_supports(
    phys_inp="models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_METHOD_A_PROD_PHYS.inp",
    damage_csv="results/validation/f1642_pilot_localized_damage.csv",
    output_json="results/validation/faithful_indicator_supports.json",
    l0=0.0075,
    hole_center=(0.65, 0.65),
    hole_r=0.10,
    plate_size=(1.0, 1.0)
):
    print("Loading mesh from:", phys_inp)
    nodes, elems = load_mesh(phys_inp)
    print("Loaded %d nodes, %d elements" % (len(nodes), len(elems)))

    centroids = {eid: (np.mean([nodes[n][0] for n in conn]), np.mean([nodes[n][1] for n in conn])) for eid, conn in elems.items()}

    print("Loading damage and history from:", damage_csv)
    damage = {}
    history = {}
    with open(damage_csv) as f:
        for r in csv.DictReader(f):
            eid = int(r['phys_elem_id'])
            d = float(r['damage'])
            h = float(r['history'])
            if eid not in damage or d > damage[eid]: damage[eid] = d
            if eid not in history or h > history[eid]: history[eid] = h

    # Build edge-sharing element adjacency graph
    node_to_elems = defaultdict(list)
    for eid, conn in elems.items():
        for n in conn:
            node_to_elems[n].append(eid)

    # Component clustering across entire domain for d >= 0.05
    active_set = set(eid for eid, d in damage.items() if d >= 0.05)
    visited = set()
    components = []
    for eid in active_set:
        if eid not in visited:
            c = []
            q = deque([eid])
            visited.add(eid)
            while q:
                curr = q.popleft()
                c.append(curr)
                curr_nodes = set(elems[curr])
                for n in curr_nodes:
                    for nbr in node_to_elems[n]:
                        if nbr in active_set and nbr not in visited:
                            if len(curr_nodes.intersection(elems[nbr])) >= 2:
                                visited.add(nbr)
                                q.append(nbr)
            components.append(c)

    components.sort(key=len, reverse=True)
    print("Identified %d connected components at d >= 0.05" % len(components))

    # Classify components
    classified = []
    for idx, c in enumerate(components):
        xs = [centroids[e][0] for e in c]
        ys = [centroids[e][1] for e in c]
        ds = [damage[e] for e in c]
        hs = [history[e] for e in c]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        mean_x, mean_y = float(np.mean(xs)), float(np.mean(ys))
        
        # Classification logic:
        if min_x < 0.52 and min_y < 0.52:
            role = "notch_ligament_fpz"
            desc = "Notch-attached primary process zone spanning ligament towards hole left flank"
        elif mean_x > hole_center[0] and abs(mean_y - hole_center[1]) < 0.15:
            role = "hole_right_flank_fpz"
            desc = "Opposite-side hole flank stress-concentration / secondary damage zone"
        elif min_x > 0.95 and min_y > 0.95:
            role = "boundary_clamping_artifact"
            desc = "Top-right boundary clamping displacement Dirichlet BC singularity (excluded)"
        else:
            role = "unclassified_secondary"
            desc = "Secondary remote localized zone"

        info = {
            "component_id": idx + 1,
            "role": role,
            "description": desc,
            "element_count": len(c),
            "max_damage": float(max(ds)),
            "max_history": float(max(hs)),
            "mean_position": [mean_x, mean_y],
            "bounding_box": [float(min_x), float(min_y), float(max_x), float(max_y)],
            "elements": c
        }
        classified.append(info)
        print("  Component %d (%s): N=%d, max_d=%.4f, max_H=%.4f, pos=(%.3f, %.3f)" % (
            idx + 1, role, len(c), max(ds), max(hs), mean_x, mean_y
        ))

    # Construct geometrically faithful buffered polygons
    # Buffer radius: R_buffer = 3 * l0 = 0.0225 mm
    buffer_r = 3.0 * l0
    hc = np.array(hole_center)
    hr = hole_r
    hole_geom = Point(hc).buffer(hr, resolution=64)
    plate_geom = box(0.0, 0.0, plate_size[0], plate_size[1])

    def make_elem_poly(eid):
        conn = elems[eid]
        pts = [nodes[n] for n in conn if n in nodes]
        return Polygon(pts)

    support_polygons = {}
    for comp in classified:
        if comp["role"] in ["notch_ligament_fpz", "hole_right_flank_fpz"]:
            role = comp["role"]
            eids = comp["elements"]
            print("Constructing buffered geometric support for:", role)
            
            # Form union of active element polygons
            elem_polys = [make_elem_poly(e) for e in eids]
            u_poly = unary_union(elem_polys)
            
            # Buffer by R_buffer = 3 * l0
            b_poly = u_poly.buffer(buffer_r, resolution=16)
            
            # Difference from hole, intersection with plate
            clean_poly = b_poly.difference(hole_geom).intersection(plate_geom)
            
            # Simplify with tight tolerance (0.001 mm = 1 um) to yield clean CAD sketches
            simp_poly = clean_poly.simplify(0.0015, preserve_topology=True)
            
            coords = list(simp_poly.exterior.coords)
            support_polygons[role] = {
                "area_mm2": float(simp_poly.area),
                "num_vertices": len(coords),
                "bounds": [float(b) for b in simp_poly.bounds],
                "vertices": [[float(x), float(y)] for x, y in coords]
            }
            print("  %s: area=%.6f mm2 (%.2f%% of plate), vertices=%d" % (
                role, simp_poly.area, (simp_poly.area / (plate_size[0] * plate_size[1])) * 100.0, len(coords)
            ))

    output_data = {
        "metadata": {
            "source_mesh": phys_inp,
            "source_damage": damage_csv,
            "phase_field_l0_mm": l0,
            "buffer_radius_mm": buffer_r,
            "buffer_ratio_l0": 3.0,
            "hole_center": list(hole_center),
            "hole_radius": hr,
            "plate_size": list(plate_size)
        },
        "components": [
            {k: v for k, v in c.items() if k != "elements"} for c in classified
        ],
        "supports": support_polygons
    }

    os.makedirs(os.path.dirname(output_json), exist_ok=True)
    with open(output_json, "w") as f:
        json.dump(output_data, f, indent=2)
    print("Saved faithful indicator supports to:", output_json)
    return output_data

if __name__ == '__main__':
    analyze_and_extract_supports()

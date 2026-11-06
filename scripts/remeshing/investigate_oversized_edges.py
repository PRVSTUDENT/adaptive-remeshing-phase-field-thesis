# -*- coding: utf-8 -*-
"""
scripts/remeshing/investigate_oversized_edges.py
================================================
Investigates elements in the physical mesh with consecutive-node edge lengths
exceeding the nominal target maxElementSize = 0.020 mm (20 um).
Reports element IDs, element types, node coordinates, edge lengths, aspect ratios,
and geometric locations.
"""

import math
import sys
from collections import defaultdict

def investigate_edges(inp_path, threshold_mm=0.020):
    nodes = {}
    elems = {}
    elem_types = {}
    in_nodes, in_elems = False, False
    current_type = None

    with open(inp_path, "r") as f:
        for l in f:
            l = l.strip()
            if not l or l.startswith("**"):
                continue
            if l.startswith("*"):
                in_nodes = l.upper().startswith("*NODE")
                if l.upper().startswith("*ELEMENT"):
                    in_elems = True
                    # Extract type
                    parts = l.upper().split(",")
                    for p in parts:
                        if "TYPE" in p:
                            current_type = p.split("=")[1].strip()
                else:
                    in_elems = False
                continue
            parts = [p.strip() for p in l.split(",") if p.strip()]
            if in_nodes and len(parts) >= 3:
                try:
                    nodes[int(parts[0])] = (float(parts[1]), float(parts[2]))
                except ValueError:
                    continue
            elif in_elems and len(parts) >= 4:
                try:
                    eid = int(parts[0])
                    elems[eid] = [int(p) for p in parts[1:]]
                    elem_types[eid] = current_type
                except ValueError:
                    continue

    print("Loaded %d nodes, %d elements from %s" % (len(nodes), len(elems), inp_path))

    oversized = []
    all_aspect_ratios = []
    
    for eid, conn in elems.items():
        pts = [nodes[n] for n in conn]
        n_pts = len(pts)
        edges = []
        for i in range(n_pts):
            p1 = pts[i]
            p2 = pts[(i + 1) % n_pts]
            edges.append(math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2))
        
        min_e = min(edges)
        max_e = max(edges)
        ar = max_e / min_e if min_e > 0 else float("inf")
        all_aspect_ratios.append(ar)

        if max_e > threshold_mm:
            cx = sum(p[0] for p in pts) / len(pts)
            cy = sum(p[1] for p in pts) / len(pts)
            oversized.append({
                "eid": eid,
                "type": elem_types[eid],
                "conn": conn,
                "pts": pts,
                "centroid": (cx, cy),
                "edges": edges,
                "min_edge_um": min_e * 1e3,
                "max_edge_um": max_e * 1e3,
                "aspect_ratio": ar
            })

    oversized.sort(key=lambda x: x["max_edge_um"], reverse=True)
    print("\nTotal elements with edge > %.4f mm (%.1f um): %d / %d (%.3f%%)" % (
        threshold_mm, threshold_mm * 1e3, len(oversized), len(elems), len(oversized) / float(len(elems)) * 100.0
    ))

    print("\nTop 15 oversized elements:")
    for i, e in enumerate(oversized[:15], 1):
        print("  [%2d] EID %d (%s) Centroid: (%.4f, %.4f) | Max edge: %.4f um | Min edge: %.4f um | AR: %.2f" % (
            i, e["eid"], e["type"], e["centroid"][0], e["centroid"][1],
            e["max_edge_um"], e["min_edge_um"], e["aspect_ratio"]
        ))
        for j, (p1, p2) in enumerate(zip(e["pts"], e["pts"][1:] + [e["pts"][0]])):
            edge_len = math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2) * 1e3
            print("       Edge %d: node %d (%.4f, %.4f) -> node %d (%.4f, %.4f) = %.4f um" % (
                j+1, e["conn"][j], p1[0], p1[1], e["conn"][(j+1)%len(e["conn"])], p2[0], p2[1], edge_len
            ))

    # Spatial distribution of oversized elements
    zones = defaultdict(int)
    for e in oversized:
        cx, cy = e["centroid"]
        if cx >= 0.90:
            zones["right_boundary (x>=0.9)"] += 1
        elif cx <= 0.10:
            zones["left_boundary (x<=0.1)"] += 1
        elif cy >= 0.90:
            zones["top_boundary (y>=0.9)"] += 1
        elif cy <= 0.10:
            zones["bottom_boundary (y<=0.1)"] += 1
        else:
            zones["interior"] += 1

    print("\nSpatial distribution of elements with edge > 20 um:")
    for z, count in sorted(zones.items()):
        print("  %-30s: %d" % (z, count))

    return oversized

if __name__ == "__main__":
    inp = sys.argv[1] if len(sys.argv) > 1 else "models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_METHOD_A_PROD_PHYS.inp"
    investigate_edges(inp)

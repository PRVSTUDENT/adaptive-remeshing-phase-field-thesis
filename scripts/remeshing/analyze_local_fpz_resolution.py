# -*- coding: utf-8 -*-
"""
scripts/remeshing/analyze_local_fpz_resolution.py
=================================================
Calculates detailed local mesh statistics across specific geometric zones:
1. Notch Tip Zone: [0.48, 0.52] x [0.48, 0.52] mm
2. Ligament Zone: Polygon/corridor connecting notch tip (0.50, 0.50) to hole boundary
3. Hole Boundary Zone: Annulus around hole center (0.65, 0.65) with r in [0.095, 0.115] mm
4. Outer Coarse Zone: Elements outside fpz
"""

import math
import sys

def analyze_local_resolution(inp_path):
    nodes = {}
    elems = {}
    in_nodes, in_elems = False, False

    with open(inp_path, "r") as f:
        for l in f:
            l = l.strip()
            if not l or l.startswith("**"):
                continue
            if l.startswith("*"):
                in_nodes = l.upper().startswith("*NODE")
                in_elems = l.upper().startswith("*ELEMENT")
                continue
            parts = [p.strip() for p in l.split(",") if p.strip()]
            if in_nodes and len(parts) >= 3:
                try:
                    nodes[int(parts[0])] = (float(parts[1]), float(parts[2]))
                except ValueError:
                    continue
            elif in_elems and len(parts) >= 4:
                try:
                    elems[int(parts[0])] = [int(p) for p in parts[1:]]
                except ValueError:
                    continue

    print("Loaded %d nodes, %d elements from %s" % (len(nodes), len(elems), inp_path))

    # Zone definitions
    # Hole center and radius
    hx, hy, hr = 0.65, 0.65, 0.10
    l0 = 0.0075  # 7.5 um
    target_h = l0 / 5.0  # 1.5 um

    # Zone classification for each element (by centroid)
    zones = {
        "notch_tip": [],       # Near (0.5, 0.5)
        "ligament": [],        # Between tip and hole
        "hole_boundary": [],   # Along hole perimeter
        "far_field": []        # Remainder
    }

    elem_sizes = {}
    for eid, conn in elems.items():
        pts = [nodes[n] for n in conn]
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        
        # Element characteristic size h = sqrt(Area) or average edge length
        n_pts = len(pts)
        edges = []
        for i in range(n_pts):
            p1 = pts[i]
            p2 = pts[(i + 1) % n_pts]
            edges.append(math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2))
        h_elem = max(edges) # conservative measure: maximum edge length of element
        elem_sizes[eid] = (h_elem, min(edges), edges)

        dist_tip = math.sqrt((cx - 0.50)**2 + (cy - 0.50)**2)
        dist_hole_center = math.sqrt((cx - hx)**2 + (cy - hy)**2)
        dist_hole_surface = abs(dist_hole_center - hr)

        if dist_tip <= 0.025: # Within ~3.3 l0 of tip
            zones["notch_tip"].append(eid)
        elif dist_hole_surface <= 0.015: # Within 2 l0 of hole surface
            zones["hole_boundary"].append(eid)
        elif 0.50 <= cx <= hx and 0.48 <= cy <= (hy + 0.05) and dist_hole_center > hr:
            zones["ligament"].append(eid)
        else:
            zones["far_field"].append(eid)

    # Print statistics per zone
    print("\n=== DETAILED LOCAL RESOLUTION ANALYSIS (l0 = %.4f mm, target h <= %.4f mm = 1.5 um) ===" % (l0, target_h))
    for zname, eids in [("notch_tip", zones["notch_tip"]),
                        ("ligament", zones["ligament"]),
                        ("hole_boundary", zones["hole_boundary"]),
                        ("far_field", zones["far_field"])]:
        if not eids:
            continue
        max_edges = [elem_sizes[eid][0] for eid in eids]
        min_edges = [elem_sizes[eid][1] for eid in eids]
        all_edges = []
        for eid in eids:
            all_edges.extend(elem_sizes[eid][2])
        all_edges.sort()
        n = len(all_edges)

        p01 = all_edges[int(n * 0.01)]
        p10 = all_edges[int(n * 0.10)]
        p50 = all_edges[int(n * 0.50)]
        p90 = all_edges[int(n * 0.90)]
        p95 = all_edges[int(n * 0.95)]
        max_e = all_edges[-1]
        min_e = all_edges[0]

        frac_target = sum(1 for e in all_edges if e <= target_h) / float(n) * 100.0

        print("\n--- ZONE: %s (Elements: %d, Edges: %d) ---" % (zname.upper(), len(eids), n))
        print("  Min edge:        %.4f um" % (min_e * 1e3))
        print("  p01 edge:        %.4f um" % (p01 * 1e3))
        print("  p10 edge:        %.4f um" % (p10 * 1e3))
        print("  Median edge:     %.4f um" % (p50 * 1e3))
        print("  p90 edge:        %.4f um" % (p90 * 1e3))
        print("  p95 edge:        %.4f um" % (p95 * 1e3))
        print("  Max edge:        %.4f um (%.4f mm)" % (max_e * 1e3, max_e))
        print("  Edges <= l0/5 (1.5 um): %.1f%%" % frac_target)
        print("  Resolution: h_p10 / l0 = %.3f, h_median / l0 = %.3f" % (p10 / l0, p50 / l0))

if __name__ == "__main__":
    inp = sys.argv[1] if len(sys.argv) > 1 else "PK_HOLE_METHOD_A_PROD_PHYS.inp"
    analyze_local_resolution(inp)

# -*- coding: utf-8 -*-
import sys
from pathlib import Path

def analyze_mesh(inp_path):
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

    print("Total physical nodes: %d, elements: %d" % (len(nodes), len(elems)))

    edges = []
    for eid, conn in elems.items():
        n_pts = len(conn)
        for i in range(n_pts):
            n1 = conn[i]
            n2 = conn[(i + 1) % n_pts]
            p1 = nodes[n1]
            p2 = nodes[n2]
            d = ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5
            if d > 1e-9:
                edges.append(d)

    edges.sort()
    n_edges = len(edges)
    min_edge = edges[0]
    p01_edge = edges[int(n_edges * 0.01)]
    p05_edge = edges[int(n_edges * 0.05)]
    med_edge = edges[int(n_edges * 0.50)]
    max_edge = edges[-1]

    print("Total valid element edges: %d" % n_edges)
    print("Min edge length: %.4f um (h_min parameter: 1.0 um, l0: 7.5 um)" % (min_edge * 1e3))
    print("p01 edge length: %.4f um" % (p01_edge * 1e3))
    print("p05 edge length: %.4f um" % (p05_edge * 1e3))
    print("Median edge length: %.4f um" % (med_edge * 1e3))
    print("Max edge length: %.4f mm (h_max parameter: 0.02 mm)" % max_edge)
    print("Crack tip resolution: h_p01 / l0 = %.3f" % (p01_edge / 0.0075))

    # Spatial zones
    notch_elems = sum(1 for eid, conn in elems.items() if any(0.45 <= nodes[n][0] <= 0.55 and 0.45 <= nodes[n][1] <= 0.55 for n in conn))
    hole_elems = sum(1 for eid, conn in elems.items() if any(0.08 <= ((nodes[n][0] - 0.65) ** 2 + (nodes[n][1] - 0.65) ** 2) ** 0.5 <= 0.12 for n in conn))
    print("Elements in notch tip zone [0.45, 0.55]x[0.45, 0.55]: %d" % notch_elems)
    print("Elements in hole boundary zone (r in [0.08, 0.12]): %d" % hole_elems)

if __name__ == "__main__":
    inp = sys.argv[1] if len(sys.argv) > 1 else "PK_HOLE_METHOD_A_PROD_PHYS.inp"
    analyze_mesh(inp)

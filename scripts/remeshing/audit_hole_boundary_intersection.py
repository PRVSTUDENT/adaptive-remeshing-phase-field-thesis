# -*- coding: utf-8 -*-
"""
scripts/remeshing/audit_hole_boundary_intersection.py
Audits exact geometric intersection and proximity of the d >= 0.95 primary crack
to the circular hole boundary (center 0.65, 0.65, radius 0.10 mm).
"""

import csv
import json
import math

inp = "models/pandey_kumar_mode1/224_f1734_case2_distal_refinement/PK_F1728_CASE_2_ADAPT_PHYS.inp"
sdv_csv = "results/validation/f1735_case2_final_frame_sdv.csv"

nodes = {}
elements = {}
with open(inp) as f:
    r_n, r_e = False, False
    for line in f:
        l = line.strip().upper()
        if not l or l.startswith("**"):
            continue
        if l.startswith("*NODE"):
            r_n, r_e = True, False
            continue
        elif l.startswith("*ELEMENT") and not l.startswith("*ELEMENT OUTPUT"):
            r_n, r_e = False, True
            continue
        elif l.startswith("*"):
            r_n, r_e = False, False
            continue
        p = [x.strip() for x in line.strip().split(",")]
        if r_n:
            try:
                nodes[int(p[0])] = (float(p[1]), float(p[2]))
            except:
                pass
        elif r_e:
            try:
                elements[int(p[0])] = [int(x) for x in p[1:]]
            except:
                pass

sdv = {int(r[0]): float(r[1]) for r in csv.reader(open(sdv_csv)) if r[0] != "physical_element_id"}
centroids = {eid: (sum(nodes[n][0] for n in c) / len(c), sum(nodes[n][1] for n in c) / len(c)) for eid, c in elements.items()}

# Primary left crack elements: centroids x <= 0.65 and d >= 0.95
left_lig = [eid for eid, d in sdv.items() if d >= 0.95 and centroids[eid][0] <= 0.65]

hole_c = (0.65, 0.65)
R = 0.10

# 1. Centroid min distance to hole boundary
centroid_dists = [abs(math.sqrt((centroids[eid][0] - hole_c[0])**2 + (centroids[eid][1] - hole_c[1])**2) - R) for eid in left_lig]
min_centroid_dist = min(centroid_dists)

# 2. Node min distance to hole boundary for elements in left_lig
min_node_dist = 1e9
closest_node = None
closest_elem = None
nodes_on_hole = []

for eid in left_lig:
    for nid in elements[eid]:
        pt = nodes[nid]
        r = math.sqrt((pt[0] - hole_c[0])**2 + (pt[1] - hole_c[1])**2)
        dist = abs(r - R)
        if dist < 1e-5:  # within 0.01 um of boundary (on boundary)
            if nid not in nodes_on_hole:
                nodes_on_hole.append(nid)
        if dist < min_node_dist:
            min_node_dist = dist
            closest_node = nid
            closest_elem = eid

print("Left ligament d >= 0.95 count: %d" % len(left_lig))
print("Minimum centroid distance to hole boundary: %.4e mm (%.3f um)" % (min_centroid_dist, min_centroid_dist * 1000))
print("Minimum node distance to hole boundary: %.4e mm (%.3f um)" % (min_node_dist, min_node_dist * 1000))
print("Closest node: %d at (%.6f, %.6f)" % (closest_node, nodes[closest_node][0], nodes[closest_node][1]))
print("Number of d >= 0.95 elements sharing a node strictly ON the hole boundary: %d" % len(nodes_on_hole))

# Check element connectivity to hole:
elements_with_node_on_hole = [eid for eid in left_lig if any(nid in nodes_on_hole for nid in elements[eid])]
print("Elements with d >= 0.95 containing a node on hole boundary: %d" % len(elements_with_node_on_hole))
for eid in elements_with_node_on_hole[:10]:
    print("  Elem %d: d = %.4f, nodes = %s" % (eid, sdv[eid], str(elements[eid])))

results = {
    "left_ligament_d_ge_095_count": len(left_lig),
    "min_centroid_dist_mm": min_centroid_dist,
    "min_centroid_dist_um": min_centroid_dist * 1000,
    "min_node_dist_mm": min_node_dist,
    "min_node_dist_um": min_node_dist * 1000,
    "closest_node_id": closest_node,
    "closest_node_coords": list(nodes[closest_node]),
    "nodes_on_hole_boundary_count": len(nodes_on_hole),
    "elements_with_node_on_hole_count": len(elements_with_node_on_hole),
    "elements_with_node_on_hole_ids": elements_with_node_on_hole,
    "geometric_intersection_established": (len(elements_with_node_on_hole) > 0 or min_node_dist < 1e-4)
}

with open("results/validation/f1735_case2_hole_intersection_audit.json", "w") as f:
    json.dump(results, f, indent=2)
print("Saved audit to results/validation/f1735_case2_hole_intersection_audit.json")

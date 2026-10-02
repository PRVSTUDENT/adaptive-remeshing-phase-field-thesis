#!/usr/bin/env python3
"""
Inspect coordinates of high damage elements in PK10R3.
"""

import os

inp_path = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R3_REFINED_TIP/M2CORR_PK10R3_REFINED_TIP.inp"
if not os.path.exists(inp_path):
    inp_path = "D:/Master thesis/Adaptive remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R3_REFINED_TIP/M2CORR_PK10R3_REFINED_TIP.inp"

nodes = {}
elems = {}

with open(inp_path, 'r') as f:
    reading_nodes = False
    reading_elems = False
    
    for line in f:
        line_s = line.strip()
        if "*NODE" in line_s.upper() and "*OUTPUT" not in line_s.upper():
            reading_nodes = True
            reading_elems = False
            continue
        elif "*ELEMENT" in line_s.upper():
            reading_nodes = False
            reading_elems = True
            continue
        elif line_s.startswith("*"):
            reading_nodes = False
            reading_elems = False
            continue
            
        if reading_nodes:
            parts = line_s.split(",")
            if len(parts) >= 3:
                try:
                    nid = int(parts[0])
                    x = float(parts[1])
                    y = float(parts[2])
                    nodes[nid] = (x, y)
                except ValueError:
                    pass
        elif reading_elems:
            parts = line_s.split(",")
            if len(parts) >= 5:
                try:
                    eid = int(parts[0])
                    n1, n2, n3, n4 = int(parts[1]), int(parts[2]), int(parts[3]), int(parts[4])
                    elems[eid] = (n1, n2, n3, n4)
                except ValueError:
                    pass

print("Parsed %d nodes and %d elements." % (len(nodes), len(elems)))

for target_elem in [8331, 8617, 26063, 26349]:
    eid = target_elem
    if eid > 17732:
        eid = target_elem - 17732
    if eid in elems:
        n_list = elems[eid]
        coords = [nodes[n] for n in n_list if n in nodes]
        xc = sum([c[0] for c in coords]) / float(len(coords))
        yc = sum([c[1] for c in coords]) / float(len(coords))
        print("Element %d (Physical Quad %d): Centroid = (%.6f, %.6f) mm, Nodes = %s" % (
            target_elem, eid, xc, yc, str(n_list)))

#!/usr/bin/env python3
"""
Inspect exact coordinates and SDVs of elements in PK10R2 and PK10R3.
"""

import os

def check_elem_coords(inp_path, elem_ids, n_phys):
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
                        nodes[int(parts[0])] = (float(parts[1]), float(parts[2]))
                    except: pass
            elif reading_elems:
                parts = line_s.split(",")
                if len(parts) >= 5:
                    try:
                        elems[int(parts[0])] = [int(parts[i]) for i in range(1, 5)]
                    except: pass
                    
    print("Mesh %s: %d nodes, %d elements" % (inp_path, len(nodes), len(elems)))
    for eid in elem_ids:
        phys_id = eid if eid <= n_phys else (eid - n_phys if eid <= 2*n_phys else eid - 2*n_phys)
        if phys_id in elems:
            conn = elems[phys_id]
            coords = [nodes[n] for n in conn if n in nodes]
            cx = sum([c[0] for c in coords]) / float(len(coords))
            cy = sum([c[1] for c in coords]) / float(len(coords))
            print("  Elem %5d (PhysQuad %5d): Centroid = (%9.6f, %9.6f) mm | Nodes = %s" % (
                eid, phys_id, cx, cy, str(conn)))

if __name__ == "__main__":
    p_r2 = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R2_TOPOLOGY_CORRECTED/M2CORR_PK10R2_TOPOLOGY_CORRECTED.inp"
    p_r3 = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R3_REFINED_TIP/M2CORR_PK10R3_REFINED_TIP.inp"
    
    print("--- PK10R2 (N_PHYS = 6048) ---")
    check_elem_coords(p_r2, [8973, 8847, 6049, 6050, 6051, 6052], 6048)
    
    print("\n--- PK10R3 (N_PHYS = 17732) ---")
    check_elem_coords(p_r3, [26349, 26063, 17733, 17734, 17735, 17736], 17732)

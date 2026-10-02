#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Builds reference-identical 3-layer production UEL input decks for Mode-I adapted meshes:
- Layer 1: Phase-field User Elements (U1 for quads, U3 for tris) -> IDs 1..N_phys
- Layer 2: Displacement User Elements (U2 for quads, U4 for tris) -> IDs (N_phys+1)..2*N_phys
- Layer 3: Companion UMAT CPE4/CPE3 Elements -> IDs (2*N_phys+1)..3*N_phys
- Rigid top tensile pull tied to RP (999999) via *EQUATION
- Wrapped NSET cards (max 16 entries per line) to satisfy Abaqus keyword parser rules
- Step 1: Pre-peak linear loading to u = 0.0050 mm (time=1.0, dt_init=0.02, dt_max=0.02)
- Step 2: Fracture propagation to u = 0.0100 mm (time=1.0, dt_init=0.002, dt_max=0.002)
"""

from __future__ import print_function
import os
import sys
import json
import hashlib

def write_wrapped_nset(f, nset_name, node_list, max_per_line=16):
    f.write("*NSET, NSET=%s\n" % nset_name)
    sorted_nodes = sorted(node_list)
    for i in range(0, len(sorted_nodes), max_per_line):
        chunk = sorted_nodes[i:i + max_per_line]
        f.write(", ".join(str(n) for n in chunk) + "\n")

def convert_raw_to_production_uel_deck(src_raw_inp, dst_uel_inp, job_name="PK_M1_JOB2_ADAPTED"):
    nodes = {}
    quad_elems = {}
    tri_elems = {}
    
    in_nodes = False
    in_elements = False
    elem_type = None

    with open(src_raw_inp, 'r') as f:
        for line in f:
            l = line.strip()
            if not l or l.startswith('**'):
                continue
            if l.startswith('*'):
                in_nodes = False
                in_elements = False
                upper = l.upper()
                if upper.startswith('*NODE'):
                    in_nodes = True
                elif upper.startswith('*ELEMENT'):
                    in_elements = True
                    if 'CPS4' in upper or 'CPE4' in upper or 'QUAD' in upper:
                        elem_type = 'QUAD'
                    elif 'CPS3' in upper or 'CPE3' in upper or 'TRI' in upper:
                        elem_type = 'TRI'
                    else:
                        elem_type = 'QUAD'
                continue

            if in_nodes:
                parts = [p.strip() for p in l.split(',') if p.strip()]
                if len(parts) >= 3:
                    try:
                        nid = int(parts[0])
                        x = float(parts[1])
                        y = float(parts[2])
                        nodes[nid] = (x, y)
                    except ValueError:
                        continue

            if in_elements:
                parts = [p.strip() for p in l.split(',') if p.strip()]
                if len(parts) >= 4:
                    try:
                        int_parts = [int(p) for p in parts]
                        eid = int_parts[0]
                        conn = int_parts[1:]
                        if elem_type == 'QUAD' or len(conn) == 4:
                            quad_elems[eid] = tuple(conn[:4])
                        else:
                            tri_elems[eid] = tuple(conn[:3])
                    except ValueError:
                        continue

    num_phys_nodes = len(nodes)
    num_phys_quads = len(quad_elems)
    num_phys_tris = len(tri_elems)
    num_phys_elems = num_phys_quads + num_phys_tris

    # Find boundary nodes (tolerance 1e-4 mm for 1.0 mm x 1.0 mm plate)
    bottom_nodes = [nid for nid, (x, y) in nodes.items() if abs(y - 0.0) < 1e-4]
    top_nodes = [nid for nid, (x, y) in nodes.items() if abs(y - 1.0) < 1e-4]
    pin_candidates = [nid for nid in bottom_nodes if abs(nodes[nid][0] - 0.0) < 1e-4]
    pin_node = min(pin_candidates) if pin_candidates else bottom_nodes[0]
    rp_nid = 999999

    with open(dst_uel_inp, 'w') as f:
        f.write("*HEADING\n")
        f.write("%s - Mode-I Adapted Refined PFM Solve\n" % job_name)
        f.write("** Finite Elements: %d (%d quads, %d tris), Nodes: %d\n" % (num_phys_elems, num_phys_quads, num_phys_tris, num_phys_nodes))
        f.write("** Parameters: E=210 GPa, nu=0.3, l0=0.0075 mm, Gc=0.0027 kN/mm, eta=1e-7\n")
        f.write("** ----------------------------------------------------------\n")
        
        # User Element Interfaces
        f.write("*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n3\n")
        f.write("*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n1, 2\n")
        if num_phys_tris > 0:
            f.write("*USER ELEMENT, TYPE=U3, NODES=3, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n3\n")
            f.write("*USER ELEMENT, TYPE=U4, NODES=3, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n1, 2\n")
        
        # Physical Nodes
        f.write("*NODE\n")
        for nid in sorted(nodes.keys()):
            x, y = nodes[nid]
            f.write("%d, %.12g, %.12g\n" % (nid, x, y))
        # Reference point node for top pull
        f.write("%d, 0.5, 1.0\n" % rp_nid)

        # Layer 1: Phase-field user elements (U1 for quads, U3 for tris) -> IDs 1..N_phys
        if quad_elems:
            f.write("*ELEMENT, TYPE=U1, ELSET=PHASE_QUAD\n")
            for eid in sorted(quad_elems.keys()):
                c = quad_elems[eid]
                f.write("%d, %s\n" % (eid, ", ".join(str(n) for n in c)))
        if tri_elems:
            f.write("*ELEMENT, TYPE=U3, ELSET=PHASE_TRI\n")
            for eid in sorted(tri_elems.keys()):
                c = tri_elems[eid]
                f.write("%d, %s\n" % (eid, ", ".join(str(n) for n in c)))

        # Layer 2: Displacement user elements (U2 for quads, U4 for tris) -> IDs (N_phys+1)..2*N_phys
        offset_disp = num_phys_elems
        if quad_elems:
            f.write("*ELEMENT, TYPE=U2, ELSET=DISP_QUAD\n")
            for eid in sorted(quad_elems.keys()):
                c = quad_elems[eid]
                f.write("%d, %s\n" % (eid + offset_disp, ", ".join(str(n) for n in c)))
        if tri_elems:
            f.write("*ELEMENT, TYPE=U4, ELSET=DISP_TRI\n")
            for eid in sorted(tri_elems.keys()):
                c = tri_elems[eid]
                f.write("%d, %s\n" % (eid + offset_disp, ", ".join(str(n) for n in c)))

        # Layer 3: Companion UMAT elements for visualization & error evaluation -> IDs (2*N_phys+1)..3*N_phys
        offset_umat = 2 * num_phys_elems
        if quad_elems:
            f.write("*ELEMENT, TYPE=CPE4, ELSET=UMAT_QUADS\n")
            for eid in sorted(quad_elems.keys()):
                c = quad_elems[eid]
                f.write("%d, %s\n" % (eid + offset_umat, ", ".join(str(n) for n in c)))
        if tri_elems:
            f.write("*ELEMENT, TYPE=CPE3, ELSET=UMAT_TRIS\n")
            for eid in sorted(tri_elems.keys()):
                c = tri_elems[eid]
                f.write("%d, %s\n" % (eid + offset_umat, ", ".join(str(n) for n in c)))

        # Element sets
        f.write("*ELSET, ELSET=All_elem\nUMAT_QUADS\n")
        if tri_elems:
            f.write("UMAT_TRIS\n")
        f.write("*ELSET, ELSET=umatelem\nAll_elem\n")

        # Node sets (wrapped for Abaqus keyword parser safety)
        write_wrapped_nset(f, "N_BOTTOM", bottom_nodes)
        write_wrapped_nset(f, "N_PIN", [pin_node])
        write_wrapped_nset(f, "N_TOP", top_nodes)
        write_wrapped_nset(f, "N_RP", [rp_nid])

        # UEL Properties: l0, Gc, E, nu, eta, N_PHYS
        f.write("*UEL PROPERTY, ELSET=PHASE_QUAD\n0.0075, 0.0027, 210.0, 0.3, 1.0e-7, %d.\n" % num_phys_elems)
        f.write("*UEL PROPERTY, ELSET=DISP_QUAD\n0.0075, 0.0027, 210.0, 0.3, 1.0e-7, %d.\n" % num_phys_elems)
        if tri_elems:
            f.write("*UEL PROPERTY, ELSET=PHASE_TRI\n0.0075, 0.0027, 210.0, 0.3, 1.0e-7, %d.\n" % num_phys_elems)
            f.write("*UEL PROPERTY, ELSET=DISP_TRI\n0.0075, 0.0027, 210.0, 0.3, 1.0e-7, %d.\n" % num_phys_elems)

        # Companion UMAT section
        f.write("*SOLID SECTION, ELSET=All_elem, MATERIAL=DUMMY_MAT\n1.0\n")
        f.write("*MATERIAL, NAME=DUMMY_MAT\n*USER MATERIAL, CONSTANTS=2\n210.0, 0.3\n")
        f.write("*DEPVAR\n16\n")

        # Equations tying top nodes to RP
        f.write("** EQUATIONS (Rigid top tensile pull tied to RP)\n")
        for tn in sorted(top_nodes):
            f.write("*EQUATION\n2\n%d, 2, 1.0, %d, 2, -1.0\n" % (tn, rp_nid))

        # Step 1: Pre-peak linear loading to u = 0.005 mm (50 increments of 0.0001 mm)
        f.write("** ----------------------------------------------------------\n")
        f.write("** STEP 1: Linear Loading to u = 0.005 mm\n")
        f.write("** ----------------------------------------------------------\n")
        f.write("*STEP, NAME=Step-1, NLGEOM=NO, INC=10000\n")
        f.write("*STATIC\n")
        f.write("0.02, 1.0, 1.0e-7, 0.02\n")
        f.write("*BOUNDARY\n")
        f.write("N_BOTTOM, 2, 2, 0.0\n")
        f.write("N_PIN, 1, 1, 0.0\n")
        f.write("N_TOP, 1, 1, 0.0\n")
        f.write("N_RP, 2, 2, 0.0050\n")
        f.write("*RESTART, WRITE, FREQUENCY=0\n")
        f.write("*OUTPUT, FIELD, FREQUENCY=1\n")
        f.write("*NODE OUTPUT, NSET=N_RP\nU, RF\n")
        f.write("*ELEMENT OUTPUT, ELSET=DISP_QUAD\nSDV\n")
        f.write("*ELEMENT OUTPUT, ELSET=All_elem\nS, MISESERI\n")
        f.write("*NODE PRINT, FREQ=1, NSET=N_RP\nU2, RF2\n")
        f.write("*END STEP\n")

        # Step 2: Fine fracture propagation to u = 0.010 mm (500 increments of 0.00001 mm)
        f.write("** ----------------------------------------------------------\n")
        f.write("** STEP 2: Fracture Propagation to u = 0.010 mm\n")
        f.write("** ----------------------------------------------------------\n")
        f.write("*STEP, NAME=Step-2, NLGEOM=NO, INC=20000\n")
        f.write("*STATIC\n")
        f.write("0.002, 1.0, 1.0e-8, 0.002\n")
        f.write("*BOUNDARY\n")
        f.write("N_RP, 2, 2, 0.0100\n")
        f.write("*RESTART, WRITE, FREQUENCY=0\n")
        f.write("*OUTPUT, FIELD, FREQUENCY=1\n")
        f.write("*NODE OUTPUT, NSET=N_RP\nU, RF\n")
        f.write("*ELEMENT OUTPUT, ELSET=DISP_QUAD\nSDV\n")
        f.write("*ELEMENT OUTPUT, ELSET=All_elem\nS, MISESERI\n")
        f.write("*NODE PRINT, FREQ=1, NSET=N_RP\nU2, RF2\n")
        f.write("*END STEP\n")

    print("Successfully built production UEL deck: %s" % dst_uel_inp)
    print("  Physical Nodes: %d (Bottom: %d, Top: %d, Pin: %d)" % (num_phys_nodes, len(bottom_nodes), len(top_nodes), pin_node))
    print("  Physical Elements: %d (%d quads, %d tris)" % (num_phys_elems, num_phys_quads, num_phys_tris))
    print("  Total Layered Elements: %d" % (3 * num_phys_elems))
    return {
        "num_nodes": num_phys_nodes,
        "num_quads": num_phys_quads,
        "num_tris": num_phys_tris,
        "num_elems": num_phys_elems,
        "total_layered_elems": 3 * num_phys_elems,
        "dst_path": dst_uel_inp
    }

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python build_adapted_job2_production_deck.py <src_raw_inp> <dst_uel_inp> [job_name]")
        sys.exit(1)
    src = sys.argv[1]
    dst = sys.argv[2]
    jn = sys.argv[3] if len(sys.argv) >= 4 else "PK_M1_JOB2_ADAPTED"
    convert_raw_to_production_uel_deck(src, dst, jn)

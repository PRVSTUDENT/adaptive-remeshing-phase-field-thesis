#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Reconstructs reference-identical 3-layer production UEL input deck for Mode-I Spatial Fine candidate:
- Layer 1: Phase-field User Elements (U1 quads, U3 tris) -> IDs 1..N_base
- Layer 2: Displacement User Elements (U2 quads, U4 tris) -> IDs (N_base+1)..2*N_base
- Layer 3: Companion UMAT CPE4/CPE3 Elements -> IDs (2*N_base+1)..3*N_base
- Property card: PROPS(6) = float(N_base)
- Rigid top tensile pull tied to RP (999999) via *EQUATION
- Wrapped NSET cards (max 16 entries per line) to satisfy Abaqus keyword parser rules
- Step 1: Pre-peak linear loading to u = 0.0050 mm (dt=5e-4, INC=2500)
- Step 2: Fracture propagation to u = 0.0100 mm (dt=2e-4, dt_min=1e-9, INC=6000, Controls: 4,10,9,20,10,4,0,10)
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

def write_wrapped_elset(f, elset_name, elem_list, max_per_line=16):
    f.write("*ELSET, ELSET=%s\n" % elset_name)
    sorted_elems = sorted(elem_list)
    for i in range(0, len(sorted_elems), max_per_line):
        chunk = sorted_elems[i:i + max_per_line]
        f.write(", ".join(str(e) for e in chunk) + "\n")

def build_production_deck(src_raw_inp, dst_deck_path, job_heading="PK_MODE1_STAGE14_ADAPT_SPATIAL_FINE_FRACTURE"):
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
                    if 'CPE4' in upper or 'CPS4' in upper or 'QUAD' in upper:
                        elem_type = 'QUAD'
                    elif 'CPE3' in upper or 'CPS3' in upper or 'TRI' in upper:
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

    print("Parsed Raw Mesh:")
    print("  Nodes: %d" % num_phys_nodes)
    print("  Quads: %d, Tris: %d, Total Base Elements: %d" % (num_phys_quads, num_phys_tris, num_phys_elems))

    # Boundary nodes (1.0 mm x 1.0 mm plate)
    bottom_nodes = [nid for nid, (x, y) in nodes.items() if abs(y - 0.0) < 1e-4]
    top_nodes = [nid for nid, (x, y) in nodes.items() if abs(y - 1.0) < 1e-4]
    pin_candidates = [nid for nid in bottom_nodes if abs(nodes[nid][0] - 0.0) < 1e-4]
    pin_node = min(pin_candidates) if pin_candidates else bottom_nodes[0]
    rp_nid = 999999

    # Build 3-Layer Deck
    with open(dst_deck_path, 'w') as f:
        f.write("*HEADING\n")
        f.write("%s - 3-Layer UEL Spatial Fine Fracture Solve\n" % job_heading)
        f.write("** Finite Elements: %d (%d quads, %d tris), Nodes: %d\n" % (num_phys_elems, num_phys_quads, num_phys_tris, num_phys_nodes))
        f.write("** Parameters: E=210 GPa, nu=0.3, l0=0.0075 mm, Gc=0.0027 kN/mm, eta=1e-7\n")
        f.write("** Stage 14U-AM: minElementSize=0.0005 mm (0.5 um resolution floor)\n")
        f.write("** ----------------------------------------------------------\n")
        
        # User Element Declarations
        f.write("*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n3\n")
        f.write("*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n1, 2\n")
        if num_phys_tris > 0:
            f.write("*USER ELEMENT, TYPE=U3, NODES=3, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n3\n")
            f.write("*USER ELEMENT, TYPE=U4, NODES=3, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n1, 2\n")
        
        # Nodes
        f.write("*NODE\n")
        for nid in sorted(nodes.keys()):
            x, y = nodes[nid]
            f.write("%d, %.10f, %.10f\n" % (nid, x, y))
        f.write("%d, 0.5000000000, 1.0000000000\n" % rp_nid)

        # Layer 1: Phase-field UEL (U1 for quads, U3 for tris) -> IDs 1..N_base
        phase_elem_ids = []
        if quad_elems:
            f.write("*ELEMENT, TYPE=U1, ELSET=PHASE_QUAD\n")
            for eid in sorted(quad_elems.keys()):
                c = quad_elems[eid]
                f.write("%d, %s\n" % (eid, ", ".join(str(n) for n in c)))
                phase_elem_ids.append(eid)
        if tri_elems:
            f.write("*ELEMENT, TYPE=U3, ELSET=PHASE_TRI\n")
            for eid in sorted(tri_elems.keys()):
                c = tri_elems[eid]
                f.write("%d, %s\n" % (eid, ", ".join(str(n) for n in c)))
                phase_elem_ids.append(eid)

        # Layer 2: Displacement UEL (U2 for quads, U4 for tris) -> IDs (N_base+1)..2*N_base
        offset_disp = num_phys_elems
        mech_elem_ids = []
        if quad_elems:
            f.write("*ELEMENT, TYPE=U2, ELSET=MECH_QUAD\n")
            for eid in sorted(quad_elems.keys()):
                c = quad_elems[eid]
                f.write("%d, %s\n" % (eid + offset_disp, ", ".join(str(n) for n in c)))
                mech_elem_ids.append(eid + offset_disp)
        if tri_elems:
            f.write("*ELEMENT, TYPE=U4, ELSET=MECH_TRI\n")
            for eid in sorted(tri_elems.keys()):
                c = tri_elems[eid]
                f.write("%d, %s\n" % (eid + offset_disp, ", ".join(str(n) for n in c)))
                mech_elem_ids.append(eid + offset_disp)

        # Layer 3: Companion UMAT (CPE4 for quads, CPE3 for tris) -> IDs (2*N_base+1)..3*N_base
        offset_umat = 2 * num_phys_elems
        umat_elem_ids = []
        if quad_elems:
            f.write("*ELEMENT, TYPE=CPE4, ELSET=UMAT_QUADS\n")
            for eid in sorted(quad_elems.keys()):
                c = quad_elems[eid]
                f.write("%d, %s\n" % (eid + offset_umat, ", ".join(str(n) for n in c)))
                umat_elem_ids.append(eid + offset_umat)
        if tri_elems:
            f.write("*ELEMENT, TYPE=CPE3, ELSET=UMAT_TRIS\n")
            for eid in sorted(tri_elems.keys()):
                c = tri_elems[eid]
                f.write("%d, %s\n" % (eid + offset_umat, ", ".join(str(n) for n in c)))
                umat_elem_ids.append(eid + offset_umat)

        # Composite Element Sets
        write_wrapped_elset(f, "PHASE_ELEM", phase_elem_ids)
        write_wrapped_elset(f, "MECH_ELEM", mech_elem_ids)
        write_wrapped_elset(f, "UMATELEM", umat_elem_ids)
        
        f.write("*ELSET, ELSET=All_elem\n")
        f.write("UMATELEM\n")

        # Node Sets
        write_wrapped_nset(f, "N_BOTTOM", bottom_nodes)
        write_wrapped_nset(f, "N_PIN", [pin_node])
        write_wrapped_nset(f, "N_TOP", top_nodes)
        write_wrapped_nset(f, "N_RP", [rp_nid])

        # UEL Property Cards: PROPS(6) = float(N_base)
        f.write("*UEL PROPERTY, ELSET=PHASE_ELEM\n")
        f.write("0.0075, 0.0027, 210.0, 0.3, 1.0e-7, %d.0\n" % num_phys_elems)
        f.write("*UEL PROPERTY, ELSET=MECH_ELEM\n")
        f.write("0.0075, 0.0027, 210.0, 0.3, 1.0e-7, %d.0\n" % num_phys_elems)

        # Solid Section & Material for Layer 3 Companion UMAT
        f.write("*SOLID SECTION, ELSET=UMATELEM, MATERIAL=UMAT_MAT\n1.0,\n")
        f.write("*MATERIAL, NAME=UMAT_MAT\n")
        f.write("*USER MATERIAL, CONSTANTS=2\n")
        f.write("210000.0, 0.3\n")
        f.write("*DEPVAR\n16\n")

        # Equations: Rigid top tensile pull tied to RP
        f.write("** EQUATIONS (Rigid top tensile pull tied to RP)\n")
        for tn in sorted(top_nodes):
            f.write("*EQUATION\n2\n%d, 2, 1.0, %d, 2, -1.0\n" % (tn, rp_nid))

        # Step 1: Pre-peak linear loading to u = 0.0050 mm
        f.write("** ----------------------------------------------------------\n")
        f.write("** STEP 1: Linear Loading to u = 0.005 mm\n")
        f.write("** ----------------------------------------------------------\n")
        f.write("*STEP, NAME=Step-1, NLGEOM=NO, INC=2500\n")
        f.write("*STATIC\n")
        f.write("5.0E-4, 1.0, 1.0E-9, 5.0E-4\n")
        f.write("*BOUNDARY\n")
        f.write("N_BOTTOM, 2, 2, 0.0\n")
        f.write("N_PIN, 1, 1, 0.0\n")
        f.write("N_TOP, 1, 1, 0.0\n")
        f.write("N_RP, 2, 2, 0.0050\n")
        f.write("*OUTPUT, FIELD, FREQUENCY=1\n")
        f.write("*NODE OUTPUT, NSET=N_RP\nU, RF\n")
        f.write("*ELEMENT OUTPUT, ELSET=All_elem\nS, MISESERI\n")
        f.write("*NODE PRINT, FREQ=1, NSET=N_RP\nU2, RF2\n")
        f.write("*END STEP\n")

        # Step 2: Fracture propagation to u = 0.0100 mm with Stage-14U solver controls
        f.write("** ----------------------------------------------------------\n")
        f.write("** STEP 2: Fracture Propagation to u = 0.010 mm\n")
        f.write("** ----------------------------------------------------------\n")
        f.write("*STEP, NAME=Step-2, NLGEOM=NO, INC=6000\n")
        f.write("*STATIC\n")
        f.write("2.0E-4, 1.0, 1.0E-9, 2.0E-4\n")
        f.write("*CONTROLS, PARAMETERS=TIME INCREMENTATION\n")
        f.write("4, 10, 9, 20, 10, 4, 0, 10\n")
        f.write("*BOUNDARY\n")
        f.write("N_RP, 2, 2, 0.0100\n")
        f.write("*RESTART, WRITE, FREQUENCY=0\n")
        f.write("*OUTPUT, FIELD, FREQUENCY=1\n")
        f.write("*NODE OUTPUT, NSET=N_RP\nU, RF\n")
        f.write("*ELEMENT OUTPUT, ELSET=All_elem\nS, MISESERI\n")
        f.write("*NODE PRINT, FREQ=1, NSET=N_RP\nU2, RF2\n")
        f.write("*END STEP\n")

    print("Successfully generated 3-layer production deck: %s" % dst_deck_path)
    return {
        'num_phys_nodes': num_phys_nodes,
        'num_phys_quads': num_phys_quads,
        'num_phys_tris': num_phys_tris,
        'num_phys_elems': num_phys_elems,
        'total_3layer_elements': 3 * num_phys_elems,
        'top_nodes_count': len(top_nodes),
        'bottom_nodes_count': len(bottom_nodes)
    }

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python build_stage14uam_spatial_fine_deck.py <raw_inp> <dst_inp>")
        sys.exit(1)
    raw_inp = sys.argv[1]
    dst_inp = sys.argv[2]
    build_production_deck(raw_inp, dst_inp)

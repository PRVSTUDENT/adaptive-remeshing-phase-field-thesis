#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Build Corrected Isolated Production Decks for 2.0% and 5.0% Task-5 PFM Solves.
Ensures 100% schedule parity with the reference workflow:
- Step 1: 5.0E-4, 1.0, 1.0E-9, 5.0E-4 (2,000 increments to u=0.0050 mm)
- Step 2: 2.0E-4, 1.0, 1.0E-14, 2.0E-4 (5,000 increments to u=0.0100 mm)
- 10-item line-wrapped NSET definitions to avoid Abaqus parser truncation.
"""

from __future__ import print_function
import os
import sys
import hashlib

def compute_sha256(filepath):
    if not os.path.exists(filepath):
        return ""
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def build_corrected_deck(phys_inp_path, target_inp_path, error_target_str):
    print("Reading physical mesh from:", phys_inp_path)
    nodes = {}
    quad_elems = {}
    tri_elems = {}

    in_nodes = False
    in_elements = False
    elem_type = None

    with open(phys_inp_path, 'r') as f:
        for line in f:
            l = line.strip()
            if not l or l.startswith('**'):
                continue
            if l.startswith('*'):
                in_nodes = False
                in_elements = False
                if l.upper().startswith('*NODE'):
                    in_nodes = True
                elif l.upper().startswith('*ELEMENT'):
                    in_elements = True
                    if 'CPS4' in l.upper() or 'CPE4' in l.upper() or 'QUAD' in l.upper():
                        elem_type = 'QUAD'
                    elif 'CPS3' in l.upper() or 'CPE3' in l.upper() or 'TRI' in l.upper():
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

    print("Mesh (%s): %d nodes, %d elements (%d quads, %d tris)" %
          (error_target_str, num_phys_nodes, num_phys_elems, num_phys_quads, num_phys_tris))

    # Identify boundary nodes
    bottom_nodes = [nid for nid, (x, y) in nodes.items() if abs(y - 0.0) < 1e-4]
    top_nodes = [nid for nid, (x, y) in nodes.items() if abs(y - 1.0) < 1e-4]
    pin_candidates = [nid for nid in bottom_nodes if abs(nodes[nid][0] - 0.0) < 1e-4]
    pin_node = min(pin_candidates) if pin_candidates else bottom_nodes[0]
    rp_nid = 999999

    print("Boundary Nodes: Bottom=%d, Top=%d, Pin Node=%d, RP Node=%d" %
          (len(bottom_nodes), len(top_nodes), pin_node, rp_nid))

    with open(target_inp_path, 'w') as f:
        f.write("*HEADING\n")
        f.write("Pandey & Kumar (2025) Mode-I %s Corrected Adaptive Refined PFM Solve (Sharp Slit)\n" % error_target_str)
        f.write("** Physical Elements: %d (%d quads, %d tris), Nodes: %d\n" %
                (num_phys_elems, num_phys_quads, num_phys_tris, num_phys_nodes))
        f.write("** Parameters: E=210.0 kN/mm^2, nu=0.3, l0=0.0075 mm, Gc=0.0027 kN/mm, k=1.0e-7\n")
        f.write("** ----------------------------------------------------------\n")

        # User Element Interfaces
        f.write("*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n3\n")
        f.write("*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n1, 2\n")
        if num_phys_tris > 0:
            f.write("*USER ELEMENT, TYPE=U3, NODES=3, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n3\n")
            f.write("*USER ELEMENT, TYPE=U4, NODES=3, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n1, 2\n")

        # Nodes
        f.write("*NODE\n")
        for nid in sorted(nodes.keys()):
            x, y = nodes[nid]
            f.write("%d, %.10e, %.10e\n" % (nid, x, y))
        f.write("%d, 0.5, 1.0\n" % rp_nid)

        # Layer 1: Phase-field UEL (1..N_phys)
        if quad_elems:
            f.write("*ELEMENT, TYPE=U1, ELSET=PHASE_QUAD\n")
            for eid in sorted(quad_elems.keys()):
                f.write("%d, %s\n" % (eid, ", ".join(str(n) for n in quad_elems[eid])))
        if tri_elems:
            f.write("*ELEMENT, TYPE=U3, ELSET=PHASE_TRI\n")
            for eid in sorted(tri_elems.keys()):
                f.write("%d, %s\n" % (eid, ", ".join(str(n) for n in tri_elems[eid])))

        # Layer 2: Displacement UEL (N_phys+1..2*N_phys)
        offset_disp = num_phys_elems
        if quad_elems:
            f.write("*ELEMENT, TYPE=U2, ELSET=DISP_QUAD\n")
            for eid in sorted(quad_elems.keys()):
                f.write("%d, %s\n" % (eid + offset_disp, ", ".join(str(n) for n in quad_elems[eid])))
        if tri_elems:
            f.write("*ELEMENT, TYPE=U4, ELSET=DISP_TRI\n")
            for eid in sorted(tri_elems.keys()):
                f.write("%d, %s\n" % (eid + offset_disp, ", ".join(str(n) for n in tri_elems[eid])))

        # Layer 3: Companion UMAT (2*N_phys+1..3*N_phys)
        offset_umat = 2 * num_phys_elems
        if quad_elems:
            f.write("*ELEMENT, TYPE=CPE4, ELSET=UMAT_QUADS\n")
            for eid in sorted(quad_elems.keys()):
                f.write("%d, %s\n" % (eid + offset_umat, ", ".join(str(n) for n in quad_elems[eid])))
        if tri_elems:
            f.write("*ELEMENT, TYPE=CPE3, ELSET=UMAT_TRIS\n")
            for eid in sorted(tri_elems.keys()):
                f.write("%d, %s\n" % (eid + offset_umat, ", ".join(str(n) for n in tri_elems[eid])))

        # Sets
        f.write("*ELSET, ELSET=All_elem\nUMAT_QUADS\n")
        if tri_elems:
            f.write("UMAT_TRIS\n")
        f.write("*ELSET, ELSET=umatelem\nAll_elem\n")

        def write_nset(file_handle, set_name, node_list):
            file_handle.write("*NSET, NSET=" + set_name + "\n")
            chunk_size = 10
            for i in range(0, len(node_list), chunk_size):
                chunk = node_list[i:i + chunk_size]
                file_handle.write(", ".join(str(n) for n in chunk) + "\n")

        write_nset(f, "N_BOTTOM", bottom_nodes)
        write_nset(f, "N_PIN", [pin_node])
        write_nset(f, "N_TOP", top_nodes)
        write_nset(f, "N_RP", [rp_nid])

        # UEL Properties: l0, Gc, E, nu, eta, N_phys
        f.write("*UEL PROPERTY, ELSET=PHASE_QUAD\n0.0075, 0.0027, 210.0, 0.3, 1.0e-7, %d.\n" % num_phys_elems)
        f.write("*UEL PROPERTY, ELSET=DISP_QUAD\n0.0075, 0.0027, 210.0, 0.3, 1.0e-7, %d.\n" % num_phys_elems)
        if tri_elems:
            f.write("*UEL PROPERTY, ELSET=PHASE_TRI\n0.0075, 0.0027, 210.0, 0.3, 1.0e-7, %d.\n" % num_phys_elems)
            f.write("*UEL PROPERTY, ELSET=DISP_TRI\n0.0075, 0.0027, 210.0, 0.3, 1.0e-7, %d.\n" % num_phys_elems)

        # Companion UMAT Material Section
        f.write("*SOLID SECTION, ELSET=All_elem, MATERIAL=DUMMY_MAT\n1.0\n")
        f.write("*MATERIAL, NAME=DUMMY_MAT\n*USER MATERIAL, CONSTANTS=2\n210.0, 0.3\n*DEPVAR\n16\n")

        # Coupling Equations
        f.write("** EQUATIONS (Rigid top tensile pull tied to RP)\n")
        for tn in sorted(top_nodes):
            f.write("*EQUATION\n2\n%d, 2, 1.0, %d, 2, -1.0\n" % (tn, rp_nid))

        # Step 1: Monotonic loading to u = 0.0050 mm (2000 increments)
        f.write("** ----------------------------------------------------------\n")
        f.write("** STEP 1: Monotonic Tensile Loading to u = 0.0050 mm (2000 increments)\n")
        f.write("** ----------------------------------------------------------\n")
        f.write("*STEP, NAME=Step-1, NLGEOM=NO, INC=6000\n")
        f.write("*STATIC\n5.0E-4, 1.0, 1.0E-9, 5.0E-4\n")
        f.write("*BOUNDARY\nN_BOTTOM, 2, 2, 0.0\nN_PIN, 1, 1, 0.0\nN_TOP, 1, 1, 0.0\nN_RP, 2, 2, 0.0050\n")
        f.write("*RESTART, WRITE, FREQUENCY=0\n")
        f.write("*OUTPUT, FIELD, FREQUENCY=1\n")
        f.write("*NODE OUTPUT, NSET=N_RP\nU, RF\n")
        f.write("*NODE OUTPUT\nU, RF\n")
        f.write("*ELEMENT OUTPUT, ELSET=umatelem\nSDV, S, E\n")
        f.write("*NODE PRINT, FREQ=1, NSET=N_RP\nU2, RF2\n")
        f.write("*END STEP\n")

        # Step 2: Fracture propagation to u = 0.0100 mm (5000 increments)
        f.write("** ----------------------------------------------------------\n")
        f.write("** STEP 2: Fracture Propagation to u = 0.0100 mm (5000 increments)\n")
        f.write("** ----------------------------------------------------------\n")
        f.write("*STEP, NAME=Step-2, NLGEOM=NO, INC=10000\n")
        f.write("*STATIC\n2.0E-4, 1.0, 1.0E-14, 2.0E-4\n")
        f.write("*BOUNDARY\nN_RP, 2, 2, 0.0100\n")
        f.write("*RESTART, WRITE, FREQUENCY=0\n")
        f.write("*OUTPUT, FIELD, FREQUENCY=1\n")
        f.write("*NODE OUTPUT, NSET=N_RP\nU, RF\n")
        f.write("*NODE OUTPUT\nU, RF\n")
        f.write("*ELEMENT OUTPUT, ELSET=umatelem\nSDV, S, E\n")
        f.write("*NODE PRINT, FREQ=1, NSET=N_RP\nU2, RF2\n")
        f.write("*END STEP\n")

    sha256 = compute_sha256(target_inp_path)
    print("Wrote %s (SHA-256: %s)" % (target_inp_path, sha256))
    return {
        "num_nodes": num_phys_nodes,
        "num_elements": num_phys_elems,
        "num_quads": num_phys_quads,
        "num_tris": num_phys_tris,
        "sha256": sha256
    }

if __name__ == "__main__":
    # Build 2.0% deck
    p2_phys = "models/pandey_kumar_mode1/06_production_adaptive_2pct/PK_MODE1_PROPOSED_PFM_PHYS.inp"
    if not os.path.exists(p2_phys):
        p2_phys = "models/pandey_kumar_mode1/05_proposed_adaptive_2pct/PK_MODE1_2PCT_PHYS.inp"
    p2_uel = "models/pandey_kumar_mode1/06_production_adaptive_2pct/PK_MODE1_PROPOSED_PFM.inp"
    r2 = build_corrected_deck(p2_phys, p2_uel, "2.0%")
    
    # Build 5.0% deck
    p5_phys = "models/pandey_kumar_mode1/07_production_adaptive_5pct/PK_MODE1_5PCT_PFM_PHYS.inp"
    p5_uel = "models/pandey_kumar_mode1/07_production_adaptive_5pct/PK_MODE1_5PCT_PFM.inp"
    r5 = build_corrected_deck(p5_phys, p5_uel, "5.0%")
    
    print("\nSummary:")
    print("2.0% Deck SHA-256:", r2["sha256"])
    print("5.0% Deck SHA-256:", r5["sha256"])

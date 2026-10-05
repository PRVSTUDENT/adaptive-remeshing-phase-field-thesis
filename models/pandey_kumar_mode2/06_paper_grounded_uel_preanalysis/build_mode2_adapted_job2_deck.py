#!/usr/bin/env python3
"""
Convert raw adapted mesh to production 3-layer Mode-II Job-2_UEL.inp deck:
- Layer 1: Phase-field user elements (U1 quads, U3 tris) -> IDs 1..N_phys
- Layer 2: Mechanical user elements (U2 quads, U4 tris) -> IDs (N_phys+1)..2*N_phys
- Layer 3: Companion visualization elements (CPE4 quads, CPE3 tris) -> IDs (2*N_phys+1)..3*N_phys
- Rigid top horizontal shear pull tied to RP (999999) via *EQUATION
- Wrapped NSET cards (max 16 entries per line)
- Mode-II fracture properties: l0=0.015 mm, Gc=0.0027 kN/mm, E=210 GPa, nu=0.3
- Step 1: u1 -> 0.0100 mm (1000 incs)
- Step 2: u1 -> 0.0600 mm (6000 incs)
"""

from __future__ import print_function
import os
import sys

def write_wrapped_nset(f, nset_name, node_list, max_per_line=16):
    f.write("*NSET, NSET=%s\n" % nset_name)
    sorted_nodes = sorted(node_list)
    for i in range(0, len(sorted_nodes), max_per_line):
        chunk = sorted_nodes[i:i + max_per_line]
        f.write(", ".join(str(n) for n in chunk) + "\n")

def convert_raw_to_mode2_job2_deck(src_raw_inp, dst_uel_inp, job_name="Job-2_UEL"):
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
    rp_nid = 999999

    print("Converting %s -> %s" % (src_raw_inp, dst_uel_inp))
    print("Mesh: %d elements (%d quads, %d tris), %d nodes" % 
          (num_phys_elems, num_phys_quads, num_phys_tris, num_phys_nodes))
    print("Boundary nodes: %d bottom, %d top" % (len(bottom_nodes), len(top_nodes)))

    with open(dst_uel_inp, 'w') as f:
        f.write("*HEADING\n")
        f.write("%s - Mode-II Adapted Refined PFM Solve\n" % job_name)
        f.write("** Finite Elements: %d (%d quads, %d tris), Nodes: %d\n" % 
                (num_phys_elems, num_phys_quads, num_phys_tris, num_phys_nodes))
        f.write("** Parameters: E=210 GPa, nu=0.3, l0=0.015 mm, Gc=0.0027 kN/mm, eta=1e-7, N_PHYS=%d.\n" % num_phys_elems)
        f.write("** ----------------------------------------------------------\n")
        f.write("*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n3\n")
        f.write("*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n1, 2\n")
        if num_phys_tris > 0:
            f.write("*USER ELEMENT, TYPE=U3, NODES=3, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n3\n")
            f.write("*USER ELEMENT, TYPE=U4, NODES=3, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n1, 2\n")

        # Nodes
        f.write("*NODE\n")
        for nid in sorted(nodes.keys()):
            x, y = nodes[nid]
            f.write("%d, %.12g, %.12g\n" % (nid, x, y))
        f.write("%d, 0.5, 1.0\n" % rp_nid)

        # Mapping elements to 1..N_phys
        sorted_quad_eids = sorted(quad_elems.keys())
        sorted_tri_eids = sorted(tri_elems.keys())

        elem_map = {}
        new_eid = 1
        for orig_eid in sorted_quad_eids:
            elem_map[orig_eid] = new_eid
            new_eid += 1
        for orig_eid in sorted_tri_eids:
            elem_map[orig_eid] = new_eid
            new_eid += 1

        # Layer 1: Phase-field UEL elements (1..N_phys)
        f.write("*ELEMENT, TYPE=U1, ELSET=PHASE_QUADS\n")
        for orig_eid in sorted_quad_eids:
            c = quad_elems[orig_eid]
            f.write("%d, %s\n" % (elem_map[orig_eid], ", ".join(str(n) for n in c)))
        if num_phys_tris > 0:
            f.write("*ELEMENT, TYPE=U3, ELSET=PHASE_TRIS\n")
            for orig_eid in sorted_tri_eids:
                c = tri_elems[orig_eid]
                f.write("%d, %s\n" % (elem_map[orig_eid], ", ".join(str(n) for n in c)))

        # Layer 2: Mechanical UEL elements ((N_phys+1)..2*N_phys)
        offset_disp = num_phys_elems
        f.write("*ELEMENT, TYPE=U2, ELSET=MECH_QUADS\n")
        for orig_eid in sorted_quad_eids:
            c = quad_elems[orig_eid]
            f.write("%d, %s\n" % (elem_map[orig_eid] + offset_disp, ", ".join(str(n) for n in c)))
        if num_phys_tris > 0:
            f.write("*ELEMENT, TYPE=U4, ELSET=MECH_TRIS\n")
            for orig_eid in sorted_tri_eids:
                c = tri_elems[orig_eid]
                f.write("%d, %s\n" % (elem_map[orig_eid] + offset_disp, ", ".join(str(n) for n in c)))

        # Layer 3: Companion UMAT CPE4/CPE3 ((2*N_phys+1)..3*N_phys)
        offset_umat = 2 * num_phys_elems
        f.write("*ELEMENT, TYPE=CPE4, ELSET=UMAT_QUADS\n")
        for orig_eid in sorted_quad_eids:
            c = quad_elems[orig_eid]
            f.write("%d, %s\n" % (elem_map[orig_eid] + offset_umat, ", ".join(str(n) for n in c)))
        if num_phys_tris > 0:
            f.write("*ELEMENT, TYPE=CPE3, ELSET=UMAT_TRIS\n")
            for orig_eid in sorted_tri_eids:
                c = tri_elems[orig_eid]
                f.write("%d, %s\n" % (elem_map[orig_eid] + offset_umat, ", ".join(str(n) for n in c)))

        # Sets
        f.write("*ELSET, ELSET=PHASE_ELEM, GENERATE\n1, %d, 1\n" % num_phys_elems)
        f.write("*ELSET, ELSET=MECH_ELEM, GENERATE\n%d, %d, 1\n" % (num_phys_elems + 1, 2 * num_phys_elems))
        f.write("*ELSET, ELSET=All_elem, GENERATE\n%d, %d, 1\n" % (2 * num_phys_elems + 1, 3 * num_phys_elems))
        f.write("*ELSET, ELSET=umatelem, GENERATE\n%d, %d, 1\n" % (2 * num_phys_elems + 1, 3 * num_phys_elems))

        # Node sets (wrapped)
        write_wrapped_nset(f, "N_BOTTOM", bottom_nodes)
        write_wrapped_nset(f, "N_TOP", top_nodes)
        write_wrapped_nset(f, "N_RP", [rp_nid])

        # UEL Properties
        f.write("*UEL PROPERTY, ELSET=PHASE_ELEM\n0.015, 0.0027, 210.0, 0.3, 1.0e-7, %d.\n" % num_phys_elems)
        f.write("*UEL PROPERTY, ELSET=MECH_ELEM\n0.015, 0.0027, 210.0, 0.3, 1.0e-7, %d.\n" % num_phys_elems)

        # Companion section
        f.write("*SOLID SECTION, ELSET=All_elem, MATERIAL=UMAT_MAT\n1.0,\n")
        f.write("*MATERIAL, NAME=UMAT_MAT\n*USER MATERIAL, CONSTANTS=3\n210.0, 0.3, %d.\n" % num_phys_elems)
        f.write("*DEPVAR\n20,\n")

        # Coupling Equations for Mode-II Shear Pull
        for tn in sorted(top_nodes):
            f.write("*EQUATION\n2\n%d, 1, 1.0, %d, 1, -1.0\n" % (tn, rp_nid))

        # Steps
        f.write("** STEP 1: Linear Loading to u1 = 0.0100 mm\n")
        f.write("*STEP, NAME=Step-1, NLGEOM=NO, INC=3000\n")
        f.write("*STATIC\n")
        f.write("0.001, 1.0, 1.0e-9, 0.001\n")
        f.write("*BOUNDARY\n")
        f.write("N_BOTTOM, 1, 2, 0.0\n")
        f.write("N_TOP, 2, 2, 0.0\n")
        f.write("N_RP, 1, 1, 0.0100\n")
        f.write("*RESTART, WRITE, FREQUENCY=0\n")
        f.write("*OUTPUT, FIELD, TIME INTERVAL=0.001\n")
        f.write("*NODE OUTPUT, NSET=N_RP\nU, RF\n")
        f.write("*ELEMENT OUTPUT, ELSET=All_elem\nSDV\n")
        f.write("*NODE PRINT, FREQ=1, NSET=N_RP\nU1, RF1\n")
        f.write("*END STEP\n")

        f.write("** STEP 2: Fracture Propagation to u1 = 0.0600 mm\n")
        f.write("*STEP, NAME=Step-2, NLGEOM=NO, INC=7000\n")
        f.write("*STATIC\n")
        f.write("0.0002, 1.0, 1.0e-9, 0.0002\n")
        f.write("*BOUNDARY\n")
        f.write("N_RP, 1, 1, 0.0600\n")
        f.write("*RESTART, WRITE, FREQUENCY=0\n")
        f.write("*OUTPUT, FIELD, TIME INTERVAL=0.001\n")
        f.write("*NODE OUTPUT, NSET=N_RP\nU, RF\n")
        f.write("*ELEMENT OUTPUT, ELSET=All_elem\nSDV\n")
        f.write("*NODE PRINT, FREQ=1, NSET=N_RP\nU1, RF1\n")
        f.write("*END STEP\n")

    print("Saved production UEL deck to %s" % dst_uel_inp)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python build_mode2_adapted_job2_deck.py <raw_inp> <dst_uel_inp> [job_name]")
        sys.exit(1)
    src = sys.argv[1]
    dst = sys.argv[2]
    jname = sys.argv[3] if len(sys.argv) >= 4 else "Job-2_UEL"
    convert_raw_to_mode2_job2_deck(src, dst, jname)

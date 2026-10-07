#!/usr/bin/env python3
"""
Mode-II Adapted Job-2_UEL.inp Builder
Converts raw native adapted mesh (M2_3_ADAPTED_RAW_2PCT.inp) into complete 3-layer production UEL input deck:
- Layer 1: Phase-field UEL (U1 quads, U3 tris) -> 1..N_phys (DOF 3)
- Layer 2: Mechanical UEL (U2 quads, U4 tris) -> (N_phys+1)..2*N_phys (DOFs 1, 2)
- Layer 3: Companion UMAT visualization elements (CPE4 quads, CPE3 tris) -> (2*N_phys+1)..3*N_phys
- Boundary conditions:
  * N_BOTTOM: y = 0.0 -> u1 = 0, u2 = 0
  * N_TOP: y = 1.0 -> u2 = 0, u1 coupled to N_RP (999999) via *EQUATION
- Loading schedule:
  * Step-1: ux = 0 -> 0.0100 mm (2000 increments, Dt=5.0e-4, Dux=5.0 nm)
  * Step-2: ux = 0.0100 -> 0.0200 mm (2000 increments, Dt=5.0e-4, Dux=5.0 nm, Paper Horizon)
- Properties:
  * E = 210.0 kN/mm^2 (210 GPa)
  * nu = 0.3
  * Gc = 0.0027 kN/mm (2.7 N/mm)
  * l0 = 0.015 mm (15.0 um)
  * k = 1.0e-7
  * N_PHYS = 22530
"""

import sys
import os

def write_wrapped_nset(f, nset_name, node_list, max_per_line=16):
    f.write("*NSET, NSET=%s\n" % nset_name)
    sorted_nodes = sorted(node_list)
    for i in range(0, len(sorted_nodes), max_per_line):
        chunk = sorted_nodes[i:i + max_per_line]
        f.write(", ".join(str(n) for n in chunk) + "\n")

def generate_mode2_adapted_job2_deck(src_raw_inp, dst_uel_inp, job_name="Job-2_UEL"):
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

    # Find boundary nodes (tolerance 1e-4 mm for 1.0 mm x 1.0 mm domain)
    bottom_nodes = [nid for nid, (x, y) in nodes.items() if abs(y - 0.0) < 1e-4]
    top_nodes = [nid for nid, (x, y) in nodes.items() if abs(y - 1.0) < 1e-4]
    rp_nid = 999999

    print("Building Mode-II Adapted Deck:")
    print("  Source Raw: %s" % src_raw_inp)
    print("  Target UEL: %s" % dst_uel_inp)
    print("  Nodes: %d, Elements: %d (%d quads, %d tris)" %
          (num_phys_nodes, num_phys_elems, num_phys_quads, num_phys_tris))
    print("  Boundary Nodes: Bottom=%d, Top=%d" % (len(bottom_nodes), len(top_nodes)))

    with open(dst_uel_inp, 'w') as f:
        f.write("*Heading\n")
        f.write("** %s: Mode-II Pandey-Kumar (2025) Adapted Refined PFM Solve with Paper Horizon (ux = 0.0200 mm)\n" % job_name)
        f.write("** Physical Mesh: %d elements (%d quads, %d tris), %d nodes\n" %
                (num_phys_elems, num_phys_quads, num_phys_tris, num_phys_nodes))
        f.write("** Layered UEL/UMAT System: Layer 1 (U1/U3 phase), Layer 2 (U2/U4 mech), Layer 3 (CPE4/CPE3 companion)\n")
        f.write("** Parameters: E=210 GPa, nu=0.3, l0=0.015 mm, Gc=0.0027 kN/mm, eta=1e-7, N_PHYS=%d.\n" % num_phys_elems)
        f.write("** ==========================================================\n")
        f.write("*Preprint, echo=NO, model=NO, history=NO, contact=NO\n")
        f.write("** ----------------------------------------------------------\n")
        f.write("** USER ELEMENT INTERFACES (f42_mixed_uel_mode2_miehe.for)\n")
        f.write("** ----------------------------------------------------------\n")
        f.write("*User Element, nodes=4, type=U1, properties=6, coordinates=2, variables=18, unsymm\n3\n")
        f.write("*User Element, nodes=4, type=U2, properties=6, coordinates=2, variables=18, unsymm\n1, 2\n")
        if num_phys_tris > 0:
            f.write("*User Element, nodes=3, type=U3, properties=6, coordinates=2, variables=18, unsymm\n3\n")
            f.write("*User Element, nodes=3, type=U4, properties=6, coordinates=2, variables=18, unsymm\n1, 2\n")

        # Nodes
        f.write("** ----------------------------------------------------------\n")
        f.write("** NODES\n")
        f.write("** ----------------------------------------------------------\n")
        f.write("*Node\n")
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
        f.write("** ----------------------------------------------------------\n")
        f.write("** LAYER 1: PHASE FIELD USER ELEMENTS (1..%d)\n" % num_phys_elems)
        f.write("** ----------------------------------------------------------\n")
        f.write("*Element, type=U1, elset=PHASE_QUADS\n")
        for orig_eid in sorted_quad_eids:
            c = quad_elems[orig_eid]
            f.write("%d, %s\n" % (elem_map[orig_eid], ", ".join(str(n) for n in c)))
        if num_phys_tris > 0:
            f.write("*Element, type=U3, elset=PHASE_TRIS\n")
            for orig_eid in sorted_tri_eids:
                c = tri_elems[orig_eid]
                f.write("%d, %s\n" % (elem_map[orig_eid], ", ".join(str(n) for n in c)))

        # Layer 2: Mechanical UEL elements ((N_phys+1)..2*N_phys)
        offset_disp = num_phys_elems
        f.write("** ----------------------------------------------------------\n")
        f.write("** LAYER 2: MECHANICAL USER ELEMENTS (%d..%d)\n" % (num_phys_elems + 1, 2 * num_phys_elems))
        f.write("** ----------------------------------------------------------\n")
        f.write("*Element, type=U2, elset=MECH_QUADS\n")
        for orig_eid in sorted_quad_eids:
            c = quad_elems[orig_eid]
            f.write("%d, %s\n" % (elem_map[orig_eid] + offset_disp, ", ".join(str(n) for n in c)))
        if num_phys_tris > 0:
            f.write("*Element, type=U4, elset=MECH_TRIS\n")
            for orig_eid in sorted_tri_eids:
                c = tri_elems[orig_eid]
                f.write("%d, %s\n" % (elem_map[orig_eid] + offset_disp, ", ".join(str(n) for n in c)))

        # Layer 3: Companion UMAT CPE4/CPE3 ((2*N_phys+1)..3*N_phys)
        offset_umat = 2 * num_phys_elems
        f.write("** ----------------------------------------------------------\n")
        f.write("** LAYER 3: COMPANION VISUALIZATION ELEMENTS (%d..%d)\n" % (2 * num_phys_elems + 1, 3 * num_phys_elems))
        f.write("** ----------------------------------------------------------\n")
        f.write("*Element, type=CPE4, elset=UMAT_QUADS\n")
        for orig_eid in sorted_quad_eids:
            c = quad_elems[orig_eid]
            f.write("%d, %s\n" % (elem_map[orig_eid] + offset_umat, ", ".join(str(n) for n in c)))
        if num_phys_tris > 0:
            f.write("*Element, type=CPE3, elset=UMAT_TRIS\n")
            for orig_eid in sorted_tri_eids:
                c = tri_elems[orig_eid]
                f.write("%d, %s\n" % (elem_map[orig_eid] + offset_umat, ", ".join(str(n) for n in c)))

        # Sets
        f.write("** ----------------------------------------------------------\n")
        f.write("** ELEMENT SETS\n")
        f.write("** ----------------------------------------------------------\n")
        f.write("*Elset, elset=PHASE_ELEM, generate\n1, %d, 1\n" % num_phys_elems)
        f.write("*Elset, elset=MECH_ELEM, generate\n%d, %d, 1\n" % (num_phys_elems + 1, 2 * num_phys_elems))
        f.write("*Elset, elset=All_elem, generate\n%d, %d, 1\n" % (2 * num_phys_elems + 1, 3 * num_phys_elems))
        f.write("*Elset, elset=umatelem, generate\n%d, %d, 1\n" % (2 * num_phys_elems + 1, 3 * num_phys_elems))

        # Node sets (wrapped)
        f.write("** ----------------------------------------------------------\n")
        f.write("** NODE SETS\n")
        f.write("** ----------------------------------------------------------\n")
        write_wrapped_nset(f, "N_BOTTOM", bottom_nodes)
        write_wrapped_nset(f, "N_TOP", top_nodes)
        write_wrapped_nset(f, "N_RP", [rp_nid])

        # UEL Properties
        f.write("** ----------------------------------------------------------\n")
        f.write("** PROPERTIES & MATERIALS\n")
        f.write("** ----------------------------------------------------------\n")
        f.write("*UEL Property, elset=PHASE_ELEM\n210.0, 0.3, 0.0027, 0.015, 1.0E-7, %d.\n" % num_phys_elems)
        f.write("*UEL Property, elset=MECH_ELEM\n210.0, 0.3, 0.0027, 0.015, 1.0E-7, %d.\n" % num_phys_elems)

        # Companion section
        f.write("*Solid Section, elset=All_elem, material=UMAT_MAT\n1.0,\n")
        f.write("*Material, name=UMAT_MAT\n*User Material, constants=3\n1.0E-11, 0.3, %d.\n" % num_phys_elems)
        f.write("*Depvar\n20,\n")

        # Coupling Equations for Mode-II Shear Pull
        f.write("** ----------------------------------------------------------\n")
        f.write("** EQUATIONS (Rigid top surface coupled to RP 999999 for u1)\n")
        f.write("** ----------------------------------------------------------\n")
        for tn in sorted(top_nodes):
            f.write("*Equation\n2\n%d, 1, 1.0, %d, 1, -1.0\n" % (tn, rp_nid))

        # Steps
        f.write("** ==========================================================\n")
        f.write("** STEP 1: Monotonic Shear Loading to u1 = 0.0100 mm (2000 incs, Dt=5e-4, Dux=5.0 nm)\n")
        f.write("** ==========================================================\n")
        f.write("*Step, name=Step-1, nlgeom=NO, inc=3000\n")
        f.write("*Static\n")
        f.write("5.0E-4, 1.0, 1.0E-9, 5.0E-4\n")
        f.write("*Boundary\n")
        f.write("N_BOTTOM, 1, 2, 0.0\n")
        f.write("N_TOP, 2, 2, 0.0\n")
        f.write("N_RP, 1, 1, 0.0100\n")
        f.write("*Restart, write, frequency=0\n")
        f.write("*Output, field, time interval=0.001\n")
        f.write("*Node Output, nset=N_RP\nU, RF\n")
        f.write("*Element Output, elset=All_elem, directions=YES\n")
        f.write("MISESERI, MISESAVG, S, EVOL\n")
        f.write("*Element Output, elset=umatelem\nSDV\n")
        f.write("*Node Print, freq=1, nset=N_RP\nU1, RF1\n")
        f.write("*End Step\n")

        f.write("** ==========================================================\n")
        f.write("** STEP 2: Monotonic Shear Loading to u1 = 0.0200 mm (2000 incs, Dt=5e-4, Dux=5.0 nm, Paper Horizon)\n")
        f.write("** ==========================================================\n")
        f.write("*Step, name=Step-2, nlgeom=NO, inc=3000\n")
        f.write("*Static\n")
        f.write("5.0E-4, 1.0, 1.0E-9, 5.0E-4\n")
        f.write("*Boundary\n")
        f.write("N_RP, 1, 1, 0.0200\n")
        f.write("*Restart, write, frequency=0\n")
        f.write("*Output, field, time interval=0.001\n")
        f.write("*Node Output, nset=N_RP\nU, RF\n")
        f.write("*Element Output, elset=All_elem, directions=YES\n")
        f.write("MISESERI, MISESAVG, S, EVOL\n")
        f.write("*Element Output, elset=umatelem\nSDV\n")
        f.write("*Node Print, freq=1, nset=N_RP\nU1, RF1\n")
        f.write("*End Step\n")

    print("SUCCESS: Successfully wrote %s" % dst_uel_inp)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python build_mode2_adapted_job2_deck.py <src_raw_inp> <dst_uel_inp> [job_name]")
        sys.exit(1)
    src_raw = sys.argv[1]
    dst_uel = sys.argv[2]
    jname = sys.argv[3] if len(sys.argv) >= 4 else "Job-2_UEL"
    generate_mode2_adapted_job2_deck(src_raw, dst_uel, jname)

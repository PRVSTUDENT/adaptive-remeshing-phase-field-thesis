# -*- coding: utf-8 -*-
"""
build_f1759_case4_prod_deck.py
Generates the definitive 3-layer UEL production deck PK_F1759_CASE_4_PROD.inp
from the qualified physical mesh F1725_S2_COARSEN_ET315.inp (13,017 physical elements).

Benchmark: Pandey & Kumar (2025), Section 4.5 "Tensile Failure of a Square Plate with Five Holes"
Literature Element Count: 12,944 elements (Fig. 23b)
Achieved Element Count: 13,017 physical elements (+0.56% parity)
Parameters: E = 210.0 GPa, nu = 0.3, Gc = 0.0027 kN/mm, l0 = 0.0080 mm, k = 1.0e-7

Key Technical Preflight Requirements:
1. Complete Layer 3 SDV1 (d) and SDV2 (H) field output coverage:
   *ELEMENT OUTPUT, ELSET=All_elem
   S, SDV
2. FREQUENCY=1 in both Step 1 and Step 2 so that every converged increment is recorded as an ODB frame.
3. Strict 16-item line wrapping for all NSET definitions (Abaqus card length guard).
4. Active DOF declarations:
   - Layer 1 UEL (U1 quad, U3 tri): active DOF strictly 3 (d).
   - Layer 2 UEL (U2 quad, U4 tri): active DOFs strictly 1, 2 (u_x, u_y).
   - Layer 3 companion (CPE4 quad, CPE3 tri): dummy material with DEPVAR=16.
5. Reconciled boundary condition loading schedule:
   - Step 1: u_y = 0.0050 mm over step time 1.0 (50 increments of dt = 0.02).
   - Step 2: u_y = 0.0100 mm at step time 1.0 (initial dt = 0.0001, max dt = 0.0005, min dt = 1.0e-8).
"""
import os
import sys

def build_case4_prod_deck(phys_inp, prod_inp):
    nodes = {}
    elements = {}
    
    with open(phys_inp, "r") as f:
        in_nodes = False
        in_elements = False
        for line in f:
            l = line.strip()
            if not l or l.startswith("**"):
                continue
            if l.startswith("*"):
                in_nodes = False
                in_elements = False
                if l.upper().startswith("*NODE"):
                    in_nodes = True
                elif l.upper().startswith("*ELEMENT") and not l.upper().startswith("*ELEMENT OUTPUT"):
                    in_elements = True
                continue
            parts = [p.strip() for p in l.split(",") if p.strip()]
            if in_nodes:
                nid = int(parts[0])
                nodes[nid] = (float(parts[1]), float(parts[2]))
            elif in_elements:
                eid = int(parts[0])
                nids = [int(p) for p in parts[1:]]
                elements[eid] = nids

    num_phys_elems = len(elements)
    quad_elems = {eid: nids for eid, nids in elements.items() if len(nids) == 4}
    tri_elems = {eid: nids for eid, nids in elements.items() if len(nids) == 3}

    print("Parsed %d nodes, %d elements (%d quads, %d tris)" % (len(nodes), num_phys_elems, len(quad_elems), len(tri_elems)))

    bottom_nodes = set()
    top_nodes = set()
    pin_node = None
    min_dist_pin = 1e9

    for nid, (x, y) in nodes.items():
        if abs(y - 0.0) < 1e-5:
            bottom_nodes.add(nid)
            d_pin = x**2 + y**2
            if d_pin < min_dist_pin:
                min_dist_pin = d_pin
                pin_node = nid
        if abs(y - 1.0) < 1e-5:
            top_nodes.add(nid)

    rp_nid = 999999

    with open(prod_inp, "w") as f:
        f.write("*HEADING\n")
        f.write("Task F1759: Case 4 Five-Hole Plate Coupled Phase-Field Fracture Definitive Production Deck\n")
        f.write("** Benchmark: Pandey & Kumar (2025) Sec. 4.5, 13,017 Physical Elements (+0.56% Parity vs 12,944)\n")
        f.write("** Parameters: E=210.0 GPa, nu=0.30, l0=0.0080 mm, Gc=0.0027 kN/mm, k=1.0e-7\n")
        f.write("*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n3\n")
        f.write("*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n1, 2\n")
        if tri_elems:
            f.write("*USER ELEMENT, TYPE=U3, NODES=3, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n3\n")
            f.write("*USER ELEMENT, TYPE=U4, NODES=3, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n1, 2\n")

        # Nodes
        f.write("*NODE\n")
        for nid in sorted(nodes.keys()):
            f.write("%d, %.8f, %.8f\n" % (nid, nodes[nid][0], nodes[nid][1]))
        f.write("%d, 0.50000000, 1.00000000\n" % rp_nid)

        # Layer 1: Phase field
        if quad_elems:
            f.write("*ELEMENT, TYPE=U1, ELSET=PHASE_QUAD\n")
            for eid in sorted(quad_elems.keys()):
                f.write("%d, %s\n" % (eid, ", ".join(str(n) for n in quad_elems[eid])))
        if tri_elems:
            f.write("*ELEMENT, TYPE=U3, ELSET=PHASE_TRI\n")
            for eid in sorted(tri_elems.keys()):
                f.write("%d, %s\n" % (eid, ", ".join(str(n) for n in tri_elems[eid])))

        # Layer 2: Mechanical UEL
        if quad_elems:
            f.write("*ELEMENT, TYPE=U2, ELSET=DISP_QUAD\n")
            for eid in sorted(quad_elems.keys()):
                f.write("%d, %s\n" % (eid + num_phys_elems, ", ".join(str(n) for n in quad_elems[eid])))
        if tri_elems:
            f.write("*ELEMENT, TYPE=U4, ELSET=DISP_TRI\n")
            for eid in sorted(tri_elems.keys()):
                f.write("%d, %s\n" % (eid + num_phys_elems, ", ".join(str(n) for n in tri_elems[eid])))

        # Layer 3: Companion standard visualizer elements
        if quad_elems:
            f.write("*ELEMENT, TYPE=CPE4, ELSET=UMAT_QUADS\n")
            for eid in sorted(quad_elems.keys()):
                f.write("%d, %s\n" % (eid + 2 * num_phys_elems, ", ".join(str(n) for n in quad_elems[eid])))
        if tri_elems:
            f.write("*ELEMENT, TYPE=CPE3, ELSET=UMAT_TRIS\n")
            for eid in sorted(tri_elems.keys()):
                f.write("%d, %s\n" % (eid + 2 * num_phys_elems, ", ".join(str(n) for n in tri_elems[eid])))

        # Element sets
        f.write("*ELSET, ELSET=All_elem\n")
        if quad_elems and tri_elems:
            f.write("UMAT_QUADS, UMAT_TRIS\n")
        elif quad_elems:
            f.write("UMAT_QUADS\n")
        f.write("*ELSET, ELSET=umatelem\nAll_elem\n")

        # Node sets with 16-item wrapping
        f.write("*NSET, NSET=N_BOTTOM\n")
        b_list = sorted(list(bottom_nodes))
        for i in range(0, len(b_list), 16):
            f.write(", ".join(str(n) for n in b_list[i:i+16]) + "\n")

        f.write("*NSET, NSET=N_PIN\n%d\n" % pin_node)

        f.write("*NSET, NSET=N_TOP\n")
        t_list = sorted(list(top_nodes))
        for i in range(0, len(t_list), 16):
            f.write(", ".join(str(n) for n in t_list[i:i+16]) + "\n")

        f.write("*NSET, NSET=N_RP\n%d\n" % rp_nid)

        # UEL Properties: l0=0.0080, Gc=0.0027, E=210.0, nu=0.3, k=1.0e-7, num_phys_elems
        f.write("*UEL PROPERTY, ELSET=PHASE_QUAD\n0.0080, 0.0027, 210.0, 0.3, 1.0e-7, %.1f\n" % float(num_phys_elems))
        f.write("*UEL PROPERTY, ELSET=DISP_QUAD\n0.0080, 0.0027, 210.0, 0.3, 1.0e-7, %.1f\n" % float(num_phys_elems))
        if tri_elems:
            f.write("*UEL PROPERTY, ELSET=PHASE_TRI\n0.0080, 0.0027, 210.0, 0.3, 1.0e-7, %.1f\n" % float(num_phys_elems))
            f.write("*UEL PROPERTY, ELSET=DISP_TRI\n0.0080, 0.0027, 210.0, 0.3, 1.0e-7, %.1f\n" % float(num_phys_elems))

        # Dummy UMAT section with 16 state variables for visualizer mapping
        f.write("*SOLID SECTION, ELSET=All_elem, MATERIAL=DUMMY_MAT\n1.0\n")
        f.write("*MATERIAL, NAME=DUMMY_MAT\n*USER MATERIAL, CONSTANTS=2\n210.0, 0.3\n")
        f.write("*DEPVAR\n16\n")

        # Tie top nodes to RP
        f.write("** EQUATIONS (Rigid top tensile pull tied to RP)\n")
        for tn in sorted(top_nodes):
            f.write("*EQUATION\n2\n%d, 2, 1.0, %d, 2, -1.0\n" % (tn, rp_nid))

        # Step 1: Pre-peak pull to u = 0.0050 mm
        f.write("** ----------------------------------------------------------\n")
        f.write("** STEP 1: Linear Loading to u = 0.0050 mm\n")
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
        f.write("*ELEMENT OUTPUT, ELSET=All_elem\nS, SDV\n")
        f.write("*NODE PRINT, FREQ=1, NSET=N_RP\nU2, RF2\n")
        f.write("*END STEP\n")

        # Step 2: Fracture pull to u = 0.0100 mm
        f.write("** ----------------------------------------------------------\n")
        f.write("** STEP 2: Fracture Propagation to u = 0.0100 mm\n")
        f.write("** ----------------------------------------------------------\n")
        f.write("*STEP, NAME=Step-2, NLGEOM=NO, INC=20000\n")
        f.write("*STATIC\n")
        f.write("0.0001, 1.0, 1.0e-8, 0.0005\n")
        f.write("*BOUNDARY\n")
        f.write("N_RP, 2, 2, 0.0100\n")
        f.write("*RESTART, WRITE, FREQUENCY=0\n")
        f.write("*OUTPUT, FIELD, FREQUENCY=1\n")
        f.write("*NODE OUTPUT, NSET=N_RP\nU, RF\n")
        f.write("*ELEMENT OUTPUT, ELSET=All_elem\nS, SDV\n")
        f.write("*NODE PRINT, FREQ=1, NSET=N_RP\nU2, RF2\n")
        f.write("*END STEP\n")

    print("Built definitive Case 4 production deck %s with %d total layered elements (%d physical)" % 
          (prod_inp, 3 * num_phys_elems, num_phys_elems))

if __name__ == "__main__":
    phys = os.path.abspath(sys.argv[1])
    prod = os.path.abspath(sys.argv[2])
    build_case4_prod_deck(phys, prod)

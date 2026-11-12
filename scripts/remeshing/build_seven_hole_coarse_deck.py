# -*- coding: utf-8 -*-
"""
scripts/remeshing/build_seven_hole_coarse_deck.py
=================================================
Builds the 3-layer UEL-UMAT coupled coarse input deck PK_F1726_SEVEN_HOLE_COARSE.inp
from PK_F1726_SEVEN_HOLE_COARSE_PHYS.inp.
"""

from __future__ import print_function
import os
import sys

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
STUDY_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "218_f1726_seven_hole_study")
PHYS_INP = os.path.join(STUDY_DIR, "PK_F1726_SEVEN_HOLE_COARSE_PHYS.inp")
COARSE_COUPLED_INP = os.path.join(STUDY_DIR, "PK_F1726_SEVEN_HOLE_COARSE.inp")

def build_coarse_coupled_deck():
    nodes = {}
    quad_elems = {}
    tri_elems = {}

    in_nodes = False
    in_elements = False
    elem_type = None

    with open(PHYS_INP, "r") as f:
        for line in f:
            l = line.strip()
            if not l or l.startswith("**"):
                continue
            if l.startswith("*"):
                in_nodes = False
                in_elements = False
                u = l.upper()
                if u.startswith("*NODE"):
                    in_nodes = True
                elif u.startswith("*ELEMENT"):
                    in_elements = True
                    if "CPE4" in u or "CPS4" in u:
                        elem_type = "QUAD"
                    elif "CPE3" in u or "CPS3" in u:
                        elem_type = "TRI"
                    else:
                        elem_type = "OTHER"
                continue

            parts = [p.strip() for p in l.split(",") if p.strip()]
            if in_nodes and len(parts) >= 3:
                try:
                    nid = int(parts[0])
                    nodes[nid] = (float(parts[1]), float(parts[2]))
                except ValueError:
                    pass
            elif in_elements and len(parts) >= 4:
                try:
                    int_parts = [int(p) for p in parts]
                    eid = int_parts[0]
                    conn = int_parts[1:]
                    if elem_type == "QUAD" or len(conn) == 4:
                        quad_elems[eid] = tuple(conn[:4])
                    else:
                        tri_elems[eid] = tuple(conn[:3])
                except ValueError:
                    pass

    num_quads = len(quad_elems)
    num_tris = len(tri_elems)
    num_phys = num_quads + num_tris
    num_nodes = len(nodes)

    print("Parsed Physical Mesh: %d nodes, %d elements (%d quads, %d tris)" % (
        num_nodes, num_phys, num_quads, num_tris
    ))

    # Boundary node sets
    tol = 1e-4
    bottom_nodes = [nid for nid, (x, y) in nodes.items() if abs(y - 0.0) < tol]
    top_nodes = [nid for nid, (x, y) in nodes.items() if abs(y - 1.0) < tol]
    pin_candidates = [nid for nid in bottom_nodes if abs(nodes[nid][0] - 0.0) < tol]
    pin_node = min(pin_candidates) if pin_candidates else bottom_nodes[0]
    rp_nid = 999999

    print("Boundary sets: %d bottom nodes, %d top nodes, pin node %d" % (
        len(bottom_nodes), len(top_nodes), pin_node
    ))

    # Renumber physical elements 1 .. num_phys deterministically
    sorted_all_eids = sorted(list(quad_elems.keys()) + list(tri_elems.keys()))
    eid_map = {}
    new_quads = {}
    new_tris = {}
    new_eid = 1
    for old_eid in sorted(quad_elems.keys()):
        eid_map[old_eid] = new_eid
        new_quads[new_eid] = quad_elems[old_eid]
        new_eid += 1
    for old_eid in sorted(tri_elems.keys()):
        eid_map[old_eid] = new_eid
        new_tris[new_eid] = tri_elems[old_eid]
        new_eid += 1

    # Offsets
    disp_offset = num_phys
    umat_offset = 2 * num_phys

    with open(COARSE_COUPLED_INP, "w") as out:
        out.write("** ==========================================================\n")
        out.write("** TASK F1726: SEVEN-HOLE COARSE PHASE-FIELD MODEL (METHOD A)\n")
        out.write("** Physical elements: %d (Quads: %d, Tris: %d), Nodes: %d\n" % (
            num_phys, num_quads, num_tris, num_nodes
        ))
        out.write("** Layered elements: %d, Total nodes: %d\n" % (
            3 * num_phys, num_nodes + 1
        ))
        out.write("** Direct UEL-UMAT stress coupling via COMMON /CB_F1720_STRESS/\n")
        out.write("** ==========================================================\n")
        out.write("*HEADING\n")
        out.write("F1726 Coarse Seven-Hole Simulation with Direct UEL-UMAT Coupling\n")

        # UEL cards
        out.write("*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n3\n")
        out.write("*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n1, 2\n")
        if num_tris > 0:
            out.write("*USER ELEMENT, TYPE=U3, NODES=3, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n3\n")
            out.write("*USER ELEMENT, TYPE=U4, NODES=3, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n1, 2\n")

        # Nodes
        out.write("*NODE\n")
        for nid in sorted(nodes.keys()):
            x, y = nodes[nid]
            out.write("%d, %.9e, %.9e\n" % (nid, x, y))
        out.write("%d, %.9e, %.9e\n" % (rp_nid, 0.5, 1.0))

        # Layer 1: Phase field (DOF 3)
        if new_quads:
            out.write("*ELEMENT, TYPE=U1, ELSET=PHASE_QUAD\n")
            for eid in sorted(new_quads.keys()):
                out.write("%d, %s\n" % (eid, ", ".join(str(n) for n in new_quads[eid])))
        if new_tris:
            out.write("*ELEMENT, TYPE=U3, ELSET=PHASE_TRI\n")
            for eid in sorted(new_tris.keys()):
                out.write("%d, %s\n" % (eid, ", ".join(str(n) for n in new_tris[eid])))

        # Layer 2: Displacement (DOF 1, 2)
        if new_quads:
            out.write("*ELEMENT, TYPE=U2, ELSET=DISP_QUAD\n")
            for eid in sorted(new_quads.keys()):
                out.write("%d, %s\n" % (eid + disp_offset, ", ".join(str(n) for n in new_quads[eid])))
        if new_tris:
            out.write("*ELEMENT, TYPE=U4, ELSET=DISP_TRI\n")
            for eid in sorted(new_tris.keys()):
                out.write("%d, %s\n" % (eid + disp_offset, ", ".join(str(n) for n in new_tris[eid])))

        # Layer 3: Visualizer CPE4/CPE3
        if new_quads:
            out.write("*ELEMENT, TYPE=CPE4, ELSET=UMAT_QUADS\n")
            for eid in sorted(new_quads.keys()):
                out.write("%d, %s\n" % (eid + umat_offset, ", ".join(str(n) for n in new_quads[eid])))
        if new_tris:
            out.write("*ELEMENT, TYPE=CPE3, ELSET=UMAT_TRIS\n")
            for eid in sorted(new_tris.keys()):
                out.write("%d, %s\n" % (eid + umat_offset, ", ".join(str(n) for n in new_tris[eid])))

        # Sets
        out.write("*ELSET, ELSET=PHASE_ELEM\nPHASE_QUAD\n")
        if new_tris:
            out.write("PHASE_TRI\n")
        out.write("*ELSET, ELSET=MECH_ELEM\nDISP_QUAD\n")
        if new_tris:
            out.write("DISP_TRI\n")
        out.write("*ELSET, ELSET=All_elem\nUMAT_QUADS\n")
        if new_tris:
            out.write("UMAT_TRIS\n")
        out.write("*ELSET, ELSET=umatelem\nAll_elem\n")

        # Node sets
        def write_nset(name, nlist):
            out.write("*NSET, NSET=%s\n" % name)
            for i in range(0, len(nlist), 16):
                chunk = nlist[i:i+16]
                out.write(", ".join(str(n) for n in chunk) + "\n")

        write_nset("N_BOTTOM", sorted(bottom_nodes))
        write_nset("N_TOP", sorted(top_nodes))
        out.write("*NSET, NSET=N_PIN\n%d\n" % pin_node)
        out.write("*NSET, NSET=N_RP\n%d\n" % rp_nid)

        # Properties
        num_phys_f = float(num_phys)
        out.write("*UEL PROPERTY, ELSET=PHASE_ELEM\n")
        out.write("0.008000, 0.002700, 210.00, 0.30, 1.0e-07, %.1f\n" % num_phys_f)
        out.write("*UEL PROPERTY, ELSET=MECH_ELEM\n")
        out.write("0.008000, 0.002700, 210.00, 0.30, 1.0e-07, %.1f\n" % num_phys_f)

        out.write("*SOLID SECTION, ELSET=umatelem, MATERIAL=UMAT_MAT\n1.0\n")
        out.write("*MATERIAL, NAME=UMAT_MAT\n")
        out.write("*USER MATERIAL, CONSTANTS=4\n")
        out.write("210.00, 0.30, %.1f, 1.0\n" % num_phys_f)
        out.write("*DEPVAR\n20\n")

        # Rigid tie equations: top nodes tied to RP in DOF 2
        out.write("** ----------------------------------------------------------\n")
        out.write("** EQUATIONS (Rigid top tensile pull tied to RP in DOF 2)\n")
        out.write("** ----------------------------------------------------------\n")
        for nid in sorted(top_nodes):
            out.write("*EQUATION\n2\n")
            out.write("%d, 2, 1.0, %d, 2, -1.0\n" % (nid, rp_nid))

        # Step 1: Precritical loading to uy = 0.0050 mm
        out.write("** ----------------------------------------------------------\n")
        out.write("** STEP 1: Linear elastic loading to u_y = 0.0050 mm (50 incs)\n")
        out.write("** ----------------------------------------------------------\n")
        out.write("*STEP, NAME=Step-1, NLGEOM=NO, INC=1000\n")
        out.write("*STATIC\n0.02, 1.0, 1.0E-07, 0.02\n")
        out.write("*BOUNDARY\n")
        out.write("N_BOTTOM, 2, 2, 0.0\n")
        out.write("N_PIN, 1, 1, 0.0\n")
        out.write("N_RP, 1, 1, 0.0\n")
        out.write("N_RP, 2, 2, 0.0050\n")
        out.write("*OUTPUT, FIELD, FREQUENCY=5\n")
        out.write("*NODE OUTPUT, NSET=N_RP\nU, RF\n")
        out.write("*NODE OUTPUT, NSET=N_BOTTOM\nRF\n")
        out.write("*NODE OUTPUT\nU\n")
        out.write("*ELEMENT OUTPUT, ELSET=umatelem\nS, MISESERI, MISESAVG, EVOL, SDV\n")
        out.write("*NODE PRINT, FREQ=1, NSET=N_RP\nU2, RF2\n")
        out.write("*END STEP\n")

        # Step 2: Tensile loading into progressive localization regime
        out.write("** ----------------------------------------------------------\n")
        out.write("** STEP 2: Tension into localization regime to u_y = 0.0070 mm\n")
        out.write("** ----------------------------------------------------------\n")
        out.write("*STEP, NAME=Step-2, NLGEOM=NO, INC=5000\n")
        out.write("*STATIC\n0.0025, 1.0, 1.0E-07, 0.0025\n")
        out.write("*BOUNDARY\n")
        out.write("N_RP, 2, 2, 0.0070\n")
        out.write("*OUTPUT, FIELD, FREQUENCY=2\n")
        out.write("*NODE OUTPUT, NSET=N_RP\nU, RF\n")
        out.write("*NODE OUTPUT, NSET=N_BOTTOM\nRF\n")
        out.write("*NODE OUTPUT\nU\n")
        out.write("*ELEMENT OUTPUT, ELSET=umatelem\nS, MISESERI, MISESAVG, EVOL, SDV\n")
        out.write("*NODE PRINT, FREQ=1, NSET=N_RP\nU2, RF2\n")
        out.write("*END STEP\n")

    print("SUCCESS: Built coarse coupled deck at %s" % COARSE_COUPLED_INP)
    print("File size: %d bytes" % os.path.getsize(COARSE_COUPLED_INP))

if __name__ == "__main__":
    build_coarse_coupled_deck()

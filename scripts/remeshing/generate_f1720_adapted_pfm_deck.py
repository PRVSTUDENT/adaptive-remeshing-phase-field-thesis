# -*- coding: utf-8 -*-
"""
scripts/remeshing/generate_f1720_adapted_pfm_deck.py
===================================================
Task F1720 Stage 5: Assembles the 3-Layer Adapted Phase-Field Fracture Model
(PK_F1720_ADAPTED_PFM.inp) from the Primary Physical Adapted Mesh
(PK_F1720_ADAPTED_PHYS.inp).

Zero data leakage! Pure Method A: simulation runs fresh from initial undamaged state (u=0, d=0).

Architecture:
  - Layer 1: Phase field UEL (U1 for quads, U3 for tris) -> active DOF 3 (d)
  - Layer 2: Displacement UEL (U2 for quads, U4 for tris) -> active DOFs 1, 2 (ux, uy)
  - Layer 3: Standard continuum elements (CPE4 for quads, CPE3 for tris) with direct-coupled UMAT
  - Kinematic coupling of top boundary nodes to Reference Point (RP) node
"""

from __future__ import print_function
import os
import sys
import math

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
ADAPTED_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "214_f1720_adapted_mesh")
PHYS_INP = os.path.join(ADAPTED_DIR, "PK_F1720_ADAPTED_PHYS.inp")
PROD_INP = os.path.join(ADAPTED_DIR, "PK_F1720_ADAPTED_PFM.inp")

def parse_physical_mesh(phys_inp_path):
    assert os.path.exists(phys_inp_path), "Input file not found: " + phys_inp_path

    nodes = {}
    quads = {}
    tris = {}

    in_nodes = False
    in_elems = False
    current_elem_type = 'QUAD'

    with open(phys_inp_path, 'r') as f:
        for line in f:
            l = line.strip()
            if not l or l.startswith('**'):
                continue

            if l.startswith('*'):
                u = l.upper()
                if u.startswith('*NODE'):
                    in_nodes = True
                    in_elems = False
                elif u.startswith('*ELEMENT'):
                    in_nodes = False
                    in_elems = True
                    if 'CPE4' in u or 'CPS4' in u or 'QUAD' in u:
                        current_elem_type = 'QUAD'
                    elif 'CPE3' in u or 'CPS3' in u or 'TRI' in u:
                        current_elem_type = 'TRI'
                    else:
                        current_elem_type = 'QUAD'
                else:
                    in_nodes = False
                    in_elems = False
                continue

            if in_nodes:
                parts = [p.strip() for p in l.split(',') if p.strip()]
                if len(parts) >= 3:
                    try:
                        nid = int(parts[0])
                        nodes[nid] = (float(parts[1]), float(parts[2]))
                    except ValueError:
                        pass
            elif in_elems:
                parts = [p.strip() for p in l.split(',') if p.strip()]
                if len(parts) >= 4:
                    try:
                        eid = int(parts[0])
                        conn = [int(p) for p in parts[1:]]
                        if current_elem_type == 'QUAD' or len(conn) == 4:
                            quads[eid] = tuple(conn[:4])
                        else:
                            tris[eid] = tuple(conn[:3])
                    except ValueError:
                        pass

    return nodes, quads, tris

def generate_adapted_pfm_deck():
    print("=" * 80)
    print("F1720 STAGE 5: GENERATING ADAPTED PHASE-FIELD SIMULATION DECK")
    print("=" * 80)

    nodes, quads, tris = parse_physical_mesh(PHYS_INP)
    n_phys = len(quads) + len(tris)
    n_quads = len(quads)
    n_tris = len(tris)
    n_nodes = len(nodes)

    print("Physical Mesh Statistics:")
    print("  Total Elements: %d (Quads: %d, Tris: %d)" % (n_phys, n_quads, n_tris))
    print("  Total Nodes:    %d" % n_nodes)

    # Identify boundary nodes
    bottom_nodes = []
    top_nodes = []
    for nid, (x, y) in nodes.items():
        if abs(y - 0.0) < 1e-5:
            bottom_nodes.append(nid)
        elif abs(y - 1.0) < 1e-5:
            top_nodes.append(nid)

    # Reference point node
    rp_node = max(nodes.keys()) + 1
    # Pin node on bottom boundary closest to origin
    pin_candidates = [nid for nid in bottom_nodes if abs(nodes[nid][0] - 0.0) < 1e-4]
    pin_node = pin_candidates[0] if pin_candidates else min(bottom_nodes, key=lambda n: nodes[n][0])

    print("Boundary Sets:")
    print("  Bottom Nodes: %d" % len(bottom_nodes))
    print("  Top Nodes:    %d" % len(top_nodes))
    print("  Pin Node:     %d (x=%.6f, y=%.6f)" % (pin_node, nodes[pin_node][0], nodes[pin_node][1]))
    print("  RP Node:      %d at (0.5, 1.0)" % rp_node)

    with open(PROD_INP, 'w') as f:
        f.write("*HEADING\n")
        f.write("Task F1720: Five-Hole Adaptive Phase-Field Fracture Simulation (Method A)\n")
        f.write("** Specimen: Pandey & Kumar (2025) Section 4.5 Five-Hole Plate (1.0 x 1.0 mm)\n")
        f.write("** Physical Mesh: %d elements (%d quads, %d tris), %d nodes\n" % (n_phys, n_quads, n_tris, n_nodes))
        f.write("** Total Layered Elements: %d, Total Nodes: %d\n" % (3 * n_phys, n_nodes + 1))
        f.write("** ==========================================================\n")

        # User Element Declarations
        f.write("*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n3\n")
        f.write("*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n1, 2\n")
        if n_tris > 0:
            f.write("*USER ELEMENT, TYPE=U3, NODES=3, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n3\n")
            f.write("*USER ELEMENT, TYPE=U4, NODES=3, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n1, 2\n")

        # Nodes
        f.write("*NODE\n")
        for nid in sorted(nodes.keys()):
            x, y = nodes[nid]
            f.write("%d, %.9e, %.9e\n" % (nid, x, y))
        f.write("%d, 0.50000000, 1.00000000\n" % rp_node)

        # Layer 1: Phase field UEL (U1 / U3)
        if n_quads > 0:
            f.write("*ELEMENT, TYPE=U1, ELSET=PHASE_QUADS\n")
            for eid in sorted(quads.keys()):
                f.write("%d, %s\n" % (eid, ", ".join(str(n) for n in quads[eid])))
        if n_tris > 0:
            f.write("*ELEMENT, TYPE=U3, ELSET=PHASE_TRIS\n")
            for eid in sorted(tris.keys()):
                f.write("%d, %s\n" % (eid, ", ".join(str(n) for n in tris[eid])))

        # Layer 2: Displacement UEL (U2 / U4)
        offset_mech = n_phys
        if n_quads > 0:
            f.write("*ELEMENT, TYPE=U2, ELSET=MECH_QUADS\n")
            for eid in sorted(quads.keys()):
                f.write("%d, %s\n" % (eid + offset_mech, ", ".join(str(n) for n in quads[eid])))
        if n_tris > 0:
            f.write("*ELEMENT, TYPE=U4, ELSET=MECH_TRIS\n")
            for eid in sorted(tris.keys()):
                f.write("%d, %s\n" % (eid + offset_mech, ", ".join(str(n) for n in tris[eid])))

        # Layer 3: Companion Continuum Elements (CPE4 / CPE3)
        offset_comp = 2 * n_phys
        if n_quads > 0:
            f.write("*ELEMENT, TYPE=CPE4, ELSET=UMAT_QUADS\n")
            for eid in sorted(quads.keys()):
                f.write("%d, %s\n" % (eid + offset_comp, ", ".join(str(n) for n in quads[eid])))
        if n_tris > 0:
            f.write("*ELEMENT, TYPE=CPE3, ELSET=UMAT_TRIS\n")
            for eid in sorted(tris.keys()):
                f.write("%d, %s\n" % (eid + offset_comp, ", ".join(str(n) for n in tris[eid])))

        # ELSET unions
        f.write("*ELSET, ELSET=PHASE_ELEM\nPHASE_QUADS\n")
        if n_tris > 0:
            f.write("PHASE_TRIS\n")
        f.write("*ELSET, ELSET=MECH_ELEM\nMECH_QUADS\n")
        if n_tris > 0:
            f.write("MECH_TRIS\n")
        f.write("*ELSET, ELSET=umatelem\nUMAT_QUADS\n")
        if n_tris > 0:
            f.write("UMAT_TRIS\n")
        f.write("*ELSET, ELSET=All_elem\numatelem\n")

        # NSETs
        def write_nset(file_handle, set_name, id_list, max_per_line=16):
            file_handle.write("*NSET, NSET=%s\n" % set_name)
            ids_sorted = sorted(id_list)
            for i in range(0, len(ids_sorted), max_per_line):
                chunk = ids_sorted[i:i + max_per_line]
                file_handle.write("%s\n" % ", ".join(str(nid) for nid in chunk))

        write_nset(f, "N_BOTTOM", bottom_nodes)
        write_nset(f, "N_TOP", top_nodes)
        f.write("*NSET, NSET=N_RP\n%d\n" % rp_node)
        f.write("*NSET, NSET=N_PIN\n%d\n" % pin_node)

        # UEL Properties
        # l0=0.0080 mm, Gc=0.0027 kN/mm, E0=210.0 kN/mm^2, nu=0.30, k=1.0e-7, N_PHYS
        props_line = "0.0080, 0.0027, 210.0, 0.3, 1.0e-7, %.1f\n" % float(n_phys)
        f.write("*UEL PROPERTY, ELSET=PHASE_ELEM\n%s" % props_line)
        f.write("*UEL PROPERTY, ELSET=MECH_ELEM\n%s" % props_line)

        # Companion UMAT Section (Config B: dummy-scaled direct coupling, SCALE_MODE = 1.0)
        f.write("*SOLID SECTION, ELSET=umatelem, MATERIAL=UMAT_MAT\n1.0\n")
        f.write("*MATERIAL, NAME=UMAT_MAT\n")
        f.write("*USER MATERIAL, CONSTANTS=4\n")
        f.write("210.0, 0.3, %.1f, 1.0\n" % float(n_phys))
        f.write("*DEPVAR\n20\n")

        # Kinematic Coupling: Couple DOF 2 of each node in N_TOP to RP node via *EQUATION
        f.write("*EQUATION\n")
        for nid in sorted(top_nodes):
            f.write("2\n")
            f.write("%d, 2, 1.0, %d, 2, -1.0\n" % (nid, rp_node))

        # STEP 1: Pre-Critical Loading to u = 0.0050 mm
        f.write("** ----------------------------------------------------------\n")
        f.write("** STEP 1: Pre-Critical Loading to u = 0.0050 mm\n")
        f.write("** ----------------------------------------------------------\n")
        f.write("*STEP, NAME=Step-1, NLGEOM=NO, INC=2500\n")
        f.write("*STATIC\n")
        f.write("0.02, 1.0, 1.0e-8, 0.02\n")
        f.write("*BOUNDARY\n")
        f.write("N_BOTTOM, 2, 2, 0.0\n")
        f.write("N_PIN, 1, 1, 0.0\n")
        f.write("N_RP, 1, 1, 0.0\n")
        f.write("N_RP, 2, 2, 0.0050\n")
        f.write("*OUTPUT, FIELD, FREQUENCY=1\n")
        f.write("*ELEMENT OUTPUT, ELSET=umatelem\n")
        f.write("S, MISESERI, MISESAVG, EVOL, SDV\n")
        f.write("*ELEMENT OUTPUT, ELSET=PHASE_ELEM\n")
        f.write("SDV\n")
        f.write("*NODE OUTPUT, NSET=N_RP\n")
        f.write("U, RF\n")
        f.write("*OUTPUT, HISTORY\n")
        f.write("*NODE OUTPUT, NSET=N_RP\n")
        f.write("U2, RF2\n")
        f.write("*END STEP\n")

        # STEP 2: Critical Fracture Propagation to u = 0.0080 mm
        f.write("** ----------------------------------------------------------\n")
        f.write("** STEP 2: Critical Fracture Propagation to u = 0.0080 mm\n")
        f.write("** ----------------------------------------------------------\n")
        f.write("*STEP, NAME=Step-2, NLGEOM=NO, INC=5000\n")
        f.write("*STATIC\n")
        f.write("0.0025, 1.0, 1.0e-9, 0.0025\n")
        f.write("*BOUNDARY\n")
        f.write("N_BOTTOM, 2, 2, 0.0\n")
        f.write("N_PIN, 1, 1, 0.0\n")
        f.write("N_RP, 1, 1, 0.0\n")
        f.write("N_RP, 2, 2, 0.0080\n")
        f.write("*OUTPUT, FIELD, FREQUENCY=1\n")
        f.write("*ELEMENT OUTPUT, ELSET=umatelem\n")
        f.write("S, MISESERI, MISESAVG, EVOL, SDV\n")
        f.write("*ELEMENT OUTPUT, ELSET=PHASE_ELEM\n")
        f.write("SDV\n")
        f.write("*NODE OUTPUT, NSET=N_RP\n")
        f.write("U, RF\n")
        f.write("*OUTPUT, HISTORY\n")
        f.write("*NODE OUTPUT, NSET=N_RP\n")
        f.write("U2, RF2\n")
        f.write("*END STEP\n")

    print("SUCCESS: Generated %s (%d bytes)" % (PROD_INP, os.path.getsize(PROD_INP)))

if __name__ == "__main__":
    generate_adapted_pfm_deck()

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Build Small Mode-I Verification Model (64 Quads) for Controlled Parallelization Qualification.
Domain: 1.0 x 1.0 mm, sharp mathematical slit at y=0.5 (0 <= x <= 0.5 mm).
Material & PFM parameters identical to Mode-I reference:
  E = 210.0 kN/mm^2, nu = 0.3, Gc = 0.0027 kN/mm, l0 = 0.0075 mm, k = 1.0e-7
Architecture:
  Layer 1: Phase UEL (U1, DOF 3, elems 1..64)
  Layer 2: Mech UEL (U2, DOFs 1,2, elems 65..128)
  Layer 3: Companion Vis (CPE4, elems 129..192)
Loading: 5 increments to u = 0.0010 mm (Delta u = 0.0002 mm).
"""

import os
import sys

def build_mini_mode1_deck(output_dir):
    os.makedirs(output_dir, exist_ok=True)
    target_inp = os.path.join(output_dir, "PK_M1_MINI_64.inp")

    Nx = 8
    Ny = 8
    dx = 1.0 / Nx
    dy = 1.0 / Ny

    # Generate nodes
    # Grid: (Nx+1) x (Ny+1) nodes
    # At y = 0.5 (j = 4), for x in [0, 0.5] (i = 0, 1, 2, 3), duplicate nodes for upper flank
    node_coords = {}
    lower_grid = {} # (i, j) -> nid
    upper_flank = {} # i -> nid for upper flank at j = 4, i < 4

    nid = 1
    for j in range(Ny + 1):
        y = j * dy
        for i in range(Nx + 1):
            x = i * dx
            node_coords[nid] = (x, y)
            lower_grid[(i, j)] = nid
            nid += 1

    # Upper flank nodes at y = 0.5 (j = 4, x <= 0.375, i = 0, 1, 2, 3)
    for i in range(4):
        x = i * dx
        y = 0.5
        node_coords[nid] = (x, y)
        upper_flank[i] = nid
        nid += 1

    rp_nid = 999999

    # Generate elements
    # 8 x 8 = 64 quads
    quad_elems = {}
    eid = 1
    for j in range(Ny):
        for i in range(Nx):
            if j < 4:
                # Below slit: uses standard lower_grid nodes
                n1 = lower_grid[(i, j)]
                n2 = lower_grid[(i + 1, j)]
                n3 = lower_grid[(i + 1, j + 1)]
                n4 = lower_grid[(i, j + 1)]
            else:
                # Above slit:
                # Bottom edge of element is at j
                if j == 4:
                    # Bottom nodes at y = 0.5
                    n1 = upper_flank[i] if i in upper_flank else lower_grid[(i, j)]
                    n2 = upper_flank[i + 1] if (i + 1) in upper_flank else lower_grid[(i + 1, j)]
                else:
                    n1 = lower_grid[(i, j)]
                    n2 = lower_grid[(i + 1, j)]
                n3 = lower_grid[(i + 1, j + 1)]
                n4 = lower_grid[(i, j + 1)]
            quad_elems[eid] = (n1, n2, n3, n4)
            eid += 1

    num_phys_elems = len(quad_elems)
    num_phys_nodes = len(node_coords)

    # Boundary sets
    bottom_nodes = [nid_k for nid_k, (x, y) in node_coords.items() if abs(y - 0.0) < 1e-6]
    top_nodes = [nid_k for nid_k, (x, y) in node_coords.items() if abs(y - 1.0) < 1e-6]
    pin_node = [nid_k for nid_k in bottom_nodes if abs(node_coords[nid_k][0] - 0.0) < 1e-6][0]

    with open(target_inp, "w") as f:
        f.write("*Heading\n")
        f.write("** Small Mode-I Verification Model (64 Quads, 85 Nodes)\n")
        f.write("** Geometry: 1.0 x 1.0 mm, slit at y=0.5 (a0=0.5 mm)\n")
        f.write("** Material: E=210.0 kN/mm^2, nu=0.3, Gc=0.0027 kN/mm, l0=0.0075 mm, k=1.0e-7\n")
        f.write("*Preprint, echo=NO, model=NO, history=NO, contact=NO\n")
        f.write("** ==========================================================\n")
        f.write("** USER ELEMENTS (Phase U1: 1..NPHYS, Mech U2: NPHYS+1..2*NPHYS)\n")
        f.write("** ==========================================================\n")
        f.write("*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n3\n")
        f.write("*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n1, 2\n")
        f.write("** ==========================================================\n")
        f.write("** NODES\n")
        f.write("** ==========================================================\n")
        f.write("*Node\n")
        for n_id in sorted(node_coords.keys()):
            x, y = node_coords[n_id]
            f.write("%d, %.10f, %.10f\n" % (n_id, x, y))
        f.write("%d, 0.5000000000, 1.0000000000\n" % rp_nid)

        # Layer 1: Phase elements
        f.write("** ==========================================================\n")
        f.write("** LAYER 1: Phase-Field User Elements (1..%d)\n" % num_phys_elems)
        f.write("** ==========================================================\n")
        f.write("*Element, type=U1, elset=PHASE_QUADS\n")
        for e_id in sorted(quad_elems.keys()):
            conn = quad_elems[e_id]
            f.write("%d, %d, %d, %d, %d\n" % (e_id, conn[0], conn[1], conn[2], conn[3]))

        # Layer 2: Mechanical elements
        f.write("** ==========================================================\n")
        f.write("** LAYER 2: Mechanical User Elements (%d..%d)\n" % (num_phys_elems + 1, 2 * num_phys_elems))
        f.write("** ==========================================================\n")
        f.write("*Element, type=U2, elset=MECH_QUADS\n")
        for e_id in sorted(quad_elems.keys()):
            conn = quad_elems[e_id]
            f.write("%d, %d, %d, %d, %d\n" % (e_id + num_phys_elems, conn[0], conn[1], conn[2], conn[3]))

        # Layer 3: Visualization elements
        f.write("** ==========================================================\n")
        f.write("** LAYER 3: Visualization CPE4 Elements (%d..%d)\n" % (2 * num_phys_elems + 1, 3 * num_phys_elems))
        f.write("** ==========================================================\n")
        f.write("*Element, type=CPE4, elset=VIS_QUADS\n")
        for e_id in sorted(quad_elems.keys()):
            conn = quad_elems[e_id]
            f.write("%d, %d, %d, %d, %d\n" % (e_id + 2 * num_phys_elems, conn[0], conn[1], conn[2], conn[3]))

        # Sets
        f.write("*Elset, elset=umatelem\nVIS_QUADS\n")
        f.write("*Nset, nset=N_BOTTOM\n")
        f.write(", ".join(str(n) for n in sorted(bottom_nodes)) + "\n")
        f.write("*Nset, nset=N_TOP\n")
        f.write(", ".join(str(n) for n in sorted(top_nodes)) + "\n")
        f.write("*Nset, nset=N_PIN\n%d\n" % pin_node)
        f.write("*Nset, nset=N_RP\n%d\n" % rp_nid)

        # UEL Properties: l0, Gc, E, nu, k, N_phys
        f.write("*UEL PROPERTY, ELSET=PHASE_QUADS\n0.0075, 0.0027, 210.0, 0.3, 1.0e-7, %d.\n" % num_phys_elems)
        f.write("*UEL PROPERTY, ELSET=MECH_QUADS\n0.0075, 0.0027, 210.0, 0.3, 1.0e-7, %d.\n" % num_phys_elems)

        # Companion UMAT Section
        f.write("*Solid Section, elset=VIS_QUADS, material=DUMMY_MAT\n1.0\n")
        f.write("*Material, name=DUMMY_MAT\n*User Material, constants=3\n210.0, 0.3, %d.\n*Depvar\n18\n" % num_phys_elems)

        # Equations (Top tied to RP)
        f.write("** Coupling Equations for Rigid Pull\n")
        for tn in sorted(top_nodes):
            f.write("*Equation\n2\n%d, 2, 1.0, %d, 2, -1.0\n" % (tn, rp_nid))

        # Step 1: 5 increments to u = 0.0010 mm
        f.write("** ==========================================================\n")
        f.write("** STEP 1: Monotonic Tensile Loading to u = 0.0010 mm (5 incs)\n")
        f.write("** ==========================================================\n")
        f.write("*Step, name=Step-1, nlgeom=NO, inc=100\n")
        f.write("*Static\n0.2, 1.0, 1.0E-5, 0.2\n")
        f.write("*Boundary\nN_BOTTOM, 2, 2, 0.0\nN_PIN, 1, 1, 0.0\nN_TOP, 1, 1, 0.0\nN_RP, 2, 2, 0.0010\n")
        f.write("*Restart, write, frequency=0\n")
        f.write("*Output, field, frequency=1\n")
        f.write("*Node Output, nset=N_RP\nU, RF\n")
        f.write("*Node Output\nU, RF\n")
        f.write("*Element Output, elset=umatelem\nSDV, S, E\n")
        f.write("*Node Print, freq=1, nset=N_RP\nU2, RF2\n")
        f.write("*End Step\n")

    print("Created mini Mode-I verification deck:", target_inp)
    print("  Physical Nodes:", num_phys_nodes)
    print("  Physical Elements:", num_phys_elems)
    print("  Total Layered Elements:", num_phys_elems * 3)
    return target_inp

if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "models/pandey_kumar_mode1/14_mpi_qualification_small"
    build_mini_mode1_deck(out_dir)

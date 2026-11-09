#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/model_generation/assemble_hole_candidate_e10_prod_deck.py
================================================================
Deterministic generator assembling Candidate E10 physical mesh
(PK_HOLE_SEL_E10_PHYS.inp) into the authoritative 3-layer UEL production
input deck (PK_HOLE_SEL_E10_PROD.inp) for Task F1704.

Architecture:
  - Physical mesh: 9,164 physical elements (8,891 CPE4 quads, 273 CPE3 triangles)
  - 9,251 physical nodes + 1 reference point node (Node 999999 at x=0.5, y=1.0)
  - Layer 1: Phase UEL elements
      * Quads: IDs 1..8891, Type U1, Active DOF 3, NDOFEL=4
      * Tris:  IDs 8892..9164, Type U3, Active DOF 3, NDOFEL=3
  - Layer 2: Mechanical displacement UEL elements
      * Quads: IDs 9165..18055, Type U2, Active DOFs 1,2, NDOFEL=8
      * Tris:  IDs 18056..18328, Type U4, Active DOFs 1,2, NDOFEL=6
  - Layer 3: Companion visualization elements
      * Quads: IDs 18329..27219, Type CPE4
      * Tris:  IDs 27220..27492, Type CPE3
      * Material: DUMMY_MAT with zero-stress UMAT (STRESS=0, DDSDDE=1.D-11)
  - Boundary conditions:
      * Bottom roller (N_BOTTOM): uy = 0 along y = 0
      * Pinned point (N_PIN, Node 26): ux = 0 at (0, 0)
      * Top lateral restraint (N_TOP): ux = 0 along y = 1.0
      * Rigid pull constraint (*EQUATION): Each N_TOP node tied to N_RP in DOF 2
  - Loading:
      * Step 1: Linear elastic loading to uy = 0.0050 mm across 50 increments
      * Step 2: Fracture propagation to uy = 0.0150 mm across 500 increments
"""

from __future__ import print_function
import hashlib
import os
import sys
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
PHYS_PATH = REPO_ROOT / "models/pandey_kumar_mode1/176_method_a_plate_with_hole/candidates/PK_HOLE_SEL_E10_PHYS.inp"
OUTPUT_DIR = REPO_ROOT / "models/pandey_kumar_mode1/176_method_a_plate_with_hole"
PROD_PATH = OUTPUT_DIR / "PK_HOLE_SEL_E10_PROD.inp"
UEL_PATH  = REPO_ROOT / "models/pandey_kumar_mode1/f42_mixed_uel.for"
FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

# Physical Parameters
E_MOD  = 210.0     # kN/mm^2 (210 GPa)
E_NU   = 0.30      # Poisson's ratio
E_GC   = 0.0027    # kN/mm (2.7 kJ/m^2)
E_L0   = 0.0075    # mm (7.5 um)
E_K    = 1.0e-07   # Residual stiffness parameter
RP_NID = 999999    # Reference Point Node ID
RP_CRD = (0.50, 1.00)


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()


def format_nset(nodes, max_per_line=16):
    lines = []
    nodes = sorted(nodes)
    for i in range(0, len(nodes), max_per_line):
        chunk = nodes[i:i + max_per_line]
        lines.append(", ".join(str(n) for n in chunk))
    return lines


def assemble_deck():
    print("=== STARTING CANDIDATE E10 PRODUCTION DECK ASSEMBLY ===")
    assert PHYS_PATH.exists(), f"Physical mesh not found: {PHYS_PATH}"
    assert UEL_PATH.exists(), f"UEL source not found: {UEL_PATH}"
    uel_sha = sha256_file(UEL_PATH)
    assert uel_sha == FROZEN_UEL_SHA256, f"Frozen UEL SHA-256 mismatch! Found: {uel_sha}"
    print(f"Verified frozen UEL hash: {uel_sha}")

    # 1. Parse physical mesh
    nodes = {}       # nid -> (x, y)
    quad_elems = {}  # local_id -> [n1, n2, n3, n4]
    tri_elems = {}   # local_id -> [n1, n2, n3]
    mode = None

    with open(PHYS_PATH, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("**"):
                continue
            if line.startswith("*Node"):
                mode = "NODE"
                continue
            elif line.startswith("*Element, type=CPE3") or line.startswith("*Element,type=CPE3"):
                mode = "CPE3"
                continue
            elif line.startswith("*Element, type=CPE4") or line.startswith("*Element,type=CPE4"):
                mode = "CPE4"
                continue
            elif line.startswith("*"):
                mode = None
                continue

            if mode == "NODE":
                parts = [p.strip() for p in line.split(",")]
                nid = int(parts[0])
                x, y = float(parts[1]), float(parts[2])
                nodes[nid] = (x, y)
            elif mode == "CPE3":
                parts = [p.strip() for p in line.split(",")]
                eid = int(parts[0])
                nids = [int(p) for p in parts[1:]]
                tri_elems[eid] = nids
            elif mode == "CPE4":
                parts = [p.strip() for p in line.split(",")]
                eid = int(parts[0])
                nids = [int(p) for p in parts[1:]]
                quad_elems[eid] = nids

    n_nodes = len(nodes)
    n_quads = len(quad_elems)
    n_tris  = len(tri_elems)
    n_phys  = n_quads + n_tris

    print(f"Parsed Physical Mesh:")
    print(f"  Nodes: {n_nodes}")
    print(f"  Quads: {n_quads}")
    print(f"  Tris:  {n_tris}")
    print(f"  Total Physical Elements: {n_phys}")
    assert n_quads == 8891, f"Expected 8891 quads, found {n_quads}"
    assert n_tris  == 273,  f"Expected 273 tris, found {n_tris}"
    assert n_phys  == 9164, f"Expected 9164 elements, found {n_phys}"
    assert n_nodes == 9251, f"Expected 9251 nodes, found {n_nodes}"

    # 2. Identify Boundary Node Sets
    tol = 1.0e-5
    n_bottom = [nid for nid, (x, y) in nodes.items() if abs(y) < tol]
    n_top    = [nid for nid, (x, y) in nodes.items() if abs(y - 1.0) < tol]
    n_pin    = [nid for nid, (x, y) in nodes.items() if abs(x) < tol and abs(y) < tol]

    print(f"Boundary Sets:")
    print(f"  N_BOTTOM: {len(n_bottom)} nodes")
    print(f"  N_TOP:    {len(n_top)} nodes")
    print(f"  N_PIN:    {len(n_pin)} node (ID: {n_pin[0]})")
    assert len(n_pin) == 1, f"Expected exactly 1 pinned node at (0,0), found {len(n_pin)}"
    assert len(n_bottom) > 0, "No bottom nodes found"
    assert len(n_top) > 0, "No top nodes found"

    # 3. Assemble Production Deck
    lines = []
    lines.append("*HEADING")
    lines.append(f"** Production Deck: PK_HOLE_SEL_E10_PROD (Mode-I Off-Axis Circular Hole Benchmark)")
    lines.append(f"** Physical elements: {n_phys} ({n_quads} quads, {n_tris} tris), Nodes: {n_nodes}")
    lines.append(f"** Parameters: E={E_MOD} GPa, nu={E_NU:.2f}, l0={E_L0} mm, Gc={E_GC} kN/mm, k={E_K:.1e}")
    lines.append(f"** UEL Subroutine: models/pandey_kumar_mode1/f42_mixed_uel.for (SHA256: {FROZEN_UEL_SHA256})")
    lines.append("** ----------------------------------------------------------")

    # User element interfaces
    lines.append("*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM")
    lines.append("3")
    lines.append("*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM")
    lines.append("1, 2")
    lines.append("*USER ELEMENT, TYPE=U3, NODES=3, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM")
    lines.append("3")
    lines.append("*USER ELEMENT, TYPE=U4, NODES=3, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM")
    lines.append("1, 2")

    # Node Block
    lines.append("*NODE")
    for nid in sorted(nodes.keys()):
        x, y = nodes[nid]
        lines.append(f"{nid}, {x:17.10e}, {y:17.10e}")
    lines.append(f"{RP_NID}, {RP_CRD[0]:17.10e}, {RP_CRD[1]:17.10e}")

    # Layer 1: Phase Elements (JTYPE 1 for quads, JTYPE 3 for tris)
    lines.append("*ELEMENT, TYPE=U1, ELSET=PHASE_QUAD")
    for idx, (eid, conn) in enumerate(sorted(quad_elems.items()), start=1):
        lines.append(f"{idx}, {conn[0]}, {conn[1]}, {conn[2]}, {conn[3]}")

    lines.append("*ELEMENT, TYPE=U3, ELSET=PHASE_TRI")
    for idx, (eid, conn) in enumerate(sorted(tri_elems.items()), start=n_quads + 1):
        lines.append(f"{idx}, {conn[0]}, {conn[1]}, {conn[2]}")

    # Layer 2: Mechanical Elements (JTYPE 2 for quads, JTYPE 4 for tris)
    lines.append("*ELEMENT, TYPE=U2, ELSET=DISP_QUAD")
    for idx, (eid, conn) in enumerate(sorted(quad_elems.items()), start=n_phys + 1):
        lines.append(f"{idx}, {conn[0]}, {conn[1]}, {conn[2]}, {conn[3]}")

    lines.append("*ELEMENT, TYPE=U4, ELSET=DISP_TRI")
    for idx, (eid, conn) in enumerate(sorted(tri_elems.items()), start=n_phys + n_quads + 1):
        lines.append(f"{idx}, {conn[0]}, {conn[1]}, {conn[2]}")

    # Layer 3: Companion Elements (CPE4 for quads, CPE3 for tris)
    lines.append("*ELEMENT, TYPE=CPE4, ELSET=UMAT_QUADS")
    for idx, (eid, conn) in enumerate(sorted(quad_elems.items()), start=2 * n_phys + 1):
        lines.append(f"{idx}, {conn[0]}, {conn[1]}, {conn[2]}, {conn[3]}")

    lines.append("*ELEMENT, TYPE=CPE3, ELSET=UMAT_TRIS")
    for idx, (eid, conn) in enumerate(sorted(tri_elems.items()), start=2 * n_phys + n_quads + 1):
        lines.append(f"{idx}, {conn[0]}, {conn[1]}, {conn[2]}")

    # Element Sets for Visualization and Output
    lines.append(f"*ELSET, ELSET=All_elem, GENERATE")
    lines.append(f"{2 * n_phys + 1}, {3 * n_phys}, 1")
    lines.append(f"*ELSET, ELSET=umatelem, GENERATE")
    lines.append(f"{2 * n_phys + 1}, {3 * n_phys}, 1")

    # Node Sets
    lines.append("*NSET, NSET=N_BOTTOM")
    for l in format_nset(n_bottom):
        lines.append(l)

    lines.append("*NSET, NSET=N_TOP")
    for l in format_nset(n_top):
        lines.append(l)

    lines.append("*NSET, NSET=N_PIN")
    lines.append(f"{n_pin[0]}")

    lines.append("*NSET, NSET=N_RP")
    lines.append(f"{RP_NID}")

    # UEL Properties: PROPS(1..6) = (l0, Gc, E, nu, k_res, N_PHYS)
    prop_line = f"{E_L0}, {E_GC}, {E_MOD}, {E_NU:.2f}, {E_K:.1e}, {float(n_phys)}"
    lines.append("*UEL PROPERTY, ELSET=PHASE_QUAD")
    lines.append(prop_line)
    lines.append("*UEL PROPERTY, ELSET=DISP_QUAD")
    lines.append(prop_line)
    lines.append("*UEL PROPERTY, ELSET=PHASE_TRI")
    lines.append(prop_line)
    lines.append("*UEL PROPERTY, ELSET=DISP_TRI")
    lines.append(prop_line)

    # Visualization companion section and dummy material
    lines.append("*SOLID SECTION, ELSET=All_elem, MATERIAL=DUMMY_MAT")
    lines.append("1.0")
    lines.append("*MATERIAL, NAME=DUMMY_MAT")
    lines.append("*USER MATERIAL, CONSTANTS=3")
    lines.append(f"{E_MOD}, {E_NU:.2f}, {float(n_phys)}")
    lines.append("*DEPVAR")
    lines.append("20")

    # Equations tying N_TOP nodes to N_RP in DOF 2
    lines.append("** ----------------------------------------------------------")
    lines.append("** EQUATIONS (Rigid top tensile pull tied to RP in DOF 2)")
    lines.append("** ----------------------------------------------------------")
    for nid in sorted(n_top):
        lines.append("*EQUATION")
        lines.append("2")
        lines.append(f"{nid}, 2, 1.0, {RP_NID}, 2, -1.0")

    # STEP 1: Linear loading to uy = 0.0050 mm
    lines.append("** ----------------------------------------------------------")
    lines.append("** STEP 1: Linear Loading to u = 0.0050 mm")
    lines.append("** ----------------------------------------------------------")
    lines.append("*STEP, NAME=Step-1, NLGEOM=NO, INC=10000")
    lines.append("*STATIC")
    lines.append("0.02, 1.0, 1.0e-7, 0.02")
    lines.append("*BOUNDARY")
    lines.append("N_BOTTOM, 2, 2, 0.0")
    lines.append("N_PIN, 1, 1, 0.0")
    lines.append("N_TOP, 1, 1, 0.0")
    lines.append(f"N_RP, 2, 2, 0.0050")
    lines.append("*RESTART, WRITE, FREQUENCY=1")
    lines.append("*OUTPUT, FIELD, FREQUENCY=1")
    lines.append("*NODE OUTPUT, NSET=N_RP")
    lines.append("U, RF")
    lines.append("*ELEMENT OUTPUT, ELSET=umatelem")
    lines.append("MISESERI, MISESAVG, S, E, SDV")
    lines.append("*NODE PRINT, FREQ=1, NSET=N_RP")
    lines.append("U2, RF2")
    lines.append("*END STEP")

    # STEP 2: Fracture propagation to uy = 0.0150 mm
    lines.append("** ----------------------------------------------------------")
    lines.append("** STEP 2: Fracture Propagation to u = 0.0150 mm")
    lines.append("** ----------------------------------------------------------")
    lines.append("*STEP, NAME=Step-2, NLGEOM=NO, INC=20000")
    lines.append("*STATIC")
    lines.append("0.002, 1.0, 1.0e-8, 0.002")
    lines.append("*BOUNDARY")
    lines.append(f"N_RP, 2, 2, 0.0150")
    lines.append("*RESTART, WRITE, FREQUENCY=1")
    lines.append("*OUTPUT, FIELD, FREQUENCY=1")
    lines.append("*NODE OUTPUT, NSET=N_RP")
    lines.append("U, RF")
    lines.append("*ELEMENT OUTPUT, ELSET=umatelem")
    lines.append("MISESERI, MISESAVG, S, E, SDV")
    lines.append("*NODE PRINT, FREQ=1, NSET=N_RP")
    lines.append("U2, RF2")
    lines.append("*END STEP")

    # Write output file
    output_content = "\n".join(lines) + "\n"
    with open(PROD_PATH, "w") as f:
        f.write(output_content)

    prod_sha = sha256_file(PROD_PATH)
    file_size = PROD_PATH.stat().st_size
    line_count = len(lines)

    print(f"\nSuccessfully generated production deck:")
    print(f"  Path:       {PROD_PATH}")
    print(f"  Lines:      {line_count}")
    print(f"  Size:       {file_size:,} bytes")
    print(f"  SHA-256:    {prod_sha}")
    print(f"  N_PHYS:     {n_phys}")
    print(f"  N_LAYERS:   3 (Total elements = {3 * n_phys})")
    print(f"  Layer 1:    Elements 1..{n_phys} (U1/U3 phase)")
    print(f"  Layer 2:    Elements {n_phys + 1}..{2 * n_phys} (U2/U4 mech)")
    print(f"  Layer 3:    Elements {2 * n_phys + 1}..{3 * n_phys} (CPE4/CPE3 companion)")
    print(f"  Top Eqns:   {len(n_top)}")
    print("=== CANDIDATE E10 DECK GENERATION COMPLETE ===")
    return prod_sha


if __name__ == "__main__":
    assemble_deck()

# -*- coding: utf-8 -*-
"""
scripts/models/build_f1719_coarse_phase_field_model.py
======================================================
Task F1719 Phase 3:
Builds the genuine 3-layer UEL/UMAT phase-field input deck for the five-hole
perforated plate benchmark (Pandey & Kumar 2025, Section 4.5).

Source geometry:
- Authentic five-hole plate (1.0 x 1.0 mm, 5 voids).
- 2,747 physical elements (2,663 quads, 84 tris), 2,844 nodes.
- Total layered elements: 8,241 (2,747 Phase UEL + 2,747 Mech UEL + 2,747 Visualizer UMAT).

Governing material parameters:
- E = 210.0 kN/mm^2 (210 GPa)
- nu = 0.30
- Gc = 0.0027 kN/mm (2.7 N/mm)
- l0 = 0.0080 mm (8 um)
- k_res = 1.0e-7
- Amor tension-compression split

Loading:
- Step 1: Uniaxial tension to u_y = 0.0050 mm (dt = 5.0e-4, 2000 incs max)
- Step 2: Uniaxial tension to u_y = 0.0070 mm (dt = 2.0e-4, 5000 incs max)
- Full-field nodal displacements u(x, y) requested across all nodes.
- Visualizer element SDVs (SDV14=d, SDV15=deg, SDV16=H, SDV17=E_frac, SDV18=E_elas) requested.
- Zero fine-mesh data dependency!
"""

import os
import sys

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
COARSE_PHYS_INP = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "207_f1714_five_hole_benchmark", "PK_F1714_JOB1_COARSE.inp")
OUT_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "210_f1719_five_hole_coarse_pfm")
OUT_INP = os.path.join(OUT_DIR, "PK_F1719_COARSE_PFM.inp")

if not os.path.exists(OUT_DIR):
    os.makedirs(OUT_DIR)


def wrap_nset(node_list, max_per_line=16):
    lines = []
    for i in range(0, len(node_list), max_per_line):
        chunk = node_list[i:i + max_per_line]
        lines.append(", ".join(str(n) for n in chunk))
    return lines


def parse_coarse_mesh(inp_path):
    nodes = {}
    quads = {}
    tris = {}

    with open(inp_path, "r") as f:
        in_nodes = False
        in_elems_quad = False
        in_elems_tri = False

        for line in f:
            line_str = line.strip()
            if not line_str or line_str.startswith("**"):
                continue

            upper = line_str.upper()
            if upper == "*NODE" or upper.startswith("*NODE,"):
                in_nodes = True
                in_elems_quad = False
                in_elems_tri = False
                continue

            if upper.startswith("*ELEMENT, TYPE=CPE4") or upper.startswith("*ELEMENT,TYPE=CPE4"):
                in_nodes = False
                in_elems_quad = True
                in_elems_tri = False
                continue

            if upper.startswith("*ELEMENT, TYPE=CPE3") or upper.startswith("*ELEMENT,TYPE=CPE3"):
                in_nodes = False
                in_elems_quad = False
                in_elems_tri = True
                continue

            if line_str.startswith("*"):
                in_nodes = False
                in_elems_quad = False
                in_elems_tri = False
                continue

            if in_nodes:
                parts = [p.strip() for p in line_str.split(",")]
                nid = int(parts[0])
                nodes[nid] = (float(parts[1]), float(parts[2]))
            elif in_elems_quad:
                parts = [p.strip() for p in line_str.split(",") if p.strip()]
                eid = int(parts[0])
                quads[eid] = [int(p) for p in parts[1:]]
            elif in_elems_tri:
                parts = [p.strip() for p in line_str.split(",") if p.strip()]
                eid = int(parts[0])
                tris[eid] = [int(p) for p in parts[1:]]

    return nodes, quads, tris


def build():
    print("=" * 70)
    print("BUILDING GENUINE COARSE PHASE-FIELD MODEL (TASK F1719)")
    print("=" * 70)

    nodes, quads, tris = parse_coarse_mesh(COARSE_PHYS_INP)
    n_phys = len(quads) + len(tris)
    print(f"Parsed coarse mesh: {len(nodes)} nodes, {len(quads)} quads, {len(tris)} tris (total {n_phys} physical elements).")

    # Detect boundary nodes
    tol = 1.0e-5
    bottom_nodes = []
    top_nodes = []
    for nid, (x, y) in nodes.items():
        if abs(y - 0.0) < tol:
            bottom_nodes.append(nid)
        if abs(y - 1.0) < tol:
            top_nodes.append(nid)

    bottom_nodes.sort()
    top_nodes.sort()
    print(f"Boundary nodes: {len(bottom_nodes)} bottom nodes (y=0), {len(top_nodes)} top nodes (y=1).")

    # Pin node (bottom-left)
    pin_node = bottom_nodes[0]
    for nid in bottom_nodes:
        if abs(nodes[nid][0] - 0.0) < tol:
            pin_node = nid
            break

    # Master reference node
    rp_node = max(nodes.keys()) + 1
    rp_x = 0.5
    rp_y = 1.0
    print(f"Reference node ID: {rp_node} at ({rp_x}, {rp_y}). Pin node ID: {pin_node}.")

    ordered_tris = sorted(tris.items())
    ordered_quads = sorted(quads.items())
    n_tri = len(ordered_tris)
    n_quad = len(ordered_quads)

    lines = []
    lines.append("** ==========================================================")
    lines.append("** TASK F1719: GENUINE COARSE FIVE-HOLE PHASE-FIELD MODEL")
    lines.append("** Sourced directly from coarse mesh PK_F1714_JOB1_COARSE.inp")
    lines.append(f"** Physical Elements: {n_phys} (Quads: {n_quad}, Tris: {n_tri}), Nodes: {len(nodes)}")
    lines.append(f"** Layered Elements: {3 * n_phys}, Total Nodes: {len(nodes) + 1}")
    lines.append("** ZERO fine-mesh data dependency! Fully independent calculation.")
    lines.append("** ==========================================================")
    lines.append("*HEADING")
    lines.append("F1719 Coarse Phase-Field Five-Hole Simulation (Amor Split UEL/UMAT)")

    # UEL element types
    lines.append("*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM")
    lines.append("3")
    lines.append("*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM")
    lines.append("1, 2")
    lines.append("*USER ELEMENT, TYPE=U3, NODES=3, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM")
    lines.append("3")
    lines.append("*USER ELEMENT, TYPE=U4, NODES=3, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM")
    lines.append("1, 2")

    # Nodes
    lines.append("*NODE")
    for nid, (x, y) in sorted(nodes.items()):
        lines.append(f"{nid}, {x:.8e}, {y:.8e}")
    lines.append(f"{rp_node}, {rp_x:.8e}, {rp_y:.8e}")

    # LAYER 1: Phase field (U1 quads, U3 tris)
    if ordered_tris:
        lines.append("*ELEMENT, TYPE=U3, ELSET=PHASE_TRIS")
        for idx, (old_eid, enodes) in enumerate(ordered_tris):
            eid = idx + 1
            lines.append(f"{eid}, " + ", ".join(str(n) for n in enodes))

    if ordered_quads:
        lines.append("*ELEMENT, TYPE=U1, ELSET=PHASE_QUADS")
        for idx, (old_eid, enodes) in enumerate(ordered_quads):
            eid = n_tri + idx + 1
            lines.append(f"{eid}, " + ", ".join(str(n) for n in enodes))

    # LAYER 2: Mechanical displacements (U2 quads, U4 tris)
    if ordered_tris:
        lines.append("*ELEMENT, TYPE=U4, ELSET=MECH_TRIS")
        for idx, (old_eid, enodes) in enumerate(ordered_tris):
            eid = n_phys + idx + 1
            lines.append(f"{eid}, " + ", ".join(str(n) for n in enodes))

    if ordered_quads:
        lines.append("*ELEMENT, TYPE=U2, ELSET=MECH_QUADS")
        for idx, (old_eid, enodes) in enumerate(ordered_quads):
            eid = n_phys + n_tri + idx + 1
            lines.append(f"{eid}, " + ", ".join(str(n) for n in enodes))

    # LAYER 3: Visualizer companion elements (CPE4 quads, CPE3 tris)
    if ordered_tris:
        lines.append("*ELEMENT, TYPE=CPE3, ELSET=UMAT_TRIS")
        for idx, (old_eid, enodes) in enumerate(ordered_tris):
            eid = 2 * n_phys + idx + 1
            lines.append(f"{eid}, " + ", ".join(str(n) for n in enodes))

    if ordered_quads:
        lines.append("*ELEMENT, TYPE=CPE4, ELSET=UMAT_QUADS")
        for idx, (old_eid, enodes) in enumerate(ordered_quads):
            eid = 2 * n_phys + n_tri + idx + 1
            lines.append(f"{eid}, " + ", ".join(str(n) for n in enodes))

    # Element sets
    lines.append("*ELSET, ELSET=PHASE_ELEM")
    if ordered_tris:
        lines.append("PHASE_TRIS")
    if ordered_quads:
        lines.append("PHASE_QUADS")

    lines.append("*ELSET, ELSET=MECH_ELEM")
    if ordered_tris:
        lines.append("MECH_TRIS")
    if ordered_quads:
        lines.append("MECH_QUADS")

    lines.append("*ELSET, ELSET=umatelem")
    if ordered_tris:
        lines.append("UMAT_TRIS")
    if ordered_quads:
        lines.append("UMAT_QUADS")

    lines.append("*ELSET, ELSET=All_elem")
    lines.append("umatelem")

    # Boundary sets
    lines.append("*NSET, NSET=N_BOTTOM")
    for line in wrap_nset(bottom_nodes):
        lines.append(line)

    lines.append("*NSET, NSET=N_TOP")
    for line in wrap_nset(top_nodes):
        lines.append(line)

    lines.append("*NSET, NSET=N_RP")
    lines.append(f"{rp_node}")

    lines.append("*NSET, NSET=N_PIN")
    lines.append(f"{pin_node}")

    # UEL Properties
    # PROPS: l0 (0.008 mm), Gc (0.0027 kN/mm), E (210.0 kN/mm^2), nu (0.30), k (1.0e-7), N_PHYS (2747.0)
    uel_props = f"0.008000, 0.002700, 210.00, 0.30, 1.0e-07, {n_phys}.0"
    lines.append("*UEL PROPERTY, ELSET=PHASE_ELEM")
    lines.append(uel_props)
    lines.append("*UEL PROPERTY, ELSET=MECH_ELEM")
    lines.append(uel_props)

    # UMAT Section & Material
    lines.append("*SOLID SECTION, ELSET=umatelem, MATERIAL=UMAT_MAT")
    lines.append("1.0")
    lines.append("*MATERIAL, NAME=UMAT_MAT")
    lines.append("*USER MATERIAL, CONSTANTS=3")
    lines.append(f"210.00, 0.30, {n_phys}.0")
    lines.append("*DEPVAR")
    lines.append("20")

    # MPC Kinematic equations linking top edge to N_RP
    lines.append("*EQUATION")
    for top_nid in top_nodes:
        lines.append("2")
        lines.append(f"{top_nid}, 2, 1.0, {rp_node}, 2, -1.0")

    # STEP 1: Linear elastic loading up to u_y = 0.0050 mm
    lines.append("** ----------------------------------------------------------")
    lines.append("** STEP 1: Linear elastic loading to u_y = 0.0050 mm (50 incs)")
    lines.append("** ----------------------------------------------------------")
    lines.append("*STEP, NAME=Step-1, NLGEOM=NO, INC=1000")
    lines.append("*STATIC")
    lines.append("0.02, 1.0, 1.0E-07, 0.02")
    lines.append("*BOUNDARY")
    lines.append("N_BOTTOM, 2, 2, 0.0")
    lines.append("N_PIN, 1, 1, 0.0")
    lines.append("N_RP, 1, 1, 0.0")
    lines.append("N_RP, 2, 2, 0.0050")
    lines.append("*OUTPUT, FIELD, FREQUENCY=5")
    lines.append("*NODE OUTPUT, NSET=N_RP")
    lines.append("U, RF")
    lines.append("*NODE OUTPUT, NSET=N_BOTTOM")
    lines.append("RF")
    lines.append("*NODE OUTPUT")
    lines.append("U")
    lines.append("*ELEMENT OUTPUT, ELSET=All_elem")
    lines.append("SDV")
    lines.append("*NODE PRINT, FREQ=1, NSET=N_RP")
    lines.append("U2, RF2")
    lines.append("*END STEP")

    # STEP 2: Tension up to u_y = 0.0070 mm (capturing localization)
    lines.append("** ----------------------------------------------------------")
    lines.append("** STEP 2: Tension to u_y = 0.0070 mm (capturing localization)")
    lines.append("** ----------------------------------------------------------")
    lines.append("*STEP, NAME=Step-2, NLGEOM=NO, INC=5000")
    lines.append("*STATIC")
    lines.append("0.0025, 1.0, 1.0E-07, 0.0025")
    lines.append("*BOUNDARY")
    lines.append("N_RP, 2, 2, 0.0070")
    lines.append("*OUTPUT, FIELD, FREQUENCY=2")
    lines.append("*NODE OUTPUT, NSET=N_RP")
    lines.append("U, RF")
    lines.append("*NODE OUTPUT, NSET=N_BOTTOM")
    lines.append("RF")
    lines.append("*NODE OUTPUT")
    lines.append("U")
    lines.append("*ELEMENT OUTPUT, ELSET=All_elem")
    lines.append("SDV")
    lines.append("*NODE PRINT, FREQ=1, NSET=N_RP")
    lines.append("U2, RF2")
    lines.append("*END STEP")

    with open(OUT_INP, "w") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Saved coarse phase-field input deck to: {OUT_INP}")
    print(f"Total lines: {len(lines)}, size: {os.path.getsize(OUT_INP)} bytes.")
    print("=" * 70)


if __name__ == "__main__":
    build()

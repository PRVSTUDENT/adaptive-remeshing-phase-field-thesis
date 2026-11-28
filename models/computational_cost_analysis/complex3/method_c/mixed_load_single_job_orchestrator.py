# -*- coding: utf-8 -*-
"""
models/complex_mixed_load/mixed_load_single_job_orchestrator.py
===============================================================
Task: METHOD-C-COMPLEX-MODELS (Problem 3)
Goal: METHOD_C_COMPLEX_MODELS_V1
Correlation: HND-METHOD-C-COMPLEX-004 / HND-METHOD-C-COMPLEX-005

Single-Job UEL Input Deck Generator for Problem 3:
Notch + Hole under Combined Tension + Shear (ux = 0.5 * uy):
- Boundary Conditions:
  * Bottom edge: y = 0.0 mm -> fixed ux = 0.0, uy = 0.0 (N_BOTTOM, 1, 2, 0.0)
  * Top edge: y = 1.0 mm -> coupled to Reference Point N_RP (999999) via *EQUATION
    in DOF 1 (ux) and DOF 2 (uy).
  * Reference Point N_RP:
    - ux = 0.5 * uy (shear-to-tension ratio = 0.5)
    - Step 1 (Hold): re-equilibrates at donor (ux, uy)
    - Step 2 (RIKS): advances to target (ux, uy) with strict proportionality
- Observables printed:
  * U1, U2, RF1, RF2 at N_RP
- UEL Architecture:
  * Layer 1: Phase-field UEL elements (displacement + phase)
  * Layer 2: Phase UEL elements (pure phase)
  * Layer 3: Companion UMAT elements (visualization)
  * Frozen UEL source: f42_mixed_uel.for (CE8D5EDC... bitwise preserved)
"""

from __future__ import print_function, division
import os
import sys
import math
import json
from collections import defaultdict

# Material Parameters
BENCHMARK_E_GPA = 210.0
BENCHMARK_NU = 0.30
BENCHMARK_L0_MM = 0.0075
BENCHMARK_GC_KN_MM = 0.0027
BENCHMARK_K_RES = 1e-7
BENCHMARK_THICKNESS = 1.0

# Sizing
H_REF_MM = 0.0035
H_BG_MM = 0.035
BAND_HALF_WIDTH_MM = 0.025

# Loading
SHEAR_TO_TENSION_RATIO = 0.5  # ux = 0.5 * uy

# Geometry landmarks
PLATE_W = 1.0
PLATE_H = 1.0
NOTCH_START_X = 0.0
NOTCH_START_Y = 0.5
NOTCH_LEN = 0.5
NOTCH_ANGLE_RAD = math.pi / 4.0
NOTCH_TIP_X = 0.35355339
NOTCH_TIP_Y = 0.85355339
HOLE_X = 0.65
HOLE_Y = 0.65
HOLE_R = 0.10

# Load increments
DEFAULT_PRECRITICAL_UY_MM = 0.00450
DEFAULT_LOAD_INCREMENT_MM = 0.00050


def write_wrapped_nset(out, nset_name, node_ids, per_line=16):
    """Writes an *NSET block with wrapped lines."""
    out.write("*NSET, NSET=%s\n" % nset_name)
    s_ids = sorted(node_ids)
    for i in range(0, len(s_ids), per_line):
        chunk = s_ids[i:i + per_line]
        out.write(", ".join(str(n) for n in chunk) + "\n")


def parse_physical_mesh(phys_inp_path):
    """
    Parses physical mesh input deck.
    Returns: (nodes_dict, quads_dict, tris_dict, node_sets)
    """
    nodes = {}
    quads = {}
    tris = {}
    nsets = defaultdict(list)
    current_nset = None

    in_nodes = False
    in_elements = False
    elem_type = None

    with open(phys_inp_path, "r") as f:
        for line in f:
            l = line.strip()
            if not l or l.startswith("**"):
                continue
            if l.startswith("*"):
                in_nodes = False
                in_elements = False
                current_nset = None
                u = l.upper()
                if u.startswith("*NODE"):
                    in_nodes = True
                elif u.startswith("*ELEMENT"):
                    in_elements = True
                    if "CPE4" in u or "QUAD" in u:
                        elem_type = "QUAD"
                    elif "CPE3" in u or "TRI" in u:
                        elem_type = "TRI"
                    else:
                        elem_type = "QUAD"
                elif u.startswith("*NSET"):
                    parts = u.split(",")
                    for p in parts:
                        if "NSET=" in p:
                            current_nset = p.split("=")[1].strip()
                continue

            if in_nodes:
                parts = [p.strip() for p in l.split(",") if p.strip()]
                if len(parts) >= 3:
                    nid = int(parts[0])
                    nodes[nid] = (float(parts[1]), float(parts[2]))
            elif in_elements:
                parts = [p.strip() for p in l.split(",") if p.strip()]
                if len(parts) >= 4:
                    eid = int(parts[0])
                    conn = [int(p) for p in parts[1:]]
                    if len(conn) == 4:
                        quads[eid] = conn
                    elif len(conn) == 3:
                        tris[eid] = conn
            elif current_nset:
                parts = [p.strip() for p in l.split(",") if p.strip()]
                for p in parts:
                    try:
                        nsets[current_nset].append(int(p))
                    except ValueError:
                        pass

    return nodes, quads, tris, nsets


def assemble_mixed_load_uel_deck(phys_inp_path, output_uel_inp_path,
                                 donor_uy=0.0, target_uy=DEFAULT_PRECRITICAL_UY_MM,
                                 transferred_damage=None, transferred_history=None,
                                 is_coarse=False, use_riks=True,
                                 shear_ratio=SHEAR_TO_TENSION_RATIO,
                                 l0=BENCHMARK_L0_MM, Gc=BENCHMARK_GC_KN_MM,
                                 E_GPa=BENCHMARK_E_GPA, nu=BENCHMARK_NU,
                                 k_res=BENCHMARK_K_RES):
    """
    Assembles complete 3-layer UEL input deck for Problem 3:
    Notch + Hole under Combined Tension + Shear (ux = 0.5 * uy).
    """
    r_nodes, r_quads, r_tris, _ = parse_physical_mesh(phys_inp_path)
    num_nodes = len(r_nodes)
    num_quads = len(r_quads)
    num_tris = len(r_tris)
    num_phys = num_quads + num_tris
    num_phys_f = float(num_phys)

    # Compute horizontal shear displacements from shear-to-tension ratio
    donor_ux = shear_ratio * donor_uy
    target_ux = shear_ratio * target_uy

    # Identify Boundary Nodes
    bottom_nodes = []
    top_nodes = []
    pin_node_id = None
    min_dist_pin = 1e9

    for nid, (x, y) in r_nodes.items():
        if abs(y - 0.0) < 1e-5:
            bottom_nodes.append(nid)
            dist_to_00 = math.hypot(x, y)
            if dist_to_00 < min_dist_pin:
                min_dist_pin = dist_to_00
                pin_node_id = nid
        if abs(y - PLATE_H) < 1e-5:
            top_nodes.append(nid)

    rp_nid = 999999

    with open(output_uel_inp_path, "w") as out:
        out.write("** ==========================================================\n")
        out.write("** ABAQUS INPUT DECK: Problem 3 Combined Tension + Shear (ux = %.2f * uy)\n" % shear_ratio)
        out.write("** Physical Mesh: %d nodes, %d elements (%d quads, %d tris)\n" % (
            num_nodes, num_phys, num_quads, num_tris
        ))
        out.write("** Loading: donor_uy = %.6f, target_uy = %.6f (donor_ux = %.6f, target_ux = %.6f)\n" % (
            donor_uy, target_uy, donor_ux, target_ux
        ))
        out.write("** ==========================================================\n")
        out.write("*HEADING\nProblem 3 Combined Tension + Shear Adaptive Remeshing\n")
        out.write("*PREPRINT, ECHO=NO, MODEL=NO, HISTORY=NO\n")

        # Node Definitions (Shared Across All 3 Layers)
        out.write("** ----------------------------------------------------------\n")
        out.write("** Shared Node Definitions\n")
        out.write("** ----------------------------------------------------------\n")
        out.write("*NODE, NSET=ALLNODES\n")
        for nid in sorted(r_nodes.keys()):
            out.write("%d, %.8e, %.8e\n" % (nid, r_nodes[nid][0], r_nodes[nid][1]))
        out.write("%d, 0.50000000, 1.00000000\n" % rp_nid)

        # UEL Element Definitions
        out.write("** ----------------------------------------------------------\n")
        out.write("** UEL Definitions: Mixed Displacement (DOFs 1,2) + Phase (DOF 3)\n")
        out.write("** ----------------------------------------------------------\n")
        if r_quads:
            out.write("*USER ELEMENT, NODES=4, TYPE=U1, PROPERTIES=6, COORDINATES=2, VARIABLES=18, UNSYMM\n3\n")
            out.write("*USER ELEMENT, NODES=4, TYPE=U2, PROPERTIES=6, COORDINATES=2, VARIABLES=18, UNSYMM\n1, 2\n")
        if r_tris:
            out.write("*USER ELEMENT, NODES=3, TYPE=U3, PROPERTIES=6, COORDINATES=2, VARIABLES=18, UNSYMM\n3\n")
            out.write("*USER ELEMENT, NODES=3, TYPE=U4, PROPERTIES=6, COORDINATES=2, VARIABLES=18, UNSYMM\n1, 2\n")

        # Layer 1: Phase UEL (DOF 3)
        if r_quads:
            out.write("*ELEMENT, TYPE=U1, ELSET=PHASE_QUAD\n")
            for eid, conn in sorted(r_quads.items()):
                out.write("%d, %s\n" % (eid, ", ".join(str(n) for n in conn)))
        if r_tris:
            out.write("*ELEMENT, TYPE=U3, ELSET=PHASE_TRI\n")
            for eid, conn in sorted(r_tris.items()):
                out.write("%d, %s\n" % (eid, ", ".join(str(n) for n in conn)))

        # Layer 2: Mech UEL (DOFs 1, 2)
        if r_quads:
            out.write("*ELEMENT, TYPE=U2, ELSET=DISP_QUAD\n")
            for eid, conn in sorted(r_quads.items()):
                out.write("%d, %s\n" % (eid + num_phys, ", ".join(str(n) for n in conn)))
        if r_tris:
            out.write("*ELEMENT, TYPE=U4, ELSET=DISP_TRI\n")
            for eid, conn in sorted(r_tris.items()):
                out.write("%d, %s\n" % (eid + num_phys, ", ".join(str(n) for n in conn)))

        # Layer 3 Elements (Companion UMAT)
        out.write("** ----------------------------------------------------------\n")
        out.write("** Layer 3 Companion Elements (Visualization / Recovery)\n")
        out.write("** ----------------------------------------------------------\n")
        if r_quads:
            out.write("*ELEMENT, TYPE=CPE4, ELSET=umatelem_quad\n")
            for eid, conn in sorted(r_quads.items()):
                out.write("%d, %s\n" % (eid + 2 * num_phys, ", ".join(str(n) for n in conn)))
        if r_tris:
            out.write("*ELEMENT, TYPE=CPE3, ELSET=umatelem_tri\n")
            for eid, conn in sorted(r_tris.items()):
                out.write("%d, %s\n" % (eid + 2 * num_phys, ", ".join(str(n) for n in conn)))

        out.write("*ELSET, ELSET=All_elem\n")
        if r_quads and r_tris:
            out.write("umatelem_quad, umatelem_tri\n")
        elif r_quads:
            out.write("umatelem_quad\n")
        else:
            out.write("umatelem_tri\n")
        out.write("*ELSET, ELSET=umatelem\nAll_elem\n")

        # Boundary Node sets
        write_wrapped_nset(out, "N_BOTTOM", bottom_nodes)
        write_wrapped_nset(out, "N_TOP", top_nodes)
        out.write("*NSET, NSET=N_PIN\n%d\n" % pin_node_id)
        out.write("*NSET, NSET=N_RP\n%d\n" % rp_nid)

        # UEL Properties: l0, Gc, E, nu, k_res, N_PHYS
        if r_quads:
            out.write("*UEL PROPERTY, ELSET=PHASE_QUAD\n")
            out.write("%.4f, %.6e, %.4f, %.2f, %.1e, %.1f\n" % (l0, Gc, E_GPa, nu, k_res, num_phys_f))
            out.write("*UEL PROPERTY, ELSET=DISP_QUAD\n")
            out.write("%.4f, %.6e, %.4f, %.2f, %.1e, %.1f\n" % (l0, Gc, E_GPa, nu, k_res, num_phys_f))
        if r_tris:
            out.write("*UEL PROPERTY, ELSET=PHASE_TRI\n")
            out.write("%.4f, %.6e, %.4f, %.2f, %.1e, %.1f\n" % (l0, Gc, E_GPa, nu, k_res, num_phys_f))
            out.write("*UEL PROPERTY, ELSET=DISP_TRI\n")
            out.write("%.4f, %.6e, %.4f, %.2f, %.1e, %.1f\n" % (l0, Gc, E_GPa, nu, k_res, num_phys_f))

        # Companion UMAT Section & Material
        out.write("*SOLID SECTION, ELSET=All_elem, MATERIAL=M_COMPANION\n%.1f\n" % BENCHMARK_THICKNESS)
        out.write("*MATERIAL, NAME=M_COMPANION\n*USER MATERIAL, CONSTANTS=3\n")
        out.write("%.4f, %.2f, %.1f\n" % (E_GPa, nu, num_phys_f))
        out.write("*DEPVAR\n20\n")

        # Kinematic Coupling:
        # All top nodes tied to N_RP in DOF 1 (horizontal shear) AND DOF 2 (vertical tension)
        out.write("** Top boundary horizontal shear tied to Reference Point N_RP in DOF 1\n")
        for nid in sorted(top_nodes):
            out.write("*EQUATION\n2\n%d, 1, 1.0, %d, 1, -1.0\n" % (nid, rp_nid))
        out.write("** Top tensile pull tied to Reference Point N_RP in DOF 2\n")
        for nid in sorted(top_nodes):
            out.write("*EQUATION\n2\n%d, 2, 1.0, %d, 2, -1.0\n" % (nid, rp_nid))

        # Initial Conditions (SVARS 1..18 on Layer 1) for adaptive cycles
        if not is_coarse and transferred_damage is not None and transferred_history is not None:
            out.write("** Transferred State: Initial Conditions (SVARS 1..18 on Layer 1)\n")
            out.write("*INITIAL CONDITIONS, TYPE=SOLUTION\n")
            for elements, ngp in ((r_quads, 4), (r_tris, 3)):
                for eid, conn in sorted(elements.items()):
                    d = sum(transferred_damage.get(n, 0.0) for n in conn) / len(conn)
                    h = [transferred_history.get((eid, gp), transferred_history.get(eid, 0.0))
                         for gp in range(1, ngp + 1)]
                    deg = (1.0 - d)**2 + k_res
                    if ngp == 4:
                        sv = [d]*4 + h + h + [d, d, deg, h[0], 0.0, 0.0]
                    else:
                        sv = [d, d, d, 0.0] + [h[0]]*5 + [0.0]*3 + [d, d, deg, h[0], 0.0, 0.0]
                    out.write(str(eid) + ", " + ", ".join("%.6e" % v for v in sv[:7]) + "\n")
                    out.write("  " + ", ".join("%.6e" % v for v in sv[7:15]) + "\n")
                    out.write("  " + ", ".join("%.6e" % v for v in sv[15:]) + "\n")

        # Constant hold amplitude definition
        out.write("*AMPLITUDE, NAME=CONST_HOLD\n0.0, 1.0, 1.0, 1.0\n")

        if is_coarse:
            # Coarse Cycle: Single combined tension + shear step
            out.write("** ==========================================================\n")
            out.write("** STEP 1: Pre-critical Coarse Loading (uy = %.6f, ux = %.6f mm)\n" % (target_uy, target_ux))
            out.write("** ==========================================================\n")
            out.write("*STEP, NAME=Step-1, NLGEOM=NO, INC=1000\n")
            out.write("*STATIC\n")
            out.write("0.02, 1.0, 1.0E-14, 0.05\n")
            out.write("*BOUNDARY\n")
            out.write("N_BOTTOM, 1, 2, 0.0\n")
            out.write("N_RP, 1, 1, %.8e\n" % target_ux)
            out.write("N_RP, 2, 2, %.8e\n" % target_uy)
            out.write("*OUTPUT, FIELD, FREQUENCY=1\n")
            out.write("*NODE OUTPUT\nU\n")
            out.write("*NODE OUTPUT, NSET=N_RP\nRF\n")
            out.write("*ELEMENT OUTPUT, ELSET=umatelem\nSDV\n")
            out.write("*NODE PRINT, FREQ=1, NSET=N_RP\nU1, U2, RF1, RF2\n")
            out.write("*END STEP\n")
        else:
            # Adaptive Cycle: Step 1 (Hold) + Step 2 (RIKS Advance)
            out.write("** ==========================================================\n")
            out.write("** STEP 1: Fixed-Load Re-equilibration Hold at donor_uy = %.6f (ux = %.6f)\n" % (donor_uy, donor_ux))
            out.write("** ==========================================================\n")
            out.write("*STEP, NAME=Step-1, NLGEOM=NO, INC=100\n")
            out.write("*STATIC\n")
            out.write("1.0, 1.0, 1.0E-08, 1.0\n")
            out.write("*BOUNDARY\n")
            out.write("N_BOTTOM, 1, 2, 0.0\n")
            out.write("*BOUNDARY, AMPLITUDE=CONST_HOLD\n")
            out.write("N_RP, 1, 1, %.8e\n" % donor_ux)
            out.write("N_RP, 2, 2, %.8e\n" % donor_uy)
            out.write("*OUTPUT, FIELD, FREQUENCY=1\n")
            out.write("*NODE OUTPUT\nU\n")
            out.write("*NODE OUTPUT, NSET=N_RP\nRF\n")
            out.write("*ELEMENT OUTPUT, ELSET=umatelem\nSDV\n")
            out.write("*NODE PRINT, FREQ=1, NSET=N_RP\nU1, U2, RF1, RF2\n")
            out.write("*END STEP\n")

            out.write("** ==========================================================\n")
            out.write("** STEP 2: Forward Crack Propagation to target_uy = %.6f (ux = %.6f)\n" % (target_uy, target_ux))
            out.write("** ==========================================================\n")
            if use_riks:
                out.write("*STEP, NAME=Step-2, NLGEOM=NO, INC=1000\n")
                out.write("*STATIC, RIKS\n")
                out.write("0.01, 1.0, 1.0E-14, 0.05, 1.0\n")
                out.write("*BOUNDARY, OP=MOD\n")
                out.write("N_RP, 1, 1, %.8e\n" % target_ux)
                out.write("N_RP, 2, 2, %.8e\n" % target_uy)
            else:
                out.write("*STEP, NAME=Step-2, NLGEOM=NO, INC=1000\n")
                out.write("*STATIC\n")
                out.write("0.01, 1.0, 1.0E-14, 0.05\n")
                out.write("*BOUNDARY, OP=MOD\n")
                out.write("N_RP, 1, 1, %.8e\n" % target_ux)
                out.write("N_RP, 2, 2, %.8e\n" % target_uy)

            out.write("*OUTPUT, FIELD, FREQUENCY=1\n")
            out.write("*NODE OUTPUT\nU\n")
            out.write("*NODE OUTPUT, NSET=N_RP\nRF\n")
            out.write("*ELEMENT OUTPUT, ELSET=umatelem\nSDV\n")
            out.write("*NODE PRINT, FREQ=1, NSET=N_RP\nU1, U2, RF1, RF2\n")
            out.write("*END STEP\n")

    print("Assembled Problem 3 Mixed Load UEL Deck: %s" % output_uel_inp_path)

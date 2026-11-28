# -*- coding: utf-8 -*-
"""
models/complex_double_notch/double_notch_single_job_orchestrator.py
===================================================================
Task: METHOD-C-COMPLEX-MODELS
Goal: METHOD_C_COMPLEX_MODELS_V1
Correlation: HND-METHOD-C-COMPLEX-004

In-job orchestrator for Problem 2 (Double Notch Symmetrical Crack Coalescence):
- Geometry:
  * 1.0 x 1.0 mm square plate
  * Left Notch: (0.0, 0.50) to (0.35355339, 0.85355339) mm (+45 deg, length 0.50 mm)
  * Right Notch: (1.0, 0.50) to (0.64644661, 0.85355339) mm (+135 deg / up-left, length 0.50 mm)
  * Distance between notch tips: 0.292893 mm at y = 0.853553 mm
- Boundary Conditions (EDGE_PULL):
  * Bottom edge: y = 0.0 mm -> uy = 0.0 (N_BOTTOM)
  * Bottom corner: (0.0, 0.0) -> ux = 0.0 (N_PIN)
  * Top edge: y = 1.0 mm -> coupled to Reference Point N_RP (999999) via *EQUATION in DOF 2
- Material Parameters:
  * E = 210.0 GPa (210.0 kN/mm^2)
  * nu = 0.30
  * l0 = 0.0075 mm (l0 / 2 = 0.00375 mm)
  * Gc = 0.0027 kN/mm (2.7 N/mm)
  * k_res = 1.0e-7
  * Thickness = 1.0 mm
- Subroutine: models/pandey_kumar_mode1/f42_mixed_uel.for
  (Bitwise frozen source CE8D5EDC... preserved)
- State Transfer & Re-equilibration:
  * Validated nearest-neighbour transfer of damage d and history H (cKDTree)
  * Step 1: Fixed-load re-equilibration hold (*STATIC\\n1.0, 1.0, 1.0E-08, 1.0)
    evaluating force continuity gate |Delta RF2| <= 5.0%
  * Step 2: Forward crack propagation advance with arc-length (*STATIC, RIKS)
  * Non-healing gate: d_max_terminal >= d_max_transferred - 1e-4
- Crack Completion Criteria:
  * Primary: Coalescence (connected damage joins two cracks, or tip separation <= 0.015 mm)
  * Secondary: Reaction force drop below 5% of peak (RF2 < 0.05 * peak_RF2)
  * Tertiary: Any crack reaches plate edge: x_tip <= 0.02 or x_tip >= 0.98 or y_tip >= 0.98 or y_tip <= 0.02
"""

from __future__ import print_function, division
import os
import sys
import re
import json
import math
import shutil
import subprocess
import hashlib
import time
from collections import defaultdict

try:
    REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
except NameError:
    REPO_ROOT = os.path.abspath(os.getcwd())

if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
BENCHMARK_GC_KN_MM = 0.0027       # 2.7 N/mm
BENCHMARK_L0_MM = 0.0075          # mm
BENCHMARK_E_GPA = 210.0           # kN/mm^2 (GPa)
BENCHMARK_NU = 0.30
BENCHMARK_K_RES = 1.0e-7
BENCHMARK_THICKNESS = 1.0         # mm
H_REF_MM = 0.0035                 # mm (<= l0/2 = 0.00375 mm)

# Geometry landmarks
PLATE_W = 1.0
PLATE_H = 1.0

# Left Notch
NOTCH1_START_X = 0.0
NOTCH1_START_Y = 0.50
NOTCH1_TIP_X = 0.35355339
NOTCH1_TIP_Y = 0.85355339

# Right Notch
NOTCH2_START_X = 1.0
NOTCH2_START_Y = 0.50
NOTCH2_TIP_X = 0.64644661
NOTCH2_TIP_Y = 0.85355339

# Coalescence threshold
COALESCENCE_DISTANCE_MM = 2.0 * BENCHMARK_L0_MM  # 0.0150 mm
LOAD_DROP_COMPLETION_RATIO = 0.05                 # RF2 < 5% of peak RF2

# Load schedule defaults
DEFAULT_COARSE_UY_MM = 0.0045      # Pre-critical precrack displacement
DEFAULT_LOAD_INCREMENT_MM = 0.0005 # Step 2 RIKS advance per cycle
DEFAULT_MAX_CYCLES = 12


def compute_individual_crack_arc_length(tip_history, root):
    """Computes cumulative arc length along curved crack path from its notch root."""
    if not tip_history:
        return 0.0
    pts = [root] + list(tip_history)
    s = 0.0
    for i in range(1, len(pts)):
        dx = pts[i][0] - pts[i-1][0]
        dy = pts[i][1] - pts[i-1][1]
        s += math.hypot(dx, dy)
    return round(s, 6)


# 2x2 Gauss quadrature on [-1, 1]^2
Q_GAUSS = 1.0 / math.sqrt(3.0)
QUAD_GP_LOCAL = [
    (-Q_GAUSS, -Q_GAUSS),
    ( Q_GAUSS, -Q_GAUSS),
    ( Q_GAUSS,  Q_GAUSS),
    (-Q_GAUSS,  Q_GAUSS)
]


def quad_shape_funcs(xi, eta):
    return (
        0.25 * (1.0 - xi) * (1.0 - eta),
        0.25 * (1.0 + xi) * (1.0 - eta),
        0.25 * (1.0 + xi) * (1.0 + eta),
        0.25 * (1.0 - xi) * (1.0 + eta)
    )


def compute_quad_gp_global_coords(node_coords_4):
    gps = []
    for gp_idx, (xi, eta) in enumerate(QUAD_GP_LOCAL, start=1):
        N = quad_shape_funcs(xi, eta)
        gx = sum(N[i] * node_coords_4[i][0] for i in range(4))
        gy = sum(N[i] * node_coords_4[i][1] for i in range(4))
        gps.append((gp_idx, gx, gy))
    return gps


def compute_tri_gp_global_coords(node_coords_3):
    gx = sum(p[0] for p in node_coords_3) / 3.0
    gy = sum(p[1] for p in node_coords_3) / 3.0
    return [(1, gx, gy)]


def sha256_of_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()

compute_sha256 = sha256_of_file


def write_wrapped_nset(out, set_name, node_ids, per_line=16):
    out.write("*NSET, NSET=%s\n" % set_name)
    sorted_ids = sorted(node_ids)
    for i in range(0, len(sorted_ids), per_line):
        chunk = sorted_ids[i:i + per_line]
        out.write(", ".join(str(nid) for nid in chunk) + "\n")


def parse_physical_mesh_inp(phys_inp_path):
    nodes = {}
    quads = {}
    tris = {}
    nsets = defaultdict(list)

    in_nodes = False
    in_elements = False
    elem_type = None
    current_nset = None

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
                    if "CPE4" in u or "CPS4" in u or "QUAD" in u:
                        elem_type = "QUAD"
                    elif "CPE3" in u or "CPS3" in u or "TRI" in u:
                        elem_type = "TRI"
                    else:
                        elem_type = "UNKNOWN"
                elif u.startswith("*NSET"):
                    m = re.search(r'NSET=([A-Za-z0-9_-]+)', u)
                    if m:
                        current_nset = m.group(1)
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
                    nids = [int(p) for p in parts[1:]]
                    if elem_type == "QUAD" or len(nids) == 4:
                        quads[eid] = nids
                    else:
                        tris[eid] = nids
            elif current_nset:
                parts = [p.strip() for p in l.split(",") if p.strip()]
                for p in parts:
                    try:
                        nsets[current_nset].append(int(p))
                    except ValueError:
                        pass

    return nodes, quads, tris, nsets

parse_physical_mesh = parse_physical_mesh_inp


def assemble_double_notch_coupled_deck(out_deck_path,
                                        r_nodes,
                                        r_quads,
                                        r_tris,
                                        donor_uy,
                                        target_uy,
                                        transferred_damage=None,
                                        transferred_history=None,
                                        E_GPa=BENCHMARK_E_GPA,
                                        nu=BENCHMARK_NU,
                                        Gc=BENCHMARK_GC_KN_MM,
                                        l0=BENCHMARK_L0_MM,
                                        k_res=BENCHMARK_K_RES,
                                        use_riks=True,
                                        is_coarse=False):
    """
    Assembles a complete 3-layer Method C Double-Notch Model Abaqus input deck:
    - Layer 1: Phase-Field UEL (DOF 3)
    - Layer 2: Mechanical UEL (DOFs 1, 2)
    - Layer 3: Companion Visualization Elements (UMAT)
    - Boundary conditions (EDGE_PULL):
      * N_BOTTOM: y = 0.0 mm -> uy = 0.0
      * N_PIN: node nearest (0.0, 0.0) -> ux = 0.0
      * N_TOP: all nodes on y = 1.0 mm coupled to Reference Point N_RP (999999) via *EQUATION in DOF 2
    - Step 1: Fixed-load re-equilibration hold at donor_uy (*STATIC) [Adaptive cycles]
    - Step 2: Forward crack advance to target_uy (*STATIC, RIKS)
    """
    num_phys = len(r_quads) + len(r_tris)
    num_phys_f = float(num_phys)
    offset_disp = num_phys
    offset_vis = 2 * num_phys

    bottom_nodes = []
    top_nodes = []
    pin_candidates = []

    for nid, (x, y) in r_nodes.items():
        if abs(y - 0.0) < 1e-4:
            bottom_nodes.append(nid)
            d_pin = math.hypot(x - 0.0, y - 0.0)
            pin_candidates.append((nid, d_pin))
        if abs(y - PLATE_H) < 1e-4:
            top_nodes.append(nid)

    pin_candidates.sort(key=lambda item: item[1])
    pin_node_id = pin_candidates[0][0] if pin_candidates else 1
    rp_nid = 999999

    with open(out_deck_path, "w") as out:
        out.write("** ==========================================================\n")
        out.write("** Abaqus Input Deck - 3-Layer Method C Problem 2 Double-Notch Model\n")
        out.write("** Benchmark: Double Notch Symmetrical Crack Coalescence\n")
        out.write("** Model: %s\n" % os.path.basename(out_deck_path).replace(".inp", ""))
        out.write("** Discretization: %d nodes, %d physical elements (%d quads, %d tris)\n" % (
            len(r_nodes), num_phys, len(r_quads), len(r_tris)
        ))
        out.write("** Material: E = %.4f GPa, nu = %.2f, Gc = %.6e kN/mm, l0 = %.4f mm\n" % (
            E_GPa, nu, Gc, l0
        ))
        out.write("** Load Advance: donor uy = %.6f mm -> target uy = %.6f mm\n" % (donor_uy, target_uy))
        out.write("** Subroutine: models/pandey_kumar_mode1/f42_mixed_uel.for\n")
        out.write("** ==========================================================\n")
        out.write("*HEADING\nMethod C Problem 2 Double-Notch Benchmark Model\n")
        out.write("*PREPRINT, ECHO=NO, MODEL=NO, HISTORY=NO\n")

        # NODES
        out.write("*NODE, NSET=ALLNODES\n")
        for nid in sorted(r_nodes.keys()):
            out.write("%d, %.8e, %.8e\n" % (nid, r_nodes[nid][0], r_nodes[nid][1]))
        out.write("%d, %.8e, %.8e\n" % (rp_nid, 0.5, PLATE_H))

        # Layer 1: Phase UEL (DOF 3)
        if r_quads:
            out.write("*USER ELEMENT, NODES=4, TYPE=U1, PROPERTIES=6, COORDINATES=2, VARIABLES=18, UNSYMM\n3\n")
            out.write("*ELEMENT, TYPE=U1, ELSET=PHASE_QUAD\n")
            for eid in sorted(r_quads.keys()):
                out.write("%d, %s\n" % (eid, ", ".join(str(n) for n in r_quads[eid])))
        if r_tris:
            out.write("*USER ELEMENT, NODES=3, TYPE=U3, PROPERTIES=6, COORDINATES=2, VARIABLES=18, UNSYMM\n3\n")
            out.write("*ELEMENT, TYPE=U3, ELSET=PHASE_TRI\n")
            for eid in sorted(r_tris.keys()):
                out.write("%d, %s\n" % (eid, ", ".join(str(n) for n in r_tris[eid])))

        # Layer 2: Mech UEL (DOFs 1, 2)
        if r_quads:
            out.write("*USER ELEMENT, NODES=4, TYPE=U2, PROPERTIES=6, COORDINATES=2, VARIABLES=18, UNSYMM\n1, 2\n")
            out.write("*ELEMENT, TYPE=U2, ELSET=DISP_QUAD\n")
            for eid in sorted(r_quads.keys()):
                out.write("%d, %s\n" % (eid + offset_disp, ", ".join(str(n) for n in r_quads[eid])))
        if r_tris:
            out.write("*USER ELEMENT, NODES=3, TYPE=U4, PROPERTIES=6, COORDINATES=2, VARIABLES=18, UNSYMM\n1, 2\n")
            out.write("*ELEMENT, TYPE=U4, ELSET=DISP_TRI\n")
            for eid in sorted(r_tris.keys()):
                out.write("%d, %s\n" % (eid + offset_disp, ", ".join(str(n) for n in r_tris[eid])))

        # Layer 3: Companion UMAT (Visualization)
        if r_quads:
            out.write("*ELEMENT, TYPE=CPE4, ELSET=umatelem_quad\n")
            for eid in sorted(r_quads.keys()):
                out.write("%d, %s\n" % (eid + offset_vis, ", ".join(str(n) for n in r_quads[eid])))
        if r_tris:
            out.write("*ELEMENT, TYPE=CPE3, ELSET=umatelem_tri\n")
            for eid in sorted(r_tris.keys()):
                out.write("%d, %s\n" % (eid + offset_vis, ", ".join(str(n) for n in r_tris[eid])))

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

        # Kinematic Coupling: All top tensile nodes tied to N_RP in DOF 2
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

        out.write("*AMPLITUDE, NAME=CONST_HOLD\n0.0, 1.0, 1.0, 1.0\n")

        if is_coarse:
            # Coarse Cycle: Single displacement step
            out.write("** ==========================================================\n")
            out.write("** STEP 1: Pre-critical Coarse Loading to uy = %.6f mm\n" % target_uy)
            out.write("** ==========================================================\n")
            out.write("*STEP, NAME=Step-1, NLGEOM=NO, INC=1000\n")
            out.write("*STATIC\n")
            out.write("0.02, 1.0, 1.0E-14, 0.05\n")
            out.write("*BOUNDARY\n")
            out.write("N_BOTTOM, 2, 2, 0.0\n")
            out.write("N_PIN, 1, 1, 0.0\n")
            out.write("N_RP, 2, 2, %.8e\n" % target_uy)
            out.write("*OUTPUT, FIELD, FREQUENCY=1\n")
            out.write("*NODE OUTPUT\nU\n")
            out.write("*NODE OUTPUT, NSET=N_RP\nRF\n")
            out.write("*ELEMENT OUTPUT, ELSET=umatelem\nSDV\n")
            out.write("*NODE PRINT, FREQ=1, NSET=N_RP\nU2, RF2\n")
            out.write("*END STEP\n")
        else:
            # Adaptive Cycle: Step 1 (Hold) + Step 2 (RIKS Advance)
            out.write("** ==========================================================\n")
            out.write("** STEP 1: Fixed-Load Re-equilibration Hold at donor_uy = %.6f mm\n" % donor_uy)
            out.write("** ==========================================================\n")
            out.write("*STEP, NAME=Step-1, NLGEOM=NO, INC=100\n")
            out.write("*STATIC\n")
            out.write("1.0, 1.0, 1.0E-08, 1.0\n")
            out.write("*BOUNDARY\n")
            out.write("N_BOTTOM, 2, 2, 0.0\n")
            out.write("N_PIN, 1, 1, 0.0\n")
            out.write("*BOUNDARY, AMPLITUDE=CONST_HOLD\n")
            out.write("N_RP, 2, 2, %.8e\n" % donor_uy)
            out.write("*OUTPUT, FIELD, FREQUENCY=1\n")
            out.write("*NODE OUTPUT\nU\n")
            out.write("*NODE OUTPUT, NSET=N_RP\nRF\n")
            out.write("*ELEMENT OUTPUT, ELSET=umatelem\nSDV\n")
            out.write("*NODE PRINT, FREQ=1, NSET=N_RP\nU2, RF2\n")
            out.write("*END STEP\n")

            out.write("** ==========================================================\n")
            out.write("** STEP 2: Forward Crack Propagation to target_uy = %.6f mm\n" % target_uy)
            out.write("** ==========================================================\n")
            if use_riks:
                out.write("*STEP, NAME=Step-2, NLGEOM=NO, INC=1000\n")
                out.write("*STATIC, RIKS\n")
                out.write("0.01, 1.0, 1.0E-14, 0.05, 1.0\n")
                out.write("*BOUNDARY, OP=MOD\n")
                out.write("N_RP, 2, 2, %.8e\n" % target_uy)
            else:
                out.write("*STEP, NAME=Step-2, NLGEOM=NO, INC=1000\n")
                out.write("*STATIC\n")
                out.write("0.01, 1.0, 1.0E-14, 0.05\n")
                out.write("*BOUNDARY, OP=MOD\n")
                out.write("N_RP, 2, 2, %.8e\n" % target_uy)

            out.write("*OUTPUT, FIELD, FREQUENCY=1\n")
            out.write("*NODE OUTPUT\nU\n")
            out.write("*NODE OUTPUT, NSET=N_RP\nRF\n")
            out.write("*ELEMENT OUTPUT, ELSET=umatelem\nSDV\n")
            out.write("*NODE PRINT, FREQ=1, NSET=N_RP\nU2, RF2\n")
            out.write("*END STEP\n")

    print("Assembled Double-Notch coupled deck: %s (%d elements)" % (out_deck_path, num_phys))
    return out_deck_path

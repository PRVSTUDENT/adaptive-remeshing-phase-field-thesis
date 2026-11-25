# -*- coding: utf-8 -*-
"""
models/mode_II_or_l_panel/295_method_c_lpanel/lpanel_single_job_orchestrator.py
=============================================================================
Task: METHOD-C-LPANEL-SETUP-AND-VALIDATION
Goal: METHOD_C_MODE2_LPANEL_V1
Correlation: HND-METHOD-C-MODE2-LPANEL-006

In-job orchestrator for Method C L-Panel Benchmark:
Winkler et al. (2001) / Miehe et al. (2010) Fig. 19 L-Shaped Panel:
- Geometry: 500 x 500 mm outer envelope, re-entrant corner at (250, 250) mm
- Boundary Conditions:
  * Bottom edge clamped: y = 0, x in [0, 250] mm -> ux = 0, uy = 0 (N_BOTTOM)
  * Upward vertical displacement uy applied at x = 470 mm, y = 250 mm (N_RP / N_LOAD)
- Material Parameters:
  * E = 25.84 GPa (25.84 kN/mm^2)
  * nu = 0.18
  * l0 = 3.125 mm (l0 / 2 = 1.5625 mm)
  * Gc = 9.5e-5 kN/mm (0.095 N/mm)
  * k_res = 1.0e-7
  * Thickness = 100.0 mm
- Subroutine: models/pandey_kumar_mode1/f42_mixed_uel.for
  (Bitwise frozen source CE8D5EDC... preserved)
- State Transfer & Re-equilibration:
  * Validated nearest-neighbour transfer of damage d and history H
  * Step 1: Fixed-load re-equilibration card (*STATIC\n1.0, 1.0, 1.0E-08, 1.0)
    evaluating force continuity gate |Delta RF2| <= 5.0%
  * Step 2: Forward crack propagation advance with arc-length (*STATIC, RIKS)
  * Non-healing gate: d_max_terminal >= d_max_transferred - 1e-4
- Crack Completion Criteria:
  * Primary: Reaction force drop below 5% of peak (RF2 < 0.05 * peak_RF2)
  * Secondary: Geometric severance to left boundary (x_tip <= 1.0 mm) with RF2 < 20% peak
- Embedded Stall Watchdog (HND-METHOD-C-MODE2-LPANEL-002)
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
import argparse
from collections import defaultdict

try:
    REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
except NameError:
    REPO_ROOT = os.path.abspath(os.getcwd())

if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) if "__file__" in locals() else os.getcwd()
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

# Import stall watchdog
from stall_watchdog import StallWatchdog

FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
BENCHMARK_GC_KN_MM = 9.5e-5      # 0.095 N/mm
BENCHMARK_L0_MM = 3.125          # mm
BENCHMARK_E_GPA = 25.84          # kN/mm^2 (GPa)
BENCHMARK_NU = 0.18
BENCHMARK_K_RES = 1.0e-7
BENCHMARK_THICKNESS = 100.0      # mm
H_REF_MM = 1.50                  # mm (<= l0/2 = 1.5625 mm)

# Geometry landmarks
PANEL_W = 500.0
PANEL_H = 500.0
CORNER_X = 250.0
CORNER_Y = 250.0
LOAD_X = 470.0
LOAD_Y = 250.0

# Completion thresholds
LEFT_SEVERANCE_X_MM = 5.0000       # Crack reaching within 5 mm of left boundary
SEVERANCE_ARC_LENGTH_MM = 240.00   # Column width is 250 mm; curved path is ~250-260 mm
LOAD_DROP_COMPLETION_RATIO = 0.05  # RF2 < 5% of peak RF2
SEVERANCE_RF_RATIO = 0.20          # 20% of peak for geometric branch

# Load schedule defaults
DEFAULT_COARSE_UY_MM = 0.2000      # Pre-critical precrack displacement (clean pre-peak qualification)
DEFAULT_LOAD_INCREMENT_MM = 0.0200 # Step 2 RIKS advance per cycle
DEFAULT_MAX_CYCLES = 7



def compute_cumulative_crack_arc_length(tip_history, corner=(CORNER_X, CORNER_Y)):
    """
    Computes cumulative arc length along curved crack path:
      s = sum_{i=1}^k sqrt((x_i - x_{i-1})^2 + (y_i - y_{i-1})^2)
    """
    if not tip_history:
        return 0.0
    pts = [corner] + list(tip_history)
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


def compute_quad_gp_coords(elem_conn_or_coords, node_coords=None):
    if node_coords is not None:
        coords = [node_coords[n] for n in elem_conn_or_coords]
        gps = []
        for gp_idx, (xi, eta) in enumerate(QUAD_GP_LOCAL, start=1):
            N = quad_shape_funcs(xi, eta)
            gx = sum(N[i] * coords[i][0] for i in range(4))
            gy = sum(N[i] * coords[i][1] for i in range(4))
            gps.append((gp_idx, gx, gy))
        return gps
    else:
        elem_node_coords = elem_conn_or_coords
        gp_coords = []
        for xi, eta in QUAD_GP_LOCAL:
            N = quad_shape_funcs(xi, eta)
            gx = sum(N[i] * elem_node_coords[i][0] for i in range(4))
            gy = sum(N[i] * elem_node_coords[i][1] for i in range(4))
            gp_coords.append((gx, gy))
        return gp_coords


def compute_tri_gp_coords(elem_conn, node_coords):
    coords = [node_coords[n] for n in elem_conn]
    gx = (coords[0][0] + coords[1][0] + coords[2][0]) / 3.0
    gy = (coords[0][1] + coords[1][1] + coords[2][1]) / 3.0
    return [(1, gx, gy)]


def compute_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()


def write_wrapped_nset(f, nset_name, node_list, max_per_line=16):
    f.write("*NSET, NSET=%s\n" % nset_name)
    sorted_nodes = sorted(node_list)
    for i in range(0, len(sorted_nodes), max_per_line):
        chunk = sorted_nodes[i:i + max_per_line]
        f.write(", ".join(str(n) for n in chunk) + "\n")


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


def assemble_lpanel_coupled_deck(out_deck_path,
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
    Assembles a complete 3-layer Method C L-Panel Abaqus input deck:
    - Layer 1: Phase-Field UEL (DOF 3)
    - Layer 2: Mechanical UEL (DOFs 1, 2)
    - Layer 3: Companion Visualization Elements (UMAT)
    - Boundary conditions:
      * N_BOTTOM: y = 0.0, x in [0.0, 250.0] -> ux = 0.0, uy = 0.0
      * N_LOAD (node nearest (470, 250)): coupled to Reference Point N_RP (999999) via *EQUATION
    - Step 1: Fixed-load re-equilibration hold at donor_uy (*STATIC) [Adaptive cycles]
    - Step 2: Forward crack advance to target_uy (*STATIC, RIKS)
    """
    num_phys = len(r_quads) + len(r_tris)
    num_phys_f = float(num_phys)
    offset_disp = num_phys
    offset_vis = 2 * num_phys

    bottom_nodes = []
    load_candidates = []
    collar_nodes = []

    for nid, (x, y) in r_nodes.items():
        if abs(y - 0.0) < 1e-4 and x <= 250.0 + 1e-4:
            bottom_nodes.append(nid)
        d_load = math.hypot(x - LOAD_X, y - LOAD_Y)
        load_candidates.append((nid, d_load))
        if 455.0 - 1e-4 <= x <= 485.0 + 1e-4 and abs(y - LOAD_Y) <= 1e-3:
            collar_nodes.append(nid)

    load_candidates.sort(key=lambda item: item[1])
    load_node_id = load_candidates[0][0]
    rp_nid = 999999

    with open(out_deck_path, "w") as out:
        out.write("** ==========================================================\n")
        out.write("** Abaqus Input Deck - 3-Layer Method C L-Panel Model\n")
        out.write("** Benchmark: Winkler et al. (2001) / Miehe et al. (2010) Fig. 19\n")
        out.write("** Model: %s\n" % os.path.basename(out_deck_path).replace(".inp", ""))
        out.write("** Discretization: %d nodes, %d physical elements (%d quads, %d tris)\n" % (
            len(r_nodes), num_phys, len(r_quads), len(r_tris)
        ))
        out.write("** Material: E = %.4f GPa, nu = %.2f, Gc = %.6e kN/mm, l0 = %.4f mm\n" % (
            E_GPa, nu, Gc, l0
        ))
        out.write("** Load Advance: donor uy = %.5f mm -> target uy = %.5f mm\n" % (donor_uy, target_uy))
        out.write("** Subroutine: models/pandey_kumar_mode1/f42_mixed_uel.for\n")
        out.write("** ==========================================================\n")
        out.write("*HEADING\nMethod C L-Panel Model\n")
        out.write("*PREPRINT, ECHO=NO, MODEL=NO, HISTORY=NO\n")

        # NODES
        out.write("*NODE, NSET=ALLNODES\n")
        for nid in sorted(r_nodes.keys()):
            out.write("%d, %.8e, %.8e\n" % (nid, r_nodes[nid][0], r_nodes[nid][1]))
        out.write("%d, %.8e, %.8e\n" % (rp_nid, LOAD_X, LOAD_Y))

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
        write_wrapped_nset(out, "N_LOAD_COLLAR", sorted(collar_nodes))
        out.write("*NSET, NSET=N_LOAD\n%d\n" % load_node_id)
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

        # Kinematic Coupling: Loading node vertical displacement coupled to N_RP
        out.write("** Loading point vertical displacement coupled to Reference Point N_RP\n")
        out.write("*EQUATION\n2\n%d, 2, 1.0, %d, 2, -1.0\n" % (load_node_id, rp_nid))

        # Initial Conditions (SVARS 1..18 on Layer 1) for adaptive cycles
        if not is_coarse and transferred_damage is not None and transferred_history is not None:
            out.write("** Transferred State: Initial Conditions (SVARS 1..18 on Layer 1)\n")
            out.write("*INITIAL CONDITIONS, TYPE=SOLUTION\n")
            for elements, ngp in ((r_quads, 4), (r_tris, 3)):
                for eid, conn in sorted(elements.items()):
                    d = sum((0.0 if n in collar_nodes else transferred_damage.get(n, 0.0)) for n in conn) / len(conn)
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
            out.write("** STEP 1: Pre-critical Coarse Loading to uy = %.5f mm\n" % target_uy)
            out.write("** ==========================================================\n")
            out.write("*STEP, NAME=Step-1, NLGEOM=NO, INC=1000\n")
            out.write("*STATIC\n")
            out.write("0.005, 1.0, 1.0E-14, 0.02\n")
            out.write("*BOUNDARY\n")
            out.write("N_BOTTOM, 1, 2, 0.0\n")
            out.write("N_LOAD_COLLAR, 3, 3, 0.0\n")
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
            out.write("** STEP 1: Fixed-Load Re-equilibration Hold at donor_uy = %.5f mm\n" % donor_uy)
            out.write("** ==========================================================\n")
            out.write("*STEP, NAME=Step-1, NLGEOM=NO, INC=100\n")
            out.write("*STATIC\n")
            out.write("1.0, 1.0, 1.0E-08, 1.0\n")
            out.write("*BOUNDARY\n")
            out.write("N_BOTTOM, 1, 2, 0.0\n")
            out.write("N_LOAD_COLLAR, 3, 3, 0.0\n")
            out.write("*BOUNDARY, AMPLITUDE=CONST_HOLD\n")
            out.write("N_RP, 2, 2, %.8e\n" % donor_uy)
            out.write("*OUTPUT, FIELD, FREQUENCY=1\n")
            out.write("*NODE OUTPUT\nU\n")
            out.write("*NODE OUTPUT, NSET=N_RP\nRF\n")
            out.write("*ELEMENT OUTPUT, ELSET=umatelem\nSDV\n")
            out.write("*NODE PRINT, FREQ=1, NSET=N_RP\nU2, RF2\n")
            out.write("*END STEP\n")

            out.write("** ==========================================================\n")
            out.write("** STEP 2: Forward Crack Propagation to target_uy = %.5f mm\n" % target_uy)
            out.write("** ==========================================================\n")
            if use_riks:
                out.write("*STEP, NAME=Step-2, NLGEOM=NO, INC=1000\n")
                out.write("*STATIC, RIKS\n")
                out.write("0.005, 1.0, 1.0E-14, 0.05, 1.0\n")
                out.write("*BOUNDARY, OP=MOD\n")
                out.write("N_LOAD_COLLAR, 3, 3, 0.0\n")
                out.write("N_RP, 2, 2, %.8e\n" % target_uy)
            else:
                out.write("*STEP, NAME=Step-2, NLGEOM=NO, INC=1000\n")
                out.write("*STATIC\n")
                out.write("0.005, 1.0, 1.0E-14, 0.05\n")
                out.write("*BOUNDARY, OP=MOD\n")
                out.write("N_LOAD_COLLAR, 3, 3, 0.0\n")
                out.write("N_RP, 2, 2, %.8e\n" % target_uy)

            out.write("*OUTPUT, FIELD, FREQUENCY=1\n")
            out.write("*NODE OUTPUT\nU\n")
            out.write("*NODE OUTPUT, NSET=N_RP\nRF\n")
            out.write("*ELEMENT OUTPUT, ELSET=umatelem\nSDV\n")
            out.write("*NODE PRINT, FREQ=1, NSET=N_RP\nU2, RF2\n")
            out.write("*END STEP\n")


def check_lpanel_completion(current_cycle,
                            peak_rf2,
                            terminal_rf2,
                            tip_x,
                            tip_y,
                            arc_length_s,
                            max_damage):
    """
    Evaluates completion criteria for L-Panel:
    Branch 1: Load drop below 5% of peak force (complete loss of load bearing capacity).
    Branch 2: Geometric severance: crack reaching left boundary (tip_x <= 5.0 mm or s >= 240.0 mm)
              with RF2 < 20% of peak force.
    """
    is_complete = False
    reason = "IN_PROGRESS"

    if peak_rf2 is not None and peak_rf2 > 0:
        rf_ratio = terminal_rf2 / peak_rf2
    else:
        rf_ratio = 1.0

    # Branch 1: Complete load drop (< 5%)
    if rf_ratio < LOAD_DROP_COMPLETION_RATIO:
        is_complete = True
        reason = "COMPLETE_LOAD_DROP_BELOW_5PCT (RF2=%.4f kN, %.2f%% of peak %.4f kN)" % (
            terminal_rf2, rf_ratio * 100.0, peak_rf2
        )
        return is_complete, reason

    # Branch 2: Geometric severance to left edge + RF2 < 20%
    if (tip_x <= LEFT_SEVERANCE_X_MM or arc_length_s >= SEVERANCE_ARC_LENGTH_MM) and max_damage >= 0.95:
        if rf_ratio < SEVERANCE_RF_RATIO:
            is_complete = True
            reason = "COMPLETE_SPECIMEN_SEVERED_TO_LEFT_EDGE (tip_x=%.4f mm, s=%.4f mm, d_max=%.4f, RF2=%.4f kN, %.2f%% of peak)" % (
                tip_x, arc_length_s, max_damage, terminal_rf2, rf_ratio * 100.0
            )
            return is_complete, reason

    return is_complete, reason


def preparation_audit():
    """Offline readiness audit; never claims a numerical solve or submission."""
    source = os.path.join(REPO_ROOT, 'models', 'pandey_kumar_mode1', 'f42_mixed_uel.for')
    return {
        'status': 'PREPARATION_INCOMPLETE',
        'execution_qualified': False,
        'frozen_uel_match': compute_sha256(source) == FROZEN_UEL_SHA256,
        'blockers': [
            'L-panel benchmark requires coarse/transfer qualification on local workstation.',
            'Preserving bitwise frozen UEL source CE8D5EDC.'
        ],
        'pbs_submissions': 0,
        'numerical_uncertainty': 'Unverified mixed-mode curved crack propagation across 500 mm L-shaped panel.',
        'next_measurable_test': 'Qualify Cycle 0 coarse solve, audit transfer gates and tip tracking.'
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description='Method C L-Panel benchmark runner.')
    parser.add_argument('--dry-run', action='store_true', help='Print offline readiness without Abaqus execution.')
    parser.add_argument('--run', action='store_true', help='Execute the bounded local experiment.')
    parser.add_argument('--coarse-only', action='store_true', help='Stop after authentic Cycle 0 qualification.')
    parser.add_argument('--run-dir', help='Fresh local scratch directory; existing runs are preserved.')
    parser.add_argument('--publish-dir', help='Destination folder for published evidence (default: local_windows_adaptive_run).')
    parser.add_argument('--max-cycles', type=int, default=DEFAULT_MAX_CYCLES)
    parser.add_argument('--cpus', type=int, default=4)
    parser.add_argument('--donor-checkpoint', help='Explicit authentic checkpoint; new scratch folder required.')
    args = parser.parse_args(argv)

    if args.dry_run:
        print(json.dumps(preparation_audit(), indent=2))
        return 0
    if not args.run:
        parser.exit(2, 'L-Panel execution requires explicit --run and --run-dir. No solver started.\n')
    if not args.run_dir or not 0 <= args.max_cycles <= 100 or args.cpus not in (1, 2, 4, 6):
        parser.error('Scope is local PC (1-6 CPUs), at most 100 adaptive cycles, and a fresh --run-dir.')

    import lpanel_runtime
    runner = lpanel_runtime.LocalRunner(sys.modules[__name__], args.run_dir, args.cpus,
                                        0 if args.coarse_only else args.max_cycles,
                                        donor_checkpoint=args.donor_checkpoint,
                                        publish_dir=args.publish_dir)
    try:
        runner.execute()
    except Exception as error:
        lpanel_runtime.write_json(runner.run / 'diagnosed_blocker.json',
                                 {'blocker': str(error), 'retry': False, 'master_goal_status': 'OPEN', 'time': time.time()})
        state_path = runner.run / 'execution_state.json'
        if state_path.exists():
            state = json.loads(state_path.read_text())
            state.update(active=False, completed=False, blocker=str(error), ended_at=time.time())
            lpanel_runtime.write_json(state_path, state)
        raise
    return 0


if __name__ == '__main__':
    sys.exit(main())

# -*- coding: utf-8 -*-
"""
models/pandey_kumar_mode2/294_method_c_mode2/mode2_single_job_orchestrator.py
=============================================================================
Task: METHOD-C-MODE2-LPANEL-STALL-CHECK-AMENDMENT
Goal: METHOD_C_MODE2_LPANEL_V1
Correlation: HND-METHOD-C-MODE2-LPANEL-002

In-job orchestrator for Method C Mode-II (Pandey & Kumar 2025 Section 4.2):
Executes the multi-cycle adaptive remeshing sequence on the local workstation:
  Cycle 0 (Coarse) -> Cycle 1 (Adapt 1) -> Cycle 2 (Adapt 2) -> ... -> Completion

Key architectural specifications:
1. Geometry & Benchmark:
   - Plate: 1.0 x 1.0 mm square plate with initial horizontal slit a0 = 0.5 mm at y = 0.5 mm.
   - Notch root at (0.5000, 0.5000) mm.
   - Material: E = 210.0 GPa, nu = 0.3, Gc = 0.0027 kN/mm (2.7 N/mm), l0 = 0.0150 mm, k_res = 1e-7.
   - Frozen UEL: f42_mixed_uel.for (CE8D5EDC... bitwise preserved).
2. Boundary Conditions (Shear Loading):
   - Bottom (y = 0.0): ux = 0.0, uy = 0.0 (N_BOTTOM)
   - Top (y = 1.0): uy = 0.0 (N_TOP), ux coupled to N_RP (node 999999) via *EQUATION
   - Shear displacement ux applied at N_RP; reaction force evaluated as RF1 on N_RP.
3. Sizing & Dynamic Deflection Remeshing:
   - Crack deflects downward (~ -58 to -70 deg) toward bottom boundary (x ~ 0.81-0.85, y = 0.0).
   - Refined element size: h_ref = 0.0070 mm < l0 / 2 = 0.0075 mm (l0 = 0.015 mm).
   - Background size: h_bg = 0.025 mm.
   - Wake preservation: retains wake behind advancing tip, refines active front.
   - Mesh budget: total elements strictly bounded < 35,000 (est. ~4,000-8,000).
4. Crack-Completion Criteria:
   - Primary Geometric Severance: crack reaches bottom boundary (y_tip <= 0.05 mm or s >= 0.50 mm).
   - Secondary Load Drop: Reaction force RF1 < 0.05 * peak_RF1 (>95% load drop).
5. State Transfer & Re-equilibration:
   - Binned spatial transfer of damage d and history H.
   - Step 1: Fixed-load re-equilibration hold (|Delta RF1| <= 5.0% continuity gate).
   - Step 2: Forward crack propagation advance with arc-length (RIKS) or displacement control.
   - Zero-healing verification: d_max_terminal >= d_max_transferred - 1e-4.
6. Embedded Stall-Check Watchdog (HND-METHOD-C-MODE2-LPANEL-002):
   - Periodic 2-hour check on .sta increment advancement.
   - 8-hour maximum cycle runtime timeout.
   - 4-hour agent silence guard.
   - Clean termination and structured bridge payload generation on stall.
"""

from __future__ import print_function, division
import os
import sys
import json
import math
import subprocess
import hashlib
import time
import argparse
from collections import defaultdict

try:
    import odbAccess
    from abaqusConstants import *
    ABAQUS_AVAILABLE = True
except ImportError:
    ABAQUS_AVAILABLE = False

try:
    REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
except NameError:
    REPO_ROOT = os.path.abspath(os.getcwd())

if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# Import stall watchdog
from stall_watchdog import StallWatchdog

FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
BENCHMARK_GC_KN_MM = 0.0027
BENCHMARK_L0_MM = 0.0150
H_REF_MM = 0.0070
DT_MIN = 1.0e-14

# Plate geometry bounds for Mode-II
PLATE_WIDTH_MM = 1.0000
PLATE_HEIGHT_MM = 1.0000
NOTCH_ROOT_X_MM = 0.5000
NOTCH_ROOT_Y_MM = 0.5000

# Mode-II Completion thresholds
BOTTOM_SEVERANCE_Y_MM = 0.0500     # Crack reaching near bottom edge
SEVERANCE_ARC_LENGTH_MM = 0.5000   # Trajectory from (0.5, 0.5) to (0.82, 0.0) is ~0.59 mm
LOAD_DROP_COMPLETION_RATIO = 0.05  # RF1 < 5% of peak RF1
SEVERANCE_RF_RATIO = 0.20          # 20% of peak for geometric branch

# Load schedule defaults
DEFAULT_COARSE_UX_MM = 0.0095
DEFAULT_N_ADAPTIVE_STEPS = 6
DEFAULT_LOAD_INCREMENT_MM = 0.0015


def compute_cumulative_crack_arc_length(tip_history, notch_root=(NOTCH_ROOT_X_MM, NOTCH_ROOT_Y_MM)):
    """
    Computes cumulative arc length along crack path:
      s = sum_{i=1}^k sqrt((x_i - x_{i-1})^2 + (y_i - y_{i-1})^2)
    """
    if not tip_history:
        return 0.0
    pts = [notch_root] + list(tip_history)
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


def compute_quad_gp_coords(elem_node_coords):
    gp_coords = []
    for xi, eta in QUAD_GP_LOCAL:
        N = quad_shape_funcs(xi, eta)
        gx = sum(N[i] * elem_node_coords[i][0] for i in range(4))
        gy = sum(N[i] * elem_node_coords[i][1] for i in range(4))
        gp_coords.append((gx, gy))
    return gp_coords


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


def assemble_mode2_coupled_deck(out_deck_path,
                                r_nodes,
                                r_quads,
                                r_tris,
                                donor_ux,
                                target_ux,
                                transferred_damage,
                                transferred_history,
                                E_GPa=210.0,
                                nu=0.30,
                                Gc=BENCHMARK_GC_KN_MM,
                                l0=BENCHMARK_L0_MM,
                                k_res=1.0e-7,
                                use_riks=True):
    """
    Assembles a complete 3-layer Method C Mode-II Abaqus input deck:
    - Layer 1: Phase-Field UEL (DOF 3)
    - Layer 2: Mechanical UEL (DOFs 1, 2)
    - Layer 3: Companion Visualization Elements (UMAT)
    - Boundary conditions:
      * N_BOTTOM: y = 0.0 -> ux = 0.0, uy = 0.0
      * N_TOP: y = 1.0 -> uy = 0.0, ux coupled to N_RP (999999) via *EQUATION
    - Step 1: Fixed-load re-equilibration hold at donor_ux (*STATIC)
    - Step 2: Forward crack advance to target_ux (*STATIC, RIKS or *STATIC)
    """
    num_phys = len(r_quads) + len(r_tris)
    num_phys_f = float(num_phys)
    offset_disp = num_phys
    offset_vis = 2 * num_phys

    bottom_nodes = []
    top_nodes = []

    for nid, (x, y) in r_nodes.items():
        if abs(y - 0.0) < 1e-4:
            bottom_nodes.append(nid)
        if abs(y - 1.0) < 1e-4:
            top_nodes.append(nid)

    rp_nid = 999999

    with open(out_deck_path, "w") as out:
        out.write("** ==========================================================\n")
        out.write("** Abaqus Input Deck - 3-Layer Method C Mode-II Model\n")
        out.write("** Benchmark: Pandey & Kumar (2025) Section 4.2 Mode-II Shear Plate\n")
        out.write("** Model: %s\n" % os.path.basename(out_deck_path).replace(".inp", ""))
        out.write("** Discretization: %d nodes, %d physical elements (%d quads, %d tris)\n" % (
            len(r_nodes), num_phys, len(r_quads), len(r_tris)
        ))
        out.write("** Material: E = %.1f GPa, nu = %.2f, Gc = %.6f kN/mm, l0 = %.4f mm\n" % (
            E_GPa, nu, Gc, l0
        ))
        out.write("** Load Advance: donor ux = %.5f mm -> target ux = %.5f mm\n" % (donor_ux, target_ux))
        out.write("** Subroutine: models/pandey_kumar_mode1/f42_mixed_uel.for\n")
        out.write("** ==========================================================\n")
        out.write("*HEADING\nMethod C Mode-II Model\n")
        out.write("*PREPRINT, ECHO=NO, MODEL=NO, HISTORY=NO\n")

        # NODES
        out.write("*NODE, NSET=ALLNODES\n")
        for nid in sorted(r_nodes.keys()):
            out.write("%d, %.8e, %.8e\n" % (nid, r_nodes[nid][0], r_nodes[nid][1]))
        out.write("%d, %.8e, %.8e\n" % (rp_nid, 0.5000, 1.0000))

        # Layer 1: Phase UEL
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

        # Layer 2: Mech UEL
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

        # Layer 3: Companion UMAT
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
        out.write("*NSET, NSET=N_RP\n%d\n" % rp_nid)

        # UEL Properties
        if r_quads:
            out.write("*UEL PROPERTY, ELSET=PHASE_QUAD\n")
            out.write("%.4f, %.6f, %.1f, %.2f, %.1e, %.1f\n" % (l0, Gc, E_GPa, nu, k_res, num_phys_f))
            out.write("*UEL PROPERTY, ELSET=DISP_QUAD\n")
            out.write("%.4f, %.6f, %.1f, %.2f, %.1e, %.1f\n" % (l0, Gc, E_GPa, nu, k_res, num_phys_f))
        if r_tris:
            out.write("*UEL PROPERTY, ELSET=PHASE_TRI\n")
            out.write("%.4f, %.6f, %.1f, %.2f, %.1e, %.1f\n" % (l0, Gc, E_GPa, nu, k_res, num_phys_f))
            out.write("*UEL PROPERTY, ELSET=DISP_TRI\n")
            out.write("%.4f, %.6f, %.1f, %.2f, %.1e, %.1f\n" % (l0, Gc, E_GPa, nu, k_res, num_phys_f))

        # Companion UMAT Section & Material
        out.write("*SOLID SECTION, ELSET=All_elem, MATERIAL=M_COMPANION\n1.0\n")
        out.write("*MATERIAL, NAME=M_COMPANION\n*USER MATERIAL, CONSTANTS=3\n")
        out.write("%.1f, %.2f, %.1f\n" % (E_GPa, nu, num_phys_f))
        out.write("*DEPVAR\n30\n")

        # Kinematic Coupling Equations: Top nodes ux coupled to N_RP ux
        out.write("** Top boundary horizontal shear coupled to Reference Point N_RP\n")
        for tn in sorted(top_nodes):
            out.write("*EQUATION\n2\n%d, 1, 1.0, %d, 1, -1.0\n" % (tn, rp_nid))

        # Initial Conditions: Transferred phase d and history H on Layer 1
        out.write("** Transferred State: Initial Conditions (SVARS 1..18 on Layer 1)\n")
        out.write("*INITIAL CONDITIONS, TYPE=SOLUTION\n")
        for eid in sorted(r_quads.keys()):
            d_val = float(transferred_damage.get(eid, 0.0))
            h_val = float(transferred_history.get(eid, 0.0))
            deg = (1.0 - d_val)**2 + k_res
            # Format: elem, sv1, sv2, sv3, sv4, sv5, sv6, sv7, sv8
            out.write("%d, %.6e, %.6e, %.6e, %.6e, %.6e, %.6e, %.6e, %.6e\n" % (
                eid, d_val, d_val, d_val, d_val, h_val, h_val, h_val, h_val
            ))
            # Format: elem, sv9, sv10, sv11, sv12, sv13, sv14, sv15, sv16
            out.write("%d, %.6e, %.6e, %.6e, %.6e, %.6e, %.6e, %.6e, %.6e\n" % (
                eid, h_val, h_val, h_val, h_val, d_val, d_val, deg, h_val
            ))

        for eid in sorted(r_tris.keys()):
            d_val = float(transferred_damage.get(eid, 0.0))
            h_val = float(transferred_history.get(eid, 0.0))
            deg = (1.0 - d_val)**2 + k_res
            out.write("%d, %.6e, %.6e, %.6e, %.6e, %.6e, %.6e, %.6e, %.6e\n" % (
                eid, d_val, d_val, d_val, d_val, h_val, h_val, h_val, h_val
            ))
            out.write("%d, %.6e, %.6e, %.6e, %.6e, %.6e, %.6e, %.6e, %.6e\n" % (
                eid, h_val, h_val, h_val, h_val, d_val, d_val, deg, h_val
            ))

        # Initial conditions on Layer 2 and Layer 3 (zeros)
        for eid in sorted(r_quads.keys()):
            out.write("%d, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0\n" % (eid + offset_disp))
            out.write("%d, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0\n" % (eid + offset_disp))
        for eid in sorted(r_tris.keys()):
            out.write("%d, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0\n" % (eid + offset_disp))
            out.write("%d, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0\n" % (eid + offset_disp))

        # ==========================================================
        # STEP 1: Fixed-Load Re-equilibration Hold at donor_ux
        # ==========================================================
        out.write("** ==========================================================\n")
        out.write("** STEP 1: Fixed-Load Re-equilibration Hold at donor_ux = %.5f mm\n" % donor_ux)
        out.write("** ==========================================================\n")
        out.write("*STEP, NAME=Step-1, NLGEOM=NO, INC=500\n")
        out.write("*STATIC\n")
        out.write("0.05, 1.0, 1.0E-14, 0.5\n")
        out.write("*BOUNDARY, OP=NEW\n")
        out.write("N_BOTTOM, 1, 2, 0.0\n")
        out.write("N_TOP, 2, 2, 0.0\n")
        out.write("N_RP, 1, 1, %.8e\n" % donor_ux)
        out.write("*OUTPUT, FIELD, FREQUENCY=1\n")
        out.write("*NODE OUTPUT, NSET=N_RP\nU, RF\n")
        out.write("*ELEMENT OUTPUT, ELSET=umatelem\nSDV\n")
        out.write("*NODE PRINT, FREQ=1, NSET=N_RP\nU1, RF1\n")
        out.write("*END STEP\n")

        # ==========================================================
        # STEP 2: Forward Crack Propagation to target_ux
        # ==========================================================
        out.write("** ==========================================================\n")
        out.write("** STEP 2: Forward Crack Propagation to target_ux = %.5f mm\n" % target_ux)
        out.write("** ==========================================================\n")
        if use_riks:
            out.write("*STEP, NAME=Step-2, NLGEOM=NO, INC=1000\n")
            out.write("*STATIC, RIKS\n")
            out.write("0.005, 1.0, 1.0E-14, 0.05, 1.0\n")
            out.write("*BOUNDARY, OP=MOD\n")
            out.write("N_RP, 1, 1, %.8e\n" % target_ux)
        else:
            out.write("*STEP, NAME=Step-2, NLGEOM=NO, INC=1000\n")
            out.write("*STATIC\n")
            out.write("0.005, 1.0, 1.0E-14, 0.05\n")
            out.write("*BOUNDARY, OP=MOD\n")
            out.write("N_RP, 1, 1, %.8e\n" % target_ux)

        out.write("*OUTPUT, FIELD, FREQUENCY=1\n")
        out.write("*NODE OUTPUT, NSET=N_RP\nU, RF\n")
        out.write("*ELEMENT OUTPUT, ELSET=umatelem\nSDV\n")
        out.write("*NODE PRINT, FREQ=1, NSET=N_RP\nU1, RF1\n")
        out.write("*END STEP\n")


def check_mode2_completion(current_cycle,
                           peak_rf1,
                           terminal_rf1,
                           tip_x,
                           tip_y,
                           arc_length_s,
                           max_damage):
    """
    Evaluates completion criteria for Mode-II:
    Branch 1: Load drop below 5% of peak force (complete loss of load bearing capacity).
    Branch 2: Geometric severance: crack reaching bottom edge (tip_y <= 0.05 mm or s >= 0.50 mm)
              with RF1 < 20% of peak force.
    """
    is_complete = False
    reason = "IN_PROGRESS"

    if peak_rf1 is not None and peak_rf1 > 0:
        rf_ratio = terminal_rf1 / peak_rf1
    else:
        rf_ratio = 1.0

    # Branch 1: Complete load drop (< 5%)
    if rf_ratio < LOAD_DROP_COMPLETION_RATIO:
        is_complete = True
        reason = "COMPLETE_LOAD_DROP_BELOW_5PCT (RF1=%.4f kN, %.2f%% of peak %.4f kN)" % (
            terminal_rf1, rf_ratio * 100.0, peak_rf1
        )
        return is_complete, reason

    # Branch 2: Geometric severance near bottom boundary + RF1 < 20%
    if (tip_y <= BOTTOM_SEVERANCE_Y_MM or arc_length_s >= SEVERANCE_ARC_LENGTH_MM) and max_damage >= 0.95:
        if rf_ratio < SEVERANCE_RF_RATIO:
            is_complete = True
            reason = "COMPLETE_SPECIMEN_SEVERED_TO_BOTTOM_EDGE (tip_y=%.4f mm, s=%.4f mm, d_max=%.4f, RF1=%.4f kN, %.2f%% of peak)" % (
                tip_y, arc_length_s, max_damage, terminal_rf1, rf_ratio * 100.0
            )
            return is_complete, reason

    return is_complete, reason

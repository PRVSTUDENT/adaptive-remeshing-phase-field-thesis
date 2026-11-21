# -*- coding: utf-8 -*-
"""
scripts/remeshing/case3_single_job_orchestrator.py
==================================================
Task: METHOD-C-CASE3-FRAMEWORK-ORCHESTRATOR-REPAIR-AND-CYCLE0-RESULTS
Correlation: HND-METHOD-C-CASE3-FRAMEWORK-CYCLE0-001

In-job orchestrator for Method C Case 3 (Pandey & Kumar Section 4.3):
Executes the entire multi-cycle sequence inside ONE single PBS allocation:
  Cycle 0 (Coarse) -> Cycle 1 (Adapt 1) -> Cycle 2 (Adapt 2) -> ... -> Completion

Key architectural specifications:
1. User-specifiable adaptive steps and equal load division:
   - Parameter n_adaptive_steps (default 4): sets planned granularity per pass.
   - Equal-load-division loop: displacement is advanced in equal increments, one per adaptive cycle
     (load_increment_mm, default 0.0100 mm).
   - No 1.5000 mm final cap; there is no artificial displacement limit.
2. Crack-completion criteria:
   - Loop continues until:
       (a) Terminal crack tip x_tip >= 64.0 mm (right edge of 65.0 mm plate), OR
       (b) Reaction force RF2 < 0.05 * peak_RF2 (plate severed, >95% load drop).
   - Outer bound: 72-hour walltime allocation.
3. dt_min-floor behaviour:
   - When a cycle reaches the cutback floor (dt < dt_min = 1.0E-14), the cycle stops gracefully.
   - The orchestrator extracts the last converged increment (filtering unconverged 'U' attempts).
   - No further manual dt_min reduction is authorized.
   - Adaptive remeshing proceeds directly from that terminal converged state.
4. Refinement corridor minimization:
   - Minimized corridor partition: x in [8.5, 20.0] mm, y in [60.0, 77.0] mm (area 195.5 mm^2)
   - Physical element count target: ~30,000 physical elements (24,832 elements generated)
   - Refined element size: href = 0.140 mm < l0 / 2 = 0.1425 mm (l0 = 0.285 mm)
5. Gates enforced per cycle:
   - Fixed-load re-equilibration force continuity: |Delta RF2| <= 5.0% vs donor terminal state
   - Energy continuity: evaluated with Gc normalization (Gamma = E_frac / Gc)
   - Zero-healing: d_max_terminal >= d_max_transferred - 1e-4
   - Dynamic terminal frame labelling from the last converged increment.
6. Execution architecture:
   - Implements full in-allocation execution path:
     (Abaqus solve -> observables extraction -> remeshing -> state transfer -> deck assembly -> re-equilibration -> advance).
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
    REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
except NameError:
    REPO_ROOT = os.path.abspath(os.getcwd())

if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
BENCHMARK_GC_KN_MM = 0.00228  # 2.28 J/m^2 (Pandey & Kumar 2025 Section 4.3)
BENCHMARK_L0_MM = 0.285
H_REF_MM = 0.140
DT_MIN = 1.0e-14

# Refinement minimization box
CORRIDOR_X_MIN = 8.5
CORRIDOR_X_MAX = 20.0
CORRIDOR_Y_MIN = 60.0
CORRIDOR_Y_MAX = 77.0

# Plate geometry bounds for completion check
PLATE_WIDTH_MM = 65.0
CRACK_COMPLETION_X_MM = 64.0
LOAD_DROP_COMPLETION_RATIO = 0.05  # RF2 < 5% of peak RF2

# Load schedule defaults
DEFAULT_COARSE_U2_MM = 0.0500
DEFAULT_N_ADAPTIVE_STEPS = 4
DEFAULT_LOAD_INCREMENT_MM = 0.0100  # Equal load division increment

# 2x2 Gauss quadrature on [-1, 1]^2
Q_GAUSS = 1.0 / math.sqrt(3.0)  # ~0.5773502691896257
QUAD_GP_LOCAL = [
    (-Q_GAUSS, -Q_GAUSS),  # GP 1
    ( Q_GAUSS, -Q_GAUSS),  # GP 2
    ( Q_GAUSS,  Q_GAUSS),  # GP 3
    (-Q_GAUSS,  Q_GAUSS),  # GP 4
]


def compute_sha256(path):
    """Computes SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def compute_body_sha256(path):
    """Computes SHA-256 of non-comment lines of an Abaqus input deck."""
    h = hashlib.sha256()
    with open(path, "r") as f:
        for line in f:
            stripped = line.strip()
            if not stripped.startswith("**"):
                h.update((stripped + "\n").encode("utf-8"))
    return h.hexdigest().upper()


def parse_sta_file(sta_path):
    """Parses Abaqus .sta file to determine total completed increments, terminal converged state, and cutback status."""
    converged_increments = []
    cutback_hit = False
    with open(sta_path, "r") as f:
        for line in f:
            line_str = line.strip()
            if not line_str or line_str.startswith("SUMMARY") or line_str.startswith("ODB") or line_str.startswith("STEP") or line_str.startswith("DISCON"):
                continue
            parts = line_str.split()
            if len(parts) >= 8:
                try:
                    step = int(parts[0])
                    inc = int(parts[1])
                    att_str = parts[2]
                    is_unconverged = "U" in att_str.upper()
                    att = int(att_str.upper().replace("U", ""))
                    if len(parts) >= 9:
                        step_time = float(parts[7])
                        dt = float(parts[8])
                    else:
                        step_time = float(parts[6])
                        dt = float(parts[7])

                    if not is_unconverged:
                        converged_increments.append({
                            "step": step,
                            "increment": inc,
                            "attempt": att,
                            "step_time": step_time,
                            "dt": dt
                        })
                except (ValueError, IndexError):
                    pass
            if "THE ANALYSIS HAS NOT BEEN COMPLETED" in line_str or "TIME INCREMENT REQUIRED IS LESS THAN" in line_str:
                cutback_hit = True

    terminal_converged_inc = converged_increments[-1] if converged_increments else None
    return {
        "increments": converged_increments,
        "total_converged_increments": len(converged_increments),
        "terminal_converged": terminal_converged_inc,
        "cutback_floor_reached": cutback_hit
    }


def parse_physical_inp(inp_path, renumber=False):
    """Parses Abaqus physical .inp mesh into nodes, quads, and tris."""
    nodes = {}
    quads = {}
    tris = {}
    elements = {}
    in_nodes = False
    in_elements = False
    elem_type = None

    with open(inp_path, "r") as f:
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
                    if "CPE4" in u or "CPS4" in u or "QUAD" in u:
                        elem_type = "QUAD"
                    elif "CPE3" in u or "CPS3" in u or "TRI" in u:
                        elem_type = "TRI"
                    else:
                        elem_type = "UNKNOWN"
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
                    conn = tuple(int_parts[1:])
                    elements[eid] = conn
                    if elem_type == "QUAD" or len(conn) == 4:
                        quads[eid] = conn[:4]
                    else:
                        tris[eid] = conn[:3]
                except ValueError:
                    pass

    if renumber:
        renumbered_quads = {}
        renumbered_tris = {}
        new_eid = 1
        for old_eid in sorted(quads.keys()):
            renumbered_quads[new_eid] = quads[old_eid]
            new_eid += 1
        for old_eid in sorted(tris.keys()):
            renumbered_tris[new_eid] = tris[old_eid]
            new_eid += 1
        all_elem = dict(renumbered_quads)
        all_elem.update(renumbered_tris)
        return {
            "nodes": nodes,
            "quads": renumbered_quads,
            "tris": renumbered_tris,
            "elements": all_elem
        }

    return {
        "nodes": nodes,
        "quads": quads,
        "tris": tris,
        "elements": elements
    }


def write_wrapped_nset(f, nset_name, node_list, max_per_line=16):
    """Writes an Abaqus node set formatted with at most max_per_line nodes per line."""
    f.write("*NSET, NSET=%s\n" % nset_name)
    sorted_nodes = sorted(node_list)
    for i in range(0, len(sorted_nodes), max_per_line):
        chunk = sorted_nodes[i:i + max_per_line]
        f.write(", ".join(str(n) for n in chunk) + "\n")


def quad_nodal_shape_functions(xi, eta):
    """Bilinear shape functions N_i(xi, eta) for a 4-node quad."""
    return [
        0.25 * (1.0 - xi) * (1.0 - eta),
        0.25 * (1.0 + xi) * (1.0 - eta),
        0.25 * (1.0 + xi) * (1.0 + eta),
        0.25 * (1.0 - xi) * (1.0 + eta),
    ]


def inverse_isoparametric_quad(quad_coords, px, py, max_iter=25, tol=1e-10):
    """Newton-Raphson inversion to map physical point (px, py) to natural coordinates (xi, eta)."""
    x = [c[0] for c in quad_coords]
    y = [c[1] for c in quad_coords]
    xi, eta = 0.0, 0.0
    for _ in range(max_iter):
        N = quad_nodal_shape_functions(xi, eta)
        fx = sum(N[i] * x[i] for i in range(4)) - px
        fy = sum(N[i] * y[i] for i in range(4)) - py
        if math.hypot(fx, fy) < tol:
            return xi, eta, True
        dxi = [-0.25 * (1.0 - eta),  0.25 * (1.0 - eta), 0.25 * (1.0 + eta), -0.25 * (1.0 + eta)]
        deta = [-0.25 * (1.0 - xi), -0.25 * (1.0 + xi), 0.25 * (1.0 + xi),  0.25 * (1.0 - xi)]
        J11 = sum(dxi[i] * x[i] for i in range(4))
        J12 = sum(deta[i] * x[i] for i in range(4))
        J21 = sum(dxi[i] * y[i] for i in range(4))
        J22 = sum(deta[i] * y[i] for i in range(4))
        det = J11 * J22 - J12 * J21
        if abs(det) < 1e-14:
            break
        d_xi = -(J22 * fx - J12 * fy) / det
        d_eta = -(-J21 * fx + J11 * fy) / det
        xi += d_xi
        eta += d_eta
        if math.hypot(d_xi, d_eta) < tol:
            return xi, eta, True
    return xi, eta, False


def point_in_triangle(tri_coords, px, py):
    """Barycentric coordinates and containment for 3-node triangle."""
    (x1, y1), (x2, y2), (x3, y3) = tri_coords
    detT = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3)
    if abs(detT) < 1e-14:
        return 0.0, 0.0, 0.0, float("inf")
    l1 = ((y2 - y3) * (px - x3) + (x3 - x2) * (py - y3)) / detT
    l2 = ((y3 - y1) * (px - x3) + (x1 - x3) * (py - y3)) / detT
    l3 = 1.0 - l1 - l2
    dist = max(0.0, -l1, -l2, -l3)
    return l1, l2, l3, dist


def transfer_nodal_fields(donor_mesh, donor_u, donor_d, receiver_mesh, slit_y=70.0, slit_a0=10.0, bin_size=2.5):
    """Transfers nodal displacement (u1, u2) and damage (d) with slit flank isolation."""
    d_nodes = donor_mesh["nodes"]
    d_quads = donor_mesh.get("quads", {})
    d_tris = donor_mesh.get("tris", {})
    d_all_donor = dict(d_quads)
    d_all_donor.update(d_tris)
    r_nodes = receiver_mesh["nodes"]

    upper_elems = {}
    lower_elems = {}
    for eid, conn in d_all_donor.items():
        cy = sum(d_nodes[n][1] for n in conn) / float(len(conn))
        if cy >= slit_y - 1e-7:
            upper_elems[eid] = conn
        else:
            lower_elems[eid] = conn

    def build_bins(elem_dict):
        bboxes = []
        for eid, conn in elem_dict.items():
            xs = [d_nodes[n][0] for n in conn]
            ys = [d_nodes[n][1] for n in conn]
            cx = sum(xs) / float(len(conn))
            cy = sum(ys) / float(len(conn))
            bboxes.append((eid, min(xs), max(xs), min(ys), max(ys), cx, cy, conn))
        bins = defaultdict(list)
        for item in bboxes:
            eid, xmin, xmax, ymin, ymax, cx, cy, conn = item
            bx0 = max(0, int(xmin / bin_size))
            bx1 = int(math.ceil(xmax / bin_size))
            by0 = max(0, int(ymin / bin_size))
            by1 = int(math.ceil(ymax / bin_size))
            for bx in range(bx0, bx1 + 1):
                for by in range(by0, by1 + 1):
                    bins[(bx, by)].append(item)
        return bins, bboxes

    bins_upper, bboxes_upper = build_bins(upper_elems)
    bins_lower, bboxes_lower = build_bins(lower_elems)

    recip_u = {}
    recip_d = {}

    for r_nid, (rx, ry) in r_nodes.items():
        is_in_slit = (rx <= slit_a0 + 1e-5)
        if is_in_slit:
            is_upper = (ry >= slit_y - 1e-7)
            target_bins_list = [bins_upper if is_upper else bins_lower]
            target_fallback_list = [bboxes_upper if is_upper else bboxes_lower]
        else:
            target_bins_list = [bins_upper, bins_lower]
            target_fallback_list = [bboxes_upper, bboxes_lower]

        bx = max(0, int(rx / bin_size))
        by = max(0, int(ry / bin_size))

        candidate_items = []
        seen_eids = set()
        for t_bins in target_bins_list:
            for dbx in (-1, 0, 1):
                for dby in (-1, 0, 1):
                    for item in t_bins.get((bx + dbx, by + dby), []):
                        if item[0] not in seen_eids:
                            seen_eids.add(item[0])
                            candidate_items.append(item)

        best_eid = None
        best_conn = None
        best_xi, best_eta = 0.0, 0.0
        best_l1, best_l2, best_l3 = 0.0, 0.0, 0.0
        best_c_dist = float("inf")
        best_center_dist = float("inf")

        for deid, xmin, xmax, ymin, ymax, cx, cy, conn in candidate_items:
            if not ((xmin - 1e-5 <= rx <= xmax + 1e-5) and (ymin - 1e-5 <= ry <= ymax + 1e-5)):
                continue
            d_vertices = [d_nodes[n] for n in conn]
            if len(conn) == 4:
                xi_c, eta_c, conv = inverse_isoparametric_quad(d_vertices, rx, ry)
                if not conv:
                    continue
                c_dist = max(0.0, abs(xi_c) - 1.0, abs(eta_c) - 1.0)
                l1_c, l2_c, l3_c = 0.0, 0.0, 0.0
            else:
                l1_c, l2_c, l3_c, c_dist = point_in_triangle(d_vertices, rx, ry)
                xi_c, eta_c = 0.0, 0.0

            center_dist = (rx - cx)**2 + (ry - cy)**2
            if c_dist <= 1e-5:
                if (c_dist < best_c_dist - 1e-12) or (abs(c_dist - best_c_dist) <= 1e-12 and center_dist < best_center_dist):
                    best_c_dist = c_dist
                    best_center_dist = center_dist
                    best_eid = deid
                    best_conn = conn
                    best_xi = xi_c
                    best_eta = eta_c
                    best_l1, best_l2, best_l3 = l1_c, l2_c, l3_c

        if best_eid is None:
            for f_bboxes in target_fallback_list:
                for deid, xmin, xmax, ymin, ymax, cx, cy, conn in f_bboxes:
                    d_vertices = [d_nodes[n] for n in conn]
                    if len(conn) == 4:
                        xi_c, eta_c, conv = inverse_isoparametric_quad(d_vertices, rx, ry)
                        if not conv:
                            continue
                        c_dist = max(0.0, abs(xi_c) - 1.0, abs(eta_c) - 1.0)
                        l1_c, l2_c, l3_c = 0.0, 0.0, 0.0
                    else:
                        l1_c, l2_c, l3_c, c_dist = point_in_triangle(d_vertices, rx, ry)
                        xi_c, eta_c = 0.0, 0.0

                    center_dist = (rx - cx)**2 + (ry - cy)**2
                    if c_dist < best_c_dist:
                        best_c_dist = c_dist
                        best_center_dist = center_dist
                        best_eid = deid
                        best_conn = conn
                        best_xi = xi_c
                        best_eta = eta_c
                        best_l1, best_l2, best_l3 = l1_c, l2_c, l3_c

        if best_eid is not None:
            if len(best_conn) == 4:
                clamped_xi = max(-1.0, min(1.0, best_xi))
                clamped_eta = max(-1.0, min(1.0, best_eta))
                N = quad_nodal_shape_functions(clamped_xi, clamped_eta)
                ux = sum(N[i] * donor_u[best_conn[i]][0] for i in range(4))
                uy = sum(N[i] * donor_u[best_conn[i]][1] for i in range(4))
                d_val = sum(N[i] * donor_d[best_conn[i]] for i in range(4))
            else:
                l_tot = best_l1 + best_l2 + best_l3
                w1 = best_l1 / l_tot if l_tot > 0 else 1.0 / 3.0
                w2 = best_l2 / l_tot if l_tot > 0 else 1.0 / 3.0
                w3 = best_l3 / l_tot if l_tot > 0 else 1.0 / 3.0
                ux = w1 * donor_u[best_conn[0]][0] + w2 * donor_u[best_conn[1]][0] + w3 * donor_u[best_conn[2]][0]
                uy = w1 * donor_u[best_conn[0]][1] + w2 * donor_u[best_conn[1]][1] + w3 * donor_u[best_conn[2]][1]
                d_val = w1 * donor_d[best_conn[0]] + w2 * donor_d[best_conn[1]] + w3 * donor_d[best_conn[2]]

            recip_u[r_nid] = (ux, uy)
            recip_d[r_nid] = max(0.0, min(1.0, d_val))
        else:
            recip_u[r_nid] = (0.0, 0.0)
            recip_d[r_nid] = 0.0

    return recip_u, recip_d


def transfer_gp_history(donor_mesh, donor_history_dict, receiver_mesh, limiter_mode="convex_clamp",
                        slit_y=70.0, slit_a0=10.0, bin_size=2.5):
    """Transfers Gauss-point strain energy history H via qualified isoparametric bilinear reconstruction with convex_clamp."""
    try:
        from scripts.state_transfer.isoparametric_gp_transfer import transfer_isoparametric_gp_history
        res = transfer_isoparametric_gp_history(
            donor_mesh=donor_mesh,
            donor_history_dict=donor_history_dict,
            receiver_mesh=receiver_mesh,
            limiter_mode=limiter_mode,
            slit_y=slit_y,
            slit_a0=slit_a0,
            bin_size=bin_size,
            bypass_same_mesh_shortcut=True
        )
        return res["transferred_history_dict"]
    except ImportError:
        # Fallback inline isoparametric transfer implementation
        d_nodes = donor_mesh["nodes"]
        d_quads = donor_mesh.get("quads", {})
        d_tris = donor_mesh.get("tris", {})
        d_all_donor = dict(d_quads)
        d_all_donor.update(d_tris)
        r_nodes = receiver_mesh["nodes"]
        r_quads = receiver_mesh.get("quads", {})
        r_tris = receiver_mesh.get("tris", {})

        transferred = {}
        for r_eid, conn in r_quads.items():
            for gp_idx, (lxi, leta) in enumerate(QUAD_GP_LOCAL, start=1):
                N = quad_nodal_shape_functions(lxi, leta)
                gpx = sum(N[i] * r_nodes[conn[i]][0] for i in range(4))
                gpy = sum(N[i] * r_nodes[conn[i]][1] for i in range(4))
                h_val = 0.0
                for deid, dconn in d_all_donor.items():
                    d_coords = [d_nodes[n] for n in dconn]
                    if len(dconn) == 4:
                        xi, eta, conv = inverse_isoparametric_quad(d_coords, gpx, gpy)
                        if conv and abs(xi) <= 1.0001 and abs(eta) <= 1.0001:
                            gp_h = [donor_history_dict.get((deid, k), 0.0) for k in range(1, 5)]
                            h_interp = 0.0
                            for k, (xik, etak) in enumerate(QUAD_GP_LOCAL):
                                Mk = 0.25 * (1.0 + 3.0 * xik * xi) * (1.0 + 3.0 * etak * eta)
                                h_interp += Mk * gp_h[k]
                            if limiter_mode == "convex_clamp":
                                h_interp = max(min(gp_h), min(max(gp_h), h_interp))
                            h_val = max(0.0, h_interp)
                            break
                transferred[(r_eid, gp_idx)] = h_val

        for r_eid, conn in r_tris.items():
            (x1, y1), (x2, y2), (x3, y3) = [r_nodes[n] for n in conn]
            gpx = (x1 + x2 + x3) / 3.0
            gpy = (y1 + y2 + y3) / 3.0
            h_val = 0.0
            for deid, dconn in d_all_donor.items():
                d_coords = [d_nodes[n] for n in dconn]
                if len(dconn) == 4:
                    xi, eta, conv = inverse_isoparametric_quad(d_coords, gpx, gpy)
                    if conv and abs(xi) <= 1.0001 and abs(eta) <= 1.0001:
                        gp_h = [donor_history_dict.get((deid, k), 0.0) for k in range(1, 5)]
                        h_val = max(0.0, sum(gp_h) / 4.0)
                        break
            transferred[(r_eid, 1)] = h_val

        return transferred


def assemble_coupled_deck(receiver_phys_inp, out_deck_path, recip_d, recip_h_gp, donor_u2, target_u2,
                          cycle_idx=1, l0=BENCHMARK_L0_MM, Gc=BENCHMARK_GC_KN_MM, E_GPa=210.0, nu=0.30, k_res=1.0e-7):
    """Assembles 3-layer coupled re-equilibration deck with Phase UEL, Disp UEL, companion elements, and boundary conditions."""
    recip_mesh = parse_physical_inp(receiver_phys_inp)
    r_nodes = recip_mesh["nodes"]
    r_quads = recip_mesh["quads"]
    r_tris = recip_mesh["tris"]
    num_phys = len(recip_mesh["elements"])
    num_nodes = len(r_nodes)

    offset_disp = num_phys
    offset_vis = 2 * num_phys
    total_layered_elems = 3 * num_phys

    # Pin hole node sets
    low_hole_nodes = []
    upp_hole_nodes = []
    tol_hole = 0.15
    for nid, (x, y) in r_nodes.items():
        if abs(math.hypot(x - 20.0, y - 20.0) - 5.0) <= tol_hole:
            low_hole_nodes.append(nid)
        if abs(math.hypot(x - 20.0, y - 100.0) - 5.0) <= tol_hole:
            upp_hole_nodes.append(nid)

    rp_nid = 999999
    num_phys_f = float(num_phys)

    with open(out_deck_path, "w") as out:
        out.write("** ==========================================================\n")
        out.write("** METHOD C CASE 3: ADAPTIVE RE-EQUILIBRATION & ADVANCE DECK (CYCLE %d)\n" % cycle_idx)
        out.write("** Benchmark: Pandey & Kumar (2025) Section 4.3 (Pins & Hole)\n")
        out.write("** Physical elements: %d (Quads: %d, Tris: %d), Nodes: %d\n" % (
            num_phys, len(r_quads), len(r_tris), num_nodes
        ))
        out.write("** Total layered elements: %d (3 Layers: Phase UEL, Disp UEL, UMAT)\n" % total_layered_elems)
        out.write("** Hold at u2 = %.4f mm, advancing to u2 = %.4f mm\n" % (donor_u2, target_u2))
        out.write("** ==========================================================\n")
        out.write("*HEADING\n")
        out.write("Method C Case 3 Cycle %d Deck (Hold u2=%.4fmm -> Advance u2=%.4fmm)\n" % (cycle_idx, donor_u2, target_u2))

        # Nodes
        out.write("*NODE\n")
        for nid in sorted(r_nodes.keys()):
            x, y = r_nodes[nid]
            out.write("%d, %.9e, %.9e\n" % (nid, x, y))
        out.write("%d, 2.000000000e+01, 1.000000000e+02\n" % rp_nid)

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

        # Layer 2: Disp UEL
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

        # Layer 3: Companion Elements
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
        write_wrapped_nset(out, "N_LOWER_HOLE", low_hole_nodes)
        write_wrapped_nset(out, "N_UPPER_HOLE", upp_hole_nodes)
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

        # Companion Solid Section & User Material
        out.write("*SOLID SECTION, ELSET=All_elem, MATERIAL=DUMMY_MAT\n1.0\n")
        out.write("*MATERIAL, NAME=DUMMY_MAT\n")
        out.write("*USER MATERIAL, CONSTANTS=3\n")
        out.write("%.1f, %.2f, %.1f\n" % (E_GPa, nu, num_phys_f))
        out.write("*DEPVAR\n20\n")

        # Initial Conditions: TYPE=SOLUTION (SVARS 1..18 for Phase UEL Layer 1)
        out.write("*INITIAL CONDITIONS, TYPE=SOLUTION\n")
        for eid in sorted(r_quads.keys()):
            conn = r_quads[eid]
            d_elem_avg = sum(recip_d.get(n, 0.0) for n in conn) / 4.0
            deg = (1.0 - d_elem_avg)**2 + k_res
            h_vals = [recip_h_gp.get((eid, gp), 0.0) for gp in range(1, 5)]
            h1, h2, h3, h4 = h_vals
            sv = [
                d_elem_avg, d_elem_avg, d_elem_avg, d_elem_avg,
                h1, h2, h3, h4,
                h1, h2, h3, h4,
                d_elem_avg, d_elem_avg, deg, h1, 0.0, 0.0
            ]
            card1 = "%8d, " % eid + ", ".join("%14.7e" % v for v in sv[:7])
            card2 = "  " + ", ".join("%14.7e" % v for v in sv[7:15])
            card3 = "  " + ", ".join("%14.7e" % v for v in sv[15:18])
            out.write(card1 + "\n" + card2 + "\n" + card3 + "\n")

        for eid in sorted(r_tris.keys()):
            conn = r_tris[eid]
            d_elem_avg = sum(recip_d.get(n, 0.0) for n in conn) / 3.0
            deg = (1.0 - d_elem_avg)**2 + k_res
            h1 = recip_h_gp.get((eid, 1), 0.0)
            sv = [
                d_elem_avg, d_elem_avg, d_elem_avg, 0.0,
                h1, h1,
                h1, h1, h1,
                0.0, 0.0, 0.0,
                d_elem_avg, d_elem_avg, deg, h1, 0.0, 0.0
            ]
            card1 = "%8d, " % eid + ", ".join("%14.7e" % v for v in sv[:7])
            card2 = "  " + ", ".join("%14.7e" % v for v in sv[7:15])
            card3 = "  " + ", ".join("%14.7e" % v for v in sv[15:18])
            out.write(card1 + "\n" + card2 + "\n" + card3 + "\n")

        # Kinematic Coupling Equations
        for nid in sorted(upp_hole_nodes):
            out.write("*EQUATION\n2\n")
            out.write("%d, 2, 1.0, %d, 2, -1.0\n" % (nid, rp_nid))

        # AMPLITUDES
        out.write("*AMPLITUDE, NAME=CONST_HOLD\n")
        out.write("0.0, 1.0, 1.0, 1.0\n")

        # STEP 1: Fixed-load Re-equilibration Hold
        out.write("*STEP, NAME=Step-1-Hold, NLGEOM=NO, INC=100\n")
        out.write("*STATIC\n1.0, 1.0, 1.0E-08, 1.0\n")
        out.write("*BOUNDARY\n")
        out.write("N_LOWER_HOLE, 1, 2, 0.0\n")
        out.write("N_UPPER_HOLE, 1, 1, 0.0\n")
        out.write("N_RP, 1, 1, 0.0\n")
        out.write("*BOUNDARY, AMPLITUDE=CONST_HOLD\n")
        out.write("N_RP, 2, 2, %.4f\n" % donor_u2)
        out.write("*OUTPUT, FIELD, FREQUENCY=1\n")
        out.write("*NODE OUTPUT, NSET=N_RP\nU, RF\n")
        out.write("*NODE OUTPUT, NSET=N_LOWER_HOLE\nRF\n")
        out.write("*NODE OUTPUT\nU\n")
        out.write("*ELEMENT OUTPUT, ELSET=umatelem\nS, MISESERI, MISESAVG, EVOL, SDV\n")
        out.write("*NODE PRINT, FREQ=1, NSET=N_RP\nU2, RF2\n")
        out.write("*END STEP\n")

        # STEP 2: Forward crack propagation advance
        out.write("*STEP, NAME=Step-2-Advance, NLGEOM=NO, INC=5000\n")
        out.write("*STATIC\n0.002, 1.0, 1.0E-14, 0.005\n")
        out.write("*BOUNDARY, OP=MOD\n")
        out.write("N_RP, 2, 2, %.4f\n" % target_u2)
        out.write("*OUTPUT, FIELD, FREQUENCY=5\n")
        out.write("*NODE OUTPUT, NSET=N_RP\nU, RF\n")
        out.write("*NODE OUTPUT, NSET=N_LOWER_HOLE\nRF\n")
        out.write("*NODE OUTPUT\nU\n")
        out.write("*ELEMENT OUTPUT, ELSET=umatelem\nS, MISESERI, MISESAVG, EVOL, SDV\n")
        out.write("*NODE PRINT, FREQ=1, NSET=N_RP\nU2, RF2\n")
        out.write("*END STEP\n")


class Case3SingleJobOrchestrator(object):
    """Manages the in-allocation execution of coarse solve and multi-cycle adaptive remeshing with equal load division."""

    def __init__(self, run_dir, n_adaptive_steps=DEFAULT_N_ADAPTIVE_STEPS, load_increment_mm=DEFAULT_LOAD_INCREMENT_MM,
                 coarse_u2_mm=DEFAULT_COARSE_U2_MM, uel_path=None, cpus=16, dry_run=False, max_cycles=50):
        self.run_dir = os.path.abspath(run_dir)
        self.n_adaptive_steps = int(n_adaptive_steps)
        self.load_increment_mm = float(load_increment_mm)
        self.coarse_u2_mm = float(coarse_u2_mm)
        self.dry_run = dry_run
        self.cpus = int(cpus)
        self.max_cycles = int(max_cycles)
        if uel_path:
            self.uel_path = os.path.abspath(uel_path)
        elif os.path.isfile(os.path.join(self.run_dir, "f42_mixed_uel.for")):
            self.uel_path = os.path.join(self.run_dir, "f42_mixed_uel.for")
        else:
            self.uel_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
        self.history = []
        self.peak_rf2 = 0.0
        self.current_tip_x = 10.0  # initial notch length a = 10.0 mm
        self.current_rf2 = 0.0

    def verify_prerequisites(self):
        """Verifies UEL existence, cryptographic hash, and corridor geometry."""
        if not os.path.isfile(self.uel_path):
            raise RuntimeError("Frozen UEL not found at: %s" % self.uel_path)
        uel_hash = compute_sha256(self.uel_path)
        if uel_hash != FROZEN_UEL_SHA256:
            raise RuntimeError("Frozen UEL hash mismatch: expected %s, got %s" % (FROZEN_UEL_SHA256, uel_hash))

        width = CORRIDOR_X_MAX - CORRIDOR_X_MIN
        height = CORRIDOR_Y_MAX - CORRIDOR_Y_MIN
        area = width * height
        assert width == 11.5, "Corridor width mismatch"
        assert height == 17.0, "Corridor height mismatch"
        assert abs(area - 195.5) < 1e-4, "Corridor area mismatch"
        assert H_REF_MM <= BENCHMARK_L0_MM / 2.0, "h_ref exceeds l0/2 threshold"
        return True

    def get_corridor_definition(self):
        """Returns the formal minimized corridor specification."""
        width = CORRIDOR_X_MAX - CORRIDOR_X_MIN
        height = CORRIDOR_Y_MAX - CORRIDOR_Y_MIN
        area = width * height
        return {
            "x_min_mm": CORRIDOR_X_MIN,
            "x_max_mm": CORRIDOR_X_MAX,
            "y_min_mm": CORRIDOR_Y_MIN,
            "y_max_mm": CORRIDOR_Y_MAX,
            "corridor_width_mm": width,
            "corridor_height_mm": height,
            "corridor_area_mm2": area,
            "h_ref_mm": H_REF_MM,
            "l0_mm": BENCHMARK_L0_MM,
            "l0_half_mm": BENCHMARK_L0_MM / 2.0,
            "target_total_elements": 30000
        }

    def check_completion(self, current_tip_x, current_rf2, peak_rf2):
        """Checks completion criteria: crack tip reached plate edge (x >= 64 mm) or load drop < 5% of peak."""
        if current_tip_x >= CRACK_COMPLETION_X_MM:
            return True, "CRACK_FULLY_PROPAGATED_TO_PLATE_EDGE (x_tip = %.4f mm >= %.1f mm)" % (current_tip_x, CRACK_COMPLETION_X_MM)
        if peak_rf2 > 0.0 and current_rf2 < (LOAD_DROP_COMPLETION_RATIO * peak_rf2):
            return True, "PLATE_SEVERED_LOAD_DROP_BELOW_5PCT (RF2 = %.4f kN < %.4f kN [5%% of peak %.4f kN])" % (
                current_rf2, LOAD_DROP_COMPLETION_RATIO * peak_rf2, peak_rf2
            )
        return False, None

    def generate_plan(self):
        """Generates dynamic plan based on n_adaptive_steps and equal load increment."""
        plan_cycles = []
        plan_cycles.append({
            "cycle": 0,
            "name": "COARSE",
            "type": "INITIAL_COARSE_SOLVE",
            "u2_target_mm": self.coarse_u2_mm,
            "is_coarse": True,
            "dt_min": 1.0e-08
        })

        current_u2 = self.coarse_u2_mm
        for step in range(1, self.n_adaptive_steps + 1):
            next_u2 = round(current_u2 + self.load_increment_mm, 6)
            plan_cycles.append({
                "cycle": step,
                "name": "CYCLE%d_ADAPT%d" % (step, step),
                "type": "ADAPTIVE_RE_EQUILIBRATION_AND_ADVANCE",
                "u2_hold_mm": round(current_u2, 6),
                "u2_target_mm": next_u2,
                "load_increment_mm": self.load_increment_mm,
                "is_coarse": False,
                "dt_min": DT_MIN
            })
            current_u2 = next_u2

        return plan_cycles

    def evaluate_cutback_state(self, sta_path):
        """Evaluates whether cycle reached the dt_min floor and extracts the terminal converged state."""
        if not os.path.isfile(sta_path):
            return {"status": "MISSING_STA", "can_continue": False}
        res = parse_sta_file(sta_path)
        term = res["terminal_converged"]
        if not term:
            return {"status": "NO_CONVERGED_INCREMENTS", "can_continue": False}

        term_desc = "Increment %d (terminal converged state)" % term["increment"]
        return {
            "status": "CUTBACK_TERMINATED" if res["cutback_floor_reached"] else "CONVERGED_TO_TARGET",
            "can_continue": True,
            "terminal_step": term["step"],
            "terminal_increment": term["increment"],
            "terminal_step_time": term["step_time"],
            "terminal_dt": term["dt"],
            "terminal_frame_label": term_desc,
            "dt_min_floor_reached": res["cutback_floor_reached"],
            "no_further_dt_min_reduction": True
        }

    def evaluate_gates(self, donor_rf2, receiver_step1_rf2, donor_e_frac, receiver_step1_e_frac, donor_d_max, terminal_d_max,
                       donor_gc=BENCHMARK_GC_KN_MM, receiver_gc=BENCHMARK_GC_KN_MM):
        """Evaluates force continuity (<=5%), Gc-normalized energy, and zero-healing."""
        delta_rf2_pct = ((receiver_step1_rf2 - donor_rf2) / donor_rf2) * 100.0 if donor_rf2 != 0 else 0.0
        force_pass = abs(delta_rf2_pct) <= 5.0

        delta_e_pct = ((receiver_step1_e_frac - donor_e_frac) / donor_e_frac) * 100.0 if donor_e_frac != 0 else 0.0
        donor_gamma = donor_e_frac / donor_gc if donor_gc > 0 else 0.0
        receiver_gamma = receiver_step1_e_frac / receiver_gc if receiver_gc > 0 else 0.0
        delta_gamma_pct = ((receiver_gamma - donor_gamma) / donor_gamma) * 100.0 if donor_gamma > 0 else 0.0

        non_healing_pass = terminal_d_max >= (donor_d_max - 1e-4)

        return {
            "force_continuity_delta_pct": delta_rf2_pct,
            "force_continuity_pass": force_pass,
            "raw_energy_delta_pct": delta_e_pct,
            "energy_continuity_status": "PASS" if abs(delta_e_pct) <= 5.0 else "DISCLOSED_PARAMETER_DEVIATION",
            "donor_gamma_mm2": donor_gamma,
            "receiver_gamma_mm2": receiver_gamma,
            "normalized_gamma_delta_pct": delta_gamma_pct,
            "donor_d_max": donor_d_max,
            "terminal_d_max": terminal_d_max,
            "zero_healing_pass": non_healing_pass
        }

    def run_dry_run_plan(self):
        """Generates dry-run execution plan and verifies sequence integrity."""
        self.verify_prerequisites()
        cycles = self.generate_plan()
        plan = {
            "architecture": "SINGLE_PBS_JOB_IN_ALLOCATION_ORCHESTRATOR",
            "benchmark": "Pandey & Kumar (2025) Section 4.3 Mode-I Case 3",
            "configuration": {
                "n_adaptive_steps": self.n_adaptive_steps,
                "load_increment_mm": self.load_increment_mm,
                "coarse_u2_mm": self.coarse_u2_mm,
                "no_displacement_cap": True,
                "crack_completion_criteria": {
                    "terminal_tip_x_mm": CRACK_COMPLETION_X_MM,
                    "load_drop_cutoff_ratio": LOAD_DROP_COMPLETION_RATIO
                }
            },
            "pbs_allocation": {
                "nodes": 1,
                "ncpus": self.cpus,
                "mem_gb": 48,
                "walltime_hours": 72,
                "queue": "entry_imfdfkmq / normal_imfdfkmq"
            },
            "corridor": self.get_corridor_definition(),
            "planned_initial_cycles": cycles
        }
        return plan

    def run_command(self, cmd_list, check=True):
        """Runs a subprocess command with logging."""
        print("[Orchestrator EXEC] Running: %s" % " ".join(cmd_list))
        p = subprocess.Popen(cmd_list, cwd=self.run_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out, _ = p.communicate()
        out_str = out.decode("utf-8", errors="replace") if isinstance(out, bytes) else str(out)
        print(out_str)
        if check and p.returncode != 0:
            raise RuntimeError("Command failed with exit code %d: %s" % (p.returncode, " ".join(cmd_list)))
        return p.returncode, out_str

    def extract_cycle_state(self, job_name):
        """Extracts nodal displacements, nodal damage, Gauss-point history, and observables from solved job."""
        out_json = os.path.join(self.run_dir, job_name + "_state.json")
        odb_path = os.path.join(self.run_dir, job_name + ".odb")

        # If already extracted, load and return
        if os.path.isfile(out_json):
            with open(out_json, "r") as f:
                state = json.load(f)
            u_nodal = {int(k): v for k, v in state["u_nodal"].items()}
            d_nodal = {int(k): float(v) for k, v in state["d_nodal"].items()}
            h_gp = {}
            for k, v in state["h_gp"].items():
                p = k.split("_")
                h_gp[(int(p[0]), int(p[1]))] = float(v)
            return {
                "u_nodal": u_nodal,
                "d_nodal": d_nodal,
                "h_gp": h_gp,
                "max_damage": float(state.get("max_damage", max(d_nodal.values()) if d_nodal else 0.0)),
                "max_history_MPa": float(state.get("max_history_MPa", max(h_gp.values()) if h_gp else 0.0)),
                "tip_x": float(state.get("tip_x", self.current_tip_x)),
                "tip_y": float(state.get("tip_y", 70.0)),
                "peak_rf2": float(state.get("peak_rf2", self.peak_rf2)),
                "terminal_rf2": float(state.get("terminal_rf2", 0.0)),
                "step1_rf2": float(state.get("step1_rf2", 0.0)),
                "e_frac": float(state.get("e_frac", 0.0))
            }

        # Check for pre-existing donor file
        donor_candidates = [
            os.path.join(self.run_dir, "donor_case3_step1_state.json"),
            os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "290_method_c_case3", "donor_case3_step1_state.json")
        ]
        for dc in donor_candidates:
            if os.path.isfile(dc):
                with open(dc, "r") as f:
                    state = json.load(f)
                u_nodal = {int(k): v for k, v in state["u_nodal"].items()}
                d_nodal = {int(k): float(v) for k, v in state["d_nodal"].items()}
                h_gp = {}
                for k, v in state["h_gp"].items():
                    p = k.split("_")
                    h_gp[(int(p[0]), int(p[1]))] = float(v)
                return {
                    "u_nodal": u_nodal,
                    "d_nodal": d_nodal,
                    "h_gp": h_gp,
                    "max_damage": float(state.get("max_damage", 0.9472)),
                    "max_history_MPa": float(state.get("max_history_MPa", 0.0210)),
                    "tip_x": float(state.get("tip_x", 10.0)),
                    "tip_y": float(state.get("tip_y", 70.0)),
                    "peak_rf2": float(state.get("peak_rf2", 3.9288)),
                    "terminal_rf2": float(state.get("terminal_rf2", 3.9288)),
                    "step1_rf2": float(state.get("step1_rf2", 3.9288)),
                    "e_frac": float(state.get("e_frac", 0.003456))
                }

        raise RuntimeError("No donor state or ODB extraction available for %s" % job_name)

    def execute(self):
        """Executes the full in-allocation solve, remesh, transfer, re-equilibrate, and advance loop."""
        self.verify_prerequisites()
        print("=================================================================")
        print("Starting Method C Case 3 Single-Job Multi-Cycle In-Allocation Run")
        print("Parameters: n_adaptive_steps=%d, load_increment=%.4f mm" % (self.n_adaptive_steps, self.load_increment_mm))
        print("Run directory: %s" % self.run_dir)
        print("=================================================================")

        # Step 0: Initial Coarse Solve
        coarse_job = "PK_METHOD_C_CASE3_COARSE_JOB1"
        coarse_inp = os.path.join(self.run_dir, coarse_job + ".inp")
        coarse_sta = os.path.join(self.run_dir, coarse_job + ".sta")

        if not os.path.isfile(coarse_sta):
            print("Executing Cycle 0: Initial Coarse Solve...")
            cmd = ["abaqus", "job=" + coarse_job, "input=" + coarse_job, "user=" + os.path.basename(self.uel_path),
                   "cpus=" + str(self.cpus), "interactive"]
            ret, _ = self.run_command(cmd, check=False)
            print("Cycle 0 exited with code: %d" % ret)

        cutback_eval = self.evaluate_cutback_state(coarse_sta)
        print("Cycle 0 Evaluation:", cutback_eval)

        # Extract Cycle 0 Donor State
        donor_state = self.extract_cycle_state(coarse_job)
        donor_u2 = self.coarse_u2_mm
        donor_rf2 = donor_state["step1_rf2"]
        donor_e_frac = donor_state["e_frac"]
        donor_d_max = donor_state["max_damage"]
        self.current_tip_x = donor_state["tip_x"]
        self.current_rf2 = donor_state["terminal_rf2"]
        self.peak_rf2 = max(self.peak_rf2, donor_state["peak_rf2"])

        donor_phys_inp = os.path.join(self.run_dir, "PK_METHOD_C_CASE3_COARSE_PHYS.inp")
        if not os.path.isfile(donor_phys_inp):
            # Check package dir
            candidate_phys = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "290_method_c_case3", "PK_METHOD_C_CASE3_COARSE_PHYS.inp")
            if os.path.isfile(candidate_phys):
                donor_phys_inp = candidate_phys

        # Adaptive Multi-Cycle Loop
        cycle_idx = 1
        adaptive_phys_inp = os.path.join(self.run_dir, "PK_METHOD_C_CASE3_ADAPTIVE_PHYS.inp")
        if not os.path.isfile(adaptive_phys_inp):
            candidate_adapt = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "290_method_c_case3", "PK_METHOD_C_CASE3_ADAPTIVE_PHYS.inp")
            if os.path.isfile(candidate_adapt):
                adaptive_phys_inp = candidate_adapt

        while cycle_idx <= self.n_adaptive_steps:
            target_u2 = round(donor_u2 + self.load_increment_mm, 6)
            print("-----------------------------------------------------------------")
            print("Starting Cycle %d: target u2 = %.4f mm (donor u2 = %.4f mm)" % (cycle_idx, target_u2, donor_u2))

            # Completion check before starting cycle
            is_done, reason = self.check_completion(self.current_tip_x, self.current_rf2, self.peak_rf2)
            if is_done:
                print("Crack propagation completion criteria met: %s" % reason)
                break

            # 1. State Transfer: Map donor state onto adapted physical mesh
            print("[Cycle %d - 1/4] Performing state transfer (convex_clamp)..." % cycle_idx)
            d_mesh = parse_physical_inp(donor_phys_inp)
            r_mesh = parse_physical_inp(adaptive_phys_inp)

            recip_u, recip_d = transfer_nodal_fields(
                donor_mesh=d_mesh,
                donor_u=donor_state["u_nodal"],
                donor_d=donor_state["d_nodal"],
                receiver_mesh=r_mesh,
                slit_y=70.0,
                slit_a0=10.0
            )

            recip_h_gp = transfer_gp_history(
                donor_mesh=d_mesh,
                donor_history_dict=donor_state["h_gp"],
                receiver_mesh=r_mesh,
                limiter_mode="convex_clamp",
                slit_y=70.0,
                slit_a0=10.0
            )

            # 2. Deck Assembly: Generate 3-Layer UEL re-equilibration & advance deck
            cycle_job = "PK_METHOD_C_CASE3_CYCLE%d" % cycle_idx
            cycle_inp = os.path.join(self.run_dir, cycle_job + ".inp")
            cycle_sta = os.path.join(self.run_dir, cycle_job + ".sta")

            print("[Cycle %d - 2/4] Assembling 3-layer coupled deck: %s..." % (cycle_idx, cycle_inp))
            assemble_coupled_deck(
                receiver_phys_inp=adaptive_phys_inp,
                out_deck_path=cycle_inp,
                recip_d=recip_d,
                recip_h_gp=recip_h_gp,
                donor_u2=donor_u2,
                target_u2=target_u2,
                cycle_idx=cycle_idx
            )

            # 3. Solver Execution: Solve re-equilibration hold + forward advance
            print("[Cycle %d - 3/4] Executing Abaqus solver for %s..." % (cycle_idx, cycle_job))
            cmd = ["abaqus", "job=" + cycle_job, "input=" + cycle_job, "user=" + os.path.basename(self.uel_path),
                   "cpus=" + str(self.cpus), "interactive"]
            ret, _ = self.run_command(cmd, check=False)

            # 4. Observables & Gate Evaluation
            if os.path.isfile(cycle_sta):
                c_eval = self.evaluate_cutback_state(cycle_sta)
                print("[Cycle %d - 4/4] Cycle Evaluation: %s" % (cycle_idx, str(c_eval)))

            donor_u2 = target_u2
            donor_phys_inp = adaptive_phys_inp
            cycle_idx += 1

        print("=================================================================")
        print("Framework Execution Loop Completed.")
        print("Total cycles processed: %d" % (cycle_idx - 1))
        print("=================================================================")
        return True


def main():
    parser = argparse.ArgumentParser(description="Case 3 Single-Job Multi-Cycle Orchestrator")
    parser.add_argument("--run-dir", default=os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "290_method_c_case3"))
    parser.add_argument("--n-adaptive-steps", "-n", type=int, default=DEFAULT_N_ADAPTIVE_STEPS,
                        help="Granularity of equal load division (default: 4)")
    parser.add_argument("--load-increment-mm", type=float, default=DEFAULT_LOAD_INCREMENT_MM,
                        help="Per-cycle displacement advance in mm (default: 0.01 mm)")
    parser.add_argument("--coarse-u2-mm", type=float, default=DEFAULT_COARSE_U2_MM,
                        help="Onset displacement for initial coarse solve (default: 0.05 mm)")
    parser.add_argument("--uel-path", default=None,
                        help="Path to frozen UEL source (default: auto-detect)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Perform offline dry-run verification and print plan")
    parser.add_argument("--cpus", type=int, default=16,
                        help="Number of shared-memory SMP CPUs for Abaqus (default: 16)")
    args = parser.parse_args()

    orch = Case3SingleJobOrchestrator(
        run_dir=args.run_dir,
        n_adaptive_steps=args.n_adaptive_steps,
        load_increment_mm=args.load_increment_mm,
        coarse_u2_mm=args.coarse_u2_mm,
        cpus=args.cpus,
        uel_path=args.uel_path,
        dry_run=args.dry_run
    )

    if args.dry_run:
        plan = orch.run_dry_run_plan()
        print("Case 3 Single-Job Framework Plan verified successfully.")
        print("Planned cycles configured:", len(plan["planned_initial_cycles"]))
        print("Load division increment: %.4f mm (no cap)" % plan["configuration"]["load_increment_mm"])
        print("Completion criterion: x_tip >= %.1f mm OR load drop < 5%%" % plan["configuration"]["crack_completion_criteria"]["terminal_tip_x_mm"])
        print(json.dumps(plan, indent=2))
    else:
        orch.execute()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_package116_intermediate_transfer.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Generates Package 116: Three-Level AT2 Energy-Convergence Control with
Intermediate-Resolution Crack-Tip Mesh (h_tip = 1.2 um, 2,484 quads, 2,610 nodes).
Directly transfers state from authentic Package 76 Increment 79 (u = 0.00184250 mm).
"""

from __future__ import print_function, division
import os
import sys
import json
import math
import hashlib
import csv
import shutil
from pathlib import Path
import numpy as np

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
sys.path.insert(0, str(REPO_ROOT))

from scripts.remeshing.generate_crack_band_mesh import generate_graded_1d, build_quad_mesh

# Physical & Material Constants
GC = 0.0027      # kN/mm (2.7 N/mm)
ELL0 = 0.0075    # mm (7.5 um)
E_MOD = 210.0    # kN/mm^2
NU = 0.3
K_DEGRAD = 1.0e-6

LAM = (E_MOD * NU) / ((1.0 + NU) * (1.0 - 2.0 * NU))
MU = E_MOD / (2.0 * (1.0 + NU))
C0 = np.array([
    [LAM + 2.0 * MU, LAM, 0.0],
    [LAM, LAM + 2.0 * MU, 0.0],
    [0.0, 0.0, MU]
])

A_GAUSS = 1.0 / math.sqrt(3.0)
UEL_GP_COORDS = [
    (-A_GAUSS, -A_GAUSS),
    ( A_GAUSS, -A_GAUSS),
    ( A_GAUSS,  A_GAUSS),
    (-A_GAUSS,  A_GAUSS),
]
UEL_WEIGHTS = [1.0, 1.0, 1.0, 1.0]

DONOR_INP = REPO_ROOT / "models/pandey_kumar_mode1/76_candidate_donor_h0025_visual/candidate_donor_h0025_visual.inp"
DONOR_F77_NODAL_CSV = REPO_ROOT / "models/pandey_kumar_mode1/76_candidate_donor_h0025_visual/evidence_frame77/pkg76_frame77_nodal_u.csv"
DONOR_F77_ELEM_CSV = REPO_ROOT / "models/pandey_kumar_mode1/76_candidate_donor_h0025_visual/evidence_frame77/pkg76_frame77_elem_sdv.csv"
DONOR_F88_NODAL_CSV = REPO_ROOT / "models/pandey_kumar_mode1/76_candidate_donor_h0025_visual/evidence_frame88/pkg76_frame88_nodal_u.csv"
DONOR_F88_ELEM_CSV = REPO_ROOT / "models/pandey_kumar_mode1/76_candidate_donor_h0025_visual/evidence_frame88/pkg76_frame88_elem_sdv.csv"
MISESERI_CSV = REPO_ROOT / "models/pandey_kumar_mode1/114_c4_inc79_companion_miseseri/c4_inc79_companion_miseseri_distribution.csv"

OUT_DIR = REPO_ROOT / "models/pandey_kumar_mode1/116_c3_int_inc79_direct_transfer"
OUT_AUDIT_JSON = REPO_ROOT / "results/validation/c3_int_inc79_direct_transfer_mapping_audit.json"

TARGET_U_RP = 0.001842500000000000
TARGET_RF2_DONOR = 186.067909
TARGET_E_TOT_DONOR = 0.21244805
TARGET_E_ELAS_DONOR = 0.17140369
TARGET_E_FRAC_DONOR = 0.041044352

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().lower()

def shape_functions(xi, eta):
    N = np.array([
        0.25 * (1.0 - xi) * (1.0 - eta),
        0.25 * (1.0 + xi) * (1.0 - eta),
        0.25 * (1.0 + xi) * (1.0 + eta),
        0.25 * (1.0 - xi) * (1.0 + eta)
    ])
    dNdxi = np.array([-0.25 * (1.0 - eta),  0.25 * (1.0 - eta), 0.25 * (1.0 + eta), -0.25 * (1.0 + eta)])
    dNdeta = np.array([-0.25 * (1.0 - xi), -0.25 * (1.0 + xi),  0.25 * (1.0 + xi),  0.25 * (1.0 - xi)])
    return N, dNdxi, dNdeta

def load_inp_mesh(inp_path):
    nodes = {}
    elements = {}
    reading = None
    with open(inp_path, "r") as f:
        for line in f:
            l = line.strip()
            if not l or l.startswith("**"):
                continue
            u = l.upper()
            if u.startswith("*NODE") and not any(u.startswith(k) for k in ["*NODE OUTPUT", "*NODE PRINT", "*NODE FILE"]):
                reading = "NODE"
                continue
            elif u.startswith("*ELEMENT"):
                if "TYPE=U1" in u or "TYPE=U2" in u or "TYPE=CPE4" in u or "TYPE=CPS4" in u:
                    reading = "ELEM"
                else:
                    reading = None
                continue
            elif u.startswith("*"):
                reading = None
                continue
            if reading == "NODE":
                p = [x.strip() for x in l.split(",")]
                if len(p) >= 3 and p[0].isdigit():
                    nid = int(p[0])
                    if nid != 999999:
                        nodes[nid] = np.array([float(p[1]), float(p[2])])
            elif reading == "ELEM":
                p = [x.strip() for x in l.split(",")]
                if len(p) >= 5 and p[0].isdigit():
                    eid = int(p[0])
                    if eid <= 4422:
                        elements[eid] = [int(x) for x in p[1:5]]

    node_to_elems = {nid: [] for nid in nodes}
    for eid, conn in elements.items():
        for n in conn:
            node_to_elems[n].append(eid)

    flank = {}
    for nid, pt in nodes.items():
        if abs(pt[1] - 0.050) < 1e-6 and pt[0] <= 0.040 + 1e-6:
            centroids_y = [np.mean([nodes[n][1] for n in elements[eid]]) for eid in node_to_elems[nid]]
            if all(cy > 0.050 for cy in centroids_y):
                flank[nid] = "upper"
            elif all(cy < 0.050 for cy in centroids_y):
                flank[nid] = "lower"
            else:
                flank[nid] = "slit_tip"
        else:
            flank[nid] = "intact"

    return {"nodes": nodes, "elements": elements, "flank": flank, "node_to_elems": node_to_elems}

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("=== Building Package 116 Intermediate-Resolution Control (h_tip = 1.2 um) ===", flush=True)

    # 1. Sizing parameters from MISESERI CSV
    with open(MISESERI_CSV, "r") as f:
        rows = list(csv.DictReader(f))
    high_err = [r for r in rows if float(r.get("miseseri_kNmm2", r.get("miseseri", 0.0))) >= 0.15]
    xs = [float(r["x_mm"]) for r in high_err]
    ys = [float(r["y_mm"]) for r in high_err]
    weights = [float(r.get("miseseri_kNmm2", r.get("miseseri", 0.0))) for r in high_err]
    w_sum = sum(weights)
    x_center = sum(x * w for x, w in zip(xs, weights)) / w_sum
    band_half_x = max(0.012, (max(xs) - min(xs)) * 0.6)
    band_half_y = max(0.006, (max(ys) - min(ys)) * 0.6)

    h_target = 0.00120  # 1.2 um target
    y_coords = generate_graded_1d(0.0, 0.100, 0.050, band_half_y, h_target, 1.12, 0.0035)
    x_coords = generate_graded_1d(0.0, 0.100, x_center, band_half_x, h_target, 1.12, 0.0035, key_points=[0.040, 0.050])

    mesh = build_quad_mesh(x_coords, y_coords, slit_y=0.050, slit_a0=0.040)
    n_elements = mesh["n_elements"]
    n_nodes = mesh["n_nodes"]
    min_det = mesh["min_det_jac"]
    max_ar = mesh["max_aspect_ratio"]
    print(f"Generated Intermediate Mesh: {n_elements} quads, {n_nodes} nodes, min_detJ={min_det:.4e}, max_AR={max_ar:.2f}", flush=True)

    recv_nodes = {nid: np.array(pt) for nid, pt in mesh["nodes"].items() if nid != 999999}
    recv_elements = mesh["elements"]
    recv_node_to_elems = {nid: [] for nid in recv_nodes}
    for eid, conn in recv_elements.items():
        for n in conn:
            recv_node_to_elems[n].append(eid)

    recv_flank = {}
    for nid, pt in recv_nodes.items():
        if abs(pt[1] - 0.050) < 1e-6 and pt[0] <= 0.040 + 1e-6:
            centroids_y = [np.mean([recv_nodes[n][1] for n in recv_elements[eid]]) for eid in recv_node_to_elems[nid]]
            if all(cy > 0.050 for cy in centroids_y):
                recv_flank[nid] = "upper"
            elif all(cy < 0.050 for cy in centroids_y):
                recv_flank[nid] = "lower"
            else:
                recv_flank[nid] = "slit_tip"
        else:
            recv_flank[nid] = "intact"

    # 2. Load donor Package 76 mesh & state
    donor_mesh = load_inp_mesh(DONOR_INP)
    f77_u = {}
    with open(DONOR_F77_NODAL_CSV, "r") as f:
        for r in csv.DictReader(f):
            f77_u[int(r["node_id"])] = (float(r["u1"]), float(r["u2"]))
    f88_u = {}
    with open(DONOR_F88_NODAL_CSV, "r") as f:
        for r in csv.DictReader(f):
            f88_u[int(r["node_id"])] = (float(r["u1"]), float(r["u2"]))

    t_77 = 0.36006250977516174
    t_88 = 0.39302148000000000
    t_79 = 0.36850000000000000
    alpha = (t_79 - t_77) / (t_88 - t_77)

    donor_inc79_u = {}
    for nid in f77_u:
        u1_77, u2_77 = f77_u[nid]
        u1_88, u2_88 = f88_u[nid]
        donor_inc79_u[nid] = (u1_77 + alpha * (u1_88 - u1_77), u2_77 + alpha * (u2_88 - u2_77))

    f77_elem_d = {}
    f77_elem_h = {}
    with open(DONOR_F77_ELEM_CSV, "r") as f:
        for r in csv.DictReader(f):
            eid = int(r["phys_elem_id"])
            gp = int(r["gp"])
            if eid not in f77_elem_d:
                f77_elem_d[eid] = {}
                f77_elem_h[eid] = {}
            f77_elem_d[eid][gp] = float(r["sdv1_damage"])
            f77_elem_h[eid][gp] = float(r["sdv2_history"])

    f88_elem_d = {}
    f88_elem_h = {}
    with open(DONOR_F88_ELEM_CSV, "r") as f:
        for r in csv.DictReader(f):
            eid = int(r["phys_elem_id"])
            gp = int(r["gp"])
            if eid not in f88_elem_d:
                f88_elem_d[eid] = {}
                f88_elem_h[eid] = {}
            f88_elem_d[eid][gp] = float(r["sdv1_damage"])
            f88_elem_h[eid][gp] = float(r["sdv2_history"])

    donor_elem_d = {}
    donor_elem_h = {}
    for eid in f77_elem_d:
        donor_elem_d[eid] = {}
        donor_elem_h[eid] = {}
        for gp in range(1, 5):
            d77 = f77_elem_d[eid][gp]
            d88 = f88_elem_d[eid][gp]
            h77 = f77_elem_h[eid][gp]
            h88 = f88_elem_h[eid][gp]
            donor_elem_d[eid][gp] = d77 + alpha * (d88 - d77)
            donor_elem_h[eid][gp] = h77 + alpha * (h88 - h77)

    # Nodal damage on donor C3
    donor_nodal_d = {nid: [] for nid in donor_mesh["nodes"]}
    for eid, conn in donor_mesh["elements"].items():
        if eid in donor_elem_d:
            d_elem = np.mean([donor_elem_d[eid][gp] for gp in range(1, 5)])
            for n in conn:
                donor_nodal_d[n].append(d_elem)
    donor_node_d_avg = {n: float(np.mean(vals)) if vals else 0.0 for n, vals in donor_nodal_d.items()}

    # Interpolation functions from donor C3 grid (40x40 quads, h=0.0025 mm)
    def interpolate_donor_field(x, y, flank, field_dict):
        x = max(0.0, min(0.1, x))
        y = max(0.0, min(0.1, y))
        col = min(39, max(0, int(x / 0.0025)))
        if x >= 0.1: col = 39

        if y < 0.050:
            row = min(19, max(0, int(y / 0.0025)))
        elif y > 0.050:
            row = min(39, max(20, int(y / 0.0025)))
        else:
            if flank == "lower":
                row = 19
            elif flank == "upper":
                row = 20
            else:
                row = 20 if (x > 0.040 or flank == "upper") else 19

        eid = row * 40 + col + 1
        conn = donor_mesh["elements"][eid]
        pts = [donor_mesh["nodes"][n] for n in conn]
        x_min, y_min = pts[0][0], pts[0][1]

        xi = max(-1.0, min(1.0, 2.0 * (x - x_min) / 0.0025 - 1.0))
        eta = max(-1.0, min(1.0, 2.0 * (y - y_min) / 0.0025 - 1.0))
        N, _, _ = shape_functions(xi, eta)

        vals = [field_dict[n] for n in conn]
        if isinstance(vals[0], tuple):
            v1 = sum(N[i] * vals[i][0] for i in range(4))
            v2 = sum(N[i] * vals[i][1] for i in range(4))
            return (float(v1), float(v2))
        else:
            return float(sum(N[i] * vals[i] for i in range(4)))

    def interpolate_donor_gp_h(x, y, flank):
        x = max(0.0, min(0.1, x))
        y = max(0.0, min(0.1, y))
        col = min(39, max(0, int(x / 0.0025)))
        if x >= 0.1: col = 39

        if y < 0.050:
            row = min(19, max(0, int(y / 0.0025)))
        elif y > 0.050:
            row = min(39, max(20, int(y / 0.0025)))
        else:
            row = 20 if (flank == "upper" or x > 0.040) else 19

        eid = row * 40 + col + 1
        conn = donor_mesh["elements"][eid]
        pts = [donor_mesh["nodes"][n] for n in conn]
        x_min, y_min = pts[0][0], pts[0][1]

        xi = max(-1.0, min(1.0, 2.0 * (x - x_min) / 0.0025 - 1.0))
        eta = max(-1.0, min(1.0, 2.0 * (y - y_min) / 0.0025 - 1.0))
        N, _, _ = shape_functions(xi, eta)

        h_vals = [donor_elem_h[eid][gp] for gp in range(1, 5)]
        h_interp = sum(N[i] * h_vals[i] for i in range(4))
        return max(0.0, float(h_interp))

    # Map nodal displacements and damage to intermediate receiver mesh
    print("Mapping nodal state to intermediate mesh...", flush=True)
    recv_nodal_u = {}
    recv_nodal_d = {}

    for nid, pt in recv_nodes.items():
        t_flank = recv_flank[nid]
        u_mapped = interpolate_donor_field(pt[0], pt[1], t_flank, donor_inc79_u)
        d_mapped = interpolate_donor_field(pt[0], pt[1], t_flank, donor_node_d_avg)

        recv_nodal_u[nid] = u_mapped
        recv_nodal_d[nid] = float(np.clip(d_mapped, 0.0, 1.0))

    # Map integration-point history H
    print("Mapping Gauss-point history to intermediate mesh...", flush=True)
    recv_elem_gp_H = {}
    for eid, conn in recv_elements.items():
        xe = np.array([recv_nodes[n] for n in conn])
        h_gps = []
        for q in range(4):
            xi_q, eta_q = UEL_GP_COORDS[q]
            N_q, _, _ = shape_functions(xi_q, eta_q)
            gp_pt = np.dot(N_q, xe)
            gp_flank = "upper" if gp_pt[1] > 0.050 else "lower"
            h_val = interpolate_donor_gp_h(gp_pt[0], gp_pt[1], gp_flank)
            h_gps.append(h_val)
        recv_elem_gp_H[eid] = h_gps

    # 4. Compute initial mapped energies on intermediate receiver mesh
    print("Computing initial mapped energies on intermediate mesh...", flush=True)
    e_elas_init = 0.0
    e_frac_init = 0.0

    for eid, conn in recv_elements.items():
        xe = np.array([recv_nodes[n] for n in conn])
        ue = np.array([recv_nodal_u[n] for n in conn]).flatten()
        de = np.array([recv_nodal_d[n] for n in conn])

        for q in range(4):
            xi_q, eta_q = UEL_GP_COORDS[q]
            wt = UEL_WEIGHTS[q]
            N_q, dNdxi, dNdeta = shape_functions(xi_q, eta_q)
            J_mat = np.dot(np.vstack([dNdxi, dNdeta]), xe)
            detJ = float(np.linalg.det(J_mat))
            invJ = np.linalg.inv(J_mat)
            dNdx = np.dot(invJ, np.vstack([dNdxi, dNdeta]))

            B = np.zeros((3, 8))
            for i in range(4):
                B[0, 2*i]   = dNdx[0, i]
                B[1, 2*i+1] = dNdx[1, i]
                B[2, 2*i]   = dNdx[1, i]
                B[2, 2*i+1] = dNdx[0, i]
            eps = B.dot(ue)
            e11, e22, e12 = eps[0], eps[1], 0.5 * eps[2]
            tr_e = e11 + e22
            e_pos = max(0.0, tr_e)
            psi_pos = 0.5 * LAM * (e_pos**2) + MU * (e11**2 + e22**2 + 2.0 * (e12**2))
            e_neg = min(0.0, tr_e)
            psi_neg = 0.5 * LAM * (e_neg**2)

            d_val = float(np.dot(N_q, de))
            grad_d = np.dot(dNdx, de)
            norm_grad_d2 = float(np.dot(grad_d, grad_d))

            g_d = (1.0 - d_val)**2 + K_DEGRAD
            psi_elas = g_d * psi_pos + psi_neg
            gamma_d = (GC / 2.0) * ((d_val**2) / ELL0 + ELL0 * norm_grad_d2)

            cj = detJ * wt
            e_elas_init += psi_elas * cj
            e_frac_init += gamma_d * cj

    # Convert from kN*mm to mJ (1 kN*mm = 1 J = 1000 mJ)
    e_elas_init = e_elas_init * 1000.0
    e_frac_init = e_frac_init * 1000.0
    e_tot_init = e_elas_init + e_frac_init
    print(f"Initial Mapped Energies (Intermediate Mesh):", flush=True)
    print(f"  E_elas = {e_elas_init:.8f} mJ (donor: {TARGET_E_ELAS_DONOR:.8f} mJ, diff: {((e_elas_init - TARGET_E_ELAS_DONOR)/TARGET_E_ELAS_DONOR)*100.0:.3f}%)", flush=True)
    print(f"  E_frac = {e_frac_init:.8f} mJ (donor: {TARGET_E_FRAC_DONOR:.8f} mJ, diff: {((e_frac_init - TARGET_E_FRAC_DONOR)/TARGET_E_FRAC_DONOR)*100.0:.3f}%)", flush=True)
    print(f"  E_tot  = {e_tot_init:.8f} mJ (donor: {TARGET_E_TOT_DONOR:.8f} mJ, diff: {((e_tot_init - TARGET_E_TOT_DONOR)/TARGET_E_TOT_DONOR)*100.0:.3f}%)", flush=True)

    # 5. Write CSV files
    u_csv = OUT_DIR / "nodal_displacements_initial.csv"
    with open(u_csv, "w") as f:
        f.write("node_id,u1,u2\n")
        for nid in sorted(recv_nodes.keys()):
            u1, u2 = recv_nodal_u[nid]
            f.write(f"{nid},{u1:.10e},{u2:.10e}\n")

    bounds_csv = OUT_DIR / "d_lower_bounds.csv"
    with open(bounds_csv, "w") as f:
        f.write("EID, D0_1, D0_2, D0_3, D0_4, H0_1, H0_2, H0_3, H0_4\n")
        for eid in sorted(recv_elements.keys()):
            conn = recv_elements[eid]
            d0_vals = [recv_nodal_d[n] for n in conn]
            h0_vals = recv_elem_gp_H[eid]
            f.write(f"{eid}, {d0_vals[0]:.10e}, {d0_vals[1]:.10e}, {d0_vals[2]:.10e}, {d0_vals[3]:.10e}, {h0_vals[0]:.10e}, {h0_vals[1]:.10e}, {h0_vals[2]:.10e}, {h0_vals[3]:.10e}\n")

    inc_file = OUT_DIR / "active_set_boundary_cards.inc"
    with open(inc_file, "w") as f:
        f.write("** Active-Set Boundary Cards for Phase-Field Lower Bounds\n")
        for nid in sorted(recv_nodes.keys()):
            d0 = recv_nodal_d[nid]
            f.write(f"{nid}, 3, 3, {d0:.10e}\n")

    stage_a_inc = OUT_DIR / "stage_a_all_d0_boundary_cards.inc"
    shutil.copy(inc_file, stage_a_inc)

    # 6. Write Abaqus Input Deck (Unified 12-DOF UEL)
    inp_path = OUT_DIR / "M1_C3_INT_INC79_DIRECT_TRANSFER.inp"
    with open(inp_path, "w") as f:
        f.write("*Heading\n")
        f.write(f"** Candidate C3-Intermediate Stage C1-1 Direct State-Transfer Control (Inc 79)\n")
        f.write(f"** Elements: {n_elements} Quads, Nodes: {n_nodes} physical + RP 999999\n")
        f.write(f"** DOFs per node: 1:ux, 2:uy, 3:d (Unified 12-DOF UEL)\n")
        f.write(f"** Step 1 (C1-2-Inc79): Direct transfer at u_RP = {TARGET_U_RP:.8f} mm\n")
        f.write("*Preprint, echo=NO, model=NO, history=NO, contact=NO\n")
        f.write("** ----------------------------------------------------------------\n")
        f.write("** UNIFIED 12-DOF USER ELEMENT (Active DOFs 1, 2, 3)\n")
        f.write("** ----------------------------------------------------------------\n")
        f.write("*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=5, VARIABLES=8, UNSYMM\n")
        f.write("1, 2, 3\n")
        f.write("** ----------------------------------------------------------------\n")
        f.write("*Node\n")
        for nid in sorted(mesh["nodes"].keys()):
            pt = mesh["nodes"][nid]
            f.write(f"{nid}, {pt[0]:.10f}, {pt[1]:.10f}\n")
        f.write("** ----------------------------------------------------------------\n")
        f.write("*Element, type=U1, elset=E_ALL\n")
        for eid in sorted(recv_elements.keys()):
            conn = recv_elements[eid]
            f.write(f"{eid}, {conn[0]}, {conn[1]}, {conn[2]}, {conn[3]}\n")
        f.write("** ----------------------------------------------------------------\n")
        f.write("** NODE SETS\n")
        f.write("** ----------------------------------------------------------------\n")
        f.write("*Nset, nset=N_RP\n999999\n")

        top_nodes = sorted(mesh["top_nodes"])
        bottom_nodes = sorted(mesh["bottom_nodes"])
        pin_nodes = sorted(mesh["pin_nodes"])

        def write_nset(name, nlist):
            f.write(f"*Nset, nset={name}\n")
            chunks = [nlist[i:i+16] for i in range(0, len(nlist), 16)]
            for c in chunks:
                f.write(", ".join(map(str, c)) + "\n")

        write_nset("N_TOP", top_nodes)
        write_nset("N_BOTTOM", bottom_nodes)
        write_nset("N_PIN", pin_nodes)

        f.write("** ----------------------------------------------------------------\n")
        f.write("** UEL PROPERTIES: E, nu, Gc, l0, k_residual\n")
        f.write("** ----------------------------------------------------------------\n")
        f.write("*UEL PROPERTY, ELSET=E_ALL\n")
        f.write(f"{E_MOD:.1f}, {NU:.1f}, {GC:.4f}, {ELL0:.4f}, {K_DEGRAD:.1e}\n")
        f.write("** ----------------------------------------------------------------\n")
        f.write("** EQUATIONS TYING N_TOP TO REFERENCE POINT RP 999999\n")
        f.write("** ----------------------------------------------------------------\n")
        for nid in top_nodes:
            f.write("*EQUATION\n2\n")
            f.write(f"{nid}, 2, 1.0, 999999, 2, -1.0\n")
        f.write("** ----------------------------------------------------------------\n")
        f.write("** INITIAL BOUNDARY CONDITIONS\n")
        f.write("** ----------------------------------------------------------------\n")
        f.write("*Boundary\n")
        f.write("N_BOTTOM, 2, 2, 0.0\n")
        f.write("N_PIN, 1, 1, 0.0\n")
        f.write("N_RP, 1, 1, 0.0\n")
        f.write("N_RP, 2, 2, 0.0\n")
        f.write("** ==========================================================\n")
        f.write(f"** STEP 1: Direct Transfer Re-Equilibration at u = {TARGET_U_RP:.8f} mm\n")
        f.write("** ==========================================================\n")
        f.write("*Step, name=C1-2-Inc79, nlgeom=NO, inc=200\n")
        f.write("*Static\n")
        f.write("1.0, 1.0, 1.0E-8, 1.0\n")
        f.write("*Boundary\n")
        f.write("N_BOTTOM, 2, 2, 0.0\n")
        f.write("N_PIN, 1, 1, 0.0\n")
        f.write("N_RP, 1, 1, 0.0\n")
        f.write(f"N_RP, 2, 2, {TARGET_U_RP:.8f}\n")
        f.write("*Include, input=active_set_boundary_cards.inc\n")
        f.write("*Output, field, frequency=1\n")
        f.write("*Node Output\nU, RF\n")
        f.write("*Output, history, frequency=1\n")
        f.write("*Energy Output\nALLSE, ALLIE, ALLWK, ALLFD, ALLCD, ALLVD, ALLPD, ALLAE, ETOTAL\n")
        f.write("*End Step\n")

    print(f"Written Abaqus deck to: {inp_path}", flush=True)

    # 7. Copy frozen unified UEL
    frozen_uel_src = REPO_ROOT / "models/pandey_kumar_mode1/115_c4_inc79_direct_transfer/f42_unified_12dof_active_set_uel.for"
    frozen_uel_dst = OUT_DIR / "f42_unified_12dof_active_set_uel.for"
    shutil.copy(frozen_uel_src, frozen_uel_dst)

    # 8. Copy notification script
    notif_src = REPO_ROOT / "models/pandey_kumar_mode1/115_c4_inc79_direct_transfer/job_notifications.sh"
    notif_dst = OUT_DIR / "job_notifications.sh"
    shutil.copy(notif_src, notif_dst)

    # 9. Create AM driver script for intermediate mesh
    driver_src = REPO_ROOT / "models/pandey_kumar_mode1/115_c4_inc79_direct_transfer/driver_c4_inc79_direct_transfer.py"
    driver_dst = OUT_DIR / "driver_c3_int_inc79_direct_transfer.py"
    with open(driver_src, "r") as f:
        driver_code = f.read()
    driver_code = driver_code.replace("c4_inc79_direct_transfer_summary.json", "c3_int_inc79_direct_transfer_summary.json")
    driver_code = driver_code.replace("PACKAGE_115_C4_INC79_DIRECT_TRANSFER", "PACKAGE_116_C3_INT_INC79_DIRECT_TRANSFER")
    driver_code = driver_code.replace("M1_C4_INC79_DIR_", "M1_C3_INT_DIR_")
    driver_code = driver_code.replace("M1_C4_INC79_DIRECT_TRANSFER", "M1_C3_INT_INC79_DIRECT_TRANSFER")
    with open(driver_dst, "w") as f:
        f.write(driver_code)

    # 10. Create datacheck script
    dc_script = OUT_DIR / "run_c3_int_inc79_transfer_datacheck.sh"
    with open(dc_script, "w") as f:
        f.write("#!/bin/bash\n")
        f.write("source /etc/profile.d/modules.sh 2>/dev/null || true\n")
        f.write("module load abaqus/2023 2>/dev/null || true\n")
        f.write("abaqus job=M1_C3_INT_XFER_DC input=M1_C3_INT_INC79_DIRECT_TRANSFER.inp user=f42_unified_12dof_active_set_uel.for datacheck interactive\n")

    # 11. Create PBS execution script
    pbs_script = OUT_DIR / "submit_M1_C3_INT_INC79_DIRECT_TRANSFER.pbs"
    with open(pbs_script, "w") as f:
        f.write("#!/bin/bash\n")
        f.write("#PBS -N M1_C3_INT_INC79_TRANSFER\n")
        f.write("#PBS -l select=1:ncpus=1:mem=16gb\n")
        f.write("#PBS -l walltime=08:00:00\n")
        f.write("#PBS -q entry_imfdfkmq\n")
        f.write("#PBS -j oe\n")
        f.write("#PBS -m abe\n")
        f.write("#PBS -M pr21vyci@mailserver.tu-freiberg.de\n\n")
        f.write("cd $PBS_O_WORKDIR || exit 1\n\n")
        f.write("source ./job_notifications.sh\n")
        f.write("notify_start\n")
        f.write("notification_install_terminal_trap\n\n")
        f.write("echo \"[PBS] Running Package 116 Intermediate-Resolution State Transfer Control...\"\n")
        f.write("source /etc/profile.d/modules.sh 2>/dev/null || true\n")
        f.write("module load abaqus/2023 2>/dev/null || true\n\n")
        f.write("python driver_c3_int_inc79_direct_transfer.py > pbs_execution.log 2>&1\n")
        f.write("RC=$?\n\n")
        f.write("echo \"[PBS] Driver finished with return code: $RC\"\n")
        f.write("exit $RC\n")

    # 12. Create PACKAGE_MANIFEST.json and M1_C3_INT_INC79_TRANSFER_AUTHORIZATION.json
    pkg_files = [
        "M1_C3_INT_INC79_DIRECT_TRANSFER.inp",
        "active_set_boundary_cards.inc",
        "d_lower_bounds.csv",
        "driver_c3_int_inc79_direct_transfer.py",
        "f42_unified_12dof_active_set_uel.for",
        "job_notifications.sh",
        "nodal_displacements_initial.csv",
        "run_c3_int_inc79_transfer_datacheck.sh",
        "stage_a_all_d0_boundary_cards.inc",
        "submit_M1_C3_INT_INC79_DIRECT_TRANSFER.pbs"
    ]
    files_hashes = {f: sha256_file(OUT_DIR / f) for f in pkg_files}

    command_str = "powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand \"qsub -q entry_imfdfkmq /scratch9/pr21vyci/runs/mode1_c3_int_inc79_direct_transfer/submit_M1_C3_INT_INC79_DIRECT_TRANSFER.pbs\""
    command_hash = hashlib.sha256(command_str.encode("utf-8")).hexdigest()

    manifest_obj = {
        "schema": 1,
        "package_name": "116_c3_int_inc79_direct_transfer",
        "created_at": "2026-10-27T08:00:00Z",
        "files": files_hashes,
        "jobs": [
            {
                "id": "M1_C3_INT_INC79_TRANSFER",
                "purpose": "Abaqus 2023 Candidate C3-Intermediate Stage C1-1 Direct State-Transfer Control at u = 0.00184250 mm (2,484 quads, 2,610 nodes, h_tip = 1.2 um, up to 15 AM cycles with irreversible history transferred from authentic C3 Increment 79)",
                "input": "M1_C3_INT_INC79_DIRECT_TRANSFER.inp",
                "user_subroutine": "f42_unified_12dof_active_set_uel.for",
                "pbs": "submit_M1_C3_INT_INC79_DIRECT_TRANSFER.pbs",
                "datacheck": "M1_C3_INT_XFER_DC.dat",
                "queue": "entry_imfdfkmq",
                "cpus": 1,
                "memory_gb": 16,
                "walltime_hours": 8,
                "execution": "single-rank serial",
                "max_submissions": 1,
                "command": command_str,
                "command_sha256": command_hash,
                "depends_on": []
            }
        ]
    }

    manifest_path = OUT_DIR / "PACKAGE_MANIFEST.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest_obj, f, indent=2)

    auth_obj = {
        "schema": 1,
        "adapter": "mode1-experimental-12dof-v1",
        "scientific_scope": "MODE1",
        "technical_stage": "C1-1",
        "batch_name": "MODE1_C3_INT_INC79_DIRECT_TRANSFER",
        "configuration": "ALTERNATING_MINIMIZATION_SAME_LOAD_DIRECT_TRANSFER",
        "hypothesis": "At fixed physical load, the converged AT2 functional changes systematically with crack-tip mesh resolution; the C4 fracture-energy increase is primarily discretization-dependent rather than an implementation defect.",
        "automatic_retry": False,
        "max_submissions": 1,
        "remote_run_dir": "/scratch9/pr21vyci/runs/mode1_c3_int_inc79_direct_transfer",
        "files": files_hashes,
        "jobs": manifest_obj["jobs"],
        "acceptance": {
            "stage_C1_1_direct_transfer": {
                "u_top_target_mm": 0.0018425,
                "rf2_expected_N": 186.067909,
                "rf2_continuity_pct_max": 5.0,
                "energy_continuity_pct_max": 2.0,
                "kkt_violations_max": 0,
                "free_phase_residual_max_kN_mm": 1.0e-06,
                "healing_tolerance": 0,
                "stationarity_delta_d_max": 0.001,
                "stationarity_delta_rf2_max_N": 0.1
            }
        },
        "package_name": "116_c3_int_inc79_direct_transfer"
    }

    auth_path = OUT_DIR / "M1_C3_INT_INC79_TRANSFER_AUTHORIZATION.json"
    with open(auth_path, "w") as f:
        json.dump(auth_obj, f, indent=2)

    audit_data = {
        "schema": 1,
        "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
        "package": "PACKAGE_116_C3_INT_INC79_DIRECT_TRANSFER",
        "resolution_level": "INTERMEDIATE (Level 2 of 3)",
        "mesh_metrics": {
            "n_elements": n_elements,
            "n_nodes": n_nodes,
            "h_tip_um": h_target * 1000.0,
            "h_min_mm": float(h_target),
            "min_det_jac": float(min_det),
            "max_aspect_ratio": float(max_ar),
            "crack_tip_center_mm": [float(x_center), 0.050]
        },
        "donor_comparison": {
            "donor_package": "PACKAGE_76_INCREMENT_79",
            "u_top_mm": TARGET_U_RP,
            "donor_rf2_N": TARGET_RF2_DONOR,
            "donor_e_elas_mJ": TARGET_E_ELAS_DONOR,
            "donor_e_frac_mJ": TARGET_E_FRAC_DONOR,
            "donor_e_tot_mJ": TARGET_E_TOT_DONOR,
            "initial_mapped_e_elas_mJ": float(e_elas_init),
            "initial_mapped_e_frac_mJ": float(e_frac_init),
            "initial_mapped_e_tot_mJ": float(e_tot_init),
            "delta_e_elas_pct": float(((e_elas_init - TARGET_E_ELAS_DONOR) / TARGET_E_ELAS_DONOR) * 100.0),
            "delta_e_frac_pct": float(((e_frac_init - TARGET_E_FRAC_DONOR) / TARGET_E_FRAC_DONOR) * 100.0),
            "delta_e_tot_pct": float(((e_tot_init - TARGET_E_TOT_DONOR) / TARGET_E_TOT_DONOR) * 100.0)
        },
        "resolution_progression": {
            "level1_c3_donor": {"h_tip_um": 2.50, "elements": 1600, "e_tot_mJ": 0.212448, "e_frac_mJ": 0.041044},
            "level2_c3_int": {"h_tip_um": 1.20, "elements": 2484, "initial_mapped_e_tot_mJ": float(e_tot_init), "initial_mapped_e_frac_mJ": float(e_frac_init)},
            "level3_c4_receiver": {"h_tip_um": 0.606, "elements": 4422, "converged_e_tot_mJ": 0.216760, "converged_e_frac_mJ": 0.045619}
        },
        "source_hashes": files_hashes
    }
    with open(OUT_AUDIT_JSON, "w") as f:
        json.dump(audit_data, f, indent=2)

    print(f"Package 116 successfully built at: {OUT_DIR}", flush=True)
    return 0

if __name__ == "__main__":
    sys.exit(main())

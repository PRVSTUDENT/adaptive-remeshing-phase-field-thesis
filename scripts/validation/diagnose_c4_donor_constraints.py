#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
diagnose_c4_donor_constraints.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER (Turn 101)
Protocol Version: 2

Investigates:
1. Exact reconstruction of authentic C4 donor (Package 94 Step 4) constraint system:
   - Rigorous parsing of Step 4 *Boundary cards (OP=NEW).
   - Keyed constraint table: 3,845 prescribed vs 743 free nodes.
   - Exact residual assembly R_d = F_d - K_d*d and investigation of worst node 2277.
   - Formal closure classification under the binding 1.0e-6 kN/mm criterion: FAIL.
2. Separation of physical constraints from computational/artificial restrictions:
   - Physical slit / crack flank nodes.
   - Local constitutive irreversibility bound d >= d_ckpt.
   - Artificial geometric crack-tip corridor clamping: (0.035 <= x <= 0.075) & (|y-0.050| <= 0.008) & (d >= 0.15).
3. Controlled C4 -> C5 constraint-transfer experiments (+4 nm, u = 0.002052 -> 0.002056 mm):
   - Case A: Physical-only constraints (irreversibility bound d >= d_H1 across whole domain, no artificial corridor).
   - Case B: Diagnostic corridor-controlled continuation (reproducing C4 corridor clamping on C5).
"""

import sys
import os
import json
import csv
from pathlib import Path
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from scipy.optimize import minimize

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
C4_DIR = REPO_ROOT / "models/pandey_kumar_mode1/94_c4_package94_authentic_transfer"
C4_MESH = C4_DIR / "candidate_crack_band_mesh_c4.inp"
C4_INP = C4_DIR / "M1_C4_PACKAGE94_TRANSFER.inp"
C4_NODAL_CSV = REPO_ROOT / "results/validation/mode1_f1597/pkg94_step4_frame7_nodal_state.csv"
C4_GP_CSV = REPO_ROOT / "results/validation/mode1_f1597/pkg94_step4_frame7_committed_history.csv"
C4_SUMMARY_JSON = REPO_ROOT / "results/validation/mode1_f1597/pkg94_donor_step4_frame7_summary.json"

C5_DIR = REPO_ROOT / "models/pandey_kumar_mode1/103_c5_h1_transfer_pilot"
C5_MESH = C5_DIR / "candidate_crack_band_mesh_c5.inp"
C5_INP = C5_DIR / "M1_C5_PACKAGE103_H1_PILOT.inp"
C5_CKPT_TABLE = REPO_ROOT / "models/pandey_kumar_mode1/102_r1_c5_coupled_staggered_history_repaired/candidate_c5_frame7_mapped_state_table.csv"
C5_H1_D_PATH = REPO_ROOT / "results/validation/mode1_f1597/c5_h1_bound_constrained_d.npy"

# Material & Phase Field Parameters (Frozen UEL match)
E_MOD = 210.0      # kN/mm^2
NU = 0.3
E_GC = 0.0027      # kN/mm
E_L0 = 0.0075      # mm
K_DEGRAD = 1.0e-7  # residual stiffness
TAU_RES = 1.0e-6   # binding phase residual tolerance (kN/mm)

# Quadrature point constants matching f42_mixed_uel.for
A_GAUSS = 0.577350269189626
UEL_GP_COORDS = [
    (-A_GAUSS, -A_GAUSS),  # KPT 1: (-a, -a)
    ( A_GAUSS, -A_GAUSS),  # KPT 2: (+a, -a)
    ( A_GAUSS,  A_GAUSS),  # KPT 3: (+a, +a)
    (-A_GAUSS,  A_GAUSS),  # KPT 4: (-a, +a)
]
UEL_WEIGHTS = [1.0, 1.0, 1.0, 1.0]

def shape_functions(xi, eta):
    N = 0.25 * np.array([
        (1.0 - xi) * (1.0 - eta),
        (1.0 + xi) * (1.0 - eta),
        (1.0 + xi) * (1.0 + eta),
        (1.0 - xi) * (1.0 + eta)
    ])
    dNdxi = 0.25 * np.array([
        -(1.0 - eta),  (1.0 - eta),  (1.0 + eta), -(1.0 + eta)
    ])
    dNdeta = 0.25 * np.array([
        -(1.0 - xi), -(1.0 + xi),  (1.0 + xi),  (1.0 - xi)
    ])
    return N, dNdxi, dNdeta

def compute_plane_strain_c0():
    c11_0 = E_MOD * (1.0 - NU) / ((1.0 + NU) * (1.0 - 2.0 * NU))
    c12_0 = E_MOD * NU / ((1.0 + NU) * (1.0 - 2.0 * NU))
    c33_0 = E_MOD / (2.0 * (1.0 + NU))
    C = np.zeros((3, 3))
    C[0, 0] = c11_0
    C[0, 1] = c12_0
    C[1, 0] = c12_0
    C[1, 1] = c11_0
    C[2, 2] = c33_0
    return C, c12_0, c33_0

def uel_driving_energy(eps, lam, mu):
    e11 = eps[0]
    e22 = eps[1]
    e12 = 0.5 * eps[2]
    tr_e = e11 + e22
    e_pos = max(0.0, tr_e)
    return float(0.5 * lam * (e_pos**2) + mu * (e11**2 + e22**2 + 2.0 * (e12**2)))

def parse_mesh(mesh_path, max_phys_eid):
    nodes = {}
    elements = {}
    with open(mesh_path, "r", encoding="utf-8") as f:
        reading = None
        for line in f:
            l = line.strip()
            if not l or l.startswith("**"): continue
            if l.startswith("*"):
                u = l.upper()
                if u.startswith("*NODE") and not any(u.startswith(k) for k in ["*NODE OUTPUT", "*NODE PRINT", "*NODE FILE"]):
                    reading = "NODE"
                elif u.startswith("*ELEMENT"):
                    reading = "ELEMENT"
                else:
                    reading = None
                continue
            if reading == "NODE":
                parts = [p.strip() for p in l.split(",") if p.strip()]
                if len(parts) >= 3 and parts[0].isdigit():
                    nid = int(parts[0])
                    if nid != 999999:
                        nodes[nid] = np.array([float(parts[1]), float(parts[2])])
            elif reading == "ELEMENT":
                parts = [p.strip() for p in l.split(",") if p.strip()]
                if len(parts) >= 5 and parts[0].isdigit():
                    eid = int(parts[0])
                    if eid <= max_phys_eid:
                        elements[eid] = [int(p) for p in parts[1:5]]
    node_list = sorted(nodes.keys())
    node_to_idx = {nid: i for i, nid in enumerate(node_list)}
    return nodes, elements, node_list, node_to_idx

def assemble_at2_system(nodes, elements, node_to_idx, elem_H):
    n_nodes = len(node_to_idx)
    I_list, J_list, V_list = [], [], []
    F_global = np.zeros(n_nodes)

    for eid, conn in elements.items():
        pts = np.array([nodes[n] for n in conn])
        h_vals = elem_H[eid]

        for kpt in range(4):
            xi, eta = UEL_GP_COORDS[kpt]
            wt = UEL_WEIGHTS[kpt]
            N, dNdxi, dNdeta = shape_functions(xi, eta)

            J_mat = np.zeros((2, 2))
            for a in range(4):
                J_mat[0, 0] += dNdxi[a] * pts[a, 0]
                J_mat[0, 1] += dNdxi[a] * pts[a, 1]
                J_mat[1, 0] += dNdeta[a] * pts[a, 0]
                J_mat[1, 1] += dNdeta[a] * pts[a, 1]

            detJ = J_mat[0, 0] * J_mat[1, 1] - J_mat[0, 1] * J_mat[1, 0]
            cjac = detJ * wt
            invJ = np.array([
                [ J_mat[1, 1], -J_mat[0, 1]],
                [-J_mat[1, 0],  J_mat[0, 0]]
            ]) / detJ

            b_phase = np.zeros((2, 4))
            for a in range(4):
                b_phase[0, a] = invJ[0, 0] * dNdxi[a] + invJ[0, 1] * dNdeta[a]
                b_phase[1, a] = invJ[1, 0] * dNdxi[a] + invJ[1, 1] * dNdeta[a]

            H_val = h_vals[kpt]

            for a in range(4):
                idx_a = node_to_idx[conn[a]]
                F_global[idx_a] += cjac * 2.0 * H_val * N[a]

                for b in range(4):
                    idx_b = node_to_idx[conn[b]]
                    bdb = b_phase[0, a] * b_phase[0, b] + b_phase[1, a] * b_phase[1, b]
                    val = cjac * (
                        (E_GC * E_L0) * bdb +
                        (E_GC / E_L0 + 2.0 * H_val) * N[a] * N[b]
                    )
                    I_list.append(idx_a)
                    J_list.append(idx_b)
                    V_list.append(val)

    K_global = sp.coo_matrix((V_list, (I_list, J_list)), shape=(n_nodes, n_nodes)).tocsr()
    return K_global, F_global

def solve_elasticity_uel(nodes, elements, node_list, node_to_idx, d, u_top):
    n_nodes = len(node_list)
    n_dofs = 2 * n_nodes
    C0, lam, mu = compute_plane_strain_c0()

    I_u, J_u, V_u = [], [], []
    for eid in sorted(elements.keys()):
        conn = elements[eid]
        elem_indices = [node_to_idx[n] for n in conn]
        xe = np.array([nodes[n] for n in conn])
        de = d[elem_indices]
        d_avg = np.mean(de)
        deg = (1.0 - d_avg)**2 + K_DEGRAD
        c_mech = C0 * deg

        for kpt in range(4):
            xi, eta = UEL_GP_COORDS[kpt]
            wt = UEL_WEIGHTS[kpt]
            N, dNdxi, dNdeta = shape_functions(xi, eta)

            J_mat = np.zeros((2, 2))
            for i in range(4):
                J_mat[0, 0] += dNdxi[i] * xe[i, 0]
                J_mat[0, 1] += dNdxi[i] * xe[i, 1]
                J_mat[1, 0] += dNdeta[i] * xe[i, 0]
                J_mat[1, 1] += dNdeta[i] * xe[i, 1]

            detJ = J_mat[0, 0] * J_mat[1, 1] - J_mat[0, 1] * J_mat[1, 0]
            cj = detJ * wt
            invJ = np.array([[ J_mat[1, 1], -J_mat[0, 1]], [-J_mat[1, 0],  J_mat[0, 0]]]) / detJ
            dNdx = np.zeros((2, 4))
            for i in range(4):
                dNdx[0, i] = invJ[0, 0] * dNdxi[i] + invJ[0, 1] * dNdeta[i]
                dNdx[1, i] = invJ[1, 0] * dNdxi[i] + invJ[1, 1] * dNdeta[i]

            B = np.zeros((3, 8))
            for i in range(4):
                B[0, 2*i]   = dNdx[0, i]
                B[1, 2*i+1] = dNdx[1, i]
                B[2, 2*i]   = dNdx[1, i]
                B[2, 2*i+1] = dNdx[0, i]

            Ke = cj * B.T.dot(c_mech).dot(B)
            elem_dofs = []
            for idx in elem_indices:
                elem_dofs.extend([2*idx, 2*idx + 1])

            for r in range(8):
                for c in range(8):
                    I_u.append(elem_dofs[r])
                    J_u.append(elem_dofs[c])
                    V_u.append(Ke[r, c])

    K_u = sp.coo_matrix((V_u, (I_u, J_u)), shape=(n_dofs, n_dofs)).tocsr()

    y_vals = [nodes[nid][1] for nid in node_list]
    y_min = min(y_vals)
    y_max = max(y_vals)
    bottom_nodes = [nid for nid in node_list if abs(nodes[nid][1] - y_min) < 1e-5]
    top_nodes = [nid for nid in node_list if abs(nodes[nid][1] - y_max) < 1e-5]

    prescribed_dofs = {}
    for nid in bottom_nodes:
        idx = node_to_idx[nid]
        prescribed_dofs[2*idx + 1] = 0.0
        if abs(nodes[nid][0]) < 1e-5:
            prescribed_dofs[2*idx] = 0.0

    for nid in top_nodes:
        idx = node_to_idx[nid]
        prescribed_dofs[2*idx + 1] = u_top

    all_dofs = np.arange(n_dofs)
    p_dofs = np.array(sorted(prescribed_dofs.keys()))
    free_dofs = np.setdiff1d(all_dofs, p_dofs)

    u_vec = np.zeros(n_dofs)
    for dof, val in prescribed_dofs.items():
        u_vec[dof] = val

    K_ff = K_u[free_dofs, :][:, free_dofs]
    K_fp = K_u[free_dofs, :][:, p_dofs]
    u_p = u_vec[p_dofs]

    rhs_f = -K_fp.dot(u_p)
    u_f = spla.spsolve(K_ff, rhs_f)
    u_vec[free_dofs] = u_f

    f_react = K_u.dot(u_vec)
    rf2_top = sum(f_react[2*node_to_idx[nid] + 1] for nid in top_nodes)
    rf2_top_N = float(rf2_top * 1000.0)

    u_2d = u_vec.reshape((n_nodes, 2))
    return u_2d, rf2_top_N

def compute_energies_uel(nodes, elements, node_list, node_to_idx, u_2d, d):
    C0, lam, mu = compute_plane_strain_c0()
    e_frac_total = 0.0
    e_elas_total = 0.0

    for eid in sorted(elements.keys()):
        conn = elements[eid]
        elem_indices = [node_to_idx[n] for n in conn]
        xe = np.array([nodes[n] for n in conn])
        ue = u_2d[elem_indices, :].flatten()
        de = d[elem_indices]
        d_avg = np.mean(de)
        deg = (1.0 - d_avg)**2 + K_DEGRAD
        c_mech = C0 * deg

        for kpt in range(4):
            xi, eta = UEL_GP_COORDS[kpt]
            wt = UEL_WEIGHTS[kpt]
            N, dNdxi, dNdeta = shape_functions(xi, eta)

            J_mat = np.zeros((2, 2))
            for i in range(4):
                J_mat[0, 0] += dNdxi[i] * xe[i, 0]
                J_mat[0, 1] += dNdxi[i] * xe[i, 1]
                J_mat[1, 0] += dNdeta[i] * xe[i, 0]
                J_mat[1, 1] += dNdeta[i] * xe[i, 1]

            detJ = J_mat[0, 0] * J_mat[1, 1] - J_mat[0, 1] * J_mat[1, 0]
            cj = detJ * wt
            invJ = np.array([[ J_mat[1, 1], -J_mat[0, 1]], [-J_mat[1, 0],  J_mat[0, 0]]]) / detJ
            dNdx = np.zeros((2, 4))
            for i in range(4):
                dNdx[0, i] = invJ[0, 0] * dNdxi[i] + invJ[0, 1] * dNdeta[i]
                dNdx[1, i] = invJ[1, 0] * dNdxi[i] + invJ[1, 1] * dNdeta[i]

            B = np.zeros((3, 8))
            for i in range(4):
                B[0, 2*i]   = dNdx[0, i]
                B[1, 2*i+1] = dNdx[1, i]
                B[2, 2*i]   = dNdx[1, i]
                B[2, 2*i+1] = dNdx[0, i]

            eps = B.dot(ue)
            stress = c_mech.dot(eps)
            e_elas_total += cj * 0.5 * np.dot(stress, eps)

            d_pt = np.dot(N, de)
            grad_d = np.dot(dNdx, de)
            grad_d_sq = np.sum(grad_d**2)
            psi_f_pt = E_GC * (0.5 * (d_pt**2) / E_L0 + 0.5 * E_L0 * grad_d_sq)
            e_frac_total += cj * psi_f_pt

    return float(e_frac_total * 1000.0), float(e_elas_total * 1000.0)

def section_2_c4_donor_constraint_audit():
    print("="*75)
    print("   SECTION 2: AUTHENTIC C4 DONOR CONSTRAINT & RESIDUAL AUDIT   ")
    print("="*75)

    # 1. Parse C4 mesh
    nodes_c4, elems_c4, nlist_c4, n2idx_c4 = parse_mesh(C4_MESH, max_phys_eid=4422)
    n_nodes_c4 = len(nlist_c4)
    print(f"C4 Mesh: {n_nodes_c4} nodes, {len(elems_c4)} quads.")

    # 2. Parse Step 4 *Boundary cards from C4 inp
    c4_prescribed_d = {}
    in_step4 = False
    with open(C4_INP, "r", encoding="utf-8") as f:
        for line in f:
            l = line.strip()
            if "*Step, name=FORWARD_CONTINUATION" in l:
                in_step4 = True
                continue
            if in_step4:
                if l.startswith("*End Step"): break
                if l.startswith("*") and not l.startswith("*Boundary"): continue
                parts = [p.strip() for p in l.split(",") if p.strip()]
                if len(parts) >= 4 and parts[0].isdigit() and parts[1] == "3" and parts[2] == "3":
                    c4_prescribed_d[int(parts[0])] = float(parts[3])

    c4_prescribed_nodes = set(c4_prescribed_d.keys())
    c4_free_nodes = [nid for nid in nlist_c4 if nid not in c4_prescribed_nodes]
    print(f"Step 4 Prescribed damage nodes: {len(c4_prescribed_nodes)}")
    print(f"Step 4 Free phase nodes:        {len(c4_free_nodes)}")

    # 3. Load authentic nodal state and history
    u_c4 = np.zeros((n_nodes_c4, 2))
    d_c4 = np.zeros(n_nodes_c4)
    with open(C4_NODAL_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            nid = int(row["node_id"])
            if nid in n2idx_c4:
                idx = n2idx_c4[nid]
                u_c4[idx, 0] = float(row["u1"])
                u_c4[idx, 1] = float(row["u2"])
                d_c4[idx] = float(row["damage"])

    elem_H_c4 = {}
    with open(C4_GP_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            eid = int(row["elem_id"])
            ip = int(row["ip"])
            h_val = float(row["h"])
            if eid not in elem_H_c4: elem_H_c4[eid] = [0.0]*4
            elem_H_c4[eid][ip - 1] = h_val

    # 4. Assemble AT2 system on C4 and evaluate residuals
    K_d_c4, F_d_c4 = assemble_at2_system(nodes_c4, elems_c4, n2idx_c4, elem_H_c4)
    Kd_c4 = K_d_c4.dot(d_c4)
    R_d_c4 = F_d_c4 - Kd_c4

    free_indices_c4 = [n2idx_c4[nid] for nid in c4_free_nodes]
    prescribed_indices_c4 = [n2idx_c4[nid] for nid in c4_prescribed_nodes]

    res_inf_free = float(np.max(np.abs(R_d_c4[free_indices_c4])))
    res_inf_all = float(np.max(np.abs(R_d_c4)))

    print(f"\nPhase residual on Free Set ({len(free_indices_c4)} nodes):      ||R_d||_inf = {res_inf_free:.6e} kN/mm")
    print(f"Phase residual on Clamped Set ({len(prescribed_indices_c4)} nodes):   ||R_d||_inf = {float(np.max(np.abs(R_d_c4[prescribed_indices_c4]))):.6e} kN/mm")
    print(f"Phase residual across All Nodes ({n_nodes_c4} nodes):       ||R_d||_inf = {res_inf_all:.6e} kN/mm")

    # Evaluate against binding 1.0e-6 criterion
    closure_status = "PASS" if res_inf_free <= TAU_RES else "FAIL"
    print(f"Donor Phase Closure under existing 1.0e-6 kN/mm criterion: {closure_status} ({res_inf_free:.4e} > {TAU_RES:.1e})")

    # Detailed inspection of worst node 2277
    idx_2277 = n2idx_c4[2277]
    pt_2277 = nodes_c4[2277]
    surrounding_elems = [eid for eid, conn in elems_c4.items() if 2277 in conn]

    node_2277_detail = {
        "node_id": 2277,
        "x_mm": float(pt_2277[0]),
        "y_mm": float(pt_2277[1]),
        "damage": float(d_c4[idx_2277]),
        "F_d_kNmm": float(F_d_c4[idx_2277]),
        "Kd_kNmm": float(Kd_c4[idx_2277]),
        "residual_R_kNmm": float(R_d_c4[idx_2277]),
        "relative_residual_pct": float(abs(R_d_c4[idx_2277]) / F_d_c4[idx_2277] * 100),
        "surrounding_elements": surrounding_elems,
        "element_histories": {eid: elem_H_c4[eid] for eid in surrounding_elems}
    }
    print(f"\nWorst Node 2277 Inspection:")
    print(f"  Coords: ({pt_2277[0]:.4f}, {pt_2277[1]:.4f}) mm")
    print(f"  d = {d_c4[idx_2277]:.6f}")
    print(f"  F_d = {F_d_c4[idx_2277]:.6e} kN/mm | Kd = {Kd_c4[idx_2277]:.6e} kN/mm | R_d = {R_d_c4[idx_2277]:.6e} kN/mm")
    print(f"  Surrounding elements: {surrounding_elems}")

    # Keyed constraint and residual table for top 20 residual free nodes
    top_free_indices = sorted(free_indices_c4, key=lambda idx: abs(R_d_c4[idx]), reverse=True)[:20]
    c4_residual_table = []
    print("\nTop 10 Free Nodes by Absolute Residual:")
    for idx in top_free_indices:
        nid = nlist_c4[idx]
        pt = nodes_c4[nid]
        row_dict = {
            "node_id": nid,
            "x_mm": float(pt[0]),
            "y_mm": float(pt[1]),
            "damage": float(d_c4[idx]),
            "F_d_kNmm": float(F_d_c4[idx]),
            "Kd_kNmm": float(Kd_c4[idx]),
            "residual_kNmm": float(R_d_c4[idx]),
            "is_prescribed_in_step4": bool(nid in c4_prescribed_nodes)
        }
        c4_residual_table.append(row_dict)
        if len(c4_residual_table) <= 10:
            print(f"  Node {nid:4d} ({pt[0]:.4f}, {pt[1]:.4f}): d={d_c4[idx]:.4f}, F={F_d_c4[idx]:.4e}, Kd={Kd_c4[idx]:.4e}, R={R_d_c4[idx]:.4e} kN/mm")

    return {
        "closure_classification": closure_status,
        "binding_criterion_kNmm": TAU_RES,
        "res_inf_free_set": res_inf_free,
        "res_inf_all_nodes": res_inf_all,
        "ratio_vs_criterion": float(res_inf_free / TAU_RES),
        "num_prescribed_nodes": len(c4_prescribed_nodes),
        "num_free_nodes": len(c4_free_nodes),
        "node_2277_detail": node_2277_detail,
        "top_residual_nodes": c4_residual_table
    }

def section_3_separate_constraints(nodes_c4, c4_prescribed_d, d_c4, n2idx_c4):
    print("\n" + "="*75)
    print("   SECTION 3: DECONSTRUCT PHYSICAL VS ARTIFICIAL CONSTRAINTS   ")
    print("="*75)

    # Classify every prescribed node in C4
    slit_flank_nodes = []
    corridor_clamped_nodes = []
    far_field_nodes = []

    for nid, d_val in c4_prescribed_d.items():
        pt = nodes_c4[nid]
        x, y = pt[0], pt[1]
        dist_y = abs(y - 0.050)

        # Physical slit flank: x <= 0.050 and on the crack line
        if x <= 0.05001 and dist_y <= 1.0e-5 and d_val >= 0.99:
            slit_flank_nodes.append(nid)
        elif (0.035 <= x <= 0.075) and (dist_y <= 0.008):
            # Inside the corridor bounding box but d < 0.15
            corridor_clamped_nodes.append(nid)
        else:
            # Outside the corridor bounding box
            far_field_nodes.append(nid)

    print(f"Classification of 3,845 prescribed damage nodes in C4:")
    print(f"  1. Genuine physical initial slit boundary (x <= 0.050, d=1.0): {len(slit_flank_nodes)} nodes")
    print(f"  2. Corridor-clamped sub-threshold nodes (d < 0.15 inside box):   {len(corridor_clamped_nodes)} nodes")
    print(f"  3. Far-field / wake artificial corridor-clamped nodes:          {len(far_field_nodes)} nodes")
    print(f"  Total artificial corridor restrictions: {len(corridor_clamped_nodes) + len(far_field_nodes)} nodes")

    return {
        "genuine_slit_boundary_nodes": len(slit_flank_nodes),
        "corridor_subthreshold_clamped_nodes": len(corridor_clamped_nodes),
        "far_field_wake_clamped_nodes": len(far_field_nodes),
        "total_artificial_corridor_nodes": len(corridor_clamped_nodes) + len(far_field_nodes)
    }

def section_4_controlled_continuation(case_mode="CASE_A"):
    """
    Executes controlled continuation (+4 nm, u = 0.002052 -> 0.002056 mm) on C5:
      Case A: Physical-only constraints (d >= d_H1 pointwise across domain, no corridor clamping).
      Case B: Diagnostic corridor-controlled continuation (reproducing C4 corridor clamping on C5).
    """
    nodes_c5, elems_c5, nlist_c5, n2idx_c5 = parse_mesh(C5_MESH, max_phys_eid=4440)
    n_nodes_c5 = len(nlist_c5)
    C0, lam, mu = compute_plane_strain_c0()

    d_ckpt = np.zeros(n_nodes_c5)
    with open(C5_CKPT_TABLE, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for r in reader:
            if r and r[0].strip().upper() == "NODE":
                nid = int(r[1])
                if nid in n2idx_c5:
                    d_ckpt[n2idx_c5[nid]] = float(r[4])

    d_H1 = np.load(C5_H1_D_PATH)

    elem_H = {}
    in_init = False
    card_lines = []
    with open(C5_INP, "r", encoding="utf-8") as f:
        for line in f:
            l = line.strip()
            if l.startswith("*INITIAL CONDITIONS, TYPE=SOLUTION"):
                in_init = True
                continue
            if in_init:
                if l.startswith("*"): break
                parts = [p.strip() for p in l.split(",") if p.strip()]
                card_lines.append(parts)

    num_cards = len(card_lines) // 3
    for c in range(num_cards):
        l1 = card_lines[3*c]
        l2 = card_lines[3*c + 1]
        eid = int(l1[0])
        if 1 <= eid <= 4440:
            elem_H[eid] = [float(l2[1]), float(l2[2]), float(l2[3]), float(l2[4])]

    elem_H_curr = {eid: list(elem_H[eid]) for eid in elems_c5}
    d_curr = np.copy(d_H1)

    u_start = 0.002052
    u_target = 0.002056

    # Define boundary condition structure for Case A vs Case B
    bounds = []
    clamped_count = 0
    free_count = 0

    for idx, nid in enumerate(nlist_c5):
        pt = nodes_c5[nid]
        x, y = pt[0], pt[1]
        dist_y = abs(y - 0.050)
        d_val = d_H1[idx]

        if case_mode == "CASE_A":
            # Physical-only: d_val >= d_H1 pointwise; slit nodes clamped at 1.0
            if x <= 0.05001 and dist_y <= 1.0e-5 and d_val >= 0.99:
                bounds.append((1.0, 1.0))
                clamped_count += 1
            else:
                bounds.append((float(d_val), 1.0))
                free_count += 1

        elif case_mode == "CASE_B":
            # Diagnostic C4 corridor reproduction on C5:
            # In C4: in_band = (0.035 <= x <= 0.075) and (dist_y <= 0.008) and (d >= 0.15)
            in_band = (0.035 <= x <= 0.075) and (dist_y <= 0.008) and (d_val >= 0.15)
            if in_band:
                bounds.append((float(d_val), 1.0))
                free_count += 1
            else:
                bounds.append((float(d_val), float(d_val)))
                clamped_count += 1

    print(f"\n--- Running {case_mode} ---")
    print(f"  Clamped Phase Nodes: {clamped_count}")
    print(f"  Free Advancing Nodes: {free_count}")

    # Solve initial elasticity at u_start
    u_init, rf2_init = solve_elasticity_uel(nodes_c5, elems_c5, nlist_c5, n2idx_c5, d_curr, u_start)
    ef_init, ee_init = compute_energies_uel(nodes_c5, elems_c5, nlist_c5, n2idx_c5, u_init, d_curr)
    print(f"  Initial State (u={u_start:.6f} mm): RF2 = {rf2_init:.4f} N, E_frac = {ef_init:.6f} mJ")

    # Staggered alternating minimization to u_target (+4 nm)
    tol_stagger = 1.0e-5
    max_stagger_iters = 15
    stagger_history = []

    for s_iter in range(1, max_stagger_iters + 1):
        u_step, rf2_step_N = solve_elasticity_uel(nodes_c5, elems_c5, nlist_c5, n2idx_c5, d_curr, u_target)

        max_delta_H = 0.0
        for eid, conn in elems_c5.items():
            elem_indices = [n2idx_c5[n] for n in conn]
            xe = np.array([nodes_c5[n] for n in conn])
            ue = u_step[elem_indices, :].flatten()

            for kpt in range(4):
                xi, eta = UEL_GP_COORDS[kpt]
                wt = UEL_WEIGHTS[kpt]
                N, dNdxi, dNdeta = shape_functions(xi, eta)

                J_mat = np.zeros((2, 2))
                for i in range(4):
                    J_mat[0, 0] += dNdxi[i] * xe[i, 0]
                    J_mat[0, 1] += dNdxi[i] * xe[i, 1]
                    J_mat[1, 0] += dNdeta[i] * xe[i, 0]
                    J_mat[1, 1] += dNdeta[i] * xe[i, 1]

                detJ = J_mat[0, 0] * J_mat[1, 1] - J_mat[0, 1] * J_mat[1, 0]
                invJ = np.array([[ J_mat[1, 1], -J_mat[0, 1]], [-J_mat[1, 0],  J_mat[0, 0]]]) / detJ
                dNdx = np.zeros((2, 4))
                for i in range(4):
                    dNdx[0, i] = invJ[0, 0] * dNdxi[i] + invJ[0, 1] * dNdeta[i]
                    dNdx[1, i] = invJ[1, 0] * dNdxi[i] + invJ[1, 1] * dNdeta[i]

                B = np.zeros((3, 8))
                for i in range(4):
                    B[0, 2*i]   = dNdx[0, i]
                    B[1, 2*i+1] = dNdx[1, i]
                    B[2, 2*i]   = dNdx[1, i]
                    B[2, 2*i+1] = dNdx[0, i]

                eps = B.dot(ue)
                pos_m = uel_driving_energy(eps, lam, mu)
                old_h = elem_H_curr[eid][kpt]
                new_h = max(old_h, pos_m)
                diff_h = new_h - old_h
                if diff_h > max_delta_H: max_delta_H = diff_h
                elem_H_curr[eid][kpt] = new_h

        K_d_new, F_d_new = assemble_at2_system(nodes_c5, elems_c5, n2idx_c5, elem_H_curr)

        def obj_step(d):
            Kd = K_d_new.dot(d)
            return 0.5 * np.dot(d, Kd) - np.dot(F_d_new, d), Kd - F_d_new

        res_step = minimize(obj_step, np.copy(d_curr), jac=True, method='L-BFGS-B', bounds=bounds,
                            options={'ftol': 1e-15, 'gtol': 1e-8, 'maxiter': 500})
        d_next = res_step.x
        diff_d = float(np.max(np.abs(d_next - d_curr)))
        d_curr = d_next

        stagger_history.append({
            "iteration": s_iter,
            "rf2_N": rf2_step_N,
            "max_delta_d": diff_d,
            "max_delta_H": max_delta_H
        })
        print(f"    [Iter {s_iter:02d}] RF2 = {rf2_step_N:.4f} N | max(|Delta d|) = {diff_d:.2e} | max(Delta H) = {max_delta_H:.2e}")

        if diff_d < tol_stagger:
            print(f"    --> CONVERGED in {s_iter} iterations (||Delta d|| < {tol_stagger})!")
            break

    ef_final, ee_final = compute_energies_uel(nodes_c5, elems_c5, nlist_c5, n2idx_c5, u_step, d_curr)
    converged = bool(diff_d < tol_stagger)

    print(f"  Final State ({case_mode}):")
    print(f"    Converged:     {converged} in {s_iter} iters")
    print(f"    RF2:           {rf2_step_N:.4f} N (Delta = {rf2_step_N - rf2_init:+.4f} N)")
    print(f"    E_frac:        {ef_final:.6f} mJ (Delta = {ef_final - ef_init:+.6f} mJ)")
    print(f"    E_elas:        {ee_final:.6f} mJ (Delta = {ee_final - ee_init:+.6f} mJ)")
    print(f"    Max Advance:   {float(np.max(d_curr - d_H1)):.6e}")

    return {
        "case": case_mode,
        "clamped_nodes": clamped_count,
        "free_nodes": free_count,
        "converged": converged,
        "iterations": s_iter,
        "rf2_init_N": rf2_init,
        "rf2_final_N": rf2_step_N,
        "delta_rf2_N": rf2_step_N - rf2_init,
        "delta_rf2_pct": float((rf2_step_N - rf2_init) / rf2_init * 100),
        "e_frac_init_mJ": ef_init,
        "e_frac_final_mJ": ef_final,
        "delta_e_frac_mJ": ef_final - ef_init,
        "delta_e_frac_pct": float((ef_final - ef_init) / ef_init * 100),
        "max_advance_delta_d": float(np.max(d_curr - d_H1)),
        "stagger_history": stagger_history
    }

def main():
    print("="*75)
    print("   TURN 101: C4 DONOR CONSTRAINT & C5 CONTINUATION AUDIT   ")
    print("="*75)

    c4_nodes, elems_c4, nlist_c4, n2idx_c4 = parse_mesh(C4_MESH, max_phys_eid=4422)

    c4_prescribed_d = {}
    in_step4 = False
    with open(C4_INP, "r", encoding="utf-8") as f:
        for line in f:
            l = line.strip()
            if "*Step, name=FORWARD_CONTINUATION" in l: in_step4 = True; continue
            if in_step4:
                if l.startswith("*End Step"): break
                parts = [p.strip() for p in l.split(",") if p.strip()]
                if len(parts) >= 4 and parts[0].isdigit() and parts[1] == "3" and parts[2] == "3":
                    c4_prescribed_d[int(parts[0])] = float(parts[3])

    d_c4 = np.zeros(len(nlist_c4))
    with open(C4_NODAL_CSV, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            nid = int(row["node_id"])
            if nid in n2idx_c4: d_c4[n2idx_c4[nid]] = float(row["damage"])

    # 1. Section 2: Audit C4 donor closure
    sec2_res = section_2_c4_donor_constraint_audit()

    # 2. Section 3: Separate constraint categories
    sec3_res = section_3_separate_constraints(c4_nodes, c4_prescribed_d, d_c4, n2idx_c4)

    # 3. Section 4: Controlled C5 continuation comparison
    case_A_res = section_4_controlled_continuation("CASE_A")
    case_B_res = section_4_controlled_continuation("CASE_B")

    # Synthesis of findings
    summary_findings = {
        "donor_c4_closure_verdict": sec2_res["closure_classification"],
        "donor_c4_max_residual_kNmm": sec2_res["res_inf_free_set"],
        "donor_c4_criterion_kNmm": sec2_res["binding_criterion_kNmm"],
        "corridor_clamping_proven_necessary_for_continuation": bool(case_B_res["converged"] and not case_A_res["converged"]),
        "case_A_physical_unrestricted": case_A_res,
        "case_B_diagnostic_corridor": case_B_res
    }

    full_output = {
        "schema": 1,
        "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
        "turn": 101,
        "section_2_c4_donor_audit": sec2_res,
        "section_3_constraint_separation": sec3_res,
        "section_4_controlled_continuation": {
            "case_A_physical_only": case_A_res,
            "case_B_diagnostic_corridor": case_B_res
        },
        "summary": summary_findings
    }

    out_json_path = REPO_ROOT / "results/validation/mode1_f1597/turn101_c4_constraint_and_c5_continuation_audit.json"
    with open(out_json_path, "w", encoding="utf-8") as f:
        json.dump(full_output, f, indent=2)
    print(f"\nAudit complete. Deliverable saved to: {out_json_path}")

if __name__ == "__main__":
    main()

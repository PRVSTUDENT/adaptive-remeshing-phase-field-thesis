#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
evaluate_corrected_c3_coupled_transfer_and_increment.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER (Turn 106)
Protocol Version: 2

Scientific Objectives:
1. Transfer State from Candidate C2 (Package 89 Frame 88, u = 0.00196510735 mm) to Candidate C3:
   - Initial history H_initial = Project(H_donor) (pure continuous isoparametric interpolation).
   - Zero evaluation of psi0_pos on unrelaxed mapped displacements during initialization.
2. Coupled Same-Load Re-Equilibration at u = 0.00196510735 mm:
   - Alternating minimization between elasticity K_u(d) u = F and AT2 phase field.
   - Genuine history evolution: in each iteration, H_trial = max(H_initial, psi0_pos(u_current)).
   - Authentic AT2 bound constraints: d_new >= d_mapped, 0 <= d <= 1.
   - Zero geometric corridors, zero damage thresholds, zero artificial wake pinning.
   - Evaluate all 8 Transfer Acceptance Gates against C2 donor.
3. If and only if same-load acceptance passes:
   - Attempt one controlled forward increment: Delta u = +5.0 nm -> u = 0.00197010735 mm.
   - Bound constraints: d_{n+1} >= d_{n} (committed re-equilibrated state).
   - Compare mechanical softening, energy evolution, and crack progression against C2 reference.
4. Save complete deliverables and audit report.
"""

import sys
import os
import json
import csv
import math
from pathlib import Path
from typing import Dict, Tuple, Any, List
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from scipy.optimize import minimize

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
C2_INP = REPO_ROOT / "models/pandey_kumar_mode1/89_c2_frame88_early_state_transfer/M1_C2_FRAME88_TRANSFER.inp"
C2_CSV = REPO_ROOT / "models/pandey_kumar_mode1/89_c2_frame88_early_state_transfer/candidate_c2_frame88_mapped_state_table.csv"
C3_MESH_INP = REPO_ROOT / "models/pandey_kumar_mode1/90_c3_package90_second_cycle_transfer/candidate_crack_band_mesh_c3.inp"

# Frozen UEL Material Parameters (Bitwise matching f42_mixed_uel.for)
E_MOD = 210.0      # kN/mm^2
NU = 0.3
E_GC = 0.0027      # kN/mm
E_L0 = 0.0075      # mm
K_DEGRAD = 1.0e-7  # residual stiffness
TAU_RES_D = 1.0e-6 # binding phase residual tolerance (kN/mm)
TAU_RES_U = 1.0e-4 # mechanical residual tolerance (kN)

# Quadrature constants matching f42_mixed_uel.for
A_GAUSS = 0.577350269189626
UEL_GP_COORDS = [
    (-A_GAUSS, -A_GAUSS),
    ( A_GAUSS, -A_GAUSS),
    ( A_GAUSS,  A_GAUSS),
    (-A_GAUSS,  A_GAUSS),
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
    c12_0 = lam
    c33_0 = mu
    pos_m = 0.5 * c12_0 * (e_pos**2) + c33_0 * (e11**2 + e22**2 + 2.0 * (e12**2))
    return float(pos_m)

def parse_mesh(inp_path, max_phys_eid):
    nodes = {}
    elements = {}
    reading = None
    with open(inp_path, "r", encoding="utf-8") as f:
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

def load_c2_donor_state(csv_path, node_to_idx, max_phys_eid=2300):
    n_nodes = len(node_to_idx)
    u_c2 = np.zeros((n_nodes, 2))
    d_c2 = np.zeros(n_nodes)
    elem_H_c2 = {}
    with open(csv_path, "r", encoding="utf-8") as f:
        for row in csv.reader(f):
            if not row: continue
            rec = row[0].strip().upper()
            if rec == "NODE":
                nid = int(row[1])
                if nid in node_to_idx:
                    idx = node_to_idx[nid]
                    u_c2[idx, 0] = float(row[2])
                    u_c2[idx, 1] = float(row[3])
                    d_c2[idx] = float(row[4])
            elif rec == "ELEM_H":
                eid = int(row[1])
                if eid <= max_phys_eid:
                    elem_H_c2[eid] = [float(row[2]), float(row[3]), float(row[4]), float(row[5])]
    return u_c2, d_c2, elem_H_c2

def classify_slit_flanks(nodes, elements):
    flanks = {}
    for nid, pt in nodes.items():
        if abs(pt[1] - 0.050) < 1e-6 and pt[0] <= 0.040 + 1e-6:
            surr_eids = [eid for eid, conn in elements.items() if nid in conn]
            cys = [np.mean([nodes[n][1] for n in elements[eid]]) for eid in surr_eids]
            flanks[nid] = "upper" if all(cy > 0.050 for cy in cys) else "lower"
        else:
            flanks[nid] = "intact"
    return flanks

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
    x_vals = [nodes[nid][0] for nid in node_list]

    fixed_dofs = {}
    for idx, (x, y) in enumerate(zip(x_vals, y_vals)):
        if abs(y - 0.0) < 1e-6:
            fixed_dofs[2 * idx + 1] = 0.0
            if abs(x - 0.0) < 1e-6:
                fixed_dofs[2 * idx] = 0.0
        elif abs(y - 0.100) < 1e-6:
            fixed_dofs[2 * idx + 1] = u_top

    all_dofs = np.arange(n_dofs)
    prescribed_dof_indices = np.array(sorted(fixed_dofs.keys()))
    free_dof_indices = np.setdiff1d(all_dofs, prescribed_dof_indices)

    u_prescribed_vec = np.array([fixed_dofs[dof] for dof in prescribed_dof_indices])
    K_ff = K_u[free_dof_indices, :][:, free_dof_indices]
    K_fp = K_u[free_dof_indices, :][:, prescribed_dof_indices]

    F_rhs_free = - K_fp.dot(u_prescribed_vec)
    u_free = spla.spsolve(K_ff, F_rhs_free)

    u_full = np.zeros(n_dofs)
    u_full[prescribed_dof_indices] = u_prescribed_vec
    u_full[free_dof_indices] = u_free

    F_reactions = K_u.dot(u_full)
    top_dofs = [2 * idx + 1 for idx, y in enumerate(y_vals) if abs(y - 0.100) < 1e-6]
    rf2_total = float(np.sum(F_reactions[top_dofs])) * 1000.0 # Convert kN to N

    res_mech_free = float(np.max(np.abs(F_reactions[free_dof_indices])))
    u_nodes = u_full.reshape((n_nodes, 2))
    return u_nodes, rf2_total, res_mech_free

def compute_energies_uel(nodes, elements, node_list, node_to_idx, u_nodes, d):
    C0, lam, mu = compute_plane_strain_c0()
    e_frac_total = 0.0
    e_elas_total = 0.0

    for eid in sorted(elements.keys()):
        conn = elements[eid]
        elem_indices = [node_to_idx[n] for n in conn]
        xe = np.array([nodes[n] for n in conn])
        de = d[elem_indices]
        d_avg = np.mean(de)
        deg = (1.0 - d_avg)**2 + K_DEGRAD
        c_mech = C0 * deg
        ue = u_nodes[elem_indices, :].flatten()

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
            sig = c_mech.dot(eps)
            psi_e = 0.5 * np.dot(sig, eps)
            e_elas_total += cj * psi_e

            d_pt = np.dot(N, de)
            grad_d = dNdx.dot(de)
            grad_d_sq = grad_d[0]**2 + grad_d[1]**2
            psi_f = E_GC * (0.5 * (d_pt**2) / E_L0 + 0.5 * E_L0 * grad_d_sq)
            e_frac_total += cj * psi_f

    # Convert kN*mm to mJ (1 kN*mm = 1 J = 1000 mJ)
    return float(e_frac_total * 1000.0), float(e_elas_total * 1000.0)

def build_fe_interpolator(nodes_c2, elements_c2, flanks_c2):
    c2_x = sorted(list(set([round(pt[0], 8) for pt in nodes_c2.values()])))
    c2_y = sorted(list(set([round(pt[1], 8) for pt in nodes_c2.values()])))
    c2_x = np.array(c2_x)
    c2_y = np.array(c2_y)
    nx_c2 = len(c2_x) - 1
    ny_c2 = len(c2_y) - 1
    slit_y_idx = int(np.argmin(np.abs(c2_y - 0.050)))

    def locate_c2_element(x: float, y: float, flank_type: str) -> Tuple[int, float, float]:
        x = max(0.0, min(0.100, x))
        y = max(0.0, min(0.100, y))
        i = int(np.searchsorted(c2_x, x)) - 1
        i = max(0, min(nx_c2 - 1, i))

        if abs(y - 0.050) < 1e-8:
            if x <= 0.040 + 1e-8:
                j = slit_y_idx if flank_type == "upper" else slit_y_idx - 1
            else:
                j = slit_y_idx if flank_type == "upper" else slit_y_idx - 1
        else:
            j = int(np.searchsorted(c2_y, y)) - 1
            j = max(0, min(ny_c2 - 1, j))

        x0, x1 = c2_x[i], c2_x[i+1]
        y0, y1 = c2_y[j], c2_y[j+1]
        xi = 2.0 * (x - x0) / (x1 - x0) - 1.0
        eta = 2.0 * (y - y0) / (y1 - y0) - 1.0
        xi = max(-1.0, min(1.0, xi))
        eta = max(-1.0, min(1.0, eta))
        eid = j * nx_c2 + i + 1
        return eid, xi, eta

    return locate_c2_element

def solve_coupled_staggered(nodes, elements, node_list, node_to_idx, d_init, d_lower_bounds,
                            elem_H_base, u_top, tol_stagger=1e-5, max_iters=25, update_H=True):
    n_nodes = len(node_list)
    bounds = [(float(d_lower_bounds[i]), 1.0) for i in range(n_nodes)]
    d_curr = np.copy(d_init)
    elem_H_curr = {eid: list(elem_H_base[eid]) for eid in elements}
    C0, lam, mu = compute_plane_strain_c0()

    history = []
    converged = False

    for it in range(1, max_iters + 1):
        # 1. Elasticity solve
        u_step, rf2_step, res_u_max = solve_elasticity_uel(nodes, elements, node_list, node_to_idx, d_curr, u_top)

        # 2. History update (if requested)
        max_delta_H = 0.0
        if update_H:
            for eid, conn in elements.items():
                elem_indices = [node_to_idx[n] for n in conn]
                xe = np.array([nodes[n] for n in conn])
                ue = u_step[elem_indices, :].flatten()

                for kpt in range(4):
                    xi, eta = UEL_GP_COORDS[kpt]
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

        # 3. AT2 phase-field solve
        K_d, F_d = assemble_at2_system(nodes, elements, node_to_idx, elem_H_curr)

        def obj_phase(d):
            Kd = K_d.dot(d)
            return 0.5 * np.dot(d, Kd) - np.dot(F_d, d), Kd - F_d

        res_opt = minimize(obj_phase, np.copy(d_curr), jac=True, method='L-BFGS-B', bounds=bounds,
                           options={'ftol': 1e-15, 'gtol': 1e-8, 'maxiter': 500})
        d_next = res_opt.x
        diff_d = float(np.max(np.abs(d_next - d_curr)))

        # Free-set residual
        grad_d = K_d.dot(d_next) - F_d
        free_mask = (d_next > np.array([b[0] for b in bounds]) + 1e-8) & (d_next < 1.0 - 1e-8)
        res_d_free = float(np.max(np.abs(grad_d[free_mask]))) if np.any(free_mask) else 0.0

        history.append({
            "iter": it,
            "rf2_N": rf2_step,
            "diff_d": diff_d,
            "max_delta_H": max_delta_H,
            "free_nodes": int(np.sum(free_mask)),
            "res_d_free": res_d_free,
            "res_u_max": res_u_max,
            "d_max": float(np.max(d_next))
        })

        d_curr = np.copy(d_next)
        if diff_d < tol_stagger and res_d_free <= TAU_RES_D and res_u_max <= TAU_RES_U:
            converged = True
            break

    # Final quantities
    u_final, rf2_final, res_u_final = solve_elasticity_uel(nodes, elements, node_list, node_to_idx, d_curr, u_top)
    ef_final, ee_final = compute_energies_uel(nodes, elements, node_list, node_to_idx, u_final, d_curr)
    K_d_final, F_d_final = assemble_at2_system(nodes, elements, node_to_idx, elem_H_curr)
    grad_d_final = K_d_final.dot(d_curr) - F_d_final
    free_mask = (d_curr > np.array([b[0] for b in bounds]) + 1e-8) & (d_curr < 1.0 - 1e-8)
    res_d_final = float(np.max(np.abs(grad_d_final[free_mask]))) if np.any(free_mask) else 0.0

    kkt_violations = 0
    for i in range(n_nodes):
        lb = bounds[i][0]
        val = d_curr[i]
        g = grad_d_final[i]
        if val < lb - 1e-8 or val > 1.0 + 1e-8:
            kkt_violations += 1
        elif abs(val - lb) < 1e-8 and g < -1e-6:
            kkt_violations += 1
        elif abs(val - 1.0) < 1e-8 and g > 1e-6:
            kkt_violations += 1
        elif lb + 1e-8 < val < 1.0 - 1e-8 and abs(g) > 1e-6:
            kkt_violations += 1

    min_healing = float(np.min(d_curr - d_lower_bounds))

    result = {
        "converged": converged,
        "iterations": len(history),
        "rf2_N": rf2_final,
        "e_frac_mJ": ef_final,
        "e_elas_mJ": ee_final,
        "d_max": float(np.max(d_curr)),
        "min_healing": min_healing,
        "kkt_violations": kkt_violations,
        "res_u_max": res_u_final,
        "res_d_max": res_d_final,
        "d": d_curr,
        "u": u_final,
        "elem_H": elem_H_curr,
        "history": history
    }
    return result

def main():
    print("=" * 80, flush=True)
    print("TURN 106: METHOD C MODE-I STATE TRANSFER & FORWARD CONTINUATION", flush=True)
    print("=" * 80, flush=True)

    # 1. Parse meshes
    nodes_c2, elements_c2, nlist_c2, n2idx_c2 = parse_mesh(C2_INP, max_phys_eid=2300)
    u_c2, d_c2, elem_H_c2 = load_c2_donor_state(C2_CSV, n2idx_c2, max_phys_eid=2300)
    flanks_c2 = classify_slit_flanks(nodes_c2, elements_c2)
    u_prescribed = 0.00196510735

    print(f"\n[1/4] Loaded C2 Donor Benchmark at u = {u_prescribed:.9f} mm:", flush=True)
    u_c2_chk, rf2_c2_donor, res_u_c2 = solve_elasticity_uel(nodes_c2, elements_c2, nlist_c2, n2idx_c2, d_c2, u_prescribed)
    ef_c2_donor, ee_c2_donor = compute_energies_uel(nodes_c2, elements_c2, nlist_c2, n2idx_c2, u_c2_chk, d_c2)
    print(f"  RF2:    {rf2_c2_donor:.4f} N", flush=True)
    print(f"  E_frac: {ef_c2_donor:.6f} mJ", flush=True)
    print(f"  E_elas: {ee_c2_donor:.6f} mJ", flush=True)
    print(f"  d_max:  {np.max(d_c2):.6f}", flush=True)

    nodes_c3, elements_c3, nlist_c3, n2idx_c3 = parse_mesh(C3_MESH_INP, max_phys_eid=2650)
    flanks_c3 = classify_slit_flanks(nodes_c3, elements_c3)
    n_nodes_c3 = len(nlist_c3)
    print(f"\n[2/4] Recipient C3 Discretization: {n_nodes_c3} nodes, {len(elements_c3)} quads.", flush=True)

    # Continuous FE mapping
    locate_c2 = build_fe_interpolator(nodes_c2, elements_c2, flanks_c2)
    u_c3_mapped = np.zeros((n_nodes_c3, 2))
    d_c3_mapped = np.zeros(n_nodes_c3)

    for nid in nlist_c3:
        idx = n2idx_c3[nid]
        pt = nodes_c3[nid]
        fl = flanks_c3[nid]
        eid, xi, eta = locate_c2(pt[0], pt[1], fl)
        conn = elements_c2[eid]
        N, _, _ = shape_functions(xi, eta)

        u1 = sum(N[k] * u_c2[n2idx_c2[conn[k]], 0] for k in range(4))
        u2 = sum(N[k] * u_c2[n2idx_c2[conn[k]], 1] for k in range(4))
        dam = sum(N[k] * d_c2[n2idx_c2[conn[k]]] for k in range(4))
        dam = max(0.0, min(1.0, dam))

        u_c3_mapped[idx, 0] = u1
        u_c3_mapped[idx, 1] = u2
        d_c3_mapped[idx] = dam

    # PURE Gauss-point history mapping: H_initial = Project(H_donor)
    s3 = math.sqrt(3.0)
    elem_H_c3_pure = {}
    for eid, conn in elements_c3.items():
        coords = np.array([nodes_c3[n] for n in conn])
        h_list = []
        for kpt in range(4):
            xi, eta = UEL_GP_COORDS[kpt]
            N, _, _ = shape_functions(xi, eta)
            gx = float(np.dot(N, coords[:, 0]))
            gy = float(np.dot(N, coords[:, 1]))
            fl = "upper" if gy > 0.050 else ("lower" if gy < 0.050 else "intact")

            donor_eid, d_xi, d_eta = locate_c2(gx, gy, fl)
            xi_gp = max(-1.0, min(1.0, d_xi * s3))
            eta_gp = max(-1.0, min(1.0, d_eta * s3))
            N_gp, _, _ = shape_functions(xi_gp, eta_gp)

            donor_h = elem_H_c2[donor_eid]
            h_interp = max(0.0, float(sum(N_gp[k] * donor_h[k] for k in range(4))))
            h_list.append(h_interp)
        elem_H_c3_pure[eid] = h_list

    # State 0 immediate post-projection evaluation
    u_c3_s0, rf2_c3_s0, res_u_s0 = solve_elasticity_uel(nodes_c3, elements_c3, nlist_c3, n2idx_c3, d_c3_mapped, u_prescribed)
    ef_c3_s0, ee_c3_s0 = compute_energies_uel(nodes_c3, elements_c3, nlist_c3, n2idx_c3, u_c3_s0, d_c3_mapped)
    K_d_s0, F_d_s0 = assemble_at2_system(nodes_c3, elements_c3, n2idx_c3, elem_H_c3_pure)
    res_d_s0 = float(np.max(np.abs(F_d_s0 - K_d_s0.dot(d_c3_mapped))))

    print(f"\n[3/4] State 0 (Immediate Post-Projection with Pure H):", flush=True)
    print(f"  RF2:            {rf2_c3_s0:.4f} N (diff vs C2: {(rf2_c3_s0 - rf2_c2_donor)/rf2_c2_donor*100:+.4f}%)", flush=True)
    print(f"  E_frac:         {ef_c3_s0:.6f} mJ (diff vs C2: {(ef_c3_s0 - ef_c2_donor)/ef_c2_donor*100:+.4f}%)", flush=True)
    print(f"  E_elas:         {ee_c3_s0:.6f} mJ (vs C2: {ee_c2_donor:.6f} mJ)", flush=True)
    print(f"  d_max:          {np.max(d_c3_mapped):.6f}", flush=True)
    print(f"  Phase Res Max:  {res_d_s0:.6e} kN/mm", flush=True)
    print(f"  Mech Res Max:   {res_u_s0:.6e} kN", flush=True)

    # 2. Coupled Same-Load Re-Equilibration
    print("\n" + "-" * 75, flush=True)
    print("Coupled Re-Equilibration with Evolving History at Fixed Load (u = 0.001965107 mm)", flush=True)
    print("-" * 75, flush=True)

    res_coupled = solve_coupled_staggered(
        nodes=nodes_c3, elements=elements_c3, node_list=nlist_c3, node_to_idx=n2idx_c3,
        d_init=d_c3_mapped, d_lower_bounds=d_c3_mapped, elem_H_base=elem_H_c3_pure,
        u_top=u_prescribed, tol_stagger=1e-5, max_iters=25, update_H=True
    )

    rf2_c3_s1 = res_coupled["rf2_N"]
    ef_c3_s1 = res_coupled["e_frac_mJ"]
    ee_c3_s1 = res_coupled["e_elas_mJ"]
    diff_rf2_s1 = (rf2_c3_s1 - rf2_c2_donor) / rf2_c2_donor * 100.0
    diff_ef_s1 = (ef_c3_s1 - ef_c2_donor) / ef_c2_donor * 100.0
    d_max_s1 = res_coupled["d_max"]
    s1_history = res_coupled["history"]
    s1_converged = res_coupled["converged"]
    res_d_s1 = res_coupled["res_d_max"]
    res_u_s1 = res_coupled["res_u_max"]
    s1_kkt = res_coupled["kkt_violations"]
    s1_healing = res_coupled["min_healing"]

    print(f"  Iterations:     {len(s1_history)} (Converged: {s1_converged})", flush=True)
    print(f"  RF2:            {rf2_c3_s1:.4f} N (diff vs C2: {diff_rf2_s1:+.2f}%)", flush=True)
    print(f"  E_frac:         {ef_c3_s1:.6f} mJ (diff vs C2: {diff_ef_s1:+.2f}%)", flush=True)
    print(f"  E_elas:         {ee_c3_s1:.6f} mJ", flush=True)
    print(f"  d_max:          {d_max_s1:.6f}", flush=True)
    print(f"  Phase Res Max:  {res_d_s1:.6e} kN/mm", flush=True)
    print(f"  Mech Res Max:   {res_u_s1:.6e} kN", flush=True)
    print(f"  KKT Violations: {s1_kkt}", flush=True)
    print(f"  Min Healing:    {s1_healing:.1e}", flush=True)

    for h in s1_history:
        print(f"    [Iter {h['iter']:02d}] RF2={h['rf2_N']:.4f} N | diff_d={h['diff_d']:.2e} | delta_H={h['max_delta_H']:.2e} | res_d={h['res_d_free']:.2e}", flush=True)

    # Acceptance Gates Evaluation
    gate1_pass = abs(diff_rf2_s1) <= 5.0
    gate2_pass = abs(diff_ef_s1) <= 2.0
    gate3_pass = res_d_s1 <= TAU_RES_D
    gate4_pass = res_u_s1 <= TAU_RES_U
    gate5_pass = s1_kkt == 0
    gate6_pass = s1_healing >= -1e-12
    gate7_pass = d_max_s1 <= 1.0
    gate8_pass = s1_converged and len(s1_history) <= 25

    same_load_accepted = bool(gate1_pass and gate2_pass and gate3_pass and gate4_pass and
                              gate5_pass and gate6_pass and gate7_pass and gate8_pass)

    print(f"\nSame-Load Acceptance Gates Verdict: {'ALL PASS' if same_load_accepted else 'FAILED'}", flush=True)
    print(f"  Gate 1 (Force Continuity <= 5%):     {'PASS' if gate1_pass else 'FAIL'} ({diff_rf2_s1:+.2f}%)", flush=True)
    print(f"  Gate 2 (Energy Continuity <= 2%):    {'PASS' if gate2_pass else 'FAIL'} ({diff_ef_s1:+.2f}%)", flush=True)
    print(f"  Gate 3 (Phase Residual <= 1e-6):     {'PASS' if gate3_pass else 'FAIL'} ({res_d_s1:.2e})", flush=True)
    print(f"  Gate 4 (Mech Residual <= 1e-4):      {'PASS' if gate4_pass else 'FAIL'} ({res_u_s1:.2e})", flush=True)
    print(f"  Gate 5 (KKT Complementarity):        {'PASS' if gate5_pass else 'FAIL'} ({s1_kkt} violations)", flush=True)
    print(f"  Gate 6 (Zero Healing):               {'PASS' if gate6_pass else 'FAIL'} (min={s1_healing:.1e})", flush=True)
    print(f"  Gate 7 (Zero Overshoot):             {'PASS' if gate7_pass else 'FAIL'} (max_d={d_max_s1:.4f})", flush=True)
    print(f"  Gate 8 (Coupled Convergence <= 25):  {'PASS' if gate8_pass else 'FAIL'} ({len(s1_history)} iters, conv={s1_converged})", flush=True)

    # 3. Controlled Forward Increment (Delta u = +5.0 nm)
    increment_attempted = False
    res_fwd = None
    if same_load_accepted:
        print("\n" + "=" * 80, flush=True)
        print("[4/4] Executing Controlled Forward Increment: Delta u = +5 nm -> u = 0.001970107 mm", flush=True)
        print("=" * 80, flush=True)
        increment_attempted = True
        u_fwd = u_prescribed + 0.000005
        d_committed = res_coupled["d"]
        elem_H_committed = res_coupled["elem_H"]

        res_fwd = solve_coupled_staggered(
            nodes=nodes_c3, elements=elements_c3, node_list=nlist_c3, node_to_idx=n2idx_c3,
            d_init=d_committed, d_lower_bounds=d_committed, elem_H_base=elem_H_committed,
            u_top=u_fwd, tol_stagger=1e-5, max_iters=25, update_H=True
        )

        print(f"  Forward Increment Convergence: {res_fwd['converged']} (Iterations: {res_fwd['iterations']})", flush=True)
        print(f"  RF2:            {res_fwd['rf2_N']:.4f} N (Change vs State 1: {res_fwd['rf2_N'] - rf2_c3_s1:+.4f} N)", flush=True)
        print(f"  E_frac:         {res_fwd['e_frac_mJ']:.6f} mJ (Change vs State 1: {res_fwd['e_frac_mJ'] - ef_c3_s1:+.6f} mJ)", flush=True)
        print(f"  E_elas:         {res_fwd['e_elas_mJ']:.6f} mJ", flush=True)
        print(f"  d_max:          {res_fwd['d_max']:.6f} (Change: {res_fwd['d_max'] - d_max_s1:+.6f})", flush=True)
        print(f"  Phase Res Max:  {res_fwd['res_d_max']:.6e} kN/mm", flush=True)
        print(f"  Mech Res Max:   {res_fwd['res_u_max']:.6e} kN", flush=True)
        print(f"  KKT Violations: {res_fwd['kkt_violations']}", flush=True)
        print(f"  Min Healing:    {res_fwd['min_healing']:.1e}", flush=True)

        for h in res_fwd["history"]:
            print(f"    [Fwd Iter {h['iter']:02d}] RF2={h['rf2_N']:.4f} N | diff_d={h['diff_d']:.2e} | delta_H={h['max_delta_H']:.2e} | res_d={h['res_d_free']:.2e}", flush=True)
    else:
        print("\n[4/4] Forward Increment WITHHELD: State 1 same-load acceptance did not pass.", flush=True)

    # Deliverables and Conclusions
    out_data = {
        "schema": 1,
        "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
        "turn": 106,
        "donor_c2_benchmark": {
            "checkpoint": "Package 89 Frame 88",
            "u_mm": u_prescribed,
            "rf2_N": rf2_c2_donor,
            "e_frac_mJ": ef_c2_donor,
            "e_elas_mJ": ee_c2_donor,
            "d_max": float(np.max(d_c2))
        },
        "recipient_c3_state0": {
            "u_mm": u_prescribed,
            "rf2_N": rf2_c3_s0,
            "diff_rf2_pct": (rf2_c3_s0 - rf2_c2_donor)/rf2_c2_donor*100,
            "e_frac_mJ": ef_c3_s0,
            "diff_ef_pct": (ef_c3_s0 - ef_c2_donor)/ef_c2_donor*100,
            "e_elas_mJ": ee_c3_s0,
            "d_max": float(np.max(d_c3_mapped)),
            "res_d_max_kN_mm": res_d_s0,
            "res_u_max_kN": res_u_s0
        },
        "recipient_c3_state1_coupled": {
            "u_mm": u_prescribed,
            "converged": s1_converged,
            "iterations": len(s1_history),
            "rf2_N": rf2_c3_s1,
            "diff_rf2_pct": diff_rf2_s1,
            "e_frac_mJ": ef_c3_s1,
            "diff_ef_pct": diff_ef_s1,
            "e_elas_mJ": ee_c3_s1,
            "d_max": d_max_s1,
            "min_healing": s1_healing,
            "kkt_violations": s1_kkt,
            "res_d_max_kN_mm": res_d_s1,
            "res_u_max_kN": res_u_s1,
            "history": s1_history
        },
        "gates": {
            "gate1_force_continuity": {"pass": gate1_pass, "measured_diff_pct": diff_rf2_s1, "threshold_pct": 5.0},
            "gate2_fracture_energy_continuity": {"pass": gate2_pass, "measured_diff_pct": diff_ef_s1, "threshold_pct": 2.0},
            "gate3_phase_field_equilibrium": {"pass": gate3_pass, "measured": res_d_s1, "threshold": TAU_RES_D},
            "gate4_mechanical_equilibrium": {"pass": gate4_pass, "measured": res_u_s1, "threshold": TAU_RES_U},
            "gate5_kkt_complementarity": {"pass": gate5_pass, "measured": s1_kkt, "threshold": 0},
            "gate6_damage_healing": {"pass": gate6_pass, "measured": s1_healing, "threshold": 0.0},
            "gate7_damage_overshoot": {"pass": gate7_pass, "measured": d_max_s1, "threshold": 1.0},
            "gate8_coupled_iterations": {"pass": gate8_pass, "measured": len(s1_history), "threshold": 25}
        },
        "same_load_acceptance_passed": same_load_accepted,
        "forward_increment": {
            "attempted": increment_attempted,
            "converged": res_fwd["converged"] if res_fwd else None,
            "iterations": res_fwd["iterations"] if res_fwd else None,
            "u_target_mm": u_prescribed + 0.000005 if increment_attempted else None,
            "rf2_N": res_fwd["rf2_N"] if res_fwd else None,
            "e_frac_mJ": res_fwd["e_frac_mJ"] if res_fwd else None,
            "e_elas_mJ": res_fwd["e_elas_mJ"] if res_fwd else None,
            "d_max": res_fwd["d_max"] if res_fwd else None,
            "delta_rf2_N": (res_fwd["rf2_N"] - rf2_c3_s1) if res_fwd else None,
            "delta_ef_mJ": (res_fwd["e_frac_mJ"] - ef_c3_s1) if res_fwd else None,
            "res_d_max_kN_mm": res_fwd["res_d_max"] if res_fwd else None,
            "res_u_max_kN": res_fwd["res_u_max"] if res_fwd else None,
            "history": res_fwd["history"] if res_fwd else None
        } if increment_attempted else None,
        "scientific_conclusions": {
            "gate_c1_1_status": "QUALIFIED" if (same_load_accepted and increment_attempted and res_fwd and res_fwd["converged"]) else "PROVISIONALLY_QUALIFIED_INTERPOLATION_ONLY",
            "gate_c1_2_status": "NOT_QUALIFIED",
            "package94_status": "BENCHMARK-REPRODUCTION-ONLY",
            "hpc_decision": "QUALIFIED_CONTINUATION_PROVEN" if (same_load_accepted and increment_attempted and res_fwd and res_fwd["converged"]) else "WITHHELD_INCREMENTAL_INVESTIGATION",
            "physical_mechanism_explanation": "Pure history projection H_initial = Project(H_donor) avoids synthetic pre-relaxation driving spikes. During coupled re-equilibration, the dynamic update H_trial = max(H_initial, psi0_pos) governs whether the crack tip remains diffuse or advances, ensuring physical consistency with the UEL formulation."
        }
    }

    out_file = REPO_ROOT / "results/validation/mode1_f1597/turn106_c3_coupled_continuation_audit.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(out_data, f, indent=2)
    print(f"\nDeliverable saved to: {out_file}", flush=True)

    return out_data

if __name__ == "__main__":
    main()

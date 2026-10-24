#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_aligned_forward_continuation.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER (Turn 100)
Protocol Version: 2

Tests staggered coupled continuation for C5 (+4 nm, u = 0.002052 mm -> 0.002056 mm)
with 100% aligned UEL quadrature ordering, UEL driving energy, and element-average degradation.
Compares two irreversibility bound hypotheses:
  Hypothesis A: d >= d_ckpt (unconstrained wake)
  Hypothesis B: d >= d_H1 (irreversible state preservation from verified H^1 checkpoint)
  Hypothesis C: Active-set forward continuation (clamping wake/flank nodes as in C4 Step 4)
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
C5_DIR = REPO_ROOT / "models/pandey_kumar_mode1/103_c5_h1_transfer_pilot"
C5_MESH = C5_DIR / "candidate_crack_band_mesh_c5.inp"
C5_INP = C5_DIR / "M1_C5_PACKAGE103_H1_PILOT.inp"
C5_CKPT_TABLE = REPO_ROOT / "models/pandey_kumar_mode1/102_r1_c5_coupled_staggered_history_repaired/candidate_c5_frame7_mapped_state_table.csv"
C5_H1_D_PATH = REPO_ROOT / "results/validation/mode1_f1597/c5_h1_bound_constrained_d.npy"

# Material & Phase Field Parameters
E_MOD = 210.0      # kN/mm^2
NU = 0.3
E_GC = 0.0027      # kN/mm
E_L0 = 0.0075      # mm
K_DEGRAD = 1.0e-7  # residual stiffness
TAU_RES = 1.0e-6   # kN/mm

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

def parse_c5_mesh():
    nodes = {}
    elements = {}
    with open(C5_MESH, "r", encoding="utf-8") as f:
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
                    if eid <= 4440:
                        elements[eid] = [int(p) for p in parts[1:5]]
    node_list = sorted(nodes.keys())
    node_to_idx = {nid: i for i, nid in enumerate(node_list)}
    return nodes, elements, node_list, node_to_idx

def load_c5_data():
    nodes, elements, node_list, node_to_idx = parse_c5_mesh()
    n_nodes = len(node_list)

    d_ckpt = np.zeros(n_nodes)
    with open(C5_CKPT_TABLE, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for r in reader:
            if r and r[0].strip().upper() == "NODE":
                nid = int(r[1])
                if nid in node_to_idx:
                    d_ckpt[node_to_idx[nid]] = float(r[4])

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
                if l.startswith("*"):
                    in_init = False
                    break
                parts = [p.strip() for p in l.split(",") if p.strip()]
                card_lines.append(parts)

    num_cards = len(card_lines) // 3
    for c in range(num_cards):
        l1 = card_lines[3*c]
        l2 = card_lines[3*c + 1]
        eid = int(l1[0])
        if 1 <= eid <= 4440:
            h_vals = [float(l2[1]), float(l2[2]), float(l2[3]), float(l2[4])]
            elem_H[eid] = h_vals

    return nodes, elements, node_list, node_to_idx, d_ckpt, d_H1, elem_H

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

    # Reaction forces
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

def simulate_continuation(lower_bound_mode="d_H1"):
    print("\n" + "="*75)
    print(f"   FORWARD CONTINUATION SIMULATION: BOUND MODE = {lower_bound_mode}   ")
    print("="*75)

    nodes, elements, node_list, node_to_idx, d_ckpt, d_H1, elem_H = load_c5_data()
    n_nodes = len(node_list)
    C0, lam, mu = compute_plane_strain_c0()

    u_start = 0.002052
    u_target = 0.002056

    if lower_bound_mode == "d_H1":
        d_lower = np.copy(d_H1)
        d_curr = np.copy(d_H1)
    elif lower_bound_mode == "d_ckpt":
        d_lower = np.copy(d_ckpt)
        d_curr = np.copy(d_H1)
    else:
        raise ValueError(f"Unknown mode {lower_bound_mode}")

    bounds = [(float(d_lower[i]), 1.0) for i in range(n_nodes)]
    elem_H_curr = {eid: list(elem_H[eid]) for eid in elements}

    # Evaluate at u_start
    u_init, rf2_init = solve_elasticity_uel(nodes, elements, node_list, node_to_idx, d_curr, u_start)
    ef_init, ee_init = compute_energies_uel(nodes, elements, node_list, node_to_idx, u_init, d_curr)
    print(f"Initial state at u={u_start:.6f} mm: RF2 = {rf2_init:.4f} N, E_frac = {ef_init:.6f} mJ, E_elas = {ee_init:.6f} mJ")

    # Step to u_target (+4 nm)
    print(f"\nAdvancing load to u={u_target:.6f} mm (+4 nm)...")
    tol_stagger = 1.0e-5
    max_stagger_iters = 15

    for s_iter in range(1, max_stagger_iters + 1):
        # 1. Solve elasticity at u_target
        u_step, rf2_step_N = solve_elasticity_uel(nodes, elements, node_list, node_to_idx, d_curr, u_target)

        # 2. Update GP history matching UEL exact formula
        max_delta_H = 0.0
        for eid, conn in elements.items():
            elem_indices = [node_to_idx[n] for n in conn]
            xe = np.array([nodes[n] for n in conn])
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
                if diff_h > max_delta_H:
                    max_delta_H = diff_h
                elem_H_curr[eid][kpt] = new_h

        # 3. Assemble AT2 system with updated history
        K_d_new, F_d_new = assemble_at2_system(nodes, elements, node_to_idx, elem_H_curr)

        # 4. Solve bound-constrained phase field subproblem
        def obj_step(d):
            Kd = K_d_new.dot(d)
            return 0.5 * np.dot(d, Kd) - np.dot(F_d_new, d), Kd - F_d_new

        res_step = minimize(obj_step, np.copy(d_curr), jac=True, method='L-BFGS-B', bounds=bounds,
                            options={'ftol': 1e-15, 'gtol': 1e-8, 'maxiter': 500})
        d_next = res_step.x
        diff_d = float(np.max(np.abs(d_next - d_curr)))
        d_curr = d_next

        print(f"  [Stagger {s_iter:02d}] RF2 = {rf2_step_N:.4f} N | max(|Delta d|) = {diff_d:.2e} | max(Delta H) = {max_delta_H:.2e}")

        if diff_d < tol_stagger:
            print(f"  --> Staggered coupling CONVERGED in {s_iter} iterations!")
            break

    ef_final, ee_final = compute_energies_uel(nodes, elements, node_list, node_to_idx, u_step, d_curr)
    print(f"\nFinal state at u={u_target:.6f} mm:")
    print(f"  RF2:     {rf2_step_N:.4f} N (Delta = {rf2_step_N - rf2_init:+.4f} N)")
    print(f"  E_frac:  {ef_final:.6f} mJ (Delta = {ef_final - ef_init:+.6f} mJ)")
    print(f"  E_elas:  {ee_final:.6f} mJ (Delta = {ee_final - ee_init:+.6f} mJ)")
    print(f"  E_total: {ef_final + ee_final:.6f} mJ (Delta = {(ef_final + ee_final) - (ef_init + ee_init):+.6f} mJ)")
    print(f"  max(d - d_lower): {float(np.max(d_curr - d_lower)):.6e}")
    print(f"  min(d - d_lower): {float(np.min(d_curr - d_lower)):.6e}")

    return {
        "mode": lower_bound_mode,
        "converged": bool(diff_d < tol_stagger),
        "iterations": s_iter,
        "rf2_init_N": rf2_init,
        "rf2_final_N": rf2_step_N,
        "delta_rf2_N": rf2_step_N - rf2_init,
        "e_frac_final_mJ": ef_final,
        "delta_e_frac_mJ": ef_final - ef_init,
        "max_advance": float(np.max(d_curr - d_lower))
    }

def main():
    res_A = simulate_continuation("d_ckpt")
    res_B = simulate_continuation("d_H1")

    print("\n" + "="*75)
    print("   COMPARISON OF CONTINUATION HYPOTHESES   ")
    print("="*75)
    print(f"Hypothesis A (d >= d_ckpt): Converged={res_A['converged']} in {res_A['iterations']} iters | RF2: {res_A['rf2_init_N']:.2f} -> {res_A['rf2_final_N']:.2f} N (Delta: {res_A['delta_rf2_N']:+.2f} N)")
    print(f"Hypothesis B (d >= d_H1):   Converged={res_B['converged']} in {res_B['iterations']} iters | RF2: {res_B['rf2_init_N']:.2f} -> {res_B['rf2_final_N']:.2f} N (Delta: {res_B['delta_rf2_N']:+.2f} N)")

if __name__ == "__main__":
    main()

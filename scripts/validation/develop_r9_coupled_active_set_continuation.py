#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
develop_r9_coupled_active_set_continuation.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER (Turn 137)
Protocol Version: 2

Develops, analytically derives, and numerically verifies the Candidate R9 coupled
active-set Newton solver for C3 continuation:
1. Exact consistent formulation of coupled residual R(u, d) = [R_u, R_d].
2. Four consistent analytical Jacobian blocks: K_uu, K_ud, K_du, K_dd.
3. Finite-difference validation of each Jacobian block (Frobenius norm error < 1e-5).
4. Rigorous history maximum switching test (psi+ <= H_n vs psi+ > H_n).
5. Coupled active-set Newton solution for the +1 nm continuation increment.
6. Parity evaluation against Turn 107 benchmark reference.
"""

import sys
import os
import json
import hashlib
from pathlib import Path
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
import pandas as pd

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
sys.path.append(str(REPO_ROOT / "scripts/validation"))

from evaluate_corrected_c3_coupled_transfer_and_increment import (
    C3_MESH_INP, parse_mesh, compute_plane_strain_c0, shape_functions,
    UEL_GP_COORDS, UEL_WEIGHTS, K_DEGRAD, uel_driving_energy,
    compute_energies_uel, E_MOD, NU, E_GC, E_L0, TAU_RES_D, TAU_RES_U
)

def compute_positive_stress_and_derivatives(eps, lam, mu):
    """
    Computes undegraded positive strain energy psi+, positive stress sigma0+,
    and tangent C_pos = d(sigma0+)/d(eps).
    eps = [eps11, eps22, gamma12]
    """
    e11 = eps[0]
    e22 = eps[1]
    e12 = 0.5 * eps[2]
    tr_e = e11 + e22
    e_pos = max(0.0, tr_e)
    
    pos_m = 0.5 * lam * (e_pos**2) + mu * (e11**2 + e22**2 + 2.0 * (e12**2))
    
    # Positive stress vector [sigma11+, sigma22+, tau12+]
    if tr_e > 0.0:
        s11 = lam * tr_e + 2.0 * mu * e11
        s22 = lam * tr_e + 2.0 * mu * e22
        s12 = mu * eps[2] # mu * gamma12
    else:
        s11 = 2.0 * mu * e11
        s22 = 2.0 * mu * e22
        s12 = mu * eps[2]
        
    sigma0_pos = np.array([s11, s22, s12])
    return float(pos_m), sigma0_pos

def eval_element_coupled_system(xe, ue, de, H_base, lam, mu, C0):
    """
    Evaluates element residual vectors and local Jacobian matrices:
    R_u (8), R_d (4)
    K_uu (8x8), K_ud (8x4), K_du (4x8), K_dd (4x4)
    """
    d_avg = float(np.mean(de))
    deg = (1.0 - d_avg)**2 + K_DEGRAD
    g_prime = -2.0 * (1.0 - d_avg)
    
    c_mech = C0 * deg
    
    Ru = np.zeros(8)
    Rd = np.zeros(4)
    
    Kuu = np.zeros((8, 8))
    Kud = np.zeros((8, 4))
    Kdu = np.zeros((4, 8))
    Kdd = np.zeros((4, 4))
    
    K0_elem = np.zeros((8, 8))
    elem_H = []
    
    for kpt in range(4):
        xi, eta = UEL_GP_COORDS[kpt]
        wt = UEL_WEIGHTS[kpt]
        N, dNdxi, dNdeta = shape_functions(xi, eta)
        
        J_mat = np.zeros((2, 2))
        for a in range(4):
            J_mat[0, 0] += dNdxi[a] * xe[a, 0]
            J_mat[0, 1] += dNdxi[a] * xe[a, 1]
            J_mat[1, 0] += dNdeta[a] * xe[a, 0]
            J_mat[1, 1] += dNdeta[a] * xe[a, 1]
            
        detJ = J_mat[0, 0] * J_mat[1, 1] - J_mat[0, 1] * J_mat[1, 0]
        cj = detJ * wt
        invJ = np.array([[ J_mat[1, 1], -J_mat[0, 1]], [-J_mat[1, 0],  J_mat[0, 0]]]) / detJ
        
        dNdx = np.zeros((2, 4))
        for a in range(4):
            dNdx[0, a] = invJ[0, 0] * dNdxi[a] + invJ[0, 1] * dNdeta[a]
            dNdx[1, a] = invJ[1, 0] * dNdxi[a] + invJ[1, 1] * dNdeta[a]
            
        B = np.zeros((3, 8))
        for a in range(4):
            B[0, 2*a]   = dNdx[0, a]
            B[1, 2*a+1] = dNdx[1, a]
            B[2, 2*a]   = dNdx[1, a]
            B[2, 2*a+1] = dNdx[0, a]
            
        b_d = dNdx # 2x4
        
        eps = B.dot(ue)
        pos_m, sigma0_pos = compute_positive_stress_and_derivatives(eps, lam, mu)
        
        H_n_k = H_base[kpt]
        H_trial_k = max(H_n_k, pos_m)
        elem_H.append(H_trial_k)
        
        d_val = float(N.dot(de))
        
        # Mechanical residual & Kuu
        sigma = c_mech.dot(eps)
        Ru += cj * B.T.dot(sigma)
        
        K0_elem += cj * B.T.dot(C0).dot(B)
        Kuu += cj * B.T.dot(c_mech).dot(B)
        
        # Phase residual & Kdd
        grad_d = b_d.dot(de)
        Rd += cj * (
            E_GC * E_L0 * b_d.T.dot(grad_d) +
            (E_GC / E_L0) * d_val * N +
            2.0 * H_trial_k * (d_val - 1.0) * N
        )
        
        for a in range(4):
            for b in range(4):
                bdb = b_d[0, a] * b_d[0, b] + b_d[1, a] * b_d[1, b]
                Kdd[a, b] += cj * (
                    E_GC * E_L0 * bdb +
                    (E_GC / E_L0 + 2.0 * H_trial_k) * N[a] * N[b]
                )
                
        # Phase-displacement cross-coupling Kdu = d(Rd)/d(u)
        # d(Rd)/d(H_k) = 2.0 * cj * (d_val - 1.0) * N
        # d(H_k)/d(u) = sigma0_pos.T.dot(B) if pos_m > H_n_k else 0
        if pos_m > H_n_k:
            dH_du = sigma0_pos.dot(B) # 1x8
            dRd_dH = 2.0 * cj * (d_val - 1.0) * N # 4-vector
            Kdu += np.outer(dRd_dH, dH_du) # 4x8
            
    # Displacement-phase cross-coupling Kud = d(Ru)/d(d)
    # Ru = g(d_avg) * K0_elem * ue
    # d(Ru)/d(d_a) = g_prime * (1/4) * (K0_elem * ue)
    f0 = K0_elem.dot(ue) # 8-vector
    for a in range(4):
        Kud[:, a] = 0.25 * g_prime * f0
        
    return Ru, Rd, Kuu, Kud, Kdu, Kdd, elem_H

def verify_element_jacobians():
    """
    Independent finite-difference test on element Jacobian blocks.
    """
    print("\n--- Finite-Difference Verification of Local Element Jacobian Blocks ---")
    C0, lam, mu = compute_plane_strain_c0()
    xe = np.array([[0.0, 0.0], [0.002, 0.0], [0.002, 0.002], [0.0, 0.002]])
    ue = np.array([0.0, 0.0, 2e-5, 1e-6, 2.5e-5, 1.2e-5, 0.0, 1.0e-5])
    de = np.array([0.45, 0.55, 0.65, 0.50])
    
    # Case 1: Active crack propagation (pos_m > H_n)
    H_low = [0.001, 0.001, 0.001, 0.001]
    Ru0, Rd0, Kuu, Kud, Kdu, Kdd, _ = eval_element_coupled_system(xe, ue, de, H_low, lam, mu, C0)
    
    eps_fd = 1e-7
    # 1. Kuu FD
    Kuu_fd = np.zeros((8, 8))
    for j in range(8):
        u_p = np.copy(ue); u_p[j] += eps_fd
        u_m = np.copy(ue); u_m[j] -= eps_fd
        rp, _, _, _, _, _, _ = eval_element_coupled_system(xe, u_p, de, H_low, lam, mu, C0)
        rm, _, _, _, _, _, _ = eval_element_coupled_system(xe, u_m, de, H_low, lam, mu, C0)
        Kuu_fd[:, j] = (rp - rm) / (2.0 * eps_fd)
    err_Kuu = np.linalg.norm(Kuu - Kuu_fd) / np.linalg.norm(Kuu_fd)
    
    # 2. Kud FD
    Kud_fd = np.zeros((8, 4))
    for j in range(4):
        d_p = np.copy(de); d_p[j] += eps_fd
        d_m = np.copy(de); d_m[j] -= eps_fd
        rp, _, _, _, _, _, _ = eval_element_coupled_system(xe, ue, d_p, H_low, lam, mu, C0)
        rm, _, _, _, _, _, _ = eval_element_coupled_system(xe, ue, d_m, H_low, lam, mu, C0)
        Kud_fd[:, j] = (rp - rm) / (2.0 * eps_fd)
    err_Kud = np.linalg.norm(Kud - Kud_fd) / np.linalg.norm(Kud_fd)
    
    # 3. Kdd FD
    Kdd_fd = np.zeros((4, 4))
    for j in range(4):
        d_p = np.copy(de); d_p[j] += eps_fd
        d_m = np.copy(de); d_m[j] -= eps_fd
        _, rp, _, _, _, _, _ = eval_element_coupled_system(xe, ue, d_p, H_low, lam, mu, C0)
        _, rm, _, _, _, _, _ = eval_element_coupled_system(xe, ue, d_m, H_low, lam, mu, C0)
        Kdd_fd[:, j] = (rp - rm) / (2.0 * eps_fd)
    err_Kdd = np.linalg.norm(Kdd - Kdd_fd) / np.linalg.norm(Kdd_fd)
    
    # 4. Kdu FD (active history regime)
    Kdu_fd = np.zeros((4, 8))
    for j in range(8):
        u_p = np.copy(ue); u_p[j] += eps_fd
        u_m = np.copy(ue); u_m[j] -= eps_fd
        _, rp, _, _, _, _, _ = eval_element_coupled_system(xe, u_p, de, H_low, lam, mu, C0)
        _, rm, _, _, _, _, _ = eval_element_coupled_system(xe, u_m, de, H_low, lam, mu, C0)
        Kdu_fd[:, j] = (rp - rm) / (2.0 * eps_fd)
    err_Kdu = np.linalg.norm(Kdu - Kdu_fd) / np.linalg.norm(Kdu_fd)
    
    # Case 2: Inactive crack propagation (pos_m < H_n) -> Kdu must be identically zero
    H_high = [100.0, 100.0, 100.0, 100.0]
    _, _, _, _, Kdu_inactive, _, _ = eval_element_coupled_system(xe, ue, de, H_high, lam, mu, C0)
    norm_Kdu_inactive = np.linalg.norm(Kdu_inactive)
    
    print(f"Kuu FD Relative Error: {err_Kuu:.2e} (PASS: {err_Kuu < 1e-5})")
    print(f"Kud FD Relative Error: {err_Kud:.2e} (PASS: {err_Kud < 1e-5})")
    print(f"Kdd FD Relative Error: {err_Kdd:.2e} (PASS: {err_Kdd < 1e-5})")
    print(f"Kdu FD Relative Error (Active Regime):   {err_Kdu:.2e} (PASS: {err_Kdu < 1e-5})")
    print(f"Kdu Norm (Inactive Regime, H_n >> psi+): {norm_Kdu_inactive:.2e} (PASS: {norm_Kdu_inactive == 0.0})")
    
    fd_pass = (err_Kuu < 1e-5 and err_Kud < 1e-5 and err_Kdd < 1e-5 and 
               err_Kdu < 1e-5 and norm_Kdu_inactive == 0.0)
    return {
        "err_Kuu": float(err_Kuu),
        "err_Kud": float(err_Kud),
        "err_Kdd": float(err_Kdd),
        "err_Kdu_active": float(err_Kdu),
        "norm_Kdu_inactive": float(norm_Kdu_inactive),
        "fd_pass": bool(fd_pass)
    }

def assemble_global_coupled_system(nodes, elements, node_to_idx, u_nodes, d_nodes, H_accepted):
    """
    Assembles the complete global coupled residual vectors and sparse Jacobian matrices.
    """
    n_nodes = len(node_to_idx)
    n_dofs_u = 2 * n_nodes
    C0, lam, mu = compute_plane_strain_c0()
    
    R_u_global = np.zeros(n_dofs_u)
    R_d_global = np.zeros(n_nodes)
    
    I_uu, J_uu, V_uu = [], [], []
    I_ud, J_ud, V_ud = [], [], []
    I_du, J_du, V_du = [], [], []
    I_dd, J_dd, V_dd = [], [], []
    
    elem_H_trial = {}
    
    for eid, conn in elements.items():
        elem_indices = [node_to_idx[n] for n in conn]
        xe = np.array([nodes[n] for n in conn])
        ue = u_nodes[elem_indices, :].flatten()
        de = d_nodes[elem_indices]
        H_base = H_accepted[eid]
        
        Ru_e, Rd_e, Kuu_e, Kud_e, Kdu_e, Kdd_e, h_trial_e = eval_element_coupled_system(
            xe, ue, de, H_base, lam, mu, C0
        )
        elem_H_trial[eid] = h_trial_e
        
        # Assemble residuals
        u_dofs = []
        for idx in elem_indices:
            u_dofs.extend([2 * idx, 2 * idx + 1])
            
        for r in range(8):
            R_u_global[u_dofs[r]] += Ru_e[r]
            for c in range(8):
                I_uu.append(u_dofs[r])
                J_uu.append(u_dofs[c])
                V_uu.append(Kuu_e[r, c])
                
        for a in range(4):
            idx_a = elem_indices[a]
            R_d_global[idx_a] += Rd_e[a]
            for b in range(4):
                idx_b = elem_indices[b]
                I_dd.append(idx_a)
                J_dd.append(idx_b)
                V_dd.append(Kdd_e[a, b])
                
        for r in range(8):
            for c in range(4):
                I_ud.append(u_dofs[r])
                J_ud.append(elem_indices[c])
                V_ud.append(Kud_e[r, c])
                
        for r in range(4):
            for c in range(8):
                I_du.append(elem_indices[r])
                J_du.append(u_dofs[c])
                V_du.append(Kdu_e[r, c])
                
    K_uu = sp.coo_matrix((V_uu, (I_uu, J_uu)), shape=(n_dofs_u, n_dofs_u)).tocsr()
    K_ud = sp.coo_matrix((V_ud, (I_ud, J_ud)), shape=(n_dofs_u, n_nodes)).tocsr()
    K_du = sp.coo_matrix((V_du, (I_du, J_du)), shape=(n_nodes, n_dofs_u)).tocsr()
    K_dd = sp.coo_matrix((V_dd, (I_dd, J_dd)), shape=(n_nodes, n_nodes)).tocsr()
    
    return R_u_global, R_d_global, K_uu, K_ud, K_du, K_dd, elem_H_trial

def solve_coupled_continuation_r9(nodes_c3, elements_c3, nlist_c3, n2idx_c3,
                                  u_init, d_init, H_accepted, d_lower_bounds,
                                  u_top_target, max_coupled_iters=25):
    """
    Safeguarded Coupled Active-Set Newton Solver for C3 Continuation:
    Solves for coupled (u, d) satisfying:
      R_u^free(u, d) = 0
      R_d^i(u, d) = lambda_i, with lambda_i >= 0, d_i >= d0_i, lambda_i*(d_i - d0_i) = 0
    without intermediate history accumulation (H_accepted remains strictly immutable).
    """
    n_nodes = len(nlist_c3)
    n_dofs_u = 2 * n_nodes
    
    # Boundary DOFs
    y_vals = [nodes_c3[nid][1] for nid in nlist_c3]
    x_vals = [nodes_c3[nid][0] for nid in nlist_c3]
    
    fixed_dofs = {}
    for idx, (x, y) in enumerate(zip(x_vals, y_vals)):
        if abs(y - 0.0) < 1e-6:
            fixed_dofs[2 * idx + 1] = 0.0
            if abs(x - 0.0) < 1e-6:
                fixed_dofs[2 * idx] = 0.0
        elif abs(y - 0.100) < 1e-6:
            fixed_dofs[2 * idx + 1] = u_top_target
            fixed_dofs[2 * idx] = 0.0
            
    all_dofs = np.arange(n_dofs_u)
    prescribed_dofs = np.array(sorted(fixed_dofs.keys()))
    free_u_dofs = np.setdiff1d(all_dofs, prescribed_dofs)
    
    u_nodes = np.copy(u_init)
    for dof, val in fixed_dofs.items():
        node_idx = dof // 2
        comp = dof % 2
        u_nodes[node_idx, comp] = val
        
    d_nodes = np.maximum(np.copy(d_init), d_lower_bounds)
    lambda_d = np.zeros(n_nodes)
    
    print("\n--- Starting Safeguarded Coupled Active-Set Newton Iterations ---")
    iteration_history = []
    
    c_pdas = 1.0 # Complementarity penalty factor for active set discrimination
    
    for it in range(1, max_coupled_iters + 1):
        # 1. Assemble complete coupled system at current (u_nodes, d_nodes)
        R_u, R_d, K_uu, K_ud, K_du, K_dd, elem_H_trial = assemble_global_coupled_system(
            nodes_c3, elements_c3, n2idx_c3, u_nodes, d_nodes, H_accepted
        )
        
        # Free mechanical residual
        res_u_free = float(np.max(np.abs(R_u[free_u_dofs])))
        
        # Determine Primal-Dual Active Set for phase constraint d >= d0
        # Active if d + lambda <= d0 (within tolerance)
        active_phase = (d_nodes - d_lower_bounds + c_pdas * lambda_d <= 1e-8)
        inactive_phase = ~active_phase
        
        n_act = int(np.sum(active_phase))
        n_inact = int(np.sum(inactive_phase))
        
        # Free-phase residual (Euler-Lagrange residual on inactive nodes)
        res_d_inact = float(np.max(np.abs(R_d[inactive_phase]))) if n_inact > 0 else 0.0
        
        # Check active set KKT condition: lambda >= 0 on active set
        # Update Lagrange multipliers: lambda = R_d on active set, 0 on inactive set
        lambda_d_new = np.zeros(n_nodes)
        lambda_d_new[active_phase] = R_d[active_phase]
        
        kkt_violations = int(np.sum(lambda_d_new[active_phase] < -1e-6))
        
        # Reaction force at top boundary
        top_dofs = [2 * idx + 1 for idx, y in enumerate(y_vals) if abs(y - 0.100) < 1e-6]
        rf2_total = float(np.sum(R_u[top_dofs])) * 1000.0
        
        max_h_curr = max(max(h) for h in elem_H_trial.values())
        
        print(f"Iter {it:2d}: Res_u={res_u_free:.3e} kN | Res_d_free={res_d_inact:.3e} kN/mm | "
              f"ActNodes={n_act:4d} | KKT_viols={kkt_violations} | RF2={rf2_total:.3f} N | max(H)={max_h_curr:.4f} MPa")
        
        iteration_history.append({
            "iter": it,
            "res_u_free": res_u_free,
            "res_d_free": res_d_inact,
            "active_nodes": n_act,
            "inactive_nodes": n_inact,
            "kkt_violations": kkt_violations,
            "rf2_N": rf2_total,
            "max_h_MPa": max_h_curr,
            "d_max": float(np.max(d_nodes))
        })
        
        if res_u_free <= TAU_RES_U and res_d_inact <= TAU_RES_D and kkt_violations == 0:
            print(f"--> Coupled Newton-PDAS CONVERGED successfully at iteration {it}!")
            break
            
        # 2. Formulate reduced coupled linear system for inactive phase and free displacement
        # [ K_uu[ff, ff]       K_ud[ff, inact] ] [ delta_u_f ] = - [ R_u[ff] ]
        # [ K_du[inact, ff]    K_dd[inact, inact] ] [ delta_d_inact ] = - [ R_d[inact] ]
        idx_inact = np.where(inactive_phase)[0]
        idx_act = np.where(active_phase)[0]
        
        # Active phase DOFs are fixed at lower bound: delta_d_act = d0 - d
        delta_d_act = d_lower_bounds[idx_act] - d_nodes[idx_act]
        
        # Account for delta_d_act on rhs:
        rhs_u = - R_u[free_u_dofs]
        if n_act > 0:
            rhs_u -= K_ud[free_u_dofs, :][:, idx_act].dot(delta_d_act)
            
        rhs_d = - R_d[idx_inact]
        if n_act > 0:
            rhs_d -= K_dd[idx_inact, :][:, idx_act].dot(delta_d_act)
            
        K_ff = K_uu[free_u_dofs, :][:, free_u_dofs]
        K_fi = K_ud[free_u_dofs, :][:, idx_inact]
        K_if = K_du[idx_inact, :][:, free_u_dofs]
        K_ii = K_dd[idx_inact, :][:, idx_inact]
        
        # Assemble 2x2 block matrix
        K_coupled = sp.bmat([
            [K_ff, K_fi],
            [K_if, K_ii]
        ], format="csr")
        
        rhs_coupled = np.concatenate([rhs_u, rhs_d])
        
        # Solve coupled linear system
        delta_coupled = spla.spsolve(K_coupled, rhs_coupled)
        
        n_ff = len(free_u_dofs)
        delta_u_f = delta_coupled[:n_ff]
        delta_d_inact = delta_coupled[n_ff:]
        
        # 3. Safeguarded updates with admissibility projection
        alpha = 1.0 # Newton step
        
        # Update displacements
        u_nodes_flat = u_nodes.flatten()
        u_nodes_flat[free_u_dofs] += alpha * delta_u_f
        u_nodes = u_nodes_flat.reshape((n_nodes, 2))
        
        # Update phase with lower bound safeguard d >= d0 and upper bound d <= 1
        d_nodes[idx_inact] += alpha * delta_d_inact
        d_nodes[idx_act] = d_lower_bounds[idx_act]
        d_nodes = np.maximum(d_lower_bounds, np.minimum(1.0, d_nodes))
        
        # Update Lagrange multipliers
        lambda_d = lambda_d_new
        
    e_frac, e_elas = compute_energies_uel(nodes_c3, elements_c3, nlist_c3, n2idx_c3, u_nodes, d_nodes)
    
    return {
        "converged": bool(res_u_free <= TAU_RES_U and res_d_inact <= TAU_RES_D and kkt_violations == 0),
        "iterations": it,
        "iteration_history": iteration_history,
        "u_nodes": u_nodes,
        "d_nodes": d_nodes,
        "elem_H": elem_H_trial,
        "rf2_N": rf2_total,
        "e_frac_mJ": e_frac,
        "e_elas_mJ": e_elas,
        "e_total_mJ": e_frac + e_elas,
        "d_max": float(np.max(d_nodes)),
        "res_u_free": res_u_free,
        "res_d_free": res_d_inact,
        "kkt_violations": kkt_violations
    }

def main():
    print("================================================================================")
    print("CANDIDATE R9: COUPLED ACTIVE-SET NEWTON SOLVER FOR C3 CONTINUATION")
    print("================================================================================")
    
    # Step 1: Element Jacobian verification
    fd_results = verify_element_jacobians()
    
    # Step 2: Load C3 mesh and authentic Stage-A state
    nodes_c3, elements_c3, nlist_c3, n2idx_c3 = parse_mesh(C3_MESH_INP, max_phys_eid=2650)
    n_nodes = len(nlist_c3)
    
    state_file = REPO_ROOT / "models/pandey_kumar_mode1/108_r6_c3_multi_increment_continuation/r6_extracted_states.json"
    with open(state_file, "r") as f:
        abq_data = json.load(f)
        
    stage_a = abq_data["steps"]["Stage-A"]
    u_dict = stage_a["nodes_u"]
    u_stage_a = np.zeros((n_nodes, 2))
    d_stage_a = np.zeros(n_nodes)
    for nid_str, vals in u_dict.items():
        nid = int(nid_str)
        if nid in n2idx_c3:
            idx = n2idx_c3[nid]
            u_stage_a[idx, 0] = vals[0]
            u_stage_a[idx, 1] = vals[1]
            if len(vals) > 2:
                d_stage_a[idx] = vals[2]
                
    # Load transferred lower bounds (d0, H0)
    df_bounds = pd.read_csv(REPO_ROOT / "models/pandey_kumar_mode1/108_r6_c3_multi_increment_continuation/d_lower_bounds.csv", skipinitialspace=True)
    d0_dict = {}
    h0_dict = {}
    for _, row in df_bounds.iterrows():
        eid = int(row['EID'])
        d0_dict[eid] = [row['D0_1'], row['D0_2'], row['D0_3'], row['D0_4']]
        h0_dict[eid] = [row['H0_1'], row['H0_2'], row['H0_3'], row['H0_4']]
        
    d0_nodal = np.zeros(n_nodes)
    for eid, conn in elements_c3.items():
        if eid in d0_dict:
            for k in range(4):
                nid = conn[k]
                idx = n2idx_c3[nid]
                d0_nodal[idx] = max(d0_nodal[idx], d0_dict[eid][k])
                
    if np.all(d_stage_a == 0.0):
        d_stage_a = np.copy(d0_nodal)
        
    # Compute Stage-A strain energy at Gauss points
    C0, lam, mu = compute_plane_strain_c0()
    elem_H_stage_a = {}
    for eid, conn in elements_c3.items():
        elem_indices = [n2idx_c3[n] for n in conn]
        xe = np.array([nodes_c3[n] for n in conn])
        ue = u_stage_a[elem_indices, :].flatten()
        elem_H_stage_a[eid] = []
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
            elem_H_stage_a[eid].append(pos_m)
            
    H_accepted = {}
    for eid in elements_c3:
        h0 = h0_dict.get(eid, [0.0]*4)
        h_st = elem_H_stage_a[eid]
        H_accepted[eid] = [max(h0[k], h_st[k]) for k in range(4)]
        
    max_H_stage_a = max(max(h) for h in H_accepted.values())
    print(f"\nLoaded Stage-A state: max(d)={np.max(d_stage_a):.6f}, max(H)={max_H_stage_a:.4f} MPa")
    
    # Step 3: Solve the +1 nm continuation increment
    u_top_target = 0.00196510735 + 1.0e-6 # 0.00196610735 mm
    print(f"Target displacement: u_top = {u_top_target*1e3:.7f} um (+1 nm)")
    
    sol = solve_coupled_continuation_r9(
        nodes_c3, elements_c3, nlist_c3, n2idx_c3,
        u_stage_a, d_stage_a, H_accepted, d_stage_a,
        u_top_target, max_coupled_iters=25
    )
    
    # Step 4: Parity and physical criteria evaluation
    diff_d = sol["d_nodes"] - d_stage_a
    min_healing = float(np.min(diff_d))
    delta_d_max = float(np.max(diff_d))
    
    mech_pass = sol["res_u_free"] <= TAU_RES_U
    phase_pass = sol["res_d_free"] <= TAU_RES_D
    kkt_pass = sol["kkt_violations"] == 0
    healing_pass = min_healing >= -1e-8
    
    max_H_committed = max(max(h) for h in sol["elem_H"].values())
    
    # Step 5: Evaluate Turn 107 formulation at the identical +1 nm displacement
    print("\n--- Evaluating Turn 107 Formulation at Matched +1 nm Displacement ---")
    from evaluate_corrected_c3_coupled_transfer_and_increment import solve_coupled_staggered
    sol_t107 = solve_coupled_staggered(
        nodes=nodes_c3, elements=elements_c3, node_list=nlist_c3, node_to_idx=n2idx_c3,
        d_init=d_stage_a, d_lower_bounds=d_stage_a, elem_H_base=H_accepted,
        u_top=u_top_target, tol_stagger=1e-5, max_iters=25, update_H=True
    )
    
    diff_rf2_N = float(sol["rf2_N"] - sol_t107["rf2_N"])
    diff_ef_mJ = float(sol["e_frac_mJ"] - sol_t107["e_frac_mJ"])
    diff_dmax = float(sol["d_max"] - sol_t107["d_max"])
    
    print("\n=== FINAL CANDIDATE R9 EVALUATION ===")
    print(f"Converged:               {sol['converged']} (in {sol['iterations']} iterations)")
    print(f"Mechanical Residual:     {sol['res_u_free']:.3e} kN (PASS: {mech_pass})")
    print(f"Free-Phase Residual:     {sol['res_d_free']:.3e} kN/mm (PASS: {phase_pass})")
    print(f"Active Set KKT Violations:{sol['kkt_violations']} (PASS: {kkt_pass})")
    print(f"Damage Healing Check:    min(Delta d) = {min_healing:.3e} (PASS: {healing_pass})")
    print(f"Crack Tip Advance:       max(Delta d) = {delta_d_max:.6f}")
    print(f"Reaction Force RF2:      {sol['rf2_N']:.4f} N (Turn 107 matched: {sol_t107['rf2_N']:.4f} N, diff = {diff_rf2_N:.4f} N)")
    print(f"Fracture Energy E_frac:  {sol['e_frac_mJ']:.6f} mJ (Turn 107 matched: {sol_t107['e_frac_mJ']:.6f} mJ, diff = {diff_ef_mJ:.6f} mJ)")
    print(f"Elastic Energy E_elas:   {sol['e_elas_mJ']:.6f} mJ (Turn 107 matched: {sol_t107['e_elas_mJ']:.6f} mJ)")
    print(f"Committed Max History:   {max_H_committed:.4f} MPa (vs Stage-A {max_H_stage_a:.4f} MPa)")
    
    out_dict = {
        "schema": 1,
        "task": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
        "turn": 137,
        "objective": "FORMULATE_AND_VERIFY_R9_COUPLED_ACTIVE_SET_NEWTON_OPERATOR",
        "finite_difference_verification": fd_results,
        "stage_a_baseline": {
            "u_top_mm": 0.00196510735,
            "d_max": float(np.max(d_stage_a)),
            "max_h_MPa": float(max_H_stage_a)
        },
        "continuation_increment": {
            "u_top_target_mm": float(u_top_target),
            "delta_u_mm": 1.0e-6
        },
        "candidate_r9_solution": {
            "converged": bool(sol["converged"]),
            "iterations": int(sol["iterations"]),
            "rf2_N": float(sol["rf2_N"]),
            "e_frac_mJ": float(sol["e_frac_mJ"]),
            "e_elas_mJ": float(sol["e_elas_mJ"]),
            "e_total_mJ": float(sol["e_total_mJ"]),
            "d_max": float(sol["d_max"]),
            "delta_d_max": float(delta_d_max),
            "min_healing": float(min_healing),
            "res_u_free_kN": float(sol["res_u_free"]),
            "res_d_free_kN_mm": float(sol["res_d_free"]),
            "kkt_violations": int(sol["kkt_violations"]),
            "max_h_committed_MPa": float(max_H_committed),
            "iteration_history": sol["iteration_history"]
        },
        "displacement_matched_turn107_reference": {
            "rf2_N": float(sol_t107["rf2_N"]),
            "e_frac_mJ": float(sol_t107["e_frac_mJ"]),
            "e_elas_mJ": float(sol_t107["e_elas_mJ"]),
            "d_max": float(sol_t107["d_max"]),
            "diff_rf2_N": float(diff_rf2_N),
            "diff_ef_mJ": float(diff_ef_mJ),
            "diff_dmax": float(diff_dmax)
        },
        "acceptance_gates": {
            "fd_jacobian_pass": bool(fd_results["fd_pass"]),
            "mechanical_residual_pass": bool(mech_pass),
            "free_phase_residual_pass": bool(phase_pass),
            "kkt_complementarity_pass": bool(kkt_pass),
            "healing_pass": bool(healing_pass),
            "history_ratcheting_eliminated": bool(max_H_committed < 6.0),
            "overall_mathematically_qualified": bool(
                fd_results["fd_pass"] and mech_pass and phase_pass and kkt_pass and healing_pass and (max_H_committed < 6.0)
            )
        }
    }
    
    out_path = REPO_ROOT / "results/validation/mode1_f1597/r9_coupled_active_set_evaluation.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as fp:
        json.dump(out_dict, fp, indent=2)
        
    print(f"\nSaved verified research artifact to: {out_path}")
    
if __name__ == "__main__":
    main()

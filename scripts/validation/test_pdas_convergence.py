#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_pdas_convergence.py
Detailed convergence analysis of the Primal-Dual Active-Set (PDAS) iteration
for different continuation increment sizes (Delta u = 1 nm, 2 nm, 4 nm)
and iteration caps (k_max = 15, 25, 35).
"""

import sys
import os
import math
import json
from pathlib import Path
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

from pdas_increment_controller import (
    load_donor_c4, load_receiver_c5, compute_h1_transfer,
    assemble_phase_system, TAU_RES, TAU_FEAS, CHECKPOINT_U
)

def run_pdas_for_step(nodes, elems, elem_h, node_list, node_to_idx, d_ckpt, delta_u_nm, max_iter=30):
    delta_u_mm = delta_u_nm * 1e-6
    cont_u = CHECKPOINT_U + delta_u_mm
    scale_h = (cont_u / CHECKPOINT_U)**2

    n_nodes = len(node_list)
    K_cont, F_cont = assemble_phase_system(nodes, elems, elem_h, node_list, node_to_idx, scale_h=scale_h)

    # Initialize sets
    d_k = np.copy(d_ckpt)
    U_k = (d_k >= 1.0 - TAU_FEAS)
    L_k = (d_k < 1.0 - TAU_FEAS)
    A_k = np.zeros(n_nodes, dtype=bool)

    converged = False
    history = []

    for it in range(1, max_iter + 1):
        idx_A = np.where(A_k)[0]
        idx_L = np.where(L_k)[0]
        idx_U = np.where(U_k)[0]
        idx_fixed = np.where(~A_k)[0]

        d_k[idx_L] = d_ckpt[idx_L]
        d_k[idx_U] = 1.00000000

        if len(idx_A) > 0:
            K_AA = K_cont[idx_A, :][:, idx_A]
            K_Af = K_cont[idx_A, :][:, idx_fixed]
            F_A = F_cont[idx_A] - K_Af.dot(d_k[idx_fixed])
            d_A_new = spla.spsolve(K_AA, F_A)
            d_k[idx_A] = d_A_new

        R_current = F_cont - K_cont.dot(d_k)

        violate_lower_A = (A_k & (d_k < d_ckpt - TAU_FEAS))
        violate_upper_A = (A_k & (d_k > 1.0 + TAU_FEAS))
        release_L = (L_k & (R_current > TAU_RES) & (d_ckpt < 1.0 - TAU_FEAS))
        release_U = (U_k & (R_current < -TAU_RES))

        n_changes = int(np.sum(violate_lower_A) + np.sum(violate_upper_A) + np.sum(release_L) + np.sum(release_U))
        res_A = float(np.max(np.abs(R_current[A_k]))) if len(idx_A) > 0 else 0.0

        history.append({
            "iter": it, "U": int(len(idx_U)), "L": int(len(idx_L)), "A": int(len(idx_A)),
            "delta_N": n_changes, "res_A": res_A
        })

        if n_changes == 0 and res_A <= TAU_RES:
            converged = True
            break

        U_k = (U_k & (~release_U)) | violate_upper_A
        L_k = (L_k & (~release_L)) | violate_lower_A
        A_k = (~U_k) & (~L_k)

    # Post-checks
    delta_d = d_k - d_ckpt
    n_healing_strict = int(np.sum(delta_d < 0.0))
    n_healing_tol = int(np.sum(delta_d < -TAU_FEAS))
    n_overshoot_strict = int(np.sum(d_k > 1.0))
    n_overshoot_tol = int(np.sum(d_k > 1.0 + TAU_FEAS))

    R_final = F_cont - K_cont.dot(d_k)
    res_A_final = float(np.max(np.abs(R_final[A_k]))) if np.sum(A_k) > 0 else 0.0
    kkt_L_valid = bool(np.all(R_final[L_k] <= TAU_RES))
    kkt_U_valid = bool(np.all(R_final[U_k] >= -TAU_RES))

    return {
        "delta_u_nm": delta_u_nm,
        "converged": converged,
        "iterations": len(history),
        "history": history,
        "healing_strict": n_healing_strict,
        "healing_tol": n_healing_tol,
        "overshoot_strict": n_overshoot_strict,
        "overshoot_tol": n_overshoot_tol,
        "res_A_final": res_A_final,
        "kkt_L_valid": kkt_L_valid,
        "kkt_U_valid": kkt_U_valid,
        "final_set_sizes": {"U": int(np.sum(U_k)), "L": int(np.sum(L_k)), "A": int(np.sum(A_k))}
    }

def main():
    print("=" * 80)
    print("PARAMETRIC PDAS CONVERGENCE STUDY (Turn 69)")
    print("=" * 80)

    donor = load_donor_c4()
    receiver = load_receiver_c5()

    node_list, node_to_idx, d_ckpt, u1, u2, elem_h = compute_h1_transfer(donor, receiver)
    r_nodes = receiver["nodes"]
    r_elems = receiver["elements"]

    for du in [1.0, 2.0, 4.0]:
        print(f"\nEvaluating Delta u = {du} nm...")
        res = run_pdas_for_step(r_nodes, r_elems, elem_h, node_list, node_to_idx, d_ckpt, du, max_iter=30)
        print(f"  Converged: {res['converged']} in {res['iterations']} iterations")
        print(f"  Final Set Sizes: {res['final_set_sizes']}")
        print(f"  Strict Healing: {res['healing_strict']} nodes, Tol Healing: {res['healing_tol']} nodes")
        print(f"  Strict Overshoot: {res['overshoot_strict']} nodes, Tol Overshoot: {res['overshoot_tol']} nodes")
        print(f"  Max Residual on A: {res['res_A_final']:.6e} kN/mm")
        print(f"  KKT L Valid: {res['kkt_L_valid']}, KKT U Valid: {res['kkt_U_valid']}")
        for h in res["history"][-5:]:
            print(f"    iter {h['iter']:2d}: |A|={h['A']:4d}, delta_N={h['delta_N']:3d}, res_A={h['res_A']:.2e}")

if __name__ == "__main__":
    main()

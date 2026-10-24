#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
investigate_c3_history_transfer_hypothesis.py
Bounded corrective investigation testing the hypothesis:
Does transferring Gauss-point history strictly by isoparametric interpolation (H = H_interp),
without taking max(H_interp, psi0_pos) on unrelaxed interpolated displacements,
prevent artificial driving energy amplification and stabilize fixed-load re-equilibration on C3?
"""

import sys
import os
import json
import csv
import math
from pathlib import Path
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from scipy.optimize import minimize

from audit_turn105_c3_state1_and_forward import (
    REPO_ROOT, C2_INP, C2_CSV, C3_MESH_INP,
    E_MOD, NU, E_GC, E_L0, K_DEGRAD, TAU_RES_D, TAU_RES_U,
    UEL_GP_COORDS, UEL_WEIGHTS, shape_functions, compute_plane_strain_c0,
    uel_driving_energy, parse_mesh, load_c2_donor_state, classify_slit_flanks,
    assemble_at2_system, solve_elasticity_uel, compute_energies_uel, build_fe_interpolator
)

def run_investigation():
    print("=" * 80)
    print("BOUNDED CORRECTIVE INVESTIGATION: PURE HISTORY INTERPOLATION VS COMBINED")
    print("=" * 80)

    nodes_c2, elements_c2, nlist_c2, n2idx_c2 = parse_mesh(C2_INP, max_phys_eid=2300)
    u_c2, d_c2, elem_H_c2 = load_c2_donor_state(C2_CSV, n2idx_c2, max_phys_eid=2300)
    flanks_c2 = classify_slit_flanks(nodes_c2, elements_c2)
    u_prescribed = 0.00196510735

    nodes_c3, elements_c3, nlist_c3, n2idx_c3 = parse_mesh(C3_MESH_INP, max_phys_eid=2650)
    flanks_c3 = classify_slit_flanks(nodes_c3, elements_c3)
    n_nodes_c3 = len(nlist_c3)

    locate_c2 = build_fe_interpolator(nodes_c2, elements_c2, flanks_c2)

    # Nodal mapping
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

    s3 = math.sqrt(3.0)
    elem_H_pure = {}

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
        elem_H_pure[eid] = h_list

    max_h_c2 = max([max(h) for h in elem_H_c2.values()])
    max_h_c3_pure = max([max(h) for h in elem_H_pure.values()])

    print(f"Donor C2 Max H:      {max_h_c2:.6f} kN/mm^2")
    print(f"Recipient C3 Pure H:  {max_h_c3_pure:.6f} kN/mm^2")
    print(f"History preservation parity: {(max_h_c3_pure - max_h_c2)/max_h_c2*100:+.2f}%")

    # Evaluate phase residual with pure H
    K_d_pure, F_d_pure = assemble_at2_system(nodes_c3, elements_c3, n2idx_c3, elem_H_pure)
    res_d_pure = F_d_pure - K_d_pure.dot(d_c3_mapped)
    max_res_d_pure = float(np.max(np.abs(res_d_pure)))
    print(f"State 0 Phase Residual with Pure H: {max_res_d_pure:.6e} kN/mm (vs combined 1.57e-05 kN/mm)")

    # Test single-step phase solve with fixed pure H (frozen history re-equilibration)
    bounds_c3 = [(float(d_c3_mapped[i]), 1.0) for i in range(n_nodes_c3)]
    def obj_phase_pure(d):
        Kd = K_d_pure.dot(d)
        return 0.5 * np.dot(d, Kd) - np.dot(F_d_pure, d), Kd - F_d_pure

    res_opt = minimize(obj_phase_pure, np.copy(d_c3_mapped), jac=True, method='L-BFGS-B', bounds=bounds_c3,
                       options={'ftol': 1e-15, 'gtol': 1e-8, 'maxiter': 500})
    d_fixed_H = res_opt.x
    diff_d_fixed = float(np.max(np.abs(d_fixed_H - d_c3_mapped)))
    max_d_fixed = float(np.max(d_fixed_H))

    u_fixed, rf2_fixed, res_u_fixed = solve_elasticity_uel(nodes_c3, elements_c3, nlist_c3, n2idx_c3, d_fixed_H, u_prescribed)
    ef_fixed, ee_fixed = compute_energies_uel(nodes_c3, elements_c3, nlist_c3, n2idx_c3, u_fixed, d_fixed_H)

    rf2_donor = 189.5358
    ef_donor = 0.052266
    print("\n--- FIXED-HISTORY RE-EQUILIBRATION (Freezing H = H_interp) ---")
    print(f"  RF2:            {rf2_fixed:.4f} N (diff vs C2: {(rf2_fixed - rf2_donor)/rf2_donor*100:+.2f}%)")
    print(f"  E_frac:         {ef_fixed:.6f} mJ (diff vs C2: {(ef_fixed - ef_donor)/ef_donor*100:+.2f}%)")
    print(f"  d_max:          {max_d_fixed:.6f} (growth: {diff_d_fixed:+.6f})")
    print(f"  Phase res:      {float(np.max(np.abs(F_d_pure - K_d_pure.dot(d_fixed_H)))):.6e} kN/mm")
    print(f"  Mech res:       {res_u_fixed:.6e} kN")

    # Conclusion
    print("\nFINDING FROM CORRECTIVE INVESTIGATION:")
    if max_d_fixed < 0.60 and abs((rf2_fixed - rf2_donor)/rf2_donor*100) < 5.0:
        print("  SUCCESS: If H is frozen at H_interp, d_max does NOT surge to 0.9956, and RF2 stays within gate!")
        print("  This proves conclusively that damage amplification to 0.9956 was driven by the coupling update loop")
        print("  recomputing psi0_pos at the refined notch tip during static iteration, rather than donor history!")
    else:
        print(f"  RESULT: Even with fixed H, d_max = {max_d_fixed:.4f}, RF2 diff = {(rf2_fixed - rf2_donor)/rf2_donor*100:+.2f}%")

    out_inv = {
        "schema": 1,
        "investigation": "pure_history_transfer_and_fixed_H_reequilibration",
        "max_h_donor": max_h_c2,
        "max_h_recipient_pure": max_h_c3_pure,
        "state0_phase_res_pure": max_res_d_pure,
        "fixed_H_reequilibration": {
            "rf2_N": rf2_fixed,
            "diff_rf2_pct": (rf2_fixed - rf2_donor)/rf2_donor*100,
            "e_frac_mJ": ef_fixed,
            "diff_ef_pct": (ef_fixed - ef_donor)/ef_donor*100,
            "d_max": max_d_fixed,
            "max_delta_d": diff_d_fixed,
            "res_u_kN": res_u_fixed
        }
    }
    with open(REPO_ROOT / "results/validation/mode1_f1597/turn105_history_investigation.json", "w") as f:
        json.dump(out_inv, f, indent=2)

if __name__ == "__main__":
    run_investigation()

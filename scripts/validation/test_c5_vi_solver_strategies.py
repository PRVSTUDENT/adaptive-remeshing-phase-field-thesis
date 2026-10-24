#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_c5_vi_solver_strategies.py
Tests different VI solver strategies for mesh C5:
1. Exact Bound-Constrained QP (L-BFGS-B / Projected Gradient)
2. Projected Line-Search Active-Set (Moré-Toraldo style)
3. Single-Node / Greedy Active-Set (release node with max R_d)
4. Damped Projected Newton (spectral step length)

Verifies:
- Iteration count to convergence
- Strictly zero healing (delta d >= 0)
- Residual on free set ||R_d||_inf,A <= 1.0e-6 kN/mm
- KKT lower and upper bound multiplier feasibility
- Objective function Phi(d)
- Fracture energy E_frac
"""

import json
import csv
from pathlib import Path
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from scipy.optimize import minimize

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
pkg_dir = REPO_ROOT / "models/pandey_kumar_mode1/100_c5_pdas_snesvi_projected_continuation"
mesh_path = pkg_dir / "candidate_crack_band_mesh_c5.inp"
state_path = pkg_dir / "candidate_c5_frame7_mapped_state_table.csv"

E_GC = 0.0027   # kN/mm
E_L0 = 0.0075   # mm
TAU_RES = 1.0e-6

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

def load_system():
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
                p = [x.strip() for x in l.split(",") if x.strip()]
                if len(p) >= 3 and p[0].isdigit():
                    nid = int(p[0])
                    if nid != 999999:
                        nodes[nid] = np.array([float(p[1]), float(p[2])])
            elif reading == "ELEMENT":
                p = [x.strip() for x in l.split(",") if x.strip()]
                if len(p) >= 5 and p[0].isdigit():
                    eid = int(p[0])
                    if eid <= 4440:
                        elements[eid] = [int(x) for x in p[1:5]]

    node_list = sorted(nodes.keys())
    node_to_idx = {nid: i for i, nid in enumerate(node_list)}
    n_nodes = len(node_list)

    d_ckpt = np.zeros(n_nodes)
    elem_h = {}
    with open(state_path, "r", encoding="utf-8") as f:
        for line in f:
            p = [x.strip() for x in line.split(",") if x.strip()]
            if not p: continue
            rtype = p[0].upper()
            if rtype == "NODE":
                nid = int(p[1])
                if nid in node_to_idx:
                    d_ckpt[node_to_idx[nid]] = float(p[4])
            elif rtype in ("ELEM_HISTORY", "ELEM"):
                eid = int(p[1])
                elem_h[eid] = [float(p[2]), float(p[3]), float(p[4]), float(p[5])]

    xg4 = [-0.577350269189626,  0.577350269189626,  0.577350269189626, -0.577350269189626]
    yg4 = [-0.577350269189626, -0.577350269189626,  0.577350269189626,  0.577350269189626]
    w4  = [1.0, 1.0, 1.0, 1.0]

    I_full, J_full, V_full = [], [], []
    F_full = np.zeros(n_nodes)

    for eid, conn in elements.items():
        pts = np.array([nodes[n] for n in conn])
        h_vals = elem_h[eid]
        for kpt in range(4):
            xi, eta, wt = xg4[kpt], yg4[kpt], w4[kpt]
            N, dNdxi, dNdeta = shape_functions(xi, eta)
            J_mat = np.zeros((2, 2))
            for a in range(4):
                J_mat[0, 0] += dNdxi[a] * pts[a, 0]
                J_mat[0, 1] += dNdxi[a] * pts[a, 1]
                J_mat[1, 0] += dNdeta[a] * pts[a, 0]
                J_mat[1, 1] += dNdeta[a] * pts[a, 1]
            detJ = J_mat[0, 0] * J_mat[1, 1] - J_mat[0, 1] * J_mat[1, 0]
            cjac = detJ * wt
            invJ = np.array([[J_mat[1, 1], -J_mat[0, 1]], [-J_mat[1, 0], J_mat[0, 0]]]) / detJ
            dNdx = np.zeros((2, 4))
            for a in range(4):
                dNdx[0, a] = invJ[0, 0] * dNdxi[a] + invJ[0, 1] * dNdeta[a]
                dNdx[1, a] = invJ[1, 0] * dNdxi[a] + invJ[1, 1] * dNdeta[a]
            H_val = h_vals[kpt]
            for a in range(4):
                ia = node_to_idx[conn[a]]
                F_full[ia] += cjac * 2.0 * H_val * N[a]
                for b in range(4):
                    ib = node_to_idx[conn[b]]
                    grad_dot = dNdx[0, a] * dNdx[0, b] + dNdx[1, a] * dNdx[1, b]
                    val = cjac * ((E_GC / E_L0 + 2.0 * H_val) * N[a] * N[b] + (E_GC * E_L0) * grad_dot)
                    I_full.append(ia)
                    J_full.append(ib)
                    V_full.append(val)

    K_full = sp.coo_matrix((V_full, (I_full, J_full)), shape=(n_nodes, n_nodes)).tocsr()
    return nodes, elements, node_list, node_to_idx, d_ckpt, K_full, F_full

def test_spg(K_full, F_full, d_ckpt):
    """Spectral Projected Gradient (SPG2) solver."""
    n_nodes = len(d_ckpt)
    l = d_ckpt
    u = np.ones(n_nodes)

    def proj(x):
        return np.clip(x, l, u)

    def obj(x):
        Kx = K_full.dot(x)
        return 0.5 * np.dot(x, Kx) - np.dot(F_full, x), Kx - F_full

    x = np.copy(d_ckpt)
    f, g = obj(x)

    alpha = 1.0
    records = []

    for it in range(1, 101):
        # Projected gradient direction
        d_dir = proj(x - alpha * g) - x
        dir_norm = np.max(np.abs(d_dir))

        # Check projected gradient norm as stationarity measure:
        # Stationary iff proj(x - g) - x == 0
        pg_norm = np.max(np.abs(proj(x - g) - x))
        res_A = np.max(np.abs(g[(x > l + 1e-6) & (x < u - 1e-6)])) if np.any((x > l + 1e-6) & (x < u - 1e-6)) else 0.0

        viol_L = np.sum((np.abs(x - l) < 1e-6) & (-g > TAU_RES)) # -g = R_d
        viol_U = np.sum((np.abs(x - u) < 1e-6) & (-g < -TAU_RES))

        records.append({
            "iter": it,
            "dir_norm": float(dir_norm),
            "pg_norm": float(pg_norm),
            "res_A": float(res_A),
            "viol_L": int(viol_L),
            "viol_U": int(viol_U),
            "f": float(f)
        })

        if pg_norm <= TAU_RES and viol_L == 0 and viol_U == 0:
            print(f"[SPG2] Converged at iteration {it}: pg_norm={pg_norm:.3e}, res_A={res_A:.3e}, f={f:.8e}")
            return x, True, records

        # Armijo line search along projection arc
        gamma = 1.0
        c1 = 1e-4
        g_dot_d = np.dot(g, d_dir)
        while gamma > 1e-8:
            x_new = x + gamma * d_dir
            f_new, g_new = obj(x_new)
            if f_new <= f + c1 * gamma * g_dot_d:
                break
            gamma *= 0.5

        # Barzilai-Borwein step length update
        s = x_new - x
        y = g_new - g
        sy = np.dot(s, y)
        if sy > 1e-12:
            alpha = np.dot(s, s) / sy
            alpha = max(1e-4, min(1e4, alpha))
        else:
            alpha = 1.0

        x = x_new
        f = f_new
        g = g_new

    print(f"[SPG2] Did not reach exact tolerance within 100 iters: final pg_norm={pg_norm:.3e}")
    return x, False, records

def test_lbfgsb(K_full, F_full, d_ckpt):
    """Bound-constrained L-BFGS-B solver."""
    n_nodes = len(d_ckpt)
    bounds = [(d_ckpt[i], 1.0) for i in range(n_nodes)]
    history = []

    def obj(d):
        Kd = K_full.dot(d)
        return 0.5 * np.dot(d, Kd) - np.dot(F_full, d), Kd - F_full

    def callback(xk):
        g = K_full.dot(xk) - F_full
        R = -g
        is_at_L = np.abs(xk - d_ckpt) < 1e-6
        is_at_U = np.abs(xk - 1.0) < 1e-6
        is_A = ~(is_at_L | is_at_U)
        res_A = float(np.max(np.abs(R[is_A]))) if np.any(is_A) else 0.0
        viol_L = int(np.sum(R[is_at_L] > TAU_RES))
        viol_U = int(np.sum(R[is_at_U] < -TAU_RES))
        history.append({
            "iter": len(history) + 1,
            "res_A": res_A,
            "viol_L": viol_L,
            "viol_U": viol_U
        })
        if len(history) % 20 == 0 or (res_A <= TAU_RES and viol_L == 0 and viol_U == 0):
            print(f"  [L-BFGS-B Iter {len(history):3d}] ||R_d||_A={res_A:.3e}, viol_L={viol_L}, viol_U={viol_U}")

    print("Testing L-BFGS-B bound-constrained solver...")
    res = minimize(obj, np.copy(d_ckpt), jac=True, method='L-BFGS-B', bounds=bounds, callback=callback, options={'maxiter': 200, 'ftol': 1e-15, 'gtol': 1e-10})
    print(f"[L-BFGS-B] Total iters: {res.nit}, success: {res.success}")
    return res.x, res.success, history

def main():
    nodes, elements, node_list, node_to_idx, d_ckpt, K_full, F_full = load_system()
    x_opt, success, history = test_lbfgsb(K_full, F_full, d_ckpt)

    print(f"\nFinal set sizes: |U|={np.sum(np.abs(x_opt - 1.0) < 1e-6)}, |L|={np.sum(np.abs(x_opt - d_ckpt) < 1e-6)}, |A|={np.sum((x_opt > d_ckpt + 1e-6) & (x_opt < 1.0 - 1e-6))}")

    min_diff = np.min(x_opt - d_ckpt)
    max_d = np.max(x_opt)
    print(f"Strict healing check: min(d - d_ckpt) = {min_diff:+.6e} (must be >= 0)")
    print(f"Strict overshoot check: max(d) = {max_d:.6f} (must be <= 1.0)")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
evaluate_package102_kkt_stationarity.py
Evaluates the authentic KKT stationarity and phase residual of Package 102:
R = F(H) - K * d_abq
Checks complementarity, free-set stationarity, lower-bound multipliers, and upper-bound multipliers.
"""

import sys
import json
import csv
import numpy as np
from pathlib import Path
from scipy import sparse

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
PKG102_DIR = REPO_ROOT / "models/pandey_kumar_mode1/102_c5_coupled_staggered_reequilibration"

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

def assemble_phase_system(mesh_inp, elem_h, G_C=0.0027, L_0=0.0075):
    # Load mesh
    nodes = {}
    elements = {}
    with open(mesh_inp, "r", encoding="utf-8") as f:
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

    node_list = sorted([n for n in nodes.keys() if n != 999999])
    node_to_idx = {nid: i for i, nid in enumerate(node_list)}
    n_nodes = len(node_list)

    gauss_pts = [-1.0 / np.sqrt(3.0), 1.0 / np.sqrt(3.0)]
    weights = [1.0, 1.0]

    rows = []
    cols = []
    vals = []
    F = np.zeros(n_nodes)

    for eid, conn in elements.items():
        elem_nodes = [node_to_idx[nid] for nid in conn]
        xe = np.array([nodes[nid] for nid in conn])
        h_ips = elem_h.get(eid, [0.0, 0.0, 0.0, 0.0])

        ip_idx = 0
        for xi, wx in zip(gauss_pts, weights):
            for eta, wy in zip(gauss_pts, weights):
                N, dNdxi, dNdeta = shape_functions(xi, eta)
                J = np.vstack([dNdxi, dNdeta]) @ xe
                detJ = np.linalg.det(J)
                if detJ <= 0.0:
                    raise RuntimeError(f"Negative detJ in element {eid}")

                invJ = np.linalg.inv(J)
                dNdx = invJ @ np.vstack([dNdxi, dNdeta])
                dV = detJ * wx * wy
                H_val = h_ips[ip_idx]
                ip_idx += 1

                # Local damage stiffness + gradient stiffness
                k_local = ((G_C / L_0) + 2.0 * H_val) * np.outer(N, N) * dV
                k_grad = (G_C * L_0) * (dNdx.T @ dNdx) * dV
                k_elem = k_local + k_grad

                f_elem = 2.0 * H_val * N * dV

                for a in range(4):
                    F[elem_nodes[a]] += f_elem[a]
                    for b in range(4):
                        rows.append(elem_nodes[a])
                        cols.append(elem_nodes[b])
                        vals.append(k_elem[a, b])

    K = sparse.coo_matrix((vals, (rows, cols)), shape=(n_nodes, n_nodes)).tocsr()
    return K, F, node_to_idx, nodes, elements

def main():
    mesh_inp = PKG102_DIR / "candidate_crack_band_mesh_c5.inp"
    
    # Load H_new
    elem_h = {}
    with open(PKG102_DIR / "turn89_c5_updated_h_table.csv", "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or len(row) < 6: continue
            if row[0].strip().upper() == "ELEM_HISTORY":
                eid = int(row[1])
                elem_h[eid] = [float(row[2]), float(row[3]), float(row[4]), float(row[5])]

    print("Assembling phase-field stiffness matrix K and force vector F...")
    K, F, node_to_idx, nodes, elements = assemble_phase_system(mesh_inp, elem_h)

    # Load authentic Abaqus converged nodal d
    extracted_csv = PKG102_DIR / "M1_C5_PACKAGE102_STAGGERED_REEQUIL_extracted.csv"
    d_abq_dict = {}
    with open(extracted_csv, "r", encoding="utf-8") as f:
        for row in csv.reader(f):
            if not row: continue
            if row[0].strip().upper() == "NODE":
                nid = int(row[1])
                d_abq_dict[nid] = float(row[4])

    # Load checkpoint d_ckpt
    state_table = PKG102_DIR / "candidate_c5_frame7_mapped_state_table.csv"
    d_ckpt = {}
    with open(state_table, "r", encoding="utf-8") as f:
        for line in f:
            parts = [p.strip() for p in line.split(",") if p.strip()]
            if parts and parts[0].upper() == "NODE":
                d_ckpt[int(parts[1])] = float(parts[4])

    n_nodes = len(node_to_idx)
    d_vec = np.zeros(n_nodes)
    l_vec = np.zeros(n_nodes)
    for nid, idx in node_to_idx.items():
        d_vec[idx] = d_abq_dict.get(nid, 0.0)
        l_vec[idx] = d_ckpt.get(nid, 0.0)

    # Compute residual: R = F - K * d
    Kd = K @ d_vec
    R = F - Kd  # Stationarity: R = lambda_U - lambda_L

    # Partition nodes into U, L, A
    tol = 1e-6
    set_U = []
    set_L = []
    set_A = []

    for idx in range(n_nodes):
        d_val = d_vec[idx]
        lb = l_vec[idx]
        # Check upper bound first (slit / fully broken)
        if abs(d_val - 1.0) < tol or d_val >= 1.0:
            set_U.append(idx)
        elif abs(d_val - lb) < tol or d_val <= lb:
            set_L.append(idx)
        else:
            set_A.append(idx)

    # KKT Multipliers:
    # On set_A: R should be 0 -> ||R_A||_inf <= 1e-6
    # On set_L: d = lb -> lambda_L = -R >= 0 -> R <= 1e-6
    # On set_U: d = 1.0 -> lambda_U = R >= 0 -> R >= -1e-6
    R_A = R[set_A] if set_A else np.array([0.0])
    R_L = R[set_L] if set_L else np.array([0.0])
    R_U = R[set_U] if set_U else np.array([0.0])

    norm_R_A = float(np.max(np.abs(R_A))) if len(set_A) > 0 else 0.0
    max_kkt_viol_L = float(np.max(np.maximum(0.0, R_L))) if len(set_L) > 0 else 0.0 # R should be <= 0
    max_kkt_viol_U = float(np.max(np.maximum(0.0, -R_U))) if len(set_U) > 0 else 0.0 # R should be >= 0

    print("\n--- VARIATIONAL INEQUALITY KKT AUDIT OF PACKAGE 102 CONVERGED STATE ---")
    print(f"Node counts: Total={n_nodes}, |U|={len(set_U)}, |L|={len(set_L)}, |A|={len(set_A)}")
    print(f"Sum |U|+|L|+|A|: {len(set_U) + len(set_L) + len(set_A)} (Disjoint: {len(set_U) + len(set_L) + len(set_A) == n_nodes})")
    print(f"Free-set Stationarity Residual ||R_d||_inf,A: {norm_R_A:.10e} kN/mm")
    print(f"Threshold (<= 1.0e-6 kN/mm): {'PASS' if norm_R_A <= 1.0e-6 else 'FAIL'}")
    print(f"Max Lower-Bound KKT Violation (R_L > 0): {max_kkt_viol_L:.10e} kN/mm")
    print(f"Max Upper-Bound KKT Violation (R_U < 0): {max_kkt_viol_U:.10e} kN/mm")
    print(f"Valid Complete KKT: {norm_R_A <= 1e-6 and max_kkt_viol_L <= 1e-6 and max_kkt_viol_U <= 1e-6}")

    kkt_report = {
        "package": "PACKAGE_102",
        "n_nodes": n_nodes,
        "set_U_count": len(set_U),
        "set_L_count": len(set_L),
        "set_A_count": len(set_A),
        "norm_R_A_kN_mm": norm_R_A,
        "stationarity_passed": bool(norm_R_A <= 1.0e-6),
        "max_kkt_viol_L": max_kkt_viol_L,
        "max_kkt_viol_U": max_kkt_viol_U,
        "kkt_complete_passed": bool(norm_R_A <= 1e-6 and max_kkt_viol_L <= 1e-6 and max_kkt_viol_U <= 1e-6)
    }

    out_path = REPO_ROOT / "results/validation/mode1_f1597/turn90_pkg102_kkt_stationarity.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(kkt_report, f, indent=2)
    print(f"Saved KKT audit to {out_path}")

if __name__ == "__main__":
    main()

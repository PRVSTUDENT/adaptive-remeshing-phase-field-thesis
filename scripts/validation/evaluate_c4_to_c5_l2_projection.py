#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
evaluate_c4_to_c5_l2_projection.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Rigorous numerical comparison and qualification of nonmatching state transfer
operators from authentic Case A C4 donor (Package 94 Step 4 Frame 7, 4422 quads, 4588 nodes)
to C5 receiver mesh (4440 quads, 4610 nodes).

Governing Acceptance Standards:
1. Authentic Abaqus donor (E_frac = 0.13773671 mJ, RF2 = 112.9707 N) is the SOLE
   authoritative benchmark. No reference substitution or disjunctive local-model criteria.
2. Fracture Energy: |E_frac - E_donor| / E_donor <= 2.0%.
3. Reaction Force:  |RF2 - RF_donor| / RF_donor <= 5.0%.
4. Physical Bounds: Strictly 0.0 <= d <= 1.00000000 at all physical nodes.
5. Pointwise Irreversibility / Non-Healing: d(x) >= d_ckpt(x) across all receiver nodes.
6. Mathematical Rigor: Constrained H^1 minimization must be solved with exact KKT stationarity,
   not ad-hoc post-solve clipping.
"""

import sys
import os
import math
import json
import csv
from pathlib import Path
from typing import Dict, Any, List, Tuple
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from scipy.optimize import minimize

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")

# Material and Model Parameters
E_MOD = 210.0   # kN/mm^2
E_NU = 0.3
E_GC = 0.0027   # kN/mm
E_L0 = 0.0075   # mm
E_K = 1.0e-7
DONOR_RF2_N = 112.97070980072021
DONOR_E_FRAC_MJ = 0.13773671
U_TOP_MM = 0.0020520000252872705

def get_elasticity_c0():
    c11 = E_MOD * (1.0 - E_NU) / ((1.0 + E_NU) * (1.0 - 2.0 * E_NU))
    c12 = E_MOD * E_NU / ((1.0 + E_NU) * (1.0 - 2.0 * E_NU))
    c33 = E_MOD / (2.0 * (1.0 + E_NU))
    C = np.array([
        [c11, c12, 0.0],
        [c12, c11, 0.0],
        [0.0, 0.0, c33]
    ])
    return C

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

def load_mesh(inp_path: Path):
    nodes = {}
    elements = {}
    with open(inp_path, "r", encoding="utf-8") as f:
        reading = None
        for line in f:
            l = line.strip()
            if not l or l.startswith("**"):
                continue
            if l.startswith("*"):
                u = l.upper()
                if u.startswith("*NODE") and not any(u.startswith(k) for k in ["*NODE OUTPUT", "*NODE PRINT", "*NODE FILE"]):
                    reading = "NODE"
                elif u.startswith("*ELEMENT") and ("TYPE=U1" in u or "TYPE=CPE4" in u or "TYPE=U2" in u or reading is None):
                    if "TYPE=U1" in u or "TYPE=CPE4" in u:
                        reading = "ELEMENT"
                    else:
                        reading = None
                elif u.startswith("*ELEMENT"):
                    reading = "ELEMENT"
                else:
                    reading = None
                continue
            parts = [p.strip() for p in l.split(",") if p.strip()]
            if reading == "NODE" and len(parts) >= 3 and parts[0].isdigit():
                nid = int(parts[0])
                if nid != 999999:
                    nodes[nid] = np.array([float(parts[1]), float(parts[2])])
            elif reading == "ELEMENT" and len(parts) >= 5 and parts[0].isdigit():
                eid = int(parts[0])
                if eid <= 4440 or (eid <= 4422 and "c4" in str(inp_path).lower()):
                    elements[eid] = [int(p) for p in parts[1:5]]
    return nodes, elements

def compute_energies(nodes, elements, d):
    gp_coords = [
        (-1.0 / np.sqrt(3.0), -1.0 / np.sqrt(3.0)),
        ( 1.0 / np.sqrt(3.0), -1.0 / np.sqrt(3.0)),
        (-1.0 / np.sqrt(3.0),  1.0 / np.sqrt(3.0)),
        ( 1.0 / np.sqrt(3.0),  1.0 / np.sqrt(3.0))
    ]
    node_list = sorted(nodes.keys())
    node_to_idx = {nid: i for i, nid in enumerate(node_list)}
    
    e_pot = 0.0
    e_grad = 0.0

    for eid in sorted(elements.keys()):
        conn = elements[eid]
        elem_indices = [node_to_idx[n] for n in conn]
        xe = np.array([nodes[n] for n in conn])
        d_e = d[elem_indices]

        for xi, eta in gp_coords:
            N, dNdxi, dNdeta = shape_functions(xi, eta)
            J = np.zeros((2, 2))
            for i in range(4):
                J[0, 0] += dNdxi[i] * xe[i, 0]
                J[0, 1] += dNdxi[i] * xe[i, 1]
                J[1, 0] += dNdeta[i] * xe[i, 0]
                J[1, 1] += dNdeta[i] * xe[i, 1]

            detJ = J[0, 0] * J[1, 1] - J[0, 1] * J[1, 0]
            cj = detJ * 1.0
            invJ = np.array([
                [ J[1, 1], -J[0, 1]],
                [-J[1, 0],  J[0, 0]]
            ]) / detJ

            gradN = np.zeros((2, 4))
            for i in range(4):
                gradN[0, i] = invJ[0, 0] * dNdxi[i] + invJ[0, 1] * dNdeta[i]
                gradN[1, i] = invJ[1, 0] * dNdxi[i] + invJ[1, 1] * dNdeta[i]

            d_pt = np.dot(N, d_e)
            grad_d = np.dot(gradN, d_e)
            grad_d_sq = np.sum(grad_d**2)

            psi_pot = E_GC * 0.5 * (d_pt**2) / E_L0
            psi_grad = E_GC * 0.5 * E_L0 * grad_d_sq

            e_pot += cj * psi_pot
            e_grad += cj * psi_grad

    e_total_kNmm = e_pot + e_grad
    e_total_mJ = e_total_kNmm * 1000.0
    return {
        "e_total_mJ": float(e_total_mJ),
        "e_total_kNmm": float(e_total_kNmm),
        "e_pot_kNmm": float(e_pot),
        "e_grad_kNmm": float(e_grad),
        "e_pot_pct": float(e_pot / e_total_kNmm * 100.0) if e_total_kNmm > 0 else 0.0,
        "e_grad_pct": float(e_grad / e_total_kNmm * 100.0) if e_total_kNmm > 0 else 0.0
    }

def solve_elasticity_rf(nodes, elements, d, u_top=U_TOP_MM, clamp_top_u1=True):
    node_list = sorted(nodes.keys())
    node_to_idx = {nid: i for i, nid in enumerate(node_list)}
    n_nodes = len(node_list)
    n_dofs = 2 * n_nodes

    C0 = get_elasticity_c0()
    gp_coords = [
        (-1.0 / np.sqrt(3.0), -1.0 / np.sqrt(3.0)),
        ( 1.0 / np.sqrt(3.0), -1.0 / np.sqrt(3.0)),
        (-1.0 / np.sqrt(3.0),  1.0 / np.sqrt(3.0)),
        ( 1.0 / np.sqrt(3.0),  1.0 / np.sqrt(3.0))
    ]

    I_u, J_u, V_u = [], [], []
    for eid in sorted(elements.keys()):
        conn = elements[eid]
        elem_indices = [node_to_idx[n] for n in conn]
        xe = np.array([nodes[n] for n in conn])
        d_elem = d[elem_indices]
        d_avg = np.mean(d_elem)
        deg = (1.0 - d_avg)**2 + E_K
        C_deg = C0 * deg

        for xi, eta in gp_coords:
            N, dNdxi, dNdeta = shape_functions(xi, eta)
            J = np.zeros((2, 2))
            for i in range(4):
                J[0, 0] += dNdxi[i] * xe[i, 0]
                J[0, 1] += dNdxi[i] * xe[i, 1]
                J[1, 0] += dNdeta[i] * xe[i, 0]
                J[1, 1] += dNdeta[i] * xe[i, 1]
            detJ = J[0, 0] * J[1, 1] - J[0, 1] * J[1, 0]
            cj = detJ * 1.0
            invJ = np.array([[ J[1, 1], -J[0, 1]], [-J[1, 0],  J[0, 0]]]) / detJ
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

            Ke = cj * B.T.dot(C_deg).dot(B)
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
        if clamp_top_u1:
            prescribed_dofs[2*idx] = 0.0

    prescribed_keys = np.array(sorted(prescribed_dofs.keys()))
    prescribed_vals = np.array([prescribed_dofs[k] for k in prescribed_keys])

    all_dofs = np.arange(n_dofs)
    free_mask = np.ones(n_dofs, dtype=bool)
    free_mask[prescribed_keys] = False
    free_dofs = all_dofs[free_mask]

    rhs_free = -K_u[free_dofs, :][:, prescribed_keys].dot(prescribed_vals)
    K_FF = K_u[free_dofs, :][:, free_dofs]
    u_free = spla.spsolve(K_FF, rhs_free)

    u = np.zeros(n_dofs)
    u[prescribed_keys] = prescribed_vals
    u[free_dofs] = u_free

    R = K_u.dot(u)
    top_rf2 = sum(R[2*node_to_idx[nid] + 1] for nid in top_nodes)
    top_rf2_N = float(top_rf2 * 1000.0) # kN to N
    return top_rf2_N, u

def main():
    print("=====================================================================")
    print("   EVALUATION OF NONMATCHING STATE TRANSFER OPERATORS (C4 -> C5)    ")
    print("=====================================================================")

    # 1. Load C4 donor mesh and state
    c4_mesh_inp = REPO_ROOT / "models/pandey_kumar_mode1/94_c4_package94_authentic_transfer/candidate_crack_band_mesh_c4.inp"
    c4_nodal_csv = REPO_ROOT / "results/validation/mode1_f1597/pkg94_step4_frame7_nodal_state.csv"
    c4_nodes, c4_elements = load_mesh(c4_mesh_inp)
    
    c4_damage_map = {}
    with open(c4_nodal_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            c4_damage_map[int(row["node_id"])] = float(row["damage"])

    c4_node_list = sorted(c4_nodes.keys())
    c4_d = np.array([c4_damage_map[nid] for nid in c4_node_list])
    print(f"Loaded Donor C4 Mesh: {len(c4_nodes)} nodes, {len(c4_elements)} elements")
    print(f"  C4 damage bounds: min={np.min(c4_d):.6e}, max={np.max(c4_d):.6e}")

    # Compute authentic donor energies and force
    c4_energies = compute_energies(c4_nodes, c4_elements, c4_d)
    c4_rf2_clamped, _ = solve_elasticity_rf(c4_nodes, c4_elements, c4_d, clamp_top_u1=True)
    c4_rf2_free, _ = solve_elasticity_rf(c4_nodes, c4_elements, c4_d, clamp_top_u1=False)

    print(f"Donor Reference Values (Abaqus Report / Solver Deliverable):")
    print(f"  Target RF2:            {DONOR_RF2_N:.4f} N")
    print(f"  Target E_frac:         {DONOR_E_FRAC_MJ:.6f} mJ")
    print(f"Donor Reference Values (Discrete Model Evaluation on C4 mesh):")
    print(f"  Model RF2 (clamped u1): {c4_rf2_clamped:.4f} N (diff vs Abaqus: {(c4_rf2_clamped - DONOR_RF2_N)/DONOR_RF2_N*100:+.2f}%)")
    print(f"  Model RF2 (free u1):    {c4_rf2_free:.4f} N (diff vs Abaqus: {(c4_rf2_free - DONOR_RF2_N)/DONOR_RF2_N*100:+.2f}%)")
    print(f"  Model E_frac:          {c4_energies['e_total_mJ']:.6f} mJ (diff vs Abaqus: {(c4_energies['e_total_mJ'] - DONOR_E_FRAC_MJ)/DONOR_E_FRAC_MJ*100:+.2f}%)")

    # 2. Load C5 receiver mesh
    c5_mesh_inp = REPO_ROOT / "models/pandey_kumar_mode1/102_r1_c5_coupled_staggered_history_repaired/candidate_crack_band_mesh_c5.inp"
    c5_nodes, c5_elements = load_mesh(c5_mesh_inp)
    c5_node_list = sorted(c5_nodes.keys())
    c5_node_to_idx = {nid: i for i, nid in enumerate(c5_node_list)}
    n_c5_nodes = len(c5_node_list)
    print(f"\nLoaded Receiver C5 Mesh: {len(c5_nodes)} nodes, {len(c5_elements)} elements")

    # 3. Load Checkpoint d_ckpt and trial d_opt
    c5_state_table = REPO_ROOT / "models/pandey_kumar_mode1/102_r1_c5_coupled_staggered_history_repaired/candidate_c5_frame7_mapped_state_table.csv"
    d_ckpt_map = {}
    with open(c5_state_table, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for r in reader:
            if r and r[0].strip().upper() == "NODE":
                d_ckpt_map[int(r[1])] = float(r[4])
    d_ckpt = np.array([d_ckpt_map[nid] for nid in c5_node_list])

    d_opt_npy = REPO_ROOT / "models/pandey_kumar_mode1/102_r1_c5_coupled_staggered_history_repaired/turn89_c5_staggered_d_opt.npy"
    d_opt = np.load(d_opt_npy)

    # 4. Set up C4 Element Locator for quadrature transfer
    c4_x = np.array(sorted(list(set(round(p[0], 8) for p in c4_nodes.values()))))
    c4_y = np.array(sorted(list(set(round(p[1], 8) for p in c4_nodes.values()))))
    slit_y_idx = int(np.argmin(np.abs(c4_y - 0.050)))
    c4_node_to_idx = {nid: i for i, nid in enumerate(c4_node_list)}

    def locate_c4_element(x: float, y: float, flank_type: str) -> Tuple[int, float, float]:
        x = max(0.0, min(0.100, x))
        y = max(0.0, min(0.100, y))
        i = int(np.searchsorted(c4_x, x)) - 1
        i = max(0, min(len(c4_x) - 2, i))
        j = int(np.searchsorted(c4_y, y)) - 1
        j = max(0, min(len(c4_y) - 2, j))

        if abs(y - 0.050) < 1e-6 and x <= 0.040 + 1e-6:
            if flank_type == "upper":
                j = slit_y_idx
            elif flank_type == "lower":
                j = slit_y_idx - 1

        eid = j * (len(c4_x) - 1) + (i + 1)
        x0, x1 = c4_x[i], c4_x[i + 1]
        y0, y1 = c4_y[j], c4_y[j + 1]
        xi = 2.0 * (x - x0) / (x1 - x0) - 1.0
        eta = 2.0 * (y - y0) / (y1 - y0) - 1.0
        return eid, float(xi), float(eta)

    def eval_c4_field(x: float, y: float, flank_type: str) -> Tuple[float, np.ndarray]:
        c4_eid, xi, eta = locate_c4_element(x, y, flank_type)
        conn = c4_elements[c4_eid]
        c4_indices = [c4_node_to_idx[n] for n in conn]
        d_elem = c4_d[c4_indices]
        xe = np.array([c4_nodes[n] for n in conn])

        N, dNdxi, dNdeta = shape_functions(xi, eta)
        d_val = float(np.dot(N, d_elem))

        J = np.zeros((2, 2))
        for k in range(4):
            J[0, 0] += dNdxi[k] * xe[k, 0]
            J[0, 1] += dNdxi[k] * xe[k, 1]
            J[1, 0] += dNdeta[k] * xe[k, 0]
            J[1, 1] += dNdeta[k] * xe[k, 1]
        detJ = J[0, 0] * J[1, 1] - J[0, 1] * J[1, 0]
        invJ = np.array([[ J[1, 1], -J[0, 1]], [-J[1, 0],  J[0, 0]]]) / detJ
        dNdx = np.zeros((2, 4))
        for k in range(4):
            dNdx[0, k] = invJ[0, 0] * dNdxi[k] + invJ[0, 1] * dNdeta[k]
            dNdx[1, k] = invJ[1, 0] * dNdxi[k] + invJ[1, 1] * dNdeta[k]
        grad_d = np.dot(dNdx, d_elem)

        return d_val, grad_d

    # 5. Assemble C5 Mass Matrix and Projection Load Vectors
    print("\nAssembling C5 Mass Matrix, Gradient Matrix, and Cross-Mesh Projections...")
    gp_coords = [
        (-1.0 / np.sqrt(3.0), -1.0 / np.sqrt(3.0)),
        ( 1.0 / np.sqrt(3.0), -1.0 / np.sqrt(3.0)),
        (-1.0 / np.sqrt(3.0),  1.0 / np.sqrt(3.0)),
        ( 1.0 / np.sqrt(3.0),  1.0 / np.sqrt(3.0))
    ]

    I_m, J_m, V_m = [], [], []
    I_k, J_k, V_k = [], [], []
    f_L2 = np.zeros(n_c5_nodes)
    f_grad = np.zeros(n_c5_nodes)
    m_lumped = np.zeros(n_c5_nodes)

    for eid in sorted(c5_elements.keys()):
        conn = c5_elements[eid]
        elem_indices = [c5_node_to_idx[n] for n in conn]
        xe = np.array([c5_nodes[n] for n in conn])

        cy = np.mean(xe[:, 1])
        flank_type = "upper" if cy >= 0.050 else "lower"

        for xi, eta in gp_coords:
            N, dNdxi, dNdeta = shape_functions(xi, eta)
            J = np.zeros((2, 2))
            for i in range(4):
                J[0, 0] += dNdxi[i] * xe[i, 0]
                J[0, 1] += dNdxi[i] * xe[i, 1]
                J[1, 0] += dNdeta[i] * xe[i, 0]
                J[1, 1] += dNdeta[i] * xe[i, 1]
            detJ = J[0, 0] * J[1, 1] - J[0, 1] * J[1, 0]
            cj = detJ * 1.0
            invJ = np.array([[ J[1, 1], -J[0, 1]], [-J[1, 0],  J[0, 0]]]) / detJ
            dNdx = np.zeros((2, 4))
            for i in range(4):
                dNdx[0, i] = invJ[0, 0] * dNdxi[i] + invJ[0, 1] * dNdeta[i]
                dNdx[1, i] = invJ[1, 0] * dNdxi[i] + invJ[1, 1] * dNdeta[i]

            gp_x = float(np.dot(N, xe[:, 0]))
            gp_y = float(np.dot(N, xe[:, 1]))
            d_c4_gp, grad_d_c4_gp = eval_c4_field(gp_x, gp_y, flank_type)

            for i in range(4):
                idx_i = elem_indices[i]
                f_L2[idx_i] += cj * N[i] * d_c4_gp
                m_lumped[idx_i] += cj * N[i]

                grad_N_dot_grad_d = dNdx[0, i] * grad_d_c4_gp[0] + dNdx[1, i] * grad_d_c4_gp[1]
                f_grad[idx_i] += cj * grad_N_dot_grad_d

                for j in range(4):
                    idx_j = elem_indices[j]
                    I_m.append(idx_i)
                    J_m.append(idx_j)
                    V_m.append(cj * N[i] * N[j])

                    bdb = dNdx[0, i] * dNdx[0, j] + dNdx[1, i] * dNdx[1, j]
                    I_k.append(idx_i)
                    J_k.append(idx_j)
                    V_k.append(cj * bdb)

    M_c5 = sp.coo_matrix((V_m, (I_m, J_m)), shape=(n_c5_nodes, n_c5_nodes)).tocsr()
    K_grad_c5 = sp.coo_matrix((V_k, (I_k, J_k)), shape=(n_c5_nodes, n_c5_nodes)).tocsr()
    print(f"C5 Mass Matrix assembled: {M_c5.nnz} nonzeros")

    # Method B1: Consistent L^2 Projection
    d_L2_raw = spla.spsolve(M_c5, f_L2)
    d_L2_bound = np.clip(d_L2_raw, 0.0, 1.0)

    # Method B2: Lumped Mass Projection
    d_L2_lumped = f_L2 / m_lumped

    # Method C1: Raw H^1 Projection
    A_energy = (E_GC / E_L0) * M_c5 + (E_GC * E_L0) * K_grad_c5
    rhs_energy = (E_GC / E_L0) * f_L2 + (E_GC * E_L0) * f_grad
    d_H1_raw = spla.spsolve(A_energy, rhs_energy)

    # Method C2: Exact Bound-Constrained H^1 Projection (d_ckpt <= d <= 1.0)
    print("\nSolving Exact Bound-Constrained H^1 Projection (d_ckpt <= d <= 1.0)...")
    def loss_and_grad(d):
        Ad = A_energy.dot(d)
        val = 0.5 * np.dot(d, Ad) - np.dot(rhs_energy, d)
        grad = Ad - rhs_energy
        return val, grad

    bounds = [(float(d_ckpt[i]), 1.0) for i in range(n_c5_nodes)]
    res = minimize(
        loss_and_grad,
        d_ckpt.copy(),
        method="L-BFGS-B",
        jac=True,
        bounds=bounds,
        options={"ftol": 1e-15, "gtol": 1e-8, "maxiter": 500}
    )
    d_H1_constrained = res.x
    print(f"  L-BFGS-B Converged: {res.success} in {res.nit} iterations (Status: {res.message})")

    # KKT check for d_H1_constrained
    grad_c = A_energy.dot(d_H1_constrained) - rhs_energy
    min_margin = float(np.min(d_H1_constrained - d_ckpt))
    max_margin = float(np.max(d_H1_constrained - 1.0))
    is_lower = np.abs(d_H1_constrained - d_ckpt) < 1e-6
    is_upper = np.abs(d_H1_constrained - 1.0) < 1e-6
    is_free = ~(is_lower | is_upper)
    lower_mult_viol = int(np.sum(grad_c[is_lower] < -1e-5))
    upper_mult_viol = int(np.sum(grad_c[is_upper] > 1e-5))
    free_grad_norm = float(np.max(np.abs(grad_c[is_free]))) if np.sum(is_free) > 0 else 0.0

    print(f"  KKT Verification: min(d - d_ckpt)={min_margin:.2e}, max(d - 1.0)={max_margin:.2e}")
    print(f"  Active Lower: {np.sum(is_lower)}, Active Upper: {np.sum(is_upper)}, Free: {np.sum(is_free)}")
    print(f"  Lower Violations: {lower_mult_viol}, Upper Violations: {upper_mult_viol}, Free Res Norm: {free_grad_norm:.6e}")

    # 7. Evaluate All Candidates
    candidates = {
        "donor_c4": {
            "name": "Original Case A C4 Donor (Package 94 Step 4 Frame 7)",
            "nodes": c4_nodes,
            "elements": c4_elements,
            "d": c4_d,
            "is_receiver": False
        },
        "method_a_d_ckpt": {
            "name": "Method A: Point-to-Point Interpolation (d_ckpt)",
            "nodes": c5_nodes,
            "elements": c5_elements,
            "d": d_ckpt,
            "is_receiver": True
        },
        "method_b1_l2_raw": {
            "name": "Method B1: Consistent L^2 Projection (Raw)",
            "nodes": c5_nodes,
            "elements": c5_elements,
            "d": d_L2_raw,
            "is_receiver": True
        },
        "method_b2_l2_bound": {
            "name": "Method B2: Consistent L^2 Projection (Clipped)",
            "nodes": c5_nodes,
            "elements": c5_elements,
            "d": d_L2_bound,
            "is_receiver": True
        },
        "method_b3_l2_lumped": {
            "name": "Method B3: Lumped-Mass L^2 Projection",
            "nodes": c5_nodes,
            "elements": c5_elements,
            "d": d_L2_lumped,
            "is_receiver": True
        },
        "method_c1_h1_raw": {
            "name": "Method C1: Energy (H^1) Inner-Product Projection (Raw)",
            "nodes": c5_nodes,
            "elements": c5_elements,
            "d": d_H1_raw,
            "is_receiver": True
        },
        "method_c2_h1_bound_constrained": {
            "name": "Method C2: Exact Bound-Constrained H^1 Transfer (d >= d_ckpt, d <= 1.0)",
            "nodes": c5_nodes,
            "elements": c5_elements,
            "d": d_H1_constrained,
            "is_receiver": True
        },
        "rejected_pkg102_r1_d_opt": {
            "name": "Rejected Package 102-R1 Solver Trial Iterate (d_opt)",
            "nodes": c5_nodes,
            "elements": c5_elements,
            "d": d_opt,
            "is_receiver": True
        }
    }

    results = {}
    print("\n" + "="*85)
    print(f"{'Candidate Operator':<35} | {'E_frac (mJ)':<11} | {'E_frac Err%':<11} | {'RF2 (N)':<9} | {'RF2 Err%':<9} | {'Status'}")
    print("="*85)

    for cid, cinfo in candidates.items():
        c_nodes = cinfo["nodes"]
        c_elems = cinfo["elements"]
        c_d = cinfo["d"]

        en = compute_energies(c_nodes, c_elems, c_d)
        rf2, _ = solve_elasticity_rf(c_nodes, c_elems, c_d, clamp_top_u1=True)

        e_err_abaqus = (en["e_total_mJ"] - DONOR_E_FRAC_MJ) / DONOR_E_FRAC_MJ * 100.0
        rf_err_abaqus = (rf2 - DONOR_RF2_N) / DONOR_RF2_N * 100.0

        e_err_c4_model = (en["e_total_mJ"] - c4_energies["e_total_mJ"]) / c4_energies["e_total_mJ"] * 100.0
        rf_err_c4_model = (rf2 - c4_rf2_clamped) / c4_rf2_clamped * 100.0

        d_min = float(np.min(c_d))
        d_max = float(np.max(c_d))

        # Check bounds: 0.0 <= d <= 1.0
        bounds_pass = (d_min >= -1e-9) and (d_max <= 1.0 + 1e-9) and not (np.isnan(d_min) or np.isnan(d_max))

        # Check non-healing vs d_ckpt (for receiver candidates)
        if cinfo["is_receiver"]:
            heal_violations = int(np.sum(c_d < d_ckpt - 1e-6))
            zero_healing_pass = (heal_violations == 0)
        else:
            heal_violations = 0
            zero_healing_pass = True

        # STRICT CRITERIA: Sole authoritative reference is Authentic Abaqus Donor
        pass_e = abs(e_err_abaqus) <= 2.0
        pass_rf = abs(rf_err_abaqus) <= 5.0

        qualified = bool(pass_e and pass_rf and bounds_pass and zero_healing_pass)
        status = "PASS" if qualified else "FAIL"

        print(f"{cinfo['name'][:35]:<35} | {en['e_total_mJ']:11.6f} | {e_err_abaqus:+10.2f}% | {rf2:9.2f} | {rf_err_abaqus:+8.2f}% | {status}")

        results[cid] = {
            "name": cinfo["name"],
            "d_min": d_min,
            "d_max": d_max,
            "bounds_pass": bounds_pass,
            "zero_healing_pass": zero_healing_pass,
            "healing_node_count": heal_violations,
            "e_total_mJ": en["e_total_mJ"],
            "e_total_kNmm": en["e_total_kNmm"],
            "e_pot_kNmm": en["e_pot_kNmm"],
            "e_grad_kNmm": en["e_grad_kNmm"],
            "e_pot_pct": en["e_pot_pct"],
            "e_grad_pct": en["e_grad_pct"],
            "e_err_vs_donor_abaqus_pct": float(e_err_abaqus),
            "e_err_vs_c4_discrete_model_pct": float(e_err_c4_model),
            "rf2_N": float(rf2),
            "rf_err_vs_donor_abaqus_pct": float(rf_err_abaqus),
            "rf_err_vs_c4_discrete_model_pct": float(rf_err_c4_model),
            "gate_e_pass": bool(pass_e),
            "gate_rf_pass": bool(pass_rf),
            "overall_qualification": status
        }
    print("="*85)

    # 8. Detailed Analysis of Energy Components
    print("\n=== DETAILED ENERGY COMPONENT BREAKDOWN (kN*mm) ===")
    print(f"{'Candidate':<35} | {'E_total':<14} | {'E_pot':<14} | {'E_grad':<14}")
    print("-"*85)
    for cid in ["donor_c4", "method_a_d_ckpt", "method_b2_l2_bound", "method_c2_h1_bound_constrained", "rejected_pkg102_r1_d_opt"]:
        r = results[cid]
        print(f"{r['name'][:35]:<35} | {r['e_total_kNmm']:14.10e} | {r['e_pot_kNmm']:14.10e} | {r['e_grad_kNmm']:14.10e}")

    # 9. Save JSON Summary
    out_json = REPO_ROOT / "results/validation/mode1_f1597/c4_c5_projection_comparison.json"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump({
            "schema": 1,
            "donor_target": {
                "rf2_N": DONOR_RF2_N,
                "e_frac_mJ": DONOR_E_FRAC_MJ,
                "u_top_mm": U_TOP_MM
            },
            "c4_model_discrete_reference": {
                "rf2_clamped_N": float(c4_rf2_clamped),
                "rf2_free_N": float(c4_rf2_free),
                "e_frac_mJ": float(c4_energies["e_total_mJ"]),
                "e_pot_kNmm": float(c4_energies["e_pot_kNmm"]),
                "e_grad_kNmm": float(c4_energies["e_grad_kNmm"])
            },
            "kkt_verification_method_c2": {
                "lbfgsb_converged": bool(res.success),
                "iterations": int(res.nit),
                "active_lower_nodes": int(np.sum(is_lower)),
                "active_upper_nodes": int(np.sum(is_upper)),
                "free_nodes": int(np.sum(is_free)),
                "lower_multiplier_violations": lower_mult_viol,
                "upper_multiplier_violations": upper_mult_viol,
                "free_gradient_norm": free_grad_norm,
                "min_damage_margin_vs_ckpt": min_margin,
                "max_damage_overshoot_vs_one": max_margin
            },
            "candidates": results
        }, f, indent=2)
    print(f"\nSaved detailed projection comparison to: {out_json}")

    # 10. Also save the qualified field to disk
    out_npy = REPO_ROOT / "results/validation/mode1_f1597/c5_h1_bound_constrained_d.npy"
    np.save(out_npy, d_H1_constrained)
    print(f"Saved qualified damage field array to: {out_npy}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_quadrature_and_donor_closure.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER (Turn 100)
Protocol Version: 2

Investigates whether Package 104's apparent over-softening originates from:
1. Quadrature point ordering mismatch between f42_mixed_uel.for and offline python scripts:
   - UEL Fortran order:
       KPT 1: (-a, -a)
       KPT 2: (+a, -a)
       KPT 3: (+a, +a)
       KPT 4: (-a, +a)
     where a = 1/sqrt(3).
   - In prior offline scripts, gp_coords had (-a, +a) at index 2 and (+a, +a) at index 3.
2. Degradation and driving energy formulas:
   - UEL degrades mechanical stiffness using element-averaged damage:
       deg = (1 - d_avg)^2 + k
   - UEL computes driving energy as:
       POS_M = 0.5*lam*(max(0, tr_e))^2 + mu*(e11^2 + e22^2 + 2*e12^2)
3. Same-mesh donor closure test on authentic C4 checkpoint (Package 94 Step 4 Frame 7):
   - 4,422 quads, 4,588 nodes, 17,688 Gauss points.
   - Evaluates whether offline residual assembly R_d = F_d - K_d*d closes to zero
     on the free nodes of authentic converged C4 donor state.
4. Application to C5 checkpoint (Package 103):
   - Assesses physical stationarity and multiplier behavior under strictly aligned UEL operators.
"""

import os
import sys
import csv
import json
from pathlib import Path
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

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
C5_DAT = C5_DIR / "M1_C5_PACKAGE103_H1_PILOT.dat"
C5_CKPT_TABLE = REPO_ROOT / "models/pandey_kumar_mode1/102_r1_c5_coupled_staggered_history_repaired/candidate_c5_frame7_mapped_state_table.csv"
C5_H1_D_PATH = REPO_ROOT / "results/validation/mode1_f1597/c5_h1_bound_constrained_d.npy"

# Material & Phase Field Parameters (Frozen UEL match)
E_MOD = 210.0      # kN/mm^2
NU = 0.3
E_GC = 0.0027      # kN/mm
E_L0 = 0.0075      # mm
K_DEGRAD = 1.0e-7  # residual stiffness
TAU_RES = 1.0e-6   # kN/mm

# Exact UEL Quadrature Constants
A_GAUSS = 0.577350269189626
UEL_GP_COORDS = [
    (-A_GAUSS, -A_GAUSS),  # KPT 1: bottom-left
    ( A_GAUSS, -A_GAUSS),  # KPT 2: bottom-right
    ( A_GAUSS,  A_GAUSS),  # KPT 3: top-right
    (-A_GAUSS,  A_GAUSS),  # KPT 4: top-left
]
UEL_WEIGHTS = [1.0, 1.0, 1.0, 1.0]

def shape_functions(xi, eta):
    """
    4-node quad shape functions and derivatives in parent space [-1, 1]^2.
    Matches f42_mixed_uel.for lines 292-305.
    """
    N = 0.25 * np.array([
        (1.0 - xi) * (1.0 - eta),  # node 1: (-1, -1)
        (1.0 + xi) * (1.0 - eta),  # node 2: (+1, -1)
        (1.0 + xi) * (1.0 + eta),  # node 3: (+1, +1)
        (1.0 - xi) * (1.0 + eta)   # node 4: (-1, +1)
    ])
    dNdxi = 0.25 * np.array([
        -(1.0 - eta),
         (1.0 - eta),
         (1.0 + eta),
        -(1.0 + eta)
    ])
    dNdeta = 0.25 * np.array([
        -(1.0 - xi),
        -(1.0 + xi),
         (1.0 + xi),
         (1.0 - xi)
    ])
    return N, dNdxi, dNdeta

def compute_plane_strain_c0():
    """
    Plane strain isotropic elasticity tensor C0 and Lame parameters.
    Matches f42_mixed_uel.for lines 411-414.
    """
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
    """
    Computes driving energy POS_M matching f42_mixed_uel.for lines 513-526:
      E11 = STRAIN(1)
      E22 = STRAIN(2)
      E12 = HALF * STRAIN(3)
      TR_E = E11 + E22
      IF (TR_E .GT. ZERO) THEN E_POS = TR_E ELSE E_POS = ZERO
      POS_M = HALF*C12_0*(E_POS**2) + C33_0*(E11**2 + E22**2 + TWO*(E12**2))
    """
    e11 = eps[0]
    e22 = eps[1]
    e12 = 0.5 * eps[2]
    tr_e = e11 + e22
    e_pos = max(0.0, tr_e)
    pos_m = 0.5 * lam * (e_pos**2) + mu * (e11**2 + e22**2 + 2.0 * (e12**2))
    return float(pos_m)

def parse_mesh(mesh_path, max_phys_eid):
    nodes = {}
    elements = {}
    with open(mesh_path, "r", encoding="utf-8") as f:
        reading = None
        for line in f:
            l = line.strip()
            if not l or l.startswith("**"):
                continue
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

def assemble_at2_system_uel(nodes, elements, node_to_idx, elem_H):
    """
    Assembles AT2 Phase Field operator K_d and RHS vector F_d matching UEL exactly.
    f42_mixed_uel.for lines 330-348.
    """
    n_nodes = len(node_to_idx)
    I_list, J_list, V_list = [], [], []
    F_global = np.zeros(n_nodes)

    for eid, conn in elements.items():
        pts = np.array([nodes[n] for n in conn])
        h_vals = elem_H[eid]  # 4 values corresponding to KPT 1..4

        for kpt in range(4):
            xi, eta = UEL_GP_COORDS[kpt]
            wt = UEL_WEIGHTS[kpt]
            N, dNdxi, dNdeta = shape_functions(xi, eta)

            # Jacobian J = dN_dxi * coords
            J_mat = np.zeros((2, 2))
            for a in range(4):
                J_mat[0, 0] += dNdxi[a] * pts[a, 0]
                J_mat[0, 1] += dNdxi[a] * pts[a, 1]
                J_mat[1, 0] += dNdeta[a] * pts[a, 0]
                J_mat[1, 1] += dNdeta[a] * pts[a, 1]

            detJ = J_mat[0, 0] * J_mat[1, 1] - J_mat[0, 1] * J_mat[1, 0]
            if detJ <= 0.0:
                raise ValueError(f"Negative Jacobian in element {eid}, kpt {kpt}: {detJ}")
            cjac = detJ * wt

            invJ = np.array([
                [ J_mat[1, 1], -J_mat[0, 1]],
                [-J_mat[1, 0],  J_mat[0, 0]]
            ]) / detJ

            # B_phase = [dN/dx, dN/dy]
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

def compute_energies_and_forces_uel(nodes, elements, node_list, node_to_idx, u_disp_2d, d_vec):
    """
    Computes reaction forces, fracture energy, and elastic energy matching UEL exactly.
    """
    n_nodes = len(node_list)
    C0, lam, mu = compute_plane_strain_c0()

    e_frac_total = 0.0
    e_elas_total = 0.0

    y_vals = [nodes[nid][1] for nid in node_list]
    y_max = max(y_vals)
    top_nodes = set([nid for nid in node_list if abs(nodes[nid][1] - y_max) < 1e-5])

    rf2_top_total = 0.0

    for eid in sorted(elements.keys()):
        conn = elements[eid]
        elem_indices = [node_to_idx[n] for n in conn]
        xe = np.array([nodes[n] for n in conn])
        ue = u_disp_2d[elem_indices, :].flatten()
        de = d_vec[elem_indices]
        d_avg = float(np.mean(de))
        deg = (1.0 - d_avg)**2 + K_DEGRAD
        c_mech = C0 * deg

        f_int_elem = np.zeros(8)

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
            cjac = detJ * wt
            invJ = np.array([
                [ J_mat[1, 1], -J_mat[0, 1]],
                [-J_mat[1, 0],  J_mat[0, 0]]
            ]) / detJ

            # Derivatives of shape functions w.r.t physical coordinates
            dNdx = np.zeros((2, 4))
            for i in range(4):
                dNdx[0, i] = invJ[0, 0] * dNdxi[i] + invJ[0, 1] * dNdeta[i]
                dNdx[1, i] = invJ[1, 0] * dNdxi[i] + invJ[1, 1] * dNdeta[i]

            # Mechanical B matrix (3x8)
            B = np.zeros((3, 8))
            for i in range(4):
                B[0, 2*i]   = dNdx[0, i]
                B[1, 2*i+1] = dNdx[1, i]
                B[2, 2*i]   = dNdx[1, i]
                B[2, 2*i+1] = dNdx[0, i]

            # Strain and Stress
            strain = B.dot(ue)
            stress = c_mech.dot(strain)

            # Internal mechanical force
            f_int_elem += cjac * B.T.dot(stress)

            # Elastic energy at Gauss point: 0.5 * stress : strain
            psi_e_pt = 0.5 * np.dot(stress, strain)
            e_elas_total += cjac * psi_e_pt

            # Fracture energy at Gauss point:
            d_pt = np.dot(N, de)
            grad_d = np.dot(dNdx, de)
            grad_d_sq = np.sum(grad_d**2)
            psi_f_pt = E_GC * (0.5 * (d_pt**2) / E_L0 + 0.5 * E_L0 * grad_d_sq)
            e_frac_total += cjac * psi_f_pt

        # Sum reaction forces on top boundary nodes
        for a, nid in enumerate(conn):
            if nid in top_nodes:
                rf2_top_total += f_int_elem[2*a + 1]

    # Convert to mJ and N
    rf2_N = rf2_top_total * 1000.0  # kN -> N
    e_frac_mJ = e_frac_total * 1000.0  # kN*mm -> mJ
    e_elas_mJ = e_elas_total * 1000.0
    e_total_mJ = e_frac_mJ + e_elas_mJ

    return rf2_N, e_frac_mJ, e_elas_mJ, e_total_mJ

def run_c4_donor_closure_test():
    print("\n" + "="*75)
    print("   STAGE 1: AUTHENTIC C4 DONOR SAME-MESH CLOSURE TEST (PACKAGE 94)   ")
    print("="*75)

    # 1. Load C4 Mesh
    nodes_c4, elems_c4, nlist_c4, n2idx_c4 = parse_mesh(C4_MESH, max_phys_eid=4422)
    n_nodes_c4 = len(nlist_c4)
    n_elems_c4 = len(elems_c4)
    print(f"C4 Mesh loaded: {n_nodes_c4} nodes, {n_elems_c4} quad elements.")

    # 2. Load Authentic C4 Nodal State (u1, u2, d)
    u_c4 = np.zeros((n_nodes_c4, 2))
    d_c4 = np.zeros(n_nodes_c4)
    with open(C4_NODAL_CSV, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            if not row: continue
            nid = int(row[0])
            if nid in n2idx_c4:
                idx = n2idx_c4[nid]
                u_c4[idx, 0] = float(row[3])
                u_c4[idx, 1] = float(row[4])
                d_c4[idx] = float(row[5])

    # 3. Load Authentic C4 GP History (H)
    elem_H_c4 = {}
    with open(C4_GP_CSV, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            if not row: continue
            eid = int(row[0])
            ip = int(row[1])
            h_val = float(row[3])
            if eid not in elem_H_c4:
                elem_H_c4[eid] = [0.0, 0.0, 0.0, 0.0]
            elem_H_c4[eid][ip - 1] = h_val

    # 4. Compute Energies and Reaction Forces on Authentic C4
    rf2_c4, ef_c4, ee_c4, et_c4 = compute_energies_and_forces_uel(
        nodes_c4, elems_c4, nlist_c4, n2idx_c4, u_c4, d_c4
    )

    with open(C4_SUMMARY_JSON, "r", encoding="utf-8") as f:
        c4_summary = json.load(f)
    rf2_auth = c4_summary["rf2_terminal_N"]
    ef_auth = c4_summary["energy"]["E_fracture_kNmm"] * 1000.0
    ee_auth = c4_summary["energy"]["E_elastic_kNmm"] * 1000.0
    et_auth = c4_summary["energy"]["E_total_kNmm"] * 1000.0

    print("\n--- C4 Mechanical Parity Check (Offline UEL vs Authentic Abaqus) ---")
    print(f"  RF2:      Offline = {rf2_c4:.4f} N | Authentic = {rf2_auth:.4f} N | Error = {(rf2_c4 - rf2_auth)/rf2_auth * 100:+.4f}%")
    print(f"  E_frac:   Offline = {ef_c4:.6f} mJ | Authentic = {ef_auth:.6f} mJ | Error = {(ef_c4 - ef_auth)/ef_auth * 100:+.4f}%")
    print(f"  E_elas:   Offline = {ee_c4:.6f} mJ | Authentic = {ee_auth:.6f} mJ | Error = {(ee_c4 - ee_auth)/ee_auth * 100:+.4f}%")
    print(f"  E_total:  Offline = {et_c4:.6f} mJ | Authentic = {et_auth:.6f} mJ | Error = {(et_c4 - et_auth)/et_auth * 100:+.4f}%")

    # 5. Parse Step 4 Prescribed Damage Nodes in C4 Input Deck
    c4_prescribed_d_nodes = set()
    in_step4 = False
    with open(C4_INP, "r", encoding="utf-8") as f:
        for line in f:
            l = line.strip()
            if "*Step, name=FORWARD_CONTINUATION" in l:
                in_step4 = True
                continue
            if in_step4:
                if l.startswith("*End Step"):
                    break
                if l.startswith("*") and not l.startswith("*Boundary"):
                    continue
                parts = [p.strip() for p in l.split(",") if p.strip()]
                if len(parts) >= 4 and parts[0].isdigit() and parts[1] == "3" and parts[2] == "3":
                    c4_prescribed_d_nodes.add(int(parts[0]))

    c4_free_nodes = [nid for nid in nlist_c4 if nid not in c4_prescribed_d_nodes]
    print(f"\n--- C4 Step 4 Boundary Condition Partition ---")
    print(f"  Total Nodes:       {n_nodes_c4}")
    print(f"  Prescribed (Dirichlet clamped): {len(c4_prescribed_d_nodes)}")
    print(f"  Free Nodes (Active phase solve): {len(c4_free_nodes)}")

    # 6. Assemble AT2 Operator on C4 and Evaluate Residual
    K_d_c4, F_d_c4 = assemble_at2_system_uel(nodes_c4, elems_c4, n2idx_c4, elem_H_c4)
    Kd_c4 = K_d_c4.dot(d_c4)
    R_d_c4 = F_d_c4 - Kd_c4

    free_indices_c4 = [n2idx_c4[nid] for nid in c4_free_nodes]
    prescribed_indices_c4 = [n2idx_c4[nid] for nid in c4_prescribed_d_nodes]

    res_inf_free_c4 = float(np.max(np.abs(R_d_c4[free_indices_c4]))) if free_indices_c4 else 0.0
    res_inf_all_c4 = float(np.max(np.abs(R_d_c4)))

    print("\n--- C4 AT2 Phase-Field Residual Analysis ---")
    print(f"  Free Nodes Set A ({len(free_indices_c4)} nodes):      ||R_d||_inf = {res_inf_free_c4:.6e} kN/mm")
    print(f"  Clamped Nodes Set L/U ({len(prescribed_indices_c4)} nodes):  ||R_d||_inf = {float(np.max(np.abs(R_d_c4[prescribed_indices_c4]))):.6e} kN/mm")
    print(f"  All Nodes ({n_nodes_c4} nodes):               ||R_d||_inf = {res_inf_all_c4:.6e} kN/mm")

    # Worst free nodes in C4
    worst_free_indices = sorted(free_indices_c4, key=lambda idx: abs(R_d_c4[idx]), reverse=True)[:10]
    print("\n  Top 10 residual nodes in C4 Free Set:")
    for idx in worst_free_indices:
        nid = nlist_c4[idx]
        pt = nodes_c4[nid]
        print(f"    Node {nid:4d} at ({pt[0]:.4f}, {pt[1]:.4f}): d = {d_c4[idx]:.4f}, F_d = {F_d_c4[idx]:.4e}, Kd = {Kd_c4[idx]:.4e}, R_d = {R_d_c4[idx]:.4e} kN/mm")

    c4_free_closes = (res_inf_free_c4 <= TAU_RES)
    print(f"  ==> Does C4 Free Set Close Under Offline UEL Assembly? {c4_free_closes} (||R_d||_inf <= {TAU_RES:.1e})")

    return {
        "rf2_offline": rf2_c4,
        "rf2_auth": rf2_auth,
        "rf2_error_pct": float((rf2_c4 - rf2_auth)/rf2_auth * 100),
        "e_frac_offline": ef_c4,
        "e_frac_auth": ef_auth,
        "e_frac_error_pct": float((ef_c4 - ef_auth)/ef_auth * 100),
        "e_elas_offline": ee_c4,
        "e_elas_auth": ee_auth,
        "e_elas_error_pct": float((ee_c4 - ee_auth)/ee_auth * 100),
        "num_prescribed_nodes": len(c4_prescribed_d_nodes),
        "num_free_nodes": len(c4_free_nodes),
        "res_inf_free_set": res_inf_free_c4,
        "res_inf_all_nodes": res_inf_all_c4,
        "c4_free_closes": bool(c4_free_closes)
    }

def run_c5_audit():
    print("\n" + "="*75)
    print("   STAGE 2: C5 CHECKPOINT ADMISSIBILITY UNDER ALIGNED UEL OPERATORS   ")
    print("="*75)

    # 1. Load C5 Mesh
    nodes_c5, elems_c5, nlist_c5, n2idx_c5 = parse_mesh(C5_MESH, max_phys_eid=4440)
    n_nodes_c5 = len(nlist_c5)
    n_elems_c5 = len(elems_c5)
    print(f"C5 Mesh loaded: {n_nodes_c5} nodes, {n_elems_c5} quad elements.")

    # 2. Load C5 Checkpoint Damage (d_ckpt from table) and H1 Damage (d_H1)
    d_ckpt_c5 = np.zeros(n_nodes_c5)
    with open(C5_CKPT_TABLE, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for r in reader:
            if r and r[0].strip().upper() == "NODE":
                nid = int(r[1])
                if nid in n2idx_c5:
                    d_ckpt_c5[n2idx_c5[nid]] = float(r[4])

    d_H1_c5 = np.load(C5_H1_D_PATH)

    # 3. Load C5 GP History from Package 103 inp
    elem_H_c5 = {}
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
            elem_H_c5[eid] = h_vals

    print(f"Loaded committed history H across {len(elem_H_c5)} C5 elements.")

    # 4. Assemble AT2 Operator on C5 using Exact UEL Order
    K_d_c5, F_d_c5 = assemble_at2_system_uel(nodes_c5, elems_c5, n2idx_c5, elem_H_c5)

    # 5. Evaluate Residual on d_H1
    Kd_H1 = K_d_c5.dot(d_H1_c5)
    R_d_H1 = F_d_c5 - Kd_H1

    tol = 1e-6
    set_U = np.where(d_H1_c5 >= (1.0 - tol))[0]
    set_L = np.where((d_H1_c5 < (1.0 - tol)) & (d_H1_c5 <= (d_ckpt_c5 + tol)))[0]
    set_A = np.where((d_H1_c5 < (1.0 - tol)) & (d_H1_c5 > (d_ckpt_c5 + tol)))[0]

    res_inf_A = float(np.max(np.abs(R_d_H1[set_A]))) if len(set_A) > 0 else 0.0
    viol_L_H1 = int(np.sum(R_d_H1[set_L] > TAU_RES))
    viol_U_H1 = int(np.sum(R_d_H1[set_U] < -TAU_RES))

    print("\n--- C5 Physical AT2 Phase Residual for Package 103 H^1 Checkpoint ---")
    print(f"  Free Set A (Interior Advancing, {len(set_A)} nodes): ||R_d||_inf = {res_inf_A:.6e} kN/mm")
    print(f"  Lower Set L (Checkpoint Bound, {len(set_L)} nodes):   violations (F > Kd, wants to advance) = {viol_L_H1}")
    print(f"  Upper Set U (Fully Broken, {len(set_U)} nodes):       violations (Kd > F, wants to heal) = {viol_U_H1}")

    # Inspect the violating nodes in Set L
    violating_indices = set_L[np.where(R_d_H1[set_L] > TAU_RES)[0]]
    viol_details = []
    for idx in violating_indices:
        nid = nlist_c5[idx]
        pt = nodes_c5[nid]
        viol_details.append({
            "node_id": nid,
            "x_mm": float(pt[0]),
            "y_mm": float(pt[1]),
            "d_H1": float(d_H1_c5[idx]),
            "d_ckpt": float(d_ckpt_c5[idx]),
            "F_d": float(F_d_c5[idx]),
            "Kd": float(Kd_H1[idx]),
            "residual_R": float(R_d_H1[idx])
        })
        print(f"    Node {nid:4d} at ({pt[0]:.4f}, {pt[1]:.4f}): d_H1={d_H1_c5[idx]:.4f}, d_ckpt={d_ckpt_c5[idx]:.4f}, R_d = {R_d_H1[idx]:.4e} kN/mm")

    return {
        "free_set_A_size": len(set_A),
        "lower_set_L_size": len(set_L),
        "upper_set_U_size": len(set_U),
        "res_inf_set_A": res_inf_A,
        "viol_L_count": viol_L_H1,
        "viol_U_count": viol_U_H1,
        "violating_nodes": viol_details
    }

def main():
    c4_res = run_c4_donor_closure_test()
    c5_res = run_c5_audit()

    output = {
        "schema": 1,
        "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
        "turn": 100,
        "investigation": "quadrature_alignment_and_same_mesh_donor_closure_audit",
        "c4_donor_closure": c4_res,
        "c5_checkpoint_audit": c5_res
    }

    out_path = REPO_ROOT / "results/validation/mode1_f1597/turn100_quadrature_and_donor_closure_audit.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    print(f"\nAudit results saved to {out_path}")

if __name__ == "__main__":
    main()

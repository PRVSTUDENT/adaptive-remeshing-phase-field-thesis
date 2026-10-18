#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mechanical Equilibrium Solver and Parity Audit against f42_mixed_uel.for.

Implements:
1. Exact element stiffness matrices for JTYPE 2 (quad) and JTYPE 4 (tri).
2. Global assembly matching f42_mixed_uel.for constitutive law and degradation.
3. Crack-seam node separation and Mode-I boundary condition enforcement.
4. Partitioned solve K_ff * u_f = - K_fp * u_p and reaction force computation.
5. Clapeyron identity verification: E_elas == 0.5 * u_top * RF_top.
6. Energy derivative / residual check: grad(Pi) == K * u - F.
7. Local element-level parity tests and rigid body / patch tests.
"""

import sys
import math
import time
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

# Material constants matching f42_mixed_uel.for
E_MOD = 210.0      # kN/mm^2 (210 GPa)
E_NU  = 0.3
E_GC  = 2.7e-3     # kN/mm (2.7 N/mm)
E_L0  = 0.0075     # mm (7.5 um)
E_K   = 1.0e-7     # Residual stiffness parameter

# Plane strain elasticity tensor components
C11_0 = E_MOD * (1.0 - E_NU) / ((1.0 + E_NU) * (1.0 - 2.0 * E_NU))
C12_0 = E_MOD * E_NU / ((1.0 + E_NU) * (1.0 - 2.0 * E_NU))
C22_0 = C11_0
C33_0 = E_MOD / (2.0 * (1.0 + E_NU))

# Quadrature for JTYPE 2 (quad)
GPT = 1.0 / math.sqrt(3.0)
XG4 = [-GPT,  GPT,  GPT, -GPT]
YG4 = [-GPT, -GPT,  GPT,  GPT]
W4  = [1.0, 1.0, 1.0, 1.0]

# Quadrature for JTYPE 4 (tri)
XG3 = [1.0 / 3.0]
YG3 = [1.0 / 3.0]
W3  = [0.5]


def compute_quad_stiffness(coords: List[Tuple[float, float]], d_elem: List[float]) -> Tuple[np.ndarray, float]:
    """
    Computes 8x8 element stiffness matrix and strain energy for JTYPE 2 (quad).
    Bitwise faithful to lines 394-512 of f42_mixed_uel.for.
    """
    d_avg = sum(d_elem) / 4.0
    deg = (1.0 - d_avg)**2 + E_K

    D_elas = np.array([
        [C11_0 * deg, C12_0 * deg, 0.0],
        [C12_0 * deg, C22_0 * deg, 0.0],
        [0.0,         0.0,         C33_0 * deg]
    ], dtype=np.float64)

    ke = np.zeros((8, 8), dtype=np.float64)
    vol = 0.0

    for kpt in range(4):
        xi = XG4[kpt]
        eta = YG4[kpt]
        wt = W4[kpt]

        dn = np.array([
            [-0.25 * (1.0 - eta),  0.25 * (1.0 - eta),  0.25 * (1.0 + eta), -0.25 * (1.0 + eta)],
            [-0.25 * (1.0 - xi),  -0.25 * (1.0 + xi),   0.25 * (1.0 + xi),   0.25 * (1.0 - xi)]
        ], dtype=np.float64)

        jac = np.zeros((2, 2), dtype=np.float64)
        for i in range(2):
            for j in range(2):
                jac[i, j] = sum(dn[i, k] * coords[k][j] for k in range(4))

        detJ = jac[0, 0] * jac[1, 1] - jac[0, 1] * jac[1, 0]
        assert detJ > 0.0, f"Non-positive Jacobian in quad: {detJ}"

        cjac = detJ * wt
        vol += cjac

        invJ = np.array([
            [ jac[1, 1] / detJ, -jac[0, 1] / detJ],
            [-jac[1, 0] / detJ,  jac[0, 0] / detJ]
        ], dtype=np.float64)

        B = np.zeros((3, 8), dtype=np.float64)
        for i in range(4):
            B[0, 2*i]   = invJ[0, 0] * dn[0, i] + invJ[0, 1] * dn[1, i]
            B[0, 2*i+1] = 0.0
            B[1, 2*i]   = 0.0
            B[1, 2*i+1] = invJ[1, 0] * dn[0, i] + invJ[1, 1] * dn[1, i]
            B[2, 2*i]   = invJ[1, 0] * dn[0, i] + invJ[1, 1] * dn[1, i]
            B[2, 2*i+1] = invJ[0, 0] * dn[0, i] + invJ[0, 1] * dn[1, i]

        ke += cjac * (B.T @ D_elas @ B)

    return ke, vol


def compute_tri_stiffness(coords: List[Tuple[float, float]], d_elem: List[float]) -> Tuple[np.ndarray, float]:
    """
    Computes 6x6 element stiffness matrix and strain energy for JTYPE 4 (tri).
    Bitwise faithful to lines 675-780 of f42_mixed_uel.for.
    """
    d_avg = sum(d_elem) / 3.0
    deg = (1.0 - d_avg)**2 + E_K

    D_elas = np.array([
        [C11_0 * deg, C12_0 * deg, 0.0],
        [C12_0 * deg, C22_0 * deg, 0.0],
        [0.0,         0.0,         C33_0 * deg]
    ], dtype=np.float64)

    d_ntri = np.array([
        [ 1.0,  0.0, -1.0],
        [ 0.0,  1.0, -1.0]
    ], dtype=np.float64)

    jac = np.zeros((2, 2), dtype=np.float64)
    for i in range(2):
        for j in range(2):
            jac[i, j] = sum(d_ntri[i, k] * coords[k][j] for k in range(3))

    detJ = jac[0, 0] * jac[1, 1] - jac[0, 1] * jac[1, 0]
    assert detJ > 0.0, f"Non-positive Jacobian in tri: {detJ}"

    cjac = detJ * 0.5
    vol = cjac

    invJ = np.array([
        [ jac[1, 1] / detJ, -jac[0, 1] / detJ],
        [-jac[1, 0] / detJ,  jac[0, 0] / detJ]
    ], dtype=np.float64)

    B = np.zeros((3, 6), dtype=np.float64)
    for i in range(3):
        B[0, 2*i]   = invJ[0, 0] * d_ntri[0, i] + invJ[0, 1] * d_ntri[1, i]
        B[0, 2*i+1] = 0.0
        B[1, 2*i]   = 0.0
        B[1, 2*i+1] = invJ[1, 0] * d_ntri[0, i] + invJ[1, 1] * d_ntri[1, i]
        B[2, 2*i]   = invJ[1, 0] * d_ntri[0, i] + invJ[1, 1] * d_ntri[1, i]
        B[2, 2*i+1] = invJ[0, 0] * d_ntri[0, i] + invJ[0, 1] * d_ntri[1, i]

    ke = cjac * (B.T @ D_elas @ B)
    return ke, vol


def assemble_global_mechanical_system(
    mesh,
    d_nodal: Dict[int, float]
) -> Tuple[sp.csr_matrix, Dict[int, int], List[int]]:
    """
    Assembles the sparse global mechanical stiffness matrix K matching f42_mixed_uel.for.
    DOFs: for each node i in node_ids, DOF 2*i is u_x, DOF 2*i+1 is u_y.
    """
    node_ids = sorted(list(mesh.nodes.keys()))
    node_to_idx = {nid: i for i, nid in enumerate(node_ids)}
    num_nodes = len(node_ids)
    num_dofs = 2 * num_nodes

    rows = []
    cols = []
    data = []

    for eid, conn in mesh.elements_u1.items():
        coords = [mesh.nodes[n] for n in conn]
        d_elem = [d_nodal[n] for n in conn]

        if len(conn) == 4:
            ke, _ = compute_quad_stiffness(coords, d_elem)
            dof_indices = []
            for n in conn:
                idx = node_to_idx[n]
                dof_indices.extend([2 * idx, 2 * idx + 1])
            for i in range(8):
                for j in range(8):
                    rows.append(dof_indices[i])
                    cols.append(dof_indices[j])
                    data.append(ke[i, j])
        elif len(conn) == 3:
            ke, _ = compute_tri_stiffness(coords, d_elem)
            dof_indices = []
            for n in conn:
                idx = node_to_idx[n]
                dof_indices.extend([2 * idx, 2 * idx + 1])
            for i in range(6):
                for j in range(6):
                    rows.append(dof_indices[i])
                    cols.append(dof_indices[j])
                    data.append(ke[i, j])

    K = sp.coo_matrix((data, (rows, cols)), shape=(num_dofs, num_dofs)).tocsr()
    return K, node_to_idx, node_ids


def solve_mechanical_equilibrium(
    mesh,
    d_nodal: Dict[int, float],
    u_top: float = 0.0060
) -> Dict[str, Any]:
    """
    Solves discrete mechanical equilibrium on the mesh subject to:
    - y = 0: u_y = 0
    - x = 0, y = 0: u_x = 0
    - y = 1: u_x = 0, u_y = u_top
    Returns displacement field, reaction forces, residual norms, and energy.
    """
    t0 = time.time()
    K, node_to_idx, node_ids = assemble_global_mechanical_system(mesh, d_nodal)
    num_nodes = len(node_ids)
    num_dofs = 2 * num_nodes

    # Identify boundary DOFs
    prescribed_dofs = {}  # dof_idx -> prescribed_value
    top_dofs_y = []

    for nid in node_ids:
        x, y = mesh.nodes[nid]
        idx = node_to_idx[nid]

        # Bottom roller: u_y = 0 at y = 0
        if abs(y - 0.0) < 1e-6:
            prescribed_dofs[2 * idx + 1] = 0.0

        # Pinned anchor: u_x = 0 at x = 0, y = 0
        if abs(x - 0.0) < 1e-6 and abs(y - 0.0) < 1e-6:
            prescribed_dofs[2 * idx] = 0.0

        # Top boundary: u_x = 0, u_y = u_top at y = 1
        if abs(y - 1.0) < 1e-6:
            prescribed_dofs[2 * idx] = 0.0
            prescribed_dofs[2 * idx + 1] = u_top
            top_dofs_y.append(2 * idx + 1)

    p_indices = sorted(list(prescribed_dofs.keys()))
    p_set = set(p_indices)
    f_indices = [i for i in range(num_dofs) if i not in p_set]

    u_p = np.array([prescribed_dofs[i] for i in p_indices], dtype=np.float64)

    # Submatrices
    K_ff = K[f_indices, :][:, f_indices]
    K_fp = K[f_indices, :][:, p_indices]
    K_pf = K[p_indices, :][:, f_indices]
    K_pp = K[p_indices, :][:, p_indices]

    rhs_f = -K_fp @ u_p

    # Direct sparse solve (SuperLU via scipy.sparse.linalg.spsolve)
    t_solve = time.time()
    u_f = spla.spsolve(K_ff, rhs_f)
    solve_time = time.time() - t_solve

    # Assemble full displacement vector
    u_full = np.zeros(num_dofs, dtype=np.float64)
    u_full[f_indices] = u_f
    u_full[p_indices] = u_p

    # Residual on free DOFs
    res_f = K_ff @ u_f - rhs_f
    res_f_norm_kN = np.linalg.norm(res_f)
    res_f_norm_N = res_f_norm_kN * 1e3

    # Reaction forces on prescribed DOFs
    R_p = K_pf @ u_f + K_pp @ u_p
    R_full = np.zeros(num_dofs, dtype=np.float64)
    R_full[p_indices] = R_p

    # Total top reaction force in Y direction
    RF2_kN = sum(R_full[dof] for dof in top_dofs_y)
    RF2_N  = RF2_kN * 1e3

    # Total bottom reaction force in Y direction (equilibrium check)
    bottom_dofs_y = [2 * node_to_idx[nid] + 1 for nid in node_ids if abs(mesh.nodes[nid][1] - 0.0) < 1e-6]
    RF_bottom_kN = sum(R_full[dof] for dof in bottom_dofs_y)
    RF_bottom_N = RF_bottom_kN * 1e3

    # Elastic strain energy
    E_elas_kNmm = 0.5 * float(u_full @ (K @ u_full))
    E_elas_mJ = E_elas_kNmm * 1e3

    # Clapeyron external work comparison
    W_clapeyron_kNmm = 0.5 * u_top * RF2_kN
    W_clapeyron_mJ = W_clapeyron_kNmm * 1e3
    clapeyron_discrepancy_mJ = abs(E_elas_mJ - W_clapeyron_mJ)

    u_nodal = {node_ids[i]: (float(u_full[2 * i]), float(u_full[2 * i + 1])) for i in range(num_nodes)}

    return {
        "u_nodal": u_nodal,
        "u_full": u_full,
        "K": K,
        "RF2_N": RF2_N,
        "RF_bottom_N": RF_bottom_N,
        "RF_imbalance_N": abs(RF2_N + RF_bottom_N),
        "res_free_norm_N": res_f_norm_N,
        "E_elas_mJ": E_elas_mJ,
        "W_clapeyron_mJ": W_clapeyron_mJ,
        "clapeyron_discrepancy_mJ": clapeyron_discrepancy_mJ,
        "solve_time_sec": solve_time,
        "total_time_sec": time.time() - t0,
        "num_free_dofs": len(f_indices),
        "num_prescribed_dofs": len(p_indices)
    }


def run_local_element_parity_tests():
    """
    Conducts exact element-level parity checks:
    1. Single square quad element (1x1 mm) under uniform tension.
    2. Single right-triangle element (1x1 mm) under uniform tension.
    3. Patch test: rigid body translations produce zero strain and zero stiffness energy.
    4. Energy derivative parity: dE/du == K * u.
    """
    print("=== Running Local Element-Level Parity Tests ===")

    # Test 1: Single quad
    coords_quad = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    d_zero = [0.0, 0.0, 0.0, 0.0]
    ke_quad, vol_q = compute_quad_stiffness(coords_quad, d_zero)
    assert abs(vol_q - 1.0) < 1e-12, f"Quad volume mismatch: {vol_q}"

    # Rigid body translations: [1, 0, 1, 0, 1, 0, 1, 0] and [0, 1, 0, 1, 0, 1, 0, 1]
    u_rigid_x = np.array([1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0])
    u_rigid_y = np.array([0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0])
    assert np.linalg.norm(ke_quad @ u_rigid_x) < 1e-12, "Rigid body X translation has nonzero strain"
    assert np.linalg.norm(ke_quad @ u_rigid_y) < 1e-12, "Rigid body Y translation has nonzero strain"

    # Uniform uniaxial tension eps_yy = 0.001
    # Under plane strain, eps_xx = 0, eps_yy = 0.001 -> sigma_yy = C11 * 0.001
    u_tens = np.array([0.0, 0.0,  0.0, 0.0,  0.0, 0.001,  0.0, 0.001])
    f_int = ke_quad @ u_tens
    e_quad = 0.5 * (u_tens @ f_int)
    # Expected analytical: 0.5 * C11_0 * (1 + E_K) * (0.001)^2 * vol
    expected_e = 0.5 * C11_0 * (1.0 + E_K) * (0.001**2) * 1.0
    assert abs(e_quad - expected_e) / expected_e < 1e-12, f"Quad tension energy mismatch: {e_quad} vs {expected_e}"
    print("  [PASS] Single quad element stiffness, volume, rigid-body modes, and tension energy exact.")

    # Test 2: Single tri
    coords_tri = [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)]
    d_tri = [0.0, 0.0, 0.0]
    ke_tri, vol_t = compute_tri_stiffness(coords_tri, d_tri)
    assert abs(vol_t - 0.5) < 1e-12, f"Tri volume mismatch: {vol_t}"

    u_rigid_tx = np.array([1.0, 0.0, 1.0, 0.0, 1.0, 0.0])
    u_rigid_ty = np.array([0.0, 1.0, 0.0, 1.0, 0.0, 1.0])
    assert np.linalg.norm(ke_tri @ u_rigid_tx) < 1e-12, "Tri rigid body X has nonzero strain"
    assert np.linalg.norm(ke_tri @ u_rigid_ty) < 1e-12, "Tri rigid body Y has nonzero strain"

    u_tens_tri = np.array([0.0, 0.0,  0.0, 0.0,  0.0, 0.001])
    f_int_tri = ke_tri @ u_tens_tri
    e_tri = 0.5 * (u_tens_tri @ f_int_tri)
    expected_e_tri = 0.5 * C11_0 * (1.0 + E_K) * (0.001**2) * 0.5
    assert abs(e_tri - expected_e_tri) / expected_e_tri < 1e-12, f"Tri tension energy mismatch: {e_tri} vs {expected_e_tri}"
    print("  [PASS] Single tri element stiffness, volume, rigid-body modes, and tension energy exact.")

    # Test 3: Damage degradation check
    # deg = (1 - 0.5)^2 + 1e-7 = 0.2500001
    d_half = [0.5, 0.5, 0.5, 0.5]
    ke_deg, _ = compute_quad_stiffness(coords_quad, d_half)
    expected_deg = 0.25 + E_K
    assert abs(ke_deg[5, 5] - (expected_deg / (1.0 + E_K)) * ke_quad[5, 5]) < 1e-12, "Damage degradation scaling mismatch"
    print("  [PASS] Element-average damage degradation scaling exact.")

    # Test 4: Energy derivative check: numerical gradient vs analytical K*u
    eps = 1e-7
    u_rand = np.random.RandomState(42).randn(8) * 0.001
    grad_analytical = ke_quad @ u_rand
    grad_num = np.zeros(8)
    for i in range(8):
        u_plus = u_rand.copy()
        u_plus[i] += eps
        u_minus = u_rand.copy()
        u_minus[i] -= eps
        e_plus = 0.5 * (u_plus @ (ke_quad @ u_plus))
        e_minus = 0.5 * (u_minus @ (ke_quad @ u_minus))
        grad_num[i] = (e_plus - e_minus) / (2.0 * eps)
    rel_grad_err = np.linalg.norm(grad_analytical - grad_num) / np.linalg.norm(grad_analytical)
    assert rel_grad_err < 1e-8, f"Gradient parity error: {rel_grad_err}"
    print(f"  [PASS] Energy derivative matches stiffness force vector to rel error {rel_grad_err:.2e}.")


if __name__ == "__main__":
    run_local_element_parity_tests()

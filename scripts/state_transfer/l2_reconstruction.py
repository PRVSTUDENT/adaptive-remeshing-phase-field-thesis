#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Consistent L2 Galerkin Reconstruction, Crack-Wake Stiffness Preservation,
and Nonmatching State Projection for Pandey-Kumar Mode-I Phase-Field Benchmark.

Implements:
1. Consistent L2 Galerkin reconstruction of nodal damage d from element integration-point SDV14.
2. Crack-wake stiffness preservation: prevents standard C^0 Galerkin smoothing from deflating d
   in heavily degraded crack-wake elements (d >= d_thresh, default 0.95), avoiding spurious 9x-12x
   stiffness inflation via (1 - d)^2.
3. Consistent L2 Galerkin projection from donor mesh to nonmatching recipient mesh.
4. Exact Fortran UEL-identical volumetric energy integration for 4-node quads and 3-node tris.
"""

import sys
import os
import json
import time
import math
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

REPO_ROOT = Path(r"D:\Master thesis\Adaptive remeshing")
if str(REPO_ROOT / "scripts" / "state_transfer") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts" / "state_transfer"))

from mode1_state_transfer_engine import (
    parse_mode1_input_deck,
    Mode1Mesh,
    Mode1State,
    Mode1SpatialIndex,
    compute_quad_gauss_points,
    compute_tri_gauss_points,
)

# Benchmark material parameters
E_mod = 210.0      # kN/mm^2
nu = 0.3
Gc = 2.7e-3        # kN/mm
l0 = 0.0075        # mm
k_stab = 1e-7

C11 = E_mod * (1.0 - nu) / ((1.0 + nu) * (1.0 - 2.0 * nu))
C12 = E_mod * nu / ((1.0 + nu) * (1.0 - 2.0 * nu))
C33 = E_mod / (2.0 * (1.0 + nu))

gpt = 1.0 / math.sqrt(3.0)
local_gps = [
    (-gpt, -gpt),
    ( gpt, -gpt),
    ( gpt,  gpt),
    (-gpt,  gpt),
]


def build_consistent_l2_donor_nodal_d(
    donor_mesh: Mode1Mesh,
    donor_json_path: str,
    crack_wake_threshold: Optional[float] = None
) -> Tuple[Dict[int, float], Dict[str, Any]]:
    """
    Solves M_donor * d_nodal = f_donor using exact Gauss point SDV14 values.
    If crack_wake_threshold is specified (e.g. 0.95), applies localized
    stiffness preservation to heavily degraded crack-wake elements.
    """
    print("[1] Building Consistent L2 Galerkin system on donor mesh...")
    t0 = time.time()
    with open(donor_json_path, 'r', encoding='utf-8') as f:
        donor_data = json.load(f)
    elem_sdv = donor_data["elem_sdv"]

    node_ids = sorted(list(donor_mesh.nodes.keys()))
    node_to_idx = {nid: i for i, nid in enumerate(node_ids)}
    num_nodes = len(node_ids)

    rows = []
    cols = []
    data_m = []
    f_vec = np.zeros(num_nodes, dtype=np.float64)

    for eid, conn in donor_mesh.elements_u1.items():
        coords = [donor_mesh.nodes[n] for n in conn]
        svals = elem_sdv.get(str(eid), {})
        d_gps = svals.get("SDV14", [0.0] * 4)
        if len(d_gps) < 4:
            d_gps = [d_gps[0]] * 4 if d_gps else [0.0] * 4

        indices = [node_to_idx[n] for n in conn]

        if len(coords) == 4:
            for g_idx, (xi, eta) in enumerate(local_gps):
                n1 = 0.25 * (1.0 - xi) * (1.0 - eta)
                n2 = 0.25 * (1.0 + xi) * (1.0 - eta)
                n3 = 0.25 * (1.0 + xi) * (1.0 + eta)
                n4 = 0.25 * (1.0 - xi) * (1.0 + eta)
                N = [n1, n2, n3, n4]

                dn_dxi = [-0.25*(1.0-eta), 0.25*(1.0-eta), 0.25*(1.0+eta), -0.25*(1.0+eta)]
                dn_deta = [-0.25*(1.0-xi), -0.25*(1.0+xi), 0.25*(1.0+xi), 0.25*(1.0-xi)]

                j11 = sum(dn_dxi[i] * coords[i][0] for i in range(4))
                j12 = sum(dn_deta[i] * coords[i][0] for i in range(4))
                j21 = sum(dn_dxi[i] * coords[i][1] for i in range(4))
                j22 = sum(dn_deta[i] * coords[i][1] for i in range(4))
                detJ = abs(j11 * j22 - j12 * j21)
                w_detJ = detJ

                d_val = d_gps[g_idx]

                for i in range(4):
                    f_vec[indices[i]] += N[i] * d_val * w_detJ
                    for j in range(4):
                        rows.append(indices[i])
                        cols.append(indices[j])
                        data_m.append(N[i] * N[j] * w_detJ)
        else:
            area = donor_mesh.compute_element_area(eid)
            d_val = d_gps[0] if d_gps else 0.0
            m_tri = (area / 12.0) * np.array([[2, 1, 1], [1, 2, 1], [1, 1, 2]], dtype=np.float64)
            for i in range(3):
                f_vec[indices[i]] += (area / 3.0) * d_val
                for j in range(3):
                    rows.append(indices[i])
                    cols.append(indices[j])
                    data_m.append(m_tri[i, j])

    M = sp.coo_matrix((data_m, (rows, cols)), shape=(num_nodes, num_nodes)).tocsr()
    print(f"  M_donor assembled in {time.time()-t0:.2f}s: shape={M.shape}, nnz={M.nnz}")

    t_solve = time.time()
    d_sol, info = spla.cg(M, f_vec, rtol=1e-10, atol=1e-12, maxiter=500)
    print(f"  CG solver converged with info={info} in {time.time()-t_solve:.2f}s")

    d_sol_clamped = np.clip(d_sol, 0.0, 1.0)
    donor_d_nodal = {node_ids[i]: float(d_sol_clamped[i]) for i in range(num_nodes)}

    if crack_wake_threshold is not None:
        print(f"  Applying crack-wake stiffness preservation (threshold >= {crack_wake_threshold})...")
        for iteration in range(5):
            for eid, svals in elem_sdv.items():
                d_gps = svals.get("SDV14", [])
                if not d_gps:
                    continue
                d_true = sum(d_gps) / len(d_gps)
                if d_true >= crack_wake_threshold:
                    conn = donor_mesh.elements_u1[int(eid)]
                    d_recon = sum(donor_d_nodal[n] for n in conn) / len(conn)
                    if d_recon < d_true:
                        deficit = d_true - d_recon
                        for n in conn:
                            donor_d_nodal[n] = min(1.0, donor_d_nodal[n] + deficit)

    print(f"  Donor nodal d: min={min(donor_d_nodal.values()):.6f}, max={max(donor_d_nodal.values()):.6f}")
    return donor_d_nodal, donor_data


def project_consistent_l2_to_recipient(
    donor_mesh: Mode1Mesh,
    donor_d_nodal: Dict[int, float],
    recipient_mesh: Mode1Mesh
) -> Tuple[Dict[int, float], Mode1SpatialIndex]:
    """
    Projects the donor continuous phase field onto the recipient mesh via consistent L2 Galerkin projection.
    Solves M_recip * d_recip = f_recip where f_recip,a = int (N_a * d_donor(x)) dOmega.
    """
    print("[2] Building Consistent L2 Galerkin system on recipient mesh...")
    t0 = time.time()
    spatial_index = Mode1SpatialIndex(donor_mesh)

    node_ids = sorted(list(recipient_mesh.nodes.keys()))
    node_to_idx = {nid: i for i, nid in enumerate(node_ids)}
    num_nodes = len(node_ids)

    rows = []
    cols = []
    data_m = []
    f_vec = np.zeros(num_nodes, dtype=np.float64)

    for eid, conn in recipient_mesh.elements_u1.items():
        coords = [recipient_mesh.nodes[n] for n in conn]
        flank = recipient_mesh.element_flank.get(eid, "UPPER")
        indices = [node_to_idx[n] for n in conn]

        if len(coords) == 4:
            for xi, eta in local_gps:
                n1 = 0.25 * (1.0 - xi) * (1.0 - eta)
                n2 = 0.25 * (1.0 + xi) * (1.0 - eta)
                n3 = 0.25 * (1.0 + xi) * (1.0 + eta)
                n4 = 0.25 * (1.0 - xi) * (1.0 + eta)
                N = [n1, n2, n3, n4]

                gx = sum(N[i] * coords[i][0] for i in range(4))
                gy = sum(N[i] * coords[i][1] for i in range(4))

                dn_dxi = [-0.25*(1.0-eta), 0.25*(1.0-eta), 0.25*(1.0+eta), -0.25*(1.0+eta)]
                dn_deta = [-0.25*(1.0-xi), -0.25*(1.0+xi), 0.25*(1.0+xi), 0.25*(1.0-xi)]

                j11 = sum(dn_dxi[i] * coords[i][0] for i in range(4))
                j12 = sum(dn_deta[i] * coords[i][0] for i in range(4))
                j21 = sum(dn_dxi[i] * coords[i][1] for i in range(4))
                j22 = sum(dn_deta[i] * coords[i][1] for i in range(4))
                detJ = abs(j11 * j22 - j12 * j21)
                w_detJ = detJ

                host_eid, weights = spatial_index.find_host_element(gx, gy, flank)
                host_conn = donor_mesh.elements_u1[host_eid]
                d_donor_val = sum(weights[a] * donor_d_nodal[host_conn[a]] for a in range(len(weights)))

                for i in range(4):
                    f_vec[indices[i]] += N[i] * d_donor_val * w_detJ
                    for j in range(4):
                        rows.append(indices[i])
                        cols.append(indices[j])
                        data_m.append(N[i] * N[j] * w_detJ)
        else:
            area = recipient_mesh.compute_element_area(eid)
            cx = sum(c[0] for c in coords) / 3.0
            cy = sum(c[1] for c in coords) / 3.0
            host_eid, weights = spatial_index.find_host_element(cx, cy, flank)
            host_conn = donor_mesh.elements_u1[host_eid]
            d_donor_val = sum(weights[a] * donor_d_nodal[host_conn[a]] for a in range(len(weights)))

            m_tri = (area / 12.0) * np.array([[2, 1, 1], [1, 2, 1], [1, 1, 2]], dtype=np.float64)
            for i in range(3):
                f_vec[indices[i]] += (area / 3.0) * d_donor_val
                for j in range(3):
                    rows.append(indices[i])
                    cols.append(indices[j])
                    data_m.append(m_tri[i, j])

    M_recip = sp.coo_matrix((data_m, (rows, cols)), shape=(num_nodes, num_nodes)).tocsr()
    print(f"  M_recip assembled in {time.time()-t0:.2f}s: shape={M_recip.shape}, nnz={M_recip.nnz}")

    t_solve = time.time()
    d_recip_sol, info = spla.cg(M_recip, f_vec, rtol=1e-10, atol=1e-12, maxiter=500)
    print(f"  CG solver on recipient converged with info={info} in {time.time()-t_solve:.2f}s")

    d_recip_clamped = np.clip(d_recip_sol, 0.0, 1.0)
    recip_d_nodal = {node_ids[i]: float(d_recip_clamped[i]) for i in range(num_nodes)}
    print(f"  Recipient nodal d: min={min(recip_d_nodal.values()):.6f}, max={max(recip_d_nodal.values()):.6f}")

    return recip_d_nodal, spatial_index


def compute_energies_exact(
    mesh: Mode1Mesh,
    u_nodal: Dict[int, Tuple[float, float]],
    d_nodal: Dict[int, float]
) -> Dict[str, float]:
    """
    Computes E_elas and E_frac using exact Fortran Abaqus UEL formulation
    for both 4-node quads and 3-node tris.
    """
    total_e_elas = 0.0
    total_e_frac = 0.0
    total_int_d = 0.0
    total_int_grad_d_sq = 0.0
    total_vol = 0.0

    D_NTRI = [[1.0, 0.0, -1.0], [0.0, 1.0, -1.0]]

    for eid, conn in mesh.elements_u1.items():
        coords = [mesh.nodes[n] for n in conn]
        d_elem = [d_nodal[n] for n in conn]
        d_avg = sum(d_elem) / len(d_elem)
        deg = (1.0 - d_avg)**2 + k_stab
        u = []
        for n in conn:
            u.extend(u_nodal[n])

        if len(coords) == 4:
            for xi, eta in local_gps:
                n_vec = [
                    0.25 * (1.0 - xi) * (1.0 - eta),
                    0.25 * (1.0 + xi) * (1.0 - eta),
                    0.25 * (1.0 + xi) * (1.0 + eta),
                    0.25 * (1.0 - xi) * (1.0 + eta)
                ]

                dn = [
                    [-0.25*(1.0-eta), 0.25*(1.0-eta), 0.25*(1.0+eta), -0.25*(1.0+eta)],
                    [-0.25*(1.0-xi), -0.25*(1.0+xi),  0.25*(1.0+xi),  0.25*(1.0-xi)]
                ]

                jac = [[0.0, 0.0], [0.0, 0.0]]
                for i in range(2):
                    for j in range(2):
                        jac[i][j] = sum(dn[i][k] * coords[k][j] for k in range(4))

                detJ = jac[0][0] * jac[1][1] - jac[0][1] * jac[1][0]
                cjac = detJ * 1.0

                invJ = [
                    [ jac[1][1] / detJ, -jac[0][1] / detJ],
                    [-jac[1][0] / detJ,  jac[0][0] / detJ]
                ]

                B_mech = [[0.0]*8 for _ in range(3)]
                for i in range(4):
                    B_mech[0][2*i]   = invJ[0][0]*dn[0][i] + invJ[0][1]*dn[1][i]
                    B_mech[0][2*i+1] = 0.0
                    B_mech[1][2*i]   = 0.0
                    B_mech[1][2*i+1] = invJ[1][0]*dn[0][i] + invJ[1][1]*dn[1][i]
                    B_mech[2][2*i]   = invJ[1][0]*dn[0][i] + invJ[1][1]*dn[1][i]
                    B_mech[2][2*i+1] = invJ[0][0]*dn[0][i] + invJ[0][1]*dn[1][i]

                strain = [0.0, 0.0, 0.0]
                for i in range(3):
                    strain[i] = sum(B_mech[i][j] * u[j] for j in range(8))

                stress = [
                    deg * (C11 * strain[0] + C12 * strain[1]),
                    deg * (C12 * strain[0] + C11 * strain[1]),
                    deg * (C33 * strain[2])
                ]

                psi_e_pt = 0.5 * (stress[0]*strain[0] + stress[1]*strain[1] + stress[2]*strain[2])

                grad_d_x = sum((invJ[0][0]*dn[0][i] + invJ[0][1]*dn[1][i]) * d_elem[i] for i in range(4))
                grad_d_y = sum((invJ[1][0]*dn[0][i] + invJ[1][1]*dn[1][i]) * d_elem[i] for i in range(4))
                grad_d_sq = grad_d_x**2 + grad_d_y**2

                d_pt = sum(n_vec[i] * d_elem[i] for i in range(4))
                psi_f_pt = Gc * (0.5 * (d_pt**2) / l0 + 0.5 * l0 * grad_d_sq)

                total_e_elas += cjac * psi_e_pt
                total_e_frac += cjac * psi_f_pt
                total_int_d += cjac * d_pt
                total_int_grad_d_sq += cjac * grad_d_sq
                total_vol += cjac
        elif len(coords) == 3:
            # Exact Fortran JTYPE 3 & 4 formulation
            jac = [[0.0, 0.0], [0.0, 0.0]]
            for i in range(2):
                for j in range(2):
                    jac[i][j] = sum(D_NTRI[i][k] * coords[k][j] for k in range(3))
            detJ = jac[0][0] * jac[1][1] - jac[0][1] * jac[1][0]
            cjac = detJ * 0.5

            invJ = [
                [ jac[1][1] / detJ, -jac[0][1] / detJ ],
                [-jac[1][0] / detJ,  jac[0][0] / detJ ]
            ]

            B_tri = [[0.0]*6 for _ in range(3)]
            for i in range(3):
                B_tri[0][2*i]   = invJ[0][0]*D_NTRI[0][i] + invJ[0][1]*D_NTRI[1][i]
                B_tri[0][2*i+1] = 0.0
                B_tri[1][2*i]   = 0.0
                B_tri[1][2*i+1] = invJ[1][0]*D_NTRI[0][i] + invJ[1][1]*D_NTRI[1][i]
                B_tri[2][2*i]   = invJ[1][0]*D_NTRI[0][i] + invJ[1][1]*D_NTRI[1][i]
                B_tri[2][2*i+1] = invJ[0][0]*D_NTRI[0][i] + invJ[0][1]*D_NTRI[1][i]

            strain = [0.0, 0.0, 0.0]
            for i in range(3):
                strain[i] = sum(B_tri[i][j] * u[j] for j in range(6))

            stress = [
                deg * (C11 * strain[0] + C12 * strain[1]),
                deg * (C12 * strain[0] + C11 * strain[1]),
                deg * (C33 * strain[2])
            ]

            psi_e_pt = 0.5 * (stress[0]*strain[0] + stress[1]*strain[1] + stress[2]*strain[2])

            grad_d_x = sum((invJ[0][0]*D_NTRI[0][i] + invJ[0][1]*D_NTRI[1][i]) * d_elem[i] for i in range(3))
            grad_d_y = sum((invJ[1][0]*D_NTRI[0][i] + invJ[1][1]*D_NTRI[1][i]) * d_elem[i] for i in range(3))
            grad_d_sq = grad_d_x**2 + grad_d_y**2

            d_pt = sum(d_elem) / 3.0
            psi_f_pt = Gc * (0.5 * (d_pt**2) / l0 + 0.5 * l0 * grad_d_sq)

            total_e_elas += cjac * psi_e_pt
            total_e_frac += cjac * psi_f_pt
            total_int_d += cjac * d_pt
            total_int_grad_d_sq += cjac * grad_d_sq
            total_vol += cjac

    return {
        "vol": total_vol,
        "E_elas_mJ": total_e_elas * 1e3,
        "E_frac_uJ": total_e_frac * 1e6,
        "E_total_mJ": (total_e_elas + total_e_frac) * 1e3,
        "int_d": total_int_d,
        "int_grad_d_sq": total_int_grad_d_sq
    }

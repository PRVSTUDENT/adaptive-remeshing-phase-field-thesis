#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Target Mesh Phase Projection Engine:
Solves the discrete obstacle quadratic program on the target mesh
to ensure target-discrete phase equilibrium while enforcing pointwise
damage irreversibility (d_proj >= d_trans) and physical bounds (0 <= d_proj <= 1).

Provisional Operator:
HOST_ISOPARAMETRIC_BILINEAR_WITH_TARGET_OBSTACLE_PHASE_PROJECTION
"""

import math
from typing import Dict, List, Tuple, Optional, Any, Union
import numpy as np
from scipy.sparse import coo_matrix, csr_matrix, csc_matrix
from scipy.sparse.linalg import spsolve

# Material default parameters
DEFAULT_GC = 0.0027      # kN/mm or kJ/mm^2
DEFAULT_LC = 0.015       # mm
DEFAULT_THICKNESS = 1.0  # mm

# Standard 2x2 Gauss Quadrature Points and Weights
GAUSS_2X2 = [
    (-1.0 / math.sqrt(3.0), -1.0 / math.sqrt(3.0)),
    ( 1.0 / math.sqrt(3.0), -1.0 / math.sqrt(3.0)),
    ( 1.0 / math.sqrt(3.0),  1.0 / math.sqrt(3.0)),
    (-1.0 / math.sqrt(3.0),  1.0 / math.sqrt(3.0)),
]


def quad4_shape_and_grad(xi: float, eta: float) -> Tuple[np.ndarray, np.ndarray]:
    """
    Evaluates 4-node bilinear quadrilateral shape functions and their natural gradients.
    Ordering: 1: (-1, -1), 2: (+1, -1), 3: (+1, +1), 4: (-1, +1)
    """
    n = np.array([
        0.25 * (1.0 - xi) * (1.0 - eta),
        0.25 * (1.0 + xi) * (1.0 - eta),
        0.25 * (1.0 + xi) * (1.0 + eta),
        0.25 * (1.0 - xi) * (1.0 + eta),
    ], dtype=np.float64)

    dndxi = np.array([
        [-0.25 * (1.0 - eta), -0.25 * (1.0 - xi)],
        [ 0.25 * (1.0 - eta), -0.25 * (1.0 + xi)],
        [ 0.25 * (1.0 + eta),  0.25 * (1.0 + xi)],
        [-0.25 * (1.0 + eta),  0.25 * (1.0 - xi)],
    ], dtype=np.float64)

    return n, dndxi


def element_jacobian(coords: np.ndarray, dndxi: np.ndarray) -> Tuple[float, np.ndarray]:
    """
    Computes element Jacobian determinant and inverse Jacobian matrix at a Gauss point.
    coords: (4, 2) array of nodal coordinates [x, y].
    dndxi: (4, 2) array of shape function natural derivatives.
    """
    j = coords.T.dot(dndxi)
    det_j = float(np.linalg.det(j))
    if det_j <= 0.0:
        raise ValueError(f"Non-positive Jacobian determinant: {det_j:.6e}")
    inv_j = np.linalg.inv(j)
    return det_j, inv_j


def assemble_target_phase_system(
    nodes: Dict[int, Tuple[float, float]],
    elements: Dict[int, Union[List[int], Tuple[int, ...]]],
    h_fields: Dict[Union[int, Tuple[int, int]], Union[List[float], Tuple[float, ...], float]],
    gc: float = DEFAULT_GC,
    lc: float = DEFAULT_LC,
    thickness: float = DEFAULT_THICKNESS,
) -> Tuple[List[int], Dict[int, int], csr_matrix, np.ndarray, Dict[str, Any]]:
    """
    Assembles the discrete phase stiffness matrix K(H) and source vector f(H) on the target mesh
    according to the exact Fortran UEL formulation:
      K_ij = int [ Gc * l0 * (grad N_i . grad N_j) + (Gc/l0 + 2*H) * N_i * N_j ] dOmega
      f_i  = int [ 2 * H * N_i ] dOmega

    Returns:
      (node_labels, node_index_map, K_csr, f_vec, assembly_stats)
    """
    labels = sorted(nodes.keys())
    index_map = {nid: i for i, nid in enumerate(labels)}
    num_nodes = len(labels)

    row_indices: List[int] = []
    col_indices: List[int] = []
    matrix_data: List[float] = []
    f_vec = np.zeros(num_nodes, dtype=np.float64)

    total_ip = 0
    min_det_j = float("inf")

    for eid, conn in sorted(elements.items()):
        elem_coords = np.array([nodes[n] for n in conn], dtype=np.float64)
        elem_node_indices = [index_map[n] for n in conn]

        for kpt, (xi, eta) in enumerate(GAUSS_2X2, start=1):
            total_ip += 1
            if (eid, kpt) in h_fields:
                h_val = float(h_fields[(eid, kpt)])
            elif eid in h_fields:
                val = h_fields[eid]
                if isinstance(val, (list, tuple, np.ndarray)):
                    h_val = float(val[kpt - 1])
                else:
                    h_val = float(val)
            else:
                h_val = 0.0

            n_vec, dndxi = quad4_shape_and_grad(xi, eta)
            det_j, inv_j = element_jacobian(elem_coords, dndxi)
            min_det_j = min(min_det_j, det_j)

            dndx = dndxi.dot(inv_j)
            weight = det_j * thickness

            mass_coeff = (gc / lc) + 2.0 * h_val
            local_k = gc * lc * dndx.dot(dndx.T) + mass_coeff * np.outer(n_vec, n_vec)
            local_f = 2.0 * h_val * n_vec

            local_k *= weight
            local_f *= weight

            for a, ia in enumerate(elem_node_indices):
                f_vec[ia] += local_f[a]
                for b, ib in enumerate(elem_node_indices):
                    row_indices.append(ia)
                    col_indices.append(ib)
                    matrix_data.append(local_k[a, b])

    k_csr = coo_matrix(
        (matrix_data, (row_indices, col_indices)),
        shape=(num_nodes, num_nodes),
        dtype=np.float64
    ).tocsr()

    stats = {
        "num_nodes": num_nodes,
        "num_elements": len(elements),
        "num_integration_points": total_ip,
        "min_det_j": min_det_j,
        "gc": gc,
        "lc": lc,
        "thickness": thickness
    }

    return labels, index_map, k_csr, f_vec, stats


def solve_constrained_active_set(
    k_mat: csr_matrix,
    f_vec: np.ndarray,
    d_lower: np.ndarray,
    d_upper: Optional[np.ndarray] = None,
    tol_free: float = 1.0e-10,
    tol_kkt: float = 1.0e-10,
    max_iter: int = 200,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, List[Dict[str, Any]], bool]:
    """
    Solves the constrained quadratic obstacle program:
      min 1/2 d^T K d - f^T d  s.t.  d >= d_lower,  d <= d_upper
    using a primal active-set strategy with exact lower and upper bound enforcement.
    """
    num_nodes = len(d_lower)
    d = d_lower.copy().astype(np.float64)
    active_lb = np.ones(num_nodes, dtype=bool)
    active_ub = np.zeros(num_nodes, dtype=bool)

    if d_upper is None:
        d_upper = np.ones(num_nodes, dtype=np.float64)

    history: List[Dict[str, Any]] = []
    stable_count = 0
    previous_active_lb: Optional[np.ndarray] = None
    previous_active_ub: Optional[np.ndarray] = None

    k_csr = k_mat.tocsr()

    for iteration in range(1, max_iter + 1):
        r = np.asarray(k_csr.dot(d) - f_vec, dtype=np.float64)

        # Release check:
        # At active lower bound: if r_i < -tol_kkt, driving force pushes d_i UP -> release
        release_lb = active_lb & (r < -tol_kkt)
        if np.any(release_lb):
            active_lb[release_lb] = False

        # At active upper bound: if r_i > tol_kkt (meaning f_i < (Kd)_i), driving force pushes d_i DOWN -> release
        release_ub = active_ub & (r > tol_kkt)
        if np.any(release_ub):
            active_ub[release_ub] = False

        active = active_lb | active_ub
        free = ~active

        if np.any(free):
            free_idx = np.flatnonzero(free)
            active_lb_idx = np.flatnonzero(active_lb)
            active_ub_idx = np.flatnonzero(active_ub)

            rhs = f_vec[free_idx].copy()
            if len(active_lb_idx):
                k_free_act = k_csr[free_idx, :][:, active_lb_idx]
                rhs -= k_free_act.dot(d_lower[active_lb_idx])
            if len(active_ub_idx):
                k_free_ub = k_csr[free_idx, :][:, active_ub_idx]
                rhs -= k_free_ub.dot(d_upper[active_ub_idx])

            k_free_free = k_csr[free_idx, :][:, free_idx].tocsc()
            d_free = np.asarray(spsolve(k_free_free, rhs), dtype=np.float64)

            d[active_lb] = d_lower[active_lb]
            d[active_ub] = d_upper[active_ub]
            d[free_idx] = d_free

            # Check lower bound violations
            violate_lb = free_idx[d_free < d_lower[free_idx] - 1.0e-12]
            if len(violate_lb):
                d[violate_lb] = d_lower[violate_lb]
                active_lb[violate_lb] = True

            # Check upper bound violations
            violate_ub = free_idx[d_free > d_upper[free_idx] + 1.0e-12]
            if len(violate_ub):
                d[violate_ub] = d_upper[violate_ub]
                active_ub[violate_ub] = True
        else:
            d[active_lb] = d_lower[active_lb]
            d[active_ub] = d_upper[active_ub]

        r = np.asarray(k_csr.dot(d) - f_vec, dtype=np.float64)
        active = active_lb | active_ub
        free = ~active

        free_res_inf = float(np.max(np.abs(r[free]))) if np.any(free) else 0.0
        free_res_l2 = float(np.linalg.norm(r[free])) if np.any(free) else 0.0
        min_lb_mult = float(np.min(r[active_lb])) if np.any(active_lb) else 0.0
        max_ub_mult = float(np.max(r[active_ub])) if np.any(active_ub) else 0.0 # should be <= 0
        min_lb_margin = float(np.min(d - d_lower))
        max_ub_margin = float(np.max(d - d_upper))

        unchanged = (
            (previous_active_lb is not None)
            and np.array_equal(active_lb, previous_active_lb)
            and (previous_active_ub is not None)
            and np.array_equal(active_ub, previous_active_ub)
        )
        stable_count = stable_count + 1 if unchanged else 0

        history.append({
            "iteration": iteration,
            "active_lb_nodes": int(np.count_nonzero(active_lb)),
            "active_ub_nodes": int(np.count_nonzero(active_ub)),
            "free_nodes": int(np.count_nonzero(free)),
            "released_lb": int(np.count_nonzero(release_lb)),
            "released_ub": int(np.count_nonzero(release_ub)),
            "free_res_inf": free_res_inf,
            "free_res_l2": free_res_l2,
            "min_lb_multiplier": min_lb_mult,
            "max_ub_multiplier": max_ub_mult,
            "min_lb_margin": min_lb_margin,
            "max_ub_margin": max_ub_margin,
            "stable": bool(unchanged)
        })

        if (
            free_res_inf <= tol_free
            and min_lb_mult >= -tol_kkt
            and max_ub_mult <= tol_kkt
            and min_lb_margin >= -1.0e-12
            and max_ub_margin <= 1.0e-12
            and stable_count >= 1
        ):
            return d, active_lb, active_ub, history, True

        previous_active_lb = active_lb.copy()
        previous_active_ub = active_ub.copy()

    return d, active_lb, active_ub, history, False


def project_target_phase_field(
    target_nodes: Dict[int, Tuple[float, float]],
    target_elements: Dict[int, Union[List[int], Tuple[int, ...]]],
    target_h_fields: Dict[Union[int, Tuple[int, int]], Union[List[float], Tuple[float, ...], float]],
    d_trans: Dict[int, float],
    d_ref: Optional[Dict[int, float]] = None,
    gc: float = DEFAULT_GC,
    lc: float = DEFAULT_LC,
    thickness: float = DEFAULT_THICKNESS,
    tol_free: float = 1.0e-10,
    tol_kkt: float = 1.0e-10,
    max_iter: int = 200,
) -> Tuple[Dict[int, float], Dict[str, Any]]:
    """
    High-level entry point for target-mesh constrained phase projection.
    """
    labels, index_map, k_csr, f_vec, stats = assemble_target_phase_system(
        target_nodes, target_elements, target_h_fields, gc=gc, lc=lc, thickness=thickness
    )

    d_trans_vec = np.array([d_trans[nid] for nid in labels], dtype=np.float64)
    d_lower = d_trans_vec.copy()
    d_upper = np.ones_like(d_lower)

    # Initial residual
    r_init = np.asarray(k_csr.dot(d_trans_vec) - f_vec, dtype=np.float64)
    l2_init = float(np.linalg.norm(r_init))
    rms_init = float(np.sqrt(np.mean(r_init**2)))
    max_init = float(np.max(np.abs(r_init)))

    d_proj_vec, active_lb, active_ub, history, converged = solve_constrained_active_set(
        k_csr, f_vec, d_lower, d_upper, tol_free=tol_free, tol_kkt=tol_kkt, max_iter=max_iter
    )

    free_mask = ~(active_lb | active_ub)
    r_proj = np.asarray(k_csr.dot(d_proj_vec) - f_vec, dtype=np.float64)

    r_free = r_proj[free_mask]
    l2_free = float(np.linalg.norm(r_free)) if len(r_free) else 0.0
    rms_free = float(np.sqrt(np.mean(r_free**2))) if len(r_free) else 0.0
    max_free = float(np.max(np.abs(r_free))) if len(r_free) else 0.0

    l2_proj_alg = float(np.linalg.norm(r_proj))
    rms_proj_alg = float(np.sqrt(np.mean(r_proj**2)))
    max_proj_alg = float(np.max(np.abs(r_proj)))

    diff_proj_trans = np.abs(d_proj_vec - d_trans_vec)
    max_diff_trans = float(np.max(diff_proj_trans))
    mean_diff_trans = float(np.mean(diff_proj_trans))
    rms_diff_trans = float(np.sqrt(np.mean(diff_proj_trans**2)))

    d_proj_dict = {nid: float(d_proj_vec[i]) for i, nid in enumerate(labels)}

    diagnostics = {
        "converged": converged,
        "iterations": len(history),
        "active_lb_nodes": int(np.count_nonzero(active_lb)),
        "active_ub_nodes": int(np.count_nonzero(active_ub)),
        "free_nodes": int(np.count_nonzero(free_mask)),
        "initial_residual": {
            "l2": l2_init,
            "rms": rms_init,
            "max": max_init
        },
        "post_residual_free": {
            "l2": l2_free,
            "rms": rms_free,
            "max": max_free
        },
        "post_residual_algebraic": {
            "l2": l2_proj_alg,
            "rms": rms_proj_alg,
            "max": max_proj_alg
        },
        "modification_vs_trans": {
            "max": max_diff_trans,
            "mean": mean_diff_trans,
            "rms": rms_diff_trans
        },
        "bounds": {
            "min_d": float(np.min(d_proj_vec)),
            "max_d": float(np.max(d_proj_vec)),
            "min_margin_lower": float(np.min(d_proj_vec - d_lower)),
            "max_margin_upper": float(np.max(d_proj_vec - d_upper))
        },
        "kkt_status": {
            "min_lb_multiplier": float(np.min(r_proj[active_lb])) if np.any(active_lb) else 0.0,
            "max_lb_multiplier": float(np.max(r_proj[active_lb])) if np.any(active_lb) else 0.0,
            "max_ub_multiplier": float(np.max(r_proj[active_ub])) if np.any(active_ub) else 0.0,
            "free_residual_inf": max_free
        }
    }

    if d_ref is not None:
        d_ref_vec = np.array([d_ref[nid] for nid in labels], dtype=np.float64)
        diff_trans_ref = np.abs(d_trans_vec - d_ref_vec)
        diff_proj_ref = np.abs(d_proj_vec - d_ref_vec)

        max_trans_ref = float(np.max(diff_trans_ref))
        rms_trans_ref = float(np.sqrt(np.mean(diff_trans_ref**2)))
        max_proj_ref = float(np.max(diff_proj_ref))
        rms_proj_ref = float(np.sqrt(np.mean(diff_proj_ref**2)))

        rms_red = float((rms_trans_ref - rms_proj_ref) / rms_trans_ref * 100.0) if rms_trans_ref > 0 else 0.0
        max_red = float((max_trans_ref - max_proj_ref) / max_trans_ref * 100.0) if max_trans_ref > 0 else 0.0

        diagnostics["reference_comparison"] = {
            "trans_vs_ref_max": max_trans_ref,
            "trans_vs_ref_rms": rms_trans_ref,
            "proj_vs_ref_max": max_proj_ref,
            "proj_vs_ref_rms": rms_proj_ref,
            "rms_reduction_pct": rms_red,
            "max_reduction_pct": max_red,
            "d_max_trans": float(np.max(d_trans_vec)),
            "d_max_ref": float(np.max(d_ref_vec)),
            "d_max_proj": float(np.max(d_proj_vec))
        }

    return d_proj_dict, diagnostics

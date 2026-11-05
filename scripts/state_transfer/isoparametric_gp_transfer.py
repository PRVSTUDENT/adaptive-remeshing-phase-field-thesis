#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
isoparametric_gp_transfer.py
============================
Candidate Isoparametric Bilinear Gauss-Point History Transfer Operator.
Task: F1620-METHOD-C-ISOPARAMETRIC-GP-TRANSFER-QUALIFICATION
Protocol Version: 2

Provides gradient-preserving transfer of Gauss-point history variables
for 4-node quad elements (CPE4 and 4-node UEL) under 2x2 Gauss quadrature.

Mathematical Foundation:
- 2x2 Gauss points in natural coordinates: q = 1/sqrt(3) ~= 0.577350269189626
    GP 1: (-q, -q)   GP 2: (+q, -q)
    GP 3: (+q, +q)   GP 4: (-q, +q)
- Gauss-point bilinear reconstruction functions:
    M_k(xi, eta) = 0.25 * (1 + 3 * xi_k * xi) * (1 + 3 * eta_k * eta)
- On identical mesh (same-mesh transfer):
    M_k(xi_j, eta_j) = delta_{kj}
    H_interp(xi_j, eta_j) == H_j^donor to machine precision (0.0 +/- 1e-15).
- On nonmatching receiver mesh:
    Maintains intra-element history gradients without artificial element-averaging
    flattening, preserving peak driving forces at the crack tip.
- Thermodynamic Safeguards:
    H >= 0.0 enforced strictly.
    Extrapolation limiter modes:
      * 'none': raw linear extrapolation
      * 'nonnegative': H = max(0.0, H_raw)
      * 'convex_clamp': H clamped to [min(H_donor), max(H_donor)] when outside GP rectangle
"""

from __future__ import print_function, division
import math
import sys
from pathlib import Path
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Gauss quadrature constants for 2x2 rule on [-1, 1]^2
Q_GAUSS = 1.0 / math.sqrt(3.0)  # ~0.5773502691896257
GAUSS_1D = [-Q_GAUSS, Q_GAUSS]
GAUSS_WEIGHTS = [1.0, 1.0]

# Standard Abaqus CPE4 / UEL 2x2 Gauss point locations
QUAD_GP_LOCAL = [
    (-Q_GAUSS, -Q_GAUSS),  # GP 1: (-q, -q)
    ( Q_GAUSS, -Q_GAUSS),  # GP 2: (+q, -q)
    ( Q_GAUSS,  Q_GAUSS),  # GP 3: (+q, +q)
    (-Q_GAUSS,  Q_GAUSS),  # GP 4: (-q, +q)
]


def quad_nodal_shape_functions(xi: float, eta: float) -> List[float]:
    """Evaluates standard bilinear shape functions N_i(xi, eta) for a 4-node quad."""
    return [
        0.25 * (1.0 - xi) * (1.0 - eta),
        0.25 * (1.0 + xi) * (1.0 - eta),
        0.25 * (1.0 + xi) * (1.0 + eta),
        0.25 * (1.0 - xi) * (1.0 + eta),
    ]


def quad_nodal_shape_gradients(xi: float, eta: float) -> Tuple[List[float], List[float]]:
    """Evaluates partial derivatives (dN/dxi, dN/deta) of bilinear nodal shape functions."""
    dxi = [
        -0.25 * (1.0 - eta),
         0.25 * (1.0 - eta),
         0.25 * (1.0 + eta),
        -0.25 * (1.0 + eta),
    ]
    deta = [
        -0.25 * (1.0 - xi),
        -0.25 * (1.0 + xi),
         0.25 * (1.0 + xi),
         0.25 * (1.0 - xi),
    ]
    return dxi, deta


def quad_gp_shape_functions(xi: float, eta: float) -> List[float]:
    """
    Evaluates bilinear Gauss-point interpolation shape functions M_k(xi, eta).
    These functions interpolate from the 4 Gauss points (xi_k, eta_k) and satisfy:
        M_k(xi_j, eta_j) = delta_{kj} (Kronecker delta)
        sum_{k=1}^4 M_k(xi, eta) = 1.0 for all (xi, eta)
    Formula:
        M_k(xi, eta) = 0.25 * (1 + 3 * xi_k * xi) * (1 + 3 * eta_k * eta)
    """
    funcs = []
    for xi_k, eta_k in QUAD_GP_LOCAL:
        # Note: 3 * xi_k * xi = 3 * (+/- 1/sqrt(3)) * xi = +/- sqrt(3) * xi
        val = 0.25 * (1.0 + 3.0 * xi_k * xi) * (1.0 + 3.0 * eta_k * eta)
        funcs.append(val)
    return funcs


def inverse_isoparametric_quad(
    vertices: List[Tuple[float, float]],
    x: float,
    y: float,
    max_iter: int = 25,
    tol: float = 1e-12
) -> Tuple[float, float, bool]:
    """
    Calculates natural coordinates (xi, eta) in [-1, 1]^2 corresponding to physical point (x, y)
    inside a 4-node quad with given vertex coordinates [(x1,y1), (x2,y2), (x3,y3), (x4,y4)].

    Returns (xi, eta, converged).
    """
    # Fast path for axis-aligned rectangles
    xs = [v[0] for v in vertices]
    ys = [v[1] for v in vertices]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    
    # Check if element is an axis-aligned rectangle
    is_rect = (
        abs(vertices[0][1] - vertices[1][1]) < 1e-10 and
        abs(vertices[2][1] - vertices[3][1]) < 1e-10 and
        abs(vertices[0][0] - vertices[3][0]) < 1e-10 and
        abs(vertices[1][0] - vertices[2][0]) < 1e-10
    )
    if is_rect:
        hx = xmax - xmin
        hy = ymax - ymin
        if hx > 1e-14 and hy > 1e-14:
            xi = 2.0 * (x - xmin) / hx - 1.0
            eta = 2.0 * (y - ymin) / hy - 1.0
            return xi, eta, True

    # General quad Newton-Raphson inversion
    xi, eta = 0.0, 0.0
    for _ in range(max_iter):
        N = quad_nodal_shape_functions(xi, eta)
        dxi, deta = quad_nodal_shape_gradients(xi, eta)

        # Evaluated physical position
        xp = sum(N[i] * vertices[i][0] for i in range(4))
        yp = sum(N[i] * vertices[i][1] for i in range(4))

        # Residual
        rx = x - xp
        ry = y - yp
        if math.sqrt(rx * rx + ry * ry) < tol:
            return xi, eta, True

        # Jacobian matrix J = [dx/dxi dx/deta; dy/dxi dy/deta]
        j11 = sum(dxi[i] * vertices[i][0] for i in range(4))
        j12 = sum(deta[i] * vertices[i][0] for i in range(4))
        j21 = sum(dxi[i] * vertices[i][1] for i in range(4))
        j22 = sum(deta[i] * vertices[i][1] for i in range(4))

        det = j11 * j22 - j12 * j21
        if abs(det) < 1e-15:
            break

        # Solve J * [dxi; deta] = [rx; ry]
        d_xi = ( j22 * rx - j12 * ry) / det
        d_eta = (-j21 * rx + j11 * ry) / det

        xi += d_xi
        eta += d_eta

        if math.sqrt(d_xi * d_xi + d_eta * d_eta) < tol:
            return xi, eta, True

    return xi, eta, False


def reconstruct_gp_history(
    donor_gp_values: List[float],
    xi: float,
    eta: float,
    limiter_mode: str = "convex_clamp"
) -> float:
    """
    Reconstructs the scalar history value H(xi, eta) from the 4 donor Gauss-point values
    using bilinear GP shape functions M_k(xi, eta).

    limiter_mode options:
      - 'none': unconstrained raw polynomial evaluation.
      - 'nonnegative': enforces H >= 0.0 (thermodynamic non-negativity).
      - 'convex_clamp': enforces H >= 0.0 and, when (xi, eta) lies outside the donor GP
        rectangle (|xi| > q or |eta| > q), clamps H to [min(donor_H), max(donor_H)]
        to prevent unphysical overshoot / undershoot from negative extrapolation weights.
    """
    assert len(donor_gp_values) == 4, f"Expected 4 donor GP values, got {len(donor_gp_values)}"
    
    # Evaluate bilinear shape functions
    M = quad_gp_shape_functions(xi, eta)
    h_raw = sum(M[k] * donor_gp_values[k] for k in range(4))

    # Check if point is inside the convex hull of the 4 Gauss points
    inside_gp_box = (abs(xi) <= Q_GAUSS + 1e-9) and (abs(eta) <= Q_GAUSS + 1e-9)

    if limiter_mode == "none":
        return h_raw
    elif limiter_mode == "nonnegative":
        return max(0.0, h_raw)
    elif limiter_mode == "convex_clamp":
        if inside_gp_box:
            # Inside GP box, weights are strictly nonnegative and sum to 1
            return max(0.0, h_raw)
        else:
            # Outside GP box, negative weights can occur; clamp to donor extrema
            h_min = min(donor_gp_values)
            h_max = max(donor_gp_values)
            return max(0.0, max(h_min, min(h_max, h_raw)))
    else:
        raise ValueError(f"Unknown limiter_mode: {limiter_mode}")


def transfer_isoparametric_gp_history(
    donor_mesh: Dict[str, Any],
    donor_history_dict: Dict[Tuple[int, int], float],
    receiver_mesh: Dict[str, Any],
    limiter_mode: str = "convex_clamp",
    slit_y: float = 0.050,
    slit_a0: float = 0.040,
    bin_size: float = 0.005
) -> Dict[str, Any]:
    """
    Performs full isoparametric bilinear Gauss-point history transfer from donor_mesh to receiver_mesh.

    donor_history_dict: map (donor_eid, gp_idx) -> H_val (1-based gp_idx in {1, 2, 3, 4})
    Returns dict containing:
      - 'transferred_history': map receiver_eid -> [H1, H2, H3, H4]
      - 'transferred_history_dict': map (receiver_eid, gp_idx) -> H_val
      - 'extrapolation_count': number of GPs evaluated outside donor GP box
      - 'clamped_count': number of GPs clamped by limiter
      - 'negative_prevented_count': number of raw evaluations that would have been < 0
      - 'max_extrapolation_distance': max distance outside donor GP rectangle
    """
    d_nodes = donor_mesh["nodes"]
    d_quads = donor_mesh.get("quads", donor_mesh.get("elements", {}))
    r_nodes = receiver_mesh["nodes"]
    r_quads = receiver_mesh.get("elements", receiver_mesh.get("quads", {}))

    # Pre-organize donor quads by upper and lower slit flanks
    upper_quads = {}
    lower_quads = {}
    for eid, conn in d_quads.items():
        cy = sum(d_nodes[n][1] for n in conn) / 4.0
        if cy >= slit_y - 1e-7:
            upper_quads[eid] = conn
        else:
            lower_quads[eid] = conn

    # Build 2D spatial bins for donor elements
    def build_bins(quad_dict):
        bboxes = []
        for eid, conn in quad_dict.items():
            xs = [d_nodes[n][0] for n in conn]
            ys = [d_nodes[n][1] for n in conn]
            bboxes.append((eid, min(xs), max(xs), min(ys), max(ys), conn))

        bins = defaultdict(list)
        for item in bboxes:
            eid, xmin, xmax, ymin, ymax, conn = item
            bx0 = max(0, int(xmin / bin_size))
            bx1 = int(math.ceil(xmax / bin_size))
            by0 = max(0, int(ymin / bin_size))
            by1 = int(math.ceil(ymax / bin_size))
            for bx in range(bx0, bx1 + 1):
                for by in range(by0, by1 + 1):
                    bins[(bx, by)].append(item)
        return bins, bboxes

    bins_upper, bboxes_upper = build_bins(upper_quads)
    bins_lower, bboxes_lower = build_bins(lower_quads)

    # Slit-flank identification
    r_slit_pairs = receiver_mesh.get("coincident_slit_pairs", [])
    upper_slit_nids = set(p[1] for p in r_slit_pairs)

    result_history: Dict[int, List[float]] = {}
    result_history_dict: Dict[Tuple[int, int], float] = {}

    extrapolation_count = 0
    clamped_count = 0
    negative_prevented_count = 0
    max_extrap_dist = 0.0

    for r_eid, r_conn in r_quads.items():
        r_coords = [r_nodes[n] for n in r_conn]
        r_cy = sum(c[1] for c in r_coords) / 4.0

        # Slit-flank assignment for receiver element
        is_upper = (r_cy >= slit_y - 1e-7) or any(n in upper_slit_nids for n in r_conn)
        target_bins = bins_upper if is_upper else bins_lower
        fallback_bboxes = bboxes_upper if is_upper else bboxes_lower

        elem_h = []
        for gp_idx, (r_xi, r_eta) in enumerate(QUAD_GP_LOCAL, start=1):
            # 1. Compute physical coordinates of receiver Gauss point
            N_r = quad_nodal_shape_functions(r_xi, r_eta)
            gx = sum(N_r[i] * r_coords[i][0] for i in range(4))
            gy = sum(N_r[i] * r_coords[i][1] for i in range(4))

            # Shortcut: if identical mesh and element exists directly in donor
            if r_eid in d_quads and r_conn == d_quads[r_eid]:
                # Exact same mesh shortcut
                d_gp_key = (r_eid, gp_idx)
                if d_gp_key in donor_history_dict:
                    val = float(donor_history_dict[d_gp_key])
                    elem_h.append(val)
                    result_history_dict[(r_eid, gp_idx)] = val
                    continue

            # 2. Locate host donor element containing (gx, gy)
            bx = max(0, int(gx / bin_size))
            by = max(0, int(gy / bin_size))
            candidates = target_bins.get((bx, by), [])

            best_eid = None
            best_conn = None
            for deid, xmin, xmax, ymin, ymax, conn in candidates:
                if (xmin - 1e-7 <= gx <= xmax + 1e-7) and (ymin - 1e-7 <= gy <= ymax + 1e-7):
                    best_eid = deid
                    best_conn = conn
                    break

            if best_eid is None:
                # Fallback to searching nearest bbox
                best_dist = float("inf")
                for deid, xmin, xmax, ymin, ymax, conn in fallback_bboxes:
                    cx = (xmin + xmax) / 2.0
                    cy = (ymin + ymax) / 2.0
                    dist = (gx - cx)**2 + (gy - cy)**2
                    if dist < best_dist:
                        best_dist = dist
                        best_eid = deid
                        best_conn = conn

            assert best_eid is not None, f"Failed to locate host element for GP at ({gx}, {gy})"

            # 3. Inverse isoparametric mapping: find (xi, eta) in host donor element
            d_vertices = [d_nodes[n] for n in best_conn]
            d_xi, d_eta, conv = inverse_isoparametric_quad(d_vertices, gx, gy)
            if not conv:
                # Clamp coordinates to [-1, 1] if slightly outside due to floating point
                d_xi = max(-1.0, min(1.0, d_xi))
                d_eta = max(-1.0, min(1.0, d_eta))

            # 4. Fetch the 4 donor GP values for this host element
            donor_vals = [float(donor_history_dict.get((best_eid, g), 0.0)) for g in range(1, 5)]

            # 5. Check extrapolation
            is_outside = (abs(d_xi) > Q_GAUSS + 1e-9) or (abs(d_eta) > Q_GAUSS + 1e-9)
            if is_outside:
                extrapolation_count += 1
                dist_out = max(max(0.0, abs(d_xi) - Q_GAUSS), max(0.0, abs(d_eta) - Q_GAUSS))
                if dist_out > max_extrap_dist:
                    max_extrap_dist = dist_out

            # 6. Reconstruct with limiter
            h_raw = reconstruct_gp_history(donor_vals, d_xi, d_eta, limiter_mode="none")
            h_lim = reconstruct_gp_history(donor_vals, d_xi, d_eta, limiter_mode=limiter_mode)

            if h_raw < 0.0:
                negative_prevented_count += 1
            if abs(h_lim - h_raw) > 1e-12:
                clamped_count += 1

            elem_h.append(h_lim)
            result_history_dict[(r_eid, gp_idx)] = h_lim

        result_history[r_eid] = elem_h

    return {
        "status": "TRANSFER_COMPLETE",
        "transferred_history": result_history,
        "transferred_history_dict": result_history_dict,
        "limiter_mode": limiter_mode,
        "num_elements": len(result_history),
        "num_gauss_points": len(result_history_dict),
        "extrapolation_count": extrapolation_count,
        "clamped_count": clamped_count,
        "negative_prevented_count": negative_prevented_count,
        "max_extrapolation_distance": float(max_extrap_dist),
    }

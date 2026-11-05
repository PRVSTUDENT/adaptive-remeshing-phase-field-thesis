#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
anderson_acceleration.py
========================
Limited-memory safeguarded Anderson acceleration (Anderson mixing)
for nonlinear fixed-point iteration: x = g(x).

Applied to the coupled phase-field damage fixed-point sequence:
  Fixed-point residual: r_k = g(d_k) - d_k = d_PDAS - d_k.

Mathematical formulation:
  Given history of iterates {d_i} and residuals {r_i} for i = k - m_k, ..., k:
  Differences:
    Delta d_j = d_{k - m_k + j + 1} - d_{k - m_k + j}
    Delta r_j = r_{k - m_k + j + 1} - r_{k - m_k + j}
  Solve regularized least-squares problem:
    (Delta R^T Delta R + lambda * I) gamma = Delta R^T r_k
  Form accelerated combination:
    d_bar = d_k - sum_{j=0}^{m_k-1} gamma_j * Delta d_j
    r_bar = r_k - sum_{j=0}^{m_k-1} gamma_j * Delta r_j
    d_{k+1}^{cand} = d_bar + beta * r_bar
  Safeguards:
    - Pointwise physical projection: d_{k+1} = clip(d_{k+1}^{cand}, d0, 1.0)
    - Oversized step rejection: if ||d_cand - d_current||_inf > max_step_cap (0.045),
      fall back to safe damped Picard step d_k + beta * r_k before committing to driver.
      This preserves an explicit safety margin below the 0.05 catastrophic rollback threshold.
    - Growth safeguard: if ||r_bar||_2 > 1.50 ||r_k||_2, fall back to damped Picard.
    - Conditioning safeguard: if ||gamma||_2 > gamma_max (200.0) or singular, fall back to damped Picard.
    - Active-set reset: if active set changes topology (|Delta A| > 5), clear history.
"""
from typing import Dict, List, Optional, Tuple
import math


class AndersonAccelerator:
    """
    Safeguarded limited-memory Anderson accelerator for node-resolved field vectors.
    """
    def __init__(
        self,
        memory_depth: int = 2,
        beta: float = 0.85,
        regularization: float = 1e-6,
        gamma_max: float = 200.0,
        max_step_cap: float = 0.045,
    ):
        if memory_depth < 1:
            raise ValueError("memory_depth must be at least 1")
        self.memory_depth = memory_depth
        self.beta = beta
        self.regularization = regularization
        self.gamma_max = gamma_max
        self.max_step_cap = max_step_cap

        # History queues: list of dicts {node: float}
        self.d_history: List[Dict[int, float]] = []
        self.r_history: List[Dict[int, float]] = []

        # Diagnostic counters
        self.accelerations_applied = 0
        self.fallbacks_triggered = 0
        self.resets_triggered = 0

    def reset(self):
        """Clear historical memory buffer."""
        self.d_history.clear()
        self.r_history.clear()
        self.resets_triggered += 1

    def compute_step(
        self,
        d_current: Dict[int, float],
        d_pdas: Dict[int, float],
        d0: Dict[int, float],
        damped_omega: float = 0.85,
        active_set_changed: bool = False,
    ) -> Tuple[Dict[int, float], Dict[str, any]]:
        """
        Computes the next damage iterate using safeguarded Anderson acceleration.

        Parameters:
        -----------
        d_current : Dict[int, float]
            Current damage iterate d_k.
        d_pdas : Dict[int, float]
            Evaluated raw fixed-point output g(d_k) from PDAS solver.
        d0 : Dict[int, float]
            Historical lower bound damage field.
        damped_omega : float
            Relaxation factor for safe damped Picard fallback.
        active_set_changed : bool
            Flag indicating if active set topology changed this iteration.

        Returns:
        --------
        d_next : Dict[int, float]
            Next damage iterate, guaranteed d0[n] <= d_next[n] <= 1.0.
        telemetry : dict
            Diagnostic metrics (acceleration applied, gamma coefficients, residual norm, etc.)
        """
        nodes = sorted(d_current.keys())
        # Intrinsic raw fixed point residual: r_k = g(d_k) - d_k
        r_k = {n: d_pdas[n] - d_current[n] for n in nodes}
        r_k_norm = math.sqrt(sum(r_k[n] ** 2 for n in nodes))
        r_k_inf = max(abs(r_k[n]) for n in nodes)

        # Standard safe damped Picard step
        d_picard = {}
        for n in nodes:
            val = (1.0 - damped_omega) * d_current[n] + damped_omega * d_pdas[n]
            d_picard[n] = min(1.0, max(d0[n], val))
        picard_step = max(abs(d_picard[n] - d_current[n]) for n in nodes)

        # Topology change resets memory
        if active_set_changed:
            self.reset()

        # Update history
        self.d_history.append(d_current)
        self.r_history.append(r_k)

        # Truncate history to depth + 1
        if len(self.d_history) > self.memory_depth + 1:
            self.d_history.pop(0)
            self.r_history.pop(0)

        # Need at least 2 points (1 difference pair) to accelerate
        m_k = len(self.d_history) - 1
        if m_k < 1:
            return d_picard, {
                "accelerated": False,
                "reason": "insufficient_history",
                "m_k": 0,
                "residual_l2": r_k_norm,
                "residual_linf": r_k_inf,
                "gamma": [],
                "gamma_norm": 0.0,
                "proposed_step": picard_step,
                "accepted_step": picard_step,
                "picard_step": picard_step,
            }

        # Build difference matrices: Delta D and Delta R (size N x m_k)
        # Delta d_j = d_{k - m_k + j + 1} - d_{k - m_k + j}
        delta_d = []
        delta_r = []
        for j in range(m_k):
            dd_j = {n: self.d_history[j + 1][n] - self.d_history[j][n] for n in nodes}
            dr_j = {n: self.r_history[j + 1][n] - self.r_history[j][n] for n in nodes}
            delta_d.append(dd_j)
            delta_r.append(dr_j)

        # Form normal equations: (Delta R^T Delta R + lambda * I) gamma = Delta R^T r_k
        A = [[0.0] * m_k for _ in range(m_k)]
        b = [0.0] * m_k

        for i in range(m_k):
            b[i] = sum(delta_r[i][n] * r_k[n] for n in nodes)
            for j in range(m_k):
                dot_ij = sum(delta_r[i][n] * delta_r[j][n] for n in nodes)
                if i == j:
                    dot_ij += self.regularization
                A[i][j] = dot_ij

        # Solve m_k x m_k linear system (m_k <= 3)
        gamma = self._solve_small_system(A, b)

        if gamma is None:
            self.fallbacks_triggered += 1
            return d_picard, {
                "accelerated": False,
                "reason": "singular_least_squares",
                "m_k": m_k,
                "residual_l2": r_k_norm,
                "residual_linf": r_k_inf,
                "gamma": [],
                "gamma_norm": 0.0,
                "proposed_step": 0.0,
                "accepted_step": picard_step,
                "picard_step": picard_step,
            }

        gamma_norm = math.sqrt(sum(g ** 2 for g in gamma))
        if gamma_norm > self.gamma_max:
            # Overfitting / extreme extrapolation safeguard
            self.fallbacks_triggered += 1
            return d_picard, {
                "accelerated": False,
                "reason": f"gamma_norm_exceeded ({gamma_norm:.2f} > {self.gamma_max:.2f})",
                "m_k": m_k,
                "residual_l2": r_k_norm,
                "residual_linf": r_k_inf,
                "gamma": gamma,
                "gamma_norm": gamma_norm,
                "proposed_step": 0.0,
                "accepted_step": picard_step,
                "picard_step": picard_step,
            }

        # Form accelerated iterate
        # d_bar = d_k - sum(gamma_j * delta_d_j)
        # r_bar = r_k - sum(gamma_j * delta_r_j)
        d_bar = dict(d_current)
        r_bar = dict(r_k)
        for j in range(m_k):
            gj = gamma[j]
            for n in nodes:
                d_bar[n] -= gj * delta_d[j][n]
                r_bar[n] -= gj * delta_r[j][n]

        # Candidate accelerated iterate: d_cand = d_bar + beta * r_bar
        d_cand = {}
        for n in nodes:
            val = d_bar[n] + self.beta * r_bar[n]
            d_cand[n] = min(1.0, max(d0[n], val))

        # Proposed accelerated step norm
        cand_step = max(abs(d_cand[n] - d_current[n]) for n in nodes)

        # 1. Predicted mixed residual norm safeguard: ||r_bar|| should not blow up relative to ||r_k||
        r_bar_norm = math.sqrt(sum(r_bar[n] ** 2 for n in nodes))
        if r_k_norm > 0 and r_bar_norm > 1.5 * r_k_norm:
            self.fallbacks_triggered += 1
            return d_picard, {
                "accelerated": False,
                "reason": f"predicted_residual_growth ({r_bar_norm:.4e} > 1.5 * {r_k_norm:.4e})",
                "m_k": m_k,
                "residual_l2": r_k_norm,
                "residual_linf": r_k_inf,
                "gamma": gamma,
                "gamma_norm": gamma_norm,
                "proposed_step": cand_step,
                "accepted_step": picard_step,
                "picard_step": picard_step,
            }

        # 2. Oversized step rejection safeguard:
        # If the proposed Anderson step exceeds max_step_cap (0.045), reject it BEFORE committing
        # and fall back safely to damped Picard. This prevents triggering the 0.05 catastrophic rollback.
        if cand_step > self.max_step_cap:
            self.fallbacks_triggered += 1
            return d_picard, {
                "accelerated": False,
                "reason": f"oversized_step ({cand_step:.4e} > {self.max_step_cap:.4e})",
                "m_k": m_k,
                "residual_l2": r_k_norm,
                "residual_linf": r_k_inf,
                "gamma": gamma,
                "gamma_norm": gamma_norm,
                "proposed_step": cand_step,
                "accepted_step": picard_step,
                "picard_step": picard_step,
            }

        # All safeguards passed: accept accelerated step
        self.accelerations_applied += 1
        return d_cand, {
            "accelerated": True,
            "reason": "success",
            "m_k": m_k,
            "residual_l2": r_k_norm,
            "residual_linf": r_k_inf,
            "gamma": gamma,
            "gamma_norm": gamma_norm,
            "proposed_step": cand_step,
            "accepted_step": cand_step,
            "picard_step": picard_step,
        }

    @staticmethod
    def _solve_small_system(A: List[List[float]], b: List[float]) -> Optional[List[float]]:
        """Solves m x m linear system for m in {1, 2, 3} using Cramer's rule."""
        m = len(b)
        if m == 1:
            if abs(A[0][0]) < 1e-15:
                return None
            return [b[0] / A[0][0]]
        elif m == 2:
            det = A[0][0] * A[1][1] - A[0][1] * A[1][0]
            if abs(det) < 1e-15:
                return None
            x0 = (b[0] * A[1][1] - b[1] * A[0][1]) / det
            x1 = (A[0][0] * b[1] - A[1][0] * b[0]) / det
            return [x0, x1]
        elif m == 3:
            def det3(M):
                return (
                    M[0][0] * (M[1][1] * M[2][2] - M[1][2] * M[2][1])
                    - M[0][1] * (M[1][0] * M[2][2] - M[1][2] * M[2][0])
                    + M[0][2] * (M[1][0] * M[2][1] - M[1][1] * M[2][0])
                )

            detA = det3(A)
            if abs(detA) < 1e-15:
                return None

            # Matrix with column 0 replaced by b
            A0 = [
                [b[0], A[0][1], A[0][2]],
                [b[1], A[1][1], A[1][2]],
                [b[2], A[2][1], A[2][2]]
            ]
            # Matrix with column 1 replaced by b
            A1 = [
                [A[0][0], b[0], A[0][2]],
                [A[1][0], b[1], A[1][2]],
                [A[2][0], b[2], A[2][2]]
            ]
            # Matrix with column 2 replaced by b
            A2 = [
                [A[0][0], A[0][1], b[0]],
                [A[1][0], A[1][1], b[1]],
                [A[2][0], A[2][1], b[2]]
            ]

            x0 = det3(A0) / detA
            x1 = det3(A1) / detA
            x2 = det3(A2) / detA
            return [x0, x1, x2]
        return None

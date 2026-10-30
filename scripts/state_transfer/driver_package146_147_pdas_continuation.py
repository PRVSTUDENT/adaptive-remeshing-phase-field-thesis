# -*- coding: utf-8 -*-
"""
driver_package146_147_pdas_continuation.py
Mode-I Method C: Alternating Primal-Dual Active Set (PDAS) Solver and Abaqus Continuation Controller.
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Solves the coupled re-equilibration and continuation problem between mechanical displacement u
and phase-field damage d subject to strict damage irreversibility:
    d(x) >= d0(x) for all x in Omega.

Key Formulation Features:
1. Active-Set Decoupling (Fixing Package 142 Clamping Defect):
   Partition receiver nodes into:
     - Active set A = { i : d_i <= d0_i }: clamped to d_i = d0_i via Dirichlet cards (no healing).
     - Inactive set I = { i : d_i > d0_i }: free to evolve, driven by strain energy psi_e^+.
2. Committed Donor State Preservation Across Re-Equilibration Iterations:
   Guarantees that intermediate un-converged Abaqus steps cannot ratchet up or corrupt
   the committed donor history H0. The driver strictly enforces H_k(x) = max(H0(x), psi_e^+(x))
   and re-injects authentic baseline solution initial conditions.
3. Discrete Phase Subproblem and Canonical KKT Complementarity:
   (K_d(H)) d = f_d(H) + lambda subject to d >= d0, lambda >= 0, lambda * (d - d0) = 0.
   Canonical KKT residual: r_i = (K_d d - f_d)_i.
   Multiplier: lambda_i = r_i on A, lambda_i = 0 on I.
   PDAS criterion: node i in A if d_i - c * lambda_i <= d0_i.
4. Abaqus Iteration Interface:
   - Generates decoupled active-set boundary cards per subproblem iteration.
   - Generates candidate PBS wrappers; actual delivery qualification is separate.
   - Parses authentic Abaqus `.sta`, `.dat`, `.odb`, and `uel_energy_balance.csv` outputs.
   - Drives outer coupled mechanical-phase iteration loop to convergence.
5. Stage C1-1 Multi-Gate Acceptance:
   - Reaction force continuity: |Delta RF2| / RF2_donor <= 5%
   - Energy continuity: |Delta Etot| / Etot_donor <= 2%
   - Strict irreversibility: min(d - d0) >= -1e-6
   - Physical phase bounds: 0 <= d <= 1
"""

from __future__ import print_function, division
import os
import sys
import math
import json
import gzip
import shutil
import hashlib
import csv
import re
import subprocess
import time
import signal
from pathlib import Path
from collections import defaultdict

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.c3_int_to_c4_spatial_mapping import (
    Mesh2D, QUAD_GP_LOCAL, quad_shape_functions, quad_physical_point
)

# Phase field parameters for Mode-I Pandey-Kumar specimen
GC_DEFAULT = 0.0027          # kN/mm (Griffith critical energy release rate)
L0_DEFAULT = 0.0075          # mm (phase-field length scale)
E_MODULUS = 210.0            # kN/mm^2 (Young's modulus)
NU_POISSON = 0.3             # Poisson's ratio
K_STIFFNESS_RES = 1e-7       # Residual stiffness factor

# Acceptance thresholds
GATE_FORCE_TOL = 0.05        # 5% max force jump
GATE_ENERGY_TOL = 0.02       # 2% max raw total energy jump
HEALING_TOL = 1e-6           # Inadmissible healing threshold
DAT_DAMAGE_RECOVERY_TOL = 1e-8  # Formatted ASCII .dat node text tolerance (8 significant digits)

# Frozen production UEL SHA-256
FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

# The frozen UEL uses perimeter order, unlike the spatial mapper's row order.
A_GP = 1.0 / math.sqrt(3.0)
UEL_GP_LOCAL = [(-A_GP, -A_GP), (A_GP, -A_GP),
                (A_GP, A_GP), (-A_GP, A_GP)]


def validate_damage(values, expected=None):
    if not values or (expected is not None and set(values) != set(expected)):
        raise ValueError('FAIL_CLOSED: incomplete or unexpected damage node coverage')
    if any(not math.isfinite(v) or not 0.0 <= v <= 1.0 for v in values.values()):
        raise ValueError('FAIL_CLOSED: nonfinite or out-of-bounds damage')


def shape_gradients(vertices, xi, eta):
    dx = [-.25*(1-eta), .25*(1-eta), .25*(1+eta), -.25*(1+eta)]
    de = [-.25*(1-xi), -.25*(1+xi), .25*(1+xi), .25*(1-xi)]
    a = sum(v[0]*d for v, d in zip(vertices, dx))
    b = sum(v[1]*d for v, d in zip(vertices, dx))
    c = sum(v[0]*d for v, d in zip(vertices, de))
    d = sum(v[1]*q for v, q in zip(vertices, de))
    det = a*d-b*c
    if not math.isfinite(det) or det <= 0:
        raise ValueError('FAIL_CLOSED: nonpositive element Jacobian')
    return det, [(d*x-b*y)/det for x, y in zip(dx, de)], [
        (-c*x+a*y)/det for x, y in zip(dx, de)]


def driving_history(mesh, displacement, baseline):
    """Exact frozen UEL POS_M, reconstructed from an authentic mechanical endpoint.

    Unconverged outer iterates never become a committed history baseline.
    """
    expected = {(e, g) for e in mesh.elements for g in range(1, 5)}
    if set(baseline) != expected or set(displacement) != set(mesh.nodes):
        raise ValueError('FAIL_CLOSED: incomplete mechanical/history coverage')
    if any(not math.isfinite(v) or v < 0 for v in baseline.values()):
        raise ValueError('FAIL_CLOSED: invalid history baseline')
    if any(len(u) != 2 or not all(math.isfinite(x) for x in u)
           for u in displacement.values()):
        raise ValueError('FAIL_CLOSED: invalid displacement')
    lam = E_MODULUS*NU_POISSON/((1+NU_POISSON)*(1-2*NU_POISSON))
    mu = E_MODULUS/(2*(1+NU_POISSON))
    result = {}
    for eid, conn in mesh.elements.items():
        vertices = [mesh.nodes[n] for n in conn]
        for g, (xi, eta) in enumerate(UEL_GP_LOCAL, 1):
            _, gx, gy = shape_gradients(vertices, xi, eta)
            e11 = sum(x*displacement[n][0] for n, x in zip(conn, gx))
            e22 = sum(y*displacement[n][1] for n, y in zip(conn, gy))
            e12 = .5*sum(y*displacement[n][0]+x*displacement[n][1]
                          for n, x, y in zip(conn, gx, gy))
            psi = .5*lam*max(0., e11+e22)**2 + mu*(e11**2+e22**2+2*e12**2)
            result[eid, g] = max(baseline[eid, g], psi)
    return result


class PDASReEquilibrationSolver(object):
    """
    Alternating Primal-Dual Active Set (PDAS) solver for coupled mechanical and phase-field
    state transfer re-equilibration on the receiver mesh.
    """

    def __init__(self, receiver_mesh, d0_nodal, h0_gp,
                 gc=GC_DEFAULT, l0=L0_DEFAULT, c_penalty=1.0,
                 max_iter=30, tol_d=1e-5, tol_res=1e-4):
        self.mesh = receiver_mesh
        self.d0_nodal = {int(k): float(v) for k, v in d0_nodal.items()}
        validate_damage(self.d0_nodal, receiver_mesh.nodes)
        self.h0_gp = {tuple(k) if isinstance(k, (list, tuple)) else k: float(v) for k, v in h0_gp.items()}
        if set(self.h0_gp) != {(e, g) for e in receiver_mesh.elements for g in range(1, 5)}:
            raise ValueError('FAIL_CLOSED: incomplete history coverage')
        if any(not math.isfinite(v) or v < 0 for v in self.h0_gp.values()):
            raise ValueError('FAIL_CLOSED: invalid history baseline')
        if any(not math.isfinite(v) or v <= 0 for v in (gc, l0, c_penalty, tol_d, tol_res)):
            raise ValueError('Invalid phase solver parameters')
        self.gc = gc
        self.l0 = l0
        self.c_penalty = c_penalty
        self.max_iter = max_iter
        self.tol_d = tol_d
        self.tol_res = tol_res

        # Working fields
        self.d_nodal = dict(self.d0_nodal)
        self.h_gp = dict(self.h0_gp)
        self.active_set = set(self.d0_nodal.keys())  # Start fully active (Stage A: all clamped to d0)
        self.inactive_set = set()
        self.multipliers = {n: 0.0 for n in self.d0_nodal}

        # Iteration history
        self.history = []

    def enforce_state_preservation(self, mechanical_gp_energy=None):
        """
        Preserves committed donor baseline state across iterations.
        Guarantees H(x) >= H0(x) for all Gauss points, preventing premature ratchet loss.
        """
        for k, h0_val in self.h0_gp.items():
            if mechanical_gp_energy is not None and k in mechanical_gp_energy:
                psi_plus = mechanical_gp_energy[k]
                if not math.isfinite(psi_plus) or psi_plus < 0:
                    raise ValueError('FAIL_CLOSED: invalid driving history')
                self.h_gp[k] = max(h0_val, float(psi_plus))
            else:
                self.h_gp[k] = max(h0_val, self.h_gp.get(k, h0_val))

    def evaluate_element_matrices(self, eid):
        """
        Computes 4x4 element stiffness matrix K_d and 4x1 force vector f_d for phase field:
            K_d,ij = int [ (Gc/l0 + 2H) Ni Nj + Gc l0 gradNi . gradNj ] dOmega
            f_d,i  = int [ 2H Ni ] dOmega
        """
        conn = self.mesh.elements[eid]
        vertices = [self.mesh.nodes[n] for n in conn]

        ke = [[0.0] * 4 for _ in range(4)]
        fe = [0.0] * 4

        # 2x2 Gauss integration
        for gp_idx, (xi, eta) in enumerate(UEL_GP_LOCAL):
            # Bilinear shape functions N_i
            n_vals = quad_shape_functions(xi, eta)

            # Local derivatives dN/dxi, dN/deta
            dn_dxi = [
                -0.25 * (1.0 - eta),
                 0.25 * (1.0 - eta),
                 0.25 * (1.0 + eta),
                -0.25 * (1.0 + eta),
            ]
            dn_deta = [
                -0.25 * (1.0 - xi),
                -0.25 * (1.0 + xi),
                 0.25 * (1.0 + xi),
                 0.25 * (1.0 - xi),
            ]

            # Jacobian J
            j11 = sum(dn * v[0] for dn, v in zip(dn_dxi, vertices))
            j12 = sum(dn * v[1] for dn, v in zip(dn_dxi, vertices))
            j21 = sum(dn * v[0] for dn, v in zip(dn_deta, vertices))
            j22 = sum(dn * v[1] for dn, v in zip(dn_deta, vertices))

            det_j = j11 * j22 - j12 * j21
            if not math.isfinite(det_j) or det_j <= 0:
                raise ValueError('FAIL_CLOSED: nonpositive element Jacobian')

            # Inverse Jacobian for physical derivatives dN/dx, dN/dy
            dn_dx = [(j22 * dxi - j12 * deta) / det_j for dxi, deta in zip(dn_dxi, dn_deta)]
            dn_dy = [(-j21 * dxi + j11 * deta) / det_j for dxi, deta in zip(dn_dxi, dn_deta)]

            # History value at GP (enforcing baseline lower bound)
            gp_key = (eid, gp_idx + 1)
            h_val = self.h_gp[gp_key]
            if not math.isfinite(h_val) or h_val < 0:
                raise ValueError('FAIL_CLOSED: invalid history')

            w_int = det_j  # Gauss weight = 1.0 * 1.0 = 1.0

            # Accumulate K_e and f_e
            coef_mass = (self.gc / self.l0 + 2.0 * h_val) * w_int
            coef_diff = (self.gc * self.l0) * w_int
            coef_rhs = (2.0 * h_val) * w_int

            for i in range(4):
                fe[i] += coef_rhs * n_vals[i]
                for j in range(4):
                    ke[i][j] += (
                        coef_mass * n_vals[i] * n_vals[j] +
                        coef_diff * (dn_dx[i] * dn_dx[j] + dn_dy[i] * dn_dy[j])
                    )

        return ke, fe

    def assemble_system(self):
        """
        Assembles global stiffness diagonals and off-diagonals, and RHS vector for receiver mesh.
        Returns diag dict, off_diag dict: (n1, n2) -> val, and rhs dict.
        """
        diag = defaultdict(float)
        off_diag = defaultdict(float)
        rhs = defaultdict(float)

        for eid in self.mesh.elements:
            conn = self.mesh.elements[eid]
            ke, fe = self.evaluate_element_matrices(eid)

            for i, n_i in enumerate(conn):
                rhs[n_i] += fe[i]
                for j, n_j in enumerate(conn):
                    if n_i == n_j:
                        diag[n_i] += ke[i][j]
                    else:
                        off_diag[(n_i, n_j)] += ke[i][j]

        return diag, off_diag, rhs

    def compute_kkt_residuals(self, diag, off_diag, rhs):
        """
        Computes the canonical discrete Euler-Lagrange residual r_i = (K_d d - f_d)_i
        and Lagrange multipliers lambda_i for active-set complementarity.
        Canonical sign convention:
          r_i = (K_d d - f_d)_i
          On active set A: lambda_i = r_i (positive reaction force preventing healing)
          On inactive set I: lambda_i = 0, residual is the unconstrained equation error
        """
        residuals = {}
        for n_i in self.d_nodal:
            val = diag[n_i] * self.d_nodal[n_i] - rhs[n_i]
            residuals[n_i] = val

        for (n_i, n_j), k_val in off_diag.items():
            residuals[n_i] += k_val * self.d_nodal[n_j]

        # Canonical KKT multipliers
        multipliers = {}
        for n_i in self.d_nodal:
            if n_i in self.active_set:
                multipliers[n_i] = residuals[n_i]
            else:
                multipliers[n_i] = 0.0

        return residuals, multipliers

    def step_pdas_iteration(self, diag, off_diag, rhs, omega_sor=1.0):
        """
        Performs one Primal-Dual Active Set (PDAS) partitioned solve and active-set update.
        Active nodes A are pinned to d_i = d0_i.
        Inactive nodes I are updated via projected Gauss-Seidel / SOR relaxation on K_d d = f_d.
        """
        d_prev = dict(self.d_nodal)
        active_prev = set(self.active_set)

        # 1. Update inactive nodes via Gauss-Seidel sweep
        neighbors = defaultdict(list)
        for (i, j), val in off_diag.items():
            neighbors[i].append((j, val))
        for n_i in sorted(self.d_nodal.keys()):
            if n_i in self.active_set:
                self.d_nodal[n_i] = self.d0_nodal[n_i]
            else:
                # Standard residual update
                r_i = diag[n_i] * self.d_nodal[n_i] - rhs[n_i]
                for to_n, k_val in neighbors[n_i]:
                    r_i += k_val * self.d_nodal[to_n]

                if abs(diag[n_i]) > 1e-15:
                    d_corr = -r_i / diag[n_i]
                    d_new = self.d_nodal[n_i] + omega_sor * d_corr
                    # Enforce lower bound d >= d0 and upper bound d <= 1.0
                    self.d_nodal[n_i] = max(self.d0_nodal[n_i], min(1.0, d_new))

        # 2. Evaluate KKT residuals and multipliers
        residuals, multipliers = self.compute_kkt_residuals(diag, off_diag, rhs)
        self.multipliers = multipliers

        # 3. Canonical PDAS active-set update:
        # Node i is active if d_i - c * lambda_i <= d0_i
        # Node i is inactive if d_i - c * lambda_i > d0_i
        new_active = set()
        new_inactive = set()

        for n_i in self.d_nodal:
            d_val = self.d_nodal[n_i]
            lam = residuals[n_i]
            crit = d_val - self.c_penalty * lam
            if crit <= self.d0_nodal[n_i] + 1e-12:
                new_active.add(n_i)
            else:
                new_inactive.add(n_i)

        self.active_set = new_active
        self.inactive_set = new_inactive

        # Compute convergence metrics
        delta_d_max = max(abs(self.d_nodal[n] - d_prev[n]) for n in self.d_nodal)
        active_flips = len(self.active_set.symmetric_difference(active_prev))

        # Complementarity residual: sum(|min(0, lambda)| on A) + sum(|r| on I)
        comp_err = max([abs(min(0.0, residuals[n])) for n in self.active_set] +
                       [abs(residuals[n]) for n in self.inactive_set] + [0.0])

        record = {
            "delta_d_max": delta_d_max,
            "active_flips": active_flips,
            "active_count": len(self.active_set),
            "inactive_count": len(self.inactive_set),
            "comp_err": comp_err,
        }
        self.history.append(record)
        return record

    def run_re_equilibration(self, max_iter=None, mechanical_gp_energy=None):
        """
        Executes complete PDAS re-equilibration loop until active set stabilizes
        and damage change drops below tolerance.
        """
        if max_iter is None:
            max_iter = self.max_iter

        # Ensure donor history baseline is strictly preserved
        self.enforce_state_preservation(mechanical_gp_energy)

        diag, off_diag, rhs = self.assemble_system()

        converged = False
        for it in range(max_iter):
            rec = self.step_pdas_iteration(diag, off_diag, rhs)
            if (rec["active_flips"] == 0 and rec["delta_d_max"] < self.tol_d
                    and rec['comp_err'] <= self.tol_res):
                converged = True
                break

        # Verification of no damage healing
        healing_violation = min((self.d_nodal[n] - self.d0_nodal[n]) for n in self.d_nodal)
        is_admissible = (healing_violation >= -HEALING_TOL) and all(0.0 <= self.d_nodal[n] <= 1.0 for n in self.d_nodal)

        return {
            "converged": converged,
            "iterations": len(self.history),
            "final_record": self.history[-1] if self.history else None,
            "min_damage_change": healing_violation,
            "is_admissible": is_admissible,
            "active_nodes_count": len(self.active_set),
            "inactive_nodes_count": len(self.inactive_set),
            "total_nodes": len(self.d_nodal),
        }

    def generate_active_mask(self):
        """Returns boolean dict: nid -> True if active (clamped), False if inactive (free)."""
        return {n: (n in self.active_set) for n in self.d_nodal}

    def kkt(self, damage, tau_active=1e-9, tau_free=1e-6):
        """Lower-obstacle KKT; no upper-obstacle multiplier is introduced."""
        validate_damage(damage, self.d0_nodal)
        diag, off, rhs = self.assemble_system()
        residual = {n: diag[n]*damage[n]-rhs[n] for n in damage}
        for (i, j), val in off.items():
            residual[i] += val*damage[j]
        if any(not math.isfinite(v) for v in residual.values()):
            raise ValueError('FAIL_CLOSED: nonfinite KKT residual')
        active = {n for n in damage if damage[n]-self.d0_nodal[n] <= 1e-10}
        free = set(damage)-active
        healing = min(damage[n]-self.d0_nodal[n] for n in damage)
        dual = max([max(0., -residual[n]) for n in active]+[0.])
        free_err = max([abs(residual[n]) for n in free]+[0.])
        complementarity = max(abs(residual[n]*(damage[n]-self.d0_nodal[n])) for n in damage)
        return dict(passed=healing >= -HEALING_TOL and dual <= tau_active
                    and free_err <= tau_free and complementarity <= tau_free,
                    active=active, free=free, residual=residual,
                    dual_error=dual, free_error=free_err,
                    complementarity=complementarity, min_delta_d=healing)


class AbaqusPDASIterationController(object):
    """
    Coupled Abaqus-PDAS execution and continuation controller.
    Interfaces between outer PDAS active-set decisions and authentic Abaqus/Standard solver steps.
    """

    def __init__(self, work_dir, model_name="M1_C4_PACKAGE148_STATE_TRANSFER", uel_path=None):
        self.work_dir = Path(work_dir)
        self.model_name = model_name
        self.uel_path = Path(uel_path) if uel_path else (self.work_dir / "f42_mixed_uel.for")
        self.iteration_records = []

    def verify_work_dir_integrity(self):
        """Verifies that working directory contains required master deck, UEL, and initial solution cards."""
        required = [
            self.work_dir / ("%s.inp" % self.model_name),
            self.work_dir / "initial_conditions_solution.inc",
            self.uel_path,
        ]
        for p in required:
            if not p.exists():
                raise RuntimeError("FAIL_CLOSED: Missing required file in work_dir: %s" % p)

        # Bitwise verify frozen UEL
        uel_h = self._compute_sha256(self.uel_path)
        if uel_h != FROZEN_UEL_SHA256:
            raise ValueError("FAIL_CLOSED: Frozen UEL hash mismatch in work_dir: %s" % uel_h)
        return True

    def prepare_subproblem_iteration(self, iter_idx, active_mask, d0_nodal):
        """
        Generates decoupled active_set_boundary_cards.inc for iteration `iter_idx`.
        Clamps ONLY nodes in active_mask (active_mask[nid] == True), leaving inactive nodes
        unconstrained on DOF 3 to allow physically admissible damage evolution.
        """
        active_inc = self.work_dir / "active_set_boundary_cards.inc"
        with open(str(active_inc), "w") as f:
            f.write("** Active Set Dirichlet cards for Abaqus Iteration %d\n" % iter_idx)
            f.write("** Format: node_id, 3, 3, d_value\n")
            clamped_count = 0
            for nid in sorted(d0_nodal.keys()):
                if active_mask.get(nid, True):
                    f.write("%d, 3, 3, %.8f\n" % (nid, d0_nodal[nid]))
                    clamped_count += 1

        # Check committed state preservation: confirm initial_conditions_solution.inc is intact
        sol_inc = self.work_dir / "initial_conditions_solution.inc"
        if not sol_inc.exists() or sol_inc.stat().st_size < 1000:
            raise RuntimeError("FAIL_CLOSED: Missing or truncated initial_conditions_solution.inc")

        return {
            "active_inc_path": active_inc,
            "clamped_nodes_count": clamped_count,
            "free_nodes_count": len(d0_nodal) - clamped_count,
            "total_nodes": len(d0_nodal),
        }

    def build_pbs_wrapper(self, iter_idx, job_name=None, cpus=1, memory_gb=16,
                          walltime="00:15:00", donor_rf2=None, donor_energy=None):
        """
        Generates standard PBS submission script with dual-channel notifications and safe execution traps.
        """
        if job_name is None:
            job_name = "M1_C4_P148_IT%d" % iter_idx
        if not re.match(r'^[A-Za-z][A-Za-z0-9_]{0,63}$', job_name):
            raise ValueError('Unsafe job name')
        if cpus != 1 or not 1 <= memory_gb <= 16 or walltime != '00:15:00':
            raise ValueError('Unreviewed execution resources')
        if donor_rf2 is None or donor_energy is None:
            raise ValueError('Explicit authenticated donor metrics required')
        StageC1GateEvaluator(donor_rf2, donor_energy)

        pbs_path = self.work_dir / ("submit_%s.pbs" % job_name)
        with open(str(pbs_path), "w", newline='\n') as f:
            f.write("#!/bin/bash\n")
            f.write("#PBS -N %s\n" % job_name)
            f.write("#PBS -l select=1:ncpus=%d:mem=%dgb\n" % (cpus, memory_gb))
            f.write("#PBS -l walltime=%s\n" % walltime)
            f.write("#PBS -q entry_imfdfkmq\n")
            f.write("#PBS -m abe\n")
            f.write("#PBS -M pr21vyci@mailserver.tu-freiberg.de\n")
            f.write("\n")
            f.write("set -euo pipefail\n")
            f.write('cd "${PBS_O_WORKDIR:?}"\n')
            f.write('source "$HOME/projects/adaptive-remeshing/scripts/hpc/notifications/job_notifications.sh"\n')
            f.write("notification_load_config\n")
            f.write("notification_install_terminal_trap\n")
            f.write('notify_start "${PBS_JOBNAME:?}"\n')
            f.write("\n")
            f.write("# Load Abaqus environment\n")
            f.write("module load abaqus/2023 intel/2024.2\n")
            f.write('repo="$HOME/projects/adaptive-remeshing"\n')
            f.write('python3 "$repo/scripts/state_transfer/driver_package146_147_pdas_continuation.py" '
                    '--package "$PBS_O_WORKDIR" --output "$PBS_O_WORKDIR/coupled_${PBS_JOBID:?}" '
                    '--extractor "$repo/scripts/validation/extract_package148_iteration.py" '
                    '--donor-rf2 %.17g --donor-energy %.17g --memory-gb %d\n' %
                    (donor_rf2, donor_energy, memory_gb))

        return pbs_path

    def parse_subproblem_results(self, run_dir=None, job_name=None):
        """
        Parses Abaqus outputs from completed subproblem:
          - `.sta`: confirmed Exit 0 and increments
          - `uel_energy_balance.csv`: elastic, fracture, and total energies
          - `.dat`: reaction force RF2 at RP, displacement u_RP, and nodal U3 damage
        """
        target_dir = Path(run_dir) if run_dir else self.work_dir
        jname = job_name if job_name else self.model_name

        sta_file = target_dir / ("%s.sta" % jname)
        csv_file = target_dir / "uel_energy_balance.csv"
        dat_file = target_dir / ("%s.dat" % jname)

        results = {
            "exit_status": None,
            "increments": None,
            "rf2_kN": None,
            "uRP_mm": None,
            "e_elas_kNmm": None,
            "e_frac_kNmm": None,
            "e_total_kNmm": None,
            "nodal_damage": {},
            "dat_parsed": False,
        }

        # 1. Parse STA file
        if sta_file.exists():
            with open(str(sta_file), "r") as f:
                content = f.read()
                if "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" in content:
                    results["exit_status"] = 0
                for line in content.splitlines():
                    parts = line.split()
                    if len(parts) >= 8 and parts[0].isdigit() and parts[1].isdigit():
                        results["increments"] = int(parts[1])

        # 2. Parse UEL energy balance CSV
        if csv_file.exists():
            with open(str(csv_file), "r") as f:
                last_line = ""
                for line in f:
                    if line.strip():
                        last_line = line.strip()
                if last_line and not last_line.startswith("Step"):
                    parts = [p.strip() for p in last_line.split(",")]
                    if len(parts) >= 7:
                        results["e_elas_kNmm"] = float(parts[4])
                        results["e_frac_kNmm"] = float(parts[5])
                        results["e_total_kNmm"] = float(parts[6])

        # 3. Parse DAT file
        if dat_file.exists():
            results["dat_parsed"] = True
            with open(str(dat_file), "r") as f:
                in_u_table = False
                in_rf_table = False
                for line in f:
                    if "NODE FOOT-" in line and "U1" in line and "U2" in line and "U3" in line:
                        in_u_table = True
                        continue
                    if in_u_table:
                        line_s = line.strip()
                        if not line_s or "NOTE" in line_s or line_s.startswith("-"):
                            continue
                        if line_s.startswith("MAXIMUM") or line_s.startswith("MINIMUM"):
                            in_u_table = False
                            continue
                        parts = line_s.split()
                        if len(parts) >= 4 and parts[0].isdigit():
                            nid = int(parts[0])
                            u1 = float(parts[1])
                            u2 = float(parts[2])
                            u3 = float(parts[3])
                            results["nodal_damage"][nid] = u3
                            if nid == 999999:
                                results["uRP_mm"] = u2

                    if "NODE FOOT-" in line and "RF1" in line and "RF2" in line:
                        in_rf_table = True
                        continue
                    if in_rf_table:
                        parts = line.strip().split()
                        if len(parts) >= 3 and parts[0] == "999999":
                            results["rf2_kN"] = float(parts[2])
                            in_rf_table = False

        return results

    def update_active_set_from_abaqus(self, nodal_damage, d0_nodal, previous_active_set,
                                     tolerance=1e-6, residuals=None):
        """
        Updates active and inactive node sets based on real Abaqus nodal damage field d_i:
          - Active set A: nodes where d_i <= d0_i + tol (driving force wants healing -> clamp to d0)
          - Inactive set I: nodes where d_i > d0_i + tol (driving force exceeds resistance -> free)
        """
        validate_damage(d0_nodal)
        validate_damage(nodal_damage, d0_nodal)
        if residuals is None or set(residuals) != set(d0_nodal) or any(
                not math.isfinite(v) for v in residuals.values()):
            raise ValueError('Complete signed phase residuals required for active-set update')
        new_active = set()
        new_inactive = set()
        delta_d_max = 0.0
        healing_violation = 0.0

        for nid, d0_val in d0_nodal.items():
            d_val = nodal_damage[nid]
            delta_d = d_val - d0_val
            delta_d_max = max(delta_d_max, abs(delta_d))

            if delta_d < healing_violation:
                healing_violation = delta_d

            if d_val-residuals[nid] <= d0_val+tolerance:
                new_active.add(nid)
            else:
                new_inactive.add(nid)

        active_flips = len(new_active.symmetric_difference(previous_active_set))

        return {
            "new_active_set": new_active,
            "new_inactive_set": new_inactive,
            "active_count": len(new_active),
            "inactive_count": len(new_inactive),
            "active_flips": active_flips,
            "delta_d_max": delta_d_max,
            "healing_violation": healing_violation,
            "no_healing": (healing_violation >= -HEALING_TOL),
        }

    def _compute_sha256(self, p):
        h = hashlib.sha256()
        with open(str(p), "rb") as f:
            for b in iter(lambda: f.read(1048576), b""):
                h.update(b)
        return h.hexdigest().upper()


class StageC1GateEvaluator(object):
    """
    Evaluates Stage C1-1 acceptance gates between donor (Package 146) and receiver (Package 147/148).
    """

    def __init__(self, donor_rf2=0.1873079389333725, donor_energy=0.00021270454):
        if not all(math.isfinite(v) and v > 0 for v in (donor_rf2, donor_energy)):
            raise ValueError('Positive finite donor metrics required')
        self.donor_rf2 = donor_rf2
        self.donor_energy = donor_energy

    def evaluate_gates(self, receiver_rf2, receiver_energy, min_delta_d, damage_max):
        """
        Evaluates physical acceptance criteria:
          1. Reaction force discrepancy: |Delta RF2| / RF2_donor <= 5%
          2. Raw total energy discrepancy: |Delta Etot| / Etot_donor <= 2%
          3. Damage irreversibility: min_delta_d >= -1e-6 (no healing)
          4. Damage bounds: 0.0 <= damage_max <= 1.0
        """
        if not all(math.isfinite(v) for v in
                   (receiver_rf2, receiver_energy, min_delta_d, damage_max)):
            raise ValueError('FAIL_CLOSED: nonfinite gate inputs')
        delta_rf2 = abs(receiver_rf2 - self.donor_rf2) / abs(self.donor_rf2)
        delta_energy = abs(receiver_energy - self.donor_energy) / abs(self.donor_energy)
        no_healing = (min_delta_d >= -HEALING_TOL)
        bounds_valid = (0.0 <= damage_max <= 1.0 and receiver_energy >= 0.0)

        pass_rf2 = (delta_rf2 <= GATE_FORCE_TOL)
        pass_energy = (delta_energy <= GATE_ENERGY_TOL)
        pass_all = pass_rf2 and pass_energy and no_healing and bounds_valid

        return {
            "pass_all": pass_all,
            "delta_rf2_rel": delta_rf2,
            "pass_rf2": pass_rf2,
            "delta_energy_rel": delta_energy,
            "pass_energy": pass_energy,
            "min_delta_d": min_delta_d,
            "no_healing": no_healing,
            "damage_max": damage_max,
            "bounds_valid": bounds_valid,
            "thresholds": {
                "max_rf2_rel": GATE_FORCE_TOL,
                "max_energy_rel": GATE_ENERGY_TOL,
                "healing_tol": HEALING_TOL,
            }
        }


def split_keyword_blocks(template):
    r"""Split an Abaqus input deck into keyword blocks.

    A keyword block starts with a keyword line ('*' followed by a non-'*').
    Preceding comments/blank lines before the first keyword are preserved in the
    first block. Replaces zero-width lookahead re.split(r'(?m)(?=^\*(?!\*))', ...)
    which is rejected by Python 3.6 with ValueError: split() requires a non-empty pattern match.
    """
    blocks = []
    current = []
    for line in template.splitlines(True):
        if line.startswith('*') and not line.startswith('**'):
            if current:
                blocks.append(''.join(current))
                current = []
        current.append(line)
    if current:
        blocks.append(''.join(current))
    return blocks


class CoupledAbaqusRuntime(object):
    """Bounded serial mechanical/phase solves inside ONE PBS allocation.

    Every solve has a distinct directory/job and a fresh process. No qsub, retry,
    restart from unconverged history, or modification of the frozen package.
    The phase operator and driving energy reproduce the frozen UEL equations.
    """

    def __init__(self, package, output, extractor, donor_rf2, donor_energy,
                 abaqus='abaqus', max_outer=25, max_phase=20, timeout=7200,
                 memory_gb=16, runner=None):
        self.package = Path(package).resolve()
        self.output = Path(output).resolve()
        self.extractor = Path(extractor).resolve()
        self.evaluator = StageC1GateEvaluator(donor_rf2, donor_energy)
        if not 2 <= max_outer <= 30 or not 1 <= max_phase <= 30:
            raise ValueError('Unreviewed iteration bounds')
        if not 1 <= timeout <= 25200 or not 1 <= memory_gb <= 16:
            raise ValueError('Unreviewed runtime resources')
        self.abaqus, self.max_outer, self.max_phase = abaqus, max_outer, max_phase
        self.timeout, self.memory_gb = timeout, memory_gb
        self.runner = runner or self._run_abaqus
        self.records = []

    def load(self):
        ctrl = AbaqusPDASIterationController(self.package)
        ctrl.verify_work_dir_integrity()
        if not self.extractor.is_file():
            raise ValueError('Missing endpoint extractor')
        manifest = json.loads((self.package/'PACKAGE_MANIFEST.json').read_text())
        if manifest.get('history_gp_order') != 'MAPPER_ROW_FROM_UEL_PERIMETER':
            raise ValueError('Unreviewed legacy GP ordering; regenerate a distinct candidate revision')
        for name, digest in manifest['files'].items():
            if Path(name).name != name or ctrl._compute_sha256(self.package/name) != digest:
                raise ValueError('Frozen package hash mismatch: '+name)
        if len(manifest.get('source_hashes', {})) != 4:
            raise ValueError('Incomplete donor/source bindings')
        if len(manifest.get('runtime_source_hashes', {})) != 4:
            raise ValueError('Incomplete coupled runtime source bindings')
        for name, digest in dict(manifest['source_hashes'], **manifest['runtime_source_hashes']).items():
            source = (REPO_ROOT/name).resolve()
            if (REPO_ROOT not in source.parents or
                    ctrl._compute_sha256(source) != digest):
                raise ValueError('Donor/source hash mismatch: '+name)
        self.source_hashes = {str(p): ctrl._compute_sha256(p) for p in
                              [self.extractor, Path(__file__)] +
                              [self.package/n for n in manifest['files']]}
        self.source_hashes.update(manifest['source_hashes'])
        self.source_hashes.update(manifest['runtime_source_hashes'])
        deck = self.package/(ctrl.model_name+'.inp')
        self.template = deck.read_text()
        self.mesh = Mesh2D.from_inp(deck)
        with (self.package/'nodal_phase_field_initial.csv').open() as f:
            rows = list(csv.DictReader(f))
        self.d0 = {int(r['node_id']): float(r['d0']) for r in rows}
        if len(rows) != len(self.d0):
            raise ValueError('Duplicate damage baseline node')
        validate_damage(self.d0, self.mesh.nodes)
        with (self.package/'d_lower_bounds.csv').open() as f:
            rows = list(csv.DictReader(f))
        # These columns were generated in the spatial mapper's row order.
        # Convert once to frozen UEL perimeter order, explicitly swapping 3/4.
        self.h0 = {(int(r['element_id']), gp): float(r['h0_'+str(col)])
                   for r in rows for gp, col in [(1, 1), (2, 2), (3, 4), (4, 3)]}
        if len(rows) != len(self.mesh.elements):
            raise ValueError('Duplicate/missing baseline elements')
        driving_history(self.mesh, {n: (0., 0.) for n in self.mesh.nodes}, self.h0)
        self.target_u = float(manifest['donor']['target_u_rp_mm'])
        if not math.isfinite(self.target_u) or self.target_u <= 0:
            raise ValueError('Invalid target load')
        self.solver = PDASReEquilibrationSolver(self.mesh, self.d0, self.h0)

    def _deck(self, role, damage, active, displacement, history):
        validate_damage(damage, self.d0)
        # Split Abaqus keyword blocks; remove old BC/includes, retaining all mesh,
        # material and sets. Phase has every physical displacement prescribed, so
        # remove MPC equations to avoid dependent-DOF overconstraint.
        blocks = split_keyword_blocks(self.template)
        prefix = []
        for block in blocks:
            key = block.split('\n', 1)[0].strip().lower()
            if key.startswith('*step'):
                break
            if key.startswith(('*boundary', '*include')):
                continue
            if role == 'phase' and key.startswith('*equation'):
                continue
            prefix.append(block)
        cards = [''.join(prefix), '*Initial Conditions, type=SOLUTION\n']
        for eid in sorted(self.mesh.elements):
            cards.append('%d, 0, 0, 0, 0, 0, 0, 0\n' % eid)
            cards.append('0, ' + ', '.join('%.17g' % history[eid, g] for g in range(1, 5)) + ', 0, 0, 0\n0, 0, 0\n')
        cards += ['*Amplitude, name=FIXED\n0., 1., 1., 1.\n',
                  '*Step, name=C1-1-ReEquil, nlgeom=NO, inc=1\n',
                  '*Static\n1., 1., 1., 1.\n*Boundary, amplitude=FIXED\n']
        if role == 'mechanical':
            cards += ['N_BOTTOM, 2, 2, 0.\nN_PIN, 1, 1, 0.\nN_TOP, 1, 1, 0.\n',
                      'N_RP, 1, 1, 0.\nN_RP, 2, 2, %.17g\n' % self.target_u]
            prescribed = damage
        else:
            for n in sorted(self.mesh.nodes):
                cards += ['%d, 1, 1, %.17g\n%d, 2, 2, %.17g\n' %
                          (n, displacement[n][0], n, displacement[n][1])]
            prescribed = {n: self.d0[n] for n in active}
        cards += ['%d, 3, 3, %.17g\n' % (n, prescribed[n]) for n in sorted(prescribed)]
        cards += ['*Output, field, frequency=1\n*Node Output\nU, RF\n',
                  '*Element Output, elset=umatelem\nSDV\n',
                  '*Node Print, frequency=1\nU\n',
                  '*End Step\n']
        return ''.join(cards)

    def _command(self, args, directory, logfile):
        remaining = self.deadline-time.monotonic()
        if remaining <= 0:
            raise RuntimeError('Coupled runtime deadline exceeded')
        with logfile.open('x') as log:
            # Linux PBS: isolate the launcher and solver descendants so a bounded
            # timeout terminates this solve's process group, not other user jobs.
            proc = subprocess.Popen(args, cwd=str(directory), stdout=log,
                                    stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                    start_new_session=(os.name == 'posix'))
            try:
                code = proc.wait(timeout=remaining)
            except subprocess.TimeoutExpired:
                if os.name == 'posix':
                    os.killpg(proc.pid, signal.SIGKILL)
                else:
                    proc.kill()
                proc.wait()
                raise
            if code:
                raise subprocess.CalledProcessError(code, args)

    def _run_abaqus(self, directory, job, role):
        self._command([self.abaqus, 'job='+job, 'input='+job+'.inp',
                       'user=f42_mixed_uel.for', 'cpus=1', 'memory=%d gb' % self.memory_gb,
                       'interactive'], directory, directory/'solver.stdout.txt')
        sta = directory/(job+'.sta')
        if not sta.is_file() or 'THE ANALYSIS HAS COMPLETED SUCCESSFULLY' not in sta.read_text():
            raise RuntimeError('Abaqus did not complete successfully')
        self._command([self.abaqus, 'python', str(self.extractor),
                       '--odb', str(directory/(job+'.odb')), '--output', str(directory/'endpoint.json'),
                       '--physical-nodes', str(len(self.mesh.nodes)),
                       '--physical-elements', str(len(self.mesh.elements))],
                      directory, directory/'extractor.stdout.txt')
        endpoint = directory/'endpoint.json'
        if not endpoint.is_file():
            raise RuntimeError('Missing endpoint extraction')
        result = json.loads(endpoint.read_text())
        ctrl = AbaqusPDASIterationController(directory)
        if (result.get('extractor_sha256') != ctrl._compute_sha256(self.extractor).lower()
                or result.get('odb_sha256') != ctrl._compute_sha256(directory/(job+'.odb')).lower()):
            raise ValueError('Endpoint extraction provenance mismatch')
        return result

    def solve(self, outer, inner, role, damage, active, displacement, history):
        if time.monotonic() >= self.deadline:
            raise RuntimeError('Coupled runtime deadline exceeded')
        job = 'P148_%02d_%02d_%s' % (outer, inner, role)
        directory = self.output/job
        directory.mkdir()  # Once only. Existing evidence is never overwritten.
        shutil.copyfile(str(self.package/'f42_mixed_uel.for'), str(directory/'f42_mixed_uel.for'))
        text = self._deck(role, damage, active, displacement, history)
        (directory/(job+'.inp')).write_text(text)
        result = self.runner(directory, job, role)
        expected = set(self.mesh.nodes)
        if result.get('schema') != 1 or result.get('increment') != 1 or result.get('step_time') != 1.0:
            raise ValueError('Incomplete/wrong Abaqus endpoint')
        rows = result['nodes']
        fields = {int(r[0]): tuple(float(x) for x in r[1:]) for r in rows}
        if len(fields) != len(rows) or set(fields) != expected:
            raise ValueError('Incorrect endpoint node coverage')
        if any(len(v) not in (2, 3) for v in fields.values()):
            raise ValueError('Invalid node displacement dimension')
        if role == 'mechanical':
            u = {n: v[:2] for n, v in fields.items()}
            if all(len(v) >= 3 for v in fields.values()):
                d = {n: v[2] for n, v in fields.items()}
                validate_damage(d, self.d0)
                if max(abs(d[n]-damage[n]) for n in d) > DAT_DAMAGE_RECOVERY_TOL:
                    raise ValueError('Prescribed mechanical damage not retained')
            else:
                d = dict(damage)
            if any(not all(math.isfinite(x) for x in v) for v in u.values()):
                raise ValueError('Nonfinite displacement output')
            if abs(float(result['rp_u2'])-self.target_u) > 1e-10:
                raise ValueError('Wrong endpoint displacement')
            if not math.isfinite(float(result['rf2_kN'])):
                raise ValueError('Nonfinite reaction force')
        else:
            if not all(len(v) >= 3 for v in fields.values()):
                raise ValueError('Missing phase-field damage in phase solve endpoint')
            d = {n: v[2] for n, v in fields.items()}
            u = {n: v[:2] for n, v in fields.items()}
            validate_damage(d, self.d0)
            if any(not all(math.isfinite(x) for x in v) for v in u.values()):
                raise ValueError('Nonfinite displacement output')
            if max(abs(u[n][i]-displacement[n][i]) for n in u for i in (0, 1)) > 1e-10:
                raise ValueError('Fixed mechanical displacement changed during phase solve')
            if any(abs(d[n]-self.d0[n]) > DAT_DAMAGE_RECOVERY_TOL for n in active):
                raise ValueError('Active phase constraint not retained')
        # Hash each command's exact input and endpoint (without large solver files).
        record = dict(job=job, role=role, input_sha256=hashlib.sha256(text.encode()).hexdigest(),
                      endpoint=result)
        (directory/'receipt.json').write_text(json.dumps(record, allow_nan=False, indent=2))
        return d, u, result

    def _write_report(self, status, **extra):
        report = dict(schema=1, status=status, scientific_acceptance=False,
                      sources=self.source_hashes, iterations=self.records, **extra)
        tmp = self.output/'runtime_report.tmp'
        tmp.write_text(json.dumps(report, allow_nan=False, indent=2))
        tmp.replace(self.output/'runtime_report.json')
        return report

    def run(self):
        self.load()
        self.output.mkdir()  # Fail closed on reruns and preserved run evidence.
        self.deadline = time.monotonic()+self.timeout
        damage, previous_u, previous_h = dict(self.d0), None, None
        previous_d = dict(damage)
        try:
            for outer in range(1, self.max_outer+1):
                damage, u, endpoint = self.solve(outer, 0, 'mechanical', damage,
                                                 set(damage), None, self.h0)
                history = driving_history(self.mesh, u, self.h0)
                self.solver.h_gp = history
                kkt = self.solver.kkt(damage)
                delta_d = max(abs(damage[n]-previous_d[n]) for n in damage)
                delta_u = max(abs(u[n][i]-previous_u[n][i]) for n in u for i in (0, 1)) if previous_u else None
                delta_h = max(abs(history[k]-previous_h[k]) for k in history) if previous_h else None
                self.records.append(dict(outer=outer, delta_d=delta_d, delta_u=delta_u,
                                         delta_h=delta_h, free_error=kkt['free_error'],
                                         dual_error=kkt['dual_error']))
                if (previous_u is not None and delta_d <= 1e-5 and delta_u <= 1e-9
                        and delta_h <= 1e-6 and kkt['passed']):
                    energy = float(endpoint['elastic_kNmm'])+float(endpoint['fracture_kNmm'])
                    if any(not math.isfinite(float(endpoint[k])) or float(endpoint[k]) < 0
                           for k in ('elastic_kNmm', 'fracture_kNmm')):
                        raise ValueError('Invalid authentic endpoint energy')
                    gates = self.evaluator.evaluate_gates(float(endpoint['rf2_kN']), energy,
                                                         kkt['min_delta_d'], max(damage.values()))
                    checkpoint = dict(schema=1, continuation_eligible=False,
                                      displacement=[[n]+list(u[n]) for n in sorted(u)],
                                      damage=[[n, damage[n]] for n in sorted(damage)],
                                      history=[[e, g, history[e, g]] for e, g in sorted(history)],
                                      active_nodes=sorted(kkt['active']), sources=self.source_hashes,
                                      history_semantics='max(authentic transferred H0, frozen UEL POS_M at converged endpoint)')
                    checkpoint_path = self.output/'equilibrium_checkpoint.json'
                    checkpoint_path.write_text(json.dumps(checkpoint, allow_nan=False))
                    checkpoint_hash = hashlib.sha256(checkpoint_path.read_bytes()).hexdigest()
                    report = self._write_report('EQUILIBRIUM_PASS' if gates['pass_all'] else 'PHYSICAL_GATE_FAIL',
                                                gates=gates, checkpoint_sha256=checkpoint_hash,
                                                physical_gates_passed=gates['pass_all'],
                                                full_state_preservation_verified=False,
                                                review_required='Independent donor committed-history equivalence and authentic coupled endpoint review')
                    return report
                previous_d, previous_u, previous_h = dict(damage), u, history
                diag, _, _ = self.solver.assemble_system()
                active = {n for n in damage if damage[n]-kkt['residual'][n]/diag[n] <= self.d0[n]+1e-12}
                phase_converged = False
                for inner in range(1, self.max_phase+1):
                    if time.monotonic() >= self.deadline:
                        raise RuntimeError('Coupled runtime deadline exceeded')
                    damage, _, _ = self.solve(outer, inner, 'phase', damage, active, u, history)
                    kkt = self.solver.kkt(damage)
                    self.records[-1]['phase_iterations'] = inner
                    if kkt['passed']:
                        phase_converged = True
                        break
                    active = {n for n in damage if damage[n]-kkt['residual'][n]/diag[n] <= self.d0[n]+1e-12}
                if not phase_converged:
                    raise RuntimeError('Phase KKT iteration limit exceeded')
                self._write_report('ITERATING')
            raise RuntimeError('Coupled outer iteration limit exceeded')
        except Exception as exc:
            self._write_report('FAILED', error=str(exc))
            raise


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Package 148 bounded serial coupled runtime; no scheduler calls')
    parser.add_argument('--package', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--extractor', required=True)
    parser.add_argument('--donor-rf2', type=float, required=True)
    parser.add_argument('--donor-energy', type=float, required=True)
    parser.add_argument('--abaqus', default='abaqus')
    parser.add_argument('--memory-gb', type=int, default=16)
    parser.add_argument('--timeout', type=int, default=7200)
    parser.add_argument('--max-outer', type=int, default=25)
    parser.add_argument('--max-phase', type=int, default=20)
    args = parser.parse_args()
    report = CoupledAbaqusRuntime(**vars(args)).run()
    return 0 if report['status'] == 'EQUILIBRIUM_PASS' else 2


if __name__ == '__main__':
    sys.exit(main())

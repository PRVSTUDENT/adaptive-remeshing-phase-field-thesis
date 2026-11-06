#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/validation/reconstruct_f1631_early_divergence_forensics.py
==================================================================
Task: F1631-METHOD-C-C6-EARLY-DIVERGENCE-FORENSIC-QUALIFICATION
Handoff: HND-1590fe525792

Zero-PBS forensic reconstruction of the F1630 C6 trajectory (Job 1420429.mmaster02)
at Outer 1..20 and selected later iterations (25, 30, 50, 95, 140) from authentic
subproblem artifacts.

Evaluates:
1. Full nodal displacement u_k, nodal damage (d_{k-1}, d_raw_k, d_pdas_k, d_relaxed_k),
   and 61,008 Gauss-point driving energies psi_e^+(u_k) and histories H_k = max(H0, psi_e^+(u_k)).
2. Discrete phase residuals r = K_d(H_k) d - f_d(H_k) at d_{k-1} (pre-update),
   d_raw_k (Abaqus phase solution), d_pdas_k (projected), and d_k (relaxed),
   lower-bound gap d - d0, PDAS membership, and signed KKT conditions.
3. Distribution of residual signs and magnitudes (unscaled kN*mm and diagonal-normalized
   Jacobi step -r_i / K_{d,ii}) for nodes released into the free set.
4. Spatial mapping of released nodes, newly damaged nodes, and history growth relative
   to the initial crack tip (x = 0.040 mm, y = 0.050 mm) and fracture process zone (l0 = 0.0075 mm).
5. Evolution of reaction force, elastic energy, fracture energy, total energy, and driving history
   before and after Outer 18 compared against the C5 donor reference (1419566.mmaster02).
6. Residual units, epsilon scaling, algorithmic sign conventions, ODB float32 rounding on
   prescribed active nodes, and consistency between the Abaqus UEL phase solve and
   PDASReEquilibrationSolver assembly.
"""

import argparse
import csv
import hashlib
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.c4_to_c5_spatial_mapping import Mesh2D
from scripts.state_transfer.driver_package146_147_pdas_continuation import (
    GC_DEFAULT,
    L0_DEFAULT,
    E_MODULUS,
    NU_POISSON,
    HEALING_TOL,
    UEL_GP_LOCAL,
    quad_shape_functions,
    shape_gradients,
)

DONOR_METADATA = {
    "job_id": "1419566.mmaster02",
    "checkpoint": "Checkpoint 03",
    "crack_tip_x0_mm": 0.040,
    "crack_seam_y0_mm": 0.050,
    "l0_mm": L0_DEFAULT,
    "gc_kN_per_mm": GC_DEFAULT,
}

DONOR_RECONCILIATION = "results/validation/f1636_donor_energy_reconciliation.json"
DONOR_RECONCILIATION_SHA256 = "2B246D518AC1B696C48AC59B2C51979A736201E041D4973ABD1BB938D07AAF00"
DONOR_EVIDENCE_DIR = "models/pandey_kumar_mode1/167_c5_package167_r3_c2_2_continuation/evidence/1419566.mmaster02/"


def validate_donor_energy_sources(summary, checkpoint, telemetry):
    """Require matching final state and each component, not just a matching sum."""
    if not telemetry:
        raise ValueError("Missing donor final-outer telemetry")
    final = telemetry[-1]
    for field in ("elastic_energy_kNmm", "fracture_energy_kNmm", "total_energy_kNmm",
                  "reaction_force_kN", "target_uy_mm"):
        value = summary[field]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
            raise ValueError("Invalid donor numerical field: " + field)
    if summary["status"] != "CONVERGED" or summary["physical_acceptance"] != "PASS" or checkpoint["coupled_convergence"] is not True:
        raise ValueError("Donor acceptance evidence is incomplete")
    if summary["converged_outer_iteration"] != checkpoint["outer_iteration"] or final["outer"] != checkpoint["outer_iteration"]:
        raise ValueError("Donor outer-iteration mismatch")
    pairs = [(summary["target_uy_mm"], checkpoint["target_uy_mm"]),
             (summary["reaction_force_kN"], checkpoint["reaction_force_kN"]),
             (summary["reaction_force_kN"], final["rf2_kN"]),
             (summary["total_energy_kNmm"], checkpoint["total_energy_kNmm"]),
             (summary["elastic_energy_kNmm"], final["elastic_kNmm"]),
             (summary["fracture_energy_kNmm"], final["fracture_kNmm"]),
             (summary["total_energy_kNmm"], final["total_energy_kNmm"]),
             (summary["total_energy_kNmm"], summary["elastic_energy_kNmm"] + summary["fracture_energy_kNmm"])]
    if any(not math.isfinite(b) or not math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-15) for a, b in pairs):
        raise ValueError("Inconsistent donor state or energy component")


def load_donor_reference(root=REPO_ROOT):
    """Load immutable CP03 runtime data, independently reconstructed in F1636."""
    root = Path(root)
    receipt_path = root / DONOR_RECONCILIATION
    if not receipt_path.is_file():
        raise FileNotFoundError(receipt_path)
    raw = receipt_path.read_bytes()
    if hashlib.sha256(raw).hexdigest().upper() != DONOR_RECONCILIATION_SHA256:
        raise ValueError("Donor reconciliation receipt changed")
    receipt = json.loads(raw.decode("utf-8-sig"))
    sources = {}
    for name in ("c5_forward_continuation_c2_2_summary.json", "converged_checkpoint_03.json", "live_iteration_telemetry.json"):
        relative = DONOR_EVIDENCE_DIR + name
        path = root / relative
        if not path.is_file():
            raise FileNotFoundError(path)
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest().upper() != receipt["evidence_sources"][relative]:
            raise ValueError("Donor source hash mismatch: " + name)
        sources[name] = json.loads(data.decode("utf-8-sig"))
    summary = sources["c5_forward_continuation_c2_2_summary.json"]
    validate_donor_energy_sources(summary, sources["converged_checkpoint_03.json"], sources["live_iteration_telemetry.json"])
    result = dict(DONOR_METADATA)
    for field in ("target_uy_mm", "reaction_force_kN", "elastic_energy_kNmm", "fracture_energy_kNmm", "total_energy_kNmm"):
        result[field] = summary[field]
    result["energy_reference_provenance"] = {"receipt": DONOR_RECONCILIATION,
        "receipt_sha256": DONOR_RECONCILIATION_SHA256, "outer": summary["converged_outer_iteration"],
        "sources": {DONOR_EVIDENCE_DIR + name: receipt["evidence_sources"][DONOR_EVIDENCE_DIR + name] for name in sources}}
    return result

SELECTED_OUTERS = [1, 2, 5, 10, 15, 16, 17, 18, 19, 20, 25, 30, 50, 95, 140]


def quantiles(vals: List[float]) -> Dict[str, float]:
    if not vals:
        return {"count": 0, "min": 0.0, "p05": 0.0, "p25": 0.0, "median": 0.0, "p75": 0.0, "p95": 0.0, "max": 0.0, "mean": 0.0}
    s = sorted(vals)
    n = len(s)

    def pct(p: float) -> float:
        idx = min(n - 1, max(0, int(round(p * (n - 1)))))
        return float(s[idx])

    return {
        "count": n,
        "min": float(s[0]),
        "p05": pct(0.05),
        "p25": pct(0.25),
        "median": pct(0.50),
        "p75": pct(0.75),
        "p95": pct(0.95),
        "max": float(s[-1]),
        "mean": float(sum(s) / n),
    }


class FastPrecomputedPhaseAssembler:
    """
    Precomputes element shape functions, physical gradients, and Jacobian weights at all
    61,008 Gauss points so that driving_history(u) and K_d(H), f_d(H) are evaluated
    with exact mathematical parity to PDASReEquilibrationSolver in <0.1s per iteration.
    """

    def __init__(self, mesh: Mesh2D, gc: float = GC_DEFAULT, l0: float = L0_DEFAULT):
        self.mesh = mesh
        self.gc = gc
        self.l0 = l0
        self.lam = E_MODULUS * NU_POISSON / ((1.0 + NU_POISSON) * (1.0 - 2.0 * NU_POISSON))
        self.mu = E_MODULUS / (2.0 * (1.0 + NU_POISSON))

        # Precompute per-element GP data
        # gp_data[eid] = list of 4 tuples: (det_j, n_vals, gx, gy)
        self.gp_data: Dict[int, List[Tuple[float, List[float], List[float], List[float]]]] = {}
        self.element_centroids: Dict[int, Tuple[float, float]] = {}
        self.total_volume = 0.0

        for eid, conn in mesh.elements.items():
            vertices = [mesh.nodes[n] for n in conn]
            cx = 0.25 * sum(v[0] for v in vertices)
            cy = 0.25 * sum(v[1] for v in vertices)
            self.element_centroids[eid] = (cx, cy)
            elist = []
            for gp_idx, (xi, eta) in enumerate(UEL_GP_LOCAL):
                n_vals = quad_shape_functions(xi, eta)
                det_j, gx, gy = shape_gradients(vertices, xi, eta)
                elist.append((det_j, list(n_vals), list(gx), list(gy)))
                self.total_volume += det_j
            self.gp_data[eid] = elist

    def compute_psi_plus(self, u: Dict[int, Tuple[float, float]]) -> Dict[Tuple[int, int], float]:
        psi: Dict[Tuple[int, int], float] = {}
        lam = self.lam
        mu = self.mu
        for eid, conn in self.mesh.elements.items():
            u0x, u0y = u[conn[0]]
            u1x, u1y = u[conn[1]]
            u2x, u2y = u[conn[2]]
            u3x, u3y = u[conn[3]]
            for g_idx, (_, _, gx, gy) in enumerate(self.gp_data[eid], 1):
                e11 = gx[0] * u0x + gx[1] * u1x + gx[2] * u2x + gx[3] * u3x
                e22 = gy[0] * u0y + gy[1] * u1y + gy[2] * u2y + gy[3] * u3y
                e12 = 0.5 * (
                    gy[0] * u0x + gx[0] * u0y
                    + gy[1] * u1x + gx[1] * u1y
                    + gy[2] * u2x + gx[2] * u2y
                    + gy[3] * u3x + gx[3] * u3y
                )
                tr_pos = e11 + e22 if (e11 + e22) > 0.0 else 0.0
                val = 0.5 * lam * (tr_pos * tr_pos) + mu * (e11 * e11 + e22 * e22 + 2.0 * e12 * e12)
                psi[(eid, g_idx)] = val
        return psi

    def assemble_and_residual(
        self,
        h_gp: Dict[Tuple[int, int], float],
        d_vec: Dict[int, float],
    ) -> Tuple[Dict[int, float], Dict[int, float], Dict[int, float]]:
        """
        Computes:
          - diag[n]: diagonal stiffness K_{d,nn}(H)
          - rhs[n]: force vector f_{d,n}(H)
          - residual[n]: (K_d(H) d_vec - f_d(H))_n
        Directly element-by-element to avoid building a slow dict of off-diagonals on every call.
        """
        diag: Dict[int, float] = {n: 0.0 for n in d_vec}
        rhs: Dict[int, float] = {n: 0.0 for n in d_vec}
        res: Dict[int, float] = {n: 0.0 for n in d_vec}
        gc_over_l0 = self.gc / self.l0
        gc_times_l0 = self.gc * self.l0

        for eid, conn in self.mesh.elements.items():
            d_loc = [d_vec[conn[0]], d_vec[conn[1]], d_vec[conn[2]], d_vec[conn[3]]]
            for g_idx, (det_j, n_vals, gx, gy) in enumerate(self.gp_data[eid], 1):
                h_val = h_gp[(eid, g_idx)]
                coef_mass = (gc_over_l0 + 2.0 * h_val) * det_j
                coef_diff = gc_times_l0 * det_j
                coef_rhs = (2.0 * h_val) * det_j

                # GP interpolated d and grad d
                d_gp = (
                    n_vals[0] * d_loc[0]
                    + n_vals[1] * d_loc[1]
                    + n_vals[2] * d_loc[2]
                    + n_vals[3] * d_loc[3]
                )
                gdx = gx[0] * d_loc[0] + gx[1] * d_loc[1] + gx[2] * d_loc[2] + gx[3] * d_loc[3]
                gdy = gy[0] * d_loc[0] + gy[1] * d_loc[1] + gy[2] * d_loc[2] + gy[3] * d_loc[3]

                for i in range(4):
                    ni = conn[i]
                    f_i = coef_rhs * n_vals[i]
                    k_ii = coef_mass * (n_vals[i] * n_vals[i]) + coef_diff * (gx[i] * gx[i] + gy[i] * gy[i])
                    kd_i = coef_mass * d_gp * n_vals[i] + coef_diff * (gdx * gx[i] + gdy * gy[i])
                    rhs[ni] += f_i
                    diag[ni] += k_ii
                    res[ni] += (kd_i - f_i)

        return diag, rhs, res

    def residual_for_multiple_d(
        self,
        h_gp: Dict[Tuple[int, int], float],
        d_vecs: Dict[str, Dict[int, float]],
    ) -> Tuple[Dict[int, float], Dict[int, float], Dict[str, Dict[int, float]]]:
        """
        Evaluates diag, rhs, and residuals r = K_d(H) d - f_d(H) for multiple damage vectors in one pass.
        """
        any_d = next(iter(d_vecs.values()))
        diag: Dict[int, float] = {n: 0.0 for n in any_d}
        rhs: Dict[int, float] = {n: 0.0 for n in any_d}
        res_map: Dict[str, Dict[int, float]] = {k: {n: 0.0 for n in any_d} for k in d_vecs}
        gc_over_l0 = self.gc / self.l0
        gc_times_l0 = self.gc * self.l0

        for eid, conn in self.mesh.elements.items():
            n0, n1, n2, n3 = conn
            d_locs = {k: (dv[n0], dv[n1], dv[n2], dv[n3]) for k, dv in d_vecs.items()}
            for g_idx, (det_j, n_vals, gx, gy) in enumerate(self.gp_data[eid], 1):
                h_val = h_gp[(eid, g_idx)]
                coef_mass = (gc_over_l0 + 2.0 * h_val) * det_j
                coef_diff = gc_times_l0 * det_j
                coef_rhs = (2.0 * h_val) * det_j

                for i in range(4):
                    ni = conn[i]
                    rhs[ni] += coef_rhs * n_vals[i]
                    diag[ni] += coef_mass * (n_vals[i] * n_vals[i]) + coef_diff * (gx[i] * gx[i] + gy[i] * gy[i])

                for k, d_loc in d_locs.items():
                    rmap = res_map[k]
                    d_gp = (
                        n_vals[0] * d_loc[0]
                        + n_vals[1] * d_loc[1]
                        + n_vals[2] * d_loc[2]
                        + n_vals[3] * d_loc[3]
                    )
                    gdx = gx[0] * d_loc[0] + gx[1] * d_loc[1] + gx[2] * d_loc[2] + gx[3] * d_loc[3]
                    gdy = gy[0] * d_loc[0] + gy[1] * d_loc[1] + gy[2] * d_loc[2] + gy[3] * d_loc[3]
                    for i in range(4):
                        ni = conn[i]
                        f_i = coef_rhs * n_vals[i]
                        kd_i = coef_mass * d_gp * n_vals[i] + coef_diff * (gdx * gx[i] + gdy * gy[i])
                        rmap[ni] += (kd_i - f_i)

        return diag, rhs, res_map


def parse_prescribed_dof3_from_phase_inp(inp_path: Path) -> Dict[int, float]:
    """Parses active-set DOF 3 boundary cards `node, 3, 3, val` from a phase subproblem .inp file."""
    active_prescribed: Dict[int, float] = {}
    if not inp_path.is_file():
        return active_prescribed
    in_boundary = False
    with inp_path.open("r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("**"):
                continue
            if s.startswith("*"):
                in_boundary = s.lower().startswith("*boundary")
                continue
            if in_boundary:
                parts = [p.strip() for p in s.split(",")]
                if len(parts) >= 4 and parts[1] == "3" and parts[2] == "3":
                    try:
                        nid = int(parts[0])
                        active_prescribed[nid] = float(parts[3])
                    except ValueError:
                        pass
    return active_prescribed


def parse_u_trial_from_phase_inp(inp_path: Path) -> Dict[int, Tuple[float, float]]:
    """Parses prescribed DOF 1,2 nodal displacements from a phase subproblem .inp file."""
    u1: Dict[int, float] = {}
    u2: Dict[int, float] = {}
    if not inp_path.is_file():
        return {}
    in_boundary = False
    with inp_path.open("r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("**"):
                continue
            if s.startswith("*"):
                in_boundary = s.lower().startswith("*boundary")
                continue
            if in_boundary:
                parts = [p.strip() for p in s.split(",")]
                if len(parts) >= 4:
                    try:
                        nid = int(parts[0])
                        dof = int(parts[1])
                        val = float(parts[3])
                        if dof == 1:
                            u1[nid] = val
                        elif dof == 2:
                            u2[nid] = val
                    except ValueError:
                        pass
    return {nid: (u1[nid], u2[nid]) for nid in u1 if nid in u2}


def parse_d_in_from_mech_inp(inp_path: Path) -> Dict[int, float]:
    """Parses prescribed DOF 3 nodal damage entering the mechanical subproblem .inp file."""
    return parse_prescribed_dof3_from_phase_inp(inp_path)


def load_endpoint_fields(ep_path: Path) -> Tuple[Dict[int, Tuple[float, float]], Dict[int, float], Dict[str, Any]]:
    data = json.loads(ep_path.read_text(encoding="utf-8"))
    u: Dict[int, Tuple[float, float]] = {}
    d: Dict[int, float] = {}
    for row in data.get("nodes", []):
        nid = int(row[0])
        u[nid] = (float(row[1]), float(row[2]))
        if len(row) >= 4:
            d[nid] = float(row[3])
    meta = {k: v for k, v in data.items() if k not in ("nodes", "raw_damage")}
    return u, d, meta


def load_uel_energy_csv(csv_path: Path) -> Dict[str, float]:
    if not csv_path.is_file():
        return {}
    lines = [ln.strip() for ln in csv_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    if len(lines) < 2:
        return {}
    parts = [p.strip() for p in lines[-1].split(",")]
    if len(parts) < 7:
        return {}
    return {
        "e_elastic_kNmm": float(parts[4]),
        "e_fracture_kNmm": float(parts[5]),
        "e_total_kNmm": float(parts[6]),
    }


def run_forensics(package_dir: Path, equil_dir: Path, out_json: Path) -> Dict[str, Any]:
    if out_json.exists():
        raise FileExistsError("Preserve existing forensic evidence; choose a distinct output path")
    donor_reference = load_donor_reference()
    deck_path = package_dir / "M1_C6_PACKAGE171_R12_C3_0_ADAPTIVE_REEQUILIBRATION.inp"
    mesh = Mesh2D.from_inp(deck_path, name="C6_Receiver", max_physical_node=15559)

    d0: Dict[int, float] = {}
    with (package_dir / "nodal_phase_field_initial.csv").open("r", encoding="utf-8") as f:
        r = csv.reader(f)
        next(r)
        for row in r:
            if row:
                d0[int(row[0])] = float(row[1])

    u0: Dict[int, Tuple[float, float]] = {}
    with (package_dir / "nodal_displacements_initial.csv").open("r", encoding="utf-8") as f:
        r = csv.reader(f)
        next(r)
        for row in r:
            if row:
                u0[int(row[0])] = (float(row[1]), float(row[2]))

    h0: Dict[Tuple[int, int], float] = {}
    with (package_dir / "d_lower_bounds.csv").open("r", encoding="utf-8") as f:
        r = csv.reader(f)
        next(r)
        for row in r:
            if row:
                eid = int(row[0])
                for g in range(1, 5):
                    h0[(eid, g)] = float(row[4 + g])

    telem = json.loads((equil_dir / "live_iteration_telemetry.json").read_text(encoding="utf-8"))
    telem_by_outer = {int(rec["outer"]): rec for rec in telem}

    assembler = FastPrecomputedPhaseAssembler(mesh, gc=GC_DEFAULT, l0=L0_DEFAULT)

    # Identify initial crack-tip and seam geometry
    x_tip0 = donor_reference["crack_tip_x0_mm"]
    y_seam0 = donor_reference["crack_seam_y0_mm"]
    l0 = donor_reference["l0_mm"]

    node_dist_tip: Dict[int, float] = {}
    node_abs_dy: Dict[int, float] = {}
    for nid, (x, y) in mesh.nodes.items():
        node_dist_tip[nid] = math.hypot(x - x_tip0, y - y_seam0)
        node_abs_dy[nid] = abs(y - y_seam0)

    # Initial H0 integral and stats
    h0_integral = sum(
        h0[(eid, g)] * assembler.gp_data[eid][g - 1][0]
        for eid in mesh.elements for g in range(1, 5)
    )
    h0_max = max(h0.values())

    # Replay Outer 1..20 consecutively in exact float64 (matching driver_package171_r12_c6_coupled_pdas.py)
    # and also evaluate selected later iterations 25, 30, 50, 95, 140 using exact .inp / endpoint.json states.
    c_pdas = 1.0e3
    eps_pdas = 1.0e-6

    damage_prev = dict(d0)
    prev_u_trial = None
    prev_h_trial = None
    prev_pdas_active: Set[int] = set(d0.keys())

    iteration_forensics: Dict[int, Dict[str, Any]] = {}

    all_outers_to_process = sorted(set(list(range(1, 21)) + SELECTED_OUTERS))

    for outer in all_outers_to_process:
        mech_dir = equil_dir / f"step_01_outer_{outer:02d}_mechanical"
        phase_dir = equil_dir / f"step_01_outer_{outer:02d}_phase"
        mech_ep_path = mech_dir / "endpoint.json"
        phase_ep_path = phase_dir / "endpoint.json"
        mech_inp_path = mech_dir / f"M1_C6_P171_R12_MECHANICAL_O{outer:02d}.inp"
        phase_inp_path = phase_dir / f"M1_C6_P171_R12_PHASE_O{outer:02d}.inp"

        if not (mech_ep_path.is_file() and phase_ep_path.is_file()):
            continue

        u_abaqus, d_mech_ep, mech_meta = load_endpoint_fields(mech_ep_path)
        _, d_raw_phase, phase_meta = load_endpoint_fields(phase_ep_path)
        mech_uel_csv = load_uel_energy_csv(mech_dir / "uel_energy_balance.csv")
        phase_uel_csv = load_uel_energy_csv(phase_dir / "uel_energy_balance.csv")

        # If jumping past outer > 20, recover exact float64 damage_prev and u_trial from the .inp cards
        if outer > 20:
            d_from_inp = parse_d_in_from_mech_inp(mech_inp_path)
            if len(d_from_inp) == 15559:
                damage_prev = d_from_inp
            else:
                damage_prev = d_mech_ep
            u_from_phase_inp = parse_u_trial_from_phase_inp(phase_inp_path)
            if len(u_from_phase_inp) == 15559:
                u_trial = u_from_phase_inp
            else:
                u_trial = u_abaqus
            # Also recover previous outer's active set from outer-1 phase inp if available
            prev_phase_inp = equil_dir / f"step_01_outer_{outer-1:02d}_phase" / f"M1_C6_P171_R12_PHASE_O{outer-1:02d}.inp"
            if prev_phase_inp.is_file():
                prev_pdas_active = set(parse_prescribed_dof3_from_phase_inp(prev_phase_inp).keys())
        else:
            # Consecutive exact float64 replay for Outer 1..20 (Stage 1: omega_u = 1.0)
            u_trial = dict(u_abaqus)

        # Compute psi_k and H_k = max(H0, psi_k)
        psi_k = assembler.compute_psi_plus(u_trial)
        history_k = {k: max(h0[k], psi_k[k]) for k in h0}

        # Projected PDAS damage and relaxed damage
        t_rec = telem_by_outer[outer]
        omega_d = float(t_rec["applied_omega_d"])
        new_damage_pdas = {n: min(1.0, max(d0[n], d_raw_phase[n])) for n in d_raw_phase}
        relaxed_damage = {
            n: min(1.0, max(d0[n], (1.0 - omega_d) * damage_prev[n] + omega_d * new_damage_pdas[n]))
            for n in new_damage_pdas
        }

        # Also compute what new_damage_pdas and relaxed_damage would be if active nodes were strictly
        # pinned to float64(d0[n]) rather than taking float32(d0[n]) from the Abaqus ODB
        diag, rhs, res_map = assembler.residual_for_multiple_d(
            history_k,
            {
                "pre": damage_prev,
                "raw": d_raw_phase,
                "pdas": new_damage_pdas,
                "post": relaxed_damage,
            },
        )
        r_pre = res_map["pre"]
        r_raw = res_map["raw"]
        r_pdas = res_map["pdas"]
        r_post = res_map["post"]

        # Reconstruct PDAS active set at iteration `outer`
        pdas_active = {
            n for n in damage_prev
            if (damage_prev[n] - c_pdas * r_pre[n]) <= (d0[n] + eps_pdas)
        }
        pdas_free = set(damage_prev.keys()) - pdas_active

        if outer in SELECTED_OUTERS:
            # Verify against actual phase .inp boundary cards if present
            inp_active_map = parse_prescribed_dof3_from_phase_inp(phase_inp_path)
            inp_active_match = (set(inp_active_map.keys()) == pdas_active) if inp_active_map else None

            # Newly released nodes on this iteration
            newly_released = (prev_pdas_active - pdas_active) if outer > 1 else (set(d0.keys()) - pdas_active)
            newly_added = (pdas_active - prev_pdas_active) if outer > 1 else set()

            # Check float32 ODB rounding on active nodes
            active_odb_drift = [d_raw_phase[n] - d0[n] for n in pdas_active]
            active_odb_exceed_1e10 = sum(1 for v in active_odb_drift if v > 1.0e-10)
            active_odb_negative = sum(1 for v in active_odb_drift if v < -1.0e-10)

            # Check phase solve stationarity on the TRUE PDAS free set I_k = V \ A_k
            # At d_raw_phase (what Abaqus actually solved!) vs at d_post (relaxed_damage = 0.5*d_prev + 0.5*d_pdas)
            free_r_raw_abs = [abs(r_raw[n]) for n in pdas_free]
            free_r_raw_jacobi = [abs(r_raw[n]) / diag[n] for n in pdas_free]
            free_r_post_abs = [abs(r_post[n]) for n in pdas_free]
            free_r_post_jacobi = [abs(r_post[n]) / diag[n] for n in pdas_free]

            # Signed KKT on PDAS partition (A_k, I_k) vs solver.kkt() partition (d - d0 <= 1e-10)
            kkt_active_solver = {n for n in relaxed_damage if relaxed_damage[n] - d0[n] <= 1.0e-10}
            kkt_free_solver = set(relaxed_damage.keys()) - kkt_active_solver

            pdas_dual_err_pre = max([max(0.0, -r_pre[n]) for n in pdas_active] + [0.0])
            pdas_dual_err_raw = max([max(0.0, -r_raw[n]) for n in pdas_active] + [0.0])
            pdas_dual_err_post = max([max(0.0, -r_post[n]) for n in pdas_active] + [0.0])

            # Distribution of pre-update residuals and lower-bound gaps on:
            # (a) Newly released nodes, (b) All free nodes I_k, (c) Remaining active nodes A_k
            rel_r_pre = [r_pre[n] for n in newly_released]
            rel_jacobi_step = [-r_pre[n] / diag[n] for n in newly_released]
            rel_gap_pre = [damage_prev[n] - d0[n] for n in newly_released]
            rel_pdas_shift = [-c_pdas * r_pre[n] for n in newly_released]
            rel_d_change_pdas = [new_damage_pdas[n] - damage_prev[n] for n in newly_released]
            rel_r_neg_count = sum(1 for v in rel_r_pre if v < 0.0)
            rel_r_pos_count = sum(1 for v in rel_r_pre if v >= 0.0)
            # Why was each newly released node released?
            # Case 1: at lower bound (damage_prev[n] - d0[n] <= 1e-6) and -c_pdas * r_pre[n] > eps_pdas (r_pre[n] < -1e-9)
            # Case 2: already above lower bound (damage_prev[n] - d0[n] > 1e-6)
            rel_at_bound_neg_res = sum(
                1 for n in newly_released
                if (damage_prev[n] - d0[n] <= 1.0e-6) and (-c_pdas * r_pre[n] > eps_pdas)
            )
            rel_already_above_bound = sum(
                1 for n in newly_released
                if (damage_prev[n] - d0[n] > 1.0e-6)
            )
            # Wait: how could a node in prev_pdas_active have damage_prev[n] - d0[n] > 1e-6?
            # Because if it was active at outer-1, its prescribed value in Abaqus was d0[n] (float32 rounding <= 3e-8)!
            # So EVERY node in prev_pdas_active had damage_prev[n] - d0[n] <= 3e-8 << 1e-6!

            # Spatial distribution of newly released nodes and all free nodes
            rel_dist_tip = [node_dist_tip[n] for n in newly_released]
            rel_abs_dy = [node_abs_dy[n] for n in newly_released]
            rel_in_fpz_2l0 = sum(1 for n in newly_released if node_abs_dy[n] <= 2.0 * l0)
            rel_outside_fpz_2l0 = sum(1 for n in newly_released if node_abs_dy[n] > 2.0 * l0)

            free_in_fpz_2l0 = sum(1 for n in pdas_free if node_abs_dy[n] <= 2.0 * l0)
            free_outside_fpz_2l0 = sum(1 for n in pdas_free if node_abs_dy[n] > 2.0 * l0)

            # Spatial localization of actual damage growth (d_k - d0)
            d_growth_all = {n: relaxed_damage[n] - d0[n] for n in relaxed_damage}
            d_growth_in_fpz = [d_growth_all[n] for n in relaxed_damage if node_abs_dy[n] <= 2.0 * l0]
            d_growth_outside_fpz = [d_growth_all[n] for n in relaxed_damage if node_abs_dy[n] > 2.0 * l0]
            d_growth_far_field_3l0 = [d_growth_all[n] for n in relaxed_damage if node_abs_dy[n] > 3.0 * l0]

            nodes_dg_gt_0p001 = [n for n, dg in d_growth_all.items() if dg > 1.0e-3]
            nodes_dg_gt_0p01 = [n for n, dg in d_growth_all.items() if dg > 1.0e-2]
            nodes_dg_gt_0p05 = [n for n, dg in d_growth_all.items() if dg > 5.0e-2]
            nodes_dg_gt_0p10 = [n for n, dg in d_growth_all.items() if dg > 1.0e-1]
            nodes_d_ge_0p90 = [n for n, dv in relaxed_damage.items() if dv >= 0.90]
            nodes_d_ge_0p95 = [n for n, dv in relaxed_damage.items() if dv >= 0.95]

            crack_tip_x_0p90 = max([mesh.nodes[n][0] for n in nodes_d_ge_0p90] + [x_tip0])
            crack_tip_x_0p95 = max([mesh.nodes[n][0] for n in nodes_d_ge_0p95] + [x_tip0])

            # Max damage growth outside FPZ
            max_dg_outside_2l0 = max(d_growth_outside_fpz) if d_growth_outside_fpz else 0.0
            max_dg_outside_3l0 = max(d_growth_far_field_3l0) if d_growth_far_field_3l0 else 0.0

            # Bounding box of nodes with d_k - d0 > 0.01
            if nodes_dg_gt_0p01:
                xs_0p01 = [mesh.nodes[n][0] for n in nodes_dg_gt_0p01]
                ys_0p01 = [mesh.nodes[n][1] for n in nodes_dg_gt_0p01]
                bbox_dg_0p01 = {
                    "count": len(nodes_dg_gt_0p01),
                    "x_min": min(xs_0p01),
                    "x_max": max(xs_0p01),
                    "y_min": min(ys_0p01),
                    "y_max": max(ys_0p01),
                    "max_abs_dy_from_seam": max(abs(y - y_seam0) for y in ys_0p01),
                }
            else:
                bbox_dg_0p01 = {"count": 0, "x_min": None, "x_max": None, "y_min": None, "y_max": None, "max_abs_dy_from_seam": 0.0}

            # History growth analysis: psi_k > H0
            gps_exceeding_h0 = [(eid, g) for (eid, g) in h0 if psi_k[(eid, g)] > h0[(eid, g)]]
            h_growth_vals = [history_k[k] - h0[k] for k in gps_exceeding_h0]
            h_integral = sum(
                history_k[(eid, g)] * assembler.gp_data[eid][g - 1][0]
                for eid in mesh.elements for g in range(1, 5)
            )
            max_psi_k = max(psi_k.values())
            max_h_k = max(history_k.values())
            max_gp_key = max(history_k.items(), key=lambda kv: kv[1])[0]
            max_gp_centroid = assembler.element_centroids[max_gp_key[0]]

            # Force and energy evolution at this outer iteration
            rf2_kN = float(mech_meta.get("rf2_kN", 0.0))
            e_elas_mech = float(mech_meta.get("elastic_kNmm", mech_uel_csv.get("e_elastic_kNmm", 0.0)))
            e_frac_mech = float(mech_meta.get("fracture_kNmm", mech_uel_csv.get("e_fracture_kNmm", 0.0)))
            e_tot_mech = float(mech_meta.get("total_energy_kNmm", e_elas_mech + e_frac_mech))
            e_frac_phase = float(phase_meta.get("fracture_kNmm", phase_uel_csv.get("e_fracture_kNmm", 0.0)))

            rf_drift_pct = (rf2_kN - donor_reference["reaction_force_kN"]) / donor_reference["reaction_force_kN"] * 100.0
            e_tot_drift_pct = (e_tot_mech - donor_reference["total_energy_kNmm"]) / donor_reference["total_energy_kNmm"] * 100.0

            iteration_forensics[outer] = {
                "outer": outer,
                "stage": int(t_rec["stage"]),
                "omega_d": omega_d,
                "omega_u": float(t_rec["applied_omega_u"]),
                "telemetry_parity": {
                    "telem_pdas_active_count": int(t_rec["pdas_active_count"]),
                    "reconstructed_pdas_active_count": len(pdas_active),
                    "phase_inp_dof3_prescribed_count": len(inp_active_map) if inp_active_map else None,
                    "phase_inp_exact_set_match": inp_active_match,
                    "telem_kkt_active_count": int(t_rec["kkt_active_count"]),
                    "reconstructed_kkt_active_count": len(kkt_active_solver),
                    "telem_delta_d": float(t_rec["delta_d"]),
                    "reconstructed_delta_d": max(abs(relaxed_damage[n] - damage_prev[n]) for n in relaxed_damage),
                    "telem_raw_delta_d": float(t_rec["raw_delta_d"]),
                    "reconstructed_raw_delta_d": max(abs(new_damage_pdas[n] - damage_prev[n]) for n in new_damage_pdas),
                    "telem_free_error": float(t_rec["free_error"]),
                    "reconstructed_kkt_post_free_error": max([abs(r_post[n]) for n in kkt_free_solver] + [0.0]),
                    "telem_dual_error": float(t_rec["dual_error"]),
                    "reconstructed_kkt_post_dual_error": max([max(0.0, -r_post[n]) for n in kkt_active_solver] + [0.0]),
                },
                "force_and_energy": {
                    "rf2_kN": rf2_kN,
                    "rf2_drift_vs_donor_pct": rf_drift_pct,
                    "e_elastic_mech_kNmm": e_elas_mech,
                    "e_fracture_mech_kNmm": e_frac_mech,
                    "e_total_mech_kNmm": e_tot_mech,
                    "e_total_drift_vs_donor_pct": e_tot_drift_pct,
                    "e_fracture_after_phase_kNmm": e_frac_phase,
                },
                "damage_and_crack_tip": {
                    "d_prev_max": max(damage_prev.values()),
                    "d_raw_phase_max": max(d_raw_phase.values()),
                    "d_raw_phase_min": min(d_raw_phase.values()),
                    "d_relaxed_max": max(relaxed_damage.values()),
                    "nodes_d_ge_0p90_count": len(nodes_d_ge_0p90),
                    "nodes_d_ge_0p95_count": len(nodes_d_ge_0p95),
                    "crack_tip_x_d_ge_0p90_mm": crack_tip_x_0p90,
                    "crack_tip_x_d_ge_0p95_mm": crack_tip_x_0p95,
                    "crack_advance_dx_0p90_mm": crack_tip_x_0p90 - x_tip0,
                    "nodes_dg_gt_1e3_count": len(nodes_dg_gt_0p001),
                    "nodes_dg_gt_1e2_count": len(nodes_dg_gt_0p01),
                    "nodes_dg_gt_5e2_count": len(nodes_dg_gt_0p05),
                    "nodes_dg_gt_1e1_count": len(nodes_dg_gt_0p10),
                    "bbox_dg_gt_1e2": bbox_dg_0p01,
                    "max_dg_in_fpz_2l0": max(d_growth_in_fpz) if d_growth_in_fpz else 0.0,
                    "max_dg_outside_fpz_2l0": max_dg_outside_2l0,
                    "max_dg_outside_fpz_3l0": max_dg_outside_3l0,
                },
                "history_evolution": {
                    "max_psi_plus_MPa": max_psi_k,
                    "max_history_MPa": max_h_k,
                    "max_history_element_id": max_gp_key[0],
                    "max_history_gp_idx": max_gp_key[1],
                    "max_history_centroid_xy_mm": list(max_gp_centroid),
                    "gps_exceeding_h0_count": len(gps_exceeding_h0),
                    "gps_exceeding_h0_pct": len(gps_exceeding_h0) / 61008.0 * 100.0,
                    "max_h_growth_over_h0_MPa": max(h_growth_vals) if h_growth_vals else 0.0,
                    "h_domain_integral_MPa_mm2": h_integral,
                    "h_domain_integral_change_pct": (h_integral - h0_integral) / h0_integral * 100.0,
                },
                "pdas_and_kkt_diagnostics": {
                    "pdas_active_count": len(pdas_active),
                    "pdas_free_count": len(pdas_free),
                    "newly_released_count": len(newly_released),
                    "newly_added_count": len(newly_added),
                    "newly_released_in_fpz_2l0": rel_in_fpz_2l0,
                    "newly_released_outside_fpz_2l0": rel_outside_fpz_2l0,
                    "free_in_fpz_2l0": free_in_fpz_2l0,
                    "free_outside_fpz_2l0": free_outside_fpz_2l0,
                    "newly_released_r_pre_neg_count": rel_r_neg_count,
                    "newly_released_r_pre_nonneg_count": rel_r_pos_count,
                    "newly_released_at_bound_neg_res_count": rel_at_bound_neg_res,
                    "newly_released_already_above_bound_count": rel_already_above_bound,
                    "newly_released_r_pre_kNmm_quantiles": quantiles(rel_r_pre),
                    "newly_released_jacobi_step_quantiles": quantiles(rel_jacobi_step),
                    "newly_released_gap_pre_quantiles": quantiles(rel_gap_pre),
                    "newly_released_pdas_shift_quantiles": quantiles(rel_pdas_shift),
                    "newly_released_d_change_pdas_quantiles": quantiles(rel_d_change_pdas),
                    "newly_released_dist_tip_mm_quantiles": quantiles(rel_dist_tip),
                    "newly_released_abs_dy_mm_quantiles": quantiles(rel_abs_dy),
                    "active_odb_float32_exceed_1e10_count": active_odb_exceed_1e10,
                    "active_odb_float32_negative_count": active_odb_negative,
                    "active_odb_float32_drift_quantiles": quantiles(active_odb_drift),
                    "free_set_r_raw_abs_kNmm_quantiles": quantiles(free_r_raw_abs),
                    "free_set_r_raw_jacobi_quantiles": quantiles(free_r_raw_jacobi),
                    "free_set_r_post_abs_kNmm_quantiles": quantiles(free_r_post_abs),
                    "free_set_r_post_jacobi_quantiles": quantiles(free_r_post_jacobi),
                    "pdas_dual_error_pre_kNmm": pdas_dual_err_pre,
                    "pdas_dual_error_raw_kNmm": pdas_dual_err_raw,
                    "pdas_dual_error_post_kNmm": pdas_dual_err_post,
                    "diag_stiffness_kNmm_quantiles": quantiles(list(diag.values())),
                },
            }

        damage_prev = relaxed_damage
        prev_u_trial = u_trial
        prev_h_trial = history_k
        prev_pdas_active = pdas_active

    result = {
        "task_id": "F1631-METHOD-C-C6-EARLY-DIVERGENCE-FORENSIC-QUALIFICATION",
        "handoff_id": "HND-1590fe525792",
        "source_job_id": "1420429.mmaster02",
        "donor_reference": donor_reference,
        "initial_transferred_state": {
            "nodes_count": len(d0),
            "elements_count": len(mesh.elements),
            "gauss_points_count": len(h0),
            "d0_min": min(d0.values()),
            "d0_max": max(d0.values()),
            "h0_min_MPa": min(h0.values()),
            "h0_max_MPa": h0_max,
            "h0_domain_integral_MPa_mm2": h0_integral,
        },
        "selected_outer_iterations": SELECTED_OUTERS,
        "iterations": {str(k): iteration_forensics[k] for k in SELECTED_OUTERS if k in iteration_forensics},
    }

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="F1631 Early Divergence Forensic Reconstructor")
    parser.add_argument(
        "--package-dir",
        type=Path,
        default=REPO_ROOT / "models" / "pandey_kumar_mode1" / "174_c6_r12_picard_baseline",
    )
    parser.add_argument(
        "--equil-dir",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=REPO_ROOT / "results" / "validation" / "f1631_early_divergence_forensics_summary.json",
    )
    args = parser.parse_args()
    res = run_forensics(args.package_dir, args.equil_dir, args.output_json)
    print(f"Forensic reconstruction complete: {len(res['iterations'])} outer states written to {args.output_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

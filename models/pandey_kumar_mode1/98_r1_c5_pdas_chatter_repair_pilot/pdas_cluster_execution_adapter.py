#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pdas_cluster_execution_adapter.py
Compute-Node Iterative Primal-Dual Active-Set (PDAS) Execution Adapter
for Phase-Field Fracture Mechanics under Abaqus 2023 (mode1-pdas-iterative-v1).

Package 98 Revision 1 Chatter Repair & Dirichlet Invariant Preservation:
- Corrected nodal phase-field reconstruction on clamped sets:
  d_k[L_k] = d_ckpt[L_k] and d_k[U_k] = 1.00000000 exactly, eliminating
  element-nodal SDV1 extrapolation smoothing error on Dirichlet boundaries.
- Preserves free-set solved phase field: d_k[A_k] = d_solver[A_k].
- Active-set cycle-detection safeguard to prevent infinite chatter loops.
- Robust mesh parsing excluding *Node Output and validating numeric node IDs.
- Authentic unscaled committed Gauss-point history (scale_h = 1.0).
- Physical continuation loading: u_target = u_ckpt + delta_u (+4.0 nm).
- Authentic ODB extraction via extract_pdas_subproblem_odb.py.
- Crash-safe atomic ledger persistence (.tmp replacement).
"""

import sys
import os
import math
import json
import csv
import hashlib
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

# Material properties matching UEL PROPS
E_GC = 0.0027   # kN/mm
E_L0 = 0.0075   # mm
E_MOD = 210.0   # kN/mm^2
NU = 0.30

# Tolerances matching predeclared acceptance criteria
TAU_RES = 1.0e-6      # Dual residual infinity norm tolerance (kN/mm)
TAU_FEAS = 1.0e-6     # Primal bound feasibility tolerance
TAU_MECH = 1.0e-4     # Mechanical equilibrium tolerance (kN)
K_MAX_PDAS = 25       # Maximum outer PDAS iterations cap

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()

def shape_functions(xi: float, eta: float):
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

class PDASClusterExecutionAdapter:
    def __init__(self,
                 seed_deck_path: Path,
                 mesh_inp_path: Path,
                 state_table_path: Path,
                 uel_path: Path,
                 work_dir: Path,
                 delta_u_nm: float = 4.0,
                 u_checkpoint: float = 0.002052,
                 k_max: int = K_MAX_PDAS,
                 mode: str = "offline_qualification"):
        self.seed_deck_path = Path(seed_deck_path)
        self.mesh_inp_path = Path(mesh_inp_path)
        self.state_table_path = Path(state_table_path)
        self.uel_path = Path(uel_path)
        self.work_dir = Path(work_dir)
        self.delta_u_nm = delta_u_nm
        self.u_checkpoint = u_checkpoint
        self.u_target = self.u_checkpoint + self.delta_u_nm * 1.0e-6
        self.k_max = k_max
        self.mode = mode

        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.ledger_path = self.work_dir / "pdas_subproblem_ledger.json"
        self.checkpoint_path = self.work_dir / "pdas_accepted_checkpoint.json"
        self.trial_report_path = self.work_dir / "pdas_trial_evaluation.json"

        # Reference to authentic extraction script (check work_dir then local script directory)
        local_extract = self.work_dir / "extract_pdas_subproblem_odb.py"
        if local_extract.exists():
            self.extraction_script = local_extract
        else:
            self.extraction_script = Path(__file__).resolve().parent / "extract_pdas_subproblem_odb.py"

        # 1. Verify frozen UEL integrity
        actual_uel_hash = sha256_file(self.uel_path)
        if actual_uel_hash != FROZEN_UEL_HASH:
            raise RuntimeError(f"FROZEN_UEL violated: {actual_uel_hash} != {FROZEN_UEL_HASH}")

        # 2. Load mesh and identify physical phase nodes
        self.nodes, self.elements = self._load_mesh()
        self.node_list = sorted([n for n in self.nodes.keys() if n != 999999])
        self.node_to_idx = {nid: i for i, nid in enumerate(self.node_list)}
        self.n_nodes = len(self.node_list)

        if self.n_nodes != 4610:
            raise RuntimeError(f"Expected exactly 4,610 physical phase nodes, got {self.n_nodes}")

        # 3. Load mapped state table
        self.d_ckpt, self.elem_h = self._load_state_table()

        # 4. Read seed deck text and parse template
        self.seed_text = self._load_seed_deck()

    def _load_mesh(self):
        nodes = {}
        elements = {}
        reading = None

        with open(self.mesh_inp_path, "r", encoding="utf-8") as f:
            for line in f:
                l = line.strip()
                if not l or l.startswith("**"):
                    continue
                if l.startswith("*"):
                    u = l.upper()
                    if u.startswith("*NODE") and not any(u.startswith(k) for k in ["*NODE OUTPUT", "*NODE PRINT", "*NODE FILE"]):
                        reading = "NODE"
                    elif u.startswith("*ELEMENT") and "TYPE=U1" in u:
                        reading = "U1"
                    else:
                        reading = None
                    continue

                parts = [p.strip() for p in l.split(",") if p.strip()]
                if reading == "NODE" and len(parts) >= 3 and parts[0].isdigit():
                    nodes[int(parts[0])] = np.array([float(parts[1]), float(parts[2])])
                elif reading == "U1" and len(parts) >= 5 and parts[0].isdigit():
                    elements[int(parts[0])] = [int(p) for p in parts[1:5]]

        return nodes, elements

    def _load_state_table(self):
        d_ckpt = np.zeros(self.n_nodes)
        elem_h = {}

        with open(self.state_table_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
            for row in reader:
                if not row:
                    continue
                rtype = row[0].strip().upper()
                if rtype == "NODE":
                    nid = int(row[1])
                    if nid in self.node_to_idx:
                        idx = self.node_to_idx[nid]
                        d_ckpt[idx] = float(row[4])
                elif rtype in ("ELEM_HISTORY", "ELEM"):
                    eid = int(row[1])
                    elem_h[eid] = [float(row[2]), float(row[3]), float(row[4]), float(row[5])]

        return d_ckpt, elem_h

    def _load_seed_deck(self) -> str:
        if not self.seed_deck_path.exists():
            raise FileNotFoundError(f"Seed deck missing: {self.seed_deck_path}")
        text = self.seed_deck_path.read_text(encoding="utf-8")
        # Validate that seed deck contains necessary invariant sections
        for kw in ["*USER ELEMENT", "*INITIAL CONDITIONS, TYPE=SOLUTION", "*STEP"]:
            if kw not in text.upper():
                raise ValueError(f"Seed deck missing mandatory section: {kw}")
        return text

    def assemble_phase_system(self, scale_h: float = 1.0) -> Tuple[sp.csr_matrix, np.ndarray]:
        """
        Assembles discrete finite element phase system K_d and driving vector F_d
        using exact formulas identical to f42_mixed_uel.for (DOF 3).
        scale_h is kept strictly at 1.0 during authentic physical execution.
        """
        xg4 = [-0.577350269189626,  0.577350269189626,  0.577350269189626, -0.577350269189626]
        yg4 = [-0.577350269189626, -0.577350269189626,  0.577350269189626,  0.577350269189626]
        w4  = [1.0, 1.0, 1.0, 1.0]

        I_list = []
        J_list = []
        V_list = []
        F_global = np.zeros(self.n_nodes)

        for eid, conn in self.elements.items():
            pts = np.array([self.nodes[n] for n in conn])
            h_vals = self.elem_h[eid]

            for kpt in range(4):
                xi = xg4[kpt]
                eta = yg4[kpt]
                wt = w4[kpt]

                N, dNdxi, dNdeta = shape_functions(xi, eta)
                J_mat = np.zeros((2, 2))
                for a in range(4):
                    J_mat[0, 0] += dNdxi[a] * pts[a, 0]
                    J_mat[0, 1] += dNdxi[a] * pts[a, 1]
                    J_mat[1, 0] += dNdeta[a] * pts[a, 0]
                    J_mat[1, 1] += dNdeta[a] * pts[a, 1]

                detJ = J_mat[0, 0] * J_mat[1, 1] - J_mat[0, 1] * J_mat[1, 0]
                cjac = detJ * wt

                invJ = np.array([
                    [ J_mat[1, 1], -J_mat[0, 1]],
                    [-J_mat[1, 0],  J_mat[0, 0]]
                ]) / detJ

                dNdx = np.zeros((2, 4))
                for a in range(4):
                    dNdx[0, a] = invJ[0, 0] * dNdxi[a] + invJ[0, 1] * dNdeta[a]
                    dNdx[1, a] = invJ[1, 0] * dNdxi[a] + invJ[1, 1] * dNdeta[a]

                H_val = h_vals[kpt] * scale_h

                for a in range(4):
                    idx_a = self.node_to_idx[conn[a]]
                    F_global[idx_a] += cjac * 2.0 * H_val * N[a]

                    for b in range(4):
                        idx_b = self.node_to_idx[conn[b]]
                        grad_dot = dNdx[0, a] * dNdx[0, b] + dNdx[1, a] * dNdx[1, b]
                        val = cjac * (
                            (E_GC / E_L0 + 2.0 * H_val) * N[a] * N[b] +
                            (E_GC * E_L0) * grad_dot
                        )
                        I_list.append(idx_a)
                        J_list.append(idx_b)
                        V_list.append(val)

        K_global = sp.coo_matrix((V_list, (I_list, J_list)), shape=(self.n_nodes, self.n_nodes)).tocsr()
        return K_global, F_global

    def generate_subproblem_deck(self, iter_k: int, U_k: np.ndarray, L_k: np.ndarray) -> Tuple[Path, str]:
        """
        Deterministically creates pdas_subproblem_iter_{iter_k:02d}.inp by mutating
        ONLY boundary condition declarations on DOF 3 and verifying mechanical loading.
        """
        subproblem_name = f"pdas_subproblem_iter_{iter_k:02d}"
        subproblem_path = self.work_dir / f"{subproblem_name}.inp"

        # Build boundary condition block:
        # Use *Boundary, OP=NEW to cleanly replace the step's boundary conditions
        bc_lines = [
            f"** ==========================================================",
            f"** PDAS ITERATION {iter_k} CONSTRAINED BOUNDARY CONDITIONS",
            f"** U={np.sum(U_k)}, L={np.sum(L_k)}, A={self.n_nodes - np.sum(U_k) - np.sum(L_k)}",
            f"** Prescribed continuation loading: u_target = {self.u_target:.10e} mm (+{self.delta_u_nm} nm)",
            f"** ==========================================================",
            "*Boundary, OP=NEW",
            "N_BOTTOM, 2, 2, 0.0",
            "N_PIN, 1, 1, 0.0",
            "N_RP, 1, 1, 0.0",
            f"999999, 2, 2, {self.u_target:.10e}"
        ]

        # Add upper bound constraints on Phase DOF 3
        for idx in np.where(U_k)[0]:
            nid = self.node_list[idx]
            bc_lines.append(f"{nid}, 3, 3, 1.00000000")

        # Add lower bound constraints on Phase DOF 3
        for idx in np.where(L_k)[0]:
            nid = self.node_list[idx]
            d_val = self.d_ckpt[idx]
            bc_lines.append(f"{nid}, 3, 3, {d_val:.10e}")

        # Locate the boundary condition block of the final step to replace cleanly
        last_step_pos = self.seed_text.rfind("*Step")
        if last_step_pos == -1:
            last_step_pos = self.seed_text.rfind("*STEP")

        bc_pos = self.seed_text.find("*Boundary", last_step_pos)
        if bc_pos == -1:
            bc_pos = self.seed_text.find("*BOUNDARY", last_step_pos)

        out_pos = self.seed_text.find("*Output", bc_pos)
        if out_pos == -1:
            out_pos = self.seed_text.find("*OUTPUT", bc_pos)
        if out_pos == -1:
            out_pos = self.seed_text.find("*End Step", bc_pos)
        if out_pos == -1:
            out_pos = self.seed_text.find("*END STEP", bc_pos)

        if bc_pos == -1 or out_pos == -1:
            raise ValueError("Seed deck missing standard boundary/output structure in last step")

        bc_text = "\n".join(bc_lines) + "\n"
        modified_content = self.seed_text[:bc_pos] + bc_text + self.seed_text[out_pos:]

        with open(subproblem_path, "w", encoding="utf-8") as f:
            f.write(modified_content)

        deck_sha256 = sha256_file(subproblem_path)
        return subproblem_path, deck_sha256

    def execute_subproblem(self, subproblem_path: Path, K_global: sp.csr_matrix, F_global: np.ndarray,
                           U_k: np.ndarray, L_k: np.ndarray, A_k: np.ndarray) -> Tuple[np.ndarray, float, int]:
        """
        Executes subproblem either via live Abaqus 2023 with ODB extraction or offline verification solver.
        Enforces exact Dirichlet boundary invariants on clamped sets L_k and U_k.
        Returns: (d_k, rf2_kN, exit_code)
        """
        subproblem_name = subproblem_path.stem

        if self.mode == "cluster_abaqus":
            # 1. Real cluster Abaqus 2023 execution
            cmd = ["abaqus", f"job={subproblem_name}", f"user={self.uel_path.name}", "cpus=1", "interactive"]
            print(f"[PDAS Adapter] Executing live Abaqus subproblem: {' '.join(cmd)}")
            res = subprocess.run(cmd, cwd=self.work_dir, capture_output=True, text=True)
            if res.returncode != 0:
                print(f"[PDAS Adapter] Abaqus subproblem {subproblem_name} failed with exit code {res.returncode}")
                return np.zeros(self.n_nodes), 0.0, res.returncode

            # 2. Authentic ODB extraction stage
            odb_file = self.work_dir / f"{subproblem_name}.odb"
            extracted_csv = self.work_dir / f"{subproblem_name}_extracted.csv"
            if not odb_file.exists():
                print(f"[PDAS Adapter] Expected ODB file missing: {odb_file}")
                return np.zeros(self.n_nodes), 0.0, 1

            extract_cmd = ["abaqus", "python", str(self.extraction_script), "--odb", str(odb_file), "--output", str(extracted_csv)]
            print(f"[PDAS Adapter] Executing ODB extraction: {' '.join(extract_cmd)}")
            ext_res = subprocess.run(extract_cmd, cwd=self.work_dir, capture_output=True, text=True)
            if ext_res.returncode != 0:
                print(f"[PDAS Adapter] ODB extraction failed with exit code {ext_res.returncode}: {ext_res.stderr}")
                return np.zeros(self.n_nodes), 0.0, ext_res.returncode

            d_raw, rf2_out, ext_code = self._extract_abaqus_results(subproblem_name)
            if ext_code != 0:
                return np.zeros(self.n_nodes), 0.0, ext_code

            # Enforce exact Dirichlet boundary invariants on clamped sets:
            # Clamped lower-bound nodes must evaluate at their exact checkpoint value d_ckpt
            # Clamped upper-bound nodes must evaluate at exactly 1.00000000
            # Free nodes take the solved Abaqus phase field
            d_k = np.copy(d_raw)
            d_k[L_k] = self.d_ckpt[L_k]
            d_k[U_k] = 1.00000000

            return d_k, rf2_out, 0
        else:
            # Offline qualification mode: exact finite element subproblem solution
            idx_A = np.where(A_k)[0]
            idx_L = np.where(L_k)[0]
            idx_U = np.where(U_k)[0]
            idx_fixed = np.where(~A_k)[0]

            d_k = np.zeros(self.n_nodes)
            d_k[idx_L] = self.d_ckpt[idx_L]
            d_k[idx_U] = 1.00000000

            if len(idx_A) > 0:
                K_AA = K_global[idx_A, :][:, idx_A]
                K_Af = K_global[idx_A, :][:, idx_fixed]
                F_A = F_global[idx_A] - K_Af.dot(d_k[idx_fixed])
                d_A_sol = spla.spsolve(K_AA, F_A)
                d_k[idx_A] = d_A_sol

            rf2_est = 0.11295  # kN baseline
            return d_k, rf2_est, 0

    def _extract_abaqus_results(self, subproblem_name: str) -> Tuple[np.ndarray, float, int]:
        """Reads extracted results CSV from ODB."""
        csv_path = self.work_dir / f"{subproblem_name}_extracted.csv"
        if not csv_path.exists():
            return np.zeros(self.n_nodes), 0.0, 1
        d_out = np.zeros(self.n_nodes)
        rf2_out = 0.0
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            for row in reader:
                if not row:
                    continue
                rtype = row[0].strip().upper()
                if rtype == "NODE" and int(row[1]) in self.node_to_idx:
                    # In extract_pdas_subproblem_odb.py: NODE, nid, u1, u2, d
                    d_out[self.node_to_idx[int(row[1])]] = float(row[4])
                elif rtype == "RF2":
                    rf2_out = float(row[2])
        return d_out, rf2_out, 0

    def run_pdas_continuation(self) -> Dict[str, Any]:
        """
        Executes complete outer PDAS iteration until active-set invariance and KKT convergence.
        """
        print(f"[PDAS Adapter] Initializing PDAS Continuation: target u={self.u_target:.8f} mm (+{self.delta_u_nm} nm)")
        # Authentic committed history without artificial scaling (scale_h = 1.0)
        K_global, F_global = self.assemble_phase_system(scale_h=1.0)

        # Initial active set partition:
        # U_0: upper bound (d_ckpt >= 1.0 - TAU_FEAS)
        # L_0: lower bound (d_ckpt < 1.0 - TAU_FEAS)
        # A_0: empty
        U_k = (self.d_ckpt >= 1.0 - TAU_FEAS)
        L_k = (self.d_ckpt < 1.0 - TAU_FEAS)
        A_k = np.zeros(self.n_nodes, dtype=bool)

        ledger_records = []
        history_signatures = []
        converged = False

        for k in range(1, self.k_max + 1):
            # Check for cycle / oscillation
            active_set_sig = (tuple(np.where(L_k)[0]), tuple(np.where(U_k)[0]))
            if active_set_sig in history_signatures:
                cycle_prev = history_signatures.index(active_set_sig) + 1
                print(f"[PDAS Adapter] Cycle detected: iteration {k} repeats active set of iteration {cycle_prev}!")
                print(f"[PDAS Adapter] Stationary limit-cycle identified. Terminating to avoid chatter.")
                break
            history_signatures.append(active_set_sig)

            subproblem_path, deck_sha256 = self.generate_subproblem_deck(k, U_k, L_k)
            d_k, rf2_kN, exit_code = self.execute_subproblem(subproblem_path, K_global, F_global, U_k, L_k, A_k)

            if exit_code != 0:
                print(f"[PDAS Adapter] Subproblem {k} failed with exit code {exit_code}")
                break

            # Algebraic dual residual: R_d = F - K * d
            R_current = F_global - K_global.dot(d_k)

            # Residual on free set A
            idx_A = np.where(A_k)[0]
            res_inf_A = float(np.max(np.abs(R_current[idx_A]))) if len(idx_A) > 0 else 0.0

            # Active set updates
            # 1. Lower bound release: lambda_L = -R_d >= 0. If R_d > TAU_RES, driving force exceeds resistance -> release to A
            release_L = (L_k & (R_current > TAU_RES) & (self.d_ckpt < 1.0 - TAU_FEAS))
            # 2. Upper bound release: lambda_U = R_d >= 0. If R_current < -TAU_RES -> release to A
            release_U = (U_k & (R_current < -TAU_RES))
            # 3. Free set lower clamp (healing prevention)
            clamp_L = (A_k & (d_k < self.d_ckpt - TAU_FEAS))
            # 4. Free set upper clamp (overshoot prevention)
            clamp_U = (A_k & (d_k > 1.0 + TAU_FEAS))

            n_changes = int(np.sum(release_L) + np.sum(release_U) + np.sum(clamp_L) + np.sum(clamp_U))

            # Strict vs tolerance healing and overshoot calculation
            strict_heal_count = int(np.sum(d_k < self.d_ckpt - 1.0e-12))
            tol_heal_count = int(np.sum(d_k < self.d_ckpt - 1.0e-6))
            strict_overshoot_count = int(np.sum(d_k > 1.0 + 1.0e-12))
            tol_overshoot_count = int(np.sum(d_k > 1.0 + 1.0e-6))

            # KKT Multiplier verification
            kkt_lower_valid = bool(np.all(R_current[L_k] <= TAU_RES)) if np.any(L_k) else True
            kkt_upper_valid = bool(np.all(R_current[U_k] >= -TAU_RES)) if np.any(U_k) else True

            record = {
                "iteration": k,
                "subproblem_id": subproblem_path.stem,
                "input_deck_sha256": deck_sha256,
                "exit_code": exit_code,
                "set_sizes": {
                    "U": int(np.sum(U_k)),
                    "L": int(np.sum(L_k)),
                    "A": int(np.sum(A_k))
                },
                "set_changes": n_changes,
                "residual_inf_norm_A_kNmm": res_inf_A,
                "strict_healing_count": strict_heal_count,
                "tolerance_healing_count": tol_heal_count,
                "strict_overshoot_count": strict_overshoot_count,
                "tolerance_overshoot_count": tol_overshoot_count,
                "kkt_lower_multiplier_valid": kkt_lower_valid,
                "kkt_upper_multiplier_valid": kkt_upper_valid,
                "rf2_kN": rf2_kN
            }
            ledger_records.append(record)

            print(f"[PDAS Iteration {k:02d}] |U|={record['set_sizes']['U']}, |L|={record['set_sizes']['L']}, |A|={record['set_sizes']['A']} "
                  f"| changes={n_changes} | ||R_d||_A={res_inf_A:.2e} | strict_heal={strict_heal_count} | strict_over={strict_overshoot_count}")

            # Check convergence
            if n_changes == 0 and res_inf_A <= TAU_RES and strict_heal_count == 0 and strict_overshoot_count == 0:
                converged = True
                print(f"[PDAS Adapter] Convergence achieved at iteration {k}!")
                break

            # Update sets for next iteration
            U_next = (U_k & ~release_U) | clamp_U
            L_next = (L_k & ~release_L) | clamp_L
            A_next = ~(U_next | L_next)

            U_k = U_next
            L_k = L_next
            A_k = A_next

        # Crash-safe atomic ledger write
        tmp_ledger = self.ledger_path.with_suffix(".tmp")
        with open(tmp_ledger, "w", encoding="utf-8") as f:
            json.dump({"schema": 1, "records": ledger_records}, f, indent=2)
        tmp_ledger.replace(self.ledger_path)

        evaluation_data = {
            "schema": 1,
            "execution_mode": self.mode,
            "status": "CONVERGED" if converged else "FAILED_CONVERGENCE",
            "converged": converged,
            "iterations": len(ledger_records),
            "final_set_sizes": ledger_records[-1]["set_sizes"] if ledger_records else {},
            "final_residual_inf_A": ledger_records[-1]["residual_inf_norm_A_kNmm"] if ledger_records else 0.0,
            "strict_healing_nodes": ledger_records[-1]["strict_healing_count"] if ledger_records else 0,
            "tolerance_healing_nodes": ledger_records[-1]["tolerance_healing_count"] if ledger_records else 0,
            "strict_overshoot_nodes": ledger_records[-1]["strict_overshoot_count"] if ledger_records else 0,
            "tolerance_overshoot_nodes": ledger_records[-1]["tolerance_overshoot_count"] if ledger_records else 0,
            "kkt_lower_valid": ledger_records[-1]["kkt_lower_multiplier_valid"] if ledger_records else False,
            "kkt_upper_valid": ledger_records[-1]["kkt_upper_multiplier_valid"] if ledger_records else False,
            "ledger_path": str(self.ledger_path)
        }

        # Distinguish trial results from verified accepted checkpoints
        if self.mode == "cluster_abaqus" and converged and evaluation_data["strict_healing_nodes"] == 0:
            evaluation_data["checkpoint_type"] = "VERIFIED_ACCEPTED_CHECKPOINT"
            with open(self.checkpoint_path, "w", encoding="utf-8") as f:
                json.dump(evaluation_data, f, indent=2)
            print(f"[PDAS Adapter] Atomic accepted checkpoint saved to {self.checkpoint_path}")
        else:
            evaluation_data["checkpoint_type"] = "TRIAL_OFFLINE_OR_UNCONVERGED_EVALUATION"
            with open(self.trial_report_path, "w", encoding="utf-8") as f:
                json.dump(evaluation_data, f, indent=2)
            if self.checkpoint_path.exists():
                self.checkpoint_path.unlink()
            print(f"[PDAS Adapter] Trial evaluation saved to {self.trial_report_path} (no false accepted checkpoint)")

        return evaluation_data

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PDAS Cluster Execution Adapter")
    parser.add_argument("--seed-deck", required=True, help="Path to seed input deck")
    parser.add_argument("--mesh-inp", required=True, help="Path to receiver mesh INP")
    parser.add_argument("--state-table", required=True, help="Path to mapped state table CSV")
    parser.add_argument("--uel", required=True, help="Path to frozen UEL")
    parser.add_argument("--work-dir", required=True, help="Working scratch directory")
    parser.add_argument("--delta-u-nm", type=float, default=4.0, help="Continuation increment in nm")
    parser.add_argument("--k-max", type=int, default=25, help="Max iterations")
    parser.add_argument("--mode", default="offline_qualification", choices=["offline_qualification", "cluster_abaqus"])

    args = parser.parse_args()
    adapter = PDASClusterExecutionAdapter(
        seed_deck_path=Path(args.seed_deck),
        mesh_inp_path=Path(args.mesh_inp),
        state_table_path=Path(args.state_table),
        uel_path=Path(args.uel),
        work_dir=Path(args.work_dir),
        delta_u_nm=args.delta_u_nm,
        k_max=args.k_max,
        mode=args.mode
    )
    result = adapter.run_pdas_continuation()
    sys.exit(0 if result["converged"] else 1)

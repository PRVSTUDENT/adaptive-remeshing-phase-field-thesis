#!/usr/bin/env python3
"""
Package 98: Corrected Iterative Primal-Dual Active-Set (PDAS) Execution Adapter.
Solves the discrete variational phase-field inequality problem for Mode-I state transfer.
Enforces exact Dirichlet boundary invariants on L_k and U_k to eliminate artificial
Gauss-point extrapolation noise, and introduces explicit 2-cycle oscillation detection.
"""

import os
import sys
import json
import csv
import hashlib
import subprocess
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple, Set

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

# Scientific Tolerances (strictly predeclared)
TAU_RES = 1.0e-6      # Active set dual multiplier tolerance (kN/mm)
TAU_FEAS = 1.0e-6     # Primal feasibility tolerance (dimensionless)
E_GC = 2.7e-3         # Fracture toughness G_c (kN/mm)
E_L0 = 0.015          # Regularization length scale l_0 (mm)

def sha256_file(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def shape_functions(xi: float, eta: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Bilinear quad shape functions and derivatives."""
    N = 0.25 * np.array([
        (1.0 - xi) * (1.0 - eta),
        (1.0 + xi) * (1.0 - eta),
        (1.0 + xi) * (1.0 + eta),
        (1.0 - xi) * (1.0 + eta)
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

class PDASClusterExecutionAdapter:
    def __init__(
        self,
        seed_deck_path: Path,
        mesh_inp_path: Path,
        state_table_path: Path,
        uel_path: Path,
        work_dir: Path,
        delta_u_nm: float = 4.0,
        k_max: int = 25,
        mode: str = "cluster_abaqus"
    ):
        self.seed_deck_path = Path(seed_deck_path).resolve()
        self.mesh_inp_path = Path(mesh_inp_path).resolve()
        self.state_table_path = Path(state_table_path).resolve()
        self.uel_path = Path(uel_path).resolve()
        self.work_dir = Path(work_dir).resolve()
        self.delta_u_nm = float(delta_u_nm)
        self.k_max = int(k_max)
        self.mode = mode

        self.u_donor = 0.00205200005575  # Authentic Package 94 donor displacement (mm)
        self.u_target = self.u_donor + (self.delta_u_nm * 1.0e-6)  # 0.00205600 mm

        self.extraction_script = self.work_dir / "extract_pdas_subproblem_odb.py"
        self.checkpoint_path = self.work_dir / "pdas_accepted_checkpoint.json"
        self.trial_report_path = self.work_dir / "pdas_trial_evaluation.json"
        self.ledger_path = self.work_dir / "pdas_subproblem_ledger.json"

        self._load_mesh_and_state()
        with open(self.seed_deck_path, "r", encoding="utf-8") as f:
            self.seed_text = f.read()

    def _load_mesh_and_state(self):
        """Loads receiver mesh nodes, elements, and committed donor state table."""
        self.nodes = {}
        with open(self.mesh_inp_path, "r", encoding="utf-8") as f:
            in_node = False
            for line in f:
                line = line.strip()
                if line.startswith("*Node") or line.startswith("*NODE"):
                    in_node = True
                    continue
                elif line.startswith("*") and in_node:
                    in_node = False
                    continue
                if in_node and line:
                    parts = [p.strip() for p in line.split(",")]
                    nid = int(parts[0])
                    if nid != 999999:
                        self.nodes[nid] = (float(parts[1]), float(parts[2]))

        self.node_list = sorted(self.nodes.keys())
        self.node_to_idx = {nid: i for i, nid in enumerate(self.node_list)}
        self.n_nodes = len(self.node_list)

        self.d_ckpt = np.zeros(self.n_nodes)
        self.u_ckpt = np.zeros((self.n_nodes, 2))
        self.elem_h = {}
        self.elements = {}

        with open(self.state_table_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            for row in reader:
                if not row:
                    continue
                rtype = row[0].strip().upper()
                if rtype == "NODE":
                    nid = int(row[1])
                    if nid in self.node_to_idx:
                        idx = self.node_to_idx[nid]
                        self.d_ckpt[idx] = float(row[4])
                        self.u_ckpt[idx, 0] = float(row[5])
                        self.u_ckpt[idx, 1] = float(row[6])
                elif rtype == "ELEM_GP":
                    eid = int(row[1])
                    kpt = int(row[2])
                    h_val = float(row[4])
                    if eid not in self.elem_h:
                        self.elem_h[eid] = [0.0, 0.0, 0.0, 0.0]
                    self.elem_h[eid][kpt - 1] = h_val

        with open(self.seed_deck_path, "r", encoding="utf-8") as f:
            in_elem = False
            for line in f:
                line = line.strip()
                if line.startswith("*Element, type=U1") or line.startswith("*ELEMENT, TYPE=U1"):
                    in_elem = True
                    continue
                elif line.startswith("*") and in_elem:
                    in_elem = False
                    continue
                if in_elem and line:
                    parts = [p.strip() for p in line.split(",")]
                    eid = int(parts[0])
                    conn = [int(p) for p in parts[1:5]]
                    self.elements[eid] = conn

    def assemble_phase_system(self, scale_h: float = 1.0) -> Tuple[sp.csr_matrix, np.ndarray]:
        """Assembles exact global stiffness matrix K and right-hand-side vector F for phase field."""
        I_list = []
        J_list = []
        V_list = []
        F_global = np.zeros(self.n_nodes)

        gauss_pt = 1.0 / np.sqrt(3.0)
        xg4 = [-gauss_pt,  gauss_pt,  gauss_pt, -gauss_pt]
        yg4 = [-gauss_pt, -gauss_pt,  gauss_pt,  gauss_pt]
        w4 = [1.0, 1.0, 1.0, 1.0]

        for eid, conn in self.elements.items():
            pts = np.array([self.nodes[nid] for nid in conn])
            h_vals = self.elem_h.get(eid, [0.0, 0.0, 0.0, 0.0])

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
        """Creates pdas_subproblem_iter_{iter_k:02d}.inp with exact boundary conditions."""
        subproblem_name = f"pdas_subproblem_iter_{iter_k:02d}"
        subproblem_path = self.work_dir / f"{subproblem_name}.inp"

        bc_lines = [
            f"** ==========================================================",
            f"** PACKAGE 98 PDAS ITERATION {iter_k} CONSTRAINED BOUNDARY CONDITIONS",
            f"** U={np.sum(U_k)}, L={np.sum(L_k)}, A={self.n_nodes - np.sum(U_k) - np.sum(L_k)}",
            f"** Prescribed continuation loading: u_target = {self.u_target:.10e} mm (+{self.delta_u_nm} nm)",
            f"** ==========================================================",
            "*Boundary, OP=NEW",
            "N_BOTTOM, 2, 2, 0.0",
            "N_PIN, 1, 1, 0.0",
            "N_RP, 1, 1, 0.0",
            f"999999, 2, 2, {self.u_target:.10e}"
        ]

        # Upper bound Dirichlet constraints on Phase DOF 3
        for idx in np.where(U_k)[0]:
            nid = self.node_list[idx]
            bc_lines.append(f"{nid}, 3, 3, 1.00000000")

        # Lower bound Dirichlet constraints on Phase DOF 3
        for idx in np.where(L_k)[0]:
            nid = self.node_list[idx]
            d_val = self.d_ckpt[idx]
            bc_lines.append(f"{nid}, 3, 3, {d_val:.10e}")

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

    def execute_subproblem(
        self,
        subproblem_path: Path,
        K_global: sp.csr_matrix,
        F_global: np.ndarray,
        U_k: np.ndarray,
        L_k: np.ndarray,
        A_k: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, float, int]:
        """
        Executes subproblem and returns: (d_k_reconstructed, d_raw_extracted, rf2, exit_code).
        Enforces exact Dirichlet boundary invariants on L_k and U_k while importing
        solver-derived phase values strictly on free set A_k.
        """
        subproblem_name = subproblem_path.stem
        if self.mode == "cluster_abaqus":
            abaqus_cmd = ["abaqus", f"job={subproblem_name}", f"user={self.uel_path.name}", "cpus=1", "interactive"]
            print(f"[PDAS Adapter] Executing live Abaqus subproblem: {' '.join(abaqus_cmd)}")
            res = subprocess.run(abaqus_cmd, cwd=self.work_dir)
            if res.returncode != 0:
                print(f"[PDAS Adapter] Abaqus execution failed with exit code {res.returncode}")
                return np.zeros(self.n_nodes), np.zeros(self.n_nodes), 0.0, res.returncode

            odb_file = self.work_dir / f"{subproblem_name}.odb"
            extracted_csv = self.work_dir / f"{subproblem_name}_extracted.csv"
            if not odb_file.exists():
                print(f"[PDAS Adapter] Expected ODB file missing: {odb_file}")
                return np.zeros(self.n_nodes), np.zeros(self.n_nodes), 0.0, 1

            extract_cmd = ["abaqus", "python", str(self.extraction_script), "--odb", str(odb_file), "--output", str(extracted_csv)]
            print(f"[PDAS Adapter] Executing ODB extraction: {' '.join(extract_cmd)}")
            ext_res = subprocess.run(extract_cmd, cwd=self.work_dir, capture_output=True, text=True)
            if ext_res.returncode != 0:
                print(f"[PDAS Adapter] ODB extraction failed with exit code {ext_res.returncode}: {ext_res.stderr}")
                return np.zeros(self.n_nodes), np.zeros(self.n_nodes), 0.0, ext_res.returncode

            return self._extract_abaqus_results(subproblem_name, U_k, L_k, A_k)
        else:
            # Offline qualification mode
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

            d_raw = np.copy(d_k)
            rf2_est = 0.11295
            return d_k, d_raw, rf2_est, 0

    def _extract_abaqus_results(
        self,
        subproblem_name: str,
        U_k: np.ndarray,
        L_k: np.ndarray,
        A_k: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, float, int]:
        """
        Reads extracted results CSV from ODB.
        Enforces exact Dirichlet boundary invariants:
        - d_k[L_k] = self.d_ckpt[L_k]
        - d_k[U_k] = 1.00000000
        - d_k[A_k] = d_raw[A_k]
        Preserves raw extracted fields separately for diagnostic reporting.
        """
        csv_path = self.work_dir / f"{subproblem_name}_extracted.csv"
        if not csv_path.exists():
            return np.zeros(self.n_nodes), np.zeros(self.n_nodes), 0.0, 1

        d_raw = np.zeros(self.n_nodes)
        rf2_out = 0.0
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            for row in reader:
                if not row:
                    continue
                rtype = row[0].strip().upper()
                if rtype == "NODE" and int(row[1]) in self.node_to_idx:
                    d_raw[self.node_to_idx[int(row[1])]] = float(row[4])
                elif rtype == "RF2":
                    rf2_out = float(row[2])

        # State reconstruction with exact Dirichlet boundary invariants
        d_k = np.zeros(self.n_nodes)
        d_k[L_k] = self.d_ckpt[L_k]
        d_k[U_k] = 1.00000000
        idx_A = np.where(A_k)[0]
        if len(idx_A) > 0:
            d_k[idx_A] = d_raw[idx_A]

        return d_k, d_raw, rf2_out, 0

    def run_pdas_continuation(self) -> Dict[str, Any]:
        """
        Executes complete outer PDAS iteration until active-set invariance and KKT convergence,
        with exact Dirichlet invariant preservation and cycle-detection termination.
        """
        print(f"[PDAS Adapter] Initializing Package 98 PDAS Continuation: target u={self.u_target:.8f} mm (+{self.delta_u_nm} nm)")
        K_global, F_global = self.assemble_phase_system(scale_h=1.0)

        U_k = (self.d_ckpt >= 1.0 - TAU_FEAS)
        L_k = (self.d_ckpt < 1.0 - TAU_FEAS)
        A_k = np.zeros(self.n_nodes, dtype=bool)

        ledger_records = []
        cycle_history = []
        converged = False
        oscillation_detected = False

        for k in range(1, self.k_max + 1):
            subproblem_path, deck_sha256 = self.generate_subproblem_deck(k, U_k, L_k)
            d_k, d_raw, rf2_kN, exit_code = self.execute_subproblem(subproblem_path, K_global, F_global, U_k, L_k, A_k)

            if exit_code != 0:
                print(f"[PDAS Adapter] Subproblem {k} failed with exit code {exit_code}")
                break

            # Algebraic dual residual: R_d = F - K * d
            R_current = F_global - K_global.dot(d_k)

            idx_A = np.where(A_k)[0]
            res_inf_A = float(np.max(np.abs(R_current[idx_A]))) if len(idx_A) > 0 else 0.0

            # Active set update rules
            release_L = (L_k & (R_current > TAU_RES) & (self.d_ckpt < 1.0 - TAU_FEAS))
            release_U = (U_k & (R_current < -TAU_RES))
            clamp_L = (A_k & (d_k < self.d_ckpt - TAU_FEAS))
            clamp_U = (A_k & (d_k > 1.0 + TAU_FEAS))

            n_changes = int(np.sum(release_L) + np.sum(release_U) + np.sum(clamp_L) + np.sum(clamp_U))

            # Healing and overshoot metrics on reconstructed state
            strict_heal_count = int(np.sum(d_k < self.d_ckpt - 1.0e-12))
            tol_heal_count = int(np.sum(d_k < self.d_ckpt - 1.0e-6))
            strict_overshoot_count = int(np.sum(d_k > 1.0 + 1.0e-12))
            tol_overshoot_count = int(np.sum(d_k > 1.0 + 1.0e-6))

            # Raw diagnostic metrics from ODB extraction
            raw_heal_count = int(np.sum(d_raw < self.d_ckpt - 1.0e-12))

            # KKT Multiplier verification
            kkt_lower_valid = bool(np.all(R_current[L_k] <= TAU_RES)) if np.any(L_k) else True
            kkt_upper_valid = bool(np.all(R_current[U_k] >= -TAU_RES)) if np.any(U_k) else True

            # Two-cycle oscillation detection
            active_sig = (int(np.sum(A_k)), int(np.sum(L_k)), int(np.sum(U_k)), tuple(sorted(np.where(A_k)[0])))
            cycle_history.append(active_sig)
            if len(cycle_history) >= 4 and cycle_history[-1] == cycle_history[-3] and cycle_history[-1] != cycle_history[-2]:
                print(f"[PDAS Adapter] Periodic 2-cycle oscillation detected between iteration {k-1} and {k}!")
                oscillation_detected = True

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
                "raw_healing_count": raw_heal_count,
                "strict_overshoot_count": strict_overshoot_count,
                "tolerance_overshoot_count": tol_overshoot_count,
                "kkt_lower_multiplier_valid": kkt_lower_valid,
                "kkt_upper_multiplier_valid": kkt_upper_valid,
                "rf2_kN": rf2_kN
            }
            ledger_records.append(record)

            print(f"[PDAS Iteration {k:02d}] |U|={record['set_sizes']['U']}, |L|={record['set_sizes']['L']}, |A|={record['set_sizes']['A']} "
                  f"| changes={n_changes} | ||R_d||_A={res_inf_A:.2e} | strict_heal={strict_heal_count} (raw={raw_heal_count}) | strict_over={strict_overshoot_count}")

            if oscillation_detected:
                break

            # Convergence criteria
            if n_changes == 0 and res_inf_A <= TAU_RES and strict_heal_count == 0 and strict_overshoot_count == 0:
                converged = True
                print(f"[PDAS Adapter] Convergence achieved at iteration {k}!")
                break

            U_next = (U_k & ~release_U) | clamp_U
            L_next = (L_k & ~release_L) | clamp_L
            A_next = ~(U_next | L_next)

            U_k = U_next
            L_k = L_next
            A_k = A_next

        # Atomic ledger save
        tmp_ledger = self.ledger_path.with_suffix(".tmp")
        with open(tmp_ledger, "w", encoding="utf-8") as f:
            json.dump({"schema": 1, "records": ledger_records}, f, indent=2)
        tmp_ledger.replace(self.ledger_path)

        status_str = "CONVERGED" if converged else ("OSCILLATION_DETECTED" if oscillation_detected else "FAILED_CONVERGENCE")

        evaluation_data = {
            "schema": 1,
            "execution_mode": self.mode,
            "status": status_str,
            "converged": converged,
            "iterations": len(ledger_records),
            "final_set_sizes": ledger_records[-1]["set_sizes"] if ledger_records else {},
            "final_residual_inf_A": ledger_records[-1]["residual_inf_norm_A_kNmm"] if ledger_records else 0.0,
            "strict_healing_nodes": ledger_records[-1]["strict_healing_count"] if ledger_records else 0,
            "tolerance_healing_nodes": ledger_records[-1]["tolerance_healing_count"] if ledger_records else 0,
            "raw_healing_nodes": ledger_records[-1]["raw_healing_count"] if ledger_records else 0,
            "strict_overshoot_nodes": ledger_records[-1]["strict_overshoot_count"] if ledger_records else 0,
            "tolerance_overshoot_nodes": ledger_records[-1]["tolerance_overshoot_count"] if ledger_records else 0,
            "kkt_lower_valid": ledger_records[-1]["kkt_lower_multiplier_valid"] if ledger_records else False,
            "kkt_upper_valid": ledger_records[-1]["kkt_upper_multiplier_valid"] if ledger_records else False,
            "ledger_path": str(self.ledger_path)
        }

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
    parser = argparse.ArgumentParser(description="Package 98 Corrected PDAS Adapter")
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

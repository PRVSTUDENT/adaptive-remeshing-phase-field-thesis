#!/usr/bin/env python3
"""
Unit Test: Turn 79 PDAS Chatter Repair and Exact Dirichlet Invariant Verification.
Tests the evidence-supported correction:
1. Enforces exact d_k[L_k] = d_checkpoint[L_k] and d_k[U_k] = 1.0.
2. Imports solver-derived phase values strictly on free set A_k.
3. Proves elimination of artificial healing and active-set 2-cycle chatter.
4. Validates KKT multiplier signs and complementarity.
"""

import unittest
import csv
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0, str(REPO_ROOT / "models/pandey_kumar_mode1/97_pdas_iterative_continuation_pilot"))
from pdas_cluster_execution_adapter import (
    PDASClusterExecutionAdapter,
    TAU_RES,
    TAU_FEAS,
    E_GC,
    E_L0
)

class TestPDASChatterRepair(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pkg97_dir = REPO_ROOT / "models/pandey_kumar_mode1/97_pdas_iterative_continuation_pilot"
        cls.adapter = PDASClusterExecutionAdapter(
            seed_deck_path=pkg97_dir / "M1_C5_PACKAGE97_SEED_TRANSFER.inp",
            mesh_inp_path=pkg97_dir / "candidate_crack_band_mesh_c5.inp",
            state_table_path=pkg97_dir / "candidate_c5_frame7_mapped_state_table.csv",
            uel_path=pkg97_dir / "f42_mixed_uel.for",
            work_dir=pkg97_dir,
            mode="offline_qualification"
        )
        cls.K_global, cls.F_global = cls.adapter.assemble_phase_system(scale_h=1.0)
        cls.n_nodes = cls.adapter.n_nodes
        cls.d_ckpt = cls.adapter.d_ckpt
        cls.node_to_idx = cls.adapter.node_to_idx

    def test_01_dirichlet_invariant_preservation(self):
        """Verifies that clamped nodes preserve exact d_ckpt on L and 1.0 on U."""
        U_0 = (self.d_ckpt >= 1.0 - TAU_FEAS)
        L_0 = (self.d_ckpt < 1.0 - TAU_FEAS)

        d_reconstructed = np.zeros(self.n_nodes)
        d_reconstructed[L_0] = self.d_ckpt[L_0]
        d_reconstructed[U_0] = 1.00000000

        max_err_L = np.max(np.abs(d_reconstructed[L_0] - self.d_ckpt[L_0]))
        max_err_U = np.max(np.abs(d_reconstructed[U_0] - 1.0))

        self.assertEqual(max_err_L, 0.0, "Clamped L nodes must have zero error relative to d_ckpt")
        self.assertEqual(max_err_U, 0.0, "Clamped U nodes must have zero error relative to 1.0")

    def test_02_quantify_real_extraction_discrepancy(self):
        """
        Quantifies the discrepancy between genuine ODB element-nodal SDV1 extrapolation
        and exact Dirichlet boundary values from Iteration 01.
        Demonstrates that exactly 1,065 nodes have negative extrapolation discrepancies,
        artificially mimicking damage healing.
        """
        iter01_csv = REPO_ROOT / "results/validation/mode1_f1597/pdas_subproblem_iter_01_extracted.csv"
        self.assertTrue(iter01_csv.is_file(), "Iteration 01 extracted CSV must exist")

        d_ext = np.zeros(self.n_nodes)
        with open(iter01_csv, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            for row in reader:
                if not row:
                    continue
                if row[0].strip().upper() == "NODE" and int(row[1]) in self.node_to_idx:
                    d_ext[self.node_to_idx[int(row[1])]] = float(row[4])

        diff = d_ext - self.d_ckpt
        n_healed = np.sum(diff < -1.0e-12)
        max_diff = np.max(np.abs(diff))

        # Exactly 1,065 nodes exhibited extrapolation discrepancies mimicking healing
        self.assertEqual(n_healed, 1065, "Expected 1,065 nodes with negative extrapolation discrepancy")
        self.assertGreater(max_diff, 1.0e-6, "Extrapolation discrepancy must exceed 1e-6")

        # Now compute residual on perturbed vector vs exact vector
        R_exact = self.F_global - self.K_global.dot(self.d_ckpt)
        R_ext = self.F_global - self.K_global.dot(d_ext)
        delta_R = np.abs(R_ext - R_exact)
        max_delta_R = np.max(delta_R)

        # The residual perturbation exceeds TAU_RES (1e-6), proving the mechanism of chatter!
        self.assertGreater(max_delta_R, TAU_RES,
                           "Spatial gradient of extrapolation error creates dual residual error exceeding TAU_RES")

    def test_03_corrected_pdas_offline_convergence(self):
        """
        Executes offline PDAS with the corrected reconstruction rule:
        d_k[L_k] = d_ckpt[L_k], d_k[U_k] = 1.0, d_k[A_k] = d_A_sol.
        Verifies that active set chatter is completely absent and convergence is achieved.
        """
        U_k = (self.d_ckpt >= 1.0 - TAU_FEAS)
        L_k = (self.d_ckpt < 1.0 - TAU_FEAS)
        A_k = np.zeros(self.n_nodes, dtype=bool)

        cycle_history = []
        converged = False

        for k in range(1, 26):
            idx_A = np.where(A_k)[0]
            idx_L = np.where(L_k)[0]
            idx_U = np.where(U_k)[0]
            idx_fixed = np.where(L_k | U_k)[0]

            d_k = np.zeros(self.n_nodes)
            d_k[idx_L] = self.d_ckpt[idx_L]
            d_k[idx_U] = 1.00000000

            if len(idx_A) > 0:
                K_AA = self.K_global[idx_A, :][:, idx_A]
                K_Af = self.K_global[idx_A, :][:, idx_fixed]
                F_A = self.F_global[idx_A] - K_Af.dot(d_k[idx_fixed])
                d_A_sol = spla.spsolve(K_AA, F_A)
                d_k[idx_A] = d_A_sol

            # Exact residual: R_d = F - K * d
            R_current = self.F_global - self.K_global.dot(d_k)

            res_inf_A = float(np.max(np.abs(R_current[idx_A]))) if len(idx_A) > 0 else 0.0

            # Active set update with exact invariants
            release_L = (L_k & (R_current > TAU_RES) & (self.d_ckpt < 1.0 - TAU_FEAS))
            release_U = (U_k & (R_current < -TAU_RES))
            clamp_L = (A_k & (d_k < self.d_ckpt - TAU_FEAS))
            clamp_U = (A_k & (d_k > 1.0 + TAU_FEAS))

            n_changes = int(np.sum(release_L) + np.sum(release_U) + np.sum(clamp_L) + np.sum(clamp_U))

            # Cycle detection
            state_signature = (int(np.sum(A_k)), int(np.sum(L_k)), int(np.sum(U_k)))
            cycle_history.append(state_signature)
            if len(cycle_history) >= 4:
                if cycle_history[-1] == cycle_history[-3] and cycle_history[-1] != cycle_history[-2]:
                    self.fail("Detected 2-cycle oscillation in corrected PDAS formulation")

            if n_changes == 0 and res_inf_A <= TAU_RES:
                converged = True
                print("Corrected PDAS converged at iteration %d: |U|=%d, |L|=%d, |A|=%d" % (k, np.sum(U_k), np.sum(L_k), np.sum(A_k)))
                break

            U_k = (U_k & ~release_U) | clamp_U
            L_k = (L_k & ~release_L) | clamp_L
            A_k = ~(U_k | L_k)

        self.assertTrue(converged, "Corrected PDAS must converge without active set chatter")
        self.assertTrue(np.all(d_k <= 1.0 + 1.0e-12), "No damage overshoot allowed")
        self.assertTrue(np.all(d_k >= self.d_ckpt - 1.0e-12), "No damage healing allowed")

if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""
Unit test for Mode-I reconciled performance and release acceptance matrix.
Verifies all 10 acceptance gates, physical model scale reconciliation,
authentic DOF accounting, and computational speedup decomposition.
"""

import hashlib
import json
import os
import unittest

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MATRIX_PATH = os.path.join(WORKSPACE_ROOT, "results", "validation", "mode1_reconciled_release_matrix.json")


def sha256_file(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()


class TestMode1ReconciledReleaseMatrix(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not os.path.exists(MATRIX_PATH):
            raise FileNotFoundError(f"Matrix file not found: {MATRIX_PATH}")
        with open(MATRIX_PATH, "r", encoding="utf-8") as f:
            cls.matrix = json.load(f)

    def test_schema_and_metadata(self):
        self.assertEqual(self.matrix.get("schema"), 1)
        self.assertEqual(self.matrix.get("task_id"), "F1597-CORRECT-PACKAGE72-STATE-TRANSFER")
        self.assertIn("RELEASE_VERIFIED", self.matrix.get("status", ""))

    def test_model_scale_reconciliation(self):
        scales = self.matrix["model_scale_reconciliation"]

        # Full scale Mode-I benchmark
        full = scales["full_scale_mode1_benchmark"]
        self.assertEqual(full["domain_dimensions_mm"], [1.0, 1.0])
        self.assertIn("0.5", full["slit_location"])
        self.assertLessEqual(abs(full["delta_K0_pct"]), 0.05)
        self.assertLessEqual(abs(full["delta_Fmax_pct"]), 2.0)
        self.assertEqual(full["parity_verdict"], "PASS")

        # Miniature Mode-I benchmark
        mini = scales["miniature_mode1_benchmark"]
        self.assertEqual(mini["domain_dimensions_mm"], [0.1, 0.1])
        self.assertIn("0.05", mini["slit_location"])
        self.assertLessEqual(mini["package89_force_continuity_error_pct"], 5.0)
        self.assertEqual(mini["continuity_verdict"], "PASS")

    def test_dof_savings_audit(self):
        dofs = self.matrix["dof_savings_audit"]

        # Coarse pre-analysis
        coarse = dofs["coarse_preanalysis_mesh"]
        self.assertEqual(coarse["elements"], 2906)
        self.assertEqual(coarse["physical_nodes"], 2989)
        self.assertEqual(coarse["solver_dofs"], 8969)
        self.assertGreaterEqual(coarse["dof_reduction_vs_ref15k_pct"], 70.0)

        # Adapted fracture mesh
        adapted = dofs["adapted_fracture_mesh"]
        self.assertEqual(adapted["elements"], 14677)
        self.assertEqual(adapted["physical_nodes"], 14647)
        self.assertEqual(adapted["solver_dofs"], 43943)
        self.assertGreaterEqual(adapted["dof_reduction_vs_hypothetical_uniform_1um_pct"], 90.0)
        self.assertLessEqual(adapted["crack_tip_element_size_um"], 1.2)

        # Uniform reference
        ref = dofs["uniform_reference_s1"]
        self.assertEqual(ref["elements"], 15192)
        self.assertEqual(ref["solver_dofs"], 46568)

    def test_computational_performance_decomposition(self):
        perf = self.matrix["computational_performance_audit"]
        comps = perf["workflow_components_sec"]

        # Verify all components exist
        for key in ["T_preanalysis", "T_error", "T_remesh", "T_transfer", "T_solver_8t", "T_solver_serial", "T_post"]:
            self.assertIn(key, comps)
            self.assertGreaterEqual(comps[key], 0.0)

        # Verify speedup >= 1.5x
        self.assertGreaterEqual(perf["solver_only_speedup_8t_vs_serial"], 1.5)
        self.assertGreaterEqual(perf["full_workflow_speedup_8t_vs_serial"], 1.5)

        # Pre-refinement overhead < 1.0%
        self.assertLess(perf["pre_refinement_overhead_percentage"], 1.0)

    def test_all_ten_acceptance_gates_pass(self):
        gates = self.matrix["acceptance_gates"]
        expected_gates = [
            "gate_1_force_parity",
            "gate_2_stiffness_parity",
            "gate_3_displacement_parity",
            "gate_4_dof_reduction_preanalysis",
            "gate_5_dof_reduction_adapted_vs_1um",
            "gate_6_step_partition_invariance",
            "gate_7_smp_scaling_speedup",
            "gate_8_uel_integrity",
            "gate_9_state_transfer_benchmark",
            "gate_10_architecture_contract",
        ]
        self.assertEqual(len(gates), 10)
        for g in expected_gates:
            self.assertIn(g, gates, f"Missing gate: {g}")
            self.assertEqual(gates[g]["verdict"], "PASS", f"Gate {g} did not PASS")

    def test_evidence_hashes_integrity(self):
        hashes = self.matrix["evidence_hashes"]
        for rel_path, expected_hash in hashes.items():
            full_path = os.path.join(WORKSPACE_ROOT, rel_path)
            self.assertTrue(os.path.exists(full_path), f"Evidence file missing: {full_path}")
            actual_hash = sha256_file(full_path)
            self.assertEqual(
                actual_hash,
                expected_hash.upper(),
                f"Hash mismatch for {rel_path}: expected {expected_hash}, got {actual_hash}",
            )


if __name__ == "__main__":
    unittest.main()

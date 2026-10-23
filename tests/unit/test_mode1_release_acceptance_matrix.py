"""
Unit test suite for Mode-I Release Acceptance Matrix.
Verifies all 10 release readiness gates covering golden-run reproducibility,
MISESERI semantics, automatic refinement, step partition invariance, parity,
DOF savings, UEL integrity, regression coverage, state transfer PoC, and architecture contract.
"""
import os
import json
import unittest

class TestMode1ReleaseAcceptanceMatrix(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        matrix_path = "results/validation/mode1_release_acceptance_matrix.json"
        if not os.path.exists(matrix_path):
            from scripts.validation.audit_mode1_release_readiness import run_release_audit
            run_release_audit(".")
        with open(matrix_path, "r", encoding="utf-8") as f:
            cls.matrix = json.load(f)

    def test_overall_release_status(self):
        self.assertEqual(
            self.matrix["overall_release_status"],
            "MODE1_METHOD_A_B_RELEASE_READY__METHOD_C_SCOPED_AS_OPTIONAL_EXTENSION"
        )

    def test_gate1_golden_run(self):
        g = self.matrix["gates"]["gate_1_golden_run_reproducibility"]
        self.assertEqual(g["verdict"], "PASS")
        self.assertGreaterEqual(g["total_increments"], 4800)

    def test_gate2_miseseri_semantics(self):
        g = self.matrix["gates"]["gate_2_miseseri_semantics"]
        self.assertEqual(g["verdict"], "PASS")
        self.assertEqual(g["sizing_method"], "UNIFORM_ERROR")

    def test_gate3_refinement_topology(self):
        g = self.matrix["gates"]["gate_3_automatic_refinement_and_topology"]
        self.assertEqual(g["verdict"], "PASS")
        self.assertIn("Duplicate nodes along horizontal line y=0.05 mm", g["slit_flank_conformance"])
        self.assertIn("Refinement region geometrically bounded", g["crack_corridor_limitation"])

    def test_gate4_configurable_partitions(self):
        g = self.matrix["gates"]["gate_4_configurable_loading_partitions"]
        self.assertEqual(g["verdict"], "PASS")
        self.assertEqual(g["max_diff_1s_2s"], 0.0)
        self.assertTrue(g["adapted_mesh_identical"])

    def test_gate5_parity(self):
        g = self.matrix["gates"]["gate_5_rf_crack_energy_parity"]
        self.assertEqual(g["verdict"], "PASS")
        self.assertLessEqual(abs(g["delta_k0_pct"]), 0.05)
        self.assertLessEqual(abs(g["delta_fmax_pct"]), 2.0)

    def test_gate6_dof_savings(self):
        g = self.matrix["gates"]["gate_6_dof_and_computational_savings"]
        self.assertEqual(g["verdict"], "PASS")
        self.assertGreaterEqual(g["coarse_mesh_dof_reduction_pct"], 70.0)

    def test_gate7_uel_integrity(self):
        g = self.matrix["gates"]["gate_7_uel_source_and_hash_integrity"]
        self.assertEqual(g["verdict"], "PASS")
        self.assertEqual(
            g["measured_sha256"],
            "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
        )

    def test_gate8_regression_coverage(self):
        g = self.matrix["gates"]["gate_8_regression_coverage"]
        self.assertEqual(g["verdict"], "PASS")

    def test_gate9_state_transfer_benchmark(self):
        g = self.matrix["gates"]["gate_9_state_transfer_benchmark_poc"]
        self.assertEqual(g["verdict"], "PASS")
        self.assertTrue(g["zero_healing_verified"])
        self.assertTrue(g["softening_continuation_confirmed"])

    def test_gate10_architecture_contract(self):
        g = self.matrix["gates"]["gate_10_architecture_contract"]
        self.assertEqual(g["verdict"], "PASS")

if __name__ == "__main__":
    unittest.main()

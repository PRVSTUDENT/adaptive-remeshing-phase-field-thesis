"""
Unit test suite for Package 89 acceptance gates.
Validates force continuity, smooth AT2 energy, raw UEL energy, zero healing,
solver incrementation consistency, and forward continuation softening.
"""
import os
import json
import unittest

class TestPackage89AcceptanceGates(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        matrix_path = "results/validation/package89_acceptance_matrix.json"
        if not os.path.exists(matrix_path):
            from scripts.validation.audit_package89_acceptance_matrix import run_audit
            run_audit(".")
        with open(matrix_path, "r", encoding="utf-8") as f:
            cls.matrix = json.load(f)

    def test_gate1_force_continuity(self):
        g1 = self.matrix["gates"]["gate_1_force_continuity"]
        self.assertEqual(g1["verdict"], "PASS")
        self.assertLessEqual(abs(g1["step2_error_pct"]), 5.0)
        self.assertAlmostEqual(g1["step2_relaxed_rf2_N"], 189.5358, places=3)

    def test_gate2a_smooth_at2_energy(self):
        g2a = self.matrix["gates"]["gate_2a_smooth_at2_fracture_energy"]
        self.assertEqual(g2a["verdict"], "PASS")
        self.assertLessEqual(abs(g2a["error_pct"]), 2.0)

    def test_gate2b_raw_uel_energy(self):
        g2b = self.matrix["gates"]["gate_2b_raw_uel_fracture_energy"]
        self.assertEqual(g2b["verdict"], "PASS")
        self.assertLessEqual(abs(g2b["raw_uel_error_pct"]), 2.0)
        self.assertAlmostEqual(g2b["raw_uel_error_pct"], -1.71587, places=3)

    def test_gate3_zero_healing(self):
        g3 = self.matrix["gates"]["gate_3_pointwise_irreversibility"]
        self.assertEqual(g3["verdict"], "PASS")
        self.assertEqual(g3["healing_nodes_count"], 0)
        self.assertGreaterEqual(g3["min_delta_d"], 0.0)
        self.assertGreater(g3["advancing_nodes_count"], 0)

    def test_gate4_solver_incrementation(self):
        g4 = self.matrix["gates"]["gate_4_solver_incrementation_consistency"]
        self.assertEqual(g4["verdict"], "PASS")
        self.assertEqual(g4["step4_solver_increments_sta"], 8)
        self.assertEqual(g4["step4_field_frames_odb"], 5)
        self.assertEqual(g4["cutbacks_count"], 0)

    def test_gate5_forward_continuation_softening(self):
        g5 = self.matrix["gates"]["gate_5_forward_continuation_softening"]
        self.assertEqual(g5["verdict"], "PASS")
        self.assertLess(g5["softening_delta_rf_N"], 0.0)
        self.assertGreater(g5["terminal_d_max"], 0.85)

    def test_physical_specimen_parameters(self):
        p = self.matrix["physical_specimen"]
        self.assertEqual(p["length_scale_l0_mm"], 0.0075)
        self.assertEqual(p["youngs_modulus_kN_mm2"], 210.0)
        self.assertEqual(p["fracture_energy_gc_kN_mm"], 0.0027)
        self.assertEqual(p["initial_slit_location"], "y = 0.05 mm, x in [0.0, 0.05] mm")

    def test_overall_classification(self):
        self.assertEqual(self.matrix["overall_classification"], "QUALIFIED_SINGLE_TRANSFER_BENCHMARK_AT_CRACK_INITIATION")

if __name__ == "__main__":
    unittest.main()

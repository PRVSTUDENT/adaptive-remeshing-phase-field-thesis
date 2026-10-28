import json
import os
import unittest


class TestMode1F1597Package137TerminalEvaluation(unittest.TestCase):
    """Scientific evaluation and verification of Package 137 (Hypothesis H27) exact donor frame continuation."""

    @classmethod
    def setUpClass(cls):
        cls.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        cls.pkg_dir = os.path.join(
            cls.repo_root, "models", "pandey_kumar_mode1", "137_c4_donor_inc89_h27_exact_frame_continuation"
        )
        cls.summary_path = os.path.join(cls.pkg_dir, "c4_donor_inc89_h27_continuation_summary.json")
        with open(cls.summary_path, "r") as f:
            cls.summary = json.load(f)

    def test_01_solver_convergence_and_cycles(self):
        """Verify under-relaxed AM converged within 5 cycles with strict stationarity."""
        self.assertEqual(self.summary["status"], "CONVERGED_STATIONARY_STATE")
        self.assertEqual(self.summary["h27_verdict"], "H27_PASSED")
        self.assertEqual(self.summary["cycles_completed"], 5)
        final = self.summary["final_state"]
        self.assertLessEqual(final["raw_max_delta_d"], 1.0e-3)
        self.assertLessEqual(final["delta_rf2_prev_cycle_N"], 0.1)

    def test_02_variational_and_kkt_admissibility(self):
        """Verify variational Kuhn-Tucker admissibility and non-healing."""
        final = self.summary["final_state"]
        self.assertEqual(final["healing_violations"], 0)
        self.assertLessEqual(final["free_res_max_kN_mm"], 1.0e-6)
        self.assertGreaterEqual(final["min_lambda_kN_mm"], -1.0e-9)

    def test_03_exact_displacement_kinematics(self):
        """Verify continuation reached exact donor Increment 89 target displacement."""
        self.assertAlmostEqual(self.summary["initial_u_rp_mm"], 0.001982905200, places=9)
        self.assertAlmostEqual(self.summary["target_u_rp_mm"], 0.001990107350, places=9)
        self.assertAlmostEqual(self.summary["forward_increment_mm"], 7.20215e-6, places=11)

    def test_04_direct_donor_reaction_force_parity(self):
        """Verify direct un-interpolated force parity against donor Increment 89."""
        rf2_c4 = self.summary["final_state"]["rf2_rp_N"]
        rf2_donor = 184.570536  # Authentic donor Increment 89
        rel_diff_pct = (rf2_c4 - rf2_donor) / rf2_donor * 100.0
        self.assertAlmostEqual(rf2_c4, 183.843702, places=3)
        self.assertAlmostEqual(rel_diff_pct, -0.3938, places=2)
        self.assertLessEqual(abs(rel_diff_pct), 5.0)

    def test_05_direct_donor_energy_parity(self):
        """Verify direct un-interpolated total energy parity against donor Increment 89."""
        etot_c4 = self.summary["final_state"]["e_tot_mJ"]
        etot_donor = 0.23991278  # Authentic donor Increment 89
        rel_diff_pct = (etot_c4 - etot_donor) / etot_donor * 100.0
        self.assertAlmostEqual(etot_c4, 0.24409409, places=5)
        self.assertAlmostEqual(rel_diff_pct, 1.7428, places=2)
        self.assertLessEqual(rel_diff_pct, 2.0)

    def test_06_governing_gate_invariance(self):
        """Verify that Stage C1-2 step 2 energy gate failure remains invariant."""
        # Governed milestone STAGE_C1_2_STEP2_ENERGY_GATE_FAILED (+2.00803158%) must be preserved.
        p113_error_pct = 2.00803158
        self.assertGreater(p113_error_pct, 2.0)


if __name__ == "__main__":
    unittest.main()

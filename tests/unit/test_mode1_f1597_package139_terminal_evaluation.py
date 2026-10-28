# -*- coding: utf-8 -*-
"""
test_mode1_f1597_package139_terminal_evaluation.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Independent unit test qualification of Package 139 / Hypothesis H30 terminal results:
Increment-91 Candidate C4 Under-Relaxed AM/PDAS Continuation (omega=0.70, max 35 cycles).
"""

import json
import os
import unittest


class TestMode1F1597Package139TerminalEvaluation(unittest.TestCase):
    """Independent unit test suite verifying Package 139 terminal evaluation."""

    @classmethod
    def setUpClass(cls):
        cls.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        cls.audit_path = os.path.join(
            cls.repo_root, "results", "validation", "h30_c4_inc91_package139_evaluation.json"
        )
        with open(cls.audit_path, "r") as f:
            cls.audit = json.load(f)

    def test_01_pbs_execution_receipt(self):
        """Verify PBS Job 1418554.mmaster02 exit status and runtime."""
        self.assertEqual(self.audit["pbs_job_id"], "1418554.mmaster02")
        pbs = self.audit["pbs_execution"]
        self.assertEqual(pbs["exit_code"], 0)
        self.assertEqual(pbs["status"], "CONVERGED_STATIONARY_STATE")
        self.assertEqual(pbs["cycles_completed"], 5)
        self.assertEqual(pbs["walltime_seconds"], 67)
        self.assertEqual(pbs["under_relaxation_omega"], 0.70)

    def test_02_h30_verdict_and_provenance(self):
        """Verify that H30 achieved H30_PASSED verdict."""
        self.assertEqual(self.audit["verdict"], "H30_PASSED")
        self.assertEqual(self.audit["task_id"], "F1597-CORRECT-PACKAGE72-STATE-TRANSFER")
        self.assertEqual(self.audit["package_name"], "139_c4_inc91_h30_underrelaxed_forward_continuation")

    def test_03_stationarity_and_kkt_residuals(self):
        """Verify all stationarity, residual, and multiplier criteria pass."""
        crit = self.audit["acceptance_criteria"]
        self.assertTrue(crit["c1_raw_stationarity"]["pass"])
        self.assertLessEqual(crit["c1_raw_stationarity"]["value"], 1.0e-3)

        self.assertTrue(crit["c2_reaction_force_drift"]["pass"])
        self.assertLessEqual(crit["c2_reaction_force_drift"]["value"], 0.10)

        self.assertTrue(crit["c3_free_phase_kkt_residual"]["pass"])
        self.assertLessEqual(crit["c3_free_phase_kkt_residual"]["value"], 1.0e-6)

        self.assertTrue(crit["c4_active_multiplier_bound"]["pass"])
        self.assertGreaterEqual(crit["c4_active_multiplier_bound"]["value"], -1.0e-9)

        self.assertTrue(crit["c6_partition_consistency"]["pass"])
        self.assertEqual(crit["c6_partition_consistency"]["total_nodes"], 4588)

    def test_04_pointwise_monotonicity(self):
        """Verify independent zero-healing and zero-history-loss array checks."""
        mono = self.audit["pointwise_monotonicity"]
        self.assertEqual(mono["independent_healing_violations"], 0)
        self.assertEqual(mono["independent_history_loss_violations"], 0)

    def test_05_physical_donor_parity(self):
        """Verify physical force and energy agreement with authentic donor Increment 91."""
        crit = self.audit["acceptance_criteria"]
        rf2_crit = crit["c7_donor_rf2_tolerance"]
        self.assertTrue(rf2_crit["pass"])
        self.assertLessEqual(abs(rf2_crit["error_pct"]), 5.0)
        # Computed RF2 ~ 184.31 N (+1.17%)
        self.assertAlmostEqual(rf2_crit["computed_N"], 184.3100, places=2)

        etot_crit = crit["c8_donor_etot_tolerance"]
        self.assertTrue(etot_crit["pass"])
        self.assertLessEqual(abs(etot_crit["error_pct"]), 2.0)
        # Computed Etot ~ 0.2531 mJ (+1.63%)
        self.assertAlmostEqual(etot_crit["computed_mJ"], 0.253131, places=4)

    def test_06_lossless_round_trip_restoration(self):
        """Verify exact checkpoint round-trip restoration."""
        rtr = self.audit["round_trip_restoration"]
        self.assertTrue(rtr["lossless"])
        self.assertLessEqual(rtr["max_disp_restoration_err_mm"], 1.0e-12)
        self.assertEqual(rtr["max_damage_restoration_err"], 0.0)

    def test_07_incremental_energy_consistency(self):
        """Verify incremental external work vs total energy change."""
        inc = self.audit["incremental_energetics"]
        self.assertGreater(inc["delta_w_ext_mJ"], 0.0)
        self.assertGreater(inc["delta_e_tot_mJ"], 0.0)
        self.assertLess(inc["energy_work_residual_pct"], 5.0)

    def test_08_governing_milestone_invariance(self):
        """Verify governing cross-mesh gate retention."""
        self.assertEqual(self.audit["governing_gate_retained"], "STAGE_C1_2_STEP2_ENERGY_GATE_FAILED")
        self.assertEqual(self.audit["p113_gate_valid_failure_retained"], "+2.00803158%")


if __name__ == "__main__":
    unittest.main()

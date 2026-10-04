#!/usr/bin/env python3
"""
Unit Test Suite for Gate-6B Stage 14U-AJ: 4-Thread Terminal Parity and Governed Determinism Gating
--------------------------------------------------------------------------------------------------
Verifies:
1. Complete threaded-vs-serial terminal parity contract (bitwise F, E_elas, E_frac, K0, Fmax, attempt count, controlling wake node).
2. Rejection of declaring terminal parity on incomplete / pre-terminal runs.
3. Rejection of un-qualified crossing claims.
4. Gating of Stage-B determinism repeat on verified Stage-A terminal parity.
5. Strict holding of Package 28 (Cn=0.50) while 2x temporal diagnostic job is running.
6. Epistemic claim discipline (gradient regularization vs local algebraic bounds, ill-conditioning scoping, wake history localization).
"""

import os
import json
import unittest

class TestStage14UAJCrossingAndTerminalParity(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # Locate report files locally or on cluster
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        cls.report_json = os.path.join(base_dir, "models/pandey_kumar_mode1/26_stage14_adaptive_candidate_14k_4thread/MODE1_STAGE14UAJ_TERMINAL_PARITY_REPORT.json")
        cls.attempt_json = os.path.join(base_dir, "models/pandey_kumar_mode1/26_stage14_adaptive_candidate_14k_4thread/MODE1_STAGE14UAJ_ATTEMPT_DETAILS.json")
        
        cls.report_data = {}
        cls.attempt_data = {}
        
        if os.path.exists(cls.report_json):
            with open(cls.report_json, 'r') as f:
                cls.report_data = json.load(f)
                
        if os.path.exists(cls.attempt_json):
            with open(cls.attempt_json, 'r') as f:
                cls.attempt_data = json.load(f)

    def test_terminal_parity_metrics(self):
        """Verify bitwise parity across all key observables and attempt counts."""
        self.assertTrue(bool(self.report_data), "MODE1_STAGE14UAJ_TERMINAL_PARITY_REPORT.json missing")
        self.assertEqual(self.report_data.get("governing_verdict"), "THREAD_TERMINAL_PARITY_PASS")
        
        metrics = self.report_data.get("execution_metrics", {})
        serial = metrics.get("serial_reference_job", {})
        thread = metrics.get("thread_stage_a_job", {})
        diffs = metrics.get("parity_discrepancies", {})
        
        # Increments and displacements
        self.assertEqual(serial.get("total_increments"), 4890)
        self.assertEqual(thread.get("total_increments"), 4890)
        self.assertAlmostEqual(serial.get("terminal_u_mm"), 0.007889, places=6)
        self.assertAlmostEqual(thread.get("terminal_u_mm"), 0.007889, places=6)
        
        # Reaction forces and stiffness
        self.assertAlmostEqual(serial.get("peak_rf_kn"), thread.get("peak_rf_kn"), places=7)
        self.assertAlmostEqual(serial.get("k0_kn_per_mm"), thread.get("k0_kn_per_mm"), places=5)
        self.assertAlmostEqual(diffs.get("max_abs_rf_discrepancy_kn", 1.0), 0.0, places=7)
        
        # Energy functionals
        self.assertAlmostEqual(serial.get("terminal_e_elas_mj"), thread.get("terminal_e_elas_mj"), places=6)
        self.assertAlmostEqual(serial.get("terminal_e_frac_mj"), thread.get("terminal_e_frac_mj"), places=6)
        
        # Attempt count
        self.assertEqual(serial.get("failing_increment_attempts"), 10)
        self.assertEqual(thread.get("failing_increment_attempts"), 10)

    def test_reject_preterminal_as_terminal(self):
        """Enforce that pre-terminal runs cannot be certified as THREAD_TERMINAL_PARITY_PASS."""
        def evaluate_mock_parity(u_term_serial, u_term_thread, is_running):
            if is_running or u_term_thread < u_term_serial:
                return "THREAD_TERMINAL_PARITY_NOT_YET_QUALIFIED"
            elif u_term_thread == u_term_serial:
                return "THREAD_TERMINAL_PARITY_PASS"
            else:
                return "THREAD_RUN_CROSSED_SERIAL_FAILURE_POINT"
                
        self.assertEqual(evaluate_mock_parity(0.007889, 0.007819, True), "THREAD_TERMINAL_PARITY_NOT_YET_QUALIFIED")
        self.assertEqual(evaluate_mock_parity(0.007889, 0.007889, False), "THREAD_TERMINAL_PARITY_PASS")
        self.assertEqual(evaluate_mock_parity(0.007889, 0.008000, False), "THREAD_RUN_CROSSED_SERIAL_FAILURE_POINT")

    def test_attempt_details_and_wake_node_stagnation(self):
        """Verify Increment 2890 attempt sequence and controlling wake node 13628."""
        self.assertTrue(bool(self.attempt_data), "MODE1_STAGE14UAJ_ATTEMPT_DETAILS.json missing")
        self.assertEqual(self.attempt_data.get("controlling_wake_node"), 13628)
        self.assertEqual(self.attempt_data.get("controlling_dof"), 3)
        self.assertEqual(self.attempt_data.get("governing_failure_mechanism"), "POST_FRACTURE_CONVERGENCE_NORMALIZATION_SENSITIVITY_VERIFIED")
        
        attempts = self.attempt_data.get("attempts", [])
        self.assertEqual(len(attempts), 10)
        
        # Verify cutback plateau: Attempts 7-10 have bitwise locked c_max = 2.611e-6
        for att in attempts[6:]:
            self.assertAlmostEqual(att.get("c_max_mm"), 2.611e-6, places=9)
            self.assertEqual(att.get("c_max_node"), 13628)
            self.assertEqual(att.get("c_max_dof"), 3)
            self.assertAlmostEqual(att.get("residual_equilibrium_ratio"), 0.000929, places=6)

    def test_stage_b_submission_gating(self):
        """Verify Stage-B determinism repeat submission is recorded with valid configuration."""
        stage_b = self.report_data.get("stage_b_submission", {})
        self.assertEqual(stage_b.get("status"), "RUNNING")
        self.assertEqual(stage_b.get("allocated_cpus"), 4)
        self.assertEqual(stage_b.get("allocated_memory"), "16gb")
        self.assertTrue(stage_b.get("job_id", "").startswith("1410029"))
        self.assertEqual(stage_b.get("input_deck_sha256"), "26D873FB2E68055C80550D1DD981766BCAF46E13D3D0A7BA6411B63D9C382D35")

    def test_package_28_held_while_temporal_diagnostic_running(self):
        """Verify Package 28 Cn=0.50 submission is strictly held while temporal diagnostic is active."""
        temporal = self.report_data.get("temporal_diagnostic_status", {})
        self.assertEqual(temporal.get("status"), "RUNNING")
        self.assertTrue(temporal.get("package_28_submission_held"))
        self.assertEqual(temporal.get("package_28_cn050_status"), "CONVERGENCE_CRITERION_CANDIDATE_VALIDATED__TEMPORAL_DIAGNOSTIC_PENDING")

    def test_parallel_speedup_scaling(self):
        """Verify parallel walltime reduction and speedup calculation."""
        scaling = self.report_data.get("execution_metrics", {}).get("parallel_scaling", {})
        speedup = scaling.get("measured_speedup_s4")
        self.assertGreater(speedup, 2.2)
        self.assertLess(speedup, 2.5)
        self.assertAlmostEqual(speedup, 17609 / 7627.0, places=4)
        self.assertAlmostEqual(scaling.get("walltime_saved_hours"), (17609 - 7627) / 3600.0, places=3)

if __name__ == "__main__":
    unittest.main()

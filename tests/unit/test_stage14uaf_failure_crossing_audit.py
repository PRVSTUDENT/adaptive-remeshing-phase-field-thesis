#!/usr/bin/env python3
"""
test_stage14uaf_failure_crossing_audit.py
Unit and regression test suite for Gate-6B Stage 14U-AF:
Historical-Failure-Crossing Audit and Terminal-Readiness Qualification.
"""

import os
import json
import unittest

class TestStage14UFFailureCrossingAudit(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        cls.pkg25_dir = os.path.join(cls.repo_root, "models", "pandey_kumar_mode1", "25_stage14_adaptive_candidate_14k")
        cls.audit_json = os.path.join(cls.pkg25_dir, "STAGE14UAF_CROSSING_AUDIT_DATA.json")
        cls.report_json = os.path.join(cls.pkg25_dir, "MODE1_STAGE14UAF_FAILURE_CROSSING_REPORT.json")
        cls.report_md = os.path.join(cls.pkg25_dir, "MODE1_STAGE14UAF_FAILURE_CROSSING_REPORT.md")
        
    def test_01_audit_data_and_report_files_exist(self):
        """Verify presence of Stage 14U-AF audit data and report artifacts."""
        self.assertTrue(os.path.exists(self.audit_json), f"Missing audit json: {self.audit_json}")
        self.assertTrue(os.path.exists(self.report_json), f"Missing report json: {self.report_json}")
        self.assertTrue(os.path.exists(self.report_md), f"Missing report md: {self.report_md}")

    def test_02_solver_log_attempt_evidence(self):
        """Reject claims of extended attempt usage without concrete solver-log evidence."""
        with open(self.audit_json, 'r') as f:
            data = json.load(f)
            
        attempts = data.get("inc2890_attempt_sequence", [])
        self.assertEqual(len(attempts), 10, "Inc 2890 must document exactly 10 cutback attempts")
        
        # Verify attempt 1 was 2.0e-4 and attempt 10 was 1.0e-9
        self.assertAlmostEqual(attempts[0]["dt"], 2.0e-4, places=8)
        self.assertAlmostEqual(attempts[9]["dt"], 1.0e-9, places=12)
        
        # Verify node and DOF in attempt 10
        last_it = attempts[9]["iterations"][-1]
        self.assertEqual(last_it["max_disp_corr"]["dof"], 3, "Unconverged correction must be DOF 3 (phase field)")
        self.assertEqual(last_it["max_residual"]["dof"], 3, "Unconverged residual must be DOF 3")

    def test_03_actual_rp_displacement_used_no_rounding(self):
        """Reject rounded displacement approximations in favor of actual RP U2."""
        with open(self.audit_json, 'r') as f:
            data = json.load(f)
            
        states = data.get("last_converged_states_near_crossing", [])
        self.assertGreaterEqual(len(states), 10)
        
        for s in states:
            u2 = s.get("u2_actual_mm")
            self.assertIsNotNone(u2, "State must contain actual RP U2")
            # Verify exact physical time mapping: step 2 u = 0.0050 + 0.0050 * step_time
            expected_u = 0.0050 + 0.0050 * s["step_time"]
            self.assertAlmostEqual(u2, expected_u, places=6, msg=f"Displacement must match RP U2 exactly")

    def test_04_no_forward_filling_or_extrapolation(self):
        """Reject forward-filled or extrapolated unreached crossing states."""
        with open(self.report_json, 'r') as f:
            rep = json.load(f)
            
        last_u = rep["completion_job"]["last_converged_actual_u2_mm"]
        self.assertEqual(last_u, 0.00788900)
        self.assertIsNone(rep["crossing_audit"]["first_newly_converged_state_u_gt_0_007889mm"])
        self.assertEqual(rep["governing_verdicts"]["crossing_verdict"], "HISTORICAL_FAILURE_CROSSING_REFAILED")
        self.assertEqual(rep["governing_verdicts"]["stage14v_terminal_readiness"], "STAGE14V_TERMINAL_EVALUATION_NOT_REACHED__FINAL_DISPLACEMENT_0_007889MM_LESS_THAN_0_010000MM")
        self.assertEqual(rep["governing_verdicts"]["package26_temporal_submission"], "PACKAGE26_SUBMISSION_BLOCKED__SERIAL_FAILED_BEFORE_0_010000MM")

    def test_05_terminology_governance_rejection(self):
        """Reject calling E_frac thermodynamic dissipation or using prohibited terms."""
        with open(self.report_md, 'r') as f:
            md_text = f.read()
            
        self.assertNotIn("thermodynamic dissipation", md_text.lower(), "E_frac must not be called thermodynamic dissipation")
        self.assertNotIn("physical element", md_text.lower(), "Prohibited terminology 'physical element' found")
        self.assertIn("fracture functional", md_text.lower())

    def test_06_threading_and_package_governance_maintained(self):
        """Verify 4-thread Stage-A parity and Package-27 hold statuses are preserved."""
        with open(self.report_json, 'r') as f:
            rep = json.load(f)
            
        self.assertEqual(rep["governing_verdicts"]["stage_a_4thread_parity"], "THREAD_PARITY_PASS_OVER_REACHED_RANGE")
        self.assertEqual(rep["governing_verdicts"]["stage_b_4thread_repeat"], "4THREAD_STAGEB_REPEAT_VALIDATED__WAITING_FOR_STAGEA_TERMINAL_PASS")
        self.assertEqual(rep["active_parallel_4thread_job"]["job_id"], "1410006.mmaster02")
        self.assertEqual(rep["active_parallel_4thread_job"]["status"], "RUNNING")

if __name__ == "__main__":
    unittest.main()

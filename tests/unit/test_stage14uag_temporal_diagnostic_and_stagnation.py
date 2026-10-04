#!/usr/bin/env python3
"""
test_stage14uag_temporal_diagnostic_and_stagnation.py
Unit and regression test suite for Gate-6B Stage 14U-AG:
Temporal-Refinement Diagnostic Submission and Phase-Field Newton-Stagnation Root-Cause Audit.
"""

import os
import json
import unittest
import numpy as np

class TestStage14UAGTemporalDiagnosticAndStagnation(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        cls.pkg26_dir = os.path.join(cls.repo_root, "models", "pandey_kumar_mode1", "26_stage14_temporal_refined_candidate_2x")
        cls.report_json = os.path.join(cls.pkg26_dir, "STAGE14UAG_SUBMISSION_AND_STAGNATION_REPORT.json")
        cls.report_md = os.path.join(cls.pkg26_dir, "STAGE14UAG_SUBMISSION_AND_STAGNATION_REPORT.md")
        cls.attempt_json = os.path.join(cls.pkg26_dir, "STAGE14UAG_ATTEMPT_SEQUENCE.json")
        cls.fig_pdf = os.path.join(cls.repo_root, "results", "figures", "mode1_gate6b", "fig_mode1_stage14uag_jacobian_and_stagnation.pdf")
        cls.fig_png = os.path.join(cls.repo_root, "results", "figures", "mode1_gate6b", "fig_mode1_stage14uag_jacobian_and_stagnation.png")
        
    def test_01_reports_and_figures_exist(self):
        """Verify presence of Stage 14U-AG report, data, and figure artifacts."""
        self.assertTrue(os.path.exists(self.report_json), f"Missing report json: {self.report_json}")
        self.assertTrue(os.path.exists(self.report_md), f"Missing report md: {self.report_md}")
        self.assertTrue(os.path.exists(self.attempt_json), f"Missing attempt json: {self.attempt_json}")
        self.assertTrue(os.path.exists(self.fig_pdf), f"Missing figure pdf: {self.fig_pdf}")
        self.assertTrue(os.path.exists(self.fig_png), f"Missing figure png: {self.fig_png}")

    def test_02_ten_attempt_telemetry_and_stagnation_plateau(self):
        """Verify the 10-attempt cutback sequence and bitwise stagnation plateau."""
        with open(self.attempt_json, 'r') as f:
            attempts = json.load(f)
            
        self.assertEqual(len(attempts), 10, "Inc 2890 must document exactly 10 cutback attempts")
        
        self.assertAlmostEqual(attempts[0]["dt"], 2.0e-4, places=8)
        self.assertAlmostEqual(attempts[9]["dt"], 1.0e-9, places=12)
        
        # Verify DOF 3 stagnation plateau across attempts 7 to 10
        for i in range(6, 10):
            last_it = attempts[i]["iterations"][-1]
            self.assertEqual(last_it["corr_dof"], 3, f"Attempt {i+1} correction DOF must be 3")
            self.assertEqual(last_it["corr_node"], 13628, f"Attempt {i+1} correction node must be 13628")
            self.assertAlmostEqual(last_it["largest_corr"], 2.611e-6, places=8)
            self.assertEqual(last_it["res_dof"], 3, f"Attempt {i+1} residual DOF must be 3")
            self.assertEqual(last_it["res_node"], 6479, f"Attempt {i+1} residual node must be 6479")
            self.assertAlmostEqual(last_it["largest_res"], 1.942e-9, places=11)

    def test_03_stagnating_nodes_physical_mapping(self):
        """Verify physical coordinates of stagnating nodes in severed crack wake."""
        with open(self.report_json, 'r') as f:
            data = json.load(f)
            
        nodes = data.get("stagnating_nodes_spatial_mapping", {})
        node13628 = nodes.get("node_13628", {})
        node6479 = nodes.get("node_6479", {})
        
        c13628 = node13628.get("coords_mm", [0, 0])
        self.assertAlmostEqual(c13628[0], 0.561986, places=4)
        self.assertAlmostEqual(c13628[1], 0.496392, places=4)
        self.assertIn("severed crack wake", node13628.get("location", "").lower())
        
        c6479 = node6479.get("coords_mm", [0, 0])
        self.assertAlmostEqual(c6479[0], 0.563913, places=4)
        self.assertAlmostEqual(c6479[1], 0.495441, places=4)
        self.assertIn("severed crack wake", node6479.get("location", "").lower())

    def test_04_phase_jacobian_finite_difference_consistency(self):
        """Verify offline finite-difference vs analytical Phase UEL Jacobian consistency."""
        node_coords = np.array([
            [0.562, 0.496],
            [0.563, 0.496],
            [0.563, 0.497],
            [0.562, 0.497]
        ])
        l0 = 0.0075
        Gc = 0.0027
        H = 0.05
        d_vec = np.array([0.9987, 0.9988, 0.9989, 0.9987])
        
        gp = 1.0 / np.sqrt(3.0)
        gauss_pts = [(-gp, -gp), (gp, -gp), (gp, gp), (-gp, gp)]
        weights = [1.0, 1.0, 1.0, 1.0]
        
        def compute_residual(d):
            R = np.zeros(4)
            for (xi, eta), w in zip(gauss_pts, weights):
                N = 0.25 * np.array([
                    (1.0 - xi) * (1.0 - eta),
                    (1.0 + xi) * (1.0 - eta),
                    (1.0 + xi) * (1.0 + eta),
                    (1.0 - xi) * (1.0 + eta)
                ])
                dN_dxi = 0.25 * np.array([-(1.0 - eta), (1.0 - eta), (1.0 + eta), -(1.0 + eta)])
                dN_deta = 0.25 * np.array([-(1.0 - xi), -(1.0 + xi), (1.0 + xi), (1.0 - xi)])
                dN_parent = np.vstack([dN_dxi, dN_deta])
                
                J = np.dot(dN_parent, node_coords)
                detJ = np.linalg.det(J)
                invJ = np.linalg.inv(J)
                B = np.dot(invJ, dN_parent)
                
                d_val = float(np.dot(N, d))
                grad_d = np.dot(B, d)
                
                term1 = ( (Gc / l0) * d_val - 2.0 * (1.0 - d_val) * H ) * N
                term2 = Gc * l0 * np.dot(B.T, grad_d)
                R += (term1 + term2) * detJ * w
            return R
            
        def compute_analytical_jacobian(d):
            K = np.zeros((4, 4))
            for (xi, eta), w in zip(gauss_pts, weights):
                N = 0.25 * np.array([
                    (1.0 - xi) * (1.0 - eta),
                    (1.0 + xi) * (1.0 - eta),
                    (1.0 + xi) * (1.0 + eta),
                    (1.0 - xi) * (1.0 + eta)
                ])
                dN_dxi = 0.25 * np.array([-(1.0 - eta), (1.0 - eta), (1.0 + eta), -(1.0 + eta)])
                dN_deta = 0.25 * np.array([-(1.0 - xi), -(1.0 + xi), (1.0 + xi), (1.0 - xi)])
                dN_parent = np.vstack([dN_dxi, dN_deta])
                
                J = np.dot(dN_parent, node_coords)
                detJ = np.linalg.det(J)
                invJ = np.linalg.inv(J)
                B = np.dot(invJ, dN_parent)
                
                K += ( (Gc / l0 + 2.0 * H) * np.outer(N, N) + Gc * l0 * np.dot(B.T, B) ) * detJ * w
            return K

        K_exact = compute_analytical_jacobian(d_vec)
        delta_d = np.array([1.0, -0.5, 0.8, -0.2])
        
        eps = 1e-4
        R_plus = compute_residual(d_vec + eps * delta_d)
        R_0 = compute_residual(d_vec)
        dR_fd = (R_plus - R_0) / eps
        dR_exact = np.dot(K_exact, delta_d)
        
        rel_err = float(np.linalg.norm(dR_fd - dR_exact) / np.linalg.norm(dR_exact))
        self.assertLess(rel_err, 1e-8, f"Jacobian relative tangent error too large: {rel_err}")

    def test_05_governing_verdicts_and_epistemic_classification(self):
        """Verify formal governing verdicts and root-cause hypothesis classifications."""
        with open(self.report_json, 'r') as f:
            data = json.load(f)
            
        temp_sub = data.get("temporal_diagnostic_submission", {})
        self.assertEqual(temp_sub.get("status"), "TEMPORAL_REFINEMENT_DIAGNOSTIC_RUNNING__BASELINE_REFAILED_AT_U007889")
        
        controls = data.get("controls_parameters_audit", {})
        self.assertIn("I_A = 10", controls.get("governing_cutback_parameter", ""))
        self.assertIn("dt_min = 1.0e-9 s", controls.get("governing_time_floor", ""))
        
        hyps = data.get("epistemic_hypothesis_classification", {})
        self.assertEqual(hyps.get("tangent_residual_inconsistency"), "NUMERICALLY_VERIFIED (RULED_OUT)")
        self.assertEqual(hyps.get("history_field_irreversibility_non_smoothness"), "SOURCE_VERIFIED (RULED_OUT)")
        self.assertEqual(hyps.get("phase_saturation_d_to_1"), "SOURCE_VERIFIED (OBSERVED_STATE)")
        self.assertEqual(hyps.get("convergence_metric_mismatch_under_post_fracture_softening"), "NUMERICALLY_VERIFIED (PRIMARY_ROOT_CAUSE)")
        
        term = data.get("bookkeeping_terminology_correction", {})
        self.assertEqual(term.get("corrected_classification"), "ENERGY_BOOKKEEPING_RESIDUAL_REPORTED")

    def test_06_governed_terminology_and_job_records(self):
        """Verify strict adherence to governed terminology and active job tracking."""
        with open(self.report_md, 'r') as f:
            md_text = f.read()
            
        self.assertNotIn("thermodynamic dissipation", md_text.lower())
        self.assertNotIn("physical element", md_text.lower())
        cleaned_text = md_text.lower().replace("\\_", "_")
        self.assertIn("energy_bookkeeping_residual_reported", cleaned_text)
        
        with open(self.report_json, 'r') as f:
            data = json.load(f)
            
        jobs = data.get("active_jobs_status", {})
        self.assertIn("job_1410027", jobs)
        self.assertIn("job_1410006", jobs)
        self.assertEqual(jobs["job_1410027"]["status"], "RUNNING")
        self.assertEqual(jobs["job_1410006"]["status"], "RUNNING")

if __name__ == "__main__":
    unittest.main()

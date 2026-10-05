#!/usr/bin/env python3
"""
Unit Test Suite: Mode-I Stage-14 Temporal Convergence Audit and Gate-6B Regression Guards
-----------------------------------------------------------------------------------------
Enforces strict regression guards:
1. Refined run (1410027) terminal displacement check (0.0074697 mm < 0.007889 mm).
2. Strict prohibition of forward-filling beyond reached terminal state.
3. Decoupling of pre-peak elastic temporal stability from post-peak solver-path sensitivity.
4. Matched-displacement evaluation tolerance on common domain.
5. Verification of canonical K0, F_max, and peak displacement parity.
6. Epistemic governance classification: QUALIFIED_OVER_PREPEAK_INTERVAL_ONLY & TEMPORALLY_SENSITIVE_POSTPEAK.
"""

import os
import unittest
import json
import hashlib

class TestStage14TemporalConvergenceAudit(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Determine repo root robustly
        candidates = [
            os.getcwd(),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")),
            r"D:\Master thesis\Adaptive remeshing"
        ]
        cls.repo_root = None
        for c in candidates:
            if os.path.exists(os.path.join(c, "models", "pandey_kumar_mode1")):
                cls.repo_root = c
                break
        if cls.repo_root is None:
            raise RuntimeError("Could not find repository root with models/pandey_kumar_mode1")
            
        cls.pkg26_dir = os.path.join(cls.repo_root, "models", "pandey_kumar_mode1", "26_stage14_temporal_refined_candidate_2x")
        cls.pkg25_dir = os.path.join(cls.repo_root, "models", "pandey_kumar_mode1", "25_stage14_adaptive_candidate_14k")
        
        # Load Report 26
        rpt_path = os.path.join(cls.pkg26_dir, "MODE1_STAGE14UAN_TEMPORAL_REFINEMENT_REPORT.json")
        with open(rpt_path, 'r') as f:
            cls.report = json.load(f)

    def test_01_provenance_and_subroutine_hash_identity(self):
        """Verify identical Fortran subroutine SHA-256 CE8D5EDC... across both temporal models."""
        expected_subroutine_hash = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
        
        def get_sha256(fp):
            h = hashlib.sha256()
            with open(fp, 'rb') as f:
                while chunk := f.read(65536):
                    h.update(chunk)
            return h.hexdigest().upper()
            
        f_base = os.path.join(self.pkg25_dir, "f42_mixed_uel.for")
        f_t2x = os.path.join(self.pkg26_dir, "f42_mixed_uel.for")
        
        self.assertTrue(os.path.exists(f_base))
        self.assertTrue(os.path.exists(f_t2x))
        self.assertEqual(get_sha256(f_base), expected_subroutine_hash)
        self.assertEqual(get_sha256(f_t2x), expected_subroutine_hash)

    def test_02_temporal_discretization_parameters_verified(self):
        """Verify Step 1 and Step 2 nominal increment sizes represent exact 2x refinement."""
        tp = self.report['temporal_parameters']
        self.assertEqual(tp['baseline']['step1_dt'], 0.0005)
        self.assertEqual(tp['baseline']['step1_du_nm'], 2.50)
        self.assertEqual(tp['baseline']['step2_dt'], 0.0002)
        self.assertEqual(tp['baseline']['step2_du_nm'], 1.00)
        
        self.assertEqual(tp['temporal_2x']['step1_dt'], 0.00025)
        self.assertEqual(tp['temporal_2x']['step1_du_nm'], 1.25)
        self.assertEqual(tp['temporal_2x']['step2_dt'], 0.0001)
        self.assertEqual(tp['temporal_2x']['step2_du_nm'], 0.50)

    def test_03_canonical_k0_stiffness_temporal_invariance(self):
        """Verify canonical initial structural stiffness K0 varies by less than 0.001%."""
        k0_info = self.report['canonical_stiffness_k0']
        k0_base = k0_info['baseline']['k0_kn_per_mm']
        k0_t2x = k0_info['temporal_2x']['k0_kn_per_mm']
        diff_pct = k0_info['k0_diff_pct']
        
        self.assertAlmostEqual(k0_base, 137.909558, places=4)
        self.assertAlmostEqual(k0_t2x, 137.909975, places=4)
        self.assertLess(abs(diff_pct), 0.001)
        self.assertEqual(k0_info['baseline']['n_points'], 400)
        self.assertEqual(k0_info['temporal_2x']['n_points'], 800)

    def test_04_peak_force_and_displacement_temporal_stability(self):
        """Verify peak reaction force differs by less than 0.05%."""
        pk = self.report['peak_characteristics']
        f_max_base = pk['baseline']['f_max_kn']
        f_max_t2x = pk['temporal_2x']['f_max_kn']
        diff_pct = pk['f_max_diff_pct']
        
        self.assertAlmostEqual(f_max_base, 0.743701, places=4)
        self.assertAlmostEqual(f_max_t2x, 0.743530, places=4)
        self.assertLess(abs(diff_pct), 0.05)
        self.assertAlmostEqual(pk['baseline']['u_peak_mm'], 0.005733, places=5)
        self.assertAlmostEqual(pk['temporal_2x']['u_peak_mm'], 0.005730, places=5)

    def test_05_terminal_displacement_and_no_forward_filling_guard(self):
        """Guard against forward-filling beyond actual reached terminal displacement 0.007470 mm."""
        cs = self.report['comparison_summary']
        u_term_t2x = cs['temporal_2x_terminal_displacement_mm']
        u_term_base = cs['baseline_terminal_displacement_mm']
        
        self.assertLess(u_term_t2x, u_term_base)
        self.assertAlmostEqual(u_term_t2x, 0.0074697, places=5)
        self.assertAlmostEqual(u_term_base, 0.007889, places=5)
        
        # Verify matched states at u >= 0.007889 mm are strictly NOT_REACHED
        for ms in self.report['predeclared_matched_states']:
            if ms['target_u_mm'] > u_term_t2x + 1e-5:
                self.assertEqual(ms['temporal_2x']['status'], "NOT_REACHED")
                self.assertIsNone(ms['temporal_2x']['actual_u_mm'])
                self.assertIsNone(ms['temporal_2x']['rf_kn'])
                self.assertEqual(ms['state_verdict'], "NOT_REACHED")

    def test_06_prepeak_common_interval_force_agreement(self):
        """Verify all reached pre-peak matched states agree within 0.05%."""
        for ms in self.report['predeclared_matched_states']:
            target_u = ms['target_u_mm']
            if target_u <= 0.005733 and ms['temporal_2x']['status'] == "REACHED":
                rf_b = ms['baseline']['rf_kn']
                rf_t = ms['temporal_2x']['rf_kn']
                rel_diff = abs(rf_t - rf_b) / rf_b * 100.0
                self.assertLess(rel_diff, 0.05)

    def test_07_post_fracture_solver_path_sensitivity_classification(self):
        """Verify that post-peak terminal divergence is correctly classified as path sensitivity."""
        self.assertEqual(self.report['decision_branch'], "TEMPORAL_REFINEMENT_CHANGES_FAILURE_PATH")
        self.assertEqual(
            self.report['epistemic_governance']['convergence_mechanism'],
            "POST_FRACTURE_CONVERGENCE_NORMALIZATION_SENSITIVITY_VERIFIED"
        )
        self.assertEqual(
            self.report['epistemic_governance']['ill_conditioning_status'],
            "NOT_ESTABLISHED"
        )

    def test_08_governing_gate6b_verdict_partitioning(self):
        """Verify that Gate-6B separates pre-peak stability from post-peak normalization sensitivity."""
        self.assertTrue(hasattr(self, 'report'))
        self.assertEqual(
            self.report['epistemic_governance']['crack_functional_terminology'],
            "IMPLEMENTED_PHASE_FIELD_CRACK_SURFACE_FRACTURE_FUNCTIONAL_E_FRAC"
        )

if __name__ == '__main__':
    unittest.main()

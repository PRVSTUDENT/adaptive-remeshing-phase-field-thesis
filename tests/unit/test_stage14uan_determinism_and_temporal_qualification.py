#!/usr/bin/env python3
"""
Unit Test Suite for Gate-6B Stage 14U-AN:
4-Thread Shared-Memory Determinism Qualification, 2x Temporal Refinement Diagnostic,
and Stage-A 8-Thread / Package 28 Submissions.
"""

import os
import json
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestStage14UANQualification(unittest.TestCase):
    def setUp(self):
        self.stage_b_json = os.path.join(REPO_ROOT, 'models/pandey_kumar_mode1/27_stage14_adaptive_candidate_14k_4thread_stage_b/MODE1_STAGE14UAN_STAGE_B_FULL_DETERMINISM_REPORT.json')
        self.temporal_json = os.path.join(REPO_ROOT, 'models/pandey_kumar_mode1/26_stage14_temporal_refined_candidate_2x/MODE1_STAGE14UAN_TEMPORAL_REFINEMENT_REPORT.json')
        self.pkg29_manifest = os.path.join(REPO_ROOT, 'models/pandey_kumar_mode1/29_stage14_adaptive_candidate_14k_8thread/PACKAGE_MANIFEST.json')
        self.pkg28_manifest = os.path.join(REPO_ROOT, 'models/pandey_kumar_mode1/28_stage14_convergence_control_candidate/PACKAGE_MANIFEST.json')

    def test_01_stage_b_4thread_determinism_metrics(self):
        self.assertTrue(os.path.exists(self.stage_b_json), f"Missing {self.stage_b_json}")
        with open(self.stage_b_json, 'r') as f:
            d = json.load(f)
        
        self.assertEqual(d['verdict'], "THREAD_PARITY_PASS + THREAD_DETERMINISM_PASS + THREAD_PARALLELIZATION_QUALIFIED_4T")
        self.assertEqual(d['comparison_summary']['common_increments_evaluated_nodes'], 4890)
        self.assertAlmostEqual(d['comparison_summary']['stage_b_vs_stage_a_max_abs_rf_kn'], 0.0, places=8)
        self.assertAlmostEqual(d['canonical_stiffness_k0']['stage_b_vs_stage_a_k0_diff_pct'], 0.0, places=6)
        self.assertAlmostEqual(d['canonical_stiffness_k0']['stage_b']['k0_kn_per_mm'], 137.909558, places=4)
        self.assertAlmostEqual(d['peak_characteristics']['stage_b']['f_max_kn'], 0.74370082, places=6)

    def test_02_stage_b_matched_states_bitwise_match(self):
        with open(self.stage_b_json, 'r') as f:
            d = json.load(f)
        
        states = d['predeclared_matched_states']
        self.assertEqual(len(states), 9)
        for s in states:
            self.assertEqual(s['parity_status'], "BITWISE_MATCH")
            self.assertEqual(s['stage_b']['status'], "REACHED")

    def test_03_temporal_2x_diagnostic_metrics(self):
        self.assertTrue(os.path.exists(self.temporal_json), f"Missing {self.temporal_json}")
        with open(self.temporal_json, 'r') as f:
            d = json.load(f)
        
        self.assertEqual(d['comparison_summary']['temporal_2x_increments_completed'], 8958)
        self.assertAlmostEqual(d['canonical_stiffness_k0']['temporal_2x']['k0_kn_per_mm'], 137.909975, places=4)
        self.assertAlmostEqual(d['canonical_stiffness_k0']['k0_diff_pct'], 0.0003025, places=5)
        self.assertAlmostEqual(d['peak_characteristics']['temporal_2x']['f_max_kn'], 0.74353024, places=6)
        self.assertAlmostEqual(d['comparison_summary']['temporal_2x_terminal_displacement_mm'], 0.007469709, places=6)

    def test_04_temporal_2x_decision_branch(self):
        with open(self.temporal_json, 'r') as f:
            d = json.load(f)
        
        self.assertIn(d['decision_branch'], ["TEMPORAL_REFINEMENT_CHANGES_FAILURE_PATH", "TEMPORAL_REFINEMENT_REFAILS_SAME_MECHANISM"])
        self.assertEqual(d['epistemic_governance']['convergence_mechanism'], "POST_FRACTURE_CONVERGENCE_NORMALIZATION_SENSITIVITY_VERIFIED")
        self.assertEqual(d['epistemic_governance']['ill_conditioning_status'], "NOT_ESTABLISHED")

    def test_05_package_29_8thread_configuration(self):
        self.assertTrue(os.path.exists(self.pkg29_manifest), f"Missing {self.pkg29_manifest}")
        with open(self.pkg29_manifest, 'r') as f:
            d = json.load(f)
        
        self.assertEqual(d['package_id'], "PACKAGE_29_STAGE14_ADAPTIVE_14K_8THREAD_STAGE_A_TWIN")
        self.assertEqual(d['governed_files']['pbs_script']['cpus'], 8)
        self.assertEqual(d['governed_files']['pbs_script']['mp_mode'], "threads")

    def test_06_package_28_convergence_control_configuration(self):
        self.assertTrue(os.path.exists(self.pkg28_manifest), f"Missing {self.pkg28_manifest}")
        with open(self.pkg28_manifest, 'r') as f:
            d = json.load(f)
        
        self.assertEqual(d['package_name'], "28_stage14_convergence_control_candidate")
        self.assertEqual(d['files']['input_deck']['step2_controls']['field_displacement']['Cn'], 0.5)

if __name__ == '__main__':
    unittest.main()

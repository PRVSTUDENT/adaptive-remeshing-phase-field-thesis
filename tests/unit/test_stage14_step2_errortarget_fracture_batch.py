#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit Test Suite for Mode-I Stage-14 Step-2 errorTarget Fracture Batch Evaluator:
1. Test reference values separation (Fixed Ref vs ET1 Adaptive Baseline).
2. Test pure-Python compute_canonical_k0 OLS accuracy and R2 computation.
3. Test compute_trapezoidal_work unit conversion to mJ.
4. Test extract_matched_states strict zero forward-filling and interpolation.
5. Test classify_fracture_response stability thresholds.
6. Test batch specification integrity (ET1, ET2, ET3, ET5).
7. Test figure manifest generation.
"""

import os
import sys
import unittest
import math

# Add repo root to path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.evaluation.evaluate_stage14_step2_errortarget_fracture_batch import (
    FIXED_REFERENCE_VALUES,
    ET1_ADAPTIVE_BASELINE_VALUES,
    MATCHED_DISPLACEMENTS_MM,
    BATCH_SPECIFICATION,
    compute_canonical_k0,
    compute_trapezoidal_work,
    extract_matched_states,
    classify_fracture_response,
    generate_batch_status_report
)

from scripts.postprocessing.plot_stage14_step2_fracture_sensitivity_templates import (
    export_plot_manifest
)

class TestStage14Step2FractureBatch(unittest.TestCase):

    def test_01_reference_and_baseline_separation(self):
        """Verify fixed reference anchor and ET1 adaptive baseline are strictly separated."""
        # Fixed reference (Job 1409734)
        self.assertEqual(FIXED_REFERENCE_VALUES['base_elements'], 15192)
        self.assertAlmostEqual(FIXED_REFERENCE_VALUES['K0_canonical_kN_per_mm'], 137.945520, places=5)
        self.assertAlmostEqual(FIXED_REFERENCE_VALUES['F_max_kN'], 0.757778, places=5)
        self.assertAlmostEqual(FIXED_REFERENCE_VALUES['u_peak_mm'], 0.005857, places=5)

        # ET1 adaptive baseline (14,483 FE)
        self.assertEqual(ET1_ADAPTIVE_BASELINE_VALUES['base_elements'], 14483)
        self.assertAlmostEqual(ET1_ADAPTIVE_BASELINE_VALUES['K0_canonical_kN_per_mm'], 137.909558, places=5)
        self.assertAlmostEqual(ET1_ADAPTIVE_BASELINE_VALUES['F_max_kN'], 0.743701, places=5)
        self.assertAlmostEqual(ET1_ADAPTIVE_BASELINE_VALUES['u_peak_mm'], 0.005733, places=5)
        self.assertAlmostEqual(ET1_ADAPTIVE_BASELINE_VALUES['u_term_mm'], 0.007889, places=5)
        self.assertEqual(ET1_ADAPTIVE_BASELINE_VALUES['native_localization_verdict'], "STAGE14_TARGET_LIKE_LOCALIZATION_EXACT_MATCH")

    def test_02_canonical_k0_ols_computation(self):
        """Verify pure-Python compute_canonical_k0 computes accurate slope and R2."""
        # Synthetic perfect linear data: F = 138.0 * u + 0.0001
        u_synth = [i * 0.00001 for i in range(100)]
        f_synth = [138.0 * u + 0.0001 for u in u_synth]
        
        fit = compute_canonical_k0(u_synth, f_synth, n_fit=50)
        self.assertAlmostEqual(fit['K0'], 138.0, places=6)
        self.assertAlmostEqual(fit['intercept'], 0.0001, places=6)
        self.assertAlmostEqual(fit['R2'], 1.0, places=6)
        self.assertEqual(fit['n_points'], 50)

    def test_03_trapezoidal_work_conversion(self):
        """Verify trapezoidal work calculation converts kN*mm to mJ correctly (1 kN*mm = 1000 mJ)."""
        u = [0.0, 0.001, 0.002]  # mm
        f = [0.0, 0.1, 0.2]      # kN
        # Int 0 to 0.002 of 100*u du = 0.5 * 100 * (0.002)^2 = 50 * 4e-6 = 0.0002 kN*mm = 0.2 mJ
        w = compute_trapezoidal_work(u, f)
        self.assertEqual(len(w), 3)
        self.assertAlmostEqual(w[0], 0.0, places=6)
        self.assertAlmostEqual(w[1], 0.05, places=6)  # 0.5 * 0.1 * 0.001 * 1000 = 0.05 mJ
        self.assertAlmostEqual(w[2], 0.20, places=6)  # 0.05 + 0.5 * 0.3 * 0.001 * 1000 = 0.20 mJ

    def test_04_strict_matched_states_extraction(self):
        """Verify matched displacement extraction strictly flags unreached states as NOT_REACHED."""
        u_reached = [0.0, 0.001, 0.002, 0.003, 0.004, 0.005]  # max u = 0.005 mm
        f_reached = [0.0, 0.138, 0.276, 0.414, 0.552, 0.690]
        
        targets = [0.001, 0.003, 0.005, 0.006, 0.007]
        results = extract_matched_states(u_reached, f_reached, targets)
        
        # Reached states
        self.assertEqual(results[0.001]['status'], 'REACHED')
        self.assertAlmostEqual(results[0.001]['force_kN'], 0.138, places=5)
        self.assertEqual(results[0.003]['status'], 'REACHED')
        self.assertAlmostEqual(results[0.003]['force_kN'], 0.414, places=5)
        self.assertEqual(results[0.005]['status'], 'REACHED')
        self.assertAlmostEqual(results[0.005]['force_kN'], 0.690, places=5)
        
        # Unreached states (no forward-filling!)
        self.assertEqual(results[0.006]['status'], 'NOT_REACHED')
        self.assertIsNone(results[0.006]['force_kN'])
        self.assertEqual(results[0.007]['status'], 'NOT_REACHED')
        self.assertIsNone(results[0.007]['force_kN'])

    def test_05_classification_logic(self):
        """Verify fracture response classification rules against Gate-6B criteria."""
        k0_ref = FIXED_REFERENCE_VALUES['K0_canonical_kN_per_mm']
        fmax_ref = FIXED_REFERENCE_VALUES['F_max_kN']
        
        # Stable case: Delta K0 = 0.026% (<0.5%), Delta Fmax = 1.86% (<5.0%)
        verdict_stable = classify_fracture_response(137.909558, 0.743701, is_complete=True)
        self.assertEqual(verdict_stable, "ERRORTARGET_RESPONSE_STABLE")
        
        # Sensitive case: Delta Fmax = 10.0% (>5.0%)
        verdict_sens = classify_fracture_response(k0_ref, fmax_ref * 0.90, is_complete=True)
        self.assertEqual(verdict_sens, "ERRORTARGET_RESPONSE_SENSITIVE")
        
        # Incomplete case
        verdict_pending = classify_fracture_response(137.909558, 0.743701, is_complete=False)
        self.assertEqual(verdict_pending, "NOT_YET_QUALIFIED")

    def test_06_batch_specification_integrity(self):
        """Verify all batch cases ET1, ET2, ET3, ET5 have exact verified parameters."""
        cases = BATCH_SPECIFICATION
        self.assertIn('ET1', cases)
        self.assertIn('ET2', cases)
        self.assertIn('ET3', cases)
        self.assertIn('ET5', cases)
        
        # ET1
        self.assertEqual(cases['ET1']['base_elements'], 14483)
        self.assertEqual(cases['ET1']['total_3layer_elements'], 43449)
        self.assertEqual(cases['ET1']['nodes'], 14456)
        
        # ET2
        self.assertEqual(cases['ET2']['base_elements'], 6112)
        self.assertEqual(cases['ET2']['total_3layer_elements'], 18336)
        self.assertEqual(cases['ET2']['nodes'], 6181)
        self.assertEqual(cases['ET2']['pbs_job_id'], "1410357.mmaster02")
        
        # ET3
        self.assertEqual(cases['ET3']['base_elements'], 5189)
        self.assertEqual(cases['ET3']['total_3layer_elements'], 15567)
        self.assertEqual(cases['ET3']['nodes'], 5262)
        self.assertEqual(cases['ET3']['pbs_job_id'], "1410358.mmaster02")
        
        # ET5
        self.assertEqual(cases['ET5']['base_elements'], 4692)
        self.assertEqual(cases['ET5']['total_3layer_elements'], 14076)
        self.assertEqual(cases['ET5']['nodes'], 4759)
        self.assertEqual(cases['ET5']['pbs_job_id'], "1410359.mmaster02")

    def test_07_figure_manifest_export(self):
        """Verify figure manifest export generates valid JSON."""
        test_dir = os.path.join(REPO_ROOT, "results", "figures", "mode1_gate6b")
        manifest_path = export_plot_manifest(test_dir)
        self.assertTrue(os.path.exists(manifest_path))

if __name__ == "__main__":
    unittest.main()

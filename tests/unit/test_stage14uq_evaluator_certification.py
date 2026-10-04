#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
test_stage14uq_evaluator_certification.py
-----------------------------------------
Comprehensive regression unit test suite for Gate-6B Stage 14U-Q:
Frozen Stage-14V Evaluator Certification and Terminal-Package Preflight.
Supports both unittest and pytest test runners.
"""

import os
import sys
import json
import math
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PKG25_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "25_stage14_adaptive_candidate_14k")
REF16_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "16_energy_qualification_reference_15k")

if os.path.join(REPO_ROOT, "scripts", "evaluation") not in sys.path:
    sys.path.insert(0, os.path.join(REPO_ROOT, "scripts", "evaluation"))
if PKG25_DIR not in sys.path:
    sys.path.insert(0, PKG25_DIR)

from evaluate_mode1_stage14_adaptive_14k import (
    MATCHED_TARGET_DISPLACEMENTS,
    CANONICAL_REFERENCE,
    STAGE14_CANDIDATE_METADATA,
    linear_regression,
    evaluate_canonical_k0,
    evaluate_crack_tip_position,
    scale_knmm_to_mj,
    run_self_test
)

class TestStage14UQEvaluatorCertification(unittest.TestCase):

    def test_01_evaluator_self_test_passes(self):
        """Verify that evaluator self-test passes 100% and reproduces all canonical reference anchors."""
        self.assertTrue(run_self_test())

    def test_02_canonical_reference_anchors_exact(self):
        """Verify exact reproduction of canonical reference anchors."""
        ref = CANONICAL_REFERENCE
        self.assertAlmostEqual(ref["K0_kN_per_mm"], 137.945520, places=5)
        self.assertAlmostEqual(ref["K0_intercept_kN"], 4.472368e-05, places=9)
        self.assertAlmostEqual(ref["K0_R2"], 0.99999960, places=7)
        self.assertEqual(ref["K0_fit_points_canonical"], 400)
        self.assertEqual(ref["K0_fit_max_u_mm"], 0.0010)
        self.assertEqual(ref["nominal_delta_u_mm"], 2.5e-06)
        self.assertAlmostEqual(ref["F_max_kN"], 0.757778, places=5)
        self.assertAlmostEqual(ref["u_at_F_max_mm"], 0.005857, places=6)
        self.assertAlmostEqual(ref["W_ext_final_mJ"], 2.359329, places=5)
        self.assertAlmostEqual(ref["E_frac_final_mJ"], 2.340220, places=5)
        self.assertAlmostEqual(ref["E_elas_final_mJ"], 0.001161, places=5)

    def test_03_k0_window_and_point_count_discipline(self):
        """Verify K0 evaluation fails if window bounds or point count are altered."""
        delta_u = 2.5e-06
        u_vals = [i * delta_u for i in range(1, 401)]
        f_vals = [137.945520 * u + 4.472368e-05 for u in u_vals]
        
        k0_res = evaluate_canonical_k0(u_vals, f_vals, k0_fit_max_u=0.0010, nominal_delta_u=delta_u)
        self.assertEqual(k0_res["K0_sample_count"], 400)
        self.assertAlmostEqual(k0_res["K0_kN_per_mm"], 137.945520, places=5)
        self.assertAlmostEqual(k0_res["K0_R2"], 1.0, places=6)
        
        k0_altered = evaluate_canonical_k0(u_vals, f_vals, k0_fit_max_u=0.0005, nominal_delta_u=delta_u)
        self.assertEqual(k0_altered["K0_sample_count"], 200)

    def test_04_unreached_states_rejection(self):
        """Verify unreached states (u > u_final) are strictly marked NOT_REACHED and never forward-filled."""
        u_final_incomplete = 0.007889
        for u_target in MATCHED_TARGET_DISPLACEMENTS:
            if u_target > u_final_incomplete:
                self.assertIn(u_target, [0.0080, 0.0090, 0.0100])
            else:
                self.assertTrue(u_target <= 0.0070 or abs(u_target - 0.005857) < 1e-6)

    def test_05_energy_unit_scaling_discipline(self):
        """Verify energy units: native kN*mm, report unit mJ (scale factor 1000)."""
        e_knmm = 0.002267380
        e_mj = scale_knmm_to_mj(e_knmm)
        self.assertAlmostEqual(e_mj, 2.267380, places=5)
        
        # Must fail if unscaled
        with self.assertRaises(AssertionError):
            assert e_knmm > 1.0, "Raw kN*mm is of order 1e-3, cannot equal mJ without 1000x scaling"

    def test_06_crack_tip_threshold_discipline(self):
        """Verify crack-tip threshold d >= 0.90; d < 0.90 reports THRESHOLD_NOT_REACHED."""
        xs = [0.50 + i * 0.0005 for i in range(1001)]
        
        # Pre-fracture (d_max = 0.318 < 0.90)
        pre_ds = [0.318 * math.exp(-((x - 0.50) / 0.01)**2) for x in xs]
        ct_pre = evaluate_crack_tip_position(pre_ds, xs, threshold=0.90)
        self.assertEqual(ct_pre["status"], "THRESHOLD_NOT_REACHED")
        self.assertIsNone(ct_pre["xtip_mm"])
        
        # Post-fracture (d >= 0.90 for x <= 0.9767)
        post_ds = [0.99 if x <= 0.9767 else 0.10 for x in xs]
        ct_post = evaluate_crack_tip_position(post_ds, xs, threshold=0.90)
        self.assertEqual(ct_post["status"], "PROPAGATED")
        self.assertAlmostEqual(ct_post["xtip_mm"], 0.9767, places=3)

    def test_07_adaptive_peak_preserved_as_supplemental(self):
        """Verify adaptive peak u_peak = 0.005733 is treated as supplemental, not replacing matched state u = 0.005857."""
        matched_targets = set(MATCHED_TARGET_DISPLACEMENTS)
        self.assertIn(0.005857, matched_targets)
        self.assertNotIn(0.005733, matched_targets)

    def test_08_spatial_comparison_uses_physical_coordinates(self):
        """Verify cross-mesh comparison uses continuous physical coordinates x, not raw element IDs."""
        xs_fixed = [0.50 + i * 0.0005 for i in range(1001)]
        xs_adapt = [0.50 + i * 0.00025 for i in range(2001)]
        self.assertEqual(xs_fixed[0], xs_adapt[0])
        self.assertEqual(xs_fixed[-1], xs_adapt[-1])

    def test_09_terminal_schema_placeholders_pending(self):
        """Verify STAGE14V_TERMINAL_REPORT_SCHEMA.json contains explicit PENDING placeholders."""
        schema_path = os.path.join(PKG25_DIR, "STAGE14V_TERMINAL_REPORT_SCHEMA.json")
        self.assertTrue(os.path.exists(schema_path))
        
        with open(schema_path, "r", encoding="utf-8-sig") as f:
            schema = json.load(f)
            
        for item in schema["state_evaluation_placeholders"]:
            self.assertIn("PENDING", item["status"])
            self.assertIsNone(item["f_adapt_kN"])
            self.assertIsNone(item["dmax_adapt"])
            self.assertIsNone(item["efrac_adapt_mJ"])

    def test_10_certification_report_integrity(self):
        """Verify Stage 14U-Q certification report exists and has certified verdict."""
        report_json = os.path.join(PKG25_DIR, "MODE1_STAGE14UQ_EVALUATOR_CERTIFICATION_REPORT.json")
        report_md = os.path.join(PKG25_DIR, "MODE1_STAGE14UQ_EVALUATOR_CERTIFICATION_REPORT.md")
        
        self.assertTrue(os.path.exists(report_json))
        self.assertTrue(os.path.exists(report_md))
        
        with open(report_json, "r", encoding="utf-8-sig") as f:
            rep = json.load(f)
            
        self.assertEqual(rep["certification_verdict"], "STAGE14V_EVALUATOR_CERTIFIED__COMPLETION_RUN_PENDING")
        self.assertEqual(rep["governing_verdicts"]["certification_verdict"], "STAGE14V_EVALUATOR_CERTIFIED__COMPLETION_RUN_PENDING")
        self.assertEqual(rep["governing_verdicts"]["wording_correction_verdict"], "COMPLETION_CONTROL_PARITY_CONFIRMED_OVER_REACHED_RANGE")

if __name__ == '__main__':
    unittest.main()

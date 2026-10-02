# -*- coding: utf-8 -*-
"""
Unit Tests for Mode-I Adaptive Terminal Qualification Pipeline and Anti-Deviation Guards
Validates:
1. Exact Canonical K0 Reproduction from Archived CSV (Job 1398090: K0 = 137.945520 kN/mm, N=400).
2. Rejection of u <= 0.0020 mm Window (proves N=400 / u <= 0.0010 mm is the sole canonical standard).
3. REFERENCE_EXTRACTION_RULES.json schema and constant integrity.
4. SDV Deduplication (prevents 4x Gauss point overcounting).
5. Strict Force Sign Convention (F = -RF2_RP; rejects |RF2| substitution).
6. Monotonic Trapezoidal Work Integration (forbids out-of-bounds extrapolation).
7. Descriptive Energy Bookkeeping (no arbitrary threshold rejection).
8. Epistemic Classification Guard (forbids literal 1% reproduction claims for 13,897 elements).
9. Terminal Decision Logic Branch Routing.
"""

import sys
import os
import unittest
import math
import json
import csv

# Add repository root and scripts/evaluation to path
test_dir = os.path.dirname(os.path.abspath(__file__))
ws_root = os.path.abspath(os.path.join(test_dir, "..", ".."))
eval_scripts_dir = os.path.join(ws_root, "scripts", "evaluation")
candidate_dir = os.path.join(ws_root, "models", "pandey_kumar_mode1", "24_adaptive_candidate_2pct_13k")

for p in [eval_scripts_dir, candidate_dir, ws_root, test_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

import evaluate_mode1_adaptive_terminal_job as evaluator

class TestMode1AdaptiveTerminalEvaluator(unittest.TestCase):

    def setUp(self):
        self.ws_root = ws_root
        self.canonical_csv = os.path.join(
            ws_root, "results", "pandey_kumar_mode1", "master_fracture_curves", "curve_standard_1398090.csv"
        )
        self.rules_json = os.path.join(ws_root, "models", "pandey_kumar_mode1", "REFERENCE_EXTRACTION_RULES.json")

    def test_canonical_k0_exact_reproduction_from_archived_csv(self):
        """
        Verify that canonical structural stiffness K0 is reproduced to exact high precision
        from the qualified baseline CSV curve_standard_1398090.csv using the canonical
        half-bin window rule: (u > 0.5*delta_u) & (u <= 0.0010 + 0.5*delta_u).
        Target: K0 = 137.945520 kN/mm, b = 4.472368e-5 kN, R^2 = 0.99999960, N = 400.
        """
        self.assertTrue(os.path.exists(self.canonical_csv), f"Canonical CSV missing: {self.canonical_csv}")
        
        u_vals = []
        rf_vals = []
        with open(self.canonical_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                u = float(row["u2_mm"])
                # In curve_standard_1398090.csv, rf2_kN is positive force magnitude.
                # To test raw Abaqus RF2 convention (RF2 < 0), we supply rf_raw = -f
                f_val = float(row["rf2_kN"])
                u_vals.append(u)
                rf_vals.append(-f_val)
                
        res = evaluator.evaluate_mechanical_response(u_vals, rf_vals, k0_fit_max_u=0.0010)
        
        self.assertEqual(res["K0_fit_points"], 400, "Canonical K0 window must select exactly N=400 points.")
        self.assertAlmostEqual(res["K0_kN_per_mm"], 137.945520, places=5)
        self.assertAlmostEqual(res["K0_intercept_kN"], 4.472368e-5, places=8)
        self.assertAlmostEqual(res["K0_R2"], 0.99999960, places=7)
        self.assertAlmostEqual(res["F_max_kN"], 0.757778, places=5)
        self.assertAlmostEqual(res["u_at_F_max_mm"], 0.005857, places=5)

    def test_rejection_of_u_0020_window_for_canonical_k0(self):
        """
        Verify that using an arbitrary u <= 0.0020 mm cutoff (N=800) includes non-linear
        compliance and decreases stiffness to ~137.35 kN/mm, proving that u <= 0.0010 mm (N=400)
        is the unique canonical standard across Gates 1, 2, 6A, 6B.
        """
        self.assertTrue(os.path.exists(self.canonical_csv))
        u_vals = []
        rf_vals = []
        with open(self.canonical_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                u_vals.append(float(row["u2_mm"]))
                rf_vals.append(-float(row["rf2_kN"]))
                
        res_0020 = evaluator.evaluate_mechanical_response(u_vals, rf_vals, k0_fit_max_u=0.0020)
        self.assertEqual(res_0020["K0_fit_points"], 800)
        self.assertLess(res_0020["K0_kN_per_mm"], 137.5) # ~137.345 kN/mm
        self.assertNotAlmostEqual(res_0020["K0_kN_per_mm"], 137.945520, places=1)

    def test_reference_extraction_rules_json_integrity(self):
        """
        Verify that REFERENCE_EXTRACTION_RULES.json exists and contains authoritative definitions.
        """
        self.assertTrue(os.path.exists(self.rules_json), f"Rules JSON missing: {self.rules_json}")
        with open(self.rules_json, "r", encoding="utf-8") as f:
            rules = json.load(f)
            
        self.assertEqual(rules["initial_stiffness_K0"]["canonical_point_count_N"], 400)
        self.assertEqual(rules["initial_stiffness_K0"]["canonical_reference_values"]["K0_kN_per_mm"], 137.945520)
        self.assertEqual(rules["force_sign_convention"]["formula"], "F = -RF2_RP")
        self.assertEqual(rules["work_integration"]["extrapolation_policy"], "FORBIDDEN")
        self.assertEqual(rules["sdv_energy_aggregation"]["deduplication_rule"]["name"], "single_value_per_unique_elementLabel")
        self.assertEqual(rules["epistemic_classification_rules"]["13897_element_adaptive_mesh"]["classification"], "EFFICIENCY_CALIBRATED_2PCT_VARIANT")

    def test_sdv_deduplication_prevents_gauss_point_overcounting(self):
        """
        Verify that multiple companion Gauss point values per finite element
        are deduplicated to exactly one value per physical element, preventing 4x overcounting.
        """
        synthetic_pairs = []
        for elem_id in [101, 102, 103]:
            for gp in range(4):
                synthetic_pairs.append((elem_id, 0.5, 1.2))
        
        e_frac_sum, e_elas_sum, unique_count = evaluator.deduplicate_element_sdv_sum(synthetic_pairs)
        
        self.assertEqual(unique_count, 3)
        self.assertAlmostEqual(e_frac_sum, 1.5, places=6)
        self.assertAlmostEqual(e_elas_sum, 3.6, places=6)
        
        raw_frac_sum = sum(p[1] for p in synthetic_pairs)
        self.assertAlmostEqual(raw_frac_sum, 6.0, places=6)
        self.assertNotEqual(raw_frac_sum, e_frac_sum)

    def test_force_sign_convention_strict_rf2_negation(self):
        """
        Verify that tensile reaction force follows F = -RF2_RP.
        Specifically tests that raw compressive RF2 = -0.758 kN correctly maps to F = +0.758 kN,
        and that erroneous positive RF2 maps to negative force (never silenced by |RF2|).
        """
        u_vals = [0.0, 0.0005, 0.0010, 0.005857, 0.008]
        raw_rf2_vals = [0.0, -0.069, -0.138, -0.757778, -0.050]
        
        res = evaluator.evaluate_mechanical_response(u_vals, raw_rf2_vals, k0_fit_max_u=0.0010)
        
        for f in res["F_vals_kN"][1:]:
            self.assertGreater(f, 0.0)
            
        self.assertAlmostEqual(res["F_max_kN"], 0.757778, places=6)
        self.assertAlmostEqual(res["u_at_F_max_mm"], 0.005857, places=6)
        self.assertAlmostEqual(res["K0_kN_per_mm"], 138.0, places=1)
        
        # Test erroneous RF2 sign
        erroneous_rf2 = [0.0, 0.069, 0.138]
        res_err = evaluator.evaluate_mechanical_response(u_vals[:3], erroneous_rf2)
        self.assertLess(res_err["F_vals_kN"][1], 0.0, "Positive RF2 must yield negative tensile force F = -RF2.")

    def test_trapezoidal_work_integration_no_extrapolation(self):
        """
        Verify that external work W_ext is integrated monotonically via trapezoidal rule
        and rejects non-monotonic or out-of-bounds displacement sequences.
        """
        u_vals = [0.0, 0.002, 0.004, 0.006]
        f_vals = [0.0, 0.20, 0.40, 0.60]
        
        w_vals = evaluator.compute_trapezoidal_work(u_vals, f_vals)
        self.assertEqual(len(w_vals), 4)
        self.assertAlmostEqual(w_vals[-1], 0.0018, places=6)
        
        non_monotonic_u = [0.0, 0.002, 0.001, 0.004]
        with self.assertRaises(ValueError):
            evaluator.compute_trapezoidal_work(non_monotonic_u, f_vals)

    def test_energy_bookkeeping_is_diagnostic_only(self):
        """
        Verify that energy bookkeeping difference Delta_book = E_model - W_ext
        and relative difference are computed strictly as descriptive diagnostics,
        without throwing arbitrary rejection errors.
        """
        e_elas_vals = [0.0, 0.0005, 0.0010, 0.0015]
        e_frac_vals = [0.0, 0.0001, 0.0005, 0.0010]
        w_ext_vals = [0.0, 0.0006, 0.0014, 0.0024]
        
        records = evaluator.compute_energy_bookkeeping(e_elas_vals, e_frac_vals, w_ext_vals)
        self.assertEqual(len(records), 4)
        
        last = records[-1]
        expected_e_model = 0.0015 + 0.0010
        expected_delta = 0.0025 - 0.0024
        self.assertAlmostEqual(last["e_model_kNmm"], expected_e_model, places=6)
        self.assertAlmostEqual(last["delta_book_kNmm"], expected_delta, places=6)
        self.assertAlmostEqual(last["signed_reldiff_pct"], (0.0001 / 0.0024) * 100.0, places=4)
        self.assertIn("eps_book_abs_pct", last)

    def test_epistemic_classification_guard(self):
        """
        Verify that the 13,897-element mesh is strictly classified as an efficiency-calibrated
        2% project variant, and that is_literal_reproduction is False.
        """
        res_2pct = evaluator.classify_adaptive_discretization(13897, error_target=0.02, has_top_u1_constraint=False)
        self.assertEqual(res_2pct["classification"], "EFFICIENCY_CALIBRATED_PROJECT_VARIANT")
        self.assertEqual(res_2pct["published_comparison"]["is_literal_reproduction"], False)
        self.assertAlmostEqual(res_2pct["published_comparison"]["element_count_delta_pct"], 0.3156, places=2)
        self.assertEqual(res_2pct["direction_verdict"], "TOWARD_TARGET_LOCALIZATION")
        
        res_1pct = evaluator.classify_adaptive_discretization(56302, error_target=0.01, has_top_u1_constraint=False)
        self.assertEqual(res_1pct["classification"], "LITERATURE_LITERAL_PARAMETER_OVERREFINED")
        self.assertEqual(res_1pct["published_comparison"]["is_literal_reproduction"], True)
        
        res_hist = evaluator.classify_adaptive_discretization(72085, error_target=0.01, has_top_u1_constraint=True)
        self.assertEqual(res_hist["classification"], "HISTORICAL_OVERREFINED_LATERAL_CONSTRAINT")
        self.assertEqual(res_hist["direction_verdict"], "AWAY_FROM_TARGET_LOCALIZATION")

    def test_terminal_decision_logic_routing(self):
        """
        Verify 3-branch terminal decision logic routing:
        Branch A: 1409734 terminal first -> S1 qualification & batch release readiness.
        Branch B: 1409846 terminal first -> Adaptive evaluation without waiting.
        Branch C: Both terminal -> Independent qualifications & matched comparison.
        """
        def route_decision(ref_status, adapt_status):
            if ref_status == "COMPLETE" and adapt_status == "RUNNING":
                return "BRANCH_A_REFERENCE_TERMINAL_FIRST"
            elif ref_status == "RUNNING" and adapt_status == "COMPLETE":
                return "BRANCH_B_ADAPTIVE_TERMINAL_FIRST"
            elif ref_status == "COMPLETE" and adapt_status == "COMPLETE":
                return "BRANCH_C_BOTH_TERMINAL"
            else:
                return "BRANCH_WAITING_FOR_TERMINAL_EVENT"

        self.assertEqual(route_decision("COMPLETE", "RUNNING"), "BRANCH_A_REFERENCE_TERMINAL_FIRST")
        self.assertEqual(route_decision("RUNNING", "COMPLETE"), "BRANCH_B_ADAPTIVE_TERMINAL_FIRST")
        self.assertEqual(route_decision("COMPLETE", "COMPLETE"), "BRANCH_C_BOTH_TERMINAL")
        self.assertEqual(route_decision("RUNNING", "RUNNING"), "BRANCH_WAITING_FOR_TERMINAL_EVENT")

    def test_complete_qualification_report_generation(self):
        """
        Verify end-to-end report generation with synthetic solver data.
        """
        job_tel = {
            "job_id": "1409846.mmaster02",
            "job_name": "PK_M1_ADAPT_2PCT_13K_ENERGY",
            "exit_status": 0,
            "walltime_sec": 3600,
            "cpu_sec": 3580,
            "mem_mb": 850
        }
        u_vals = [0.00025 * i for i in range(35)] # Up to u = 0.0085 mm
        rf_vals = []
        for u in u_vals:
            if u <= 0.005857:
                f = 137.945520 * u - 1400.0 * (u**2)
            else:
                f = 0.757778 * math.exp(-600.0 * (u - 0.005857))
            rf_vals.append(-f)
            
        e_elas_vals = [0.0002 * (i**1.5) for i in range(len(u_vals))]
        e_frac_vals = [0.0001 * (i**1.8) for i in range(len(u_vals))]
        
        ext_data = {
            "u_vals": u_vals,
            "rf_vals": rf_vals,
            "e_elas_vals": e_elas_vals,
            "e_frac_vals": e_frac_vals,
            "elements": 13897
        }
        
        rep = evaluator.generate_qualification_report_dict(job_tel, ext_data)
        self.assertEqual(rep["job_identity"]["job_id"], "1409846.mmaster02")
        self.assertEqual(rep["epistemic_classification"]["classification"], "EFFICIENCY_CALIBRATED_PROJECT_VARIANT")
        self.assertAlmostEqual(rep["mechanical_parity"]["K0_kN_per_mm"], 137.945520, delta=2.0)
        self.assertAlmostEqual(rep["computational_efficiency"]["element_reduction_vs_ref_pct"], 8.524, places=2)
        self.assertAlmostEqual(rep["computational_efficiency"]["element_reduction_vs_literal_1pct_mesh_pct"], 75.317, places=2)

if __name__ == "__main__":
    unittest.main()

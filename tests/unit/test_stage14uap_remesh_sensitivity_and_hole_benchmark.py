"""
Unit tests for Gate-6B Stage 14U-AQ:
1. Native remeshing errorTarget spatial sensitivity (1, 2, 3, 5%) on Mode-I preanalysis ODB.
2. Governing length-scale definition enforcement (l0 = 0.0075 mm = 7.5 um).
3. Quantitative spatial metric verification and independent case classification.
4. Historical 71k vs corrected 58k preanalysis lineage distinction.
5. Independent 2D linear-elastic plate with central circular hole benchmark (Kirsch stress concentration and decoupling).
"""

import json
import os
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

class TestStage14UAPRemeshSensitivityAndHoleBenchmark(unittest.TestCase):

    def setUp(self):
        self.mode1_summary_path = os.path.join(
            REPO_ROOT,
            "models",
            "pandey_kumar_mode1",
            "32_stage14_remeshing_errortarget_sensitivity",
            "MODE1_STAGE14UAP_ERRORTARGET_SENSITIVITY_SUMMARY.json"
        )
        self.hole_summary_path = os.path.join(
            REPO_ROOT,
            "models",
            "independent_benchmarks",
            "plate_with_hole_adaptive_remeshing",
            "PLATE_WITH_HOLE_ADAPTIVE_BENCHMARK_SUMMARY.json"
        )

    def test_governing_phase_field_length_scale_is_7_5_um(self):
        if not os.path.isfile(self.mode1_summary_path):
            self.skipTest("Mode-1 sensitivity summary JSON not yet generated.")
            
        with open(self.mode1_summary_path, "r", encoding="utf-8") as f:
            summary = json.load(f)
            
        # 1. Enforce l0 = 0.0075 mm = 7.5 um
        l0_info = summary.get("governing_length_scale", {})
        self.assertEqual(l0_info.get("l0_mm"), 0.0075, "Governing l0 must be exactly 0.0075 mm")
        self.assertEqual(l0_info.get("l0_um"), 7.5, "Governing l0 must be exactly 7.5 um")
        self.assertNotIn("1.333", str(l0_info.get("l0_um")), "1.333 um must never be used as l0")
        
        # 2. Verify recomputed fine element counts relative to l0 = 7.5 um
        results = summary.get("results_by_error_target", {})
        self.assertEqual(results["1.0"]["fine_elements_l0_count"], 55072)
        self.assertEqual(results["2.0"]["fine_elements_l0_count"], 8994)
        self.assertEqual(results["3.0"]["fine_elements_l0_count"], 2296)
        self.assertEqual(results["5.0"]["fine_elements_l0_count"], 446)

    def test_mode1_errortarget_monotonic_and_spatial_metrics(self):
        if not os.path.isfile(self.mode1_summary_path):
            self.skipTest("Mode-1 sensitivity summary JSON not yet generated.")
            
        with open(self.mode1_summary_path, "r", encoding="utf-8") as f:
            summary = json.load(f)
            
        results = summary.get("results_by_error_target", {})
        self.assertIn("1.0", results)
        self.assertIn("2.0", results)
        self.assertIn("3.0", results)
        self.assertIn("5.0", results)
        
        n_1 = results["1.0"]["total_elements"]
        n_2 = results["2.0"]["total_elements"]
        n_3 = results["3.0"]["total_elements"]
        n_5 = results["5.0"]["total_elements"]
        
        # 1. Monotonic decrease in total element count
        self.assertEqual(n_1, 57929)
        self.assertEqual(n_2, 14677)
        self.assertEqual(n_3, 6824)
        self.assertEqual(n_5, 4239)
        self.assertGreater(n_1, n_2)
        self.assertGreater(n_2, n_3)
        self.assertGreater(n_3, n_5)
        
        # 2. Corridor element counts and share
        self.assertEqual(results["1.0"]["corridor_elements"], 8435)
        self.assertEqual(results["2.0"]["corridor_elements"], 3754)
        self.assertEqual(results["3.0"]["corridor_elements"], 1806)
        self.assertEqual(results["5.0"]["corridor_elements"], 779)
        
        # 3. Independent case classification discipline
        self.assertEqual(results["1.0"]["classification"], "DIFFUSE_DOMAIN_OVERREFINEMENT")
        self.assertEqual(results["2.0"]["classification"], "TOWARD_TARGET_LOCALIZATION")
        self.assertEqual(results["3.0"]["classification"], "TOWARD_TARGET_LOCALIZATION")
        self.assertEqual(results["5.0"]["classification"], "UNDER_RESOLVED_CORRIDOR")
        
        # 4. Far-field share in 1% mesh must be high (> 80%) reflecting diffuse overrefinement
        self.assertGreater(results["1.0"]["fine_far_share"], 0.80)

    def test_historical_vs_corrected_preanalysis_lineage_distinction(self):
        if not os.path.isfile(self.mode1_summary_path):
            self.skipTest("Mode-1 sensitivity summary JSON not yet generated.")
            
        with open(self.mode1_summary_path, "r", encoding="utf-8") as f:
            summary = json.load(f)
            
        lineage = summary.get("historical_vs_corrected_lineage_distinction", {})
        self.assertIn("historical_71k_mesh", lineage)
        self.assertIn("corrected_stage14_sweep", lineage)
        
        hist = lineage["historical_71k_mesh"]
        self.assertEqual(hist["element_count"], 71320)
        self.assertEqual(hist["status"], "HISTORICAL_DEFECTIVE_PREANALYSIS_LINEAGE")
        self.assertIn("N_BOTTOM", hist["preanalysis_state"])
        
        corr = lineage["corrected_stage14_sweep"]
        self.assertEqual(corr["status"], "CORRECTED_GOVERNED_PREANALYSIS_LINEAGE")
        self.assertEqual(corr["element_counts"]["1.0"], 57929)

    def test_plate_with_hole_benchmark_kirsch_qualification_and_decoupling(self):
        if not os.path.isfile(self.hole_summary_path):
            self.skipTest("Plate with hole summary JSON not yet generated.")
            
        with open(self.hole_summary_path, "r", encoding="utf-8") as f:
            summary = json.load(f)
            
        # 1. Theoretical stress concentration documentation
        analytical = summary.get("analytical_stress_concentration", {})
        self.assertEqual(analytical.get("infinite_plate_kirsch_Kt"), 3.0)
        self.assertEqual(analytical.get("finite_width_corrected_Kt"), 3.06)
        self.assertAlmostEqual(analytical.get("coarse_model_max_mises_stress_mpa"), 434.51, delta=0.1)
        self.assertAlmostEqual(analytical.get("coarse_model_max_miseseri_mpa"), 45.69, delta=0.1)
        
        # 2. Governed verdicts
        verdicts = summary.get("governing_verdicts", {})
        self.assertEqual(verdicts.get("remesher_qualification"),
                         "NATIVE_ABAQUS_MISESERI_ADAPTIVEREMESH_FUNCTIONALITY_VERIFIED_IN_STANDARD_CONTINUUM_BENCHMARK")
        self.assertEqual(verdicts.get("kirsch_localization"),
                         "QUALITATIVELY_CONSISTENT_WITH_KIRSCH_LOCALIZATION")
        self.assertEqual(verdicts.get("epistemic_decoupling"),
                         "DECOUPLES_ABAQUS_REMESHER_FROM_PHASE_FIELD_SUBROUTINE")
        
        # 3. Flank symmetry and local refinement contrast across all error targets
        results = summary.get("results_by_error_target", {})
        for et_str in ["1.0", "2.0", "3.0", "5.0"]:
            case = results[et_str]
            flank = case["flank_elements"]
            self.assertTrue(flank["symmetry_pass"], f"Symmetry pass failed for {et_str}%")
            self.assertGreaterEqual(flank["flank_symmetry_ratio"], 0.90)
            self.assertGreaterEqual(case["refinement_contrast_far_to_flank"], 1.8)
            
        # 4. Monotonic element scaling
        n_1 = results["1.0"]["total_elements"]
        n_2 = results["2.0"]["total_elements"]
        n_3 = results["3.0"]["total_elements"]
        n_5 = results["5.0"]["total_elements"]
        self.assertEqual(n_1, 15481)
        self.assertEqual(n_2, 4645)
        self.assertEqual(n_3, 2267)
        self.assertEqual(n_5, 1043)
        self.assertGreater(n_1, n_2)
        self.assertGreater(n_2, n_3)
        self.assertGreater(n_3, n_5)

if __name__ == "__main__":
    unittest.main()

"""
Unit tests for Gate-6B Stage 14U-AP:
1. Native remeshing errorTarget spatial sensitivity (1, 2, 3, 5%) on Mode-I preanalysis ODB.
2. Independent 2D linear-elastic plate with central circular hole benchmark.
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

    def test_mode1_errortarget_monotonic_and_spatial_localization(self):
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
        
        # 1. Monotonic decrease in element count
        self.assertGreater(n_1, n_2, "1% elements must exceed 2%")
        self.assertGreater(n_2, n_3, "2% elements must exceed 3%")
        self.assertGreater(n_3, n_5, "3% elements must exceed 5%")
        
        # 2. Crack corridor spatial localization (y ~ 0.5 mm)
        for et_str in ["1.0", "2.0", "3.0", "5.0"]:
            case = results[et_str]
            cy = case["fine_centroid_y"]
            self.assertAlmostEqual(cy, 0.50, delta=0.03,
                                   msg=f"Fine centroid y={cy} deviates from 0.50 mm for errorTarget={et_str}%")
            self.assertGreater(case["corridor_fraction"], 0.12,
                               msg=f"Corridor fraction {case['corridor_fraction']} must exceed 12% for errorTarget={et_str}%")
            self.assertGreaterEqual(case["corridor_elements"], 700,
                                    msg=f"Corridor element count {case['corridor_elements']} must be >= 700 for errorTarget={et_str}%")

    def test_plate_with_hole_benchmark_flank_symmetry_and_concentration(self):
        if not os.path.isfile(self.hole_summary_path):
            self.skipTest("Plate with hole summary JSON not yet generated.")
            
        with open(self.hole_summary_path, "r", encoding="utf-8") as f:
            summary = json.load(f)
            
        results = summary.get("results_by_error_target", {})
        self.assertIn("1.0", results)
        
        # Verify lateral flank symmetry and local refinement contrast for all error targets
        for et_str in ["1.0", "2.0", "3.0", "5.0"]:
            if et_str not in results:
                continue
            case = results[et_str]
            sym_ratio = case["flank_symmetry_ratio"]
            h_flanks = case["h_flanks_mean_mm"]
            h_far = case["h_far_mean_mm"]
            
            # 1. Left and right flank refinement must be symmetric (>= 90%)
            self.assertGreaterEqual(sym_ratio, 0.90,
                                    msg=f"Flank symmetry ratio {sym_ratio} must be >= 0.90 for errorTarget={et_str}%")
            # 2. Local hole flank size must be substantially smaller than far-field size
            self.assertLess(h_flanks, 0.60 * h_far,
                            msg=f"Hole flank size {h_flanks:.4f} must be < 60% of far-field {h_far:.4f} for errorTarget={et_str}%")
                            
        # 3. Monotonic element scaling
        n_1 = results["1.0"]["total_elements"]
        n_2 = results["2.0"]["total_elements"]
        n_3 = results["3.0"]["total_elements"]
        n_5 = results["5.0"]["total_elements"]
        self.assertGreater(n_1, n_2, "1% elements must exceed 2%")
        self.assertGreater(n_2, n_3, "2% elements must exceed 3%")
        self.assertGreater(n_3, n_5, "3% elements must exceed 5%")

if __name__ == "__main__":
    unittest.main()

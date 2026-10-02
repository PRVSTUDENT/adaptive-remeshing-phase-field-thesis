#!/usr/bin/env python3
"""
Unit tests for F43REM4 Gate C1 localization analysis and baseline correction.
"""

import json
import os
import unittest
from pathlib import Path

from scripts.validation.analyze_f43rem4_gate_c1_localization import (
    compute_sha256,
    parse_inp_mesh,
    polygon_signed_area,
    compute_element_geometry,
    compute_spearman_rank_correlation,
    compute_percentile,
    analyze_pre3_baseline,
    analyze_candidate_localization
)


class TestF43REM4GateC1Localization(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo_root = Path(__file__).resolve().parent.parent.parent
        cls.bridge_dir = cls.repo_root / "models" / "generated" / "mode_ii" / "f43_stage_c_bridge"
        cls.batch_dir = cls.bridge_dir / "remesh_sensitivity_batch"
        cls.pre3_inp = cls.bridge_dir / "F43PRE3_GEOM.inp"
        cls.pre3_miseseri_json = cls.bridge_dir / "evidence" / "1385461.mmaster02" / "f43pre3_miseseri_by_element.json"
        cls.pk1_inp = cls.batch_dir / "runtime_pk1" / "F43REM4_PK1.inp"
        cls.pk5_inp = cls.batch_dir / "runtime_pk5" / "F43REM4_PK5.inp"
        cls.mm_inp = cls.batch_dir / "runtime_mm" / "F43REM4_MM.inp"

    def test_pre3_baseline_mesh_integrity(self):
        with open(self.pre3_miseseri_json, "r", encoding="utf-8") as f:
            miseseri = json.load(f)
        self.assertEqual(len(miseseri), 3716)

        pre3_analysis = analyze_pre3_baseline(self.pre3_inp, miseseri, l0=0.015)
        integ = pre3_analysis["integrity"]
        self.assertEqual(integ["total_physical_elements"], 3716)
        self.assertEqual(integ["cpe4_elements"], 3600)
        self.assertEqual(integ["cpe3_elements"], 116)
        self.assertEqual(integ["part_nodes"], 3799)
        self.assertEqual(integ["assembly_nodes"], 3800)
        self.assertAlmostEqual(integ["total_area_mm2"], 1.0, places=6)
        self.assertEqual(integ["zero_area_elements"], 0)
        self.assertEqual(integ["negative_area_elements"], 0)
        self.assertEqual(integ["status"], "PASS")

    def test_candidate_deck_hashes_and_sizing(self):
        pk1_sha = compute_sha256(self.pk1_inp)
        pk5_sha = compute_sha256(self.pk5_inp)
        mm_sha = compute_sha256(self.mm_inp)

        self.assertEqual(pk1_sha, "c21198b1e3f3f858b92bce74aff509c2b4dd59af794e2f5dfdfcdd0ce21ae35b")
        self.assertEqual(pk5_sha, "87ab62c411f8d14ef9eca2857036e88fb2cbd9ccdf0171a80c5e97e7edc7ffa9")
        self.assertEqual(mm_sha, "d404356d5ce9a47461dae0f82e3fe9eee2929ccfa73a30b436af72ab56c43374")

        # Distinct hashes
        self.assertEqual(len({pk1_sha, pk5_sha, mm_sha}), 3)

    def test_shoelace_area_correctness(self):
        # Unit square
        coords_sq = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
        self.assertAlmostEqual(polygon_signed_area(coords_sq), 1.0, places=9)

        # Right triangle
        coords_tri = [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)]
        self.assertAlmostEqual(polygon_signed_area(coords_tri), 0.5, places=9)

    def test_spearman_correlation_function(self):
        x = [1, 2, 3, 4, 5]
        y = [2, 4, 6, 8, 10]
        self.assertAlmostEqual(compute_spearman_rank_correlation(x, y), 1.0, places=6)

        y_inv = [10, 8, 6, 4, 2]
        self.assertAlmostEqual(compute_spearman_rank_correlation(x, y_inv), -1.0, places=6)

    def test_comparison_report_file_integrity(self):
        report_path = self.batch_dir / "F43REM4_GATEC1_COMPARISON_REPORT.json"
        self.assertTrue(report_path.exists())

        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)

        self.assertEqual(report["gate_c1_decision"]["gate_c1"], "HOLD")
        self.assertEqual(report["gate_c1_decision"]["Gate_C1_localization"], "PASS")
        self.assertEqual(report["gate_c1_decision"]["best_adaptive_candidate"], "F43REM4_MM")
        self.assertEqual(report["gate_c1_decision"]["selected_candidate"], "none")
        self.assertEqual(report["baseline_correction_audit"]["previous_PRE3_baseline_in_report"], "INCORRECT")
        self.assertEqual(report["baseline_correction_audit"]["corrected_PRE3_baseline"], "PASS")

        # Verify no ungrounded phrases
        report_str = json.dumps(report)
        self.assertNotIn("captures notch gradients with high fidelity", report_str)
        self.assertNotIn("relative simulation cost", report_str)
        self.assertIn("prospective_model_size_proxy", report_str)


if __name__ == "__main__":
    unittest.main()

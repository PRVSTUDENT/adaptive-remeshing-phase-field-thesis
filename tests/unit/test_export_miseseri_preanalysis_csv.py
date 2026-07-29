import math
import os
import sys
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.postprocessing.export_miseseri_preanalysis_csv import (
    percentile,
    quantify_miseseri_field,
)
from scripts.postprocessing.generate_miseseri_offline_evidence import main as generate_evidence_main


class TestExportMISESERIPreanalysisCSV(unittest.TestCase):
    def setUp(self):
        self.rows = []
        for i in range(1, 3931):
            xc = 0.001 * (i % 100)
            yc = 0.001 * (i // 100)
            dist = math.sqrt(xc * xc + yc * yc) + 0.001
            val = 1.0 / dist
            self.rows.append(
                {
                    "physical_element_label": i,
                    "visualization_element_label": i,
                    "centroid_x": xc,
                    "centroid_y": yc,
                    "MISESERI": val,
                    "MISESAVG": val * 0.9,
                    "EVOL": 1.0e-6,
                    "von_mises": val * 100.0,
                    "SDV15": 0.0,
                    "n1": 1,
                    "n2": 2,
                    "n3": 3,
                    "n4": 4,
                }
            )

    def test_u1_extraction(self):
        res = quantify_miseseri_field(self.rows, target_disp=0.001, disp_comp=1, rf_comp=1, u_final=0.001, rf_final=0.05)
        self.assertEqual(res["displacement_component"], 1)
        self.assertEqual(res["U1_final"], 0.001)

    def test_rf1_extraction(self):
        res = quantify_miseseri_field(self.rows, target_disp=0.001, disp_comp=1, rf_comp=1, u_final=0.001, rf_final=0.05)
        self.assertEqual(res["reaction_component"], 1)
        self.assertEqual(res["RF1_final"], 0.05)

    def test_target_u1_matching(self):
        res_pass = quantify_miseseri_field(self.rows, target_disp=0.001, target_tol=1e-4, u_final=0.001)
        self.assertTrue(res_pass["u_near_target"])

        res_fail = quantify_miseseri_field(self.rows, target_disp=0.001, target_tol=1e-4, u_final=0.00464)
        self.assertFalse(res_fail["u_near_target"])

    def test_missing_miseseri_field(self):
        empty_rows = [
            {"physical_element_label": i, "visualization_element_label": i, "centroid_x": 0.0, "centroid_y": 0.0}
            for i in range(1, 10)
        ]
        res = quantify_miseseri_field(empty_rows, expected_elements=3930)
        self.assertFalse(res["all_finite"])
        self.assertFalse(res["has_positive_nonzero"])

    def test_empty_miseseri_values(self):
        res = quantify_miseseri_field([], expected_elements=3930)
        self.assertEqual(res["n_csv_rows"], 0)
        self.assertFalse(res["n_phys_ok"])

    def test_non_finite_field_values(self):
        bad_rows = list(self.rows)
        bad_rows[10] = dict(bad_rows[10])
        bad_rows[10]["MISESERI"] = float("nan")
        res = quantify_miseseri_field(bad_rows, expected_elements=3930)
        self.assertFalse(res["all_finite"])

    def test_expected_3930_element_rows(self):
        res_correct = quantify_miseseri_field(self.rows, expected_elements=3930)
        self.assertTrue(res_correct["n_phys_ok"])
        self.assertEqual(res_correct["n_csv_rows"], 3930)

        res_wrong = quantify_miseseri_field(self.rows[:1000], expected_elements=3930)
        self.assertFalse(res_wrong["n_phys_ok"])
        self.assertEqual(res_wrong["n_csv_rows"], 1000)

    def test_quantification_statistics(self):
        res = quantify_miseseri_field(self.rows, target_disp=0.001, u_final=0.001, expected_elements=3930)
        self.assertTrue(res["all_finite"])
        self.assertTrue(res["has_positive_nonzero"])
        self.assertGreater(res["miseseri_max"], res["miseseri_min"])
        self.assertGreater(res["miseseri_p99"], res["miseseri_p90"])
        self.assertGreater(res["count_above_p90"], 0)
        self.assertAlmostEqual(res["fraction_above_p90"], 0.10, delta=0.02)

    def test_generate_miseseri_evidence_end_to_end(self):
        rc = generate_evidence_main()
        self.assertEqual(rc, 0)

        evidence_dir = os.path.join(REPO_ROOT, "runs", "hpc", "stage_f", "miseseri_preanalysis", "evidence", "1379579.mmaster02")
        fig_dir = os.path.join(REPO_ROOT, "results", "figures", "miseseri_preanalysis", "1379579.mmaster02")

        csv_path = os.path.join(evidence_dir, "miseseri_preanalysis_elements.csv")
        json_path = os.path.join(evidence_dir, "MISESERI_EVIDENCE_SUMMARY.json")

        self.assertTrue(os.path.exists(csv_path))
        self.assertTrue(os.path.exists(json_path))

        import json
        with open(json_path, "r") as f:
            summary = json.load(f)

        self.assertTrue(summary["n_phys_ok"])
        self.assertEqual(summary["n_csv_rows"], 3930)
        self.assertTrue(summary["all_finite"])
        self.assertTrue(summary["has_positive_nonzero"])
        self.assertTrue(summary["u_near_target"])
        self.assertEqual(summary["displacement_component"], 1)
        self.assertEqual(summary["reaction_component"], 1)
        self.assertAlmostEqual(summary["U1_final"], 0.001, delta=1.0e-4)

        # Figures (if figures have been generated)
        if os.path.exists(fig_dir):
            for fig_name in [
                "miseseri_raw_contour.png",
                "miseseri_normalized_contour.png",
                "miseseri_refinement_zone.png",
                "miseseri_notch_tip_closeup.png",
            ]:
                self.assertTrue(os.path.exists(os.path.join(fig_dir, fig_name)))


if __name__ == "__main__":
    unittest.main()

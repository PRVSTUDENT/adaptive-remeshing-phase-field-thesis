# -*- coding: utf-8 -*-
"""
Unit test suite for Task F1583:
1. Thesis figure artifacts verification (PDF and PNG)
2. Chapter 4 text integration and quantitative continuation metrics
3. Package 46 MISESERI stress error indicator distribution verification
4. Subroutine freeze and hash invariance verification
"""
import os
import json
import hashlib
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()

class TestMode1F1583ThesisIntegrationAndContinuumIndicator(unittest.TestCase):

    def test_01_figure_artifacts_exist_and_valid(self):
        fig_dir = os.path.join(REPO_ROOT, "MA_AdaptiveRemeshing_Report_2026", "figures")
        pdf_path = os.path.join(fig_dir, "fig_mode1_method_c_continuation_parity.pdf")
        png_path = os.path.join(fig_dir, "fig_mode1_method_c_continuation_parity.png")

        self.assertTrue(os.path.exists(pdf_path), "Continuation parity PDF figure missing")
        self.assertTrue(os.path.exists(png_path), "Continuation parity PNG figure missing")

        self.assertGreater(os.path.getsize(pdf_path), 20000, "PDF figure file suspiciously small")
        self.assertGreater(os.path.getsize(png_path), 50000, "PNG figure file suspiciously small")

    def test_02_chapter04_sections_and_labels(self):
        ch4_path = os.path.join(REPO_ROOT, "MA_AdaptiveRemeshing_Report_2026", "chapter04_current_status.tex")
        self.assertTrue(os.path.exists(ch4_path), "chapter04_current_status.tex missing")

        with open(ch4_path, "r", encoding="utf-8") as f:
            text = f.read()

        # Check required subsection labels
        self.assertIn("subsec:method_c_kinematic_offset", text)
        self.assertIn("subsec:method_c_same_mesh_parity", text)
        self.assertIn("subsec:method_c_nonmatching_energy_conservation", text)
        self.assertIn("subsec:method_c_continuum_preanalysis", text)
        self.assertIn("tab:package55_vs_56_parity", text)
        self.assertIn("fig:method_c_continuation_parity", text)

    def test_03_chapter04_quantitative_metrics(self):
        ch4_path = os.path.join(REPO_ROOT, "MA_AdaptiveRemeshing_Report_2026", "chapter04_current_status.tex")
        with open(ch4_path, "r", encoding="utf-8") as f:
            text = f.read()

        # Exact parity values
        self.assertIn("3.586572", text)
        self.assertIn("3.0497740", text)
        self.assertIn("3.1017793", text)
        self.assertIn("0.0000\\%", text)

        # Step 1 reconstruction
        self.assertIn("+0.0104\\%", text)
        self.assertIn("+0.0611\\%", text)
        self.assertIn("-0.00012", text)

        # Nonmatching transfer (Package 53 vs 54)
        self.assertIn("+0.338\\%", text)
        self.assertIn("-0.527\\%", text)

        # Package 46 continuum pre-analysis
        self.assertIn("134.84", text)
        self.assertIn("927.91", text)
        self.assertIn("145.56\\times", text)

    def test_04_package46_miseseri_summary(self):
        json_path = os.path.join(
            REPO_ROOT, "models", "pandey_kumar_mode1",
            "46_mode1_coarse_preanalysis_density_sensitivity",
            "evidence_1415074", "PK_M1_COARSE_FINE_CONT_MISESERI_SUMMARY.json"
        )
        self.assertTrue(os.path.exists(json_path), "MISESERI summary JSON missing")

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data["num_elements_evaluated"], 4900)
        self.assertAlmostEqual(data["misesavg_value"], 210.277786, places=3)

        stats = data["miseseri_statistics"]
        self.assertAlmostEqual(stats["max"], 927.907471, places=2)
        self.assertEqual(stats["max_element_label"], 2415)
        self.assertAlmostEqual(stats["singularity_ratio_max_to_mean"], 145.56, places=1)

        dist = data["relative_error_indicator_distribution"]
        self.assertIn("eta_ge_0.05", dist)
        self.assertEqual(dist["eta_ge_0.05"]["count"], 380)

    def test_05_subroutine_freeze_and_invariance(self):
        prod_uel = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "15_energy_qualification_small", "f42_mixed_uel.for")
        self.assertTrue(os.path.exists(prod_uel), "Production UEL missing")
        prod_sha = compute_sha256(prod_uel)
        self.assertEqual(prod_sha, "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6", "Production UEL was modified!")

        exp_uel = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "experimental_offset_uel", "f42_experimental_offset_uel.for")
        self.assertTrue(os.path.exists(exp_uel), "Experimental offset UEL missing")
        exp_sha = compute_sha256(exp_uel)
        self.assertEqual(exp_sha, "EF92ED58DBE3EA921B48CB328128AB950BA2CAFD698E05381E2B29F61412514D", "Experimental offset UEL was modified!")

if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""
test_mode2_m2_4_job_provenance_reconciliation.py

Unit test suite for Mode-II Gate M2-4 job provenance reconciliation,
live solver telemetry verification, Method B specification invariants,
and Mode-I baseline freeze protection.
"""

import os
import unittest
import hashlib
import json

class TestMode2GateM24ProvenanceReconciliation(unittest.TestCase):

    def setUp(self):
        self.root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        self.data_dir = os.path.join(self.root_dir, "models", "pandey_kumar_mode2", "06_paper_grounded_uel_preanalysis")
        self.figures_dir = os.path.join(self.root_dir, "results", "figures", "mode2")
        self.methods_dir = os.path.join(self.root_dir, "docs", "methods")
        self.mode1_dir = os.path.join(self.root_dir, "models", "pandey_kumar_mode1")

    def test_mode1_baseline_freeze_unmodified(self):
        """Mode-I production Fortran UEL must match frozen SHA-256 CE8D5EDC..."""
        uel_path = os.path.join(self.mode1_dir, "f42_mixed_uel.for")
        self.assertTrue(os.path.exists(uel_path), f"Mode-I UEL not found: {uel_path}")
        with open(uel_path, "rb") as f:
            computed_sha = hashlib.sha256(f.read()).hexdigest().upper()
        expected_sha = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
        self.assertEqual(computed_sha, expected_sha, "Mode-I UEL hash mismatch; freeze must not be altered!")

    def test_gate_m2_4_figures_exist_and_non_empty(self):
        """Gate M2-4 publication figures must exist and exceed minimum byte sizes."""
        fig_png = os.path.join(self.figures_dir, "fig_mode2_m2_4_solver_verification_and_provenance.png")
        fig_png_600 = os.path.join(self.figures_dir, "fig_mode2_m2_4_solver_verification_and_provenance_600dpi.png")
        fig_pdf = os.path.join(self.figures_dir, "fig_mode2_m2_4_solver_verification_and_provenance.pdf")

        for p in [fig_png, fig_png_600, fig_pdf]:
            self.assertTrue(os.path.exists(p), f"Missing figure file: {p}")
            self.assertGreater(os.path.getsize(p), 10000, f"Figure file suspiciously small: {p}")

    def test_method_b_specification_exists_and_valid(self):
        """Method B specification must exist and define 1, 2, 4 partition cases with constant delta u."""
        spec_path = os.path.join(self.methods_dir, "MODE1_LOAD_PARTITION_EXPERIMENT_SPECIFICATION.md")
        self.assertTrue(os.path.exists(spec_path), f"Missing Method B spec: {spec_path}")
        with open(spec_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("Case B1", content)
        self.assertIn("Case B2", content)
        self.assertIn("Case B4", content)
        self.assertIn("No state transfer", content)
        self.assertIn("constant displacement increment", content.lower())

    def test_coarse_benchmark_retest_summary(self):
        """Coarse benchmark Job 1411104 summary must verify Exit 0, d_max=1.000, F_max=514.51 N."""
        sum_path = os.path.join(self.data_dir, "MODE2_J1_COARSE_RETEST_SUMMARY.json")
        self.assertTrue(os.path.exists(sum_path), f"Missing coarse summary JSON: {sum_path}")
        with open(sum_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data.get("job_name"), "M2_J1_COARSE_RETEST")
        self.assertEqual(data.get("element_count"), 2960)
        self.assertAlmostEqual(data.get("f_max_N", 0.0), 514.51, places=1)
        self.assertAlmostEqual(data.get("final_dmax", 0.0), 1.000, places=3)
        self.assertAlmostEqual(data.get("k0_kN_per_mm", 0.0), 45.80, places=1)
        self.assertAlmostEqual(data.get("chord_angle_deg", 0.0), -57.95, places=1)

    def test_live_adapted_retest_telemetry(self):
        """Live adapted retest Job 1411103 telemetry must confirm active progress, softening, and d_max > 0.15."""
        sum_path = os.path.join(self.data_dir, "MODE2_J2_ADAPTED_RETEST_LIVE_SUMMARY.json")
        self.assertTrue(os.path.exists(sum_path), f"Missing live summary JSON: {sum_path}")
        with open(sum_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data.get("job_id"), "1411103.mmaster02")
        self.assertEqual(data.get("mesh_fe_count"), 22530)
        self.assertGreater(data.get("total_increments_completed", 0), 1400)
        self.assertGreater(data.get("current_ux_um", 0.0), 7.0)
        self.assertGreater(data.get("current_rf_N", 0.0), 300.0)
        self.assertGreater(data.get("latest_d_max", 0.0), 0.15)
        # Verify tangent softening
        k0 = data.get("k0_initial_stiffness_kN_mm", 45.68)
        k_tan = data.get("tangent_k_kN_mm", 45.68)
        self.assertLess(k_tan, k0, "Tangent stiffness must soften relative to K0!")

    def test_job_provenance_report_exists(self):
        """Gate M2-4 solver verification and provenance report must exist and contain complete job matrix."""
        report_path = os.path.join(self.root_dir, "docs", "mode2", "MODE2_M2_4_SOLVER_VERIFICATION_AND_PROVENANCE_REPORT.md")
        self.assertTrue(os.path.exists(report_path), f"Missing Gate M2-4 report: {report_path}")
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("1410790.mmaster02", content)
        self.assertIn("1410797.mmaster02", content)
        self.assertIn("1410807.mmaster02", content)
        self.assertIn("1411104.mmaster02", content)
        self.assertIn("1411103.mmaster02", content)
        self.assertIn("COARSE_BENCHMARK_PASSED__ADAPTED_RETEST_RUNNING", content)

if __name__ == "__main__":
    unittest.main()

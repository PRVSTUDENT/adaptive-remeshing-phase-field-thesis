# -*- coding: utf-8 -*-
"""
Unit tests for Gate-6B Stage 5: Step and Frame Semantics of adaptiveRemesh.
Verifies multi-frame ODB audit metrics, linear scaling invariance,
native CAE sensitivity results, and artifact presence.
"""

import os
import json
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class TestStage5StepFrameSemantics(unittest.TestCase):

    def setUp(self):
        self.stage5_data_dir = os.path.join(
            PROJECT_ROOT,
            "models", "pandey_kumar_mode1",
            "90_mode1_preanalysis_continuum_matched_2906",
            "stage5_extracted_frames"
        )
        self.figures_dir = os.path.join(PROJECT_ROOT, "results", "figures", "mode1_gate6b")
        self.report_md = os.path.join(
            PROJECT_ROOT, "models", "pandey_kumar_mode1",
            "MODE1_STAGE5_STEP_FRAME_SEMANTICS_REPORT.md"
        )
        self.report_json = os.path.join(
            PROJECT_ROOT, "models", "pandey_kumar_mode1",
            "MODE1_STAGE5_STEP_FRAME_SEMANTICS_REPORT.json"
        )

    def test_audit_json_metrics(self):
        audit_path = os.path.join(self.stage5_data_dir, "STAGE5_STEP_FRAME_SEMANTICS_AUDIT.json")
        self.assertTrue(os.path.exists(audit_path), "Audit JSON must exist")
        with open(audit_path, "r") as f:
            data = json.load(f)

        self.assertEqual(data["total_elements"], 2906)
        self.assertEqual(data["total_nodes"], 2989)
        self.assertEqual(data["step_inventory"]["Step-1"]["total_frames"], 501)
        self.assertEqual(data["step_inventory"]["Step-2"]["total_frames"], 1001)

        # Check linear scaling and invariance against Step-2 End
        comp = data["pairwise_comparisons"]["Step2_End_u01000_vs_Step1_End"]
        self.assertTrue(comp["is_exact_linear_scale"])
        self.assertAlmostEqual(comp["scaling_ratio_max"], 2.0, places=5)
        self.assertLess(comp["max_normalized_difference"], 1e-7)

        # Check regional shares on Step1_End_u00500 frame
        fe = data["frame_evaluations"]["Step1_End_u00500"]
        self.assertAlmostEqual(fe["miseseri_max"], 0.950009, places=4)
        self.assertAlmostEqual(fe["corridor_share"], 0.243457, places=4)
        self.assertAlmostEqual(fe["far_field_share"], 0.655663, places=4)

    def test_native_remesh_sensitivity_results(self):
        res_path = os.path.join(self.stage5_data_dir, "STAGE5_NATIVE_REMESH_SENSITIVITY_RESULTS.json")
        self.assertTrue(os.path.exists(res_path), "Native remesh sensitivity JSON must exist")
        with open(res_path, "r") as f:
            data = json.load(f)

        self.assertIn("remesh_step1_target1pct", data)
        self.assertIn("remesh_step2_target1pct", data)
        self.assertIn("remesh_step1_target2pct", data)
        self.assertIn("remesh_step2_target2pct", data)
        self.assertIn("remesh_step1_target5pct", data)
        self.assertIn("remesh_step2_target5pct", data)

        # 1% target parity (< 0.5% diff)
        n1 = data["remesh_step1_target1pct"]["remeshed_elements"]
        n2 = data["remesh_step2_target1pct"]["remeshed_elements"]
        delta_1pct = abs(n1 - n2) / float(n1) * 100.0
        self.assertLess(delta_1pct, 0.5, "1% target step1 vs step2 diff must be < 0.5%")

        # 2% target parity (< 0.5% diff)
        n1_2 = data["remesh_step1_target2pct"]["remeshed_elements"]
        n2_2 = data["remesh_step2_target2pct"]["remeshed_elements"]
        delta_2pct = abs(n1_2 - n2_2) / float(n1_2) * 100.0
        self.assertLess(delta_2pct, 0.5, "2% target step1 vs step2 diff must be < 0.5%")

    def test_reports_and_verdict(self):
        self.assertTrue(os.path.exists(self.report_md), "Markdown report must exist")
        self.assertTrue(os.path.exists(self.report_json), "JSON report must exist")

        with open(self.report_json, "r") as f:
            rep = json.load(f)

        self.assertEqual(rep["stage5_verdict"], "FRAME_SELECTION_VERIFIED_NOT_DOMINANT_CAUSE")
        self.assertEqual(rep["directional_classification"], "NO_MEANINGFUL_IMPROVEMENT")

    def test_publication_figures_exist(self):
        expected_figs = [
            "fig_stage5_miseseri_multiframe_spatial.pdf",
            "fig_stage5_miseseri_multiframe_spatial.png",
            "fig_stage5_normalized_footprint_invariance.pdf",
            "fig_stage5_normalized_footprint_invariance.png",
            "fig_stage5_regional_share_invariance.pdf",
            "fig_stage5_regional_share_invariance.png",
            "fig_stage5_native_remesh_comparison.pdf",
            "fig_stage5_native_remesh_comparison.png"
        ]
        for fname in expected_figs:
            fpath = os.path.join(self.figures_dir, fname)
            self.assertTrue(os.path.exists(fpath), "Figure must exist: " + fname)
            self.assertGreater(os.path.getsize(fpath), 1000, "Figure size must be > 1KB")


if __name__ == "__main__":
    unittest.main()

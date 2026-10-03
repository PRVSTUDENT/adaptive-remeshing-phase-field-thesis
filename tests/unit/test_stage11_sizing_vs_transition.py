# -*- coding: utf-8 -*-
"""
Unit tests for Gate-6B Stage 11: Native Sizing-Demand vs Mesh-Transition Propagation Audit.
"""
import unittest
import os
import json
import pandas as pd

class TestStage11SizingVsTransition(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        cls.report_md = os.path.join(cls.root_dir, "models", "pandey_kumar_mode1", "MODE1_STAGE11_SIZING_VS_TRANSITION_REPORT.md")
        cls.report_json = os.path.join(cls.root_dir, "models", "pandey_kumar_mode1", "MODE1_STAGE11_SIZING_VS_TRANSITION_REPORT.json")
        cls.mapping_csv = os.path.join(cls.root_dir, "models", "pandey_kumar_mode1", "MODE1_STAGE11_COARSE_TO_ADAPTED_MAPPING.csv")
        cls.transect_csv = os.path.join(cls.root_dir, "models", "pandey_kumar_mode1", "MODE1_STAGE11_TRANSECT_DATA.csv")
        cls.diag_summary = os.path.join(cls.root_dir, "models", "pandey_kumar_mode1", "97_mode1_stage11_min_transition_diagnostic", "STAGE11_MINTRANS_OFF_SUMMARY.json")
        cls.lineage_json = os.path.join(cls.root_dir, "models", "pandey_kumar_mode1", "MODE1_1PCT_LINEAGE_RECONCILIATION.json")
        
        if os.path.exists(cls.report_json):
            with open(cls.report_json, "r") as f:
                cls.data = json.load(f)
        else:
            cls.data = None
            
        if os.path.exists(cls.mapping_csv):
            cls.df_map = pd.read_csv(cls.mapping_csv)
        else:
            cls.df_map = None
            
        if os.path.exists(cls.transect_csv):
            cls.df_trans = pd.read_csv(cls.transect_csv)
        else:
            cls.df_trans = None

    def test_01_report_artifacts_exist(self):
        self.assertTrue(os.path.exists(self.report_md), "MODE1_STAGE11_SIZING_VS_TRANSITION_REPORT.md must exist")
        self.assertTrue(os.path.exists(self.report_json), "MODE1_STAGE11_SIZING_VS_TRANSITION_REPORT.json must exist")
        self.assertTrue(os.path.exists(self.mapping_csv), "MODE1_STAGE11_COARSE_TO_ADAPTED_MAPPING.csv must exist")
        self.assertTrue(os.path.exists(self.transect_csv), "MODE1_STAGE11_TRANSECT_DATA.csv must exist")
        self.assertTrue(os.path.exists(self.diag_summary), "STAGE11_MINTRANS_OFF_SUMMARY.json must exist")
        self.assertTrue(os.path.exists(self.lineage_json), "MODE1_1PCT_LINEAGE_RECONCILIATION.json must exist")

    def test_02_causal_verdict_and_diagnostic(self):
        self.assertIsNotNone(self.data)
        self.assertEqual(self.data['audit_id'], "GATE6B-STAGE11-SIZING-VS-TRANSITION-AUDIT-20261003")
        self.assertEqual(self.data['causal_verdict'], "BROADNESS_PRIMARILY_PRESENT_IN_NATIVE_SIZING_DEMAND")
        self.assertEqual(self.data['diagnostic_classification'], "MESH_CONTROL_NO_MEANINGFUL_IMPROVEMENT")

    def test_03_lineage_reconciliation_integrity(self):
        self.assertIsNotNone(self.data)
        lineage = self.data['lineage_reconciliation_summary']
        self.assertIn('lineage_4b_package90_matched_control_56k', lineage)
        self.assertIn('lineage_5_package93_inf_companion_58k', lineage)
        p90 = lineage['lineage_4b_package90_matched_control_56k']
        p93 = lineage['lineage_5_package93_inf_companion_58k']
        self.assertEqual(p90['elements'], 56344)
        self.assertEqual(p93['elements'], 57929)

    def test_04_mapping_csv_and_transect_coverage(self):
        self.assertIsNotNone(self.df_map)
        self.assertEqual(len(self.df_map), 2906, "Mapping CSV must contain exactly 2,906 coarse element rows")
        self.assertTrue((self.df_map['h_median_p93_mm'] > 0.0).all())
        
        self.assertIsNotNone(self.df_trans)
        # Check that all 6 transect lines are present
        h_vals = set(self.df_trans[self.df_trans['transect_type'] == 'HORIZONTAL']['transect_value'])
        v_vals = set(self.df_trans[self.df_trans['transect_type'] == 'VERTICAL']['transect_value'])
        self.assertEqual(h_vals, {0.50, 0.55, 0.60})
        self.assertEqual(v_vals, {0.50, 0.65, 0.80})

    def test_05_figures_exist_and_non_empty(self):
        fig_dir = os.path.join(self.root_dir, "results", "figures", "mode1_gate6b")
        for i in range(1, 5):
            png = os.path.join(fig_dir, f"mode1_stage11_fig{i}_*.png")
            import glob
            matches_png = glob.glob(os.path.join(fig_dir, f"mode1_stage11_fig{i}_*.png"))
            matches_pdf = glob.glob(os.path.join(fig_dir, f"mode1_stage11_fig{i}_*.pdf"))
            self.assertTrue(len(matches_png) > 0, f"Fig {i} PNG must exist")
            self.assertTrue(len(matches_pdf) > 0, f"Fig {i} PDF must exist")
            self.assertGreater(os.path.getsize(matches_png[0]), 10000, f"Fig {i} PNG must be non-empty")
            self.assertGreater(os.path.getsize(matches_pdf[0]), 10000, f"Fig {i} PDF must be non-empty")

if __name__ == '__main__':
    unittest.main()

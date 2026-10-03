# -*- coding: utf-8 -*-
"""
Unit tests for Gate-6B Stage 10: Native 1% Adaptive Remeshing of Package-93 Infinitesimal Companion ODB.
"""
import unittest
import os
import json
import pandas as pd

class TestStage10InfCompanionRemesh(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        cls.stage10_dir = os.path.join(cls.root_dir, "models", "pandey_kumar_mode1", "95_mode1_stage10_inf_companion_remesh")
        cls.summary_path = os.path.join(cls.stage10_dir, "STAGE10_INF_COMPANION_REMESH_SUMMARY.json")
        cls.report_json_path = os.path.join(cls.root_dir, "models", "pandey_kumar_mode1", "MODE1_STAGE10_INF_COMPANION_REMESH_REPORT.json")
        cls.csv_path = os.path.join(cls.stage10_dir, "stage10_adapted_elements.csv")
        
        # Load summary if present
        if os.path.exists(cls.summary_path):
            with open(cls.summary_path, "r") as f:
                cls.summary = json.load(f)
        else:
            cls.summary = None
            
        if os.path.exists(cls.report_json_path):
            with open(cls.report_json_path, "r") as f:
                cls.report_json = json.load(f)
        else:
            cls.report_json = None
            
        if os.path.exists(cls.csv_path):
            cls.df = pd.read_csv(cls.csv_path)
        else:
            cls.df = None

    def test_01_summary_structure_and_sizing_contract(self):
        self.assertIsNotNone(self.summary, "STAGE10_INF_COMPANION_REMESH_SUMMARY.json must exist")
        self.assertEqual(self.summary['audit_id'], "GATE6B-STAGE10-INF-COMPANION-NATIVE-REMESH-20261003")
        self.assertEqual(self.summary['status'], "STAGE10_INF_COMPANION_NATIVE_REMESH_COMPLETED")
        
        # Sizing contract
        contract = self.summary['sizing_contract']
        self.assertEqual(contract['error_target_pct'], 1.0)
        self.assertEqual(contract['sizing_method'], 'UNIFORM_ERROR')
        self.assertEqual(contract['refinement_factor'], 10)
        self.assertEqual(contract['coarsening_factor'], 'NOT_ALLOWED')
        self.assertEqual(contract['min_element_size_mm'], 0.001)
        self.assertEqual(contract['max_element_size_mm'], 0.020)

    def test_02_adapted_mesh_metrics(self):
        self.assertIsNotNone(self.summary)
        adapted = self.summary['adapted_mesh']
        self.assertGreater(adapted['total_elements'], 20000, "Adapted mesh should contain >20,000 elements for 1.0% errorTarget")
        self.assertGreater(adapted['total_nodes'], 20000)
        
        # Sizing bounds
        stats = adapted['h_eq_stats']
        self.assertGreaterEqual(stats['min'], 0.0005, "Minimum element size should be bounded (allowing triangle geometric factor)")
        self.assertLessEqual(stats['max'], 0.025, "Maximum element size should be near 0.020 mm")

    def test_03_spatial_morphology_and_far_field_refinement(self):
        self.assertIsNotNone(self.summary)
        morphology = self.summary['spatial_morphology']
        
        # Broad far field refinement
        self.assertGreater(morphology['far_field_fraction'], 0.50, "Far field fraction should exceed 50% under uniform sizing")
        self.assertGreater(morphology['crack_corridor_count'], 5000)
        self.assertGreater(morphology['far_field_total_count'], 10000)
        
        # Wake vs ligament counts
        self.assertGreater(morphology['wake_count'], 0)
        self.assertGreater(morphology['ligament_count'], 0)

    def test_04_adapted_elements_csv_integrity(self):
        self.assertIsNotNone(self.df, "stage10_adapted_elements.csv must exist")
        self.assertEqual(len(self.df), self.summary['adapted_mesh']['total_elements'])
        
        # Coordinates within domain [0, 1] x [0, 1]
        self.assertGreaterEqual(self.df['cx'].min(), 0.0)
        self.assertLessEqual(self.df['cx'].max(), 1.0)
        self.assertGreaterEqual(self.df['cy'].min(), 0.0)
        self.assertLessEqual(self.df['cy'].max(), 1.0)
        
        # Area strictly positive
        self.assertTrue((self.df['area'] > 0.0).all(), "All element areas must be strictly positive")
        self.assertTrue((self.df['aspect_ratio'] >= 1.0).all(), "Aspect ratio must be >= 1.0")

    def test_05_directional_verdict(self):
        self.assertIsNotNone(self.report_json, "MODE1_STAGE10_INF_COMPANION_REMESH_REPORT.json must exist")
        verdict = self.report_json['verdict']
        valid_verdicts = [
            'INF_COMPANION_NATIVE_REMESH_NO_MEANINGFUL_IMPROVEMENT',
            'INF_COMPANION_NATIVE_REMESH_TOWARD_TARGET_LOCALIZATION'
        ]
        self.assertIn(verdict, valid_verdicts)

if __name__ == '__main__':
    unittest.main()

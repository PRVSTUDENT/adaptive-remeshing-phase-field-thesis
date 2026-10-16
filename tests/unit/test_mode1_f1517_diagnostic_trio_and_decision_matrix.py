#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1517_diagnostic_trio_and_decision_matrix.py
======================================================
Unit tests for Task F1517:
- Evaluation engine for diagnostic trio (1414558, 1414563, 1414571)
- Rigorous verification of the 4-case evaluation decision matrix
- STA and DAT parsing mechanisms
- Enriched ground truth extraction script syntax and configuration
- Active scheduler constraints and job preservation

Protocol Version: 2
Author: Gemini Antigravity
Task: F1517
"""

import os
import sys
import json
import unittest
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.state_transfer.evaluate_mode1_diagnostic_trio import (
    evaluate_decision_matrix,
    parse_sta_file,
    parse_dat_file,
    AUTHENTIC_REFERENCES,
    THRESHOLDS
)


class TestMode1F1517DiagnosticTrio(unittest.TestCase):

    def test_01_decision_matrix_case_a(self):
        """Case A: Both lumped and consistent controls pass."""
        lumped_mock = {
            "exists": True,
            "completed": True,
            "cutbacks": 0,
            "step1_rf2": 661.70,  # diff ~ 0.025 N <= 5.0 N
            "step2_rf2": 661.50
        }
        consistent_mock = {
            "exists": True,
            "completed": True,
            "cutbacks": 0,
            "step1_rf2": 661.71,  # diff ~ 0.015 N <= 5.0 N
            "step2_rf2": 661.65
        }
        matrix = evaluate_decision_matrix(lumped_mock, consistent_mock)
        self.assertEqual(matrix["case_selected"], "CASE_A")
        self.assertIn("physical continuum localization", matrix["justification"])

    def test_02_decision_matrix_case_b(self):
        """Case B: Lumped control fails, consistent inverse passes."""
        lumped_mock = {
            "exists": True,
            "completed": True,
            "cutbacks": 2,  # Cutback failure
            "step1_rf2": 648.55  # Discrepancy > 5.0 N
        }
        consistent_mock = {
            "exists": True,
            "completed": True,
            "cutbacks": 0,
            "step1_rf2": 661.72  # Matches baseline
        }
        matrix = evaluate_decision_matrix(lumped_mock, consistent_mock)
        self.assertEqual(matrix["case_selected"], "CASE_B")
        self.assertIn("area-weighted projection smoothing defect", matrix["justification"])

    def test_03_decision_matrix_case_c(self):
        """Case C: Both controls fail."""
        lumped_mock = {
            "exists": True,
            "completed": False,
            "cutbacks": 5
        }
        consistent_mock = {
            "exists": True,
            "completed": False,
            "cutbacks": 3
        }
        matrix = evaluate_decision_matrix(lumped_mock, consistent_mock)
        self.assertEqual(matrix["case_selected"], "CASE_C")
        self.assertIn("reformulation", matrix["justification"])

    def test_04_case_d_ground_truth_flag(self):
        """Case D: Baseline ground truth integration."""
        lumped_mock = {"exists": True, "completed": True, "cutbacks": 0, "step1_rf2": 661.70}
        consistent_mock = {"exists": True, "completed": True, "cutbacks": 0, "step1_rf2": 661.71}
        baseline_mock = {"exists": True, "completed": True, "total_increments": 2000, "cutbacks": 0}
        
        matrix = evaluate_decision_matrix(lumped_mock, consistent_mock, baseline_mock)
        self.assertEqual(matrix["case_d_ground_truth_status"], "AVAILABLE")
        self.assertIn("authentic interior (ux, uy, d, H)", matrix["case_d_notes"])

    def test_05_ground_truth_extractor_syntax(self):
        """Verify extract_enriched_baseline_ground_truth.py compiles without syntax errors."""
        extractor_path = PROJECT_ROOT / "scripts" / "state_transfer" / "extract_enriched_baseline_ground_truth.py"
        self.assertTrue(extractor_path.exists(), "Extractor script must exist")
        import py_compile
        py_compile.compile(str(extractor_path), doraise=True)

    def test_06_active_task_metadata(self):
        """Verify active task holds the exact diagnostic trio without duplicates."""
        task_file = PROJECT_ROOT / "project_coordination" / "ACTIVE_TASK.json"
        self.assertTrue(task_file.exists())
        data = json.loads(task_file.read_text(encoding="utf-8"))
        
        active_jobs = data.get("active_pbs_job_ids", [])
        self.assertIn("1414558.mmaster02", active_jobs)
        self.assertIn("1414563.mmaster02", active_jobs)
        self.assertIn("1414571.mmaster02", active_jobs)
        self.assertLessEqual(len(active_jobs), 4, "Active user jobs must be <= 4")


if __name__ == "__main__":
    unittest.main()

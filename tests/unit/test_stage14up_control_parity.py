#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
test_stage14up_control_parity.py
--------------------------------
Unit test suite for Gate-6B Mode-I Stage 14U-P:
Completion-Run Control-Parity and Prior-Failure-Crossing Audit.
Supports both unittest and pytest test runners.
"""
import os
import json
import csv
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PKG25_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "25_stage14_adaptive_candidate_14k")
FIG_DIR = os.path.join(REPO_ROOT, "results", "figures", "mode1_gate6b")

class TestStage14UPControlParity(unittest.TestCase):

    def test_01_predecessor_data_integrity(self):
        """Verify predecessor Job 1409953 data files exist and have valid baseline properties."""
        fu_path = os.path.join(PKG25_DIR, "PK_MODE1_STAGE14_ADAPT_14K_FRACTURE_fu.csv")
        energy_path = os.path.join(PKG25_DIR, "uel_energy_balance.csv")
        
        self.assertTrue(os.path.exists(fu_path), "Predecessor fu.csv must exist")
        self.assertTrue(os.path.exists(energy_path), "Predecessor energy csv must exist")
        
        with open(fu_path, 'r', encoding='utf-8-sig') as f:
            reader = list(csv.reader(f))
            self.assertTrue(len(reader) > 4800, f"Expected >4800 rows in fu.csv, got {len(reader)}")
            last_row = reader[-1]
            u_final = float(last_row[5])
            self.assertAlmostEqual(u_final, 0.007889, places=4)

    def test_02_active_run_snapshot_integrity(self):
        """Verify live snapshot of active rerun 1409982 is present and valid."""
        snap_json_path = os.path.join(PKG25_DIR, "stage14up_live_snapshot.json")
        snap_csv_path = os.path.join(PKG25_DIR, "stage14up_live_snapshot.csv")
        
        self.assertTrue(os.path.exists(snap_json_path), "Live snapshot JSON must exist")
        self.assertTrue(os.path.exists(snap_csv_path), "Live snapshot CSV must exist")
        
        with open(snap_json_path, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
            self.assertEqual(data["job_id"], "1409982.mmaster02")
            self.assertTrue(data["total_records"] > 0)
            self.assertEqual(data["latest_step"], 1)
            self.assertTrue(data["latest_u_mm"] > 0.0)
            self.assertTrue(data["latest_u_mm"] < 0.007889, "Snapshot must be in pre-failure regime")

    def test_03_deterministic_force_parity(self):
        """Verify bit-for-bit / high-precision force parity between predecessor and rerun."""
        report_json_path = os.path.join(PKG25_DIR, "MODE1_STAGE14UP_CONTROL_PARITY_AND_FAILURE_CROSSING_REPORT.json")
        self.assertTrue(os.path.exists(report_json_path), "Parity report JSON must exist")
        
        with open(report_json_path, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
            
        metrics = data["parity_audit_metrics"]
        self.assertEqual(metrics["parity_verdict"], "COMPLETION_CONTROL_PARITY_CONFIRMED_OVER_REACHED_RANGE")
        self.assertTrue(metrics["common_increments_evaluated"] >= 200)
        self.assertTrue(metrics["max_absolute_force_difference_kN"] < 1.0e-7, "Max force diff must be < 1e-7 kN (text rounding limit)")
        self.assertTrue(metrics["max_relative_force_difference_pct"] < 0.01, "Max relative force error must be < 0.01%")
        self.assertTrue(metrics["rms_force_difference_kN"] < 1.0e-8)

    def test_04_energy_parity(self):
        """Verify elastic strain energy and fracture functional parity across common window."""
        report_json_path = os.path.join(PKG25_DIR, "MODE1_STAGE14UP_CONTROL_PARITY_AND_FAILURE_CROSSING_REPORT.json")
        with open(report_json_path, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
            
        metrics = data["parity_audit_metrics"]
        self.assertTrue(metrics["max_absolute_elastic_energy_difference_mJ"] < 1.0e-8)
        self.assertTrue(metrics["max_absolute_fracture_energy_difference_mJ"] < 1.0e-8)

    def test_05_failure_crossing_classification(self):
        """Verify proper classification of failure-crossing status."""
        report_json_path = os.path.join(PKG25_DIR, "MODE1_STAGE14UP_CONTROL_PARITY_AND_FAILURE_CROSSING_REPORT.json")
        with open(report_json_path, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
            
        crossing = data["failure_crossing_audit"]
        self.assertEqual(crossing["crossing_status"], "PRE_FAILURE_CONTROL_PARITY_EVALUATED__FAILURE_CROSSING_PENDING")
        self.assertEqual(crossing["crossing_verdict"], "SOLVER_ACTIVELY_ADVANCING_IN_PRE_FAILURE_REGIME")
        self.assertTrue(crossing["current_displacement_mm"] < crossing["prior_failure_displacement_mm"])

    def test_06_figures_exist(self):
        """Verify that Stage 14U-P parity and discrepancy figures were generated."""
        overlay_png = os.path.join(FIG_DIR, "fig_mode1_stage14up_parity_overlay.png")
        overlay_pdf = os.path.join(FIG_DIR, "fig_mode1_stage14up_parity_overlay.pdf")
        discrepancy_png = os.path.join(FIG_DIR, "fig_mode1_stage14up_discrepancy.png")
        discrepancy_pdf = os.path.join(FIG_DIR, "fig_mode1_stage14up_discrepancy.pdf")
        
        self.assertTrue(os.path.exists(overlay_png), "Overlay PNG must exist")
        self.assertTrue(os.path.exists(overlay_pdf), "Overlay PDF must exist")
        self.assertTrue(os.path.exists(discrepancy_png), "Discrepancy PNG must exist")
        self.assertTrue(os.path.exists(discrepancy_pdf), "Discrepancy PDF must exist")
        self.assertTrue(os.path.getsize(overlay_png) > 10000)
        self.assertTrue(os.path.getsize(discrepancy_png) > 10000)

if __name__ == '__main__':
    unittest.main()

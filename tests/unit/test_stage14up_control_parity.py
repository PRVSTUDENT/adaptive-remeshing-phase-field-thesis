#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
test_stage14up_control_parity.py
--------------------------------
Unit test suite for Gate-6B Mode-I Stage 14U-P:
Completion-Run Control-Parity and Prior-Failure-Crossing Audit.
"""
import os
import json
import csv
import pytest
import math

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PKG25_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "25_stage14_adaptive_candidate_14k")
FIG_DIR = os.path.join(REPO_ROOT, "results", "figures", "mode1_gate6b")

def test_stage14up_predecessor_data_integrity():
    """Verify predecessor Job 1409953 data files exist and have valid baseline properties."""
    fu_path = os.path.join(PKG25_DIR, "PK_MODE1_STAGE14_ADAPT_14K_FRACTURE_fu.csv")
    energy_path = os.path.join(PKG25_DIR, "uel_energy_balance.csv")
    
    assert os.path.exists(fu_path), "Predecessor fu.csv must exist"
    assert os.path.exists(energy_path), "Predecessor energy csv must exist"
    
    with open(fu_path, 'r') as f:
        reader = list(csv.reader(f))
        assert len(reader) > 4800, f"Expected >4800 rows in fu.csv, got {len(reader)}"
        last_row = reader[-1]
        u_final = float(last_row[5])
        assert abs(u_final - 0.007889) < 1e-4, f"Expected terminal u ~ 0.007889 mm, got {u_final}"

def test_stage14up_active_run_snapshot_integrity():
    """Verify live snapshot of active rerun 1409982 is present and valid."""
    snap_json_path = os.path.join(PKG25_DIR, "stage14up_live_snapshot.json")
    snap_csv_path = os.path.join(PKG25_DIR, "stage14up_live_snapshot.csv")
    
    assert os.path.exists(snap_json_path), "Live snapshot JSON must exist"
    assert os.path.exists(snap_csv_path), "Live snapshot CSV must exist"
    
    with open(snap_json_path, 'r') as f:
        data = json.load(f)
        assert data["job_id"] == "1409982.mmaster02"
        assert data["total_records"] > 0
        assert data["latest_step"] == 1
        assert data["latest_u_mm"] > 0.0
        assert data["latest_u_mm"] < 0.007889, "Snapshot must be in pre-failure regime"

def test_stage14up_deterministic_force_parity():
    """Verify bit-for-bit / high-precision force parity between predecessor and rerun."""
    report_json_path = os.path.join(PKG25_DIR, "MODE1_STAGE14UP_CONTROL_PARITY_AND_FAILURE_CROSSING_REPORT.json")
    assert os.path.exists(report_json_path), "Parity report JSON must exist"
    
    with open(report_json_path, 'r') as f:
        data = json.load(f)
        
    metrics = data["parity_audit_metrics"]
    assert metrics["parity_verdict"] == "DETERMINISTIC_CONTROL_PARITY_VERIFIED"
    assert metrics["common_increments_evaluated"] >= 200
    assert metrics["max_absolute_force_difference_kN"] < 1.0e-7, "Max force diff must be < 1e-7 kN (text rounding limit)"
    assert metrics["max_relative_force_difference_pct"] < 0.01, "Max relative force error must be < 0.01%"
    assert metrics["rms_force_difference_kN"] < 1.0e-8

def test_stage14up_energy_parity():
    """Verify elastic strain energy and fracture functional parity across common window."""
    report_json_path = os.path.join(PKG25_DIR, "MODE1_STAGE14UP_CONTROL_PARITY_AND_FAILURE_CROSSING_REPORT.json")
    with open(report_json_path, 'r') as f:
        data = json.load(f)
        
    metrics = data["parity_audit_metrics"]
    assert metrics["max_absolute_elastic_energy_difference_mJ"] < 1.0e-8
    assert metrics["max_absolute_fracture_energy_difference_mJ"] < 1.0e-8

def test_stage14up_failure_crossing_classification():
    """Verify proper classification of failure-crossing status."""
    report_json_path = os.path.join(PKG25_DIR, "MODE1_STAGE14UP_CONTROL_PARITY_AND_FAILURE_CROSSING_REPORT.json")
    with open(report_json_path, 'r') as f:
        data = json.load(f)
        
    crossing = data["failure_crossing_audit"]
    assert crossing["crossing_status"] == "PRE_FAILURE_CONTROL_PARITY_EVALUATED__FAILURE_CROSSING_PENDING"
    assert crossing["crossing_verdict"] == "SOLVER_ACTIVELY_ADVANCING_IN_PRE_FAILURE_REGIME"
    assert crossing["current_displacement_mm"] < crossing["prior_failure_displacement_mm"]

def test_stage14up_figures_exist():
    """Verify that Stage 14U-P parity and discrepancy figures were generated."""
    overlay_png = os.path.join(FIG_DIR, "fig_mode1_stage14up_parity_overlay.png")
    overlay_pdf = os.path.join(FIG_DIR, "fig_mode1_stage14up_parity_overlay.pdf")
    discrepancy_png = os.path.join(FIG_DIR, "fig_mode1_stage14up_discrepancy.png")
    discrepancy_pdf = os.path.join(FIG_DIR, "fig_mode1_stage14up_discrepancy.pdf")
    
    assert os.path.exists(overlay_png), "Overlay PNG must exist"
    assert os.path.exists(overlay_pdf), "Overlay PDF must exist"
    assert os.path.exists(discrepancy_png), "Discrepancy PNG must exist"
    assert os.path.exists(discrepancy_pdf), "Discrepancy PDF must exist"
    assert os.path.getsize(overlay_png) > 10000
    assert os.path.getsize(discrepancy_png) > 10000

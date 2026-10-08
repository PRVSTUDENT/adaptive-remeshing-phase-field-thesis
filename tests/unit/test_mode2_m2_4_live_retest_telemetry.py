# -*- coding: utf-8 -*-
"""
test_mode2_m2_4_live_retest_telemetry.py
Unit tests verifying live solver telemetry, stiffness metrics, and figure artifacts
for Mode-II Gate M2-4 adapted fracture retest (PBS Job 1411103.mmaster02, 22,530 FEs).
"""

import os
import json
import csv
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MODEL_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode2", "06_paper_grounded_uel_preanalysis")
FIGURES_DIR = os.path.join(REPO_ROOT, "results", "figures", "mode2")

def test_live_rf_csv_structure_and_monotonicity():
    csv_path = os.path.join(MODEL_DIR, "mode2_j2_adapted_retest_live_rf.csv")
    assert os.path.isfile(csv_path), "Live RF CSV does not exist: %s" % csv_path
    
    rows = []
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append((float(row["ux_mm"]), float(row["rf1_kN"]), float(row["rf1_N"])))
            
    assert len(rows) >= 1300, "Expected at least 1300 rows, got %d" % len(rows)
    
    # Check monotonicity of displacement
    ux_vals = [r[0] for r in rows]
    for i in range(1, len(ux_vals)):
        assert ux_vals[i] >= ux_vals[i-1], "Non-monotonic displacement at index %d" % i
        
    # Check that reaction force increases initially
    assert rows[100][1] > rows[10][1] > 0.0

def test_live_summary_json_integrity():
    json_path = os.path.join(MODEL_DIR, "MODE2_J2_ADAPTED_RETEST_LIVE_SUMMARY.json")
    assert os.path.isfile(json_path), "Live summary JSON does not exist: %s" % json_path
    
    with open(json_path, "r") as f:
        data = json.load(f)
        
    assert data["job_name"] == "M2_J2_ADAPT_RETEST"
    assert data["job_id"] == "1411103.mmaster02"
    assert data["mesh_fe_count"] == 22530
    assert data["mesh_node_count"] == 22642
    assert data["total_increments_completed"] >= 1300
    assert data["current_ux_um"] >= 6.5
    assert data["current_rf_N"] >= 290.0

def test_elastic_stiffness_accuracy():
    json_path = os.path.join(MODEL_DIR, "MODE2_J2_ADAPTED_RETEST_LIVE_SUMMARY.json")
    with open(json_path, "r") as f:
        data = json.load(f)
        
    k0 = data["k0_initial_stiffness_kN_mm"]
    # Reference coarse stiffness is 45.80 kN/mm, adapted is expected ~45.68 kN/mm
    assert 45.0 <= k0 <= 46.5, "Initial stiffness K0 out of expected physical range: %.4f" % k0
    assert abs(k0 - 45.6826) < 0.1

def test_stiffness_softening_onset():
    json_path = os.path.join(MODEL_DIR, "MODE2_J2_ADAPTED_RETEST_LIVE_SUMMARY.json")
    with open(json_path, "r") as f:
        data = json.load(f)
        
    k0 = data["k0_initial_stiffness_kN_mm"]
    sec_k = data["secant_k_kN_mm"]
    tan_k = data["tangent_k_kN_mm"]
    
    # Secant and tangent stiffness must indicate progressive softening
    assert sec_k < k0, "Secant stiffness %.4f should be less than K0 %.4f" % (sec_k, k0)
    assert tan_k < sec_k, "Tangent stiffness %.4f should be less than Secant K %.4f" % (tan_k, sec_k)
    assert data["tangent_k_pct_k0"] < 98.0

def test_publication_figures_exist():
    png_path = os.path.join(FIGURES_DIR, "fig_mode2_m2_4_adapted_retest_live_telemetry.png")
    pdf_path = os.path.join(FIGURES_DIR, "fig_mode2_m2_4_adapted_retest_live_telemetry.pdf")
    
    assert os.path.isfile(png_path), "PNG figure does not exist: %s" % png_path
    assert os.path.isfile(pdf_path), "PDF figure does not exist: %s" % pdf_path
    assert os.path.getsize(png_path) > 50000, "PNG figure size suspiciously small"
    assert os.path.getsize(pdf_path) > 10000, "PDF figure size suspiciously small"

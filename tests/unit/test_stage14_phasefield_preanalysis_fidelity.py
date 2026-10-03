# -*- coding: utf-8 -*-
"""
Unit tests for Gate-6B Stage 14: Phase-Field-Coupled Pre-Analysis / MISESERI-History Fidelity Audit.
Validates multi-state evolution data, native remeshing recovery of narrow corridor morphology,
element count parity with Pandey & Kumar (2025), reports, and publication figures.
"""
import os
import json
import hashlib
import pytest
import pandas as pd

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
STAGE14_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "99_mode1_stage14_phasefield_preanalysis_fidelity")
FIGURES_DIR = os.path.join(REPO_ROOT, "results", "figures", "mode1_gate6b")
SUMMARY_JSON = os.path.join(STAGE14_DIR, "STAGE14_EVOLUTION_AUDIT_SUMMARY.json")
REMESH_JSON = os.path.join(STAGE14_DIR, "STAGE14_NATIVE_REMESH_COMPARISON.json")
REPORT_MD = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "MODE1_STAGE14_PHASEFIELD_PREANALYSIS_REPORT.md")
REPORT_JSON = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "MODE1_STAGE14_PHASEFIELD_PREANALYSIS_REPORT.json")

def get_file_sha256(path):
    if not os.path.exists(path):
        return None
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

@pytest.fixture(scope="module")
def remesh_data():
    assert os.path.exists(REMESH_JSON), f"Remesh comparison JSON not found: {REMESH_JSON}"
    with open(REMESH_JSON, "r") as f:
        data = json.load(f)
    return data

@pytest.fixture(scope="module")
def report_data():
    assert os.path.exists(REPORT_JSON), f"Report JSON not found: {REPORT_JSON}"
    with open(REPORT_JSON, "r") as f:
        data = json.load(f)
    return data

def test_stage14_report_structure(report_data):
    """Verify top-level keys and governing verdict in Stage 14 report."""
    assert report_data["report_id"] == "MODE1_STAGE14_PHASEFIELD_PREANALYSIS_REPORT_20261003"
    assert report_data["governing_scientific_verdict"] == "PHASEFIELD_EVOLUTION_TOWARD_TARGET_MISESERI_LOCALIZATION"
    assert report_data["source_preanalysis_odb"]["coarse_mesh_elements"] == 2906
    assert report_data["source_preanalysis_odb"]["step1_displacement_mm"] == 0.005
    assert report_data["source_preanalysis_odb"]["step2_displacement_mm"] == 0.010

def test_stage14_state_csv_files_exist():
    """Verify all 8 state CSV files exist and have 2,906 rows."""
    states = [
        "state1_u0050_baseline",
        "state2_u0055_damage_onset",
        "state3_u00586_near_peak",
        "state4_u0061_postpeak_onset",
        "state5_u0066_propagation",
        "state6_u0080_extended_crack",
        "state7_u0098_late_propagation",
        "state8_u0100_final_rupture"
    ]
    for tag in states:
        csv_p = os.path.join(STAGE14_DIR, f"stage14_{tag}.csv")
        assert os.path.exists(csv_p), f"State CSV missing: {csv_p}"
        df = pd.read_csv(csv_p)
        assert len(df) == 2906
        assert set(df.columns) == {"label", "cx", "cy", "area", "h_eq", "d", "H", "miseseri", "norm_miseseri"}

def test_stage14_native_remesh_recovery(remesh_data):
    """Verify Step-2 native remesh recovers narrow horizontal corridor and ~14k elements."""
    step2_res = remesh_data["step2_all_inc"]
    
    # Element count matches published 13,941 within 5%
    assert 13000 <= step2_res["total_elements"] <= 16000
    assert abs(step2_res["total_elements"] - 13941) / 13941.0 < 0.05
    
    # Corridor fraction > 60% and far field < 40%
    assert step2_res["corridor_fraction"] >= 0.60
    assert step2_res["far_fraction"] <= 0.40
    
    # Coarse area fraction > 50%
    assert step2_res["coarse_remaining_area_fraction"] >= 0.50
    
    # Refined band width w(x) behavior
    bw = step2_res["band_widths_5um"]
    assert bw["0.1"]["width_mm"] == 0.0
    assert bw["0.2"]["width_mm"] == 0.0
    assert bw["0.3"]["width_mm"] == 0.0
    assert 0.15 <= bw["0.5"]["width_mm"] <= 0.30  # Tip band width
    assert 0.08 <= bw["0.7"]["width_mm"] <= 0.20  # Right ligament band width
    assert 0.05 <= bw["0.9"]["width_mm"] <= 0.15  # Near right edge

def test_stage14_reports_and_figures_exist():
    """Verify Stage 14 markdown/JSON reports and publication figures exist."""
    assert os.path.exists(REPORT_MD), f"Report MD missing: {REPORT_MD}"
    assert os.path.exists(REPORT_JSON), f"Report JSON missing: {REPORT_JSON}"
    
    figs = [
        "fig_mode1_stage14_phasefield_miseseri_evolution.png",
        "fig_mode1_stage14_phasefield_miseseri_evolution.pdf",
        "fig_mode1_stage14_adapted_mesh_comparison.png",
        "fig_mode1_stage14_adapted_mesh_comparison.pdf",
        "fig_mode1_stage14_corridor_transects.png",
        "fig_mode1_stage14_corridor_transects.pdf"
    ]
    for f in figs:
        fig_path = os.path.join(FIGURES_DIR, f)
        assert os.path.exists(fig_path), f"Figure missing: {fig_path}"

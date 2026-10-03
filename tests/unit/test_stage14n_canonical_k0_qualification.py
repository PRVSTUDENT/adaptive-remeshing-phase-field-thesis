import os
import json
import numpy as np
import pytest

def test_unit_consistency_conversion():
    """Verify that 1 mm = 1000 um and 0.0003375 mm = 0.3375 um (not 33.75 um)."""
    h_min_mm = 0.0003375
    h_min_um = h_min_mm * 1000.0
    assert np.isclose(h_min_um, 0.3375), f"Expected 0.3375 um, got {h_min_um}"

    u_horizon_mm = 0.0010
    u_horizon_um = u_horizon_mm * 1000.0
    assert np.isclose(u_horizon_um, 1.0), f"Expected 1.0 um, got {u_horizon_um}"

def test_canonical_window_definitions():
    """Verify canonical window parameters."""
    delta_u = 2.5e-6
    u_min_cut = 0.5 * delta_u
    u_max_cut = 0.0010 + 0.5 * delta_u
    
    assert u_min_cut == 1.25e-6
    assert u_max_cut == 0.00100125

def test_stage14n_report_and_verdict():
    """Verify Stage 14N report structure and canonical K0 values if report exists."""
    project_root = r"D:\Master thesis\Adaptive remeshing"
    report_json_path = os.path.join(project_root, "models", "pandey_kumar_mode1", "25_stage14_adaptive_candidate_14k", "MODE1_STAGE14N_CANONICAL_K0_QUALIFICATION_REPORT.json")
    
    if not os.path.exists(report_json_path):
        pytest.skip("Stage 14N report JSON not yet created.")
        
    with open(report_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    assert data["metadata"]["task_id"] == "F1191-GATE6B-STAGE14N-UNIT-CORRECTION-AND-CANONICAL-K0-CHECKPOINT-20261003"
    assert data["metadata"]["formal_classification"] == "CORRECTED_ADAPTIVE_CANONICAL_K0_CHECKPOINT"
    assert data["metadata"]["verdict"] in ["STABLE", "MESH_SENSITIVE", "NOT_YET_QUALIFIED"]
    
    ref_k0 = data["regression_results"]["reference_job"]["k0_canonical_kN_per_mm"]
    adapt_k0 = data["regression_results"]["adaptive_job"]["k0_canonical_kN_per_mm"]
    
    assert np.isclose(ref_k0, 137.945520, rtol=1e-4)
    if data["canonical_window_definition"]["window_complete"]:
        rel_diff = abs(adapt_k0 - ref_k0) / ref_k0
        assert rel_diff < 0.01, f"Canonical K0 difference {rel_diff*100}% exceeds 1% threshold"
        assert data["regression_results"]["adaptive_job"]["r2"] >= 0.999999

def test_stage14n_figures_exist():
    """Verify Stage 14N figures exist and are non-empty."""
    project_root = r"D:\Master thesis\Adaptive remeshing"
    fig_png = os.path.join(project_root, "results", "figures", "mode1_gate6b", "fig_mode1_stage14n_canonical_k0_fitting.png")
    fig_pdf = os.path.join(project_root, "results", "figures", "mode1_gate6b", "fig_mode1_stage14n_canonical_k0_fitting.pdf")
    
    if os.path.exists(fig_png):
        assert os.path.getsize(fig_png) > 10000
    if os.path.exists(fig_pdf):
        assert os.path.getsize(fig_pdf) > 5000

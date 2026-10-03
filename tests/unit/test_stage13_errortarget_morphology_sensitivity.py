# -*- coding: utf-8 -*-
"""
Unit tests for Gate-6B Stage 13: Literature-Supported errorTarget Morphology Sensitivity Diagnostic.
Validates sensitivity summary JSON, generated .inp decks, element CSVs, morphology metrics,
trend consistency, and publication-quality figures.
"""
import os
import json
import hashlib
import pytest
import pandas as pd

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
STAGE13_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "99_mode1_stage13_errortarget_morphology_sensitivity")
FIGURES_DIR = os.path.join(REPO_ROOT, "results", "figures", "mode1_gate6b")
SUMMARY_JSON = os.path.join(STAGE13_DIR, "STAGE13_ERRORTARGET_SENSITIVITY_SUMMARY.json")
REPORT_MD = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "MODE1_STAGE13_ERRORTARGET_MORPHOLOGY_REPORT.md")
REPORT_JSON = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "MODE1_STAGE13_ERRORTARGET_MORPHOLOGY_REPORT.json")

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
def summary_data():
    assert os.path.exists(SUMMARY_JSON), f"Summary JSON not found: {SUMMARY_JSON}"
    with open(SUMMARY_JSON, "r") as f:
        data = json.load(f)
    return data

def test_stage13_summary_structure(summary_data):
    """Verify top-level keys and fixed parameters in summary JSON."""
    assert summary_data["audit_id"] == "GATE6B-STAGE13-ERRORTARGET-MORPHOLOGY-SENSITIVITY-20261003"
    assert summary_data["active_phase"] == "MODE1_GATE6B_ACTIVE_EVALUATION_AND_CONTINUATION"
    
    fixed = summary_data["fixed_parameters"]
    assert fixed["coarse_mesh_elements"] == 2906
    assert fixed["sizing_method"] == "UNIFORM_ERROR"
    assert fixed["region"] == "ALL_ELEM"
    assert fixed["refinement_factor"] == 10
    assert fixed["coarsening_factor"] == "NOT_ALLOWED"
    assert fixed["min_element_size_mm"] == 0.001
    assert fixed["max_element_size_mm"] == 0.020
    
    allowed_conclusions = {
        "LITERATURE_INFORMED_ERRORTARGET_DOES_NOT_RESOLVE_TARGET_LOCALIZATION",
        "LITERATURE_SUPPORTED_ERRORTARGET_CAN_RECOVER_TARGET_LIKE_MORPHOLOGY",
        "LITERATURE_SUPPORTED_ERRORTARGET_IMPROVES_BUT_DOES_NOT_RECOVER_TARGET_MORPHOLOGY",
        "LITERATURE_SUPPORTED_ERRORTARGET_DOES_NOT_RESOLVE_LOCALIZATION"
    }
    assert summary_data["overall_stage13_conclusion"] in allowed_conclusions

def test_stage13_all_cases_exist_and_hashes_match(summary_data):
    """Verify all 4 errorTarget cases exist (inp, csv) and hashes match."""
    cases = ["et10", "et20", "et30", "et50"]
    assert set(summary_data["sensitivity_cases"].keys()) == set(cases)
    
    for k in cases:
        case = summary_data["sensitivity_cases"][k]
        deck_path = case["deck_path"]
        csv_path = case["csv_path"]
        
        assert os.path.exists(deck_path), f"Deck missing: {deck_path}"
        assert os.path.exists(csv_path), f"CSV missing: {csv_path}"
        
        assert get_file_sha256(deck_path) == case["deck_sha256"]
        assert get_file_sha256(csv_path) == case["csv_sha256"]
        
        # Verify CSV row count equals total elements
        df = pd.read_csv(csv_path)
        assert len(df) == case["total_elements"]
        assert set(df.columns) == {"label", "type", "cx", "cy", "area", "h_eq", "aspect_ratio"}

def test_stage13_morphology_metrics_validity(summary_data):
    """Verify element counts, fractions, and directional verdicts for each case."""
    allowed_verdicts = {
        "TOWARD_TARGET_LOCALIZATION",
        "NO_MEANINGFUL_IMPROVEMENT",
        "AWAY_FROM_TARGET_LOCALIZATION"
    }
    
    prev_elems = 1e9
    for k in ["et10", "et20", "et30", "et50"]:
        case = summary_data["sensitivity_cases"][k]
        assert case["total_elements"] > 0
        assert case["total_nodes"] > 0
        assert case["directional_verdict"] in allowed_verdicts
        
        # Check fractions sum to ~1.0
        assert abs(case["corridor_fraction"] + case["far_field_fraction"] - 1.0) < 1e-4
        assert abs(case["quad_fraction"] + case["tri_fraction"] - 1.0) < 1e-4
        
        # Monotonicity check: increasing errorTarget must reduce or equal element count
        assert case["total_elements"] <= prev_elems, f"Non-monotonic element count at {k}: {case['total_elements']} > {prev_elems}"
        prev_elems = case["total_elements"]
        
        # Crack tip min element size should stay near minElementSize (0.001 mm = 1.0 um)
        assert case["h_eq_stats_corridor"]["min_um"] <= 2.5, f"Crack tip not refined in {k}: min_um = {case['h_eq_stats_corridor']['min_um']}"

def test_stage13_reports_and_figures_exist():
    """Verify Stage 13 markdown/JSON reports and publication figures exist."""
    assert os.path.exists(REPORT_MD), f"Report MD missing: {REPORT_MD}"
    assert os.path.exists(REPORT_JSON), f"Report JSON missing: {REPORT_JSON}"
    
    figs = [
        "fig_mode1_stage13_errortarget_mesh_comparison.png",
        "fig_mode1_stage13_errortarget_mesh_comparison.pdf",
        "fig_mode1_stage13_crack_zoom_comparison.png",
        "fig_mode1_stage13_crack_zoom_comparison.pdf",
        "fig_mode1_stage13_sizing_transects.png",
        "fig_mode1_stage13_sizing_transects.pdf"
    ]
    for f in figs:
        fig_path = os.path.join(FIGURES_DIR, f)
        assert os.path.exists(fig_path), f"Figure missing: {fig_path}"

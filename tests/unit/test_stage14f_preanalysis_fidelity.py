"""
Unit tests for Gate-6B Stage 14F: Pandey-Kumar Job-1 Pre-Analysis Loading & Methodological-Fidelity Audit.
"""

import os
import json
import pytest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FIDELITY_REPORT_JSON = os.path.join(ROOT_DIR, "models", "pandey_kumar_mode1", "MODE1_STAGE14F_JOB1_PREANALYSIS_METHOD_FIDELITY_REPORT.json")
FIDELITY_REPORT_MD = os.path.join(ROOT_DIR, "models", "pandey_kumar_mode1", "MODE1_STAGE14F_JOB1_PREANALYSIS_METHOD_FIDELITY_REPORT.md")
FIGURES_DIR = os.path.join(ROOT_DIR, "results", "figures", "mode1_gate6b")

FIG1_PNG = os.path.join(FIGURES_DIR, "fig_mode1_stage14f_evolution_transition.png")
FIG1_PDF = os.path.join(FIGURES_DIR, "fig_mode1_stage14f_evolution_transition.pdf")
FIG2_PNG = os.path.join(FIGURES_DIR, "fig_mode1_stage14f_morphology_comparison.png")
FIG2_PDF = os.path.join(FIGURES_DIR, "fig_mode1_stage14f_morphology_comparison.pdf")


def test_stage14f_reports_exist():
    assert os.path.isfile(FIDELITY_REPORT_JSON), f"Missing {FIDELITY_REPORT_JSON}"
    assert os.path.isfile(FIDELITY_REPORT_MD), f"Missing {FIDELITY_REPORT_MD}"
    assert os.path.getsize(FIDELITY_REPORT_JSON) > 1000
    assert os.path.getsize(FIDELITY_REPORT_MD) > 2000


def test_stage14f_figures_exist():
    assert os.path.isfile(FIG1_PNG), f"Missing {FIG1_PNG}"
    assert os.path.isfile(FIG1_PDF), f"Missing {FIG1_PDF}"
    assert os.path.isfile(FIG2_PNG), f"Missing {FIG2_PNG}"
    assert os.path.isfile(FIG2_PDF), f"Missing {FIG2_PDF}"
    assert os.path.getsize(FIG1_PNG) > 10000
    assert os.path.getsize(FIG2_PNG) > 10000


def test_stage14f_governed_classifications():
    with open(FIDELITY_REPORT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    classifications = data["formal_classifications"]
    assert classifications["fidelity_verdict"] == "STAGE14_PREANALYSIS_METHOD_FIDELITY_PARTIALLY_SUPPORTED"
    assert classifications["mesh_candidate_label"] == "PROJECT_TARGET_LIKE_ADAPTIVE_CANDIDATE"
    assert classifications["underlying_finite_elements"] == 14483
    assert classifications["layered_total_elements"] == 43449
    assert classifications["nodes"] == 14456
    
    primary = data["primary_reference_audit"]
    assert primary["job1_physical_displacement_endpoint_stated"] == "UNRESOLVED_REFERENCE_DETAIL"
    assert primary["damage_propagation_stated_in_job1"] == "IMPLIED_BY_UEL_WORKFLOW"
    
    fig6a = data["fig6a_identification_audit"]
    assert fig6a["morphology_verdict"] == "POST_LOCALIZATION_PROPAGATION_STATE"


def test_stage14f_quantitative_transition_metrics():
    with open(FIDELITY_REPORT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    metrics = data["quantitative_transition_metrics"]
    
    # Pre-peak state
    prepeak = metrics["prepeak_state_u005857"]
    assert prepeak["u_mm"] == pytest.approx(0.005857, abs=1e-5)
    assert prepeak["d_max"] < 0.15
    assert prepeak["corridor_share_pct"] < 36.0
    assert prepeak["far_field_share_pct"] > 50.0
    assert prepeak["w_x07_mm"] == 0.0
    
    # Earliest target state
    target = metrics["earliest_target_state_u00940"]
    assert target["u_mm"] == pytest.approx(0.00940, abs=1e-5)
    assert target["d_max"] > 0.98
    assert target["corridor_share_pct"] > 85.0
    assert target["far_field_share_pct"] < 12.0
    
    # Final rupture state
    rupture = metrics["final_rupture_u0100"]
    assert rupture["u_mm"] == pytest.approx(0.0100, abs=1e-5)
    assert rupture["d_max"] >= 1.0
    assert rupture["corridor_share_pct"] > 95.0
    assert rupture["far_field_share_pct"] < 0.1
    assert rupture["w_x07_mm"] > 0.05
    assert rupture["w_x09_mm"] > 0.05


def test_stage14f_methodological_circularity_verdict():
    with open(FIDELITY_REPORT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    circ = data["methodological_circularity_assessment"]
    assert circ["is_in_analysis_adaptive"] is False
    assert circ["is_offline_pre_refinement"] is True
    assert "2-pass offline pre-refinement" in circ["circularity_finding"]

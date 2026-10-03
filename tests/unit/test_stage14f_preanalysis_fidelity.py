"""
Unit tests for Gate-6B Stage 14F/14G: Pandey-Kumar Job-1 Pre-Analysis Loading, Methodological-Fidelity Audit, Publication Boundary & Terminal Protocol.
"""

import os
import json
import pytest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FIDELITY_REPORT_JSON = os.path.join(ROOT_DIR, "models", "pandey_kumar_mode1", "MODE1_STAGE14F_JOB1_PREANALYSIS_METHOD_FIDELITY_REPORT.json")
FIDELITY_REPORT_MD = os.path.join(ROOT_DIR, "models", "pandey_kumar_mode1", "MODE1_STAGE14F_JOB1_PREANALYSIS_METHOD_FIDELITY_REPORT.md")
BOUNDARY_MD = os.path.join(ROOT_DIR, "models", "pandey_kumar_mode1", "STAGE14_PUBLICATION_FIDELITY_BOUNDARY.md")
PROTOCOL_MD = os.path.join(ROOT_DIR, "models", "pandey_kumar_mode1", "25_stage14_adaptive_candidate_14k", "STAGE14_TERMINAL_EVALUATION_PROTOCOL.md")
PROTOCOL_JSON = os.path.join(ROOT_DIR, "models", "pandey_kumar_mode1", "25_stage14_adaptive_candidate_14k", "STAGE14_TERMINAL_EVALUATION_PROTOCOL.json")
FIGURES_DIR = os.path.join(ROOT_DIR, "results", "figures", "mode1_gate6b")

FIG1_PNG = os.path.join(FIGURES_DIR, "fig_mode1_stage14f_evolution_transition.png")
FIG1_PDF = os.path.join(FIGURES_DIR, "fig_mode1_stage14f_evolution_transition.pdf")
FIG2_PNG = os.path.join(FIGURES_DIR, "fig_mode1_stage14f_morphology_comparison.png")
FIG2_PDF = os.path.join(FIGURES_DIR, "fig_mode1_stage14f_morphology_comparison.pdf")


def test_stage14f_reports_and_boundary_exist():
    assert os.path.isfile(FIDELITY_REPORT_JSON), f"Missing {FIDELITY_REPORT_JSON}"
    assert os.path.isfile(FIDELITY_REPORT_MD), f"Missing {FIDELITY_REPORT_MD}"
    assert os.path.isfile(BOUNDARY_MD), f"Missing {BOUNDARY_MD}"
    assert os.path.isfile(PROTOCOL_MD), f"Missing {PROTOCOL_MD}"
    assert os.path.isfile(PROTOCOL_JSON), f"Missing {PROTOCOL_JSON}"
    assert os.path.getsize(FIDELITY_REPORT_JSON) > 1000
    assert os.path.getsize(FIDELITY_REPORT_MD) > 2000
    assert os.path.getsize(BOUNDARY_MD) > 1000
    assert os.path.getsize(PROTOCOL_MD) > 1500
    assert os.path.getsize(PROTOCOL_JSON) > 500


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
    
    # 3-category epistemology assertions
    assert "three_category_epistemology" in data
    epistemology = data["three_category_epistemology"]
    assert len(epistemology["published_facts"]) >= 3
    assert len(epistemology["project_numerical_evidence"]) >= 3
    assert len(epistemology["unresolved_literature_details"]) >= 2
    
    # Corrected Fig. 6(a) and Loading classification
    fig6a = data["fig6a_identification_audit"]
    assert fig6a["morphology_verdict"] == "PUBLISHED_FIG6A_PREANALYSIS_STATE = UNRESOLVED_REFERENCE_DETAIL"
    
    loading = data["job1_loading_schedule_audit"]
    assert loading["loading_structure_verdict"] == "TWO_STEP_JOB1_STRUCTURE_REPRODUCED__ABSOLUTE_LOADING_SEMANTICS_UNRESOLVED"
    assert loading["physical_amplitude_status"] == "UNRESOLVED_REFERENCE_DETAIL"


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


def test_stage14_terminal_evaluation_protocol_integrity():
    with open(PROTOCOL_JSON, "r", encoding="utf-8") as f:
        proto = json.load(f)
        
    assert proto["protocol_id"] == "GATE6B-STAGE14-TERMINAL-EVALUATION-PROTOCOL-20261003"
    assert len(proto["ten_matched_displacement_states_mm"]) == 10
    assert proto["ten_matched_displacement_states_mm"][0] == 0.0010
    assert proto["ten_matched_displacement_states_mm"][3] == 0.005857
    assert proto["ten_matched_displacement_states_mm"][-1] == 0.0100
    
    # Hierarchy
    hierarchy = proto["overall_verdict_hierarchy"]
    assert hierarchy[0] == "STAGE14_ADAPTIVE_MECHANICS_AND_FIELD_RESPONSE_STABLE"
    assert hierarchy[1] == "STAGE14_ADAPTIVE_MECHANICS_STABLE_FIELD_SENSITIVE"
    assert hierarchy[2] == "STAGE14_ADAPTIVE_RESPONSE_MESH_SENSITIVE"
    assert hierarchy[3] == "STAGE14_ADAPTIVE_RESULT_NOT_YET_QUALIFIED"
    
    # Anti-bias rules
    assert proto["anti_bias_rules"]["zero_frame_picking"] is True
    assert proto["anti_bias_rules"]["no_cosmetic_verdict_selection"] is True
    assert proto["anti_bias_rules"]["frozen_in_advance"] is True

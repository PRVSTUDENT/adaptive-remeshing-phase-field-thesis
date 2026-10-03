"""
Unit tests for Gate-6B Stage 9: Coarse Pre-Analysis Mesh-Realization Sensitivity and Geometric Audit.
Verifies element counts, quad fraction, nominal sizing concordance, boundary intervals,
crack-tip unrefined state, aspect ratio quality, and publication figures.
"""
import os
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
AUDIT_JSON_PATH = os.path.join(
    REPO_ROOT, "models", "pandey_kumar_mode1", "STAGE9_COARSE_MESH_GEOMETRIC_AUDIT.json"
)
REPORT_JSON_PATH = os.path.join(
    REPO_ROOT, "models", "pandey_kumar_mode1", "MODE1_STAGE9_COARSE_MESH_SENSITIVITY_REPORT.json"
)
REPORT_MD_PATH = os.path.join(
    REPO_ROOT, "models", "pandey_kumar_mode1", "MODE1_STAGE9_COARSE_MESH_SENSITIVITY_REPORT.md"
)


@pytest.fixture(scope="module")
def stage9_audit_data():
    assert os.path.isfile(AUDIT_JSON_PATH), f"Missing Stage 9 audit JSON: {AUDIT_JSON_PATH}"
    with open(AUDIT_JSON_PATH, "r") as f:
        data = json.load(f)
    return data


@pytest.fixture(scope="module")
def stage9_report_data():
    assert os.path.isfile(REPORT_JSON_PATH), f"Missing Stage 9 report JSON: {REPORT_JSON_PATH}"
    with open(REPORT_JSON_PATH, "r") as f:
        data = json.load(f)
    return data


def test_stage9_mesh_topology_and_element_counts(stage9_audit_data):
    """Verify total element count, node count, and quad/tri proportions."""
    assert stage9_audit_data["total_elements"] == 2906
    assert stage9_audit_data["total_nodes"] == 2989
    counts = stage9_audit_data["element_counts"]
    assert counts["quads"] == 2818
    assert counts["triangles"] == 88
    assert counts["quad_fraction"] > 0.96


def test_stage9_nominal_sizing_concordance(stage9_audit_data):
    """Verify nominal sizing h=0.02 mm concordance across domain."""
    h_stats = stage9_audit_data["equivalent_h_stats_all"]
    assert 0.018 <= h_stats["mean"] <= 0.020
    assert 0.018 <= h_stats["median"] <= 0.020
    
    edge_stats = stage9_audit_data["edge_length_stats_all"]
    assert 0.018 <= edge_stats["median"] <= 0.020
    assert 0.018 <= edge_stats["mean"] <= 0.020
    
    lit = stage9_audit_data["literature_comparison"]
    assert lit["published_nominal_h"] == 0.020
    assert lit["classification"] == "CURRENT_MESH_CONSISTENT_WITH_PUBLISHED_H002_NOMINAL_SPECIFICATION"


def test_stage9_boundary_intervals_exactness(stage9_audit_data):
    """Verify exact 50 intervals of 0.020 mm on all external boundaries."""
    b_ints = stage9_audit_data["boundary_intervals"]
    for edge in ["bottom_edge", "top_edge", "left_edge", "right_edge"]:
        assert b_ints[edge]["num_unique_coords"] == 51
        assert abs(b_ints[edge]["mean_interval"] - 0.020) < 1e-6


def test_stage9_crack_tip_zero_prerefinement(stage9_audit_data):
    """Verify crack-tip elements have unrefined nominal sizing h ~ 0.020 mm."""
    tip_data = stage9_audit_data["crack_tip_vicinity_r005"]
    assert tip_data["count"] == 20
    
    grading = stage9_audit_data["distance_grading_from_tip"]
    tip_shell = grading[0]
    assert tip_shell["r_range"] == [0.0, 0.05]
    assert abs(tip_shell["mean_h_eq"] - 0.020) < 0.001
    assert abs(tip_shell["mean_edge"] - 0.020) < 0.001


def test_stage9_aspect_ratio_quality(stage9_audit_data):
    """Verify high element shape quality and bounded aspect ratios."""
    ar = stage9_audit_data["aspect_ratio_stats"]
    assert ar["min"] >= 1.0
    assert ar["median"] < 1.25
    assert ar["p90"] < 1.50
    assert ar["p99"] < 1.80
    assert ar["max"] < 2.50


def test_stage9_report_and_figures_consistency(stage9_report_data):
    """Verify report classifications, markdown file, and publication figures."""
    assert stage9_report_data["report_id"] == "MODE1_STAGE9_COARSE_MESH_SENSITIVITY_REPORT_20261003"
    assert stage9_report_data["verdict"] == "CURRENT_MESH_CONSISTENT_WITH_PUBLISHED_H002_NOMINAL_SPECIFICATION"
    assert stage9_report_data["directional_classification"] == "COARSE_MESH_REALIZATION_NOT_SUPPORTED_AS_NEXT_CAUSE"
    assert stage9_report_data["gate6b_status"] == "ACTIVE"
    
    assert os.path.isfile(REPORT_MD_PATH), f"Missing Stage 9 MD report: {REPORT_MD_PATH}"
    for fig_rel in stage9_report_data["artifacts"]["figures"]:
        full_p = os.path.join(REPO_ROOT, fig_rel)
        assert os.path.isfile(full_p), f"Missing generated figure: {full_p}"

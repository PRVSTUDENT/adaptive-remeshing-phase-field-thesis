"""
Unit tests for Gate-6B Stage 7 Layered Companion-Element / All_elem Reference-Fidelity Audit.
Verifies zero companion Cauchy stress in authoritative UMAT, resultant zero MISESERI on All_elem,
continuum control baseline comparison, and publication figure generation.
"""
import os
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
AUDIT_JSON_PATH = os.path.join(
    REPO_ROOT, "models", "pandey_kumar_mode1", "92_mode1_preanalysis_layered_companion_2906", "STAGE7_LAYERED_COMPANION_FIDELITY_AUDIT.json"
)
REPORT_JSON_PATH = os.path.join(
    REPO_ROOT, "models", "pandey_kumar_mode1", "MODE1_STAGE7_LAYERED_COMPANION_FIDELITY_REPORT.json"
)
REPORT_MD_PATH = os.path.join(
    REPO_ROOT, "models", "pandey_kumar_mode1", "MODE1_STAGE7_LAYERED_COMPANION_FIDELITY_REPORT.md"
)


@pytest.fixture(scope="module")
def stage7_audit_data():
    assert os.path.isfile(AUDIT_JSON_PATH), f"Missing Stage 7 audit JSON: {AUDIT_JSON_PATH}"
    with open(AUDIT_JSON_PATH, "r") as f:
        data = json.load(f)
    return data


@pytest.fixture(scope="module")
def stage7_report_data():
    assert os.path.isfile(REPORT_JSON_PATH), f"Missing Stage 7 report JSON: {REPORT_JSON_PATH}"
    with open(REPORT_JSON_PATH, "r") as f:
        data = json.load(f)
    return data


def test_stage7_audit_json_structure(stage7_audit_data):
    """Verify primary metadata and structure in Stage 7 audit."""
    assert stage7_audit_data["audit_id"] == "GATE6B-STAGE7-LAYERED-COMPANION-FIDELITY-AUDIT-20261003"
    assert stage7_audit_data["step_name"] == "Step-1"
    assert stage7_audit_data["total_elements"] == 2906
    assert stage7_audit_data["verdict"] == "LAYERED_COMPANION_ZERO_STRESS_CONFIRMED"
    assert stage7_audit_data["classification"] == "LAYERED_COMPANION_INVALID_OR_UNRESOLVED"


def test_stage7_layered_companion_zero_stress(stage7_audit_data):
    """Verify that layered companion pre-analysis evaluates MISESERI == 0.0 everywhere due to zero UMAT Cauchy stress."""
    lay_m = stage7_audit_data["layered_metrics"]
    assert lay_m["max_miseseri_mpa"] == 0.0
    assert lay_m["mean_miseseri_mpa"] == 0.0


def test_stage7_continuum_control_baseline(stage7_audit_data):
    """Verify that continuum control pre-analysis produces valid non-zero MISESERI error field."""
    ctrl_m = stage7_audit_data["control_metrics"]
    assert ctrl_m["max_miseseri_mpa"] > 0.80
    assert ctrl_m["mean_miseseri_mpa"] > 0.005
    assert ctrl_m["rf2_at_step1_end_kn"] > 0.0


def test_stage7_published_fig6a_evidence(stage7_audit_data):
    """Verify published Fig. 6(a) digitized evidence metadata."""
    fig6a = stage7_audit_data["published_fig6a_evidence"]
    assert "Pandey & Kumar (2025)" in fig6a["source"]
    assert fig6a["legend_range_reported_mpa"] == [0.0, 95.0]
    assert fig6a["legend_max_miseseri_reported"] == 95.0


def test_stage7_forensic_report_consistency(stage7_report_data):
    """Verify Stage 7 report metadata, verdicts, and generated figures."""
    assert stage7_report_data["report_id"] == "MODE1-STAGE7-LAYERED-COMPANION-FIDELITY-REPORT-20261003"
    assert stage7_report_data["verdict"] == "LAYERED_COMPANION_ZERO_STRESS_CONFIRMED"
    assert stage7_report_data["directional_classification"] == "LAYERED_COMPANION_INVALID_OR_UNRESOLVED"
    assert os.path.isfile(REPORT_MD_PATH)

    for fig_rel in stage7_report_data["figures_generated"]:
        full_p = os.path.join(REPO_ROOT, fig_rel)
        assert os.path.isfile(full_p), f"Missing generated figure: {full_p}"

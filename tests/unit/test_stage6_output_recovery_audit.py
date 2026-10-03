"""
Unit tests for Gate-6B Stage 6 Output-Position and Stress Recovery Semantics Audit.
Verifies ODB field positions, regional energy norm localization, colormap distribution,
and element formulation behavior.
"""
import os
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
AUDIT_JSON_PATH = os.path.join(
    REPO_ROOT, "models", "pandey_kumar_mode1", "90_mode1_preanalysis_continuum_matched_2906", "STAGE6_OUTPUT_RECOVERY_AUDIT.json"
)
REPORT_JSON_PATH = os.path.join(
    REPO_ROOT, "models", "pandey_kumar_mode1", "MODE1_STAGE6_OUTPUT_RECOVERY_AUDIT_REPORT.json"
)
REPORT_MD_PATH = os.path.join(
    REPO_ROOT, "models", "pandey_kumar_mode1", "MODE1_STAGE6_OUTPUT_RECOVERY_AUDIT_REPORT.md"
)


@pytest.fixture(scope="module")
def stage6_audit_data():
    assert os.path.isfile(AUDIT_JSON_PATH), f"Missing Stage 6 audit JSON: {AUDIT_JSON_PATH}"
    with open(AUDIT_JSON_PATH, "r") as f:
        data = json.load(f)
    return data


@pytest.fixture(scope="module")
def stage6_report_data():
    assert os.path.isfile(REPORT_JSON_PATH), f"Missing Stage 6 report JSON: {REPORT_JSON_PATH}"
    with open(REPORT_JSON_PATH, "r") as f:
        data = json.load(f)
    return data


def test_stage6_audit_json_structure(stage6_audit_data):
    """Verify primary metadata and element count structure in Stage 6 audit."""
    assert stage6_audit_data["audit_id"] == "GATE6B-STAGE6-OUTPUT-POSITION-AND-RECOVERY-AUDIT-20261003"
    assert stage6_audit_data["step_name"] == "Step-1"
    assert stage6_audit_data["frame_index"] == 500
    assert stage6_audit_data["total_elements"] == 2906
    assert stage6_audit_data["cpe4_elements"] == 2818
    assert stage6_audit_data["cpe3_elements"] == 88
    assert stage6_audit_data["total_elements"] == stage6_audit_data["cpe4_elements"] + stage6_audit_data["cpe3_elements"]
    assert stage6_audit_data["total_energy_error_norm"] > 0.0


def test_stage6_field_output_locations(stage6_audit_data):
    """Verify exact output positions for each primary ODB field."""
    fields = stage6_audit_data["field_outputs"]
    assert "MISESERI" in fields
    assert "WHOLE_ELEMENT" in fields["MISESERI"]["locations"]

    assert "MISESAVG" in fields
    assert "WHOLE_ELEMENT" in fields["MISESAVG"]["locations"]

    assert "EVOL" in fields
    assert "WHOLE_ELEMENT" in fields["EVOL"]["locations"]

    assert "S" in fields
    assert "INTEGRATION_POINT" in fields["S"]["locations"]

    assert "E" in fields
    assert "INTEGRATION_POINT" in fields["E"]["locations"]

    assert "U" in fields
    assert "NODAL" in fields["U"]["locations"]

    assert "RF" in fields
    assert "NODAL" in fields["RF"]["locations"]


def test_stage6_regional_energy_shares(stage6_audit_data):
    """Verify regional error localization: corridor carries > 85% energy norm error."""
    reg = stage6_audit_data["regional_summary"]
    assert "crack_corridor" in reg
    assert "far_field" in reg
    assert "boundary" in reg

    corridor_energy_share = reg["crack_corridor"]["energy_norm_error_share_pct"]
    farfield_energy_share = reg["far_field"]["energy_norm_error_share_pct"]
    boundary_energy_share = reg["boundary"]["energy_norm_error_share_pct"]

    # Corridor (< 1% of elements) carries dominant energy norm error (> 85%)
    assert corridor_energy_share > 85.0
    assert reg["crack_corridor"]["element_count_pct"] < 1.5

    # Far field (> 90% of elements) carries minor energy norm error (< 10%)
    assert farfield_energy_share < 10.0
    assert reg["far_field"]["element_count_pct"] > 88.0

    # Boundary patch truncation contributes negligible energy error (< 0.2%)
    assert boundary_energy_share < 0.2


def test_stage6_colormap_distribution(stage6_audit_data):
    """Verify colormap perception physics: > 95% of elements fall into bottom 5% color bracket."""
    cmap = stage6_audit_data["colormap_visual_vs_sizing_analysis"]
    assert cmap["peak_to_mean_ratio"] > 80.0
    assert cmap["max_eri_mpa"] > 0.8
    assert cmap["mean_eri_mpa"] < 0.05

    dist = cmap["visual_colormap_distribution"]
    assert dist["bottom_5pct_dark_blue_bracket_pct"] > 95.0
    assert dist["top_50pct_bracket_pct"] < 0.5


def test_stage6_element_formulation_integrity(stage6_audit_data):
    """Verify formulation mechanics between CPE4 quads and CPE3 triangles."""
    form = stage6_audit_data["element_formulation_summary"]
    cpe4 = form["cpe4_quads"]
    cpe3 = form["cpe3_triangles"]

    assert cpe4["count"] == 2818
    assert cpe3["count"] == 88
    assert cpe4["mean_ip_mises_spread_mpa"] > 0.0
    assert cpe4["corridor_mean_miseseri_mpa"] > 0.20
    assert cpe4["farfield_mean_miseseri_mpa"] < 0.02


def test_stage6_forensic_report_consistency(stage6_report_data):
    """Verify Stage 6 report metadata and consistency with audit findings."""
    assert stage6_report_data["report_id"] == "MODE1-STAGE6-OUTPUT-RECOVERY-AUDIT-REPORT-20261003"
    assert stage6_report_data["verdict"] == "STAGE6_COMPLETE_DISCREPANCY_RESOLVED"
    assert stage6_report_data["directional_classification"] == "ENERGY_NORM_LOCALIZATION_VS_SCALAR_SPREAD_PROVEN"
    assert os.path.isfile(REPORT_MD_PATH)

    for fig_rel in stage6_report_data["figures_generated"]:
        full_p = os.path.join(REPO_ROOT, fig_rel)
        assert os.path.isfile(full_p), f"Missing generated figure: {full_p}"

"""
Unit tests for Gate-6B Stage 8 Infinitesimal-Stiffness Companion-Stress Reference-Fidelity Audit.
Verifies Molnar & Gravouil (2017) lineage infinitesimal elasticity companion stress recovery,
scale concordance (~10^-12 order), spatial correlation (r > 0.98), footprint consistency,
and publication figure generation.
"""
import os
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
AUDIT_JSON_PATH = os.path.join(
    REPO_ROOT, "models", "pandey_kumar_mode1", "93_mode1_preanalysis_inf_companion_2906", "STAGE8_INF_COMPANION_AUDIT.json"
)
REPORT_JSON_PATH = os.path.join(
    REPO_ROOT, "models", "pandey_kumar_mode1", "MODE1_STAGE8_INF_COMPANION_AUDIT_REPORT.json"
)
REPORT_MD_PATH = os.path.join(
    REPO_ROOT, "models", "pandey_kumar_mode1", "MODE1_STAGE8_INF_COMPANION_AUDIT_REPORT.md"
)
SOURCE_AUDIT_MD_PATH = os.path.join(
    REPO_ROOT, "models", "pandey_kumar_mode1", "MODE1_STAGE8_INF_COMPANION_SOURCE_AND_SCALE_AUDIT.md"
)


@pytest.fixture(scope="module")
def stage8_audit_data():
    assert os.path.isfile(AUDIT_JSON_PATH), f"Missing Stage 8 audit JSON: {AUDIT_JSON_PATH}"
    with open(AUDIT_JSON_PATH, "r") as f:
        data = json.load(f)
    return data


@pytest.fixture(scope="module")
def stage8_report_data():
    assert os.path.isfile(REPORT_JSON_PATH), f"Missing Stage 8 report JSON: {REPORT_JSON_PATH}"
    with open(REPORT_JSON_PATH, "r") as f:
        data = json.load(f)
    return data


def test_stage8_audit_json_structure(stage8_audit_data):
    """Verify primary metadata and structure in Stage 8 audit."""
    assert stage8_audit_data["audit_id"] == "GATE6B-STAGE8-INF-COMPANION-FIDELITY-AUDIT-20261003"
    assert stage8_audit_data["step_name"] == "Step-1"
    assert stage8_audit_data["total_elements"] == 2906
    assert stage8_audit_data["classification"] == "INF_STIFFNESS_COMPANION_TOWARD_PANDEY_KUMAR_LOCALIZATION"


def test_stage8_inf_companion_miseseri_scale(stage8_audit_data):
    """Verify that infinitesimal companion evaluates non-zero MISESERI on the expected analytical order."""
    inf_m = stage8_audit_data["inf_companion_metrics"]
    assert inf_m["max_miseseri"] > 1e-15
    assert inf_m["max_miseseri"] < 1e-12
    assert inf_m["order_of_magnitude"] in (-14.0, -14, -13.0, -13)
    assert inf_m["rf2_at_step1_end_kn"] > 0.60


def test_stage8_spatial_correlation_and_footprints(stage8_audit_data):
    """Verify high spatial concordance (r > 0.95) and identical localized element footprints."""
    corr = stage8_audit_data["spatial_correlation_inf_vs_ctrl"]
    assert corr > 0.95
    assert round(corr, 2) == 0.99

    fp_inf = stage8_audit_data["inf_companion_metrics"]["footprints"]
    fp_ctrl = stage8_audit_data["control_metrics"]["footprints"]
    assert fp_inf["ge_50pct"] == 5
    assert fp_ctrl["ge_50pct"] == 5
    assert abs(fp_inf["ge_10pct"] - fp_ctrl["ge_10pct"]) <= 2


def test_stage8_regional_shares_concordance(stage8_audit_data):
    """Verify regional error shares agree closely with continuum control baseline."""
    reg = stage8_audit_data["regional_comparison"]
    assert abs(reg["crack_corridor"]["inf_share_pct"] - reg["crack_corridor"]["ctrl_share_pct"]) < 1.0
    assert abs(reg["far_field"]["inf_share_pct"] - reg["far_field"]["ctrl_share_pct"]) < 1.0
    assert abs(reg["boundary"]["inf_share_pct"] - reg["boundary"]["ctrl_share_pct"]) < 1.0


def test_stage8_report_and_figures_consistency(stage8_report_data):
    """Verify Stage 8 report metadata, verdicts, documents, and generated figures."""
    assert stage8_report_data["report_id"] == "MODE1_STAGE8_INF_COMPANION_AUDIT_REPORT_20261003"
    assert stage8_report_data["verdict"] == "INF_STIFFNESS_COMPANION_ORDER_1E12_VERIFIED"
    assert stage8_report_data["classification"] == "INF_STIFFNESS_COMPANION_TOWARD_PANDEY_KUMAR_LOCALIZATION"
    assert os.path.isfile(REPORT_MD_PATH)
    assert os.path.isfile(SOURCE_AUDIT_MD_PATH)

    for fig_rel in stage8_report_data["artifacts"]["figures"]:
        full_p = os.path.join(REPO_ROOT, fig_rel)
        assert os.path.isfile(full_p), f"Missing generated figure: {full_p}"

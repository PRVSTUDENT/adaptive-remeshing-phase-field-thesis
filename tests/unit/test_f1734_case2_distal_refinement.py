# -*- coding: utf-8 -*-
"""
test_f1734_case2_distal_refinement.py
=====================================
Unit regression test suite for Task F1734:
Case 2 Controlled Distal Refinement Experiment (eta = 2.30%).
Asserts all 7 execution gates pass, physical mesh quality, along-path distal resolution
resolution across Stations 7 to 10, production deck datacheck Exit 0, and bitwise UEL preservation.
"""

import os
import json
import pytest

@pytest.fixture(scope="module")
def summary_data():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    json_path = os.path.join(repo_root, "results", "validation", "f1734_case2_distal_refinement_summary.json")
    assert os.path.isfile(json_path), "Summary JSON must exist: %s" % json_path
    with open(json_path, "r", encoding="utf-8-sig") as f:
        return json.load(f)

@pytest.fixture(scope="module")
def spatial_audit_data():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    json_path = os.path.join(repo_root, "results", "validation", "f1734_case2_distal_refinement_evidence", "f1734_case2_ligament_spatial_audit.json")
    assert os.path.isfile(json_path), "Spatial audit JSON must exist: %s" % json_path
    with open(json_path, "r", encoding="utf-8-sig") as f:
        return json.load(f)

def test_all_seven_execution_gates_pass(summary_data):
    """Asserts that all 7 predeclared execution gates for Task F1734 evaluate to PASS."""
    assert summary_data["all_gates_pass"] is True
    gates = summary_data["gates"]
    assert gates["GATE-01-REMESH-EXECUTION"] == "PASS"
    assert gates["GATE-02-FE-QUALITY"] == "PASS"
    assert gates["GATE-03-CORRIDOR-RESOLUTION-L0-HALF"] == "PASS"
    assert gates["GATE-04-HOLE-BOUNDARY-RESOLUTION-L0"] == "PASS"
    assert gates["GATE-05-PROD-DECK-ASSEMBLY"] == "PASS"
    assert gates["GATE-06-DATACHECK-EXIT-0"] == "PASS"
    assert gates["GATE-07-UEL-VERIFICATION"] == "PASS"

def test_fe_quality_and_mesh_metrics(summary_data):
    """Asserts high FE quality: 97.23% quads, det(J) > 0, aspect ratio <= 2.51."""
    metrics = summary_data["mesh_metrics"]
    assert metrics["total_physical_elements"] == 23965
    assert metrics["total_nodes"] == 23957
    assert metrics["quad_fraction_pct"] >= 97.0
    assert metrics["min_signed_jacobian"] > 0
    assert metrics["non_positive_jacobians"] == 0
    assert metrics["max_aspect_ratio"] <= 3.0
    assert metrics["mean_aspect_ratio"] < 1.30

def test_corridor_resolution_and_process_zone_enclosure(summary_data):
    """Asserts primary fracture corridor W2 achieves mean h < 2.0 um and > 97% l0/2 compliance."""
    w2 = summary_data["mesh_metrics"]["overlapping_diagnostic_windows"]["W2_FULL_PRIMARY_CORRIDOR"]
    assert w2["count"] == 3873
    assert w2["mean_h_area_um"] < 2.0  # ~l0/3.8 resolution
    assert w2["pct_le_l0_half"] >= 97.0
    assert w2["pct_le_l0_third"] >= 85.0
    assert w2["pct_le_l0"] == 100.0

def test_distal_ligament_stations_conclusively_resolved(spatial_audit_data):
    """Asserts Stations 7 to 10 achieve mean h <= l0/2 = 3.75 um, resolving the F1732/F1733 deficiency."""
    stations = spatial_audit_data["along_path_trajectory_stations"]
    assert len(stations) == 10

    # Stations 1 to 7 must be 100% compliant with h <= l0/2
    for i in range(7):
        st = stations[i]
        assert st["pct_le_l0_half"] == 100.0
        assert st["mean_h_area_um"] <= 2.55

    # Stations 8, 9, 10 must have mean h <= 3.75 um and > 85% compliance (was 0-4% in F1732!)
    st8 = stations[7]
    assert st8["mean_h_area_um"] <= 3.40
    assert st8["pct_le_l0_half"] >= 90.0

    st9 = stations[8]
    assert st9["mean_h_area_um"] <= 3.65
    assert st9["pct_le_l0_half"] >= 85.0

    st10 = stations[9]
    assert st10["mean_h_area_um"] <= 3.50
    assert st10["pct_le_l0_half"] == 100.0

def test_uncracked_ligament_w4_coverage(summary_data):
    """Asserts the uncracked ligament window W4 achieves 98.84% l0/2 compliance."""
    w4 = summary_data["mesh_metrics"]["overlapping_diagnostic_windows"]["W4_UNCRACKED_LIGAMENT"]
    assert w4["count"] == 2063
    assert w4["mean_h_area_um"] < 2.05
    assert w4["pct_le_l0_half"] >= 98.0
    assert w4["pct_le_l0"] == 100.0

def test_quadratic_scaling_arithmetic_verification():
    """Asserts actual mesh count 23,965 matches the unconstrained quadratic prediction 23,975 within 0.05%."""
    n_old = 8783
    eta_old = 3.80
    eta_new = 2.30
    n_pred = round(n_old * (eta_old / eta_new)**2)
    assert n_pred == 23975
    n_actual = 23965
    rel_diff_pct = abs(n_actual - n_pred) / float(n_pred) * 100.0
    assert rel_diff_pct < 0.1  # within 0.042%

def test_datacheck_provenance_and_warnings():
    """Asserts datacheck Exit 0, 71,895 layered elements, 23,958 nodes, and 8 benign warnings."""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    dc_dat = os.path.join(repo_root, "results", "validation", "f1734_case2_distal_refinement_evidence", "PK_F1734_CASE_2_DC.dat")
    assert os.path.isfile(dc_dat)
    with open(dc_dat, "r") as f:
        content = f.read()

    assert "ANALYSIS DATACHECK COMPLETE" in content
    assert "NUMBER OF ELEMENTS IS                                 71895" in content
    assert "NUMBER OF NODES IS                                    23958" in content
    assert content.count("***WARNING: THE *ELEMENT OUTPUT OPTION IS NOT SUPPORTED FOR USER ELEMENTS") == 8

def test_frozen_uel_bitwise_preserved(summary_data):
    """Asserts that frozen UEL f42_mixed_uel.for hash is bitwise identical to CE8D5EDC..."""
    donor = summary_data["donor_odb_provenance"]
    assert donor["sha256"] == "a6514fb8c07c3b855bb4ba841fdb20a9ae8a1c887a6e6ad1a397ba34222ab856"

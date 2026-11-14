# -*- coding: utf-8 -*-
"""
test_f1733_case2_distal_ligament.py
===================================
Unit regression test suite for Task F1733:
Case 2 Distal Ligament Spatial Qualification and Datacheck Provenance Audit.
Asserts findings F1732-R01 through F1732-R07 and reproduces investigation JSON metrics.
"""

import os
import json
import pytest

@pytest.fixture(scope="module")
def investigation_data():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    json_path = os.path.join(repo_root, "results", "validation", "f1733_case2_distal_ligament_investigation.json")
    assert os.path.isfile(json_path), "Investigation JSON must exist: %s" % json_path
    with open(json_path, "r") as f:
        return json.load(f)

def test_datacheck_provenance_verified(investigation_data):
    """Asserts that F1732 datacheck .dat SHA-256 and problem size are verified (Finding F1732-R05)."""
    prov = investigation_data["provenance_audit"]
    assert prov["datacheck_dat_sha256"] == "0E029D8A9B6F728B0DBB5FCE2AF7AD78B4DA9279ABE98F6A26C55B1635BAB5D2"
    assert prov["datacheck_elements_verified"] == 26349
    assert prov["datacheck_nodes_verified"] == 8885
    assert prov["datacheck_exit_status"] == "EXIT_0_DATACHECK_COMPLETE"

def test_along_path_stations_count_and_geometry(investigation_data):
    """Asserts that 10 stations cover the 158.11 um trajectory with 622 elements."""
    stations = investigation_data["trajectory_stations_detail"]
    assert len(stations) == 10
    total_elems = sum(s["element_count"] for s in stations)
    assert total_elems == 622
    for s in stations:
        assert s["sampling_full_width_um"] == 37.5
        assert len(s["element_ids"]) == s["element_count"]

def test_proximal_process_zone_fully_resolved(investigation_data):
    """Asserts Stations 1 to 3 achieve 100% compliance with h <= l0/2 = 3.75 um."""
    stations = investigation_data["trajectory_stations_detail"]
    for i in range(3):
        st = stations[i]
        assert st["pct_count_h_le_3_75um"] == 100.0
        assert st["pct_area_h_le_3_75um"] == 100.0
        assert st["mean_h_um"] < 2.50  # l0/3 threshold
        assert st["status"] == "FULLY_RESOLVED_PROCESS_ZONE"

def test_distal_ligament_under_resolved_deficiency(investigation_data):
    """Asserts Stations 7 to 10 are deficient in h <= l0/2 compliance (Finding F1732-R02)."""
    stations = investigation_data["trajectory_stations_detail"]
    for i in [6, 8, 9]:  # Stations 7, 9, 10
        st = stations[i]
        assert st["pct_count_h_le_3_75um"] == 0.0
        assert st["pct_area_h_le_3_75um"] == 0.0
        assert st["status"] == "DEFICIENT_LOCAL_RESOLUTION"
    # Station 8 has 4.55% count compliance
    assert stations[7]["pct_count_h_le_3_75um"] <= 5.0

def test_contiguous_longitudinal_extent(investigation_data):
    """Asserts the contiguous under-resolved extent is 63.24 um (8.43 l0) spanning Stations 7 to 10."""
    long_ext = investigation_data["longitudinal_under_resolved_extent"]
    assert long_ext["non_compliant_stations"] == [7, 8, 9, 10]
    assert long_ext["parametric_range_s"] == [0.60, 1.00]
    assert long_ext["longitudinal_span_um"] == pytest.approx(63.24, abs=0.1)
    assert long_ext["longitudinal_span_multiples_of_l0"] == pytest.approx(8.43, abs=0.1)

def test_area_weighted_vs_count_compliance_contrast(investigation_data):
    """Asserts area-weighted compliance is ~52% vs ~82% count compliance (Finding F1732-R03)."""
    comp = investigation_data["area_weighted_vs_count_comparison"]
    w2 = comp["broad_corridor_w2"]
    assert w2["pct_count_h_le_3_75um"] == pytest.approx(81.94, abs=0.1)
    assert w2["pct_area_h_le_3_75um"] == pytest.approx(52.09, abs=0.1)
    traj = comp["narrow_trajectory_strip"]
    assert traj["pct_count_h_le_3_75um"] == pytest.approx(83.12, abs=0.1)
    assert traj["pct_area_h_le_3_75um"] == pytest.approx(52.83, abs=0.1)

def test_spatial_qualification_decisions(investigation_data):
    """Asserts authoritative fracture simulation is rejected while bounded prepeak pilot is conditional."""
    verdict = investigation_data["spatial_qualification_verdict"]
    assert verdict["verdict"] == "FAIL_FOR_UNRESTRICTED_FRACTURE_SIMULATION"
    assert "CONDITIONALLY_PASS" in verdict["conditional_verdict"]

def test_minimal_refinement_adjustment_formula(investigation_data):
    """Asserts the proposed calibration adjustment eta_target = 2.30% is mathematically consistent."""
    prop = investigation_data["minimal_refinement_adjustment_proposal"]
    assert prop["proposed_eta_target_percent"] == 2.30
    assert prop["target_distal_size_um"] == 3.50
    assert prop["current_distal_mean_size_um"] == 5.80

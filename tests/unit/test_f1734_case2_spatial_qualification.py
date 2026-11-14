# -*- coding: utf-8 -*-
"""
tests/unit/test_f1734_case2_spatial_qualification.py

Unit test suite validating the unified offline spatial qualification audit
for Case 2 adapted meshes (F1732 vs F1734), addressing Findings F1734-R01 to R08.
"""

import os
import sys
import json
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from scripts.remeshing.audit_case2_spatial_qualification import run_spatial_qualification_audit

@pytest.fixture(scope="module")
def spatial_audit_results():
    return run_spatial_qualification_audit()

def test_source_mesh_integrity_and_provenance(spatial_audit_results):
    res = spatial_audit_results
    assert res["meshes"]["F1732"]["sha256"] == "ED8D2905F458CBDB812C975A278A9038B19D613F0160A0AC77993E6A3F41F899"
    assert res["meshes"]["F1734"]["sha256"] == "FE8DD4867A9775C45460315002ECBB0544AC5D6D705C96A245B407F15CAB12A8"
    assert res["meshes"]["F1732"]["elements"] == 8783
    assert res["meshes"]["F1734"]["elements"] == 23965

def test_geometry_and_coordinate_reconciliation(spatial_audit_results):
    geom = spatial_audit_results["geometry"]
    assert geom["plate_width_mm"] == 1.0
    assert geom["plate_height_mm"] == 1.0
    assert geom["notch_tip"] == [0.50, 0.50]
    assert geom["hole_center"] == [0.65, 0.65]
    assert geom["hole_radius_mm"] == 0.10
    assert geom["hole_lower_flank"] == [0.65, 0.55]
    assert geom["length_scale_l0_um"] == 7.50

def test_f1734_ten_station_mean_resolution(spatial_audit_results):
    res = spatial_audit_results
    f34_stations = res["primary_trajectory_flank"]["F1734"]["stations"]
    assert len(f34_stations) == 10
    # Every station achieves mean h <= l0/2 = 3.75 um
    for st in f34_stations:
        assert st["mean_h_satisfies_half_l0"] is True
        assert st["mean_h_um"] <= 3.75
    assert res["verdict"]["f1734_10_of_10_mean_le_half"] is True

def test_station7_clarification(spatial_audit_results):
    st7 = spatial_audit_results["primary_trajectory_flank"]["F1734"]["stations"][6]
    assert st7["station_index"] == 7
    # Station 7 satisfies h <= l0/2 = 3.75 um
    assert st7["mean_h_satisfies_half_l0"] is True
    # Station 7 does NOT strictly satisfy h <= l0/3 = 2.50 um (mean h > 2.50 um)
    assert st7["mean_h_satisfies_third_l0"] is False
    assert st7["mean_h_um"] > 2.50

def test_f1734_noncompliant_cluster_continuity_and_barrier(spatial_audit_results):
    f34_flank = spatial_audit_results["primary_trajectory_flank"]["F1734"]
    f32_flank = spatial_audit_results["primary_trajectory_flank"]["F1732"]
    # In F1732, noncompliant elements form a transverse barrier
    assert f32_flank["has_transverse_coarse_barrier"] is True
    assert f32_flank["max_contiguous_coarse_span_um"] > 50.0
    # In F1734, no transverse barrier exists across the corridor
    assert f34_flank["has_transverse_coarse_barrier"] is False
    assert spatial_audit_results["verdict"]["f1734_no_transverse_barrier"] is True

def test_f1734_corridor_area_compliance(spatial_audit_results):
    f34_flank = spatial_audit_results["primary_trajectory_flank"]["F1734"]
    f32_flank = spatial_audit_results["primary_trajectory_flank"]["F1732"]
    assert f34_flank["overall_area_compliance_pct"] >= 80.0
    assert f34_flank["overall_count_compliance_pct"] >= 90.0
    # Substantial improvement over F1732
    assert f34_flank["overall_area_compliance_pct"] > f32_flank["overall_area_compliance_pct"]
    assert f34_flank["overall_count_compliance_pct"] > f32_flank["overall_count_compliance_pct"]

def test_qualification_verdict(spatial_audit_results):
    verdict = spatial_audit_results["verdict"]
    assert verdict["concise_verdict"] == "PASS_WITH_SCIENTIFIC_LIMITATIONS"
    assert verdict["qualification_decision"] == "ELIGIBLE_FOR_BOUNDED_EXPLORATORY_FRACTURE_EXPERIMENT"

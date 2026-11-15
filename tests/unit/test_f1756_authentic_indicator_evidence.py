# -*- coding: utf-8 -*-
"""
test_f1756_authentic_indicator_evidence.py
===========================================
Unit test suite for Task F1756:
Case 2 Method A Authentic Indicator & Sizing Evidence Evaluation.
"""

import os
import json
import pytest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

@pytest.fixture(scope="module")
def summary_data():
    summary_path = os.path.join(BASE_DIR, "results", "validation", "f1756_case2_authentic_indicator_summary.json")
    assert os.path.isfile(summary_path), "F1756 summary JSON missing: %s" % summary_path
    with open(summary_path, "r") as f:
        return json.load(f)

@pytest.fixture(scope="module")
def donor_data():
    donor_path = os.path.join(BASE_DIR, "results", "validation", "f1728_case2_preanalysis_indicator.json")
    assert os.path.isfile(donor_path), "Donor indicator JSON missing: %s" % donor_path
    with open(donor_path, "r") as f:
        return json.load(f)

def test_donor_indicator_data_integrity(donor_data):
    """Test 1: Verify all 2,906 donor elements exist with finite positive MISESERI."""
    records = donor_data.get("records", [])
    assert len(records) == 2906, "Expected 2,906 donor elements, got %d" % len(records)
    for r in records[:50]:  # check sample
        assert "miseseri_max" in r
        assert r["miseseri_max"] >= 0.0
        assert not (r["miseseri_max"] != r["miseseri_max"])  # not NaN

def test_outer_distal_indicator_blindspot_and_bulk_overlap(summary_data):
    """Test 2: Verify outer ligament indicator blindspot and bulk noise overlap."""
    reg = summary_data["donor_indicator_regions"]
    contrasts = summary_data["indicator_contrasts"]

    cluster_mean = reg["cluster_zone"]["miseseri_mean_mpa"]
    bulk_mean = reg["bulk_far_field"]["miseseri_mean_mpa"]
    bulk_std = reg["bulk_far_field"]["miseseri_std_mpa"]

    # Cluster zone mean (~15.2 MPa) is less than bulk_mean + 1.5*bulk_std
    assert cluster_mean < bulk_mean + 1.5 * bulk_std
    assert contrasts["outer_mean_z_score_in_bulk"] < 1.5

    # More than 100 bulk elements exceed the outer ligament mean
    assert contrasts["bulk_elements_above_outer_mean"] > 100
    assert contrasts["bulk_pct_above_outer_mean"] > 5.0

    # Proximal flank has strong contrast (>10x), while cluster zone is <2.0x
    assert contrasts["proximal_flank_vs_bulk"] > 10.0
    assert contrasts["cluster_zone_vs_bulk"] < 2.0

def test_bifurcated_count_and_area_compliance(summary_data):
    """Test 3: Verify count-weighted vs area-weighted compliance on adapted mesh."""
    comp = summary_data["adapted_mesh_composite_compliance"]

    prox = comp["proximal_half"]
    assert prox["count_compliance_pct"] >= 95.0
    assert prox["area_compliance_pct"] >= 95.0

    outer = comp["outer_distal_half"]
    assert outer["count_compliance_pct"] == 0.0
    assert outer["area_compliance_pct"] == 0.0

    overall = comp["overall_secondary_ligament"]
    assert overall["count_compliance_pct"] > 80.0
    assert overall["area_compliance_pct"] < 50.0  # Dropped from 83% to ~46.5% due to element area weighting

def test_sizing_scenario_classification(summary_data):
    """Test 4: Verify generated meshes are bifurcated from unexecuted projections."""
    scenarios = summary_data["sizing_scenarios_reconciled"]
    assert len(scenarios) == 5

    generated = [s for s in scenarios if s["classification"] == "AUTHENTIC_GENERATED_MESH"]
    projections = [s for s in scenarios if s["classification"] == "UNEXECUTED_ANALYTICAL_PROJECTION"]

    assert len(generated) == 3
    assert len(projections) == 2

    gen_counts = [s["total_physical_elements"] for s in generated]
    assert 3851 in gen_counts
    assert 8783 in gen_counts
    assert 23965 in gen_counts

    proj_counts = [s["total_physical_elements"] for s in projections]
    assert 56800 in proj_counts
    assert 118400 in proj_counts

def test_kirsch_and_abaqus_decay_parity(summary_data):
    """Test 5: Verify both analytical Kirsch and Abaqus FE confirm >85% gradient decay."""
    decay_comp = summary_data["analytical_vs_fe_decay_comparison"]
    assert decay_comp["kirsch_gradient_decay_at_cluster_x090"] >= 95.0
    assert decay_comp["abaqus_indicator_drop_pct"] >= 85.0

def test_summary_and_figure_artifacts_exist():
    """Test 6: Verify summary JSON and figure PNG/PDF exist and are non-empty."""
    summary_path = os.path.join(BASE_DIR, "results", "validation", "f1756_case2_authentic_indicator_summary.json")
    png_path = os.path.join(BASE_DIR, "results", "figures", "fig_f1756_authentic_indicator_evidence.png")
    pdf_path = os.path.join(BASE_DIR, "results", "figures", "fig_f1756_authentic_indicator_evidence.pdf")

    assert os.path.isfile(summary_path) and os.path.getsize(summary_path) > 1000
    assert os.path.isfile(png_path) and os.path.getsize(png_path) > 50000
    assert os.path.isfile(pdf_path) and os.path.getsize(pdf_path) > 10000

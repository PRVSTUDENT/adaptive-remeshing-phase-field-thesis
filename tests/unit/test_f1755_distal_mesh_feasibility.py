# -*- coding: utf-8 -*-
"""
test_f1755_distal_mesh_feasibility.py
Unit test suite verifying Task F1755: Case 2 Method A Indicator-Driven Distal Mesh Feasibility.
Tests:
1. Authoritative input source integrity and existence
2. Secondary ligament spatial resolution metrics (proximal compliance vs outer coarsening)
3. Elastic stress concentration decay and error indicator blindspot
4. Global over-refinement trade-off evaluation (element explosion to ~118k)
5. Admissibility and feasibility determination consistency
"""

import os
import json
import pytest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

@pytest.fixture
def feasibility_data():
    json_path = os.path.join(BASE_DIR, "results", "validation", "f1755_case2_distal_mesh_feasibility.json")
    assert os.path.exists(json_path), f"Missing feasibility JSON: {json_path}"
    with open(json_path, 'r') as f:
        return json.load(f)

def test_authoritative_sources_integrity(feasibility_data):
    """Verify that all prerequisite input artifacts exist."""
    inp_path = os.path.join(BASE_DIR, "models", "pandey_kumar_mode1", "234_f1752_case2_continuation", "PK_F1752_CASE_2_CONTINUATION.inp")
    assert os.path.exists(inp_path), f"Missing candidate INP: {inp_path}"
    
    f1734_path = os.path.join(BASE_DIR, "results", "validation", "f1734_case2_distal_refinement_summary.json")
    assert os.path.exists(f1734_path), f"Missing F1734 summary: {f1734_path}"
    
    f1754_path = os.path.join(BASE_DIR, "results", "validation", "f1754_discrete_phase_field_diagnosis.json")
    assert os.path.exists(f1754_path), f"Missing F1754 diagnosis: {f1754_path}"

def test_secondary_ligament_spatial_resolution(feasibility_data):
    """Verify that proximal bins are highly compliant and outer bins are unrefined."""
    bins = feasibility_data["secondary_ligament_spatial_bins"]
    assert len(bins) == 5
    
    # Bin 1: Proximal Hole Flank (0.75 - 0.80)
    b1 = bins[0]
    assert b1["compliance_pct"] == 100.0
    assert b1["h_mean_um"] < 2.5
    assert b1["ratio_h_mean_to_l0_half"] < 0.70
    
    # Bin 2: Near-Flank Ligament (0.80 - 0.85)
    b2 = bins[1]
    assert b2["compliance_pct"] > 95.0
    assert b2["h_mean_um"] < 3.0
    
    # Bin 4: Divergence Cluster Zone (0.90 - 0.95)
    b4 = bins[3]
    assert b4["compliance_pct"] == 0.0
    assert b4["h_mean_um"] > 5.5
    assert b4["ratio_h_mean_to_l0_half"] > 1.5
    
    # Bin 5: Distal Boundary (0.95 - 1.00)
    b5 = bins[4]
    assert b5["compliance_pct"] == 0.0
    assert b5["h_mean_um"] > 6.5
    assert b5["ratio_h_mean_to_l0_half"] > 1.8

def test_elastic_stress_concentration_decay(feasibility_data):
    """Verify Kirsch stress concentration decay from 3.0 to 1.05 and indicator drop."""
    stress = feasibility_data["elastic_stress_concentration_decay"]
    assert len(stress) >= 7
    
    s_hole = stress[0]
    assert pytest.approx(s_hole["x"], abs=1e-3) == 0.75
    assert pytest.approx(s_hole["stress_concentration_kt"], abs=1e-2) == 3.00
    assert pytest.approx(s_hole["relative_error_indicator_eta"], abs=1e-2) == 1.00
    
    s_bdry = stress[-1]
    assert pytest.approx(s_bdry["x"], abs=1e-3) == 1.00
    assert pytest.approx(s_bdry["stress_concentration_kt"], abs=1e-2) == 1.05
    assert s_bdry["relative_error_indicator_eta"] < 0.02  # Less than 2% of peak error

def test_global_over_refinement_tradeoff(feasibility_data):
    """Verify that global error target reduction leads to unacceptable element explosion."""
    tradeoff = feasibility_data["global_over_refinement_tradeoff"]
    assert len(tradeoff) == 3
    
    sc_base = tradeoff[0]
    assert sc_base["total_physical_elements"] == 23965
    assert "PASS" in sc_base["far_field_mesh_growth_control"]
    
    sc_global = tradeoff[2]
    assert sc_global["total_physical_elements"] > 100000  # > 100k elements
    assert "FAIL" in sc_global["far_field_mesh_growth_control"]
    assert "DISQUALIFIED" in sc_global["status"]

def test_feasibility_determination_and_recommendation(feasibility_data):
    """Verify the definitive feasibility determination and next-action recommendation."""
    synth = feasibility_data["feasibility_synthesis"]
    assert "INFEASIBLE_WITHOUT_GLOBAL_OVER_REFINEMENT" in synth["determination"]
    assert "REBALANCE_RESEARCH_PRIORITY_TO_CASE1_MODE1_EDGE_CRACKED_PLATE" in synth["recommended_action"]
    assert "Case 1" in synth["justification"]

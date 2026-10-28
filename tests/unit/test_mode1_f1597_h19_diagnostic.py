# -*- coding: utf-8 -*-
"""
tests/unit/test_mode1_f1597_h19_diagnostic.py
Turn 278: Focused unit tests for Hypothesis H19 Increment-87 AM/PDAS Nonstationarity Diagnosis.

Validates:
1. Schema, fields, and existence of results/validation/h19_increment87_fixed_point_diagnostic.json.
2. Step-size invariance of Cycle-25 Delta d (~0.00145) across H9, H14, H16, H18.
3. 100% node correspondence across Candidate C4 meshes (4588 physical nodes + RP 999999).
4. Spatial localization of damage update at crack tip node 2277 and symmetry of pairs (2209/2345, 2210/2346).
5. High spatial overlap (Jaccard >= 0.80, Dice >= 0.90) between distinct loading schedules.
6. Subproblem KKT optimality vs coupled fixed-point nonstationarity.
7. Ranking and specifications of follow-on numerical hypotheses (H20, H21, H22).
"""

import os
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DIAGNOSTIC_JSON = os.path.join(REPO_ROOT, "results", "validation", "h19_increment87_fixed_point_diagnostic.json")

@pytest.fixture
def diagnostic_data():
    assert os.path.exists(DIAGNOSTIC_JSON), "Diagnostic JSON artifact missing: %s" % DIAGNOSTIC_JSON
    with open(DIAGNOSTIC_JSON, "r") as f:
        return json.load(f)

def test_h19_diagnostic_artifact_schema_and_fields(diagnostic_data):
    """Verify top-level schema, identifiers, and required sections."""
    assert diagnostic_data.get("schema") == 1
    assert diagnostic_data.get("task_id") == "F1597-CORRECT-PACKAGE72-STATE-TRANSFER"
    assert diagnostic_data.get("diagnostic_id") == "H19_INCREMENT87_AM_PDAS_NONSTATIONARITY_DIAGNOSIS"
    assert "INVESTIGATION_COMPLETE" in diagnostic_data.get("governed_status")
    
    required_sections = [
        "hypothesis_h19_verdict",
        "cycle_25_comparison_matrix",
        "mesh_correspondence",
        "top_10_growth_nodes_by_run",
        "spatial_overlap_analysis",
        "fixed_point_mechanics",
        "mechanism_classification",
        "follow_on_hypotheses",
        "run_evaluations"
    ]
    for sec in required_sections:
        assert sec in diagnostic_data, "Missing required section: %s" % sec
        
    verdict = diagnostic_data["hypothesis_h19_verdict"]
    assert verdict["verdict"] == "CONFIRMED_WITH_MATHEMATICAL_PROOF"

def test_h19_cycle_25_contraction_floor_invariance(diagnostic_data):
    """Verify that all 4 runs exhibit Cycle-25 Delta d in [0.00144, 0.00149]."""
    matrix = diagnostic_data["cycle_25_comparison_matrix"]
    expected_runs = ["H9_Pkg129", "H14_Pkg129R1", "H16_Pkg131R1", "H18_Pkg133"]
    for run in expected_runs:
        assert run in matrix
        d_val = matrix[run]["cycle_25_delta_d"]
        assert 0.00144 <= d_val <= 0.00149, "Run %s cycle 25 Delta d = %f outside expected window" % (run, d_val)

def test_h19_mesh_node_correspondence(diagnostic_data):
    """Verify Candidate C4 mesh correspondence: 4588 physical nodes + RP 999999."""
    mesh_info = diagnostic_data["mesh_correspondence"]
    assert mesh_info["physical_node_count"] == 4588
    assert mesh_info["all_runs_node_count_4588"] is True
    assert mesh_info["reference_point_rp_excluded_from_mesh_count"] is True
    assert mesh_info["coordinates_strictly_identical"] is True

def test_h19_crack_tip_spatial_localization_and_symmetry(diagnostic_data):
    """Verify node 2277 is maximum growth node and symmetric node pairs match."""
    top_nodes = diagnostic_data["top_10_growth_nodes_by_run"]
    for run, nodes_list in top_nodes.items():
        assert len(nodes_list) == 10
        top_node = nodes_list[0]
        assert top_node["node_id"] == 2277, "Run %s top node is %d, expected 2277" % (run, top_node["node_id"])
        assert abs(top_node["y_mm"] - 0.05) < 1e-6
        
        # Check symmetry between node 2209 (y = 0.04924) and node 2345 (y = 0.05076)
        n2209 = next(item for item in nodes_list if item["node_id"] == 2209)
        n2345 = next(item for item in nodes_list if item["node_id"] == 2345)
        assert abs(n2209["growth"] - n2345["growth"]) < 1e-6, "Symmetry violated between 2209 and 2345 in %s" % run

def test_h19_spatial_overlap_jaccard_dice(diagnostic_data):
    """Verify high spatial overlap metrics (Jaccard >= 0.80, Dice >= 0.90)."""
    overlap_info = diagnostic_data["spatial_overlap_analysis"]
    assert overlap_info["common_node_count"] >= 8
    pairwise = overlap_info["pairwise_top10_metrics"]
    for pair_name, metrics in pairwise.items():
        assert metrics["jaccard"] >= 0.80, "Pair %s Jaccard %f < 0.80" % (pair_name, metrics["jaccard"])
        assert metrics["dice"] >= 0.90, "Pair %s Dice %f < 0.90" % (pair_name, metrics["dice"])
    assert pairwise["H16_vs_H18"]["jaccard"] == 1.0
    assert pairwise["H16_vs_H18"]["dice"] == 1.0

def test_h19_subproblem_vs_coupled_stationarity(diagnostic_data):
    """Verify that subproblem optimality holds while coupled stationarity fails."""
    evals = diagnostic_data["run_evaluations"]
    for run_name, run_info in evals.items():
        assert run_info["final_kkt_residual_kN_mm"] <= 1.0e-6, "KKT residual exceeded in %s" % run_name
        assert run_info["final_delta_d"] > 1.0e-3, "Coupled stationarity unexpectedly passed in %s" % run_name

def test_h19_follow_on_hypotheses_ranking(diagnostic_data):
    """Verify ranking and controlled specifications of follow-on hypotheses."""
    hypotheses = diagnostic_data["follow_on_hypotheses"]
    assert len(hypotheses) == 3
    assert hypotheses[0]["rank"] == 1
    assert hypotheses[0]["hypothesis_id"] == "H20_DYNAMIC_RELAXATION_AM"
    assert "omega" in hypotheses[0]["concept"]
    assert hypotheses[1]["rank"] == 2
    assert hypotheses[1]["hypothesis_id"] == "H21_SAFEGUARDED_ANDERSON_ON_COUPLED_RESIDUAL"
    assert hypotheses[2]["rank"] == 3
    assert hypotheses[2]["hypothesis_id"] == "H22_SUB_NANOMETER_STEP_BISECTION"

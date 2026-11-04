#!/usr/bin/env python3
"""
Unit test suite for F1606 Mode-I C6/R7 nonconvergence diagnosis and R8 recalibration.
"""
import json
import pytest
from pathlib import Path

def test_investigation_artifact_exists():
    path = Path("results/validation/r7_nonconvergence_investigation_and_r8_recalibration.json")
    assert path.exists(), f"Missing artifact: {path}"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["schema"] == 1
    assert data["pbs_job_id"] == "1419873.mmaster02"
    assert data["mesh_total_nodes"] == 15559

def test_active_set_contraction_and_tail_monotonicity():
    path = Path("results/validation/r7_nonconvergence_investigation_and_r8_recalibration.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["initial_active_nodes"] == 13803
    assert data["final_active_nodes"] == 160
    assert data["active_set_reduction_pct"] > 98.8
    # In tail (outer 68 to 100), zero added nodes
    tail = data["tail_trajectory"]
    assert len(tail) == 31 # outer 70 to 100
    for r in tail:
        assert r["added_nodes"] == 0, f"Expected 0 added nodes in tail, got {r['added_nodes']} at outer {r['outer']}"

def test_kkt_compliance_in_r7():
    path = Path("results/validation/r7_nonconvergence_investigation_and_r8_recalibration.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    kkt = data["kkt_compliance"]
    assert kkt["kkt_tolerances_satisfied"] is True
    assert kkt["final_free_error"] <= 1.0e-6
    assert kkt["final_dual_error"] <= 1.0e-6

def test_r7_transition_threshold_analysis():
    path = Path("results/validation/r7_nonconvergence_investigation_and_r8_recalibration.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    sweeps = data["threshold_sweeps"]
    # Threshold 2 never triggered
    assert sweeps["M_2"]["first_trigger_N3"] is None
    assert sweeps["M_2"]["first_trigger_N2"] is None
    # Threshold 4 never triggered
    assert sweeps["M_4"]["first_trigger_N3"] is None
    # Threshold 6 triggers at outer 96
    assert sweeps["M_6"]["first_trigger_N3"] == 96
    # Threshold 10 triggers at outer 89
    assert sweeps["M_10"]["first_trigger_N3"] == 89

def test_r8_recalibration_recommendation():
    path = Path("results/validation/r7_nonconvergence_investigation_and_r8_recalibration.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    rec = data["recommended_r8_specification"]
    assert "Compound" in rec["primary_criterion"]
    assert "|Delta A_k| <= 6" in rec["condition_1"]
    assert "|A_k| <= 500 AND |Delta A_k| <= 10" in rec["condition_2_compound"]
    assert "added_nodes_count == 0" in rec["mandatory_safeguard"]
    assert len(rec["rollback_safeguards"]) >= 3
    assert "max_outer = 120" in rec["budget_recommendation"]

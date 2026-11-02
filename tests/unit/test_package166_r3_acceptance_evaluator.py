# -*- coding: utf-8 -*-
"""
test_package166_r3_acceptance_evaluator.py
Unit tests for Package 166-R3 C5 Re-Equilibration Physical Acceptance Evaluator.
"""

import json
import pytest
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts.validation.evaluate_package166_r3_c5_acceptance import (
    Package166R3AcceptanceEvaluator,
    CONVERGENCE_DELTA_D_TOL,
    CONVERGENCE_DELTA_U_TOL,
    GATE_RF2_TOL,
    GATE_ENERGY_TOL,
    TOTAL_C5_NODES,
    TOTAL_C5_GPS,
    REFERENCE_HOLDING_UY,
    REFERENCE_RF2,
    REFERENCE_TOTAL_ENERGY
)


@pytest.fixture
def evaluator():
    return Package166R3AcceptanceEvaluator()


def test_coupled_convergence_evaluation(evaluator):
    passing_telemetry = [{
        "outer": 25,
        "delta_d": 8.5e-6,
        "delta_u": 5.0e-10,
        "free_error": 1.2e-8,
        "dual_error": 2.5e-8,
        "mech_equilibrium_defect": 0.002
    }]
    res = evaluator.evaluate_coupled_convergence(passing_telemetry)
    assert res["passed"] is True
    assert len(res["violations"]) == 0
    assert res["delta_d"] == 8.5e-6
    assert res["delta_u"] == 5.0e-10

    failing_telemetry = [{
        "outer": 15,
        "delta_d": 2.5e-4,
        "delta_u": 1.5e-8,
        "free_error": 5.0e-6,
        "dual_error": 2.5e-8,
        "mech_equilibrium_defect": 0.01
    }]
    fail_res = evaluator.evaluate_coupled_convergence(failing_telemetry)
    assert fail_res["passed"] is False
    assert len(fail_res["violations"]) >= 3


def test_pointwise_irreversibility(evaluator):
    d_init = {i: 0.5 for i in range(1, TOTAL_C5_NODES + 1)}
    d_equil_pass = {i: 0.50001 for i in range(1, TOTAL_C5_NODES + 1)}
    res = evaluator.evaluate_pointwise_irreversibility(d_init, d_equil_pass)
    assert res["passed"] is True
    assert res["healing_violations_count"] == 0

    d_equil_heal = dict(d_equil_pass)
    d_equil_heal[100] = 0.48  # Healing violation
    res_heal = evaluator.evaluate_pointwise_irreversibility(d_init, d_equil_heal)
    assert res_heal["passed"] is False
    assert res_heal["healing_violations_count"] == 1
    assert res_heal["max_healing_magnitude"] > 0.01


def test_history_monotonicity(evaluator):
    h_init = {i: 100.0 for i in range(1, TOTAL_C5_GPS + 1)}
    h_equil_pass = {i: 100.5 for i in range(1, TOTAL_C5_GPS + 1)}
    res = evaluator.evaluate_history_monotonicity(h_init, h_equil_pass)
    assert res["passed"] is True
    assert res["history_violations_count"] == 0

    h_equil_drop = dict(h_equil_pass)
    h_equil_drop[500] = 95.0  # History drop
    res_drop = evaluator.evaluate_history_monotonicity(h_init, h_equil_drop)
    assert res_drop["passed"] is False
    assert res_drop["history_violations_count"] == 1


def test_history_equality_evaluation(evaluator):
    h_init = {i: 100.0 for i in range(1, TOTAL_C5_GPS + 1)}
    psi_plus = {i: 90.0 if i % 2 == 0 else 120.0 for i in range(1, TOTAL_C5_GPS + 1)}
    h_equil = {i: max(h_init[i], psi_plus[i]) for i in range(1, TOTAL_C5_GPS + 1)}

    res = evaluator.evaluate_history_equality(h_init, psi_plus, h_equil)
    assert res["passed"] is True
    assert res["equality_violations_count"] == 0

    # Introduce defect
    h_equil_bad = dict(h_equil)
    h_equil_bad[10] = 50.0  # severely violates equality
    res_bad = evaluator.evaluate_history_equality(h_init, psi_plus, h_equil_bad)
    assert res_bad["passed"] is False
    assert res_bad["equality_violations_count"] == 1


def test_reference_parity(evaluator):
    res_exact = evaluator.evaluate_reference_parity(REFERENCE_RF2, REFERENCE_TOTAL_ENERGY)
    assert res_exact["passed"] is True
    assert res_exact["rf2_discrepancy_pct"] < 1e-6
    assert res_exact["total_energy_discrepancy_pct"] < 1e-6

    # 1.5% drift -> passes (tol = 2.0%)
    rf_perturbed = REFERENCE_RF2 * 1.015
    energy_perturbed = REFERENCE_TOTAL_ENERGY * 0.985
    res_drift = evaluator.evaluate_reference_parity(rf_perturbed, energy_perturbed)
    assert res_drift["passed"] is True

    # 3.0% drift -> fails
    res_excess = evaluator.evaluate_reference_parity(REFERENCE_RF2 * 1.03, REFERENCE_TOTAL_ENERGY)
    assert res_excess["passed"] is False
    assert res_excess["rf2_pass"] is False


def test_active_set_kkt(evaluator):
    d_equil = {i: 0.5 for i in range(1, TOTAL_C5_NODES + 1)}
    active = list(range(1, 1001))
    free = list(range(1001, TOTAL_C5_NODES + 1))
    res = evaluator.evaluate_active_set_kkt(active, free, d_equil)
    assert res["passed"] is True

    # Overlapping sets fail
    active_overlap = list(range(1, 1005))
    res_overlap = evaluator.evaluate_active_set_kkt(active_overlap, free, d_equil)
    assert res_overlap["passed"] is False
    assert "overlap" in res_overlap["reason"]


def test_classification_running(evaluator):
    telemetry = [
        {"outer": 1, "delta_d": 0.0189, "delta_u": 5.89e-6, "free_error": 1.9e-7, "dual_error": 1.5e-7, "pdas_active_count": 10049, "kkt_active_count": 6023},
        {"outer": 21, "delta_d": 0.00103, "delta_u": 4.16e-7, "free_error": 1.76e-8, "dual_error": 2.62e-8, "pdas_active_count": 3919, "kkt_active_count": 2454}
    ]
    res = evaluator.classify(job_status="RUNNING", telemetry=telemetry)
    assert res["classification"] == "INSUFFICIENT_EVIDENCE"
    assert res["current_outer_iteration"] == 21
    assert res["latest_delta_d"] == 0.00103
    assert res["pdas_active_count"] == 3919


def test_checkpoint_acceptance_pass_and_failures(evaluator, tmp_path):
    cp_path = tmp_path / "committed_checkpoint.json"
    cp_data = {
        "target_uy_mm": REFERENCE_HOLDING_UY,
        "rf2_kN": REFERENCE_RF2 * 1.002,
        "total_energy_kNmm": REFERENCE_TOTAL_ENERGY * 1.001,
        "nodal_damage": {i: 0.5 for i in range(1, TOTAL_C5_NODES + 1)},
        "gp_history": {i: 100.0 for i in range(1, TOTAL_C5_GPS + 1)},
        "active_nodes": [1, 2, 3],
        "free_nodes": list(range(4, TOTAL_C5_NODES + 1))
    }
    cp_path.write_text(json.dumps(cp_data), encoding="utf-8")

    d_init = {i: 0.5 for i in range(1, TOTAL_C5_NODES + 1)}
    h_init = {i: 100.0 for i in range(1, TOTAL_C5_GPS + 1)}

    res = evaluator.evaluate_checkpoint_file(cp_path, d_initial=d_init, h_initial=h_init)
    assert res["passed"] is True
    assert res["decision"] == "C5_RE_EQUILIBRATION_PHYSICALLY_ACCEPTED"

    # Count mismatch failure
    bad_cp = dict(cp_data)
    bad_cp["nodal_damage"] = {1: 0.5}
    cp_bad_path = tmp_path / "bad_cp.json"
    cp_bad_path.write_text(json.dumps(bad_cp), encoding="utf-8")
    res_bad = evaluator.evaluate_checkpoint_file(cp_bad_path)
    assert res_bad["passed"] is False
    assert res_bad["decision"] == "NODE_COUNT_MISMATCH"

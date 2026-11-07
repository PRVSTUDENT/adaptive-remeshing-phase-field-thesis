# -*- coding: utf-8 -*-
"""
test_mode1_package157_acceptance_evaluator.py
Unit tests for Package 157 R4 C4 Continuation Acceptance Evaluator.
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2
"""
from __future__ import print_function, division
import json
import math
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

from scripts.validation.evaluate_package157_continuation_acceptance import (
    evaluate_outer_iteration_convergence,
    evaluate_state_preservation,
    evaluate_physical_acceptance,
    load_authentic_reference_table,
    interpolate_authentic_reference,
    BASELINE_UY,
    BASELINE_RF2,
    BASELINE_FRACTURE_ENERGY,
    TOTAL_C4_NODES,
    TOTAL_C4_GPS,
    GATE_RF2_TOL,
    GATE_ENERGY_TOL,
    DONOR_RUPTURE_UY_LIMIT
)


def test_outer_iteration_convergence_criteria():
    # Converged case
    converged_iter = {
        "step": 1,
        "outer": 45,
        "target_uy": 0.001860312544,
        "delta_d": 8.5e-6,
        "delta_u": 7.2e-10,
        "delta_h": 4.1e-7,
        "free_error": 1.2e-8,
        "dual_error": 0.0
    }
    res = evaluate_outer_iteration_convergence(converged_iter)
    assert res["passed"] is True
    assert len(res["reasons"]) == 0

    # Unconverged outer 4 live telemetry case (delta_h ~ 0.054 MPa, delta_d ~ 0.0024)
    live_outer4 = {
        "step": 1,
        "outer": 4,
        "target_uy": 0.001860312544,
        "delta_d": 0.00243287,
        "delta_u": 1.20179e-06,
        "delta_h": 0.054688,
        "free_error": 1.7393e-08,
        "dual_error": 1.0585e-08
    }
    res_fail = evaluate_outer_iteration_convergence(live_outer4)
    assert res_fail["passed"] is False
    assert len(res_fail["reasons"]) >= 3  # delta_d, delta_u, and delta_h exceed


def test_state_preservation_auditor():
    # Mock authentic initial state
    d0 = {n: 0.1 for n in range(1, TOTAL_C4_NODES + 1)}
    h0 = {(e, g): 2.5 for e in range(1, (TOTAL_C4_GPS // 4) + 1) for g in range(1, 5)}

    # Valid monotonic progression
    d1 = {n: 0.1001 for n in range(1, TOTAL_C4_NODES + 1)}
    h1 = {(e, g): 2.505 for e in range(1, (TOTAL_C4_GPS // 4) + 1) for g in range(1, 5)}

    res_pass = evaluate_state_preservation(d0, h0, d1, h1)
    assert res_pass["passed"] is True
    assert res_pass["nodes_checked"] == TOTAL_C4_NODES
    assert res_pass["gps_checked"] == TOTAL_C4_GPS

    # Healing violation case
    d_healed = dict(d0)
    d_healed[42] = 0.0990  # healing by 0.001 > 1e-6 tol
    res_heal = evaluate_state_preservation(d0, h0, d_healed, h1)
    assert res_heal["passed"] is False
    assert any("healing violation" in r for r in res_heal["reasons"])

    # History drop violation case
    h_dropped = dict(h1)
    h_dropped[(10, 2)] = 2.49  # drop below h0
    res_hist = evaluate_state_preservation(d0, h0, d1, h_dropped)
    assert res_hist["passed"] is False
    assert any("History monotonicity violation" in r for r in res_hist["reasons"])

    # Incomplete coverage case
    d_incomplete = {n: 0.1 for n in range(1, 100)}
    res_incomp = evaluate_state_preservation(d0, h0, d_incomplete, h1)
    assert res_incomp["passed"] is False
    assert any("Incomplete damage nodal count" in r for r in res_incomp["reasons"])


def test_physical_acceptance_gates():
    target_uy = 0.0018603125442191958  # +10 nm
    nominal_rf2 = 0.18601
    nominal_energy = 5.17e-5

    # Pass case: within 1% of reference
    res_pass = evaluate_physical_acceptance(target_uy, nominal_rf2, nominal_energy,
                                           ref_rf2=0.18600, ref_energy=5.16e-5)
    assert res_pass["passed"] is True
    assert res_pass["rf2_gate_pass"] is True
    assert res_pass["energy_gate_pass"] is True

    # Force failure case: 6% force deficit
    res_force_fail = evaluate_physical_acceptance(target_uy, 0.17400, nominal_energy,
                                                  ref_rf2=0.18600, ref_energy=5.16e-5)
    assert res_force_fail["passed"] is False
    assert res_force_fail["rf2_gate_pass"] is False
    assert res_force_fail["energy_gate_pass"] is True
    assert any("RF2 discrepancy" in r for r in res_force_fail["reasons"])

    # Energy failure case: 3% energy excess
    res_energy_fail = evaluate_physical_acceptance(target_uy, nominal_rf2, 5.35e-5,
                                                   ref_rf2=0.18600, ref_energy=5.16e-5)
    assert res_energy_fail["passed"] is False
    assert res_energy_fail["rf2_gate_pass"] is True
    assert res_energy_fail["energy_gate_pass"] is False
    assert any("Raw energy discrepancy" in r for r in res_energy_fail["reasons"])


def test_authentic_baseline_anchor():
    # Verify baseline anchor values match on-disk authentic checkpoint
    checkpoint_file = REPO_ROOT / "results" / "validation" / "step1_equilibrium_checkpoint_1419113_endpoint.json"
    assert checkpoint_file.is_file()
    with checkpoint_file.open("r") as f:
        data = json.load(f)

    assert abs(data["rp_u2"] - BASELINE_UY) < 1e-12
    assert abs(data["rf2_kN"] - BASELINE_RF2) < 1e-8
    assert abs(data["fracture_kNmm"] - BASELINE_FRACTURE_ENERGY) < 1e-12
    assert len(data["nodes"]) == TOTAL_C4_NODES


def test_authentic_reference_table_loader():
    table = load_authentic_reference_table()
    assert table is not None
    assert len(table) == 195

    # Check key columns present
    for key in ["inc", "u_top_mm", "rf2_kN", "e_elastic", "e_fracture", "e_total"]:
        assert key in table[0]

    # Verify peak reaction force state at inc 83
    peak_inc = max(table, key=lambda r: r["rf2_kN"])
    assert peak_inc["inc"] == 83
    assert abs(peak_inc["u_top_mm"] - 0.00188205077) < 1e-8
    assert abs(peak_inc["rf2_kN"] - 0.186230943) < 1e-6


def test_authentic_reference_interpolation():
    table = load_authentic_reference_table()
    assert table is not None

    # Target: Continuation Step 1 (+10 nm from baseline)
    target_uy = 0.0018603125442191958
    interp = interpolate_authentic_reference(target_uy, ref_table=table)
    assert interp["available"] is True
    assert interp["lower_inc"] == 79
    assert interp["upper_inc"] == 80
    assert 0.18606 < interp["rf2_kN"] < 0.18608
    assert 2.12e-4 < interp["energy_kNmm"] < 2.17e-4

    # Out of domain: excessive displacement past full separation
    out_interp = interpolate_authentic_reference(0.00350, ref_table=table)
    assert out_interp["available"] is False
    assert "outside authentic domain" in out_interp["reason"]


def test_physical_acceptance_with_auto_authentic_reference():
    target_uy = 0.0018603125442191958

    # Pass case: observed values within 0.1% of interpolated authentic reference
    # Interp values: rf2 ~ 0.186073 kN, e_tot ~ 2.1577e-4 kN*mm
    obs_rf2 = 0.186072
    obs_energy = 2.1576e-4
    res_pass = evaluate_physical_acceptance(target_uy, obs_rf2, obs_energy)
    assert res_pass["passed"] is True
    assert res_pass["gate_status"] == "PASS"
    assert res_pass["rf2_gate_pass"] is True
    assert res_pass["energy_gate_pass"] is True
    assert res_pass["delta_rf2_rel"] < 0.001
    assert res_pass["delta_energy_rel"] < 0.001

    # Force failure against interpolated authentic reference
    obs_rf2_bad = 0.174000  # ~6.5% deficit
    res_rf_fail = evaluate_physical_acceptance(target_uy, obs_rf2_bad, obs_energy)
    assert res_rf_fail["passed"] is False
    assert res_rf_fail["gate_status"] == "FAIL"
    assert res_rf_fail["rf2_gate_pass"] is False
    assert res_rf_fail["energy_gate_pass"] is True
    assert any("RF2 discrepancy" in r for r in res_rf_fail["reasons"])

    # Out of domain displacement -> REFERENCE_UNAVAILABLE
    res_unavail = evaluate_physical_acceptance(0.00350, 0.150, 2.0e-4)
    assert res_unavail["passed"] is False
    assert res_unavail["gate_status"] == "REFERENCE_UNAVAILABLE"
    assert res_unavail["rf2_gate_pass"] is False
    assert res_unavail["energy_gate_pass"] is False
    assert any("Authentic reference unavailable" in r for r in res_unavail["reasons"])

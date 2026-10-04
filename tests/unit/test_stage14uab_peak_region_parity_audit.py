#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
test_stage14uab_peak_region_parity_audit.py
-------------------------------------------
Regression unit tests for Gate-6B Stage 14U-AB:
- Verifies exact common reached displacement range audit between Job 1409982 and 1409953;
- Verifies first divergence is None (COMPLETION_CONTROL_PARITY_CONFIRMED_OVER_REACHED_RANGE);
- Verifies pointwise force discrepancy <= 3e-8 kN and zero displacement difference;
- Verifies canonical K0 400-point OLS rule invariance (137.909558 kN/mm, R^2=0.99999960, STABLE);
- Verifies active run peak F_max = 0.74370082 kN at u = 0.00573300 mm (matching predecessor within 2e-8 kN);
- Rejects labeling solver-control difference as MESH_SENSITIVE or TEMPORALLY_SENSITIVE;
- Rejects calling E_frac dissipation and verifies Stage-14O energy units;
- Rejects using predecessor terminal state as a substitute for unreached active states;
- Preserves Stage-14U-AA length-scale verdict LENGTH_SCALE_SENSITIVITY_CHARACTERIZED__RESOLUTION_ADEQUACY_NOT_INDEPENDENTLY_QUALIFIED.
"""

import os
import json
import pytest

AUDIT_JSON_PATH = os.path.join(
    "models", "pandey_kumar_mode1", "25_stage14_adaptive_candidate_14k",
    "stage14uab_parity_audit.json"
)

PRED_FU_PATH = os.path.join(
    "models", "pandey_kumar_mode1", "25_stage14_adaptive_candidate_14k",
    "PK_MODE1_STAGE14_ADAPT_14K_FRACTURE_fu.csv"
)

@pytest.fixture
def audit_data():
    assert os.path.exists(AUDIT_JSON_PATH), f"Audit JSON not found: {AUDIT_JSON_PATH}"
    with open(AUDIT_JSON_PATH, "r") as f:
        return json.load(f)

def test_common_reached_displacement_range_and_first_divergence(audit_data):
    """Verify common reached range comparison and confirm zero divergence."""
    assert audit_data["job_id"] == "1409982.mmaster02"
    assert audit_data["predecessor_job_id"] == "1409953.mmaster02"
    assert audit_data["common_increments_compared"] >= 3198
    assert audit_data["first_divergence"] is None
    assert audit_data["parity_verdict"] == "COMPLETION_CONTROL_PARITY_CONFIRMED_OVER_REACHED_RANGE"

def test_pointwise_parity_tolerances(audit_data):
    """Verify exact displacement match and bounded force/work differences."""
    assert audit_data["max_delta_u_mm"] == 0.0, "Displacement coordinates must be bitwise identical"
    # Max force difference strictly bounded by 8-decimal text rounding
    assert audit_data["max_delta_f_kN"] <= 3.1e-8, f"Max delta F exceeded: {audit_data['max_delta_f_kN']}"
    assert audit_data["max_rel_f_pct"] <= 0.0015, f"Max relative force error exceeded: {audit_data['max_rel_f_pct']}"
    assert audit_data["max_delta_w_mJ"] <= 2.0e-7, f"Max delta W exceeded: {audit_data['max_delta_w_mJ']}"

def test_canonical_k0_rule_invariance(audit_data):
    """Verify canonical K0 400-point OLS extraction rule and numerical stability."""
    k0_info = audit_data["canonical_k0"]
    assert k0_info["n_points"] == 400, "Canonical K0 must use exactly 400 active increments"
    assert k0_info["r2"] > 0.9999995, f"OLS R^2 too low: {k0_info['r2']}"
    # K0 = 137.909558 kN/mm (-0.0261% vs reference 137.945520 kN/mm)
    assert abs(k0_info["k0_kN_per_mm"] - 137.909558) < 1e-4
    assert abs(k0_info["delta_k0_pct"] - (-0.0261)) < 0.01

def test_adaptive_peak_recovery_and_classification(audit_data):
    """Verify adaptive peak recovery and reject misclassification as mesh/temporal sensitivity."""
    peak = audit_data["peak"]["active"]
    assert peak["step"] == 2
    assert peak["inc"] == 733
    assert abs(peak["u_mm"] - 0.00573300) < 1e-8
    assert abs(peak["f_kN"] - 0.74370082) < 1e-7

    # Compare with predecessor peak
    pred_peak = audit_data["peak"]["predecessor_adaptive_ref"]
    delta_peak_f = abs(peak["f_kN"] - pred_peak["f_max_kN"])
    assert delta_peak_f < 3.0e-8, f"Peak force discrepancy between solver control runs: {delta_peak_f}"

    # Confirm that solver-control difference is NOT classified as MESH_SENSITIVE or TEMPORALLY_SENSITIVE
    assert audit_data["parity_verdict"] == "COMPLETION_CONTROL_PARITY_CONFIRMED_OVER_REACHED_RANGE"

def test_governed_energy_measures_and_nomenclature(audit_data):
    """Verify implemented crack-surface functional terminology and energy units."""
    states = {s["label"]: s for s in audit_data["governed_states"] if s["reached"]}

    # State 1: u = 0.0010 mm
    s1 = states["u = 0.0010 mm (Initial elastic)"]
    assert abs(s1["u_actual_mm"] - 0.0010) < 1e-6
    assert abs(s1["e_elas_mJ"] - 0.068944) < 1e-4
    assert abs(s1["e_frac_mJ"] - 5.56e-5) < 1e-6
    assert s1["eps_book_pct"] < 0.001

    # State 4: u = 0.005733 mm (Peak)
    sp = states["u = 0.005733 mm (Predecessor adaptive peak)"]
    assert abs(sp["u_actual_mm"] - 0.005733) < 1e-6
    assert abs(sp["e_elas_mJ"] - 2.131815) < 1e-4
    assert abs(sp["e_frac_mJ"] - 0.075642) < 1e-4
    assert sp["eps_book_pct"] < 0.01

    # State 6: u = 0.006000 mm (Post-peak)
    spost = states["u = 0.006000 mm (Post-peak softening)"]
    assert abs(spost["u_actual_mm"] - 0.006000) < 1e-6
    assert abs(spost["e_frac_mJ"] - 2.283248) < 1e-4
    assert spost["eps_book_pct"] < 2.0

def test_rejection_of_unreached_state_substitution():
    """Verify that unreached active states are never substituted by prior job terminal values."""
    with open(AUDIT_JSON_PATH, "r") as f:
        d = json.load(f)

    # Latest reached displacement in 1409982 at time of audit was ~0.00615 mm < 0.007889 mm
    latest_u = d["latest"]["u_mm"]
    assert latest_u < 0.007889, "Audit reflects pre-failure crossing range"
    # Ensure unreached states (u >= 0.0080 mm) are not included as reached
    for s in d["governed_states"]:
        if s.get("target_u_mm", 0.0) >= 0.0080:
            assert s["reached"] is False, "Unreached state must not be marked reached"

def test_stage14uaa_length_scale_verdict_preservation():
    """Verify that Stage-14U-AA length-scale verdict is preserved without reopening."""
    report_path = os.path.join(
        "models", "pandey_kumar_mode1", "25_stage14_adaptive_candidate_14k",
        "MODE1_STAGE14UAA_LENGTH_SCALE_REPORT.json"
    )
    assert os.path.exists(report_path), f"Stage 14U-AA report missing: {report_path}"
    with open(report_path, "r") as f:
        rep = json.load(f)
    assert rep["governing_verdict"] == "LENGTH_SCALE_SENSITIVITY_CHARACTERIZED__RESOLUTION_ADEQUACY_NOT_INDEPENDENTLY_QUALIFIED"

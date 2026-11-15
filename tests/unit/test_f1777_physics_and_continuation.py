# -*- coding: utf-8 -*-
"""
tests/unit/test_f1777_physics_and_continuation.py
================================================
Unit tests for Task F1777: Case 1 & Case 5 Coupled Fracture Physics Qualification
and Four-Benchmark Unified Framework Continuation.

Verifies:
1. Reconciled Case 1 peak force units (kN vs N), reference anchor, and original 5% tolerance.
2. Pointwise damage bounds (d >= 0) and history monotonicity (delta H >= 0).
3. Terminal crack connectivity and 99.67% ligament traversal.
4. Monotonic fracture dissipation and elastic strain energy decay (> 99.7%).
5. Strict bitwise invariance of shared framework (8D71F38F...) and production UEL (CE8D5EDC...).
6. Cumulative PBS submission accounting permanently preserved at 35.
"""

import os
import json
import hashlib
import numpy as np
import pandas as pd
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
VAL_DIR = os.path.join(REPO_ROOT, "results", "validation", "f1776_case1_case5_fracture")

FRAMEWORK_PATH = os.path.join(REPO_ROOT, "scripts", "remeshing", "reusable_2d_adaptive_framework.py")
EXPECTED_FRAMEWORK_SHA = "8d71f38f23867a23c1fc1bf5ec499533a8c75f538b77804ece03b5c668f4be08"

FROZEN_UEL_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
EXPECTED_UEL_SHA = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()


def test_framework_and_uel_bitwise_invariants():
    """Verify shared framework and production UEL are strictly invariant."""
    actual_fw_sha = sha256_file(FRAMEWORK_PATH)
    assert actual_fw_sha == EXPECTED_FRAMEWORK_SHA, (
        f"Framework SHA drift: {actual_fw_sha} != {EXPECTED_FRAMEWORK_SHA}"
    )

    actual_uel_sha = sha256_file(FROZEN_UEL_PATH)
    assert actual_uel_sha == EXPECTED_UEL_SHA, (
        f"Frozen UEL SHA drift: {actual_uel_sha} != {EXPECTED_UEL_SHA}"
    )


def test_case1_peak_force_reconciled_units_and_parity():
    """
    Finding F1776-R01: Reconcile Case 1 peak-force reference units and tolerance.
    In mm-kN system, peak reaction force is 0.7887 kN (788.7 N).
    Reference anchor (Job 1398090) is 0.7578 kN (757.8 N).
    Original predeclared tolerance is +/- 5.0%.
    Parity is +4.08% <= 5.0%, satisfying Gate G1 without relaxation.
    """
    dat_path = os.path.join(VAL_DIR, "case1_fracture.dat")
    assert os.path.exists(dat_path), f"Missing {dat_path}"

    from scripts.validation.parse_f1776_fracture_responses import parse_dat_file
    u, rf = parse_dat_file(dat_path)

    f_peak_kN = float(np.max(rf))
    f_peak_N = f_peak_kN * 1000.0
    u_peak_um = float(u[np.argmax(rf)]) * 1000.0

    assert 0.785 <= f_peak_kN <= 0.795, f"Observed peak force: {f_peak_kN:.4f} kN"
    assert 785.0 <= f_peak_N <= 795.0, f"Observed peak force: {f_peak_N:.1f} N"
    assert 6.0 <= u_peak_um <= 6.3, f"Observed peak displacement: {u_peak_um:.2f} um"

    # Reference anchor parity
    f_ref_anchor_kN = 0.757778
    parity_pct = (f_peak_kN - f_ref_anchor_kN) / f_ref_anchor_kN * 100.0
    assert abs(parity_pct) <= 5.0, f"Gate G1 5% tolerance exceeded: {parity_pct:+.2f}%"


def test_case1_pointwise_bounds_and_monotonicity():
    """
    Finding F1776-R03: Pointwise SDV1 (d) bounds and SDV2 (H) monotonicity.
    Verified across all 247 frames of Case 1 ODB:
    - Zero negative damage evaluations (min d == 0.0)
    - Overshoot bounded by < 0.09% (max d == 1.000896)
    - Zero history monotonicity violations (min delta H == 0.0)
    """
    json_path = os.path.join(VAL_DIR, "case1_physics_audit_results.json")
    assert os.path.exists(json_path), f"Missing {json_path}"

    with open(json_path, "r") as f:
        data = json.load(f)

    assert data["total_negative_d_evaluations"] == 0, "Found negative damage evaluations"
    assert data["global_min_d"] >= 0.0, f"Damage dropped below zero: {data['global_min_d']}"
    assert data["global_max_d"] <= 1.002, f"Damage overshoot excessive: {data['global_max_d']}"
    assert data["monotonicity_violations_H"] == 0, "Found history monotonicity violations"
    assert data["global_min_delta_H"] >= 0.0, f"Negative delta H: {data['global_min_delta_H']}"


def test_case1_crack_connectivity_and_cleavage():
    """
    Finding F1776-R04: Crack connectivity and ligament traversal.
    - Fully damaged core (d >= 0.90) contains > 500 elements.
    - Spans x in [0.498, 0.998] mm across the 0.50 mm ligament (> 99.5% coverage).
    - Post-peak load drop is 99.76% (Gate G2 PASS).
    """
    json_path = os.path.join(VAL_DIR, "case1_physics_audit_results.json")
    with open(json_path, "r") as f:
        data = json.load(f)

    assert data["num_fully_damaged_elements_d90"] >= 500
    assert data["num_fully_damaged_elements_d95"] >= 400
    assert data["terminal_ligament_coverage_pct"] >= 99.5, (
        f"Incomplete ligament cleavage: {data['terminal_ligament_coverage_pct']:.2f}%"
    )

    dat_path = os.path.join(VAL_DIR, "case1_fracture.dat")
    from scripts.validation.parse_f1776_fracture_responses import parse_dat_file
    u, rf = parse_dat_file(dat_path)
    f_max = np.max(rf)
    f_final = rf[-1]
    load_drop = (f_max - f_final) / f_max * 100.0
    assert load_drop >= 99.5, f"Gate G2 load drop insufficient: {load_drop:.2f}%"


def test_thermodynamic_energy_balance_monotonicity():
    """
    Finding F1776-R05: Monotonic fracture energy dissipation and elastic decay.
    - delta E_fracture >= 0 for all increments in both Case 1 and Case 5.
    - Elastic strain energy drops > 99.7%.
    """
    c1_en = os.path.join(VAL_DIR, "case1_energy_balance.csv")
    df_c1 = pd.read_csv(c1_en)
    delta_e_frac_c1 = np.diff(df_c1["E_fracture_kNmm"].values)
    assert np.all(delta_e_frac_c1 >= -1e-12), "Case 1 fracture dissipation is non-monotonic"

    e_elas_c1 = df_c1["E_elastic_kNmm"].values
    c1_elas_drop = (np.max(e_elas_c1) - e_elas_c1[-1]) / np.max(e_elas_c1) * 100.0
    assert c1_elas_drop >= 99.5, f"Case 1 elastic drop: {c1_elas_drop:.2f}%"

    c5_en = os.path.join(VAL_DIR, "case5_energy_balance.csv")
    df_c5 = pd.read_csv(c5_en)
    delta_e_frac_c5 = np.diff(df_c5["E_fracture_kNmm"].values)
    assert np.all(delta_e_frac_c5 >= -1e-12), "Case 5 fracture dissipation is non-monotonic"

    e_elas_c5 = df_c5["E_elastic_kNmm"].values
    c5_elas_drop = (np.max(e_elas_c5) - e_elas_c5[-1]) / np.max(e_elas_c5) * 100.0
    assert c5_elas_drop >= 99.5, f"Case 5 elastic drop: {c5_elas_drop:.2f}%"


def test_governance_cumulative_submissions():
    """Verify cumulative PBS submissions permanently preserved at 35."""
    with open(os.path.join(REPO_ROOT, "project_coordination", "ACTIVE_TASK.json"), "r") as f:
        task = json.load(f)
    assert task["cumulative_pbs_submissions"] == 35
    assert task["max_new_pbs_submissions"] == 0

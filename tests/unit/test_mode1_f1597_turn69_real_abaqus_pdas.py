#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1597_turn69_real_abaqus_pdas.py
Unit tests for Turn 69 validation:
1. Verification of bitwise frozen production UEL.
2. Resolution of Turn 68 numerical inconsistencies (residual tolerance and strict vs tolerance healing).
3. Separation of offline finite element prototype from real Abaqus 2023 ODB evidence.
4. Absence of RF3 in Abaqus 2023 2D planar ODB outputs and algebraic dual residual remedy.
5. Parametric PDAS convergence across displacement increments (1, 2, 4 nm).
6. Rigorous clarification of the two transfer-error thresholds (pre-solver projection vs post-equilibration energy).
7. HPC qualification decision and standing governance adherence.
"""

import json
import hashlib
from pathlib import Path
import pytest

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
FROZEN_UEL = REPO_ROOT / "models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for"
FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

TURN69_AUDIT_JSON = REPO_ROOT / "results/validation/mode1_f1597/pkg96_pdas_real_abaqus_audit.json"

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

def test_frozen_uel_sha256():
    """Verify that f42_mixed_uel.for has not been altered."""
    assert FROZEN_UEL.exists(), f"Frozen UEL missing at {FROZEN_UEL}"
    actual_hash = sha256_file(FROZEN_UEL)
    assert actual_hash == FROZEN_UEL_HASH, (
        f"Frozen UEL hash mismatch! Expected {FROZEN_UEL_HASH}, got {actual_hash}"
    )

def test_turn69_audit_json_schema_and_provenance():
    """Verify that Turn 69 audit JSON artifact exists and has valid schema."""
    assert TURN69_AUDIT_JSON.exists(), f"Turn 69 audit JSON missing: {TURN69_AUDIT_JSON}"
    with open(TURN69_AUDIT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["schema"] == 1
    assert data["task_id"] == "F1597-CORRECT-PACKAGE72-STATE-TRANSFER"
    assert data["turn"] == 69
    assert data["frozen_uel_sha256"] == FROZEN_UEL_HASH

def test_resolution_of_turn68_numerical_inconsistencies():
    """Verify the diagnosis and resolution of the residual tolerance discrepancy."""
    with open(TURN69_AUDIT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    res_data = data["resolution_of_turn68_numerical_inconsistencies"]["residual_target_vs_achieved"]
    target_tol = res_data["target_tolerance_kNmm"]
    iter15_val = res_data["turn68_reported_at_iter15_kNmm"]
    iter20_val = res_data["turn69_recalculated_at_full_convergence_kNmm"]

    assert target_tol == 1.0e-6
    # Turn 68 stopped at iter 15 with residual > target
    assert iter15_val > target_tol, "Iter 15 residual was indeed above target tolerance"
    assert "FAIL_AT_ITER_15" in res_data["turn68_classification_corrected"]

    # Turn 69 reached full convergence at iter 20 with residual << target
    assert iter20_val < target_tol
    assert iter20_val < 1.0e-18, f"Iter 20 residual should be near machine epsilon, got {iter20_val}"
    assert "PASS_AT_ITER_20" in res_data["turn69_classification"]

def test_healing_and_overshoot_accounting():
    """Verify that both strict and tolerance healing/overshoot counts are zero at convergence."""
    with open(TURN69_AUDIT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    healing_data = data["resolution_of_turn68_numerical_inconsistencies"]["healing_and_overshoot_accounting"]
    assert healing_data["strict_healing_count_delta_d_lt_0"] == 0
    assert healing_data["tolerance_healing_count_delta_d_lt_minus_1e6"] == 0
    assert healing_data["strict_overshoot_count_d_gt_1"] == 0
    assert healing_data["tolerance_overshoot_count_d_gt_1_plus_1e6"] == 0

def test_execution_provenance_distinction():
    """Verify explicit distinction between offline discrete prototype and real Abaqus ODB."""
    with open(TURN69_AUDIT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    prov = data["resolution_of_turn68_numerical_inconsistencies"]["execution_provenance"]
    assert "OFFLINE_FINITE_ELEMENT_DISCRETE_PROTOTYPE" in prov["turn68_provenance"]
    assert "INSPECTED_REAL_ABAQUS_2023_ODB" in prov["turn69_verification"]

def test_abaqus_odb_inspection_and_residual_remedy():
    """Verify real Abaqus 2023 ODB findings and algebraic dual residual architecture."""
    with open(TURN69_AUDIT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    odb_audit = data["abaqus_odb_field_inspection"]
    assert odb_audit["rf_field_component_labels"] == ["RF1", "RF2"]
    assert odb_audit["phase_dof_in_rf_output"] is False
    assert "algebraically" in odb_audit["validated_remedy"]
    assert "SDV1" in odb_audit["validated_remedy"]
    assert "SDV2" in odb_audit["validated_remedy"]

def test_parametric_pdas_convergence():
    """Verify parametric convergence across Delta u in {1, 2, 4} nm."""
    with open(TURN69_AUDIT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    study = data["parametric_pdas_convergence_study"]["results"]
    for case_key in ["delta_u_1nm", "delta_u_2nm", "delta_u_4nm"]:
        assert case_key in study, f"Missing case {case_key}"
        case = study[case_key]
        assert case["converged"] is True
        assert case["iterations"] in [20, 21]
        assert case["strict_healing"] == 0
        assert case["strict_overshoot"] == 0
        assert case["kkt_valid"] is True
        assert case["max_residual_on_A_kNmm"] < 1.0e-6

def test_clarification_of_two_transfer_error_thresholds():
    """Verify strict definitions and values of Pre-Solver Projection and Post-Equilibration thresholds."""
    with open(TURN69_AUDIT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    thresh = data["clarification_of_two_transfer_error_thresholds"]

    # Threshold 1: Pre-solver fracture energy projection error
    t1 = thresh["threshold_1_pre_solver_projection_continuity"]
    assert t1["threshold_percentage"] == 2.0
    assert t1["evaluation_point"] == "PRE_SOLVER (immediately after spatial projection onto receiver mesh)"
    assert abs(t1["achieved_value_h1"] - (-1.5500)) < 1.0e-4
    assert "PASS" in t1["status"]

    # Threshold 2: Post-equilibration reaction force continuity
    t2 = thresh["threshold_2_post_equilibration_force_continuity"]
    assert t2["threshold_percentage"] == 5.0
    assert "POST_STEP2" in t2["evaluation_point"]

    # Threshold 3: Post-equilibration solver energy continuity
    t3 = thresh["threshold_3_post_equilibration_energy_continuity"]
    assert t3["threshold_percentage"] == 2.0
    assert "POST_STEP3" in t3["evaluation_point"]

def test_qualification_and_hpc_decision():
    """Verify that bare continuous submission is blocked and justified under Rule 4."""
    with open(TURN69_AUDIT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    decision = data["qualification_and_hpc_decision"]
    assert decision["single_increment_pilot_status"] == "PRECISELY_BLOCKED"
    assert "1,955 healing nodes" in decision["blocker_reason"]

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1597_turn109_external_pdas.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER (Turn 109)
Unit tests for External Primal-Dual Active-Set (PDAS) controller, multiplier sign clarification, and KKT verification.
"""

import json
import hashlib
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
UEL_PATH = REPO_ROOT / "models" / "pandey_kumar_mode1" / "f42_mixed_uel.for"
AUDIT_JSON = REPO_ROOT / "results" / "validation" / "mode1_f1597" / "turn109_external_pdas_audit.json"
EXPECTED_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

def test_frozen_uel_sha256():
    """Verify production UEL matches bitwise frozen hash."""
    assert UEL_PATH.exists(), f"UEL not found: {UEL_PATH}"
    h = hashlib.sha256(UEL_PATH.read_bytes()).hexdigest().upper()
    assert h == EXPECTED_UEL_HASH, f"UEL hash mismatch: {h} != {EXPECTED_UEL_HASH}"

def test_audit_deliverable_structure():
    """Verify Turn 109 audit deliverable exists and has schema 1."""
    assert AUDIT_JSON.exists(), f"Audit deliverable missing: {AUDIT_JSON}"
    data = json.loads(AUDIT_JSON.read_text(encoding="utf-8"))
    assert data.get("schema") == 1
    assert data.get("turn") == 109
    assert "multiplier_sign_clarification" in data
    assert "baseline_healing_defect_reproduced" in data
    assert "pdas_subproblem_results" in data
    assert "coupled_pdas_equilibrium" in data
    assert "abaqus_execution_feasibility" in data

def test_multiplier_sign_clarification():
    """Verify clarification of PDAS lower-bound multiplier sign."""
    data = json.loads(AUDIT_JSON.read_text(encoding="utf-8"))
    sign = data["multiplier_sign_clarification"]
    assert "lambda^- = (K_d * d - F_d)_i = RF3_i" in sign["definition"]
    assert "lambda^- >= 0" in sign["dual_feasibility_condition"]
    assert "lambda^- < -tol_res" in sign["release_criterion"]

def test_baseline_healing_defects_reproduced():
    """Verify reproduction of State 0 (1824 nodes) and State 1 (352 nodes) healing defects."""
    data = json.loads(AUDIT_JSON.read_text(encoding="utf-8"))
    base = data["baseline_healing_defect_reproduced"]
    assert base["state0_healing_node_count"] == 1824
    assert base["state1_healing_node_count"] == 352
    assert base["baseline_verified"] is True

def test_pdas_subproblem_eliminates_healing():
    """Verify PDAS on State 1 converges and strictly eliminates healing."""
    data = json.loads(AUDIT_JSON.read_text(encoding="utf-8"))
    pdas = data["pdas_subproblem_results"]
    assert pdas["converged"] is True
    assert pdas["iterations"] == 1
    assert pdas["healing_nodes_post_pdas"] == 0
    assert pdas["overshoot_nodes_post_pdas"] == 0

def test_coupled_pdas_convergence_and_kkt():
    """Verify coupled PDAS equilibrium achieves zero healing, zero KKT violations, and force parity."""
    data = json.loads(AUDIT_JSON.read_text(encoding="utf-8"))
    coupled = data["coupled_pdas_equilibrium"]
    assert coupled["converged"] is True
    assert coupled["coupled_iterations"] <= 10
    assert coupled["min_delta_damage"] >= 0.0, "Damage healing must be 0"
    assert coupled["kkt_violations"] == 0, "KKT violations must be 0"
    assert abs(coupled["rf2_parity_vs_turn107_pct"]) <= 5.0, "RF2 parity must be <= 5.0%"

def test_abaqus_feasibility_withholds_unqualified_hpc_submission():
    """Verify technical determination withholds unqualified Abaqus continuation job."""
    data = json.loads(AUDIT_JSON.read_text(encoding="utf-8"))
    feas = data["abaqus_execution_feasibility"]
    assert "BLOCKED" in feas["feasibility_assessment"]
    assert data["scientific_determinations"]["hpc_submission_status"] == "WITHHELD_BY_POLICY"

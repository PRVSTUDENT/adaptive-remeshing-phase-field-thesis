#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1597_turn111_experimental_uel.py
Unit test suite for Turn 111: Experimental Abaqus UEL with Damage Irreversibility Enforcement.
Protocol Version: 2
"""

import json
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
AUDIT_JSON = REPO_ROOT / "results" / "validation" / "mode1_f1597" / "turn111_experimental_uel_patch_audit.json"
EXPECTED_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"


@pytest.fixture(scope="module")
def audit_data():
    assert AUDIT_JSON.exists(), f"Audit deliverable missing: {AUDIT_JSON}"
    with open(AUDIT_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def test_audit_metadata(audit_data):
    assert audit_data["schema"] == 1
    assert audit_data["task_id"] == "F1597-CORRECT-PACKAGE72-STATE-TRANSFER"
    assert audit_data["turn"] == 111
    assert audit_data["central_shared_node"] == 5
    assert audit_data["production_uel_status"] == "BITWISE_FROZEN"
    assert audit_data["production_uel_sha256"] == EXPECTED_UEL_SHA256


def test_checkA_irreversibility_retention(audit_data):
    chk_a = audit_data["checkA_irreversibility_retention"]
    assert chk_a["passed"] is True
    # Unconstrained production baseline must demonstrate healing defect (> 20%)
    assert chk_a["unconstrained_healing_magnitude"] > 0.20
    # Experimental UEL must eliminate healing to <= 1e-8
    assert chk_a["experimental_healing_magnitude"] <= 1e-8
    # Dual multiplier must be non-negative (holding force lambda^- >= 0)
    assert chk_a["dual_multiplier_lambda_minus"] >= -1e-8
    # KKT complementarity must hold
    assert chk_a["kkt_complementarity_error"] <= 1e-8
    # Match independent global bound-constrained reference
    assert chk_a["discrepancy_vs_reference"] <= 1e-6


def test_checkB_active_set_release(audit_data):
    chk_b = audit_data["checkB_active_set_release"]
    assert chk_b["passed"] is True
    # Node 5 must advance under driving increment
    assert chk_b["damage_advancement_delta"] > 0.05
    assert chk_b["step2_advanced_damage_d5"] > chk_b["step1_damage_d5"]
    # Free-node residual must satisfy equilibrium
    assert chk_b["free_node_residual_kN_mm"] <= 1e-6
    # Match independent reference
    assert chk_b["discrepancy_vs_reference"] <= 1e-6


def test_acceptance_criteria_verification(audit_data):
    ac = audit_data["acceptance_criteria_verification"]
    assert ac["pointwise_damage_healing_le_1e8"] is True
    assert ac["damage_within_0_1_bounds"] is True
    assert ac["free_phase_residual_le_1e6"] is True
    assert ac["mechanical_residual_le_1e4"] is True
    assert ac["kkt_feasibility_and_complementarity"] is True
    assert ac["correct_activation_and_release_on_shared_nodes"] is True
    assert ac["monotonic_committed_history"] is True
    assert ac["no_state_reset_across_increments"] is True
    assert ac["consistent_force_energy_damage_vs_reference"] is True


def test_governance_and_gate_status(audit_data):
    gov = audit_data["governance_and_gate_status"]
    assert gov["gate_c1_1_status"] == "QUALIFIED_OFFLINE_ONLY"
    assert gov["gate_c1_2_status"] == "NOT_QUALIFIED"
    assert gov["package94_status"] == "BENCHMARK-REPRODUCTION-ONLY"
    assert gov["hpc_submission_status"] == "WITHHELD_BY_POLICY"

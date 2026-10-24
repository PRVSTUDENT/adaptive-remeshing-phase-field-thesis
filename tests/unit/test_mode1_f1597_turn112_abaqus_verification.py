#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1597_turn112_abaqus_verification.py
Unit test suite for Turn 112: Genuine Abaqus 2023 Verification of Experimental Irreversible UEL.
Protocol Version: 2
"""
import json
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
AUDIT_JSON = REPO_ROOT / "results" / "validation" / "mode1_f1597" / "turn112_abaqus_verification_audit.json"
EXPECTED_PROD_UEL = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
EXPECTED_EXP_UEL = "55FF5D097F207340291BB1A26603B70AB1F105BE8458914809AF08476A8FA195"


@pytest.fixture(scope="module")
def audit_data():
    assert AUDIT_JSON.exists(), f"Audit deliverable missing: {AUDIT_JSON}"
    with open(AUDIT_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def test_audit_metadata(audit_data):
    assert audit_data["schema"] == 1
    assert audit_data["task_id"] == "F1597-CORRECT-PACKAGE72-STATE-TRANSFER"
    assert audit_data["turn"] == 112
    assert audit_data["production_uel_sha256"] == EXPECTED_PROD_UEL
    assert audit_data["production_uel_status"] == "BITWISE_FROZEN_UNCHANGED"
    assert audit_data["experimental_uel_sha256"] == EXPECTED_EXP_UEL


def test_checkA_damage_retention(audit_data):
    chk_a = audit_data["checkA_damage_retention"]
    assert chk_a["passed"] is True
    assert chk_a["healing_magnitude"] <= 1e-8
    assert chk_a["healing_criterion_le_1e8"] is True
    # All 4 elements sharing Node 5 must have average exactly 0.1875
    for elem, val in chk_a["measured_element_averages"].items():
        assert abs(val - 0.1875) < 1e-6


def test_checkB_damage_advancement(audit_data):
    chk_b = audit_data["checkB_damage_advancement"]
    assert chk_b["passed"] is True
    assert chk_b["minimum_damage_advance"] > 0.50
    assert chk_b["damage_within_bounds"] is True
    assert chk_b["active_set_release_confirmed"] is True


def test_energy_dissipation_monotonicity(audit_data):
    eng = audit_data["energy_dissipation_audit"]
    assert eng["strictly_monotonic_dissipation"] is True
    assert eng["stage_b_final_fracture_energy_kNmm"] > eng["stage_a_fracture_energy_kNmm"]


def test_acceptance_criteria(audit_data):
    ac = audit_data["acceptance_criteria_verification"]
    assert ac["uel_compilation_and_loading_pass"] is True
    assert ac["lower_bound_table_ingestion_pass"] is True
    assert ac["stage_a_damage_healing_le_1e8"] is True
    assert ac["stage_b_positive_damage_advancement"] is True
    assert ac["damage_within_0_1_bounds"] is True
    assert ac["free_phase_residual_le_1e6"] is True
    assert ac["mechanical_residual_le_1e4"] is True
    assert ac["kkt_feasibility_and_complementarity"] is True
    assert ac["monotonic_committed_history"] is True


def test_governance_and_gate_status(audit_data):
    gov = audit_data["governance_and_gate_status"]
    assert gov["gate_c1_1_status"] == "QUALIFIED_OFFLINE_ONLY"
    assert gov["gate_c1_2_status"] == "NOT_QUALIFIED"
    assert gov["production_uel_status"] == "100PCT_BITWISE_FROZEN"

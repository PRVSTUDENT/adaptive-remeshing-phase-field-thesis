#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1597_turn110_checkpoint_resolution.py
Unit test suite for Turn 110: Reconciling Turn 107 vs Turn 109 PDAS checkpoint discrepancy.
Protocol Version: 2
"""

import json
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
AUDIT_JSON = REPO_ROOT / "results" / "validation" / "mode1_f1597" / "turn110_pdas_checkpoint_resolution_audit.json"
EXPECTED_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"


@pytest.fixture(scope="module")
def audit_data():
    assert AUDIT_JSON.exists(), f"Audit file not found: {AUDIT_JSON}"
    with open(AUDIT_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def test_audit_metadata(audit_data):
    assert audit_data["schema"] == 1
    assert audit_data["task_id"] == "F1597-CORRECT-PACKAGE72-STATE-TRANSFER"
    assert audit_data["turn"] == 110
    assert audit_data["root_cause_summary"]["discrepancy_resolved"] is True


def test_config_A_state1_exact_parity(audit_data):
    cfg_a = audit_data["config_A_state1_benchmark_evaluation"]
    assert cfg_a["parity_verdict"] == "PERFECT_MATCH"
    assert cfg_a["max_nodal_discrepancy"] < 1e-7
    assert cfg_a["kkt_feasibility_pass"] is True
    assert cfg_a["lbfgs_min_healing"] >= -1e-8
    assert cfg_a["pdas_min_healing"] >= -1e-8
    assert cfg_a["pdas_min_dual_multiplier"] >= -1e-8
    assert cfg_a["pdas_iterations"] <= 2
    assert abs(cfg_a["lbfgs_d_max"] - cfg_a["pdas_d_max"]) < 1e-7


def test_config_B_sensitivity_reconciliation(audit_data):
    cfg_b = audit_data["config_B_state0_coupled_sensitivity"]
    assert cfg_b["sensitivity_verdict"] == "RECONCILED"
    # Verify initial mapped gradient residual was strictly below Turn 109's 1e-6 tolerance
    assert cfg_b["initial_state0_grad_inf_kN_mm"] < 1.0e-6
    assert cfg_b["turn109_clamped_nodes"] == 2752
    # Verify reconciled PDAS reaches the reference relaxation curve
    assert cfg_b["reconciled_pdas_d_max"] >= 0.65
    assert abs(cfg_b["rf2_parity_pct"]) < 1.0
    assert abs(cfg_b["reconciled_pdas_rf2_N"] - cfg_b["turn107_reference_rf2_N"]) < 1.0


def test_config_C_forward_continuation_parity(audit_data):
    cfg_c = audit_data["config_C_forward_continuation"]
    assert cfg_c["continuation_verdict"] == "PARITY_VERIFIED"
    assert cfg_c["delta_rf2_lbfgs_N"] < 0.0
    assert cfg_c["delta_rf2_pdas_N"] < 0.0
    assert cfg_c["delta_dmax_lbfgs"] > 0.0
    assert cfg_c["delta_dmax_pdas"] > 0.0
    assert cfg_c["rf2_discrepancy_N"] < 1.5
    assert cfg_c["dmax_discrepancy"] < 0.02


def test_abaqus_hpc_governance(audit_data):
    gov = audit_data["abaqus_hpc_governance"]
    assert gov["gate_c1_1_status"] == "QUALIFIED_OFFLINE"
    assert gov["gate_c1_2_status"] == "NOT_QUALIFIED"
    assert gov["package94_status"] == "BENCHMARK-REPRODUCTION-ONLY"
    assert gov["production_uel_sha256"] == EXPECTED_UEL_SHA256
    assert gov["hpc_submission_status"] == "WITHHELD_BY_POLICY"
    assert len(gov["blocking_architectural_defects"]) >= 4

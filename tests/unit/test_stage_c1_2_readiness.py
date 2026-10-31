# -*- coding: utf-8 -*-
"""Unit test for Stage C1-2 Forward Continuation Contract and Readiness Validator."""

import pytest
from scripts.validation.validate_method_c_stage_c1_2_contract import (
    evaluate_c1_1_checkpoint_for_c1_2,
    generate_stage_c1_2_specification,
    FROZEN_UEL_SHA256,
)


def test_stage_c1_2_spec_properties():
    spec = generate_stage_c1_2_specification(".")
    assert spec["schema"] == 1
    assert spec["stage"] == "Stage_C1_2_Forward_Continuation"
    assert spec["production_uel_sha256"] == FROZEN_UEL_SHA256
    assert spec["state_serialization"]["total_integration_points"] == 28224
    assert spec["state_serialization"]["total_nodes"] == 7266
    assert spec["state_serialization"]["total_elements"] == 7056
    assert spec["current_predecessor_status"]["r8_job_id"] == "1418939.mmaster02"
    assert spec["current_predecessor_status"]["stage_c1_2_dispatch"] == "STRICTLY_BLOCKED_PENDING_C1_1_ACCEPTANCE"


def test_evaluate_c1_1_checkpoint_blocked_on_failed_gates():
    dummy_failed = {
        "schema": 1,
        "history_semantics": "max(authentic transferred H0, frozen UEL POS_M at converged endpoint)",
        "displacement": [[i, 0.0, 0.0018] for i in range(1, 200)],
        "damage": [[i, 0.1] for i in range(1, 200)],
        "history": [[i, 1, 0.5] for i in range(1, 200)],
        "gates": {
            "pass_all": False,
            "gate_force": False,
            "gate_energy": True,
        }
    }
    result = evaluate_c1_1_checkpoint_for_c1_2(dummy_failed)
    assert result["continuation_eligible"] is False
    assert any("Physical gates not passed" in b for b in result["blockers"])


def test_evaluate_c1_1_checkpoint_pass_when_compliant():
    dummy_pass = {
        "schema": 1,
        "history_semantics": "max(authentic transferred H0, frozen UEL POS_M at converged endpoint)",
        "displacement": [[i, 0.0, 0.0018] for i in range(1, 200)],
        "damage": [[i, 0.25] for i in range(1, 200)],
        "history": [[i, 1, 0.5] for i in range(1, 200)],
        "gates": {
            "pass_all": True,
            "gate_force": True,
            "gate_energy": True,
            "gate_irreversibility": True,
            "gate_bounds": True
        }
    }
    result = evaluate_c1_1_checkpoint_for_c1_2(dummy_pass)
    assert result["continuation_eligible"] is True
    assert len(result["blockers"]) == 0

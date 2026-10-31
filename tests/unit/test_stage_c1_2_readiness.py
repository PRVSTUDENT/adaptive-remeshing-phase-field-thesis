# -*- coding: utf-8 -*-
"""Unit test for Stage C1-2 Forward Continuation Contract and Readiness Validator."""

import json
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.validation.validate_method_c_stage_c1_2_contract import (
    evaluate_c1_1_checkpoint_for_c1_2,
    generate_stage_c1_2_specification,
    FROZEN_UEL_SHA256,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_stage_c1_2_spec_properties():
    spec = generate_stage_c1_2_specification(".")
    assert spec["schema"] == 1
    assert spec["stage"] == "Stage_C1_2_Forward_Continuation"
    assert spec["production_uel_sha256"] == FROZEN_UEL_SHA256
    assert spec["state_serialization"]["total_integration_points"] == 28224
    assert spec["state_serialization"]["total_nodes"] == 7266
    assert spec["state_serialization"]["total_elements"] == 7056
    assert spec["current_predecessor_status"]["r8_job_id"] == "1418939.mmaster02"
    assert spec["current_predecessor_status"]["r8_c1_1_acceptance"] == "PASSED"
    assert spec["current_predecessor_status"]["stage_c1_2_dispatch"] == "ELIGIBLE_FOR_FORWARD_CONTINUATION_PREPARATION"


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


def test_evaluate_authentic_r8_checkpoint():
    cp_path = REPO_ROOT / "results" / "validation" / "package148" / "r8_equilibrium_checkpoint.json"
    rep_path = REPO_ROOT / "results" / "validation" / "package148" / "r8_runtime_report.json"
    if not cp_path.is_file() or not rep_path.is_file():
        pytest.skip("R8 checkpoint files not yet downloaded locally")

    with open(str(cp_path), "r") as f:
        checkpoint = json.load(f)
    with open(str(rep_path), "r") as f:
        report = json.load(f)

    result = evaluate_c1_1_checkpoint_for_c1_2(checkpoint, report)
    assert result["continuation_eligible"] is True
    assert result["evaluated_node_count"] == 7265
    assert result["evaluated_gp_count"] == 28224
    assert len(result["blockers"]) == 0

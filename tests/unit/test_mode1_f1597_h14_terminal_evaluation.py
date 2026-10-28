# -*- coding: utf-8 -*-
"""
tests/unit/test_mode1_f1597_h14_terminal_evaluation.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Unit test suite for Package 129 R1 H14 terminal evaluation and falsification findings.
"""

import os
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
EVAL_JSON = os.path.join(REPO_ROOT, "results", "validation", "package129_r1_h14_terminal_evaluation.json")

@pytest.fixture(scope="module")
def eval_data():
    assert os.path.isfile(EVAL_JSON), f"Missing evaluation file: {EVAL_JSON}"
    with open(EVAL_JSON, "r") as f:
        return json.load(f)

def test_evaluation_schema_and_verdict(eval_data):
    assert eval_data.get("schema") == 1
    assert eval_data.get("task_id") == "F1597-CORRECT-PACKAGE72-STATE-TRANSFER"
    assert eval_data.get("job_id") == "1418403.mmaster02"
    assert eval_data.get("verdict") == "H14_FAILED_NONSTATIONARY"

def test_first_25_cycles_bit_exact_parity(eval_data):
    parity = eval_data.get("parity_cycles_1_to_25", {})
    assert parity.get("first_25_cycles_bit_exact_parity") is True
    assert parity.get("max_rf2_discrepancy_N") == 0.0
    assert parity.get("max_active_nodes_discrepancy") == 0

def test_critical_slowing_down_falsified(eval_data):
    csd = eval_data.get("critical_slowing_down_falsification", {})
    assert csd.get("actual_cycles_completed") == 65
    assert csd.get("min_delta_d_cycle") == 30
    assert csd.get("min_delta_d_achieved") < csd.get("cycle_25_delta_d")
    assert csd.get("cycle_65_delta_d") > csd.get("cycle_25_delta_d")
    # Verify expansion from cycle 30 to 65
    assert csd.get("cycle_65_delta_d") > 0.0050

def test_quantitative_kkt_and_physics(eval_data):
    audit = eval_data.get("quantitative_criteria_audit", {})
    assert audit.get("healing_violations_passed") is True
    assert audit.get("healing_violations") == 0
    assert audit.get("free_phase_residual_passed") is True
    assert audit.get("free_phase_residual_kN_mm") <= 1.0e-6
    assert audit.get("active_multiplier_passed") is True
    assert audit.get("active_multiplier_min_kN_mm") >= -1.0e-9
    assert audit.get("stationarity_passed") is False
    assert audit.get("rf2_parity_passed") is False # 5.29% > 5.0%

def test_governance_gate_binding(eval_data):
    gate = eval_data.get("governance_gate", {})
    assert gate.get("status") == "STAGE_C1_2_STEP2_ENERGY_GATE_FAILED"
    assert gate.get("binding") is True

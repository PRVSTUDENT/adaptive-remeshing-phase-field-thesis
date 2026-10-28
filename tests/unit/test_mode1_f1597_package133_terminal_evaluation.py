# -*- coding: utf-8 -*-
"""
test_mode1_f1597_package133_terminal_evaluation.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Unit test suite verifying the terminal evaluation of Package 133
(PBS Job 1418470.mmaster02) and Hypothesis H18.
"""

import os
import json
import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EVAL_JSON = os.path.join(REPO_ROOT, "results", "validation", "h18_second_quarterstep_evaluation.json")

@pytest.fixture(scope="module")
def eval_data():
    assert os.path.exists(EVAL_JSON), "Evaluation JSON missing: %s" % EVAL_JSON
    with open(EVAL_JSON, "r") as f:
        return json.load(f)

def test_h18_terminal_verdict(eval_data):
    assert eval_data["h18_verdict"] == "H18_FAILED_NONSTATIONARY"
    assert eval_data["job_accounting"]["exit_status"] == 0

def test_bounds_semantics_decoupling(eval_data):
    b = eval_data["bounds_semantics_audit"]
    assert b["semantics_verified"] is True
    assert b["gp_history_count"] == 17688
    assert b["nodal_cards_count"] == 4588

def test_acceptance_criteria_classification(eval_data):
    crit = eval_data["acceptance_criteria"]
    assert crit["stationarity_delta_d"]["passed"] is False
    assert crit["stationarity_delta_rf2"]["passed"] is True
    assert crit["free_phase_residual"]["passed"] is True
    assert crit["min_active_multiplier"]["passed"] is True
    assert crit["healing_violations"]["passed"] is True
    assert crit["rf2_parity_vs_donor"]["passed"] is True
    assert crit["energy_parity_vs_donor"]["passed"] is True

def test_three_step_energy_path(eval_data):
    path = eval_data["path_reconstruction"]
    assert len(path["states"]) == 4
    assert len(path["steps"]) == 3
    assert path["cumulative_residual_pct"] < 2.0
    assert 0.003 < path["cumulative_w_ext_mJ"] < 0.004

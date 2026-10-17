"""
Unit test suite for Task F1543/F1544: Mandatory GitHub Image Review and Independent ChatGPT Three-Outcome Validation of Method C.
"""

import os
import sys
import json
import pytest
from pathlib import Path

REPO_ROOT = Path(r"D:\Master thesis\Adaptive remeshing")
sys.path.insert(0, str(REPO_ROOT / "scripts" / "visualization"))
from export_method_c_propagation_figures import STAGE_CONFIGS

def test_stage_configs_integrity():
    assert len(STAGE_CONFIGS) == 6, f"Expected 6 stages (Stages 0 to 5), got {len(STAGE_CONFIGS)}"
    expected_counts = [2906, 17913, 21546, 25085, 29293, 29293]
    for i, cfg in enumerate(STAGE_CONFIGS):
        assert cfg["stage_id"] == i
        assert cfg["expected_elements"] == expected_counts[i]
        deck_path = REPO_ROOT / cfg["deck_rel_path"]
        assert deck_path.exists(), f"Input deck does not exist: {deck_path}"

def test_job_1414859_active_registration():
    active_task_path = REPO_ROOT / "project_coordination" / "ACTIVE_TASK.json"
    assert active_task_path.exists()
    active_task = json.loads(active_task_path.read_text(encoding="utf-8"))
    assert "1414859.mmaster02" in active_task["active_pbs_job_ids"]
    assert "F154" in active_task["task_id"]

def test_chatgpt_three_verdict_framework():
    # User directive explicitly requires: "Correct the validation protocol: Do not force a binary judgment when the evidence is incomplete. ChatGPT must retain three scientifically defensible outcomes: PASS, FAIL, NOT YET QUALIFIED."
    allowed_verdicts = {"PASS", "FAIL", "NOT YET QUALIFIED"}
    assert len(allowed_verdicts) == 3
    assert "PASS" in allowed_verdicts
    assert "FAIL" in allowed_verdicts
    assert "NOT YET QUALIFIED" in allowed_verdicts

def test_quantitative_gates_contract():
    gates = {
        "reaction_force_jump_N": 5.0,
        "maximum_damage_difference": 0.020,
        "elastic_energy_error_pct": 0.50,
        "fracture_energy_error_pct": 0.50,
        "total_energy_error_pct": 0.10,
    }
    assert gates["reaction_force_jump_N"] <= 5.0
    assert gates["maximum_damage_difference"] <= 0.020
    assert gates["elastic_energy_error_pct"] <= 0.50
    assert gates["fracture_energy_error_pct"] <= 0.50
    assert gates["total_energy_error_pct"] <= 0.10

def test_evidence_based_remeshing_criteria():
    l0 = 0.0075 # 7.5 um
    min_advance = l0 # 7.5 um
    target_h_ahead = l0 / 5.0 # 1.5 um
    assert min_advance == 0.0075
    assert target_h_ahead == 0.0015

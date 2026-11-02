# -*- coding: utf-8 -*-
"""
test_package163_c5_continuation_acceptance.py
Unit tests for Package 163 Stage C2-1 Physical Acceptance Evaluator.
Task: F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE
Protocol Version: 2
"""

import copy
import json
import math
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.validation.evaluate_package163_c5_continuation_acceptance import (
    Package163AcceptanceEvaluator,
    ACCEPTED_CHECKPOINT_01_SHA256,
    BASELINE_UY_MM, TARGET_UY_MM, TARGET_INCREMENT_MM,
    C4_R6_REFERENCE_FORCE_KN, C4_R6_REFERENCE_TOTAL_ENERGY_KNMM,
    TOTAL_C5_NODES, TOTAL_C5_GPS
)

P166_EVIDENCE_DIR = REPO_ROOT / "models/pandey_kumar_mode1/166_c5_package166_r3_c2_0_nonaccumulating_history/evidence/1419485.mmaster02"
AUTHENTIC_CHKPT_01_PATH = P166_EVIDENCE_DIR / "converged_checkpoint_01.json"


def create_synthetic_c5_checkpoints():
    """Generates synthetic Checkpoint 01 (C2-0) and Checkpoint 02 (C2-1)."""
    disp1 = [[nid, 0.0, BASELINE_UY_MM * (nid / float(TOTAL_C5_NODES))] for nid in range(1, TOTAL_C5_NODES + 1)]
    disp2 = [[nid, 0.0, TARGET_UY_MM * (nid / float(TOTAL_C5_NODES))] for nid in range(1, TOTAL_C5_NODES + 1)]

    dam1 = [[nid, min(0.95, 0.05 + 0.9 * (nid / float(TOTAL_C5_NODES)))] for nid in range(1, TOTAL_C5_NODES + 1)]
    dam2 = [[nid, min(0.96, dam1[nid - 1][1] + 0.0005 * (nid / float(TOTAL_C5_NODES)))] for nid in range(1, TOTAL_C5_NODES + 1)]

    hist1 = []
    hist2 = []
    for eid in range(1, 12997):
        for g in range(1, 5):
            h_val = 0.01 * (eid % 50 + g)
            hist1.append([eid, g, h_val])
            hist2.append([eid, g, h_val + 0.0001])

    c1 = {
        "schema": 1,
        "stage": "C2-0",
        "step": 1,
        "target_uy_mm": BASELINE_UY_MM,
        "outer_iteration": 69,
        "coupled_convergence": True,
        "reaction_force_kN": 0.180767,
        "total_energy_kNmm": 0.000224572,
        "displacement": disp1,
        "damage": dam1,
        "history": hist1
    }

    c2 = {
        "schema": 1,
        "stage": "C2-1",
        "step": 1,
        "target_uy_mm": TARGET_UY_MM,
        "outer_iteration": 42,
        "coupled_convergence": True,
        "reaction_force_kN": C4_R6_REFERENCE_FORCE_KN * 1.005,  # 0.5% drift
        "total_energy_kNmm": C4_R6_REFERENCE_TOTAL_ENERGY_KNMM * 1.003, # 0.3% drift
        "displacement": disp2,
        "damage": dam2,
        "history": hist2
    }
    return c1, c2


def test_predecessor_binding_acceptance():
    evaluator = Package163AcceptanceEvaluator()
    if AUTHENTIC_CHKPT_01_PATH.is_file():
        res = evaluator.validate_predecessor_binding(AUTHENTIC_CHKPT_01_PATH)
        assert res["passed"] is True
        assert res["actual_sha256"] == ACCEPTED_CHECKPOINT_01_SHA256


def test_checkpoint_continuity_validation():
    evaluator = Package163AcceptanceEvaluator()
    c1, c2 = create_synthetic_c5_checkpoints()

    res = evaluator.validate_checkpoint_continuity(c1, c2)
    assert res["passed"] is True
    assert math.isclose(res["increment_mm"], 5.0e-6, rel_tol=1e-12)

    # Rejection of wrong stage
    bad_c2 = copy.deepcopy(c2)
    bad_c2["stage"] = "C2-0"
    res = evaluator.validate_checkpoint_continuity(c1, bad_c2)
    assert res["passed"] is False

    # Rejection of wrong displacement advancement
    bad_c2 = copy.deepcopy(c2)
    bad_c2["target_uy_mm"] = 0.001870
    res = evaluator.validate_checkpoint_continuity(c1, bad_c2)
    assert res["passed"] is False


def test_coupled_convergence_evaluation():
    evaluator = Package163AcceptanceEvaluator()
    passing_telemetry = [{
        "outer": 42,
        "delta_d": 4.5e-6,
        "delta_u": 2.1e-10,
        "delta_h": 1.2e-5,
        "free_error": 1.5e-9,
        "dual_error": 3.2e-9
    }]
    res = evaluator.evaluate_coupled_convergence(passing_telemetry)
    assert res["passed"] is True

    failing_telemetry = [{
        "outer": 42,
        "delta_d": 3.5e-5,  # exceeds 1.0e-5
        "delta_u": 2.1e-10,
        "delta_h": 1.2e-5,
        "free_error": 1.5e-9,
        "dual_error": 3.2e-9
    }]
    res = evaluator.evaluate_coupled_convergence(failing_telemetry)
    assert res["passed"] is False


def test_pointwise_irreversibility_and_bounds():
    evaluator = Package163AcceptanceEvaluator()
    d1 = {i: 0.5 for i in range(1, TOTAL_C5_NODES + 1)}
    d2 = {i: 0.501 for i in range(1, TOTAL_C5_NODES + 1)}

    res = evaluator.evaluate_pointwise_irreversibility(d1, d2)
    assert res["passed"] is True
    assert res["healing_violations_count"] == 0

    # Test healing detection
    d2_healing = dict(d2)
    d2_healing[10] = 0.49  # drop of 0.01 > 1e-6
    res = evaluator.evaluate_pointwise_irreversibility(d1, d2_healing)
    assert res["passed"] is False
    assert res["healing_violations_count"] == 1

    # Test bound violation
    d2_oob = dict(d2)
    d2_oob[20] = 1.05  # > 1.0
    res = evaluator.evaluate_pointwise_irreversibility(d1, d2_oob)
    assert res["passed"] is False
    assert res["out_of_bounds_count"] == 1


def test_history_monotonicity():
    evaluator = Package163AcceptanceEvaluator()
    h1 = {(e, g): 1.0 for e in range(1, 12997) for g in range(1, 5)}
    h2 = {(e, g): 1.005 for e in range(1, 12997) for g in range(1, 5)}

    res = evaluator.evaluate_history_monotonicity(h1, h2)
    assert res["passed"] is True
    assert res["history_violations_count"] == 0

    # Test monotonicity violation
    h2_drop = dict(h2)
    h2_drop[(1, 1)] = 0.95
    res = evaluator.evaluate_history_monotonicity(h1, h2_drop)
    assert res["passed"] is False
    assert res["history_violations_count"] == 1


def test_c4_r6_reference_parity():
    evaluator = Package163AcceptanceEvaluator()
    rf_actual = C4_R6_REFERENCE_FORCE_KN * 1.01  # +1.0% drift (<= 2%)
    e_actual = C4_R6_REFERENCE_TOTAL_ENERGY_KNMM * 0.995 # -0.5% drift (<= 2%)

    res = evaluator.evaluate_reference_parity(rf_actual, e_actual)
    assert res["passed"] is True
    assert res["rf2_pass"] is True
    assert res["total_energy_pass"] is True

    # Test drift > 2%
    rf_bad = C4_R6_REFERENCE_FORCE_KN * 1.03  # +3% drift
    res = evaluator.evaluate_reference_parity(rf_bad, e_actual)
    assert res["passed"] is False
    assert res["rf2_pass"] is False


def test_state_progression_metrics():
    evaluator = Package163AcceptanceEvaluator()
    c1, c2 = create_synthetic_c5_checkpoints()

    res = evaluator.evaluate_c5_state_progression(c1, c2)
    assert res["delta_force_kN"] > 0.0
    assert res["delta_energy_kNmm"] > 0.0
    assert res["delta_max_damage"] >= 0.0
    assert res["advancing_nodes_count"] > 0


def test_full_acceptance_decision_synthetic():
    evaluator = Package163AcceptanceEvaluator()
    c1, c2 = create_synthetic_c5_checkpoints()
    telemetry = [{
        "outer": 42,
        "delta_d": 4.5e-6,
        "delta_u": 2.1e-10,
        "delta_h": 1.2e-5,
        "free_error": 1.5e-9,
        "dual_error": 3.2e-9
    }]

    result = evaluator.evaluate_full_acceptance(c1, c2, telemetry)
    assert result["physical_acceptance_decision"] == "METHOD_C_CYCLE_PHYSICAL_PASS"
    assert result["verification_passed"] is True

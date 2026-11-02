# -*- coding: utf-8 -*-
"""
test_c2_2_submission_gates_and_forecast.py
Unit tests for explicit C2-2 submission gate evaluation and live telemetry forecast.
Task: F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE
Protocol Version: 2
"""

import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.validation.check_c2_2_submission_gates import evaluate_submission_gates
from scripts.validation.analyze_package163_r2_live_progress import (
    analyze_live_telemetry, ASYMPTOTIC_RHO_ESTIMATE
)


def test_submission_gates_running_job_contradiction_resolution():
    res = evaluate_submission_gates("1419489.mmaster02")
    assert res["eligible_for_immediate_submission"] is False
    assert res["overall_status"] == "SUBMISSION_BLOCKED_BY_PREDECESSOR_DEPENDENCY"
    assert res["blocking_gate"] == "GATE_1_PREDECESSOR_CHECKPOINT_02"
    assert res["gates"]["GATE_1_PREDECESSOR_CHECKPOINT_02"]["status"] == "BLOCKED"
    assert res["gates"]["GATE_2_C5_MESH_INTEGRITY"]["status"] == "PASS"
    assert res["gates"]["GATE_3_FROZEN_UEL_SHA256"]["status"] == "PASS"
    assert res["gates"]["GATE_6_ONCE_ONLY_QUOTA"]["status"] == "ELIGIBLE"
    assert res["gates"]["GATE_7_PHYSICAL_ACCEPTANCE_CRITERIA"]["status"] == "PASS"


def test_asymptotic_convergence_forecast():
    # Sample mock telemetry up to outer 37
    mock_telemetry = [
        {"outer": 1, "pdas_active_count": 13125, "dual_error": 8.5e-9, "free_error": 0.0, "delta_d": 0.00045, "delta_u": 1e-7, "delta_h": 0.01},
        {"outer": 37, "pdas_active_count": 7561, "dual_error": 1.88e-8, "free_error": 3.20e-9, "delta_d": 0.00107, "delta_u": 2.77e-7, "delta_h": 0.0234}
    ]
    analysis = analyze_live_telemetry(mock_telemetry)
    assert analysis["current_outer_iteration"] == 37
    assert analysis["active_set_pruning"]["pruning_reduction_pct"] > 40.0
    assert analysis["kkt_residuals"]["dual_error_satisfied"] is True
    assert analysis["kkt_residuals"]["free_residual_satisfied"] is True
    forecast = analysis["asymptotic_convergence_forecast"]
    assert forecast["projected_outer_delta_d_tol"] == pytest.approx(149.1, abs=1.0)
    assert forecast["budget_outer_ceiling"] == 200
    assert "SCIENTIFIC DISTINCTION" in forecast["distinction_note"]

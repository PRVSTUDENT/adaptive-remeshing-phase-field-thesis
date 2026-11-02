"""Unit tests for Mode-I Stage C2-1 convergence recovery strategy qualification."""

import json
import math
from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from scripts.validation.investigate_convergence_recovery_strategy import (
    calculate_contraction_rate,
    project_iterations_to_tolerance,
)

FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
CHECKPOINT_01_SHA256 = "DCFD31186061FA81111DA18071CF8ADFB9BAF2C5CB343CB60F08416741C1B64A"


def test_contraction_rate_calculation():
    """Verify geometric contraction rate estimation on known synthetic decay."""
    rho_true = 0.95
    vals = [1.0 * (rho_true ** i) for i in range(25)]
    rho_est, start, end = calculate_contraction_rate(vals, window=20)
    assert math.isclose(rho_est, rho_true, rel_tol=1e-5)
    assert math.isclose(start, vals[-20], rel_tol=1e-5)
    assert math.isclose(end, vals[-1], rel_tol=1e-5)


def test_iteration_projection():
    """Verify projection calculation against analytical logarithmic formula."""
    current_val = 1.0e-7
    target_tol = 1.0e-9
    rho = 0.97
    expected_n = int(math.ceil(math.log(target_tol / current_val) / math.log(rho)))
    projected_n = project_iterations_to_tolerance(current_val, target_tol, rho)
    assert projected_n == expected_n
    assert projected_n > 0

    # Already converged case
    assert project_iterations_to_tolerance(1.0e-10, target_tol, rho) == 0


def test_convergence_recovery_investigation_artifact():
    """Verify structure and contents of the Turn 32 investigation artifact."""
    artifact_path = Path("results/validation/convergence_recovery_investigation_turn32.json")
    assert artifact_path.exists(), "Artifact results/validation/convergence_recovery_investigation_turn32.json must exist"

    with open(artifact_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data.get("schema") == 1
    assert data.get("investigation_type") == "CONVERGENCE_RECOVERY_STRATEGY_ASSESSMENT"

    p163 = data.get("job_1419489_p163_r2", {})
    assert p163.get("latest_outer") >= 180
    assert 0.95 < p163.get("rho_u_20iter") < 0.99
    assert 0.95 < p163.get("rho_h_20iter") < 0.99
    assert p163.get("simultaneous_projected_outer") > 200
    assert p163.get("budget_exceeded_risk") is True

    p157 = data.get("job_1419490_p157_r8", {})
    assert p157.get("latest_outer") >= 3
    assert p157.get("active_contraction") is True


def test_strategy_comparison_and_qualification():
    """Verify that Strategy 2 is qualified and Strategy 1 is disqualified."""
    artifact_path = Path("results/validation/convergence_recovery_investigation_turn32.json")
    with open(artifact_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    strategies = data.get("strategies", {})
    s1 = strategies.get("strategy_1_intermediate_hot_restart", {})
    s2 = strategies.get("strategy_2_clean_300_outer_contingency", {})

    # Strategy 1 verification
    assert s1.get("driver_support") is False
    assert "DISQUALIFIED" in s1.get("recommendation")
    assert len(s1.get("technical_risks", [])) >= 3

    # Strategy 2 qualification
    assert s2.get("driver_support") is True
    assert s2.get("frozen_uel_sha256") == FROZEN_UEL_SHA256
    assert CHECKPOINT_01_SHA256 in s2.get("initial_state")
    assert s2.get("estimated_walltime_hours") < 4.0
    assert s2.get("walltime_ceiling_hours") == 8.0
    assert s2.get("walltime_headroom_hours") > 4.0
    assert "QUALIFIED" in s2.get("recommendation")

"""
Unit Test Suite: Mode-I R4 Convergence Rate Diagnostics and Iteration Budget
=============================================================================
Verifies the empirical findings from:
  - scripts/validation/audit_r4_convergence_rate_diagnostics.py
  - results/validation/r4_convergence_rate_diagnostics.json
"""

import json
from pathlib import Path
import pytest

DIAGNOSTICS_PATH = Path("results/validation/r4_convergence_rate_diagnostics.json")


@pytest.fixture(scope="module")
def diagnostics():
    assert DIAGNOSTICS_PATH.exists(), f"Diagnostics artifact not found at {DIAGNOSTICS_PATH}"
    with open(DIAGNOSTICS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_diagnostics_artifact_schema_and_integrity(diagnostics):
    assert diagnostics["schema"] == 1
    assert "audit_name" in diagnostics
    assert "comparisons" in diagnostics
    assert "budget_feasibility" in diagnostics
    assert "classification_summary" in diagnostics
    assert "falsifiable_hypothesis" in diagnostics


def test_r4_step1_contraction_ratio_and_truncation(diagnostics):
    r4_s1 = diagnostics["comparisons"]["r4_step1_10nm_rejected_trial"]
    assert r4_s1["total_outers"] == 50
    assert r4_s1["converged"] is False

    metrics = r4_s1["metrics"]
    # Final delta d passed the 1e-5 limit
    assert metrics["final_delta_d"] <= 1e-5
    # Final delta u and delta H were just above their strict thresholds
    assert metrics["final_delta_u"] > 1e-9
    assert metrics["final_delta_u"] < 1e-8
    assert metrics["final_delta_h"] > 1e-6
    assert metrics["final_delta_h"] < 1e-3

    # Check geometric contraction stability
    mean_rho = metrics["mean_tail_rho_h"]
    std_rho = metrics["std_tail_rho_h"]
    assert 0.87 <= mean_rho <= 0.89
    assert std_rho < 0.005  # Extremely steady

    # Check projection
    proj_h = metrics["projected_outers_to_delta_h_target"]
    assert 80 <= proj_h <= 100
    assert r4_s1["classification"] == "ITERATION_CAP_LIMITED"


def test_r3_step1_outer50_unconverged_baseline(diagnostics):
    r3_s1 = diagnostics["comparisons"]["r3_step1_50nm_converged"]
    assert r3_s1["converged"] is True
    assert r3_s1["total_outers"] == 74

    outer50 = r3_s1["outer_50_status"]
    assert outer50["passed_at_outer_50"] is False
    assert outer50["delta_h"] > 1e-6
    assert outer50["delta_u"] > 1e-9


def test_r3_step2_divergence_vs_r4_step1_contraction(diagnostics):
    r3_s2 = diagnostics["comparisons"]["r3_step2_50nm_diverged"]
    assert r3_s2["converged"] is False
    assert r3_s2["max_delta_h"] > 100.0  # Exploded
    assert r3_s2["classification"] == "NONLINEAR_DIVERGENCE"

    # Contrast with R4 Step 1
    r4_s1 = diagnostics["comparisons"]["r4_step1_10nm_rejected_trial"]
    assert r4_s1["metrics"]["final_delta_h"] < 1e-3
    assert r4_s1["contraction_stability"]["divergence_detected"] is False
    assert r4_s1["contraction_stability"]["stagnation_detected"] is False


def test_r4_step2_subdivision_reduction(diagnostics):
    r4_s2 = diagnostics["comparisons"]["r4_step2_5nm_active_bisection"]
    red = r4_s2["initial_perturbation_reduction"]
    # Halving the increment halved initial delta H by > 45%
    assert red["reduction_fraction"] > 0.45

    metrics = r4_s2["metrics"]
    assert metrics["mean_tail_rho_h"] < 0.88
    # Projected outers should be less than Step 1
    assert metrics["projected_outers_to_delta_h_target"] < diagnostics["comparisons"]["r4_step1_10nm_rejected_trial"]["metrics"]["projected_outers_to_delta_h_target"]


def test_walltime_budget_feasibility(diagnostics):
    feas = diagnostics["budget_feasibility"]
    assert feas["feasibility_verdict"] == "HIGHLY_FEASIBLE"
    assert feas["walltime_at_100_outers_min"] <= 120.0  # <= 2 hours
    assert feas["pbs_walltime_headroom_at_100_outers_hours"] >= 6.0  # > 6 hours headroom
    assert feas["pbs_walltime_limit_hours"] == 8.0


def test_classification_summary_and_hypothesis(diagnostics):
    summary = diagnostics["classification_summary"]
    assert summary["primary_classification"] == "ITERATION_CAP_LIMITED"
    assert summary["secondary_classification"] == "SUBDIVISION_HELPFUL"
    assert summary["stagnation_detected"] is False
    assert summary["divergence_detected"] is False

    hyp = diagnostics["falsifiable_hypothesis"]
    assert len(hyp) >= 50
    assert "max_outer" in hyp
    assert "geometric contraction" in hyp
    assert "1e-6 MPa" in hyp

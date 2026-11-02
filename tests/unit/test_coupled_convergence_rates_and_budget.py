"""Unit test verifying simultaneous coupled convergence metrics, contraction rates, and budget feasibility.
Task: F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE
Protocol Version: 2
"""

import json
import math
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
EVAL_PATH = REPO_ROOT / "results" / "validation" / "coupled_convergence_evaluation_turn31.json"


def test_coupled_convergence_evaluation_artifact_exists():
    assert EVAL_PATH.is_file(), f"Missing evaluation file: {EVAL_PATH}"
    with open(EVAL_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["schema"] == 1
    assert data["evaluation"] == "COUPLED_CONVERGENCE_ASSESSMENT_TURN31"
    assert "package163_r2" in data
    assert "package157_r8" in data


def test_r2_coupled_residuals_and_contraction_rates():
    with open(EVAL_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    r2 = data["package163_r2"]
    curr = r2["current_residuals"]
    outer = r2["current_outer"]

    assert outer >= 164
    assert curr["delta_u_mm"] <= 6.0e-09
    assert curr["delta_h_MPa"] <= 6.0e-04
    assert curr["dual_error_kNmm"] < 1.0e-06
    assert curr["free_error_kN"] < 1.0e-06

    rates = r2["contraction_rates"]
    assert rates["robust_rho_u"] == pytest.approx(0.9730, rel=1e-2)
    assert rates["robust_rho_h"] == pytest.approx(0.9726, rel=1e-2)


def test_budget_feasibility_and_projection():
    with open(EVAL_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    r2 = data["package163_r2"]
    proj = r2["coupled_convergence_projection"]
    curr = r2["current_residuals"]
    tol = r2["tolerances"]

    # At current outer, delta_u and delta_H are ~3.5x to ~5x above tolerance
    ratio_u = curr["delta_u_mm"] / tol["tol_u_mm"]
    ratio_h = curr["delta_h_MPa"] / tol["tol_h_MPa"]
    assert ratio_u > 3.0
    assert ratio_h > 3.0

    # Target outer under steady rate ~0.973 is > 200
    assert proj["simultaneous_outer_target"] > 200
    assert proj["budget_sufficient"] is False

    # Values at outer 200 remain ~2x above threshold under unaccelerated rate
    assert proj["projected_delta_u_at_200_mm"] > 1.0e-09
    assert proj["projected_delta_h_at_200_MPa"] > 1.0e-04


def test_package167_gates_held_pending_running_jobs():
    with open(EVAL_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # R2 is in progress, Checkpoint 02 does not exist yet
    assert data["package163_r2"]["coupled_status"] == "IN_PROGRESS"

    # R8 is in progress, C4 reference is not yet physically accepted
    assert data["package157_r8"]["latest_outer"] >= 1

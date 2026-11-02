# -*- coding: utf-8 -*-
"""
test_c2_2_preparation_and_fallback.py
Unit tests for Stage C2-2 specification, ambiguity resolution, and no-submission fallback.
Task: F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE
Protocol Version: 2
"""

import json
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.stage_c2_2_specification import (
    get_c2_2_specification,
    evaluate_c2_2_submission_eligibility,
    STAGE_NAME, MESH_STAGE,
    TOTAL_C5_ELEMENTS, TOTAL_C5_NODES, TOTAL_C5_GPS, TOTAL_C5_SVARS,
    BASELINE_UY_MM, INCREMENT_UY_MM, TARGET_UY_MM,
    MAX_OUTER_ITERATIONS, FROZEN_UEL_SHA256
)


def test_c2_2_specification_invariants():
    spec = get_c2_2_specification()
    assert spec["stage"] == STAGE_NAME
    assert spec["mesh"] == MESH_STAGE
    assert spec["discretization"]["elements"] == 12996
    assert spec["discretization"]["nodes"] == 13278
    assert spec["discretization"]["gauss_points"] == 51984
    assert spec["discretization"]["history_svars"] == 207936


def test_c2_2_load_schedule():
    spec = get_c2_2_specification()
    load = spec["load_schedule"]
    assert load["initial_uy_mm"] == pytest.approx(0.0018653125442191958, abs=1e-12)
    assert load["increment_uy_mm"] == pytest.approx(0.000005, abs=1e-12)
    assert load["target_uy_mm"] == pytest.approx(0.0018703125442191958, abs=1e-12)
    assert load["initial_uy_mm"] + load["increment_uy_mm"] == pytest.approx(load["target_uy_mm"], abs=1e-12)


def test_c2_2_solver_parameters():
    spec = get_c2_2_specification()
    solver = spec["solver"]
    assert solver["max_outer_iterations"] == 200
    assert solver["delta_d_tol"] == 1.0e-5
    assert solver["delta_u_tol_mm"] == 1.0e-9
    assert solver["delta_h_tol_MPa"] == 1.0e-4
    assert solver["free_residual_tol_kN"] == 1.0e-6
    assert solver["dual_error_tol_kNmm"] == 1.0e-6
    assert solver["healing_tolerance"] == 1.0e-6
    assert spec["frozen_uel_sha256"] == "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"


def test_no_submission_fallback_while_r2_running():
    """
    While Job 1419489.mmaster02 is running on cluster, Checkpoint 02 does not exist locally.
    Submission eligibility MUST evaluate to False with status NO_SUBMISSION_FALLBACK.
    """
    eligibility = evaluate_c2_2_submission_eligibility()
    assert eligibility["eligible_for_submission"] is False
    assert eligibility["status"] == "NO_SUBMISSION_FALLBACK"
    assert eligibility["block_reason"] == "PREDECESSOR_CHECKPOINT_02_MISSING"
    assert eligibility["running_predecessor_job_id"] == "1419489.mmaster02"
    assert "Stage C2-2 forward continuation strictly requires" in eligibility["explanation"]

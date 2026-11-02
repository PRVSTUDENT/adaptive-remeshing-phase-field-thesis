# -*- coding: utf-8 -*-
"""
test_package163_r2_trajectory_analysis.py
Unit tests for Package 163-R2 live trajectory and transient investigation.
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

from scripts.validation.fetch_and_analyze_r2_telemetry import analyze_trajectory

ANALYSIS_PATH = REPO_ROOT / "results/validation/package163_r2_trajectory_analysis_turn22.json"
TELEMETRY_PATH = REPO_ROOT / "results/validation/package163_r2_live_telemetry_turn22.json"


def test_trajectory_analysis_artifact_exists():
    assert ANALYSIS_PATH.exists()
    assert TELEMETRY_PATH.exists()


def test_trajectory_analysis_metrics():
    data = json.loads(ANALYSIS_PATH.read_text(encoding="utf-8"))
    assert data["job_id"] == "1419489.mmaster02"
    assert data["total_saved_iterations"] >= 45

    # Active set pruning
    asp = data["active_set_pruning_dynamics"]
    assert asp["strictly_monotonic_pruning"] is True
    assert asp["oscillation_detected"] is False
    assert asp["pruning_percentage"] > 50.0

    # KKT residuals
    kkt = data["kkt_residuals"]
    assert kkt["all_iterations_pass_dual_tol"] is True
    assert kkt["all_iterations_pass_free_tol"] is True

    # Transient investigation
    ti = data["transient_investigation"]
    assert ti["mechanism"] == "ACTIVE_SET_REDISTRIBUTION_TRANSIENT"
    assert ti["delta_u_current"]["trend"] == "DECREASING_SINCE_PEAK"
    assert ti["delta_h_current"]["trend"] == "DECREASING_SINCE_PEAK"
    assert 0.90 < ti["delta_u_recent_contraction_rate"] < 1.00
    assert 0.90 < ti["delta_h_recent_contraction_rate"] < 1.00

    # Budget assessment
    cba = data["convergence_and_budget_assessment"]
    assert cba["persistent_nonconvergence_evidence"] is False
    assert cba["budget_outer_ceiling"] == 200

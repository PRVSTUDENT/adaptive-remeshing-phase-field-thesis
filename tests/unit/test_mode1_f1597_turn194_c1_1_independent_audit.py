#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1597_turn194_c1_1_independent_audit.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER (Turn 194)
Protocol Version: 2

Independent unit test suite verifying:
1. Classification of Package 110 (Job 1417601) as C1_1_PREMATURE_AM_TERMINATION.
2. Energy reconciliation against authentic R22 donor benchmark (0.238324 mJ).
3. Terminal non-stationarity: Delta d_max = 0.01315 > 1e-3, Delta RF2 = -0.851 N > 0.1 N.
4. Pointwise irreversibility (0 healing nodes) and monotonic dissipation across all cycles.
5. Corrective action formulation for dynamic fixed-point convergence.
"""

import json
from pathlib import Path
import pytest

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
AUDIT_PATH = REPO_ROOT / "results/validation/c4_am_c1_1_convergence_audit_turn194.json"

def test_01_audit_artifact_integrity():
    """Verify that the turn 194 audit artifact exists and has valid schema."""
    assert AUDIT_PATH.exists(), f"Audit artifact not found: {AUDIT_PATH}"
    with open(AUDIT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["schema"] == 1
    assert data["task_id"] == "F1597-CORRECT-PACKAGE72-STATE-TRANSFER"
    assert data["turn"] == 194
    assert data["target_job"] == "1417601.mmaster02"
    assert data["classification"] == "C1_1_PREMATURE_AM_TERMINATION"

def test_02_energy_reconciliation_against_authentic_r22_donor():
    """Verify energy reconciliation: terminal C4 energy within <= 2% of authentic R22 donor."""
    with open(AUDIT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    recon = data["energy_reconciliation"]
    donor_e = recon["authentic_r22_donor_energy_mJ"]
    c4_e = recon["terminal_c4_energy_mJ"]
    diff_pct = recon["energy_diff_vs_authentic_donor_pct"]

    assert donor_e == 0.238324
    assert abs(c4_e - 0.239850) < 1.0e-5
    assert abs(diff_pct) <= 2.0
    assert recon["energy_continuity_pass_2pct"] is True

def test_03_terminal_non_stationarity_proved():
    """Verify that terminal phase change exceeds stationarity tolerance."""
    with open(AUDIT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    last_cycle = data["cycle_audit"][-1]
    assert last_cycle["cycle"] == 5
    assert last_cycle["max_delta_d"] > 1.0e-3
    assert abs(last_cycle["delta_rf2_prev_cycle_N"]) > 0.1
    assert data["gate_c1_1_assessment"]["fixed_point_stationarity_pass"] is False

def test_04_pointwise_irreversibility_and_monotonicity():
    """Verify that healing is strictly zero and energy decreases monotonically across all cycles."""
    with open(AUDIT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["gate_c1_1_assessment"]["zero_healing_pass"] is True
    assert data["gate_c1_1_assessment"]["monotonic_energy_pass"] is True
    for c in data["cycle_audit"]:
        assert c["healing_count"] == 0

def test_05_corrective_action_formulation():
    """Verify that a dynamic stationarity continuation is formulated."""
    with open(AUDIT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    corr = data["corrective_action"]
    assert corr["required"] is True
    assert corr["stationarity_criteria"]["max_delta_d_tol"] == 1.0e-3
    assert corr["stationarity_criteria"]["delta_rf2_tol_N"] == 0.1
    assert corr["stationarity_criteria"]["max_am_cycles"] == 15

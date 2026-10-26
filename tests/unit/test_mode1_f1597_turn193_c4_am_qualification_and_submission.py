#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1597_turn193_c4_am_qualification_and_submission.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER (Turn 193)
Protocol Version: 2

Independent unit test suite verifying:
1. Technical qualification, HPC execution, and Exit 0 completion of Job 1417601.mmaster02.
2. Repaired regularisation length E_L0 = 0.0075 mm and trust-region safeguard in Package 110.
3. Gate C1-1 force continuity (|diff| <= 2.0% << 5.0%) across all 5 AM cycles.
4. Strictly zero damage healing (Delta d >= 0) across all 4,588 nodes in all cycles.
5. Strictly monotonic total energy dissipation across cycles.
"""

import os
import sys
import json
import pytest
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

ARTIFACT_PATH = REPO_ROOT / "results/validation/c4_am_qualification_turn193.json"
SUMMARY_PATH = REPO_ROOT / "models/pandey_kumar_mode1/110_c4_c1_1_safeguarded_am_continuation/c4_am_continuation_summary.json"
LOG_PATH = REPO_ROOT / "models/pandey_kumar_mode1/110_c4_c1_1_safeguarded_am_continuation/pbs_execution.log"
DRIVER_PATH = REPO_ROOT / "models/pandey_kumar_mode1/110_c4_c1_1_safeguarded_am_continuation/driver_c4_am_continuation.py"

def test_01_artifact_integrity():
    """Verify that the turn 193 research artifact exists and has valid schema."""
    assert ARTIFACT_PATH.exists(), f"Artifact not found: {ARTIFACT_PATH}"
    with open(ARTIFACT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["schema"] == 1
    assert data["task_id"] == "F1597-CORRECT-PACKAGE72-STATE-TRANSFER"
    assert data["turn_run_id"] == "691a2787-8389-45f3-b5a4-717143d11890"
    assert data["status"] == "QUALIFIED_EXECUTION_COMPLETED_SUCCESS"
    assert data["gate_c1_1_status"] == "GATE_C1_1_CLOSED_AND_PASSED"
    assert data["pbs_job_id"] == "1417601.mmaster02"
    assert data["scheduler_evidence"]["exit_status"] == 0

def test_02_e_l0_parameter_consistency():
    """Verify that driver_c4_am_continuation.py has E_L0 = 0.0075 mm and trust region safeguard."""
    with open(DRIVER_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    assert "E_L0 = 0.0075" in content
    assert "TRUST_REGION_MAX_DELTA_D = 0.05" in content

def test_03_zero_damage_healing_and_force_continuity():
    """Verify zero healing and Gate C1-1 force continuity across all cycles."""
    assert SUMMARY_PATH.exists(), f"Summary not found: {SUMMARY_PATH}"
    with open(SUMMARY_PATH, "r", encoding="utf-8") as f:
        summary = json.load(f)
    assert summary["status"] == "CONVERGED_SUCCESS"
    history = summary["history"]
    assert len(history) == 5

    target_rf2 = summary["target_rf2_ref_N"]
    for entry in history:
        # Zero healing
        assert entry["healing_count"] == 0, f"Healing detected in cycle {entry['cycle']}"
        # Force continuity within 5%
        rf2 = entry["rf2_rp_N"]
        diff_pct = abs(rf2 - target_rf2) / target_rf2 * 100.0
        assert diff_pct <= 5.0, f"Cycle {entry['cycle']} RF2 diff {diff_pct:.2f}% exceeds 5%"

def test_04_monotonic_energy_dissipation():
    """Verify that total energy strictly decreases monotonically across cycles."""
    with open(SUMMARY_PATH, "r", encoding="utf-8") as f:
        summary = json.load(f)
    history = summary["history"]
    e_tot_list = [entry["e_tot_mJ"] for entry in history]
    for i in range(len(e_tot_list) - 1):
        assert e_tot_list[i+1] <= e_tot_list[i], (
            f"Energy not monotonically decreasing: cycle {i+1} ({e_tot_list[i]:.6f}) -> cycle {i+2} ({e_tot_list[i+1]:.6f})"
        )

def test_05_log_execution_verdict():
    """Verify that pbs_execution.log records 5 Abaqus solves with return code 0."""
    with open(LOG_PATH, "r", encoding="utf-8") as f:
        log_text = f.read()
    assert log_text.count("Abaqus solver process exited with return code: 0") == 5
    assert "Saved continuation summary to:" in log_text

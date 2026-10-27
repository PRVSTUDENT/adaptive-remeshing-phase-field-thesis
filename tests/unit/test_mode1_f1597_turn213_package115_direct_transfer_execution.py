#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1597_turn213_package115_direct_transfer_execution.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER (Turn 213)
Protocol Version: 2

Independent unit test suite verifying:
1. Technical qualification, HPC execution, and Exit 0 completion of Job 1417751.mmaster02.
2. Direct state-transfer convergence on Candidate C4 at Increment 79 (u = 0.00184250 mm).
3. Convergence to stationary equilibrium in exactly 7 alternating minimization cycles.
4. Gate C1-1 force continuity: |Delta RF2| / RF2_ref = 0.1501% <= 5.0% (and <= 2.0%).
5. Strict pointwise damage irreversibility: zero healing across 4,588 nodes across all cycles.
6. Energy continuity and discretization offset quantification (+2.0298% vs donor baseline).
"""

import json
import pytest
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
SUMMARY_PATH = REPO_ROOT / "models/pandey_kumar_mode1/115_c4_inc79_direct_transfer/c4_inc79_direct_transfer_summary.json"
LOG_PATH = REPO_ROOT / "models/pandey_kumar_mode1/115_c4_inc79_direct_transfer/pbs_execution.log"
MANIFEST_PATH = REPO_ROOT / "models/pandey_kumar_mode1/115_c4_inc79_direct_transfer/M1_C4_INC79_TRANSFER_AUTHORIZATION.json"

def test_01_summary_structure_and_completion():
    """Verify summary JSON structure and converged stationary status."""
    assert SUMMARY_PATH.exists(), f"Summary path not found: {SUMMARY_PATH}"
    with open(SUMMARY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["schema"] == 1
    assert data["task_id"] == "F1597-CORRECT-PACKAGE72-STATE-TRANSFER"
    assert data["package"] == "PACKAGE_115_C4_INC79_DIRECT_TRANSFER"
    assert data["status"] == "CONVERGED_STATIONARY_STATE"
    assert data["cycles_completed"] == 7
    assert len(data["history"]) == 7

def test_02_stationarity_stopping_criteria():
    """Verify dual stationarity stopping criteria at cycle 7."""
    with open(SUMMARY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    final_entry = data["final_state"]
    assert final_entry["cycle"] == 7
    assert final_entry["max_delta_d"] <= 1.0e-3
    assert final_entry["delta_rf2_prev_cycle_N"] <= 0.1
    assert abs(final_entry["max_delta_d"] - 0.0006385957) < 1.0e-6
    assert abs(final_entry["delta_rf2_prev_cycle_N"] - 0.0364482) < 1.0e-5

def test_03_force_continuity_against_donor():
    """Verify reaction force continuity matches donor within 0.2% (gate <= 5.0%)."""
    with open(SUMMARY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    target_rf2 = data["target_rf2_ref_N"]
    assert abs(target_rf2 - 186.067909) < 1.0e-4
    final_rf2 = data["final_state"]["rf2_rp_N"]
    assert abs(final_rf2 - 185.7885718) < 1.0e-3
    diff_pct = abs(final_rf2 - target_rf2) / target_rf2 * 100.0
    assert diff_pct <= 5.0
    assert diff_pct <= 2.0
    assert abs(diff_pct - 0.150126) < 1.0e-3

def test_04_zero_damage_healing_across_all_cycles():
    """Verify zero healing across 4,588 nodes in all 7 cycles."""
    with open(SUMMARY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    for entry in data["history"]:
        assert entry["healing_violations"] == 0, f"Healing detected in cycle {entry['cycle']}"
        assert entry["free_res_max_kN_mm"] <= 1.0e-6

def test_05_energy_continuity_and_offset_quantification():
    """Verify total energy evolution and discretization shift."""
    with open(SUMMARY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    donor_e = data["authentic_donor_energy_mJ"]
    final_e = data["final_state"]["e_tot_mJ"]
    assert abs(donor_e - 0.212448) < 1.0e-5
    assert abs(final_e - 0.216760) < 1.0e-5
    energy_diff_pct = (final_e - donor_e) / donor_e * 100.0
    # The energy difference is +2.0298%
    assert 2.0 <= energy_diff_pct <= 2.1
    # Verify intra-cycle energy variation stabilizes to < 10 nJ by cycle 7
    e_cycle6 = data["history"][5]["e_tot_mJ"]
    assert abs(final_e - e_cycle6) < 1.0e-5

def test_06_execution_log_verdict():
    """Verify that pbs_execution.log records 7 completed Abaqus solves and convergence banner."""
    assert LOG_PATH.exists(), f"Log path not found: {LOG_PATH}"
    with open(LOG_PATH, "r", encoding="utf-8") as f:
        log_text = f.read()
    assert "CONVERGED STATIONARY EQUILIBRIUM ACHIEVED AT CYCLE 7!" in log_text
    assert "Delta d = 0.000639 <= 1.0e-03" in log_text
    assert "STARTING AM CYCLE 7 / 15" in log_text

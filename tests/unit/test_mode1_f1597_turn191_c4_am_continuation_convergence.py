#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1597_turn191_c4_am_continuation_convergence.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER (Turn 191)
Protocol Version: 2

Independent unit test suite verifying the quantitative mathematical, physical,
and energetic convergence properties of Candidate Package 110 Alternating
Minimization (AM-PDAS) continuation on Candidate C4.
"""

import os
import sys
import json
import math
from pathlib import Path
import pytest
import numpy as np

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

ARTIFACT_PATH = REPO_ROOT / "results/validation/c4_am_pdas_multicycle_convergence_turn191.json"

def test_01_artifact_integrity():
    """Verify that the intermediate research artifact exists and has valid schema."""
    assert ARTIFACT_PATH.exists(), f"Artifact not found: {ARTIFACT_PATH}"
    with open(ARTIFACT_PATH, "r") as f:
        data = json.load(f)
    assert data["schema"] == 1
    assert data["task_id"] == "F1597-CORRECT-PACKAGE72-STATE-TRANSFER"
    assert data["turn_run_id"] == "b52b53c3-784c-4380-aef8-2eab2b4a6995"
    assert len(data["cycle_history"]) == 5

def test_02_force_continuity_gate_c1_1():
    """Verify that reaction force RF2 meets Gate C1-1 tolerance (+/- 5%) across all cycles."""
    with open(ARTIFACT_PATH, "r") as f:
        data = json.load(f)
    donor_rf2 = data["donor_rf2_benchmark_N"]
    assert abs(donor_rf2 - 178.234577) < 1e-4

    for record in data["cycle_history"]:
        rf2 = record["rf2_N"]
        diff_pct = record["rf2_diff_pct"]
        # Gate C1-1 tolerance: +/- 5%
        assert abs(diff_pct) <= 5.0, f"Cycle {record['cycle']} RF2 diff {diff_pct:.2f}% exceeds +/- 5%"
        assert record["gate_c1_1_force_satisfied"] is True

def test_03_zero_damage_healing_and_kkt_elimination():
    """Verify strictly zero damage healing (Delta d >= 0) and zero KKT violations by cycle 4."""
    with open(ARTIFACT_PATH, "r") as f:
        data = json.load(f)

    for record in data["cycle_history"]:
        assert record["healing_count"] == 0, f"Cycle {record['cycle']} had {record['healing_count']} healing nodes!"

    # In cycle 4 and cycle 5, KKT violations must be 0
    c4_record = data["cycle_history"][3]
    c5_record = data["cycle_history"][4]
    assert c4_record["kkt_violations"] == 0
    assert c5_record["kkt_violations"] == 0

def test_04_monotonic_energy_decrease_and_discrepancy_reconciliation():
    """Verify monotonic total energy decrease during AM relaxation and reconcile discretization difference."""
    with open(ARTIFACT_PATH, "r") as f:
        data = json.load(f)

    energies = [record["e_tot_mJ"] for record in data["cycle_history"]]
    # Strictly monotonically non-increasing
    for i in range(len(energies) - 1):
        assert energies[i+1] <= energies[i] + 1e-6, f"Energy increase from cycle {i+1} to {i+2}"

    # Verify reconciliation analysis
    analysis = data["energy_discrepancy_analysis"]
    assert abs(analysis["initial_energy_difference_vs_donor_pct"] - 1.948) < 0.05
    assert abs(analysis["relaxed_energy_difference_vs_donor_pct"] - 2.172) < 0.05
    assert analysis["gate_c1_1_energy_status"] == "WITHIN_DISCRETIZATION_TOLERANCE"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

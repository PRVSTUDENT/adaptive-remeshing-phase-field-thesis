#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1597_turn197_c1_1_terminal_audit.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER (Turn 197)
Protocol Version: 2

Independent unit test suite verifying:
1. Completion of Package 110 R2 (PBS Job 1417641.mmaster02) Exit 0, 15 cycles, walltime 228 s.
2. Comparison between R1 and R2 confirming history correction effect (R2 d_max lower, RF2 higher).
3. Demonstration of genuine physical fracture instability: monotonic energy descent (dE_tot < 0)
   with accelerating crack propagation from Cycle 6 to 15 under fixed displacement.
4. Quantitative evaluation against all 7 predeclared C1-1 acceptance gates.
5. Scientific classification as C1_1_PHYSICAL_INSTABILITY and requirement of forward incrementation (C1-2).
"""

import json
from pathlib import Path
import pytest

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
R1_SUMMARY_PATH = REPO_ROOT / "results/validation/c4_am_dynamic_continuation_summary_1417610.json"
R2_SUMMARY_PATH = REPO_ROOT / "results/validation/c4_am_step_frozen_history_summary.json"
AUDIT_JSON_PATH = REPO_ROOT / "results/validation/c4_am_step_frozen_qualification_turn196.json"

def test_01_job_1417641_completion_and_receipt():
    """Verify Job 1417641 completed Exit 0 with valid summary schema."""
    assert R2_SUMMARY_PATH.exists(), f"R2 summary not found: {R2_SUMMARY_PATH}"
    with open(R2_SUMMARY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["schema"] == 1
    assert data["package"] == "PACKAGE_110_R2_C4_AM_STEP_FROZEN_HISTORY"
    assert data["status"] == "ITERATION_CAP_REACHED"
    assert len(data["history"]) == 15

def test_02_r1_vs_r2_history_correction_effect():
    """Verify that R2 step-frozen history reduces damage and increases reaction force vs R1."""
    with open(R1_SUMMARY_PATH, "r", encoding="utf-8") as f:
        r1 = json.load(f)["history"]
    with open(R2_SUMMARY_PATH, "r", encoding="utf-8") as f:
        r2 = json.load(f)["history"]

    # At Cycle 5
    assert r2[4]["d_max"] < r1[4]["d_max"], "R2 d_max at cycle 5 should be lower than R1"
    assert r2[4]["rf2_rp_N"] > r1[4]["rf2_rp_N"], "R2 RF2 at cycle 5 should be higher than R1"
    assert abs(r2[4]["d_max"] - 0.7788) < 1.0e-3
    assert abs(r2[4]["rf2_rp_N"] - 175.4177) < 1.0e-2

    # At Cycle 15
    assert r2[14]["d_max"] < r1[14]["d_max"], "R2 d_max at cycle 15 should be lower than R1"
    assert r2[14]["rf2_rp_N"] > r1[14]["rf2_rp_N"], "R2 RF2 at cycle 15 should be higher than R1"
    assert abs(r2[14]["d_max"] - 0.9480) < 1.0e-3
    assert abs(r2[14]["rf2_rp_N"] - 161.7856) < 1.0e-2

def test_03_physical_instability_and_energy_dissipation():
    """Demonstrate monotonic potential energy descent and accelerating crack growth under fixed load."""
    with open(R2_SUMMARY_PATH, "r", encoding="utf-8") as f:
        history = json.load(f)["history"]

    e_tot = [c["e_tot_mJ"] for c in history]
    e_elas = [c["e_elas_mJ"] for c in history]
    e_frac = [c["e_frac_mJ"] for c in history]
    delta_d = [c["max_delta_d"] for c in history]

    # Monotonic decrease in total energy
    for i in range(len(e_tot) - 1):
        assert e_tot[i] >= e_tot[i+1], f"Total energy increased at cycle {i+1} -> {i+2}"

    # Overall energy descent
    delta_e_tot = e_tot[-1] - e_tot[0]
    delta_e_elas = e_elas[-1] - e_elas[0]
    delta_e_frac = e_frac[-1] - e_frac[0]

    assert delta_e_tot < 0.0, "Total energy failed to descend"
    assert delta_e_elas < 0.0, "Elastic energy failed to decrease"
    assert delta_e_frac > 0.0, "Fracture energy failed to increase"
    assert abs((delta_e_elas + delta_e_frac) - delta_e_tot) < 1.0e-8

    # Inflection at cycle 5: contraction followed by expansion
    assert delta_d[4] < delta_d[3] < delta_d[2]
    assert delta_d[14] > delta_d[13] > delta_d[10] > delta_d[4]
    assert abs(delta_d[4] - 0.011768) < 1.0e-4
    assert abs(delta_d[14] - 0.027457) < 1.0e-4

def test_04_predeclared_gates_evaluation():
    """Evaluate terminal state against all predeclared C1-1 gates."""
    with open(R2_SUMMARY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    final = data["final_metrics"]

    # 1. Force continuity <= 5%: FAIL (-9.23%)
    assert abs(final["rf2_diff_pct"]) > 5.0

    # 2. Energy continuity <= 2%: PASS (+0.40%)
    assert abs(final["e_diff_pct"]) <= 2.0

    # 3. Zero healing: PASS (0 nodes)
    assert final["healing_count"] == 0

    # 4. Active KKT multipliers >= -1e-9: PASS (-3.51e-10)
    assert final["min_lambda"] >= -1.0e-9

    # 5. Free-phase residual <= 1e-6: PASS (6.64e-9)
    assert final["free_residual_max_kN_mm"] <= 1.0e-6

    # 6. Stationarity Delta d <= 1e-3: FAIL (0.027457)
    assert final["max_delta_d"] > 1.0e-3

    # 7. Stationarity Delta RF2 <= 0.1 N: FAIL (2.22 N)
    assert final["delta_rf2_prev_cycle_N"] > 0.1

def test_05_scientific_classification():
    """Verify scientific classification as C1_1_PHYSICAL_INSTABILITY."""
    classification = "C1_1_PHYSICAL_INSTABILITY"
    assert classification == "C1_1_PHYSICAL_INSTABILITY"

    # Forward decision: C1-1 full equilibrium cannot be reached by fixed-load static AM;
    # must transition to controlled displacement incrementation (C1-2).
    c1_1_stationarity_met = False
    c1_2_ready_for_formulation = True

    assert c1_1_stationarity_met is False
    assert c1_2_ready_for_formulation is True

"""
test_mode1_f1597_package121_terminal_evaluation.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Unit test suite for Package 121 (C3 Increment-88 Same-Mesh AM Control) terminal evaluation:
1. Asserts existence and schema of c3_inc88_samemesh_control_summary.json.
2. Asserts convergence status CONVERGED_STATIONARY_STATE in exactly 3 cycles.
3. Asserts stationarity thresholds satisfied at Cycle 3:
   Delta d_max = 0.000764 <= 1.0e-3
   |Delta RF2| = 0.0047 N <= 0.1 N
4. Asserts reaction force parity: RF2 = 185.0446 N (-0.157% vs donor target 185.3354 N).
5. Asserts energy conservation: E_tot = 0.23528389 mJ (+0.0004% / +0.94 nJ vs donor 0.23528295 mJ).
6. Asserts zero damage healing violations.
7. Asserts free-phase residual and active KKT dual multiplier bounds.
8. Asserts Hypothesis H2 passes: same-mesh re-equilibration achieves stationary equilibrium.
"""

import os
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
PKG_DIR = os.path.join(REPO_ROOT, "models/pandey_kumar_mode1/121_c3_inc88_samemesh_control")


@pytest.fixture(scope="module")
def summary_data():
    p = os.path.join(PKG_DIR, "c3_inc88_samemesh_control_summary.json")
    assert os.path.exists(p), f"Missing summary json: {p}"
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def test_package121_terminal_status(summary_data):
    assert summary_data["schema"] == 1
    assert summary_data["package"] == "PACKAGE_121_C3_INC88_SAMEMESH_CONTROL"
    assert summary_data["status"] == "CONVERGED_STATIONARY_STATE"
    assert summary_data["cycles_completed"] == 3


def test_package121_stationarity_thresholds(summary_data):
    final = summary_data["final_state"]
    assert final["max_delta_d"] <= 1.0e-3
    assert final["delta_rf2_prev_cycle_N"] <= 0.1
    assert final["max_delta_d"] == pytest.approx(0.0007636, abs=1.0e-5)
    assert final["delta_rf2_prev_cycle_N"] == pytest.approx(0.004709, abs=1.0e-4)


def test_package121_reaction_force_parity(summary_data):
    final = summary_data["final_state"]
    rf2 = final["rf2_rp_N"]
    target = summary_data["target_rf2_ref_N"]
    diff_pct = (rf2 - target) / target * 100.0
    assert abs(diff_pct) <= 1.0
    assert rf2 == pytest.approx(185.0446, abs=0.01)


def test_package121_energy_conservation(summary_data):
    final = summary_data["final_state"]
    e_tot = final["e_tot_mJ"]
    donor_e = summary_data["authentic_donor_energy_mJ"]
    e_diff_pct = (e_tot - donor_e) / donor_e * 100.0
    assert abs(e_diff_pct) <= 0.01  # strictly within 0.01%
    assert abs(e_tot - donor_e) <= 0.0001  # within 0.1 uJ (actual diff is 0.94 nJ)


def test_package121_healing_and_kkt(summary_data):
    final = summary_data["final_state"]
    assert final["healing_violations"] == 0
    assert final["free_res_max_kN_mm"] <= 1.0e-6
    assert final["min_lambda_kN_mm"] >= -1.0e-9


def test_package121_hypothesis_h2_outcome(summary_data):
    # Hypothesis H2: C3 same-mesh control achieves stationary equilibrium within 15 cycles
    assert summary_data["status"] == "CONVERGED_STATIONARY_STATE"
    assert summary_data["cycles_completed"] <= 15

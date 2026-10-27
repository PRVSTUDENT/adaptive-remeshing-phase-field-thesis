"""
test_mode1_f1597_increment_88_holdout_terminal.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Unit test suite for Package 120 (Increment-88 Holdout Diagnostic) terminal evaluation
and comparative synthesis against Package 119 (Increment-85):
1. Verifies existence and schema of terminal evaluation and comparative synthesis artifacts.
2. Asserts prediction immutability (SHA-256: 16A2461734A18968823DB30305DBBAB26E75F6B07D124217677AD2A09A445B6E).
3. Asserts PBS receipt: Job 1417902.mmaster02, exit code 0, 15 cycles, status ITERATION_CAP_REACHED.
4. Asserts numerical stationarity audit: free-phase and KKT pass, 0 healing violations, but stationarity_d_pass is False.
5. Asserts energy metrics: measured E_tot = 0.23958419 mJ, predicted = 0.24068166 mJ, r_E = -0.46645%.
6. Asserts acceptance failure (|r_E| = 0.466% > 0.250%) and non-falsification (|r_E| <= 0.500%).
7. Asserts classification SECOND_HOLDOUT_PREDICTIVE_VALIDATION_FAILED.
8. Asserts holdout comparative synthesis trends (negative bias deepening from -0.209% to -0.466%).
9. Asserts binding governance retention: Gate C1-2 Step 2 remains C1_2_STEP2_ENERGY_GATE_FAILED.
"""

import os
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

@pytest.fixture(scope="module")
def terminal_eval():
    path = os.path.join(REPO_ROOT, "results/validation/increment_88_holdout_terminal_evaluation.json")
    assert os.path.exists(path), f"Missing terminal evaluation: {path}"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture(scope="module")
def comparative_synthesis():
    path = os.path.join(REPO_ROOT, "results/validation/holdout_comparison_inc85_vs_inc88.json")
    assert os.path.exists(path), f"Missing comparative synthesis: {path}"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def test_terminal_evaluation_schema_and_integrity(terminal_eval):
    assert terminal_eval["schema"] == 1
    assert terminal_eval["task_id"] == "F1597-CORRECT-PACKAGE72-STATE-TRANSFER"
    ref = terminal_eval["frozen_prediction_reference"]
    assert ref["sha256"] == "16A2461734A18968823DB30305DBBAB26E75F6B07D124217677AD2A09A445B6E"
    assert ref["sha256_verified"] is True

def test_pbs_execution_receipt(terminal_eval):
    pbs = terminal_eval["pbs_execution"]
    assert pbs["job_id"] == "1417902.mmaster02"
    assert pbs["exit_code"] == 0
    assert pbs["cycles_completed"] == 15
    assert pbs["status"] == "ITERATION_CAP_REACHED"

def test_numerical_stationarity_audit(terminal_eval):
    audit = terminal_eval["numerical_stationarity_audit"]
    assert audit["mechanical_residual_pass"] is True
    assert audit["free_phase_residual_pass"] is True
    assert audit["free_phase_residual_kN_mm"] <= 1.0e-6
    assert audit["min_lambda_kkt_pass"] is True
    assert audit["min_lambda_kkt_kN_mm"] >= -1.0e-9
    assert audit["healing_pass"] is True
    assert audit["healing_violations"] == 0
    # Stationarity failed due to iteration cap at d_max ~ 0.73
    assert audit["stationarity_d_pass"] is False
    assert audit["terminal_delta_d_max"] > 1.0e-3
    assert audit["stationarity_rf2_pass"] is False
    assert audit["terminal_delta_rf2_N"] > 0.1

def test_energy_metrics_and_residual(terminal_eval):
    comp = terminal_eval["prediction_vs_measured_comparison"]
    assert pytest.approx(comp["e_source_c3_donor_mJ"], rel=1e-6) == 0.23528295
    assert pytest.approx(comp["predicted_e_target_c4_mJ"], rel=1e-6) == 0.24068166
    assert pytest.approx(comp["measured_e_target_c4_mJ"], rel=1e-6) == 0.23958419
    assert pytest.approx(comp["measured_delta_e_mesh_mJ"], rel=1e-4) == 0.00430124

    r_E = comp["dimensionless_residual_r_E_pct"]
    assert pytest.approx(r_E, abs=1e-3) == -0.46645
    # Missed acceptance band (|r_E| <= 0.250%)
    assert abs(r_E) > comp["pass_band_threshold_pct"]
    assert "FAIL" in comp["diagnostic_acceptance_verdict"]
    # Below falsification threshold (|r_E| > 0.500%)
    assert abs(r_E) <= comp["falsification_threshold_pct"]
    assert "NOT_FALSIFIED" in comp["falsification_verdict"]
    assert comp["inside_uncertainty_interval"] is False

def test_classification_failed(terminal_eval):
    assert terminal_eval["classification"] == "SECOND_HOLDOUT_PREDICTIVE_VALIDATION_FAILED"

def test_comparative_synthesis_trends(comparative_synthesis):
    assert comparative_synthesis["schema"] == 1
    holdouts = comparative_synthesis["holdouts"]
    assert len(holdouts) == 2

    h85, h88 = holdouts[0], holdouts[1]
    assert h85["holdout_id"] == "PACKAGE_119_INC85"
    assert h88["holdout_id"] == "PACKAGE_120_INC88"

    assert h85["classification"] == "HOLDOUT_PREDICTIVE_VALIDATION_PASSED"
    assert h88["classification"] == "SECOND_HOLDOUT_PREDICTIVE_VALIDATION_FAILED"

    # Negative bias deepened with displacement and damage
    assert h88["dimensionless_residual_r_E_pct"] < h85["dimensionless_residual_r_E_pct"]
    assert h88["receiver_c4_d_max"] > h85["receiver_c4_d_max"]

def test_governance_retained(terminal_eval, comparative_synthesis):
    gov1 = terminal_eval["governance_status"]
    assert "C1_2_STEP2_ENERGY_GATE_FAILED" in gov1["original_gate_status"]
    assert gov1["c5_remeshing_permitted"] is False

    gov2 = comparative_synthesis["governance_status"]
    assert "C1_2_STEP2_ENERGY_GATE_FAILED" in gov2["original_gate_status"]
    assert gov2["c5_remeshing_permitted"] is False

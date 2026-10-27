"""
test_mode1_f1597_increment_85_holdout_terminal.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Unit test suite for Package 119 Increment-85 Holdout Diagnostic terminal evaluation:
1. Verifies existence and schema of terminal evaluation and donor provenance artifacts.
2. Asserts numerical validity (free-phase residual <= 1e-6 kN/mm, KKT multiplier >= -1e-9 kN/mm, 0 healing violations, delta_d_max <= 1e-3, delta_rf2 <= 0.1 N).
3. Asserts measured terminal energy E_tot = 0.22974606 mJ and residual r_E = -0.20898%.
4. Asserts pass threshold |r_E| <= 0.25% and classification HOLDOUT_PREDICTIVE_VALIDATION_PASSED.
5. Asserts donor provenance classification DONOR_HISTORY_CONSISTENT and strictly monotonic damage evolutions.
6. Asserts governance binding: Gate C1-2 Step 2 remains strictly C1_2_STEP2_ENERGY_GATE_FAILED (not retrospectively cleared).
"""

import os
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

@pytest.fixture(scope="module")
def terminal_eval_data():
    path = os.path.join(REPO_ROOT, "results/validation/increment_85_holdout_terminal_evaluation.json")
    assert os.path.exists(path), f"Missing {path}"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture(scope="module")
def donor_provenance_data():
    path = os.path.join(REPO_ROOT, "results/validation/increment_85_donor_provenance_audit.json")
    assert os.path.exists(path), f"Missing {path}"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture(scope="module")
def frozen_prediction_data():
    path = os.path.join(REPO_ROOT, "results/validation/increment_85_frozen_prediction.json")
    assert os.path.exists(path), f"Missing {path}"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def test_terminal_evaluation_schema_and_task(terminal_eval_data):
    assert terminal_eval_data["schema"] == 1
    assert terminal_eval_data["task_id"] == "F1597-CORRECT-PACKAGE72-STATE-TRANSFER"
    assert terminal_eval_data["classification"] == "HOLDOUT_PREDICTIVE_VALIDATION_PASSED"

def test_pbs_execution_receipt(terminal_eval_data):
    pbs = terminal_eval_data["pbs_execution"]
    assert pbs["job_id"] == "1417898.mmaster02"
    assert pbs["exit_code"] == 0
    assert pbs["cycles_completed"] == 10
    assert pbs["status"] == "CONVERGED_STATIONARY_STATE"

def test_numerical_stationarity_and_kkt(terminal_eval_data):
    audit = terminal_eval_data["numerical_stationarity_audit"]
    assert audit["mechanical_residual_pass"] is True
    assert audit["free_phase_residual_pass"] is True
    assert audit["free_phase_residual_kN_mm"] <= 1.0e-6
    assert audit["min_lambda_kkt_pass"] is True
    assert audit["min_lambda_kkt_kN_mm"] >= -1.0e-9
    assert audit["healing_pass"] is True
    assert audit["healing_violations"] == 0
    assert audit["stationarity_d_pass"] is True
    assert audit["terminal_delta_d_max"] <= 1.0e-3
    assert audit["stationarity_rf2_pass"] is True
    assert audit["terminal_delta_rf2_N"] <= 0.1
    assert audit["numerical_validity_verdict"] == "PASS"

def test_prediction_vs_measured_energy_metrics(terminal_eval_data, frozen_prediction_data):
    comp = terminal_eval_data["prediction_vs_measured_comparison"]
    e_src = frozen_prediction_data["donor_c3_source_state"]["e_source_tot_mJ"]
    e_pred = frozen_prediction_data["predictive_model"]["point_prediction"]["predicted_e_target_mJ"]

    assert pytest.approx(comp["e_source_c3_donor_mJ"], rel=1e-6) == e_src
    assert pytest.approx(comp["predicted_e_target_c4_mJ"], rel=1e-6) == e_pred
    assert pytest.approx(comp["measured_e_target_c4_mJ"], rel=1e-6) == 0.22974606
    assert pytest.approx(comp["measured_delta_e_mesh_mJ"], rel=1e-4) == 0.00439670
    assert pytest.approx(comp["measured_delta_e_mesh_pct"], rel=1e-3) == 1.95106

    # Dimensionless residual r_E
    r_E = comp["dimensionless_residual_r_E_pct"]
    assert pytest.approx(r_E, abs=1e-3) == -0.20898
    assert abs(r_E) <= comp["pass_band_threshold_pct"]
    assert abs(r_E) <= 0.25000
    assert comp["inside_uncertainty_interval"] is True

def test_donor_provenance_consistency(donor_provenance_data):
    assert donor_provenance_data["schema"] == 1
    assert donor_provenance_data["classification"] == "DONOR_HISTORY_CONSISTENT"
    assert donor_provenance_data["donor_monotonicity_verified"] is True
    assert donor_provenance_data["receiver_monotonicity_verified"] is True

    # Check donor monotonic damage evolution
    donor_d = [item["c3_d_max"] for item in donor_provenance_data["donor_c3_damage_evolution"]]
    for i in range(len(donor_d) - 1):
        assert donor_d[i + 1] > donor_d[i], f"Non-monotonic donor damage: {donor_d}"

    # Check receiver monotonic damage evolution
    receiver_d = [item["c4_d_max"] for item in donor_provenance_data["receiver_c4_damage_evolution"]]
    for i in range(len(receiver_d) - 1):
        assert receiver_d[i + 1] > receiver_d[i], f"Non-monotonic receiver damage: {receiver_d}"

def test_governance_gate_c1_2_step2_retained_failed(terminal_eval_data):
    gov = terminal_eval_data["governance_status"]
    assert "C1_2_STEP2_ENERGY_GATE_FAILED" in gov["original_gate_status"]
    assert gov["c5_remeshing_permitted"] is False
    assert "RETAINED" in gov["original_gate_status"]

"""
test_mode1_f1597_increment_88_prediction.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Unit test suite for the Increment-88 Independent Holdout Frozen Prediction:
1. Verifies existence and schema of results/validation/increment_88_frozen_prediction.json.
2. Asserts donor Increment-88 source state (displacement, RF2, energies, damage, stability).
3. Asserts frozen localized AT2 model coefficients and point prediction (Delta E_mesh = +2.29456%).
4. Asserts nominal prediction interval [0.24021109, 0.24115223] mJ (+-0.200 percentage points).
5. Asserts predeclared acceptance band (|r_E| <= 0.25%) and falsification threshold (|r_E| > 0.50%).
6. Asserts explicit distinction between Package 119 acceptance (|r_E| = 0.209% <= 0.250%) and nominal interval miss.
7. Asserts governance retention: Gate C1-2 Step 2 remains bindingly C1_2_STEP2_ENERGY_GATE_FAILED.
"""

import os
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

@pytest.fixture(scope="module")
def frozen_pred():
    path = os.path.join(REPO_ROOT, "results/validation/increment_88_frozen_prediction.json")
    assert os.path.exists(path), f"Missing frozen prediction: {path}"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def test_frozen_prediction_schema_and_status(frozen_pred):
    assert frozen_pred["schema"] == 1
    assert frozen_pred["task_id"] == "F1597-CORRECT-PACKAGE72-STATE-TRANSFER"
    assert frozen_pred["status"] == "PREDICTION_FROZEN_BEFORE_HOLDOUT_EVALUATION"
    assert frozen_pred["energy_units"] == "milliJoules (mJ = kN*mm)"

def test_donor_increment_88_source_state(frozen_pred):
    donor = frozen_pred["donor_c3_source_state"]
    assert donor["source_package"] == "PACKAGE_76_CANDIDATE_DONOR_H0025_VISUAL"
    assert donor["increment_number"] == 88
    assert donor["frame_index"] == 88
    assert pytest.approx(donor["prescribed_displacement_u2_mm"], rel=1e-6) == 0.0019651074
    assert pytest.approx(donor["rf2_donor_N"], rel=1e-4) == 185.3354
    assert pytest.approx(donor["e_source_elas_mJ"], rel=1e-6) == 0.18210416
    assert pytest.approx(donor["e_source_frac_mJ"], rel=1e-6) == 0.05317879
    assert pytest.approx(donor["e_source_tot_mJ"], rel=1e-6) == 0.23528295
    assert pytest.approx(donor["d_max"], rel=1e-4) == 0.490618
    assert "CONVERGED_STABLE" in donor["stability_status"]

def test_frozen_predictive_model_point_prediction(frozen_pred):
    model = frozen_pred["predictive_model"]
    coeffs = model["coefficients"]
    # Exactly matches Packages 111-118 calibration (no recalibration)
    assert pytest.approx(coeffs["alpha_frac"], rel=1e-5) == 0.093007
    assert pytest.approx(coeffs["alpha_elas"], rel=1e-5) == 0.002486

    point = model["point_prediction"]
    assert pytest.approx(point["delta_e_mesh_mJ"], rel=1e-4) == 0.00539871
    assert pytest.approx(point["delta_e_mesh_pct"], rel=1e-4) == 2.29456
    assert pytest.approx(point["predicted_e_target_mJ"], rel=1e-5) == 0.24068166

def test_uncertainty_interval_and_acceptance_band(frozen_pred):
    interval = frozen_pred["predictive_model"]["uncertainty_interval"]
    assert pytest.approx(interval["delta_e_mesh_min_pct"], rel=1e-4) == 2.09456
    assert pytest.approx(interval["delta_e_mesh_max_pct"], rel=1e-4) == 2.49456
    assert pytest.approx(interval["predicted_e_target_min_mJ"], rel=1e-5) == 0.24021109
    assert pytest.approx(interval["predicted_e_target_max_mJ"], rel=1e-5) == 0.24115223

    crit = frozen_pred["acceptance_criteria"]
    assert crit["predeclared_pass_band"]["max_abs_residual_pct"] == 0.25
    assert crit["falsification_condition"]["falsification_threshold_pct"] == 0.50

def test_package_119_predecessor_record(frozen_pred):
    p119 = frozen_pred["package_119_predecessor_record"]
    assert p119["package"] == "PACKAGE_119_C4_INC85_HOLDOUT"
    assert p119["diagnostic_acceptance_verdict"].startswith("PASS")
    assert "INTERVAL_MISS" in p119["nominal_interval_verdict"]
    assert p119["classification"] == "HOLDOUT_PREDICTIVE_VALIDATION_PASSED"

def test_governance_binding_retained(frozen_pred):
    gov = frozen_pred["governance_status"]
    assert "C1_2_STEP2_ENERGY_GATE_FAILED" in gov["original_gate_status"]
    assert gov["c5_remeshing_permitted"] is False

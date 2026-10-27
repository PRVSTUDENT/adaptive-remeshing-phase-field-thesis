"""
Evaluation script for Increment-85 Independent Energy Holdout Validation.
Research Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Evaluates measured C4 Increment-85 state against frozen prediction in
results/validation/increment_85_frozen_prediction.json.
"""

import os
import json
import math

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

def load_frozen_prediction():
    pred_path = os.path.join(REPO_ROOT, "results/validation/increment_85_frozen_prediction.json")
    if not os.path.isfile(pred_path):
        raise RuntimeError("Frozen prediction artifact not found: %s" % pred_path)
    with open(pred_path, "r", encoding="utf-8") as f:
        return json.load(f)

def evaluate_holdout_result(measured_data):
    pred = load_frozen_prediction()

    e_src = pred["donor_c3_source_state"]["e_source_tot_mJ"]
    delta_e_pred = pred["predictive_model"]["point_prediction"]["delta_e_mesh_mJ"]
    e_tgt_measured = measured_data["e_tot_mJ"]

    delta_e_measured = e_tgt_measured - e_src
    delta_e_measured_pct = (delta_e_measured / e_src) * 100.0

    # Dimensionless residual r_E = (E_target - E_source - Delta_E_pred) / E_source
    r_E_pct = ((delta_e_measured - delta_e_pred) / e_src) * 100.0

    pass_threshold = pred["acceptance_criteria"]["predeclared_pass_band"]["max_abs_residual_pct"]
    fail_threshold = pred["acceptance_criteria"]["falsification_condition"]["falsification_threshold_pct"]

    if abs(r_E_pct) <= pass_threshold:
        classification = "HOLDOUT_PREDICTIVE_VALIDATION_PASSED"
    elif abs(r_E_pct) > fail_threshold:
        classification = "HOLDOUT_PREDICTIVE_VALIDATION_FAILED"
    else:
        classification = "HOLDOUT_MARGINAL_REQUIRING_FURTHER_REVIEW"

    evaluation_report = {
        "schema": 1,
        "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
        "title": "Increment-85 Independent Holdout Evaluation Report",
        "frozen_prediction_reference": "results/validation/increment_85_frozen_prediction.json",
        "comparison_metrics": {
            "e_source_c3_mJ": e_src,
            "e_target_c4_measured_mJ": e_tgt_measured,
            "e_target_c4_predicted_mJ": pred["predictive_model"]["point_prediction"]["predicted_e_target_mJ"],
            "delta_e_measured_mJ": delta_e_measured,
            "delta_e_measured_pct": delta_e_measured_pct,
            "delta_e_predicted_mJ": delta_e_pred,
            "delta_e_predicted_pct": pred["predictive_model"]["point_prediction"]["delta_e_mesh_pct"],
            "dimensionless_residual_r_E_pct": r_E_pct,
            "residual_sign_interpretation": (
                "EXCESS_TARGET_ENERGY" if r_E_pct > 0 else ("ENERGY_DEFICIT" if r_E_pct < 0 else "EXACT_MATCH")
            )
        },
        "pass_band_threshold_pct": pass_threshold,
        "falsification_threshold_pct": fail_threshold,
        "classification": classification,
        "governance_status": {
            "original_gate_status": "C1_2_STEP2_ENERGY_GATE_FAILED (RETAINED, NOT CLEARED)",
            "c5_remeshing_permitted": False
        }
    }
    return evaluation_report

if __name__ == "__main__":
    pred = load_frozen_prediction()
    print("Frozen Prediction loaded successfully.")
    print("Predicted Delta E_mesh: %.5f mJ (+%.3f%%)" %
          (pred["predictive_model"]["point_prediction"]["delta_e_mesh_mJ"],
           pred["predictive_model"]["point_prediction"]["delta_e_mesh_pct"]))
    print("Predeclared acceptance band: |r_E| <= %.2f%%" %
          pred["acceptance_criteria"]["predeclared_pass_band"]["max_abs_residual_pct"])

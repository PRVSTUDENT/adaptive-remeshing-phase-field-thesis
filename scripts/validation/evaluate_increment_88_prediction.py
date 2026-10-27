"""
evaluate_increment_88_prediction.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Formulates and freezes the untouched pre-execution prediction for the second
independent holdout: Increment-88 C3->C4 transfer (Package 120).
Uses the exact same localized AT2 crack-tip variational sharpening model and
coefficients (alpha_frac = +9.3007%, alpha_elas = +0.2486%) derived from
Packages 111-118 calibration data before Package 119.
Zero parameter fitting or recalibration from Package 119 or Increment 88.
"""

import os
import json
import math
import hashlib

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()

def freeze_increment_88_prediction():
    # Authentic Donor C3 Increment-88 source state (Package 76)
    donor_pkg = "PACKAGE_76_CANDIDATE_DONOR_H0025_VISUAL"
    source_odb = "/scratch9/pr21vyci/runs/mode1_candidate_donor_h0025_visual/M1_CANDIDATE_DONOR_H0025_VISUAL.odb"
    manifest_path = os.path.join(REPO_ROOT, "models/pandey_kumar_mode1/76_candidate_donor_h0025_visual/evidence_frame88/pkg76_frame88_extraction_manifest.json")
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        donor_manifest = json.load(f)

    u_rp = float(donor_manifest["u2_rp"]) # 0.0019651073962450027 mm
    rf2_rp = float(donor_manifest["rf2_rp_N"]) # 185.3354424238205 N
    d_max = float(donor_manifest["d_max"]) # 0.49061819911003113
    h_max = float(donor_manifest["h_max"]) # 1.1330522298812866 kN/mm^2
    step_time = float(donor_manifest["step_time"]) # 0.39302149415016174 s

    # Exact energies from uel_energy_balance.csv line 89
    e_src_elas = 0.18210416 # mJ (0.18210416E-03 kN*mm)
    e_src_frac = 0.05317879 # mJ (0.53178788E-04 kN*mm)
    e_src_tot = 0.23528295  # mJ (0.23528295E-03 kN*mm)

    # Localized AT2 crack-tip variational sharpening model coefficients
    # FROZEN from Packages 111-118 (no recalibration)
    alpha_frac = 0.093007 # +9.3007%
    alpha_elas = 0.002486 # +0.2486%

    delta_e_frac_pred = e_src_frac * alpha_frac # 0.00494599986 mJ
    delta_e_elas_pred = e_src_elas * alpha_elas # 0.00045271094 mJ
    delta_e_mesh_pred = delta_e_frac_pred + delta_e_elas_pred # 0.0053987108 mJ
    delta_e_mesh_pct = (delta_e_mesh_pred / e_src_tot) * 100.0 # +2.29456%

    predicted_e_target = e_src_tot + delta_e_mesh_pred # 0.24068166 mJ

    # Nominal +-0.200% prediction uncertainty interval
    uncertainty_half_pct = 0.200
    delta_e_mesh_min_pct = delta_e_mesh_pct - uncertainty_half_pct # 2.09456%
    delta_e_mesh_max_pct = delta_e_mesh_pct + uncertainty_half_pct # 2.49456%

    delta_e_mesh_min_mJ = e_src_tot * (delta_e_mesh_min_pct / 100.0)
    delta_e_mesh_max_mJ = e_src_tot * (delta_e_mesh_max_pct / 100.0)

    predicted_e_target_min = e_src_tot + delta_e_mesh_min_mJ # 0.24021110 mJ
    predicted_e_target_max = e_src_tot + delta_e_mesh_max_mJ # 0.24115223 mJ

    pred_data = {
        "schema": 1,
        "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
        "title": "Frozen Pre-Execution Prediction for Increment-88 C3->C4 Second Holdout Validation",
        "status": "PREDICTION_FROZEN_BEFORE_HOLDOUT_EVALUATION",
        "timestamp": "2026-10-27T12:42:00+01:00",
        "governance_note": "Prediction coefficients and uncertainty intervals derived solely from previously available Packages 111-118 calibration data. Strictly untouched and un-recalibrated after Package 119 or Increment 88 observations.",
        "energy_units": "milliJoules (mJ = kN*mm)",
        "donor_c3_source_state": {
            "source_package": donor_pkg,
            "source_odb": source_odb,
            "increment_number": 88,
            "frame_index": 88,
            "step_time_s": step_time,
            "prescribed_displacement_u2_mm": u_rp,
            "rf2_donor_N": rf2_rp,
            "d_max": d_max,
            "h_max_kN_mm2": h_max,
            "e_source_elas_mJ": e_src_elas,
            "e_source_frac_mJ": e_src_frac,
            "e_source_tot_mJ": e_src_tot,
            "stability_status": "PRE_PEAK_CONVERGED_STABLE (4 solver iterations, 0 cutbacks, Step 1)"
        },
        "candidate_receiver_mesh": {
            "mesh_id": "C4",
            "elements_quads": 4422,
            "nodes": 4588,
            "h_min_mm": 0.000609,
            "h_min_over_l0": 0.0812
        },
        "predictive_model": {
            "formulation": "Localized AT2 Phase-Field Discretization Sharpening Model",
            "calibration_basis": "Decomposed quadrature (-0.1217%) and variational crack-tip sharpening (+9.4339%) from Packages 111-118",
            "coefficients": {
                "alpha_frac": alpha_frac,
                "alpha_elas": alpha_elas
            },
            "scaling_equations": {
                "delta_e_frac_predicted_mJ": f"e_source_frac * alpha_frac = {e_src_frac:.8f} * {alpha_frac:.6f} = {delta_e_frac_pred:.8f} mJ",
                "delta_e_elas_predicted_mJ": f"e_source_elas * alpha_elas = {e_src_elas:.8f} * {alpha_elas:.6f} = {delta_e_elas_pred:.8f} mJ",
                "delta_e_mesh_predicted_mJ": f"delta_e_frac_predicted + delta_e_elas_predicted = {delta_e_mesh_pred:.8f} mJ",
                "delta_e_mesh_predicted_pct": f"+{delta_e_mesh_pct:.5f}%"
            },
            "point_prediction": {
                "delta_e_mesh_mJ": round(delta_e_mesh_pred, 8),
                "delta_e_mesh_pct": round(delta_e_mesh_pct, 5),
                "predicted_e_target_mJ": round(predicted_e_target, 8)
            },
            "uncertainty_interval": {
                "delta_e_mesh_min_mJ": round(delta_e_mesh_min_mJ, 8),
                "delta_e_mesh_max_mJ": round(delta_e_mesh_max_mJ, 8),
                "delta_e_mesh_min_pct": round(delta_e_mesh_min_pct, 5),
                "delta_e_mesh_max_pct": round(delta_e_mesh_max_pct, 5),
                "predicted_e_target_min_mJ": round(predicted_e_target_min, 8),
                "predicted_e_target_max_mJ": round(predicted_e_target_max, 8),
                "extrapolation_uncertainty_note": "Nominal prediction interval reflects +-0.200 percentage points around the point prediction. Evaluation of nominal interval coverage is kept distinct from diagnostic acceptance."
            }
        },
        "acceptance_criteria": {
            "dimensionless_residual_formula": "r_E = (E_target - E_source - Delta_E_mesh_predicted) / E_source",
            "residual_sign_convention": {
                "r_E_positive": "Excess target energy beyond predicted discretization sharpening (spurious hardening/ratcheting)",
                "r_E_negative": "Target energy deficit below predicted discretization sharpening (spurious dissipation/healing)",
                "r_E_zero": "Exact balance between target energy and independently predicted mesh-sharpened energy"
            },
            "predeclared_pass_band": {
                "max_abs_residual_pct": 0.25,
                "acceptance_condition": "|r_E| <= 0.25%"
            },
            "falsification_condition": {
                "falsification_threshold_pct": 0.50,
                "falsification_rule": "|r_E| > 0.50% falsifies the localized AT2 scaling model"
            }
        },
        "package_119_predecessor_record": {
            "package": "PACKAGE_119_C4_INC85_HOLDOUT",
            "job_id": "1417898.mmaster02",
            "measured_e_tot_mJ": 0.22974606,
            "predicted_e_tot_mJ": 0.23021699,
            "dimensionless_residual_r_E_pct": -0.20898,
            "diagnostic_acceptance_verdict": "PASS (|r_E| = 0.20898% <= 0.25000%)",
            "nominal_interval_verdict": "INTERVAL_MISS (measured 0.22974606 mJ is 0.00002094 mJ below nominal lower bound 0.22976699 mJ)",
            "classification": "HOLDOUT_PREDICTIVE_VALIDATION_PASSED"
        },
        "governance_status": {
            "original_gate_status": "C1_2_STEP2_ENERGY_GATE_FAILED (RETAINED, NOT CLEARED)",
            "package_113_status": "FAIL (+2.0080315% > 2.000000%)",
            "c5_remeshing_permitted": False,
            "role_of_holdout": "Prospective diagnostic verification only; does not retroactively alter Package 113 gate status"
        }
    }

    out_path = os.path.join(REPO_ROOT, "results/validation/increment_88_frozen_prediction.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(pred_data, f, indent=2)
    
    sha = sha256_file(out_path)
    print("=" * 80)
    print("INCREMENT-88 FROZEN PREDICTION CREATED AND LOCKED")
    print("=" * 80)
    print(f"Path: {out_path}")
    print(f"SHA-256: {sha}")
    print(f"Donor C3 Total Energy: {e_src_tot:.8f} mJ")
    print(f"Predicted Delta E_mesh: +{delta_e_mesh_pred:.8f} mJ (+{delta_e_mesh_pct:.5f}%)")
    print(f"Predicted C4 Target Energy: {predicted_e_target:.8f} mJ")
    print(f"Nominal Uncertainty Interval: [{predicted_e_target_min:.8f}, {predicted_e_target_max:.8f}] mJ")
    print(f"Predeclared Acceptance Band: |r_E| <= 0.25000%")
    print("=" * 80)
    return out_path, sha

if __name__ == "__main__":
    freeze_increment_88_prediction()

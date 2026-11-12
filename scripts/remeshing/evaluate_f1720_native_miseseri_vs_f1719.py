"""
F1720 Stage 3: Quantitative Evaluation of Native Abaqus MISESERI
from Direct UEL-UMAT Coupling vs Prior F1719 Companion Reconstruction.

Compares:
  1. Direct-coupled native MISESERI / MISESAVG on Layer 3 (ELSET=umatelem)
  2. Prior F1719 companion-reconstructed MISESERI / MISESAVG
  3. Element-wise correlation, ranking, and peak ligament localization
  4. Scale reconciliation vs published Figure 25(a) legend (2.20e-12)
"""

import os
import sys
import json
import math
from odbAccess import openOdb

def evaluate_native_miseseri():
    coupled_odb_path = r"D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\213_f1720_coarse_coupled\PK_F1720_COARSE_COUPLED.odb"
    f1719_rec_odb_path = r"D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\211_f1719_coarse_recovery\PK_F1719_REC_STATE2_DUMMY.odb"
    f1719_rec_json = r"D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\211_f1719_coarse_recovery\temp_recovery_fields.json"

    assert os.path.exists(coupled_odb_path), "Coupled ODB not found: " + coupled_odb_path

    print("=" * 80)
    print("F1720 STAGE 3: NATIVE ABAQUS MISESERI EVALUATION")
    print("=" * 80)

    odb_c = openOdb(coupled_odb_path, readOnly=True)

    print("Coupled ODB Steps:")
    for step_name, step in odb_c.steps.items():
        print("  Step %s: %d frames" % (step_name, len(step.frames)))

    # Step 1 last frame corresponds to u_y = 0.0050 mm (State 2)
    step1 = odb_c.steps['Step-1']
    frame_s2 = step1.frames[-1]
    print("\nEvaluating State 2 Frame (Step 1, Frame %d, Time = %.4f):" % (frame_s2.frameId, frame_s2.frameValue))

    # Extract field outputs
    miseseri_field = frame_s2.fieldOutputs['MISESERI'] if 'MISESERI' in frame_s2.fieldOutputs.keys() else None
    misesavg_field = frame_s2.fieldOutputs['MISESAVG'] if 'MISESAVG' in frame_s2.fieldOutputs.keys() else None
    s_field        = frame_s2.fieldOutputs['S'] if 'S' in frame_s2.fieldOutputs.keys() else None

    assert miseseri_field is not None, "MISESERI not found in frame!"
    assert misesavg_field is not None, "MISESAVG not found in frame!"

    print("Found MISESERI with %d values" % len(miseseri_field.values))
    print("Found MISESAVG with %d values" % len(misesavg_field.values))

    # Extract values for Layer 3 (elements 5495..8241 -> physical elements 1..2747)
    coupled_errors = {}
    miseseri_vals = []
    misesavg_vals = []
    eta_vals = []

    for i in range(len(miseseri_field.values)):
        val_e = miseseri_field.values[i]
        val_a = misesavg_field.values[i]
        elem_lbl = val_e.elementLabel

        # Layer 3 elements start at 5495
        if elem_lbl >= 5495:
            phys_idx = elem_lbl - 5494
        else:
            phys_idx = elem_lbl

        e_val = float(val_e.data)
        a_val = float(val_a.data)
        eta_val = (e_val / a_val * 100.0) if a_val > 0.0 else 0.0

        coupled_errors[phys_idx] = {
            "elem_lbl": elem_lbl,
            "phys_idx": phys_idx,
            "miseseri": e_val,
            "misesavg": a_val,
            "eta_pct": eta_val
        }
        miseseri_vals.append(e_val)
        misesavg_vals.append(a_val)
        eta_vals.append(eta_val)

    odb_c.close()

    max_eri = max(miseseri_vals)
    min_eri = min(miseseri_vals)
    mean_eri = sum(miseseri_vals) / len(miseseri_vals)

    max_avg = max(misesavg_vals)
    min_avg = min(misesavg_vals)
    mean_avg = sum(misesavg_vals) / len(misesavg_vals)

    max_eta = max(eta_vals)
    min_eta = min(eta_vals)
    mean_eta = sum(eta_vals) / len(eta_vals)

    print("\n--- Coupled Model Native MISESERI Statistics across %d Elements ---" % len(coupled_errors))
    print("  MISESERI:  Max = %.6e, Min = %.6e, Mean = %.6e" % (max_eri, min_eri, mean_eri))
    print("  MISESAVG:  Max = %.6e, Min = %.6e, Mean = %.6e" % (max_avg, min_avg, mean_avg))
    print("  Relative Error eta: Max = %.2f%%, Min = %.2f%%, Mean = %.2f%%" % (max_eta, min_eta, mean_eta))

    # Find peak elements
    sorted_by_eta = sorted(coupled_errors.values(), key=lambda x: x["eta_pct"], reverse=True)
    sorted_by_eri = sorted(coupled_errors.values(), key=lambda x: x["miseseri"], reverse=True)

    print("\nTop 5 Elements by Relative Error eta:")
    for rank, item in enumerate(sorted_by_eta[:5], 1):
        print("  #%d: PhysElem %d (Layer3 Elem %d): eta = %.2f%%, MISESERI = %.6e, MISESAVG = %.6e" %
              (rank, item["phys_idx"], item["elem_lbl"], item["eta_pct"], item["miseseri"], item["misesavg"]))

    print("\nTop 5 Elements by Raw MISESERI:")
    for rank, item in enumerate(sorted_by_eri[:5], 1):
        print("  #%d: PhysElem %d (Layer3 Elem %d): MISESERI = %.6e, MISESAVG = %.6e, eta = %.2f%%" %
              (rank, item["phys_idx"], item["elem_lbl"], item["miseseri"], item["misesavg"], item["eta_pct"]))

    # Comparison with F1719 Companion Recovery
    f1719_data = None
    if os.path.exists(f1719_rec_json):
        with open(f1719_rec_json, "r") as f:
            f1719_data = json.load(f)
        print("\nLoaded F1719 Companion Reference Data from: " + f1719_rec_json)

    correlation_r = None
    if f1719_data:
        # Compare element by element
        paired_coupled = []
        paired_f1719 = []

        for p_idx, c_info in coupled_errors.items():
            key_str = str(p_idx)
            if key_str in f1719_data:
                # In temp_recovery_fields.json, physical stress was in MPa
                # Relative error eta is scale invariant:
                f_info = f1719_data[key_str]
                f_eri = float(f_info["miseseri"])
                f_avg = float(f_info["misesavg"])
                f_eta = (f_eri / f_avg * 100.0) if f_avg > 0.0 else 0.0

                paired_coupled.append(c_info["eta_pct"])
                paired_f1719.append(f_eta)

        # Pearson correlation on relative error eta
        n_pairs = len(paired_coupled)
        if n_pairs > 1:
            mean_c = sum(paired_coupled) / n_pairs
            mean_f = sum(paired_f1719) / n_pairs
            cov = sum((paired_coupled[k] - mean_c) * (paired_f1719[k] - mean_f) for k in range(n_pairs))
            var_c = sum((paired_coupled[k] - mean_c)**2 for k in range(n_pairs))
            var_f = sum((paired_f1719[k] - mean_f)**2 for k in range(n_pairs))
            if var_c > 0.0 and var_f > 0.0:
                correlation_r = cov / math.sqrt(var_c * var_f)
                print("\nPearson Correlation r (Coupled Native eta vs F1719 Companion eta): %.6f across %d elements" %
                      (correlation_r, n_pairs))

    # Scale reconciliation with published Figure 25(a) legend (2.20e-12)
    pub_max_eri = 2.20e-12
    ratio_to_pub = max_eri / pub_max_eri
    print("\nScale Reconciliation with Published Figure 25(a) Legend:")
    print("  Published Legend Max: %.2e" % pub_max_eri)
    print("  Coupled Native Max:   %.2e" % max_eri)
    print("  Discrepancy Ratio:    %.2fx" % ratio_to_pub)

    # Save summary JSON
    out_json = r"D:\Master thesis\Adaptive remeshing\results\validation\f1720_native_miseseri_evaluation.json"
    eval_summary = {
        "num_elements": len(coupled_errors),
        "miseseri_stats": {
            "max": max_eri,
            "min": min_eri,
            "mean": mean_eri
        },
        "misesavg_stats": {
            "max": max_avg,
            "min": min_avg,
            "mean": mean_avg
        },
        "eta_stats": {
            "max_pct": max_eta,
            "min_pct": min_eta,
            "mean_pct": mean_eta
        },
        "top_5_eta_elements": sorted_by_eta[:5],
        "top_5_eri_elements": sorted_by_eri[:5],
        "pearson_correlation_vs_f1719": correlation_r,
        "ratio_to_published_legend": ratio_to_pub
    }

    with open(out_json, "w") as f:
        json.dump(eval_summary, f, indent=2)
    print("\nSaved evaluation summary to: " + out_json)

if __name__ == "__main__":
    evaluate_native_miseseri()

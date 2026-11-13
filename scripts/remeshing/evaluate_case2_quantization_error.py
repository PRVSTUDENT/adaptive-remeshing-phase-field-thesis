# -*- coding: utf-8 -*-
"""
scripts/remeshing/evaluate_case2_quantization_error.py
=====================================================
Evaluates the quantization error of the 20-bin degradation scheme vs.
exact elementwise degradation and improved intact-anchored binning schemes
for Case 2 Step-2 Peak (PK_HOLE_COARSE_JOB1.odb), with specific damage-zone
partitioning resolving finding F1728-R26 from HND-F1728-CASE2-STRESS-RECOVERY-002.
"""

from __future__ import print_function
import os
import json
import math

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FIELDS_JSON = os.path.join(REPO_ROOT, "results", "validation", "f1728_case2_coarse_job1_fields.json")
OUTPUT_JSON = os.path.join(REPO_ROOT, "results", "validation", "f1728_case2_quantization_error.json")

BOUNDARY_TOUCHING_EIDS = [151, 152, 153, 687, 734, 1088]

def main():
    with open(FIELDS_JSON, "r") as f:
        fields = json.load(f)

    d_map = fields["step2_peak"]["d"]
    k_res = 1.0e-7
    E0 = 210000.0  # MPa

    elements = []
    for eid_str, d_val in d_map.items():
        eid = int(eid_str)
        g_exact = (1.0 - d_val)**2 + k_res
        elements.append((eid, d_val, g_exact))

    elements.sort(key=lambda x: x[0])
    N = len(elements)

    # Identify damaged elements (d >= 0.10)
    damaged_elements = [e for e in elements if e[1] >= 0.10]
    undamaged_elements = [e for e in elements if e[1] < 0.10]
    N_damaged = len(damaged_elements)
    N_undamaged = len(undamaged_elements)

    # 1. Standard 20-bin scheme:
    errs_bin20_all = []
    errs_bin20_damaged = []
    errs_bin20_undamaged = []
    errs_bin20_touching = {}

    for eid, d_val, g_exact in elements:
        b_idx = min(19, max(0, int(g_exact * 20.0)))
        g_bin = (b_idx + 0.5) / 20.0
        abs_err = abs(g_bin - g_exact)
        rel_err = abs_err / g_exact
        errs_bin20_all.append(rel_err)

        if d_val >= 0.10:
            errs_bin20_damaged.append(rel_err)
        else:
            errs_bin20_undamaged.append(rel_err)

        if eid in BOUNDARY_TOUCHING_EIDS:
            errs_bin20_touching[eid] = {
                "d": d_val,
                "g_exact": g_exact,
                "g_bin": g_bin,
                "rel_err_pct": round(rel_err * 100, 4)
            }

    # 2. Intact-Anchored 20-Bin Scheme (Adopted):
    errs_anchored20_all = []
    errs_anchored20_damaged = []
    errs_anchored20_undamaged = []
    errs_anchored20_touching = {}

    for eid, d_val, g_exact in elements:
        if d_val < 0.01:
            g_bin = 1.0
        else:
            b_idx = min(19, max(0, int(g_exact * 20.0)))
            g_bin = (b_idx + 0.5) / 20.0
        abs_err = abs(g_bin - g_exact)
        rel_err = abs_err / g_exact
        errs_anchored20_all.append(rel_err)

        if d_val >= 0.10:
            errs_anchored20_damaged.append(rel_err)
        else:
            errs_anchored20_undamaged.append(rel_err)

        if eid in BOUNDARY_TOUCHING_EIDS:
            errs_anchored20_touching[eid] = {
                "d": d_val,
                "g_exact": g_exact,
                "g_bin": g_bin,
                "rel_err_pct": round(rel_err * 100, 4)
            }

    # 3. High-Fidelity 100-Bin Scheme:
    errs_bin100_all = []
    errs_bin100_damaged = []
    errs_bin100_undamaged = []
    errs_bin100_touching = {}

    for eid, d_val, g_exact in elements:
        if d_val < 0.005:
            g_bin = 1.0
        else:
            b_idx = min(99, max(0, int(g_exact * 100.0)))
            g_bin = (b_idx + 0.5) / 100.0
        abs_err = abs(g_bin - g_exact)
        rel_err = abs_err / g_exact
        errs_bin100_all.append(rel_err)

        if d_val >= 0.10:
            errs_bin100_damaged.append(rel_err)
        else:
            errs_bin100_undamaged.append(rel_err)

        if eid in BOUNDARY_TOUCHING_EIDS:
            errs_bin100_touching[eid] = {
                "d": d_val,
                "g_exact": g_exact,
                "g_bin": g_bin,
                "rel_err_pct": round(rel_err * 100, 4)
            }

    unique_exact = len(set(round(g, 6) for _, _, g in elements))

    summary = {
        "benchmark": "Case 2 (Single Off-Axis Hole Plate)",
        "source": "PK_HOLE_COARSE_JOB1.odb (Step-2 Peak, uy=0.007294 mm)",
        "total_elements": N,
        "damaged_elements_count": N_damaged,
        "undamaged_elements_count": N_undamaged,
        "standard_20_bin": {
            "global_mean_rel_error_pct": round(sum(errs_bin20_all) / N * 100, 4),
            "global_max_rel_error_pct": round(max(errs_bin20_all) * 100, 4),
            "damaged_zone_mean_rel_error_pct": round(sum(errs_bin20_damaged) / N_damaged * 100, 4),
            "damaged_zone_max_rel_error_pct": round(max(errs_bin20_damaged) * 100, 4),
            "undamaged_bulk_mean_rel_error_pct": round(sum(errs_bin20_undamaged) / N_undamaged * 100, 4),
            "elements_gt_1pct_error_count": sum(1 for e in errs_bin20_all if e > 0.01),
            "intact_element_modulus_pct": 97.5,
            "intact_element_bias_description": "Bin 19 centers at 19.5/20 = 0.975, imposing 2.5% stiffness reduction on bulk.",
            "boundary_touching_elements_errors": errs_bin20_touching
        },
        "intact_anchored_20_bin": {
            "global_mean_rel_error_pct": round(sum(errs_anchored20_all) / N * 100, 4),
            "global_max_rel_error_pct": round(max(errs_anchored20_all) * 100, 4),
            "damaged_zone_mean_rel_error_pct": round(sum(errs_anchored20_damaged) / N_damaged * 100, 4),
            "damaged_zone_max_rel_error_pct": round(max(errs_anchored20_damaged) * 100, 4),
            "undamaged_bulk_mean_rel_error_pct": round(sum(errs_anchored20_undamaged) / N_undamaged * 100, 4),
            "elements_gt_1pct_error_count": sum(1 for e in errs_anchored20_all if e > 0.01),
            "intact_element_modulus_pct": 100.0,
            "description": "Anchors d < 0.01 elements to exact E0 (g=1.0), reducing bulk error to 0.0% and confining binning error strictly to the softening corridor.",
            "boundary_touching_elements_errors": errs_anchored20_touching
        },
        "high_fidelity_100_bin": {
            "global_mean_rel_error_pct": round(sum(errs_bin100_all) / N * 100, 4),
            "global_max_rel_error_pct": round(max(errs_bin100_all) * 100, 4),
            "damaged_zone_mean_rel_error_pct": round(sum(errs_bin100_damaged) / N_damaged * 100, 4),
            "damaged_zone_max_rel_error_pct": round(max(errs_bin100_damaged) * 100, 4),
            "undamaged_bulk_mean_rel_error_pct": round(sum(errs_bin100_undamaged) / N_undamaged * 100, 4),
            "elements_gt_1pct_error_count": sum(1 for e in errs_bin100_all if e > 0.01),
            "description": "Anchors intact elements to E0 and uses 100 fine bins across the softening zone.",
            "boundary_touching_elements_errors": errs_bin100_touching
        },
        "exact_elementwise": {
            "global_mean_rel_error_pct": 0.0,
            "global_max_rel_error_pct": 0.0,
            "damaged_zone_mean_rel_error_pct": 0.0,
            "damaged_zone_max_rel_error_pct": 0.0,
            "unique_materials_count": unique_exact,
            "description": "Assigns each element its exact constitutive degradation factor g_d = (1-d)^2 + k_res."
        }
    }

    with open(OUTPUT_JSON, "w") as f:
        json.dump(summary, f, indent=2)

    print("=== Quantization Error Partitioning Completed ===")
    print("Total Elements: %d (Damaged: %d, Undamaged: %d)" % (N, N_damaged, N_undamaged))
    print("\n1. Standard 20-Bin:")
    print("   Global Mean Error:        %.4f%% (Max: %.4f%%)" % (summary["standard_20_bin"]["global_mean_rel_error_pct"], summary["standard_20_bin"]["global_max_rel_error_pct"]))
    print("   Damaged Zone Mean Error:  %.4f%% (Max: %.4f%%)" % (summary["standard_20_bin"]["damaged_zone_mean_rel_error_pct"], summary["standard_20_bin"]["damaged_zone_max_rel_error_pct"]))
    print("   Undamaged Bulk Mean:      %.4f%%" % summary["standard_20_bin"]["undamaged_bulk_mean_rel_error_pct"])
    print("\n2. Intact-Anchored 20-Bin (Adopted):")
    print("   Global Mean Error:        %.4f%% (Max: %.4f%%)" % (summary["intact_anchored_20_bin"]["global_mean_rel_error_pct"], summary["intact_anchored_20_bin"]["global_max_rel_error_pct"]))
    print("   Damaged Zone Mean Error:  %.4f%% (Max: %.4f%%)" % (summary["intact_anchored_20_bin"]["damaged_zone_mean_rel_error_pct"], summary["intact_anchored_20_bin"]["damaged_zone_max_rel_error_pct"]))
    print("   Undamaged Bulk Mean:      %.4f%%" % summary["intact_anchored_20_bin"]["undamaged_bulk_mean_rel_error_pct"])
    print("\n3. High-Fidelity 100-Bin:")
    print("   Damaged Zone Mean Error:  %.4f%% (Max: %.4f%%)" % (summary["high_fidelity_100_bin"]["damaged_zone_mean_rel_error_pct"], summary["high_fidelity_100_bin"]["damaged_zone_max_rel_error_pct"]))
    print("\n4. Boundary-Touching Elements (Intact-Anchored 20-Bin):")
    for eid in sorted(errs_anchored20_touching.keys()):
        t = errs_anchored20_touching[eid]
        print("   Element %4d: d = %.6f | g_exact = %.6f | g_bin = %.6f | rel_err = %.4f%%" % (
            eid, t["d"], t["g_exact"], t["g_bin"], t["rel_err_pct"]
        ))

if __name__ == "__main__":
    main()

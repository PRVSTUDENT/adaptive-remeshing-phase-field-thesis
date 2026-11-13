# -*- coding: utf-8 -*-
"""
scripts/remeshing/evaluate_case2_quantization_error.py
=====================================================
Evaluates the quantization error of the 20-bin degradation scheme vs.
exact elementwise degradation and improved intact-anchored binning schemes
for Case 2 Step-2 Peak (PK_HOLE_COARSE_JOB1.odb).
"""

from __future__ import print_function
import os
import json
import math

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FIELDS_JSON = os.path.join(REPO_ROOT, "results", "validation", "f1728_case2_coarse_job1_fields.json")
OUTPUT_JSON = os.path.join(REPO_ROOT, "results", "validation", "f1728_case2_quantization_error.json")

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

    # 1. Standard 20-bin scheme (historical F1719 approach):
    # b_i = min(19, max(0, int(g_exact * 20.0)))
    # g_bin20 = (b_i + 0.5) / 20.0
    errs_bin20_rel = []
    errs_bin20_abs = []
    for eid, d_val, g_exact in elements:
        b_idx = min(19, max(0, int(g_exact * 20.0)))
        g_bin = (b_idx + 0.5) / 20.0
        abs_err = abs(g_bin - g_exact)
        rel_err = abs_err / g_exact
        errs_bin20_abs.append(abs_err)
        errs_bin20_rel.append(rel_err)

    mean_rel_20 = sum(errs_bin20_rel) / N
    max_rel_20 = max(errs_bin20_rel)
    gt_1pct_20 = sum(1 for e in errs_bin20_rel if e > 0.01)

    print("Standard 20-Bin Scheme:")
    print("  Mean relative error: %.4f%%" % (mean_rel_20 * 100))
    print("  Max relative error:  %.4f%%" % (max_rel_20 * 100))
    print("  Elements > 1%% rel error: %d / %d (%.1f%%)" % (gt_1pct_20, N, 100.0 * gt_1pct_20 / N))

    # 2. Intact-Anchored 20-Bin Scheme:
    # Separate intact/elastic bulk (d < 0.01 or bin 20): g = 1.0 exactly
    # Softening range partitioned into 20 bins
    errs_anchored20_rel = []
    errs_anchored20_abs = []
    for eid, d_val, g_exact in elements:
        if d_val < 0.01:
            g_bin = 1.0
        else:
            # 20 bins in [0, 1)
            b_idx = min(19, max(0, int(g_exact * 20.0)))
            g_bin = (b_idx + 0.5) / 20.0
        abs_err = abs(g_bin - g_exact)
        rel_err = abs_err / g_exact
        errs_anchored20_abs.append(abs_err)
        errs_anchored20_rel.append(rel_err)

    mean_rel_anc20 = sum(errs_anchored20_rel) / N
    max_rel_anc20 = max(errs_anchored20_rel)
    gt_1pct_anc20 = sum(1 for e in errs_anchored20_rel if e > 0.01)

    print("\nIntact-Anchored 20-Bin Scheme:")
    print("  Mean relative error: %.4f%%" % (mean_rel_anc20 * 100))
    print("  Max relative error:  %.4f%%" % (max_rel_anc20 * 100))
    print("  Elements > 1%% rel error: %d / %d (%.1f%%)" % (gt_1pct_anc20, N, 100.0 * gt_1pct_anc20 / N))

    # 3. High-Fidelity 100-Bin Scheme:
    # Intact elements (d < 0.005): g = 1.0
    # Softening range: 100 bins
    errs_bin100_rel = []
    errs_bin100_abs = []
    for eid, d_val, g_exact in elements:
        if d_val < 0.005:
            g_bin = 1.0
        else:
            b_idx = min(99, max(0, int(g_exact * 100.0)))
            g_bin = (b_idx + 0.5) / 100.0
        abs_err = abs(g_bin - g_exact)
        rel_err = abs_err / g_exact
        errs_bin100_abs.append(abs_err)
        errs_bin100_rel.append(rel_err)

    mean_rel_100 = sum(errs_bin100_rel) / N
    max_rel_100 = max(errs_bin100_rel)
    gt_1pct_100 = sum(1 for e in errs_bin100_rel if e > 0.01)

    print("\nHigh-Fidelity 100-Bin Scheme (Intact-Anchored):")
    print("  Mean relative error: %.4f%%" % (mean_rel_100 * 100))
    print("  Max relative error:  %.4f%%" % (max_rel_100 * 100))
    print("  Elements > 1%% rel error: %d / %d (%.1f%%)" % (gt_1pct_100, N, 100.0 * gt_1pct_100 / N))

    # 4. Exact Elementwise Degradation:
    # 2906 distinct materials or 1 material per unique rounded modulus
    # Let's count how many unique materials if rounded to 3 decimal places vs exact
    unique_exact = len(set(round(g, 6) for _, _, g in elements))
    print("\nExact Elementwise Degradation:")
    print("  Unique degradation values: %d across %d elements" % (unique_exact, N))
    print("  Mean relative error: 0.0000%")
    print("  Max relative error:  0.0000%")

    summary = {
        "benchmark": "Case 2 (Single Off-Axis Hole Plate)",
        "source": "PK_HOLE_COARSE_JOB1.odb (Step-2 Peak, uy=0.007294 mm)",
        "total_elements": N,
        "standard_20_bin": {
            "mean_relative_error_pct": round(mean_rel_20 * 100, 4),
            "max_relative_error_pct": round(max_rel_20 * 100, 4),
            "elements_gt_1pct_error_count": gt_1pct_20,
            "elements_gt_1pct_error_ratio": round(float(gt_1pct_20) / N, 4),
            "intact_element_modulus_pct": 97.5,
            "intact_element_bias_description": "Bin 19 centers at 19.5/20 = 0.975, introducing a systematic 2.5% stiffness drop on undamaged bulk."
        },
        "intact_anchored_20_bin": {
            "mean_relative_error_pct": round(mean_rel_anc20 * 100, 4),
            "max_relative_error_pct": round(max_rel_anc20 * 100, 4),
            "elements_gt_1pct_error_count": gt_1pct_anc20,
            "intact_element_modulus_pct": 100.0,
            "description": "Anchors d < 0.01 elements to exact E0 (g=1.0), reducing bulk error to 0.0% and confining bin error strictly to the softening corridor."
        },
        "high_fidelity_100_bin": {
            "mean_relative_error_pct": round(mean_rel_100 * 100, 4),
            "max_relative_error_pct": round(max_rel_100 * 100, 4),
            "elements_gt_1pct_error_count": gt_1pct_100,
            "description": "Anchors intact elements to E0 and uses 100 fine bins across the softening zone."
        },
        "exact_elementwise": {
            "mean_relative_error_pct": 0.0,
            "max_relative_error_pct": 0.0,
            "unique_materials_count": unique_exact,
            "description": "Assigns each element its exact constitutive degradation factor g_d = (1-d)^2 + k_res."
        }
    }

    with open(OUTPUT_JSON, "w") as f:
        json.dump(summary, f, indent=2)
    print("\nSaved quantization evaluation to: %s" % OUTPUT_JSON)

if __name__ == "__main__":
    main()

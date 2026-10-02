"""
postprocess_mechanical_parity.py
Audits bit-for-bit or tight numerical parity between a diagnostic candidate run and an uninstrumented baseline reference.

Frozen Acceptance Criteria:
1. Initial Elastic Stiffness K0 (OLS with intercept, 0 < u <= 0.0010 mm, N=400): |Delta K0| / K0 <= 0.05%
2. Peak Reaction Force F_max: |Delta F_max| / F_max <= 0.05%
3. Peak Displacement u_peak: |Delta u_peak| <= 1.0e-4 mm (0.1 um)
4. Pre-peak Curve Parity (0 <= u <= u_peak): max |Delta F(u)| / F_max <= 0.05%
5. Full Common-Horizon Curve Parity (0 <= u <= u_common_max): max |Delta F(u)| / F_max <= 0.10%

Execution Rules:
- Monotone displacement interpolation over common displacement domain.
- No extrapolation beyond common displacement range.
- No frame-index matching across steps.
- Duplicate Step-1-terminal / Step-2-initial state removed before evaluation.
"""
import os
import sys
import json
import math

def deduplicate_curve(curve):
    """
    Deduplicates consecutive identical (u, rf) states across step boundaries.
    curve: list of (step_name, u_val, rf_val)
    """
    if not curve:
        return []
    dedup = [curve[0]]
    for pt in curve[1:]:
        prev = dedup[-1]
        if abs(pt[1] - prev[1]) < 1e-15 and abs(pt[2] - prev[2]) < 1e-15:
            continue
        dedup.append(pt)
    return dedup

def interp_1d(x_q, x_arr, y_arr):
    """
    Piecewise linear interpolation at query point x_q given strictly increasing x_arr.
    Returns interpolated y value.
    """
    if x_q <= x_arr[0]:
        return y_arr[0]
    if x_q >= x_arr[-1]:
        return y_arr[-1]
    
    # Binary search for interval
    lo = 0
    hi = len(x_arr) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if x_arr[mid] <= x_q:
            lo = mid
        else:
            hi = mid
    
    x0, x1 = x_arr[lo], x_arr[hi]
    y0, y1 = y_arr[lo], y_arr[hi]
    if abs(x1 - x0) < 1e-18:
        return y0
    frac = (x_q - x0) / (x1 - x0)
    return y0 + frac * (y1 - y0)

def compute_k0_ols(curve):
    """
    Computes initial structural stiffness K0 via unconstrained OLS with intercept
    on active elastic increments (0 < u <= 0.0010001 mm).
    """
    active = [pt for pt in curve if pt[1] > 1e-9 and pt[1] <= 0.0010001]
    if len(active) < 2:
        return 0.0, 0.0, 0.0, len(active)
    n = len(active)
    u_vals = [p[1] for p in active]
    f_vals = [p[2] for p in active]
    mean_u = sum(u_vals) / n
    mean_f = sum(f_vals) / n
    var_u = sum((x - mean_u)**2 for x in u_vals)
    if var_u == 0:
        return 0.0, 0.0, 0.0, n
    cov_uf = sum((x - mean_u)*(y - mean_f) for x, y in zip(u_vals, f_vals))
    k0 = cov_uf / var_u
    b0 = mean_f - k0 * mean_u
    ss_res = sum((y - (k0*x + b0))**2 for x, y in zip(u_vals, f_vals))
    ss_tot = sum((y - mean_f)**2 for y in f_vals)
    r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 1.0
    return k0, b0, r2, n

def audit_mechanical_parity(cand_curve_raw, ref_curve_raw, tol_f_exact=1e-8, tol_u_exact=1e-12):
    """
    Audits mechanical parity against frozen tolerance thresholds.
    cand_curve_raw: list of (step_name, u_val, rf_val)
    ref_curve_raw:  list of (step_name, u_val, rf_val)
    """
    results = {
        "status": "UNKNOWN",
        "cand_raw_points": len(cand_curve_raw),
        "ref_raw_points": len(ref_curve_raw),
        "cand_dedup_points": 0,
        "ref_dedup_points": 0,
        "k0_cand": 0.0,
        "k0_ref": 0.0,
        "k0_rel_error_pct": 0.0,
        "k0_cand_r2": 0.0,
        "k0_ref_r2": 0.0,
        "f_max_cand": 0.0,
        "f_max_ref": 0.0,
        "f_max_rel_error_pct": 0.0,
        "u_peak_cand": 0.0,
        "u_peak_ref": 0.0,
        "u_peak_abs_error_mm": 0.0,
        "pre_peak_max_abs_df": 0.0,
        "pre_peak_max_rel_df_pct": 0.0,
        "common_horizon_max_abs_df": 0.0,
        "common_horizon_max_rel_df_pct": 0.0,
        "max_exact_delta_u": 0.0,
        "max_exact_delta_f": 0.0,
        "parity_classification": "UNKNOWN",
        "failures": []
    }

    if not cand_curve_raw or not ref_curve_raw:
        results["status"] = "FAIL_EMPTY_CURVE"
        results["failures"].append("One or both input curves are empty.")
        return results

    cand_curve = deduplicate_curve(cand_curve_raw)
    ref_curve = deduplicate_curve(ref_curve_raw)
    results["cand_dedup_points"] = len(cand_curve)
    results["ref_dedup_points"] = len(ref_curve)

    # 1. K0 Extraction
    k0_c, b0_c, r2_c, n_c = compute_k0_ols(cand_curve)
    k0_r, b0_r, r2_r, n_r = compute_k0_ols(ref_curve)
    results["k0_cand"] = k0_c
    results["k0_ref"] = k0_r
    results["k0_cand_r2"] = r2_c
    results["k0_ref_r2"] = r2_r
    if k0_r > 0:
        results["k0_rel_error_pct"] = abs(k0_c - k0_r) / k0_r * 100.0

    # 2. Peak Force and Peak Displacement
    f_max_c = -1e30
    u_peak_c = 0.0
    for pt in cand_curve:
        if pt[2] > f_max_c:
            f_max_c = pt[2]
            u_peak_c = pt[1]
    
    f_max_r = -1e30
    u_peak_r = 0.0
    for pt in ref_curve:
        if pt[2] > f_max_r:
            f_max_r = pt[2]
            u_peak_r = pt[1]

    results["f_max_cand"] = f_max_c
    results["f_max_ref"] = f_max_r
    results["u_peak_cand"] = u_peak_c
    results["u_peak_ref"] = u_peak_r
    if f_max_r > 0:
        results["f_max_rel_error_pct"] = abs(f_max_c - f_max_r) / f_max_r * 100.0
    results["u_peak_abs_error_mm"] = abs(u_peak_c - u_peak_r)

    # 3. Curve Interpolation over Common Horizon
    u_c_arr = [p[1] for p in cand_curve]
    f_c_arr = [p[2] for p in cand_curve]
    u_r_arr = [p[1] for p in ref_curve]
    f_r_arr = [p[2] for p in ref_curve]

    u_min_common = max(u_c_arr[0], u_r_arr[0])
    u_max_common = min(u_c_arr[-1], u_r_arr[-1])
    u_peak_common = min(u_peak_c, u_peak_r)

    # Sample evaluation grid at union of all distinct u values in common range
    grid_u = sorted(list(set(
        [u for u in u_c_arr if u_min_common <= u <= u_max_common] +
        [u for u in u_r_arr if u_min_common <= u <= u_max_common]
    )))

    pre_peak_max_df = 0.0
    common_max_df = 0.0

    for u_q in grid_u:
        f_cand_interp = interp_1d(u_q, u_c_arr, f_c_arr)
        f_ref_interp = interp_1d(u_q, u_r_arr, f_r_arr)
        df = abs(f_cand_interp - f_ref_interp)

        if df > common_max_df:
            common_max_df = df
        if u_q <= u_peak_common + 1e-12:
            if df > pre_peak_max_df:
                pre_peak_max_df = df

    f_norm = f_max_r if f_max_r > 0 else 1.0
    results["pre_peak_max_abs_df"] = pre_peak_max_df
    results["pre_peak_max_rel_df_pct"] = (pre_peak_max_df / f_norm) * 100.0
    results["common_horizon_max_abs_df"] = common_max_df
    results["common_horizon_max_rel_df_pct"] = (common_max_df / f_norm) * 100.0

    # 4. Point-by-point exact matching if points are identical length
    if len(cand_curve) == len(ref_curve):
        max_du_exact = max(abs(c[1] - r[1]) for c, r in zip(cand_curve, ref_curve))
        max_df_exact = max(abs(c[2] - r[2]) for c, r in zip(cand_curve, ref_curve))
        results["max_exact_delta_u"] = max_du_exact
        results["max_exact_delta_f"] = max_df_exact
    else:
        results["max_exact_delta_u"] = None
        results["max_exact_delta_f"] = None

    # 5. Threshold Checks
    # Criterion 1: |Delta K0|/K0 <= 0.05%
    if results["k0_rel_error_pct"] > 0.05:
        results["failures"].append(f"K0 relative difference ({results['k0_rel_error_pct']:.4f}%) exceeds 0.05% threshold.")
    # Criterion 2: |Delta F_max|/F_max <= 0.05%
    if results["f_max_rel_error_pct"] > 0.05:
        results["failures"].append(f"F_max relative difference ({results['f_max_rel_error_pct']:.4f}%) exceeds 0.05% threshold.")
    # Criterion 3: |Delta u_peak| <= 1.0e-4 mm
    if results["u_peak_abs_error_mm"] > 1.0e-4:
        results["failures"].append(f"u_peak absolute difference ({results['u_peak_abs_error_mm']:.6e} mm) exceeds 1.0e-4 mm threshold.")
    # Criterion 4: pre-peak max normalized df <= 0.05%
    if results["pre_peak_max_rel_df_pct"] > 0.05:
        results["failures"].append(f"Pre-peak curve residual ({results['pre_peak_max_rel_df_pct']:.4f}%) exceeds 0.05% threshold.")
    # Criterion 5: full common-horizon max normalized df <= 0.10%
    if results["common_horizon_max_rel_df_pct"] > 0.10:
        results["failures"].append(f"Full common-horizon residual ({results['common_horizon_max_rel_df_pct']:.4f}%) exceeds 0.10% threshold.")

    # Classification
    if len(results["failures"]) == 0:
        results["status"] = "PASS"
        if results["max_exact_delta_f"] == 0.0 and results["max_exact_delta_u"] == 0.0:
            results["parity_classification"] = "FROZEN_MECHANICAL_PARITY_EXACT_BIT_MATCH"
        elif (results["max_exact_delta_f"] is not None and results["max_exact_delta_f"] <= tol_f_exact and
              results["max_exact_delta_u"] is not None and results["max_exact_delta_u"] <= tol_u_exact):
            results["parity_classification"] = "FROZEN_MECHANICAL_PARITY_TIGHT_NUMERICAL_PASS"
        else:
            results["parity_classification"] = "FROZEN_MECHANICAL_PARITY_INTERPOLATED_PASS"
    else:
        results["status"] = "FAIL"
        results["parity_classification"] = "MECHANICAL_PARITY_VIOLATION"

    return results

if __name__ == "__main__":
    print("Upgraded Mechanical Parity Module (Two-Curve Thresholds) loaded successfully.")

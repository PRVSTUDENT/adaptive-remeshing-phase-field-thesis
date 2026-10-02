# -*- coding: utf-8 -*-
"""
Generic Mode-I Batch Candidate Terminal Evaluator Pipeline
Protocol Version: 2
Governing Directive: "We need to have understood everything related to the first model before we increase complexity."

This module evaluates ANY Mode-I candidate solve (S1, S2, S3, T1, T2, T3, L1, L2, L3, Adaptive 13.9k)
consuming the canonical reference rules defined in REFERENCE_EXTRACTION_RULES.json:
1. Force Sign Convention: F = -RF2_RP (tensile reaction force at top RP 999999). Bare |RF2| is strictly forbidden.
2. Initial Stiffness K0: Linear regression on initial elastic increments using canonical half-bin window
   rule: (u > 0.5 * delta_u) & (u <= 0.0010 + 0.5 * delta_u), yielding N=400 points and K0 = 137.945520 kN/mm on S1.
3. Monotonic Trapezoidal Work: W_ext = \\int_0^u F(u') du' without extrapolation beyond solved frames.
4. SDV Deduplication: Single-value aggregation per unique finite element (seen = set()) to prevent 4x Gauss point overcounting.
5. Global Energy Bookkeeping: E_model = E_elas + E_frac, Delta_book = E_model - W_ext.
   Classified as a DESCRIPTIVE_DIAGNOSTIC_ONLY metric (no arbitrary pass/fail rejection).
6. Family Classification:
   - Spatial Convergence (S1 -> S2 -> S3)
   - Temporal Convergence (T1 -> T2/S1 -> T3)
   - Length-Scale Characterization (L1/S3 -> L2 -> L3) [Material sensitivity, NOT mesh convergence]
   - Adaptive Refinement (Efficiency-calibrated 2% variant, 13,897 elements)
"""

import os
import sys
import math
import json
import csv

# Canonical Reference Anchors from REFERENCE_EXTRACTION_RULES.json
CANONICAL_REFERENCE = {
    "job_id": "1409734.mmaster02",
    "elements": 15192,
    "nodes": 15521,
    "mesh_size_h_mm": 0.0030,
    "l0_mm": 0.0075,
    "delta_u_mm": 5.0e-4,
    "K0_kN_per_mm": 137.945520,
    "K0_exact_float": 137.945519645084,
    "K0_intercept_kN": 4.472368e-5,
    "K0_intercept_exact_float": 4.472367510151e-05,
    "K0_R2": 0.99999960,
    "K0_R2_exact_float": 0.999999599540,
    "K0_fit_points_canonical": 400,
    "K0_fit_max_u_mm": 0.0010,
    "F_max_kN": 0.757778,
    "u_at_F_max_mm": 0.005857,
    "t_ref_mm": 1.0,
    "W_ext_final_mJ": 2.359329,
    "E_elas_final_mJ": 0.001161,
    "E_frac_final_mJ": 2.340220,
    "E_model_final_mJ": 2.341381,
    "Delta_book_final_mJ": -0.017949,
    "eps_book_abs_pct": 0.76077,
    "published_pandey_kumar_2025": {
        "citation": "Pandey & Kumar (2025), CMES 144(3):3251-3276, DOI: 10.32604/cmes.2025.067858",
        "reported_error_target": "1.0%",
        "reported_elements": 13941,
        "reported_F_max_kN": 0.758,
        "reported_u_peak_mm": 0.005860
    }
}

CANDIDATE_CATALOG = {
    "S1": {
        "candidate_id": "S1",
        "name": "PK_M1_REF15K_ENERGY",
        "family": "SPATIAL_CONVERGENCE",
        "package_dir": "16_energy_qualification_reference_15k",
        "elements": 15192,
        "mesh_size_h_mm": 0.0030,
        "l0_mm": 0.0075,
        "dt_step1_mm": 5.0e-4,
        "dt_step2_mm": 2.0e-4,
        "role": "SPATIAL_BASELINE_ANCHOR"
    },
    "S2": {
        "candidate_id": "S2",
        "name": "PK_M1_S2_ENERGY",
        "family": "SPATIAL_CONVERGENCE",
        "package_dir": "12_fixed_convergence_h0020",
        "elements": 32184,
        "mesh_size_h_mm": 0.0020,
        "l0_mm": 0.0075,
        "dt_step1_mm": 5.0e-4,
        "dt_step2_mm": 2.0e-4,
        "role": "SPATIAL_INTERMEDIATE"
    },
    "S3": {
        "candidate_id": "S3",
        "name": "PK_M1_S3_ENERGY",
        "family": "SPATIAL_CONVERGENCE",
        "package_dir": "13_fixed_convergence_h0015",
        "elements": 41912,
        "mesh_size_h_mm": 0.0015,
        "l0_mm": 0.0075,
        "dt_step1_mm": 5.0e-4,
        "dt_step2_mm": 2.0e-4,
        "role": "SPATIAL_FINE"
    },
    "T1": {
        "candidate_id": "T1",
        "name": "PK_MODE1_T1_COARSE_ENERGY",
        "family": "TEMPORAL_CONVERGENCE",
        "package_dir": "17_temporal_convergence_t1_coarse",
        "elements": 15192,
        "mesh_size_h_mm": 0.0030,
        "l0_mm": 0.0075,
        "dt_step1_mm": 1.0e-3,
        "dt_step2_mm": 4.0e-4,
        "role": "TEMPORAL_COARSE"
    },
    "T2": {
        "candidate_id": "T2",
        "name": "PK_MODE1_T2_NOMINAL_ENERGY",
        "family": "TEMPORAL_CONVERGENCE",
        "package_dir": "18_temporal_convergence_t2_nominal",
        "elements": 15192,
        "mesh_size_h_mm": 0.0030,
        "l0_mm": 0.0075,
        "dt_step1_mm": 5.0e-4,
        "dt_step2_mm": 2.0e-4,
        "role": "TEMPORAL_NOMINAL_REUSES_S1"
    },
    "T3": {
        "candidate_id": "T3",
        "name": "PK_MODE1_T3_FINE_ENERGY",
        "family": "TEMPORAL_CONVERGENCE",
        "package_dir": "19_temporal_convergence_t3_fine",
        "elements": 15192,
        "mesh_size_h_mm": 0.0030,
        "l0_mm": 0.0075,
        "dt_step1_mm": 2.5e-4,
        "dt_step2_mm": 1.0e-4,
        "role": "TEMPORAL_FINE"
    },
    "L1": {
        "candidate_id": "L1",
        "name": "PK_MODE1_L1_BASELINE_ENERGY",
        "family": "LENGTH_SCALE_CHARACTERIZATION",
        "package_dir": "20_length_scale_l1_baseline",
        "elements": 41912,
        "mesh_size_h_mm": 0.0015,
        "l0_mm": 0.0075,
        "dt_step1_mm": 5.0e-4,
        "dt_step2_mm": 2.0e-4,
        "role": "LENGTH_SCALE_BASELINE_REUSES_S3"
    },
    "L2": {
        "candidate_id": "L2",
        "name": "PK_M1_L2_L01125_ENERGY",
        "family": "LENGTH_SCALE_CHARACTERIZATION",
        "package_dir": "21_length_scale_l2_intermediate",
        "elements": 41912,
        "mesh_size_h_mm": 0.0015,
        "l0_mm": 0.01125,
        "dt_step1_mm": 5.0e-4,
        "dt_step2_mm": 2.0e-4,
        "role": "LENGTH_SCALE_INTERMEDIATE"
    },
    "L3": {
        "candidate_id": "L3",
        "name": "PK_M1_L3_L01500_ENERGY",
        "family": "LENGTH_SCALE_CHARACTERIZATION",
        "package_dir": "22_length_scale_l3_coarse",
        "elements": 41912,
        "mesh_size_h_mm": 0.0015,
        "l0_mm": 0.01500,
        "dt_step1_mm": 5.0e-4,
        "dt_step2_mm": 2.0e-4,
        "role": "LENGTH_SCALE_COARSE"
    },
    "ADAPT_13K": {
        "candidate_id": "ADAPT_13K",
        "name": "PK_M1_ADAPT_2PCT_13K_ENERGY",
        "family": "ADAPTIVE_REFINEMENT",
        "package_dir": "24_adaptive_candidate_2pct_13k",
        "elements": 13897,
        "mesh_size_h_mm": None,
        "l0_mm": 0.0075,
        "dt_step1_mm": 5.0e-4,
        "dt_step2_mm": 2.0e-4,
        "role": "ADAPTIVE_EFFICIENCY_CALIBRATED_2PCT"
    }
}


def load_rules_json(rules_path=None):
    """Loads REFERENCE_EXTRACTION_RULES.json with fallback paths."""
    candidates = [
        rules_path,
        os.path.join(os.getcwd(), "models", "pandey_kumar_mode1", "REFERENCE_EXTRACTION_RULES.json"),
        os.path.join(os.path.dirname(__file__), "..", "..", "models", "pandey_kumar_mode1", "REFERENCE_EXTRACTION_RULES.json"),
        r"D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\REFERENCE_EXTRACTION_RULES.json"
    ]
    for c in candidates:
        if c and os.path.exists(c):
            with open(c, 'r', encoding='utf-8') as f:
                return json.load(f)
    return None


def linear_regression(x_vals, y_vals):
    """Computes ordinary least squares linear regression slope, intercept, and R^2."""
    n = len(x_vals)
    if n < 2:
        return 0.0, 0.0, 0.0
    sum_x = float(sum(x_vals))
    sum_y = float(sum(y_vals))
    sum_xx = float(sum(x * x for x in x_vals))
    sum_yy = float(sum(y * y for y in y_vals))
    sum_xy = float(sum(x * y for x, y in zip(x_vals, y_vals)))
    
    denom = n * sum_xx - sum_x * sum_x
    if abs(denom) < 1e-20:
        return 0.0, 0.0, 0.0
    slope = (n * sum_xy - sum_x * sum_y) / denom
    intercept = (sum_y - slope * sum_x) / n
    
    ss_tot = sum((y - (sum_y / n)) ** 2 for y in y_vals)
    ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(x_vals, y_vals))
    r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 1e-20 else 1.0
    return slope, intercept, r2


def compute_trapezoidal_work(u_vals, f_vals):
    """
    Integrates external work W_ext = \\int_0^u F(u') du' using trapezoidal rule.
    Strictly forbids out-of-bounds extrapolation.
    """
    if not u_vals or not f_vals or len(u_vals) != len(f_vals):
        return []
    
    w_cum = 0.0
    w_vals = [0.0]
    for i in range(1, len(u_vals)):
        du = u_vals[i] - u_vals[i-1]
        if du < -1e-12:
            raise ValueError("Non-monotonic displacement sequence detected: du = %e at index %d" % (du, i))
        dw = 0.5 * (f_vals[i] + f_vals[i-1]) * du
        w_cum += dw
        w_vals.append(w_cum)
    return w_vals


def deduplicate_element_sdv_sum(element_sdv_pairs):
    """
    Aggregates element SDV values using strict unique elementLabel deduplication.
    element_sdv_pairs: list of tuples (element_id, sdv17_val, sdv18_val)
    Returns: (e_frac_sum, e_elas_sum, unique_element_count)
    """
    seen = set()
    e_frac_sum = 0.0
    e_elas_sum = 0.0
    for eid, sdv17, sdv18 in element_sdv_pairs:
        if eid not in seen:
            seen.add(eid)
            e_frac_sum += float(sdv17)
            e_elas_sum += float(sdv18)
    return e_frac_sum, e_elas_sum, len(seen)


def evaluate_mechanical_response(u_vals, rf_vals, k0_fit_max_u=0.0010, nominal_delta_u=2.5e-6):
    """
    Evaluates mechanical response from displacement and raw RF2 histories.
    Applies exact force sign convention: F = -RF2 (rejects bare |RF2|).
    Computes K0 using the canonical half-bin window rule on (0.5*delta_u, k0_fit_max_u + 0.5*delta_u],
    F_max, u_peak, and work.
    """
    if len(u_vals) != len(rf_vals):
        raise ValueError("Displacement and RF arrays must have identical length.")
    
    # Exact force convention F = -RF2 (rejection of bare |RF2|)
    f_vals = [-rf for rf in rf_vals]
    
    # Determine increment spacing delta_u for half-bin tolerance
    if len(u_vals) > 1 and u_vals[1] > u_vals[0]:
        delta_u = u_vals[1] - u_vals[0]
    else:
        delta_u = nominal_delta_u
    tol = 0.5 * delta_u
    
    # Canonical half-bin selection window for K0 linear regression
    elastic_pairs = [(u, f) for u, f in zip(u_vals, f_vals) if (u > tol and u <= k0_fit_max_u + tol)]
    if not elastic_pairs:
        elastic_pairs = list(zip(u_vals[:5], f_vals[:5]))
    
    el_u = [p[0] for p in elastic_pairs]
    el_f = [p[1] for p in elastic_pairs]
    k0, intercept, r2 = linear_regression(el_u, el_f)
    
    f_max = max(f_vals) if f_vals else 0.0
    peak_idx = f_vals.index(f_max) if f_vals else 0
    u_peak = u_vals[peak_idx] if f_vals else 0.0
    
    w_ext = compute_trapezoidal_work(u_vals, f_vals)
    
    # Parity deltas vs canonical reference
    delta_k0_pct = ((k0 - CANONICAL_REFERENCE["K0_kN_per_mm"]) / CANONICAL_REFERENCE["K0_kN_per_mm"]) * 100.0
    delta_f_max_pct = ((f_max - CANONICAL_REFERENCE["F_max_kN"]) / CANONICAL_REFERENCE["F_max_kN"]) * 100.0
    delta_u_peak_pct = ((u_peak - CANONICAL_REFERENCE["u_at_F_max_mm"]) / CANONICAL_REFERENCE["u_at_F_max_mm"]) * 100.0
    
    return {
        "F_vals_kN": f_vals,
        "W_ext_kNmm": w_ext,
        "W_ext_mJ": [w * 1000.0 for w in w_ext],
        "K0_kN_per_mm": k0,
        "K0_intercept_kN": intercept,
        "K0_R2": r2,
        "K0_fit_points": len(elastic_pairs),
        "K0_fit_max_u_mm": k0_fit_max_u,
        "delta_K0_pct": delta_k0_pct,
        "F_max_kN": f_max,
        "u_at_F_max_mm": u_peak,
        "delta_F_max_pct": delta_f_max_pct,
        "delta_u_peak_pct": delta_u_peak_pct,
        "u_final_mm": u_vals[-1] if u_vals else 0.0,
        "F_final_kN": f_vals[-1] if f_vals else 0.0,
        "W_ext_final_kNmm": w_ext[-1] if w_ext else 0.0,
        "W_ext_final_mJ": (w_ext[-1] * 1000.0) if w_ext else 0.0
    }


def compute_energy_bookkeeping(e_elas_vals, e_frac_vals, w_ext_vals):
    """
    Computes global energy totals and descriptive bookkeeping metrics.
    Treats Delta_book as a diagnostic indicator, NOT an automatic pass/fail threshold.
    """
    records = []
    for i in range(len(w_ext_vals)):
        e_el = e_elas_vals[i] if i < len(e_elas_vals) else 0.0
        e_fr = e_frac_vals[i] if i < len(e_frac_vals) else 0.0
        w_ex = w_ext_vals[i]
        e_mod = e_el + e_fr
        d_book = e_mod - w_ex
        denom = max(abs(w_ex), abs(e_mod), 1e-12)
        eps_book_abs_pct = (abs(d_book) / denom) * 100.0
        signed_reldiff_pct = (d_book / max(abs(w_ex), 1e-12)) * 100.0
        records.append({
            "frame_index": i,
            "e_elas_kNmm": e_el,
            "e_elas_mJ": e_el * 1000.0,
            "e_frac_kNmm": e_fr,
            "e_frac_mJ": e_fr * 1000.0,
            "e_model_kNmm": e_mod,
            "e_model_mJ": e_mod * 1000.0,
            "w_ext_kNmm": w_ex,
            "w_ext_mJ": w_ex * 1000.0,
            "delta_book_kNmm": d_book,
            "delta_book_mJ": d_book * 1000.0,
            "signed_reldiff_pct": signed_reldiff_pct,
            "eps_book_abs_pct": eps_book_abs_pct
        })
    return records


def classify_candidate(candidate_id, elements=None, mesh_size_h=None, l0=None, dt=None):
    """
    Returns the formal scientific classification and family grouping for any candidate.
    """
    meta = CANDIDATE_CATALOG.get(candidate_id, {})
    family = meta.get("family", "GENERAL_STUDY")
    
    if family == "SPATIAL_CONVERGENCE":
        h_val = mesh_size_h or meta.get("mesh_size_h_mm", 0.0030)
        desc = "Spatial Discretization Convergence Candidate (h = %.4f mm, l0 = 0.0075 mm)" % h_val
        scientific_interpretation = "Evaluates spatial mesh convergence under fixed regularization length scale l0 = 0.0075 mm."
    elif family == "TEMPORAL_CONVERGENCE":
        desc = "Temporal Discretization Convergence Candidate (dt = %s, h = 0.0030 mm)" % str(dt or meta.get("dt_step1_mm"))
        scientific_interpretation = "Evaluates time-step convergence on the 15k spatial baseline."
    elif family == "LENGTH_SCALE_CHARACTERIZATION":
        l0_val = l0 or meta.get("l0_mm", 0.0075)
        desc = "Phase-Field Regularization Length-Scale Sensitivity Candidate (l0 = %.5f mm)" % l0_val
        scientific_interpretation = "STRICTLY REGULARIZATION / MATERIAL SENSITIVITY. NOT numerical mesh convergence."
    elif family == "ADAPTIVE_REFINEMENT":
        desc = "Efficiency-Calibrated 2% Adaptive Candidate (13,897 elements)"
        scientific_interpretation = "Efficiency-calibrated 2% variant (|13897-13941|/13941 = 0.32%), NOT literal Pandey-Kumar 1% reproduction."
    else:
        desc = "General Mode-I Candidate"
        scientific_interpretation = "Uncategorized Mode-I candidate."
        
    return {
        "candidate_id": candidate_id,
        "family": family,
        "description": desc,
        "scientific_interpretation": scientific_interpretation,
        "meta": meta
    }


def evaluate_candidate_data(candidate_id, job_telemetry, extraction_data):
    """
    Main evaluation entry point for a candidate dataset.
    """
    u_vals = extraction_data["u_vals"]
    rf_vals = extraction_data["rf_vals"]
    e_elas_vals = extraction_data.get("e_elas_vals", [])
    e_frac_vals = extraction_data.get("e_frac_vals", [])
    elements = extraction_data.get("elements", CANDIDATE_CATALOG.get(candidate_id, {}).get("elements", 15192))
    
    mech = evaluate_mechanical_response(u_vals, rf_vals)
    energy_records = compute_energy_bookkeeping(e_elas_vals, e_frac_vals, mech["W_ext_kNmm"])
    cand_class = classify_candidate(candidate_id, elements=elements)
    
    report = {
        "candidate_id": candidate_id,
        "candidate_classification": cand_class,
        "job_telemetry": {
            "job_id": job_telemetry.get("job_id", "UNKNOWN"),
            "job_name": job_telemetry.get("job_name", CANDIDATE_CATALOG.get(candidate_id, {}).get("name", "UNKNOWN")),
            "finite_elements": elements,
            "layered_elements": elements * 3,
            "solver_exit_status": job_telemetry.get("exit_status", 0),
            "walltime_seconds": job_telemetry.get("walltime_sec", None),
            "cpu_time_seconds": job_telemetry.get("cpu_sec", None),
            "memory_peak_mb": job_telemetry.get("mem_mb", None)
        },
        "mechanical_response": {
            "K0_kN_per_mm": mech["K0_kN_per_mm"],
            "K0_intercept_kN": mech["K0_intercept_kN"],
            "K0_R2": mech["K0_R2"],
            "K0_fit_points": mech["K0_fit_points"],
            "delta_K0_vs_S1_ref_pct": mech["delta_K0_pct"],
            "F_max_kN": mech["F_max_kN"],
            "u_at_F_max_mm": mech["u_at_F_max_mm"],
            "delta_F_max_vs_S1_ref_pct": mech["delta_F_max_pct"],
            "delta_u_peak_vs_S1_ref_pct": mech["delta_u_peak_pct"],
            "u_final_mm": mech["u_final_mm"],
            "F_final_kN": mech["F_final_kN"],
            "W_ext_final_mJ": mech["W_ext_final_mJ"]
        },
        "energy_balance": {
            "has_sdv_energies": bool(e_elas_vals and e_frac_vals),
            "final_e_elas_mJ": energy_records[-1]["e_elas_mJ"] if energy_records else None,
            "final_e_frac_mJ": energy_records[-1]["e_frac_mJ"] if energy_records else None,
            "final_e_model_mJ": energy_records[-1]["e_model_mJ"] if energy_records else None,
            "final_w_ext_mJ": energy_records[-1]["w_ext_mJ"] if energy_records else None,
            "final_delta_book_mJ": energy_records[-1]["delta_book_mJ"] if energy_records else None,
            "final_signed_reldiff_pct": energy_records[-1]["signed_reldiff_pct"] if energy_records else None,
            "final_eps_book_abs_pct": energy_records[-1]["eps_book_abs_pct"] if energy_records else None,
            "peak_abs_delta_book_mJ": max(abs(r["delta_book_mJ"]) for r in energy_records) if energy_records else None
        },
        "trajectory_records": energy_records
    }
    return report


def export_energy_balance_csv(energy_records, csv_path):
    """Exports frame-by-frame energy balance trajectory to CSV."""
    if not energy_records:
        return
    fieldnames = [
        "frame_index", "w_ext_kNmm", "w_ext_mJ", "e_elas_kNmm", "e_elas_mJ",
        "e_frac_kNmm", "e_frac_mJ", "e_model_kNmm", "e_model_mJ",
        "delta_book_kNmm", "delta_book_mJ", "signed_reldiff_pct", "eps_book_abs_pct"
    ]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in energy_records:
            writer.writerow({k: r.get(k, "") for k in fieldnames})
    print("[INFO] Exported energy balance CSV: %s" % csv_path)


if __name__ == "__main__":
    print("Mode-I Generic Batch Candidate Terminal Evaluator Module loaded successfully.")

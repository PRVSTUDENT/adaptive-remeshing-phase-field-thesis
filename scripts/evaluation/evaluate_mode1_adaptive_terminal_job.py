# -*- coding: utf-8 -*-
"""
Terminal Scientific Evaluator and Qualification Pipeline for Adaptive Mode-I Job
Target Job: PK_M1_ADAPT_2PCT_13K_ENERGY (Job 1409846.mmaster02)
Discretization: 13,897 Finite Elements (Efficiency-Calibrated 2% Variant)

Key Epistemic & Numerical Standards:
1. Force Sign Convention: F = -RF2_RP (tensile reaction force at loaded top boundary).
2. Reporting Convention: Reference thickness t_ref = 1.0 mm, Length in mm, Force in kN, Energy in kN*mm (= J) and mJ.
3. Initial Stiffness K0: Linear regression on initial elastic increments (0 < u <= 0.0020 mm).
4. SDV Deduplication: Single-value aggregation per unique finite element (prevents 4x Gauss point overcounting).
5. Energy Bookkeeping: E_frac = phase-field crack functional, E_model = E_elas + E_frac,
   Delta_book = E_model - W_ext. Descriptive diagnostic only; no arbitrary threshold rejection.
6. Epistemic Classification: Strictly classified as efficiency-calibrated 2% variant (|13897-13941|/13941 = 0.32%),
   NOT as literal Pandey & Kumar 1% reproduction.
"""

import os
import sys
import math
import json
import csv

# Canonical Reference Anchors (Job 1398090 / 1409577 / 1409734)
CANONICAL_REFERENCE = {
    "elements": 15192,
    "K0_kN_per_mm": 137.945520,
    "K0_intercept_kN": 4.472368e-5,
    "K0_R2": 0.99999960,
    "F_max_kN": 0.757778,
    "u_at_F_max_mm": 0.005857,
    "t_ref_mm": 1.0,
    "published_pandey_kumar_2025": {
        "citation": "Pandey & Kumar (2025), CMES 144(3):3251-3276, DOI: 10.32604/cmes.2025.067858",
        "reported_error_target": "1.0%",
        "reported_elements": 13941,
        "reported_F_max_kN": 0.758,
        "reported_u_peak_mm": 0.005860
    }
}

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

def evaluate_mechanical_response(u_vals, rf_vals, k0_fit_max_u=0.0020):
    """
    Evaluates mechanical response from displacement and raw RF2 histories.
    Applies exact force sign convention: F = -RF2.
    Computes K0, F_max, u_peak, and work.
    """
    if len(u_vals) != len(rf_vals):
        raise ValueError("Displacement and RF arrays must have identical length.")
    
    # Exact force convention F = -RF2 (rejection of bare |RF2|)
    f_vals = [-rf for rf in rf_vals]
    
    # Linear elastic range for K0
    elastic_pairs = [(u, f) for u, f in zip(u_vals, f_vals) if 0.0 < u <= k0_fit_max_u]
    if not elastic_pairs:
        # Fallback if first increment > 0.002
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

def classify_adaptive_discretization(elements, error_target=0.02, has_top_u1_constraint=False):
    """
    Strictly classifies adaptive discretization according to project epistemic standards.
    Prevents false claims of literature-literal reproduction or geometric identity.
    """
    delta_published_pct = (abs(elements - CANONICAL_REFERENCE["published_pandey_kumar_2025"]["reported_elements"]) / 
                           float(CANONICAL_REFERENCE["published_pandey_kumar_2025"]["reported_elements"])) * 100.0
    
    if has_top_u1_constraint:
        classification = "HISTORICAL_OVERREFINED_LATERAL_CONSTRAINT"
        is_literal_reproduction = False
    elif abs(error_target - 0.01) < 1e-4:
        classification = "LITERATURE_LITERAL_PARAMETER_OVERREFINED"
        is_literal_reproduction = True  # Parameter is literal, but mesh count differs
    elif abs(error_target - 0.02) < 1e-4:
        classification = "EFFICIENCY_CALIBRATED_PROJECT_VARIANT"
        is_literal_reproduction = False # Crucial epistemic guard
    else:
        classification = "SENSITIVITY_STUDY_VARIANT"
        is_literal_reproduction = False
        
    claim_str = (
        "Evaluated as an efficiency-calibrated 2% adaptive configuration (|{}-13941|/13941 = {:.2f}%), "
        "not as the literal Pandey-Kumar 1% reproduction.".format(elements, delta_published_pct)
    )
    
    return {
        "finite_elements": elements,
        "error_target": error_target,
        "published_comparison": {
            "reported_elements": CANONICAL_REFERENCE["published_pandey_kumar_2025"]["reported_elements"],
            "element_count_delta_pct": delta_published_pct,
            "is_literal_reproduction": is_literal_reproduction,
            "claim_statement": claim_str
        },
        "classification": classification,
        "direction_verdict": "TOWARD_TARGET_LOCALIZATION" if (elements < 20000 and not has_top_u1_constraint) else "AWAY_FROM_TARGET_LOCALIZATION"
    }

def generate_qualification_report_dict(job_telemetry, extraction_data):
    """
    Assembles complete structured qualification evaluation dictionary.
    """
    u_vals = extraction_data["u_vals"]
    rf_vals = extraction_data["rf_vals"]
    e_elas_vals = extraction_data.get("e_elas_vals", [])
    e_frac_vals = extraction_data.get("e_frac_vals", [])
    elements = extraction_data.get("elements", 13897)
    
    mech = evaluate_mechanical_response(u_vals, rf_vals)
    energy_records = compute_energy_bookkeeping(e_elas_vals, e_frac_vals, mech["W_ext_kNmm"])
    disp_class = classify_adaptive_discretization(elements, error_target=0.02, has_top_u1_constraint=False)
    
    report = {
        "job_identity": {
            "job_id": job_telemetry.get("job_id", "1409846.mmaster02"),
            "job_name": job_telemetry.get("job_name", "PK_M1_ADAPT_2PCT_13K_ENERGY"),
            "model_path": "models/pandey_kumar_mode1/24_adaptive_candidate_2pct_13k",
            "finite_elements": elements,
            "layered_elements": elements * 3,
            "solver_exit_status": job_telemetry.get("exit_status", 0),
            "walltime_seconds": job_telemetry.get("walltime_sec", None),
            "cpu_time_seconds": job_telemetry.get("cpu_sec", None),
            "memory_peak_mb": job_telemetry.get("mem_mb", None)
        },
        "epistemic_classification": disp_class,
        "mechanical_parity": {
            "K0_kN_per_mm": mech["K0_kN_per_mm"],
            "K0_reference_kN_per_mm": CANONICAL_REFERENCE["K0_kN_per_mm"],
            "delta_K0_pct": mech["delta_K0_pct"],
            "F_max_kN": mech["F_max_kN"],
            "F_max_reference_kN": CANONICAL_REFERENCE["F_max_kN"],
            "delta_F_max_pct": mech["delta_F_max_pct"],
            "u_at_F_max_mm": mech["u_at_F_max_mm"],
            "u_at_F_max_reference_mm": CANONICAL_REFERENCE["u_at_F_max_mm"],
            "delta_u_peak_pct": mech["delta_u_peak_pct"],
            "u_final_mm": mech["u_final_mm"],
            "F_final_kN": mech["F_final_kN"],
            "W_ext_final_mJ": mech["W_ext_final_mJ"]
        },
        "energy_balance_summary": {
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
        "computational_efficiency": {
            "element_reduction_vs_ref_pct": ((CANONICAL_REFERENCE["elements"] - elements) / float(CANONICAL_REFERENCE["elements"])) * 100.0,
            "element_reduction_vs_literal_1pct_mesh_pct": ((56302 - elements) / 56302.0) * 100.0,
            "walltime_reduction_vs_ref_pct": None
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
    print("Mode-I Adaptive Terminal Qualification Module loaded successfully.")

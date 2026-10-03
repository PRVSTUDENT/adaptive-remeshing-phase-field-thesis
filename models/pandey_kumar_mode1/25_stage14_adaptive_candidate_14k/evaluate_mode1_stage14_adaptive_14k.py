#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
evaluate_mode1_stage14_adaptive_14k.py
--------------------------------------
Authoritative Terminal Scientific Evaluator and Qualification Pipeline for Stage-14 Adaptive Candidate Solve:
Job: PK_MODE1_STAGE14_ADAPT_14K_FRACTURE
Discretization: 14,483 Underlying Finite Elements (43,449 3-Layer Finite Elements, 14,456 Nodes)
Stage: Stage 14B Phase-Field-Coupled Pre-Analysis Adaptive Localization Candidate

Evaluates:
1. Reaction Force & Prescribed Displacement (F-u):
   - F = -RF2_RP (tensile reaction force at RP 999999, upward displacement U2 > 0).
   - Monotonicity, maximum force F_max, peak displacement u_peak.
2. Initial Global Structural Stiffness K0:
   - Linear regression on initial elastic increments using canonical half-bin window rule:
     (u > 0.5 * delta_u) & (u <= 0.0010 + 0.5 * delta_u) across N=400 increments.
   - Evaluated against Fixed Reference Anchor (Job 1398090 / Job 1409734): K0 = 137.945520 kN/mm.
3. Energy Evolution & Bookkeeping:
   - External work W_ext = \\int F du (trapezoidal integration).
   - Elastic strain energy E_elas (SDV18), Phase-field crack energy E_frac (SDV17).
   - Bookkeeping delta: Delta_book = (E_elas + E_frac) - W_ext.
4. Strict Integration-Point Deduplication & Verification:
   - Groups by (instanceName, elementLabel) and verifies within-element IP equality.
   - Scopes to authoritative companion element set (UMATELEM).
   - Rejects inconsistent IP records with loud ValueError.
5. Comparative Parity vs Reconciled Canonical Reference (Job 1409734):
   - Delta K0 (%), Delta F_max (%), Delta u_peak (%), Delta W_ext (%), Delta E_frac (%).
   - Discrete RMS difference and continuous L2 norm on common displacement overlap.
   - Descriptive classification (STABLE, MESH_SENSITIVE, TEMPORALLY_SENSITIVE, NOT_YET_QUALIFIED).
"""

import os
import sys
import math
import json
import csv
import hashlib
import argparse

CANONICAL_REFERENCE = {
    "job_id": "1409734.mmaster02",
    "name": "PK_MODE1_REF15K_ENERGY",
    "underlying_elements": 15192,
    "nodes": 15521,
    "K0_kN_per_mm": 137.945520,
    "K0_intercept_kN": 4.472368e-05,
    "K0_R2": 0.99999960,
    "K0_fit_points_canonical": 400,
    "K0_fit_max_u_mm": 0.0010,
    "F_max_kN": 0.757778,
    "u_at_F_max_mm": 0.005857,
    "F_final_kN": 0.000232,
    "u_final_mm": 0.010000,
    "W_ext_final_mJ": 2.359329,
    "E_frac_final_mJ": 2.340220,
    "E_elas_final_mJ": 0.001161,
    "E_model_final_mJ": 2.341381,
    "Delta_book_final_mJ": -0.017949,
    "eps_book_final_pct": 0.7607,
    "t_ref_mm": 1.0,
    "provenance": {
        "mechanical_reference_job": "1398090.mmaster02",
        "energy_qualified_reference_job": "1409734.mmaster02",
        "reference_deck_sha256": "ec560a4c265730647b43dab125d166ebc57cac285d574d38222a498a967535d9",
        "reference_fortran_sha256": "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6",
        "energy_csv_path": "models/pandey_kumar_mode1/16_energy_qualification_reference_15k/uel_energy_balance.csv",
        "energy_csv_sha256": "9991f7f1ec5645b7e422fc12e1b2e367dd840c3b24a49b22dcf782c0d13f3875",
        "qualification_report_path": "models/pandey_kumar_mode1/16_energy_qualification_reference_15k/S1_1409734_SCIENTIFIC_QUALIFICATION_REPORT.json",
        "qualification_report_sha256": "1aa535f8efa94598ebf79465459dfdc59ee81c6711fb0128abab69d30237af21",
        "governed_status": "CORRECTED_S1_ENERGY_QUALIFIED"
    },
    "published_pandey_kumar_2025": {
        "citation": "Pandey & Kumar (2025), CMES 144(3):3251-3276, DOI: 10.32604/cmes.2025.067858",
        "reported_error_target": "1.0%",
        "reported_elements": 13941,
        "reported_F_max_kN": 0.758,
        "reported_u_peak_mm": 0.005860
    }
}

STAGE14_CANDIDATE_METADATA = {
    "candidate_name": "PK_M1_STAGE14_REFERENCE_FIDELITY_ADAPTIVE_CANDIDATE",
    "package_dir": "models/pandey_kumar_mode1/25_stage14_adaptive_candidate_14k",
    "deck_name": "PK_MODE1_STAGE14_ADAPT_14K_FRACTURE.inp",
    "underlying_elements": 14483,
    "underlying_nodes": 14456,
    "layered_elements": 43449,
    "quad_elements": 14082,
    "tri_elements": 401,
    "layer_partitioning": {
        "layer_1_phase_uel": {
            "element_range": [1, 14483],
            "dofs": [3],
            "quad_type": "U1 (elements 1..14082)",
            "tri_type": "U3 (elements 14083..14483)"
        },
        "layer_2_mech_uel": {
            "element_range": [14484, 28966],
            "dofs": [1, 2],
            "quad_type": "U2 (elements 14484..28565)",
            "tri_type": "U4 (elements 28566..28966)"
        },
        "layer_3_companion_umat": {
            "element_range": [28967, 43449],
            "elset": "UMATELEM",
            "quad_type": "CPE4 (elements 28967..43048)",
            "tri_type": "CPE3 (elements 43049..43449)"
        }
    },
    "preanalysis_source_stage": "Step-2 phase-field localization (earliest target Frame 880, u=0.00940 mm, d_max=0.9833)",
    "refinement_rule": "UNIFORM_ERROR, errorTarget = 1.0%, refinementFactor = 10, region = ALL_ELEM",
    "corridor_fraction_pct": 64.12,
    "coarse_area_preserved_pct": 59.39
}

def compute_sha256(filepath):
    if not filepath or not os.path.exists(filepath):
        return None
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().lower()

def linear_regression(x_vals, y_vals):
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
    return float(slope), float(intercept), float(r2)

def compute_trapezoidal_work(u_vals, f_vals):
    if not u_vals or not f_vals or len(u_vals) != len(f_vals):
        return []
    w_cum = 0.0
    w_vals = [0.0]
    for i in range(1, len(u_vals)):
        du = u_vals[i] - u_vals[i-1]
        if du < -1e-12:
            raise ValueError("Non-monotonic displacement sequence: du = %e at index %d" % (du, i))
        dw = 0.5 * (f_vals[i] + f_vals[i-1]) * du
        w_cum += dw
        w_vals.append(w_cum)
    return w_vals

def extract_element_energies_strict(sdv17_field, sdv18_field, region_set=None, atol=1e-12, rtol=1e-7):
    """
    Extracts element energies with strict integration-point deduplication, equality verification,
    and explicit region selection.
    
    Rules:
    1. If region_set is provided, extracts field subset scoped to that region.
    2. Explicitly groups FieldValue objects by (instanceName, elementLabel).
    3. For each element, collects all integration-point values for SDV17 (E_frac) and SDV18 (E_elas).
    4. Validates that all companion-IP copies of the whole-element energy are numerically identical
       within tolerance max(atol, rtol * abs(val0)).
       Fails loudly with ValueError if within-element copies disagree unexpectedly.
    5. Handles quadrilateral (e.g. 4 IPs) and triangular (e.g. 1 IP) output records separately.
    6. Sums exactly one representative value per unique element.
    
    Returns:
        dict containing:
        - total_e_frac (float): sum of element fracture functional values
        - total_e_elas (float): sum of element elastic energy values
        - total_e_model (float): total_e_frac + total_e_elas
        - unique_element_count (int): number of unique finite elements processed
        - quad_count (int): count of elements with >1 IP records (quadrilaterals)
        - tri_count (int): count of elements with 1 IP record (triangles)
        - per_element_records (dict): mapping from (instance, label) -> (e_frac, e_elas, ip_count)
    """
    v17_list = sdv17_field.getSubset(region=region_set).values if region_set else sdv17_field.values
    v18_list = sdv18_field.getSubset(region=region_set).values if region_set else sdv18_field.values
    
    if len(v17_list) != len(v18_list):
        raise ValueError("SDV17 and SDV18 value record count mismatch: %d vs %d" % (len(v17_list), len(v18_list)))
        
    elem_records_17 = {}
    elem_records_18 = {}
    
    for val17, val18 in zip(v17_list, v18_list):
        inst_name = val17.instance.name if (hasattr(val17, 'instance') and val17.instance) else ""
        eid = val17.elementLabel
        key = (inst_name, eid)
        
        # Verify alignment of record keys
        inst18 = val18.instance.name if (hasattr(val18, 'instance') and val18.instance) else ""
        if (inst18, val18.elementLabel) != key:
            raise ValueError("Mismatched element record between SDV17 %s and SDV18 %s" % (
                str(key), str((inst18, val18.elementLabel))
            ))
            
        d17 = float(val17.data)
        d18 = float(val18.data)
        
        if key not in elem_records_17:
            elem_records_17[key] = []
            elem_records_18[key] = []
        elem_records_17[key].append(d17)
        elem_records_18[key].append(d18)
        
    total_e_frac = 0.0
    total_e_elas = 0.0
    quad_count = 0
    tri_count = 0
    per_element_data = {}
    
    for key, vals17 in elem_records_17.items():
        vals18 = elem_records_18[key]
        ip_count = len(vals17)
        
        # Check IP count
        if ip_count > 1:
            quad_count += 1
        else:
            tri_count += 1
            
        # Verify within-element equality for SDV17
        v17_0 = vals17[0]
        tol17 = max(atol, rtol * abs(v17_0))
        for idx, v in enumerate(vals17[1:], start=2):
            if abs(v - v17_0) > tol17:
                raise ValueError(
                    "Inconsistent SDV17 (E_frac) energy across integration points for element %s: "
                    "IP 1 = %.12e vs IP %d = %.12e (diff = %.12e > tol = %.12e)" % (
                        str(key), v17_0, idx, v, abs(v - v17_0), tol17
                    )
                )
                
        # Verify within-element equality for SDV18
        v18_0 = vals18[0]
        tol18 = max(atol, rtol * abs(v18_0))
        for idx, v in enumerate(vals18[1:], start=2):
            if abs(v - v18_0) > tol18:
                raise ValueError(
                    "Inconsistent SDV18 (E_elas) energy across integration points for element %s: "
                    "IP 1 = %.12e vs IP %d = %.12e (diff = %.12e > tol = %.12e)" % (
                        str(key), v18_0, idx, v, abs(v - v18_0), tol18
                    )
                )
                
        total_e_frac += v17_0
        total_e_elas += v18_0
        per_element_data[key] = {
            "e_frac": v17_0,
            "e_elas": v18_0,
            "ip_count": ip_count
        }
        
    return {
        "total_e_frac": float(total_e_frac),
        "total_e_elas": float(total_e_elas),
        "total_e_model": float(total_e_frac + total_e_elas),
        "unique_element_count": len(elem_records_17),
        "quad_count": quad_count,
        "tri_count": tri_count,
        "per_element_data": per_element_data
    }

def parse_sta_file(sta_path):
    if not sta_path or not os.path.exists(sta_path):
        return None
    increments = []
    total_iters = 0
    total_cutbacks = 0
    min_dt = float('inf')
    with open(sta_path, 'r') as f:
        for line in f:
            l = line.strip()
            if not l or l.startswith('SUMMARY') or l.startswith('STEP') or l.startswith('INCREMENT') or l.startswith('Abaqus'):
                continue
            parts = l.split()
            if len(parts) >= 8 and parts[0].isdigit() and parts[1].isdigit():
                try:
                    step = int(parts[0])
                    inc = int(parts[1])
                    att_str = parts[2]
                    n_att = int(''.join(c for c in att_str if c.isdigit())) if any(c.isdigit() for c in att_str) else 1
                    n_sev = int(parts[3])
                    n_eq = int(parts[4])
                    total_iters += n_eq
                    if 'U' in att_str or n_att > 1:
                        total_cutbacks += 1
                    step_time = float(parts[6])
                    total_time = float(parts[7])
                    dt = float(parts[8]) if len(parts) > 8 else 0.0
                    if dt > 0.0 and dt < min_dt:
                        min_dt = dt
                    increments.append({
                        'step': step, 'inc': inc, 'att': n_att, 'sev': n_sev, 'eq': n_eq,
                        'step_time': step_time, 'total_time': total_time, 'dt': dt
                    })
                except (ValueError, IndexError):
                    continue
    return {
        'total_increments': len(increments),
        'total_iterations': total_iters,
        'total_cutbacks': total_cutbacks,
        'min_dt': min_dt if min_dt != float('inf') else 0.0,
        'last_step': increments[-1]['step'] if increments else 0,
        'last_inc': increments[-1]['inc'] if increments else 0,
        'last_step_time': increments[-1]['step_time'] if increments else 0.0,
        'last_total_time': increments[-1]['total_time'] if increments else 0.0
    }

def _is_float(val_str):
    try:
        float(val_str)
        return True
    except ValueError:
        return False

def read_fu_csv(csv_path):
    u_vals = []
    f_vals = []
    if not csv_path or not os.path.exists(csv_path):
        return u_vals, f_vals
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = None
        u_col = 0
        f_col = 1
        for row in reader:
            if not row or not any(cell.strip() for cell in row):
                continue
            if header is None:
                try:
                    float(row[0].strip())
                except ValueError:
                    header = [c.strip().lower() for c in row]
                    if 'displacement_mm' in header and 'reaction_force_kn' in header:
                        u_col = header.index('displacement_mm')
                        f_col = header.index('reaction_force_kn')
                    elif 'u2_mm' in header and 'rf2_kn' in header:
                        u_col = header.index('u2_mm')
                        f_col = header.index('rf2_kn')
                    elif 'u_mm' in header and 'f_kn' in header:
                        u_col = header.index('u_mm')
                        f_col = header.index('f_kn')
                    continue
            try:
                u = float(row[u_col].strip())
                f_val = float(row[f_col].strip())
                # If force is negative RF2, convert to tensile positive F = -RF2
                if f_val < -1e-6 and u > 1e-6:
                    f_val = -f_val
                u_vals.append(u)
                f_vals.append(f_val)
            except (ValueError, IndexError):
                continue
    return u_vals, f_vals

def evaluate_mechanical_metrics(u_vals, f_vals, k0_fit_max_u=0.0010, nominal_delta_u=2.5e-6):
    if not u_vals or not f_vals or len(u_vals) != len(f_vals):
        return {}
    if len(u_vals) > 1 and u_vals[1] > u_vals[0]:
        delta_u = u_vals[1] - u_vals[0]
    else:
        delta_u = nominal_delta_u
    tol = 0.5 * delta_u
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
    delta_k0_pct = ((k0 - CANONICAL_REFERENCE["K0_kN_per_mm"]) / CANONICAL_REFERENCE["K0_kN_per_mm"]) * 100.0
    delta_f_max_pct = ((f_max - CANONICAL_REFERENCE["F_max_kN"]) / CANONICAL_REFERENCE["F_max_kN"]) * 100.0
    delta_u_peak_pct = ((u_peak - CANONICAL_REFERENCE["u_at_F_max_mm"]) / CANONICAL_REFERENCE["u_at_F_max_mm"]) * 100.0
    return {
        "K0_kN_per_mm": k0,
        "K0_intercept_kN": intercept,
        "K0_R2": r2,
        "K0_sample_count": len(elastic_pairs),
        "K0_fit_max_u_mm": k0_fit_max_u,
        "delta_K0_pct": delta_k0_pct,
        "F_max_kN": f_max,
        "u_at_F_max_mm": u_peak,
        "delta_F_max_pct": delta_f_max_pct,
        "delta_u_peak_pct": delta_u_peak_pct,
        "u_final_mm": u_vals[-1] if u_vals else 0.0,
        "F_final_kN": f_vals[-1] if f_vals else 0.0,
        "W_ext_final_mJ": (w_ext[-1] * 1000.0) if w_ext else 0.0,
        "total_data_points": len(u_vals)
    }

def compare_against_reference(u_cand, f_cand, u_ref, f_ref):
    if not u_cand or not u_ref:
        return {}
    u_common_max = min(u_cand[-1], u_ref[-1])
    u_c = [u for u in u_cand if u <= u_common_max]
    f_c = [f for u, f in zip(u_cand, f_cand) if u <= u_common_max]
    f_r_interp = []
    for u in u_c:
        if u <= u_ref[0]:
            f_r_interp.append(f_ref[0])
        elif u >= u_ref[-1]:
            f_r_interp.append(f_ref[-1])
        else:
            low = 0
            high = len(u_ref) - 1
            while high - low > 1:
                mid = (low + high) // 2
                if u_ref[mid] <= u:
                    low = mid
                else:
                    high = mid
            dx = u_ref[high] - u_ref[low]
            t = (u - u_ref[low]) / dx if dx > 0 else 0.0
            f_r_interp.append(f_ref[low] + t * (f_ref[high] - f_ref[low]))
    diffs = [fc - fr for fc, fr in zip(f_c, f_r_interp)]
    abs_diffs = [abs(d) for d in diffs]
    sq_diffs = [d ** 2 for d in diffs]
    max_abs_diff_kN = max(abs_diffs) if abs_diffs else 0.0
    discrete_rms_kN = math.sqrt(sum(sq_diffs) / len(sq_diffs)) if sq_diffs else 0.0
    l2_integral = 0.0
    for i in range(len(u_c) - 1):
        du = u_c[i+1] - u_c[i]
        avg_sq = 0.5 * (sq_diffs[i+1] + sq_diffs[i])
        l2_integral += avg_sq * du
    continuous_l2_kN = math.sqrt(l2_integral / u_common_max) if u_common_max > 0 else 0.0
    return {
        "common_u_max_mm": float(u_common_max),
        "points_evaluated": len(u_c),
        "max_abs_diff_kN": float(max_abs_diff_kN),
        "discrete_rms_kN": float(discrete_rms_kN),
        "discrete_rms_N": float(discrete_rms_kN * 1000.0),
        "continuous_l2_kN": float(continuous_l2_kN),
        "continuous_l2_N": float(continuous_l2_kN * 1000.0)
    }

def run_evaluation(job_dir, ref_csv_path=None, out_json_path=None):
    print("================================================================================")
    print("STAGE 14 ADAPTIVE SOLVE (14,483 UNDERLYING ELEMENTS) TERMINAL EVALUATION")
    print("================================================================================")
    print("Job Directory: %s" % job_dir)
    
    csv_candidates = [
        os.path.join(job_dir, "PK_MODE1_STAGE14_ADAPT_14K_FRACTURE_fu.csv"),
        os.path.join(job_dir, "curve_extracted.csv"),
        os.path.join(job_dir, "fu.csv")
    ]
    u_vals, f_vals = [], []
    for c in csv_candidates:
        if os.path.exists(c):
            print("Found F-u CSV: %s" % c)
            u_vals, f_vals = read_fu_csv(c)
            break
            
    sta_candidates = [
        os.path.join(job_dir, "PK_MODE1_STAGE14_ADAPT_14K_FRACTURE.sta"),
        os.path.join(job_dir, "Job.sta")
    ]
    sta_metrics = None
    for s in sta_candidates:
        if os.path.exists(s):
            print("Found .sta file: %s" % s)
            sta_metrics = parse_sta_file(s)
            break
            
    mech_metrics = evaluate_mechanical_metrics(u_vals, f_vals)
    print("\n--- MECHANICAL PARITY METRICS ---")
    if mech_metrics:
        print("  Data points: %d (u_final = %.6f mm, F_final = %.6f kN)" % (
            mech_metrics["total_data_points"], mech_metrics["u_final_mm"], mech_metrics["F_final_kN"]
        ))
        print("  K0: %.6f kN/mm (Delta vs Ref = %+.4f%%, R^2 = %.8f, N = %d)" % (
            mech_metrics["K0_kN_per_mm"], mech_metrics["delta_K0_pct"],
            mech_metrics["K0_R2"], mech_metrics["K0_sample_count"]
        ))
        print("  F_max: %.6f kN (Delta vs Ref = %+.4f%%)" % (
            mech_metrics["F_max_kN"], mech_metrics["delta_f_max_pct"]
        ))
        print("  u_peak: %.6f mm (Delta vs Ref = %+.4f%%)" % (
            mech_metrics["u_at_F_max_mm"], mech_metrics["delta_u_peak_pct"]
        ))
        print("  External Work W_ext: %.6f mJ" % mech_metrics["W_ext_final_mJ"])
    else:
        print("  [WAITING] No completed F-u trajectory yet (simulation running or pending extraction).")
        
    comp_ref = {}
    if ref_csv_path and os.path.exists(ref_csv_path) and u_vals:
        print("\n--- COMPARISON AGAINST REFERENCE 1409734 / 1398090 ---")
        u_ref, f_ref = read_fu_csv(ref_csv_path)
        comp_ref = compare_against_reference(u_vals, f_vals, u_ref, f_ref)
        print("  Overlap u_max: %.6f mm (%d points)" % (comp_ref["common_u_max_mm"], comp_ref["points_evaluated"]))
        print("  Discrete RMS: %.4f N, Continuous L2: %.4f N" % (comp_ref["discrete_rms_N"], comp_ref["continuous_l2_N"]))
        
    eval_record = {
        "stage": "Stage 14B Phase-Field Adaptive Candidate Solve",
        "model_metadata": STAGE14_CANDIDATE_METADATA,
        "canonical_reference": CANONICAL_REFERENCE,
        "solver_sta_telemetry": sta_metrics,
        "mechanical_metrics": mech_metrics,
        "comparison_vs_reference": comp_ref
    }
    
    if out_json_path:
        with open(out_json_path, 'w', encoding='utf-8') as f:
            json.dump(eval_record, f, indent=2)
        print("\nWrote evaluation report to: %s" % out_json_path)
    print("================================================================================")
    return eval_record

def main():
    parser = argparse.ArgumentParser(description="Evaluate Stage 14 Adaptive Mode-I Fracture Solve")
    parser.add_argument("--dir", type=str, default="models/pandey_kumar_mode1/25_stage14_adaptive_candidate_14k", help="Job directory")
    parser.add_argument("--ref_csv", type=str, default="results/pandey_kumar_mode1/master_fracture_curves/curve_standard_1398090.csv", help="Reference CSV path")
    parser.add_argument("--out_json", type=str, default=None, help="Output JSON path")
    args = parser.parse_args()
    run_evaluation(args.dir, args.ref_csv, args.out_json)

if __name__ == '__main__':
    main()

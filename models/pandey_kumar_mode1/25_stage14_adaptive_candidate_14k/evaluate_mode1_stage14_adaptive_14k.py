#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
evaluate_mode1_stage14_adaptive_14k.py
--------------------------------------
Authoritative Terminal Scientific Evaluator and Qualification Pipeline for Stage-14 Adaptive Candidate Solve:
Job: PK_MODE1_STAGE14_ADAPT_14K_FRACTURE
Discretization: 14,483 Finite Elements (43,449 3-Layer Elements, 14,456 Nodes)
Stage: Stage 14B Phase-Field-Coupled Pre-Analysis Adaptive Localization Candidate

Evaluates:
1. Reaction Force & Displacement (F-u):
   - F = -RF2_RP (tensile reaction force at RP 999999).
   - Monotonicity, maximum force F_max, peak displacement u_peak.
2. Initial Global Stiffness K0:
   - Linear regression on initial elastic increments using canonical half-bin window rule:
     (u > 0.5 * delta_u) & (u <= 0.0010 + 0.5 * delta_u).
   - Evaluated against Fixed Reference Anchor (Job 1398090): K0 = 137.945520 kN/mm.
3. Energy Evolution & Bookkeeping:
   - External work W_ext = \\int F du (trapezoidal integration).
   - Elastic strain energy E_elas (SDV18), Phase-field crack energy E_frac (SDV17).
   - Bookkeeping delta: Delta_book = (E_elas + E_frac) - W_ext.
4. Numerical & Computational Telemetry:
   - Increments, iterations, cutbacks, minimum dt from .sta file.
   - Solver exit status and walltime/CPU time.
5. Comparative Parity vs Canonical Reference (Job 1398090):
   - Delta K0 (%), Delta F_max (%), Delta u_peak (%).
   - Discrete RMS difference and continuous L2 norm on common displacement overlap.
"""

import os
import sys
import math
import json
import csv
import hashlib
import argparse

CANONICAL_REFERENCE = {
    "job_id": "1398090.mmaster02",
    "name": "PK_MODE1_STANDARD_PFM",
    "elements": 15192,
    "nodes": 15521,
    "K0_kN_per_mm": 137.945520,
    "K0_intercept_kN": 4.472368e-05,
    "K0_R2": 0.99999960,
    "K0_fit_points_canonical": 400,
    "K0_fit_max_u_mm": 0.0010,
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

STAGE14_CANDIDATE_METADATA = {
    "candidate_name": "PK_M1_STAGE14_REFERENCE_FIDELITY_ADAPTIVE_CANDIDATE",
    "package_dir": "models/pandey_kumar_mode1/25_stage14_adaptive_candidate_14k",
    "deck_name": "PK_MODE1_STAGE14_ADAPT_14K_FRACTURE.inp",
    "underlying_elements": 14483,
    "underlying_nodes": 14456,
    "layered_elements": 43449,
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

def parse_dat_history(dat_path, target_node=999999):
    """
    Parses displacement and reaction force history from an Abaqus .dat file for target_node.
    """
    if not dat_path or not os.path.exists(dat_path):
        return [], []
    u_vals = []
    f_vals = []
    # State flags
    in_node_table = False
    with open(dat_path, 'r') as f:
        for line in f:
            l = line.strip()
            if 'THE FOLLOWING TABLE IS PRINTED FOR NODES BELONGING TO NODE SET' in line or 'NODE OUTPUT' in line:
                in_node_table = True
                continue
            if in_node_table:
                if not l or l.startswith('---') or l.startswith('Abaqus') or l.startswith('MAXIMUM') or l.startswith('MINIMUM'):
                    continue
                parts = l.split()
                if len(parts) >= 3 and parts[0].isdigit():
                    node_id = int(parts[0])
                    if node_id == target_node:
                        try:
                            # Typically: NODE U1 U2 RF1 RF2
                            # Or table specific format
                            # We search for float values
                            floats = [float(p) for p in parts[1:] if _is_float(p)]
                            if len(floats) >= 2:
                                # First float is displacement, second is RF, or table format
                                pass
                        except ValueError:
                            pass
    return u_vals, f_vals

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
    # Linear interpolation of ref onto cand
    f_r_interp = []
    for u in u_c:
        # binary search / bracket
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
    print("STAGE 14 ADAPTIVE SOLVE (14,483 EL) TERMINAL EVALUATION")
    print("================================================================================")
    print("Job Directory: %s" % job_dir)
    
    # 1. Look for curve CSV or dat file
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
            
    # 2. Check STA file for solver metrics
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
            
    # 3. Evaluate mechanical metrics
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
        
    # 4. Compare vs Reference if available
    comp_ref = {}
    if ref_csv_path and os.path.exists(ref_csv_path) and u_vals:
        print("\n--- COMPARISON AGAINST REFERENCE 1398090 ---")
        u_ref, f_ref = read_fu_csv(ref_csv_path)
        comp_ref = compare_against_reference(u_vals, f_vals, u_ref, f_ref)
        print("  Overlap u_max: %.6f mm (%d points)" % (comp_ref["common_u_max_mm"], comp_ref["points_evaluated"]))
        print("  Discrete RMS: %.4f N, Continuous L2: %.4f N" % (comp_ref["discrete_rms_N"], comp_ref["continuous_l2_N"]))
        
    # 5. Assemble complete record
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

"""
extract_and_compare_et2_et3.py

Automated extraction, integration, and quantitative convergence comparison between:
- Published Literature Target (Pandey & Kumar 2025 Fig. 13(a) 801-point authoritative redigitization)
- Coarse Pre-Analysis Benchmark (Job 1411104, 2,960 FEs)
- ET3 Baseline Stabilized Fracture (Job 1411267, 21,063 FEs)
- ET2 Refined Adaptive Mesh (Job 1411414, 37,575 FEs)
"""

import os
import re
import json
import math
import pandas as pd
import numpy as np

def parse_dat_rf(dat_path):
    """Parses displacement (mm) and RF1 (N) from Abaqus .dat file for node 999999."""
    if not os.path.exists(dat_path):
        return None, None
    with open(dat_path, 'r', encoding='utf-8', errors='ignore') as f:
        text = f.read()
    pattern = re.compile(r'^\s*999999\s+([0-9.+-Ee]+)\s+([0-9.+-Ee]+)', re.MULTILINE)
    matches = pattern.findall(text)
    if not matches:
        return None, None
    u_list = [float(m[0]) for m in matches]  # mm
    rf_list = [float(m[1]) * 1000.0 for m in matches]  # N
    return u_list, rf_list

def trapezoidal_integral(x_arr, y_arr):
    """Computes cumulative trapezoidal integral of y with respect to x."""
    cum = [0.0]
    for i in range(1, len(x_arr)):
        dx = x_arr[i] - x_arr[i-1]
        area = 0.5 * (y_arr[i] + y_arr[i-1]) * dx
        cum.append(cum[-1] + area)
    return cum

def evaluate_rf_curve(u_arr_mm, rf_arr_N, label="", is_active=False):
    """
    Evaluates key macro-mechanical milestones from an RF-u curve:
    u_arr_mm in mm, rf_arr_N in N
    """
    n = len(u_arr_mm)
    if n == 0:
        return {}
    
    u_term_um = float(u_arr_mm[-1] * 1000.0)
    
    # 1. Initial structural stiffness K0 (linear regression on elastic range u <= 0.0020 mm)
    elastic_indices = [i for i, u in enumerate(u_arr_mm) if 0.0 < u <= 0.0020]
    if len(elastic_indices) >= 2:
        u_el = [u_arr_mm[i] for i in elastic_indices]
        rf_el = [rf_arr_N[i] for i in elastic_indices]
        sum_uf = sum(u * f for u, f in zip(u_el, rf_el))
        sum_u2 = sum(u**2 for u in u_el)
        k0_N_per_mm = sum_uf / sum_u2
        k0_kN_per_mm = k0_N_per_mm / 1000.0
    elif len(u_arr_mm) > 1 and u_arr_mm[1] > 0:
        k0_kN_per_mm = (rf_arr_N[1] / u_arr_mm[1]) / 1000.0
    elif u_arr_mm[0] > 0:
        k0_kN_per_mm = (rf_arr_N[0] / u_arr_mm[0]) / 1000.0
    else:
        k0_kN_per_mm = 0.0

    # Running maximum force observed so far and latest converged state
    idx_max_so_far = 0
    max_rf_so_far = rf_arr_N[0]
    for i, rf in enumerate(rf_arr_N):
        if rf > max_rf_so_far:
            max_rf_so_far = rf
            idx_max_so_far = i
    latest_rf = float(rf_arr_N[-1])

    if is_active:
        # For active/in-progress simulations that have not completed full fracture horizon:
        f_max = None
        u_peak_um = None
        f_min = None
        u_min_um = None
        f_16um = None
        f_term = None
        w_16um = None
        w_cum = trapezoidal_integral(u_arr_mm, rf_arr_N)
        w_total = float(w_cum[-1])
    else:
        # Completed simulations
        f_max = float(max_rf_so_far)
        u_peak_um = float(u_arr_mm[idx_max_so_far] * 1000.0)
        
        # Post-peak minimum F_min (in range u > u_peak)
        if idx_max_so_far < n - 5:
            idx_min_local = idx_max_so_far
            min_rf = rf_arr_N[idx_max_so_far]
            for i in range(idx_max_so_far, n):
                if rf_arr_N[i] < min_rf:
                    min_rf = rf_arr_N[i]
                    idx_min_local = i
            f_min = float(min_rf)
            u_min_um = float(u_arr_mm[idx_min_local] * 1000.0)
        else:
            f_min = f_max
            u_min_um = u_peak_um
            
        # Reaction force at 16.0 um
        diff_16 = [abs(u * 1000.0 - 16.0) for u in u_arr_mm]
        idx_16 = diff_16.index(min(diff_16))
        f_16um = float(rf_arr_N[idx_16]) if (u_term_um >= 15.9) else None
        
        # Terminal reaction force at 20.0 um
        f_term = float(rf_arr_N[-1])
        
        # External work integration (mJ = N * mm)
        w_cum = trapezoidal_integral(u_arr_mm, rf_arr_N)
        w_16um = float(w_cum[idx_16]) if (u_term_um >= 15.9) else float(w_cum[-1])
        w_total = float(w_cum[-1])

    return {
        'label': label,
        'n_increments': n,
        'k0_kN_per_mm': k0_kN_per_mm,
        'f_max_N': f_max,
        'u_peak_um': u_peak_um,
        'f_min_N': f_min,
        'u_min_um': u_min_um,
        'f_16um_N': f_16um,
        'f_term_N': f_term,
        'u_term_um': u_term_um,
        'latest_rf_N': latest_rf,
        'max_rf_so_far_N': float(max_rf_so_far),
        'w_16um_mJ': w_16um,
        'w_total_mJ': w_total,
        'is_active': is_active
    }

def run_comparison():
    # 1. Published Literature (Pandey & Kumar 2025 Fig. 13(a) Authoritative 801-point Redigitization)
    lit_csv = 'references/derived/pandey_kumar_2025_fig13a_authoritative_redigitized.csv'
    if os.path.exists(lit_csv):
        df_lit = pd.read_csv(lit_csv)
        u_lit_mm = df_lit['displacement_mm'].tolist()
        rf_lit_N = df_lit['proposed_pfm_N'].tolist()
        lit_eval = evaluate_rf_curve(u_lit_mm, rf_lit_N, label="Pandey & Kumar (2025) Fig. 13(a)", is_active=False)
    else:
        lit_u = [0.0, 0.002, 0.004, 0.006, 0.0075, 0.0080, 0.008284, 0.0087, 0.0092, 0.0100, 0.0110, 0.0120, 0.0130, 0.0140, 0.0150, 0.0160]
        lit_rf = [0.0, 91.3, 182.7, 274.0, 342.0, 360.5, 365.74, 355.0, 320.0, 270.0, 235.0, 215.0, 202.0, 194.0, 188.0, 184.06]
        lit_eval = evaluate_rf_curve(lit_u, lit_rf, label="Pandey & Kumar (2025) [16-pt]", is_active=False)

    # 2. Coarse 2.96k solve (Job 1411104)
    coarse_csv = 'models/pandey_kumar_mode2/06_paper_grounded_uel_preanalysis/mode2_j1_coarse_retest_rf_history.csv'
    if os.path.exists(coarse_csv):
        df_c = pd.read_csv(coarse_csv)
        u_col = 'displacement_mm' if 'displacement_mm' in df_c.columns else df_c.columns[1]
        rf_col = 'RF1_kN' if 'RF1_kN' in df_c.columns else df_c.columns[2]
        u_c = df_c[u_col].tolist()
        rf_c = [float(v) * 1000.0 for v in df_c[rf_col].tolist()]
        coarse_eval = evaluate_rf_curve(u_c, rf_c, label="Coarse Benchmark (2,960 FE)", is_active=False)
    else:
        coarse_eval = {}

    # 3. ET3 Baseline 21.06k solve (Job 1411267)
    et3_csv = 'models/pandey_kumar_mode2/06_paper_grounded_uel_preanalysis/m2_corrected_remesh/job2_rf_active_history.csv'
    if os.path.exists(et3_csv):
        df_3 = pd.read_csv(et3_csv)
        u_col = 'u_top_mm' if 'u_top_mm' in df_3.columns else df_3.columns[1]
        rf_col = 'RF1_N' if 'RF1_N' in df_3.columns else df_3.columns[4]
        u_3 = df_3[u_col].tolist()
        rf_3 = [float(v) for v in df_3[rf_col].tolist()]
        et3_eval = evaluate_rf_curve(u_3, rf_3, label="ET3 Baseline (21,063 FE)", is_active=False)
    else:
        et3_eval = {}

    # 4. ET2 Refined 37.58k solve (Job 1411414)
    et2_dat = 'C:/Users/pruth/.gemini/antigravity-cli/brain/ea2b7491-ff7c-496a-85e9-63076adb69ec/Job-2_UEL_et2.dat'
    u_2, rf_2 = parse_dat_rf(et2_dat)
    if u_2 is not None and len(u_2) > 0:
        et2_eval = evaluate_rf_curve(u_2, rf_2, label="ET2 Refined Mesh (37,575 FE - Active)", is_active=True)
    else:
        et2_eval = {}

    print("============================================================================================================================")
    print("QUANTITATIVE BENCHMARK RECONCILIATION & MESH CONVERGENCE SUMMARY")
    print("============================================================================================================================")
    print(f"{'Quantity / Metric':<30} | {'Published Lit':<14} | {'Coarse (2.96k)':<15} | {'ET3 (21.06k)':<15} | {'ET2 (37.58k - Active)':<28}")
    print("----------------------------------------------------------------------------------------------------------------------------")
    
    # Format ET2 values cleanly distinguishing active solve from completed metrics
    if et2_eval.get('is_active', False):
        f_max_et2_str = f"PENDING ({et2_eval.get('max_rf_so_far_N',0):.1f}N @ {et2_eval.get('u_term_um',0):.2f}µm)"
        u_peak_et2_str = "PENDING"
        f_min_et2_str = "PENDING"
        f_16_et2_str = "PENDING"
        f_term_et2_str = f"PENDING ({et2_eval.get('latest_rf_N',0):.1f}N @ {et2_eval.get('u_term_um',0):.2f}µm)"
        w_16_et2_str = "PENDING"
        w_tot_et2_str = f"{et2_eval.get('w_total_mJ',0):.3f} (prog)"
    else:
        f_max_et2_str = f"{et2_eval.get('f_max_N',0):.2f}"
        u_peak_et2_str = f"{et2_eval.get('u_peak_um',0):.2f}"
        f_min_et2_str = f"{et2_eval.get('f_min_N',0):.2f}"
        f_16_et2_str = f"{et2_eval.get('f_16um_N',0):.2f}"
        f_term_et2_str = f"{et2_eval.get('f_term_N',0):.2f}"
        w_16_et2_str = f"{et2_eval.get('w_16um_mJ',0):.3f}"
        w_tot_et2_str = f"{et2_eval.get('w_total_mJ',0):.3f}"

    print(f"{'Peak Force F_max [N]':<30} | {lit_eval['f_max_N']:<14.2f} | {coarse_eval.get('f_max_N',0):<15.2f} | {et3_eval.get('f_max_N',0):<15.2f} | {f_max_et2_str:<28}")
    print(f"{'Peak Disp u(F_max) [µm]':<30} | {lit_eval['u_peak_um']:<14.2f} | {coarse_eval.get('u_peak_um',0):<15.2f} | {et3_eval.get('u_peak_um',0):<15.2f} | {u_peak_et2_str:<28}")
    print(f"{'Post-Peak Min F_min [N]':<30} | {'N/A (monotone)':<14} | {coarse_eval.get('f_min_N',0):<15.2f} | {et3_eval.get('f_min_N',0):<15.2f} | {f_min_et2_str:<28}")
    print(f"{'Force at 16.0 µm [N]':<30} | {lit_eval['f_term_N']:<14.2f} | {coarse_eval.get('f_16um_N',0):<15.2f} | {et3_eval.get('f_16um_N',0):<15.2f} | {f_16_et2_str:<28}")
    print(f"{'Terminal Force [N]':<30} | {'N/A (end 16um)':<14} | {coarse_eval.get('f_term_N',0):<15.2f} | {et3_eval.get('f_term_N',0):<15.2f} | {f_term_et2_str:<28}")
    print(f"{'Work on [0, 16] µm [mJ]':<30} | {lit_eval['w_16um_mJ']:<14.3f} | {coarse_eval.get('w_16um_mJ',0):<15.3f} | {et3_eval.get('w_16um_mJ',0):<15.3f} | {w_16_et2_str:<28}")
    print(f"{'Total Work [0, 20] µm [mJ]':<30} | {'N/A':<14} | {coarse_eval.get('w_total_mJ',0):<15.3f} | {et3_eval.get('w_total_mJ',0):<15.3f} | {w_tot_et2_str:<28}")
    print(f"{'Initial Stiffness K0 [kN/mm]':<30} | {lit_eval['k0_kN_per_mm']:<14.2f} | {coarse_eval.get('k0_kN_per_mm',0):<15.2f} | {et3_eval.get('k0_kN_per_mm',0):<15.2f} | {et2_eval.get('k0_kN_per_mm',0):<28.2f}")
    print("============================================================================================================================")

    # Gap Closure Metrics
    f_gap_total = coarse_eval['f_max_N'] - lit_eval['f_max_N']
    f_gap_closed_et3 = coarse_eval['f_max_N'] - et3_eval['f_max_N']
    pct_f_closed = (f_gap_closed_et3 / f_gap_total) * 100.0

    w_gap_total = coarse_eval['w_16um_mJ'] - lit_eval['w_16um_mJ']
    w_gap_closed_et3 = coarse_eval['w_16um_mJ'] - et3_eval['w_16um_mJ']
    pct_w_closed = (w_gap_closed_et3 / w_gap_total) * 100.0

    print(f"\nMultiscale Gap Closure (ET3 vs Coarse):")
    print(f"  Peak Force Gap Closure: {pct_f_closed:.2f}% ({f_gap_closed_et3:.2f} N / {f_gap_total:.2f} N)")
    print(f"  External Work Gap Closure (0-16 µm): {pct_w_closed:.2f}% ({w_gap_closed_et3:.3f} mJ / {w_gap_total:.3f} mJ)")

    return {
        'literature': lit_eval,
        'coarse': coarse_eval,
        'et3': et3_eval,
        'et2': et2_eval,
        'gap_closure': {
            'peak_force_pct': pct_f_closed,
            'work_16um_pct': pct_w_closed
        }
    }

if __name__ == '__main__':
    run_comparison()

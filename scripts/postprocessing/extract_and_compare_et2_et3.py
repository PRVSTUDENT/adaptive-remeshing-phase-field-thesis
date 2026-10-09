"""
extract_and_compare_et2_et3.py

Automated extraction, integration, and quantitative convergence comparison between:
- Published Literature Target (Pandey & Kumar 2025 Fig. 13(a))
- Coarse Pre-Analysis Benchmark (Job 1411104, 2,960 FEs)
- ET3 Baseline Stabilized Fracture (Job 1411267, 21,063 FEs)
- ET2 Refined Adaptive Mesh (Job 1411414, 37,575 FEs)
"""

import os
import re
import json
import math

def parse_dat_rf(dat_path):
    """Parses displacement (mm) and RF1 (kN) from Abaqus .dat file for node 999999."""
    if not os.path.exists(dat_path):
        return None, None
    with open(dat_path, 'r', encoding='utf-8', errors='ignore') as f:
        text = f.read()
    pattern = re.compile(r'^\s*999999\s+([0-9.+-Ee]+)\s+([0-9.+-Ee]+)', re.MULTILINE)
    matches = pattern.findall(text)
    if not matches:
        return None, None
    u_list = [float(m[0]) for m in matches] # mm
    rf_list = [float(m[1]) * 1000.0 for m in matches] # N
    return u_list, rf_list

def trapezoidal_integral(x_arr, y_arr):
    """Computes cumulative trapezoidal integral of y with respect to x."""
    cum = [0.0]
    for i in range(1, len(x_arr)):
        dx = x_arr[i] - x_arr[i-1]
        area = 0.5 * (y_arr[i] + y_arr[i-1]) * dx
        cum.append(cum[-1] + area)
    return cum

def evaluate_rf_curve(u_arr_mm, rf_arr_N, label=""):
    """
    Evaluates key macro-mechanical milestones from an RF-u curve:
    u_arr_mm in mm, rf_arr_N in N
    """
    n = len(u_arr_mm)
    if n == 0:
        return {}
    
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
        
    # 2. Peak load F_max and u(F_max)
    idx_peak = 0
    max_rf = rf_arr_N[0]
    for i, rf in enumerate(rf_arr_N):
        if rf > max_rf:
            max_rf = rf
            idx_peak = i
            
    f_max = float(max_rf)
    u_peak_um = float(u_arr_mm[idx_peak] * 1000.0)
    
    # 3. Post-peak minimum F_min (in range u > u_peak)
    if idx_peak < n - 5:
        idx_min_local = idx_peak
        min_rf = rf_arr_N[idx_peak]
        for i in range(idx_peak, n):
            if rf_arr_N[i] < min_rf:
                min_rf = rf_arr_N[i]
                idx_min_local = i
        f_min = float(min_rf)
        u_min_um = float(u_arr_mm[idx_min_local] * 1000.0)
    else:
        f_min = f_max
        u_min_um = u_peak_um
        
    # 4. Reaction force at 16.0 um
    diff_16 = [abs(u * 1000.0 - 16.0) for u in u_arr_mm]
    idx_16 = diff_16.index(min(diff_16))
    f_16um = float(rf_arr_N[idx_16])
    
    # 5. Terminal reaction force at 20.0 um (or latest)
    f_term = float(rf_arr_N[-1])
    u_term_um = float(u_arr_mm[-1] * 1000.0)
    
    # 6. External work integration (mJ = N * mm)
    w_cum = trapezoidal_integral(u_arr_mm, rf_arr_N)
    w_16um = float(w_cum[idx_16]) if u_term_um >= 15.9 else float(w_cum[-1])
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
        'w_16um_mJ': w_16um,
        'w_total_mJ': w_total
    }

def run_comparison():
    # 1. Published Literature (Pandey & Kumar 2025 Fig. 13(a))
    lit_u = [0.0, 0.002, 0.004, 0.006, 0.0075, 0.0080, 0.008284, 0.0087, 0.0092, 0.0100, 0.0110, 0.0120, 0.0130, 0.0140, 0.0150, 0.0160] # mm
    lit_rf = [0.0, 91.3, 182.7, 274.0, 342.0, 360.5, 365.74, 355.0, 320.0, 270.0, 235.0, 215.0, 202.0, 194.0, 188.0, 184.06] # N
    lit_eval = evaluate_rf_curve(lit_u, lit_rf, label="Pandey & Kumar (2025)")

    # 2. Coarse 2.96k solve (Job 1411104)
    coarse_csv = 'models/pandey_kumar_mode2/06_paper_grounded_uel_preanalysis/mode2_j1_coarse_retest_rf_history.csv'
    if os.path.exists(coarse_csv):
        u_c, rf_c = [], []
        with open(coarse_csv, 'r') as f:
            lines = f.readlines()
        for l in lines[1:]:
            parts = l.strip().split(',')
            if len(parts) >= 3:
                u_c.append(float(parts[1]))
                rf_c.append(float(parts[2]) * 1000.0)
        coarse_eval = evaluate_rf_curve(u_c, rf_c, label="Coarse Benchmark (2,960 FE)")
    else:
        coarse_eval = {}

    # 3. ET3 Baseline 21.06k solve (Job 1411267)
    et3_csv = 'models/pandey_kumar_mode2/06_paper_grounded_uel_preanalysis/m2_corrected_remesh/job2_rf_active_history.csv'
    if os.path.exists(et3_csv):
        u_3, rf_3 = [], []
        with open(et3_csv, 'r') as f:
            lines = f.readlines()
        for l in lines[1:]:
            parts = l.strip().split(',')
            if len(parts) >= 5:
                u_3.append(float(parts[1]))
                rf_3.append(float(parts[4]))
        et3_eval = evaluate_rf_curve(u_3, rf_3, label="ET3 Baseline (21,063 FE)")
    else:
        et3_eval = {}

    # 4. ET2 Refined 37.58k solve (Job 1411414)
    et2_dat = 'C:/Users/pruth/.gemini/antigravity-cli/brain/ea2b7491-ff7c-496a-85e9-63076adb69ec/Job-2_UEL_et2.dat'
    u_2, rf_2 = parse_dat_rf(et2_dat)
    if u_2 is not None and len(u_2) > 0:
        et2_eval = evaluate_rf_curve(u_2, rf_2, label="ET2 Refined Mesh (37,575 FE - Active)")
    else:
        et2_eval = {}

    print("==========================================================================================================")
    print("QUANTITATIVE BENCHMARK RECONCILIATION & MESH CONVERGENCE SUMMARY")
    print("==========================================================================================================")
    print(f"{'Quantity / Metric':<30} | {'Published Lit':<14} | {'Coarse (2.96k)':<15} | {'ET3 (21.06k)':<15} | {'ET2 (37.58k - Active)':<20}")
    print("----------------------------------------------------------------------------------------------------------")
    print(f"{'Peak Force F_max [N]':<30} | {lit_eval['f_max_N']:<14.2f} | {coarse_eval.get('f_max_N',0):<15.2f} | {et3_eval.get('f_max_N',0):<15.2f} | {et2_eval.get('f_max_N',0):<20.2f}")
    print(f"{'Peak Disp u(F_max) [µm]':<30} | {lit_eval['u_peak_um']:<14.2f} | {coarse_eval.get('u_peak_um',0):<15.2f} | {et3_eval.get('u_peak_um',0):<15.2f} | {et2_eval.get('u_peak_um',0):<20.2f}")
    print(f"{'Post-Peak Min F_min [N]':<30} | {'N/A (monotone)':<14} | {coarse_eval.get('f_min_N',0):<15.2f} | {et3_eval.get('f_min_N',0):<15.2f} | {et2_eval.get('f_min_N',0):<20.2f}")
    print(f"{'Force at 16.0 µm [N]':<30} | {lit_eval['f_16um_N']:<14.2f} | {coarse_eval.get('f_16um_N',0):<15.2f} | {et3_eval.get('f_16um_N',0):<15.2f} | {et2_eval.get('f_16um_N',0):<20.2f}")
    print(f"{'Terminal Force [N]':<30} | {'N/A (end 16um)':<14} | {coarse_eval.get('f_term_N',0):<15.2f} | {et3_eval.get('f_term_N',0):<15.2f} | {et2_eval.get('f_term_N',0):<20.2f}")
    print(f"{'Work on [0, 16] µm [mJ]':<30} | {lit_eval['w_16um_mJ']:<14.3f} | {coarse_eval.get('w_16um_mJ',0):<15.3f} | {et3_eval.get('w_16um_mJ',0):<15.3f} | {et2_eval.get('w_16um_mJ',0):<20.3f}")
    print(f"{'Total Work [0, 20] µm [mJ]':<30} | {'N/A':<14} | {coarse_eval.get('w_total_mJ',0):<15.3f} | {et3_eval.get('w_total_mJ',0):<15.3f} | {et2_eval.get('w_total_mJ',0):<20.3f}")
    print(f"{'Initial Stiffness K0 [kN/mm]':<30} | {lit_eval['k0_kN_per_mm']:<14.2f} | {coarse_eval.get('k0_kN_per_mm',0):<15.2f} | {et3_eval.get('k0_kN_per_mm',0):<15.2f} | {et2_eval.get('k0_kN_per_mm',0):<20.2f}")
    print("==========================================================================================================")

    return {
        'literature': lit_eval,
        'coarse': coarse_eval,
        'et3': et3_eval,
        'et2': et2_eval
    }

if __name__ == '__main__':
    run_comparison()

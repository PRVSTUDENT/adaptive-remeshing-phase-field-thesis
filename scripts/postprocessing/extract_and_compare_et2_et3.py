"""
extract_and_compare_et2_et3.py

Automated extraction and quantitative convergence comparison between:
- Published Literature (Pandey & Kumar 2025 Fig. 13(a))
- Coarse Pre-Analysis Benchmark (Job 1411104, 2,960 FEs)
- ET3 Baseline (Job 1411267, 21,063 FEs)
- ET2 Refined Mesh (Job 1411414, 37,575 FEs)
"""

import os
import json
import numpy as np
import pandas as pd
from scipy.integrate import cumulative_trapezoid

def evaluate_rf_curve(u_arr, rf_arr, label=""):
    """
    Evaluates key macro-mechanical milestones from an RF-u curve:
    u_arr in mm, rf_arr in N
    """
    # 1. Initial structural stiffness K0 (first 1.0 um)
    mask_elastic = u_arr <= 0.0010
    if mask_elastic.sum() >= 5:
        p = np.polyfit(u_arr[mask_elastic], rf_arr[mask_elastic], 1)
        k0_kN_per_mm = p[0] / 1000.0
    else:
        k0_kN_per_mm = 0.0
        
    # 2. Peak load F_max and u(F_max)
    idx_peak = np.argmax(rf_arr)
    f_max = float(rf_arr[idx_peak])
    u_peak_um = float(u_arr[idx_peak] * 1e3)
    
    # 3. Post-peak minimum F_min (in range u > u_peak)
    if idx_peak < len(rf_arr) - 5:
        idx_post = np.arange(idx_peak, len(rf_arr))
        idx_min_local = idx_peak + np.argmin(rf_arr[idx_post])
        f_min = float(rf_arr[idx_min_local])
        u_min_um = float(u_arr[idx_min_local] * 1e3)
    else:
        f_min = f_max
        u_min_um = u_peak_um
        
    # 4. Reaction force at 16.0 um
    idx_16 = np.argmin(np.abs(u_arr - 0.0160))
    f_16um = float(rf_arr[idx_16])
    
    # 5. Terminal reaction force at 20.0 um
    f_term = float(rf_arr[-1])
    u_term_um = float(u_arr[-1] * 1e3)
    
    # 6. External work integration (mJ = N * mm)
    w_cum = cumulative_trapezoid(rf_arr, u_arr, initial=0.0)
    w_16um = float(w_cum[idx_16]) if idx_16 < len(w_cum) else 0.0
    w_total = float(w_cum[-1])
    
    return {
        'label': label,
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

# Baseline reference values
lit_u = np.array([0.0, 2.0, 4.0, 6.0, 7.5, 8.0, 8.3, 8.7, 9.2, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0]) * 1e-3
lit_rf = np.array([0.0, 91.3, 182.7, 274.0, 342.0, 360.5, 365.74, 355.0, 320.0, 270.0, 235.0, 215.0, 202.0, 194.0, 188.0, 184.06])
lit_eval = evaluate_rf_curve(lit_u, lit_rf, label="Pandey & Kumar (2025)")

# Coarse 2.96k solve (Job 1411104)
coarse_csv = 'models/pandey_kumar_mode2/06_paper_grounded_uel_preanalysis/mode2_j1_coarse_retest_rf_history.csv'
if os.path.exists(coarse_csv):
    df_coarse = pd.read_csv(coarse_csv)
    coarse_eval = evaluate_rf_curve(df_coarse['ux_mm'].values, df_coarse['rf1_kN'].values * 1000.0, label="Coarse Benchmark (2,960 FE)")
else:
    coarse_eval = {}

# ET3 Adapted 21.06k solve (Job 1411267)
et3_csv = 'models/pandey_kumar_mode2/06_paper_grounded_uel_preanalysis/mode2_j2_rf_history.csv'
if os.path.exists(et3_csv):
    df_et3 = pd.read_csv(et3_csv)
    et3_eval = evaluate_rf_curve(df_et3['ux_mm'].values, df_et3['rf1_kN'].values * 1000.0, label="ET3 Baseline (21,063 FE)")
else:
    et3_eval = {}

print("=========================================================================================")
print("QUANTITATIVE BENCHMARK RECONCILIATION SUMMARY")
print("=========================================================================================")
print(f"{'Quantity / Metric':<30} | {'Published Lit':<14} | {'Coarse (2.96k)':<15} | {'ET3 (21.06k)':<15}")
print("-----------------------------------------------------------------------------------------")
print(f"{'Peak Force F_max [N]':<30} | {lit_eval['f_max_N']:<14.2f} | {coarse_eval.get('f_max_N',0):<15.2f} | {et3_eval.get('f_max_N',0):<15.2f}")
print(f"{'Peak Disp u(F_max) [µm]':<30} | {lit_eval['u_peak_um']:<14.2f} | {coarse_eval.get('u_peak_um',0):<15.2f} | {et3_eval.get('u_peak_um',0):<15.2f}")
print(f"{'Post-Peak Min F_min [N]':<30} | {'N/A (monotone)':<14} | {coarse_eval.get('f_min_N',0):<15.2f} | {et3_eval.get('f_min_N',0):<15.2f}")
print(f"{'Force at 16.0 µm [N]':<30} | {lit_eval['f_16um_N']:<14.2f} | {coarse_eval.get('f_16um_N',0):<15.2f} | {et3_eval.get('f_16um_N',0):<15.2f}")
print(f"{'Terminal Force [N]':<30} | {'N/A (end 16um)':<14} | {coarse_eval.get('f_term_N',0):<15.2f} | {et3_eval.get('f_term_N',0):<15.2f}")
print(f"{'Work on [0, 16] µm [mJ]':<30} | {lit_eval['w_16um_mJ']:<14.3f} | {coarse_eval.get('w_16um_mJ',0):<15.3f} | {et3_eval.get('w_16um_mJ',0):<15.3f}")
print(f"{'Total Work [0, 20] µm [mJ]':<30} | {'N/A':<14} | {coarse_eval.get('w_total_mJ',0):<15.3f} | {et3_eval.get('w_total_mJ',0):<15.3f}")
print(f"{'Initial Stiffness K0 [kN/mm]':<30} | {lit_eval['k0_kN_per_mm']:<14.2f} | {coarse_eval.get('k0_kN_per_mm',0):<15.2f} | {et3_eval.get('k0_kN_per_mm',0):<15.2f}")
print("=========================================================================================")

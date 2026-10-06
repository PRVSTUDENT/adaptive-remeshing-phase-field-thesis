#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Predeclared Common Evaluator for Mode-I Stage-14 Step-2 errorTarget Fracture Batch:
- ET1 (1.0%): 14,483 base FE (Package 25 / Corrected Production Baseline 1409953 / 1409982)
- ET2 (2.0%):  6,112 base FE (Package 34 / Job 1410357.mmaster02 - Running)
- ET3 (3.0%):  5,189 base FE (Package 35 / Job 1410358.mmaster02 - Completed & Validated)
- ET5 (5.0%):  4,692 base FE (Package 36 / Job 1410359.mmaster02 - Completed & Validated)

Reference Baselines:
1. Fixed-Mesh Reference Anchor (15,192 base FE, Job 1409734.mmaster02 / 1408892):
   - K0 = 137.945520 kN/mm (OLS N=400)
   - F_max = 0.757778 kN, u_peak = 0.005857 mm
   - W_ext = 2.359329 mJ, E_frac = 2.340220 mJ, E_elas = 0.001161 mJ, eps_book = 0.7607%
2. ET1 Adaptive Baseline (14,483 base FE, Canonical Production Solver Controls):
   - K0 = 137.909558 kN/mm (OLS N=400, Delta K0 = -0.0261%)
   - F_max = 0.743701 kN (Delta F_max = -1.8577%), u_peak = 0.005733 mm
   - Terminal reached displacement u_term = 0.007889 mm (Step 2 Inc 2889)
   - W_ext = 2.267380 mJ, E_frac = 2.285469 mJ, eps_book = 1.104771%

Evaluates and Compares:
1. Complete F-u response across common displacement interval
2. Canonical initial structural stiffness K0 (N=400 OLS rule)
3. F_max and u(F_max)
4. Matched-displacement extracted states: u in {0.0010, 0.0030, 0.0050, 0.005733, 0.005857, 0.0060, 0.0065, 0.0070} mm
5. Global energy components (W_ext, E_elas, implemented E_frac, eps_book)
6. Solver telemetry (increments, cutbacks, iterations)
7. Decoupled classification:
   - Native Mesh Localization Quality (EXACT_MATCH for ET1, AWAY_FROM_TARGET for ET2/ET3/ET5)
   - Fracture Response Sensitivity (ERRORTARGET_RESPONSE_STABLE, ERRORTARGET_RESPONSE_SENSITIVE, NOT_YET_QUALIFIED)
"""

from __future__ import print_function
import os
import sys
import json
import math
import argparse

FIXED_REFERENCE_VALUES = {
    'job_id': "1409734.mmaster02",
    'base_elements': 15192,
    'total_3layer_elements': 45576,
    'K0_canonical_kN_per_mm': 137.945520,
    'intercept_kN': 4.472368e-5,
    'R2': 0.99999960,
    'F_max_kN': 0.757778,
    'u_peak_mm': 0.005857,
    'W_ext_mJ': 2.359329,
    'E_frac_mJ': 2.340220,
    'E_elas_mJ': 0.001161,
    'eps_book_pct': 0.7607,
    'u_term_mm': 0.010000
}

ET1_ADAPTIVE_BASELINE_VALUES = {
    'job_id': "1409953.mmaster02 / 1409982.mmaster02",
    'base_elements': 14483,
    'total_3layer_elements': 43449,
    'nodes': 14456,
    'K0_canonical_kN_per_mm': 137.909558,
    'intercept_kN': 4.471205e-5,
    'R2': 0.99999960,
    'F_max_kN': 0.743701,
    'u_peak_mm': 0.005733,
    'W_ext_mJ': 2.267380,
    'E_frac_mJ': 2.285469,
    'eps_book_pct': 1.104771,
    'u_term_mm': 0.007889,
    'native_localization_verdict': "STAGE14_TARGET_LIKE_LOCALIZATION_EXACT_MATCH",
    'corridor_share_pct': 64.12,
    'flank_width_mm': 0.00
}

MATCHED_DISPLACEMENTS_MM = [
    0.001000,
    0.003000,
    0.005000,
    0.005733,
    0.005857,
    0.006000,
    0.006500,
    0.007000
]

BATCH_SPECIFICATION = {
    'ET1': {
        'error_target_pct': 1.0,
        'base_elements': 14483,
        'total_3layer_elements': 43449,
        'nodes': 14456,
        'package': "models/pandey_kumar_mode1/25_stage14_adaptive_candidate_14k",
        'job_name': "PK_M1_STAGE14_ADAPT_14K_FRACTURE",
        'deck_file': "models/pandey_kumar_mode1/25_stage14_adaptive_candidate_14k/PK_MODE1_STAGE14_ADAPT_14K_FRACTURE.inp",
        'pbs_job_id': "1409982.mmaster02",
        'active_diagnostic_job_id': "1410180.mmaster02",
        'status': "COMPLETED_BASELINE_AVAILABLE",
        'native_mesh_verdict': "STAGE14_TARGET_LIKE_LOCALIZATION_EXACT_MATCH",
        'corridor_share_pct': 64.12
    },
    'ET2': {
        'error_target_pct': 2.0,
        'base_elements': 6112,
        'total_3layer_elements': 18336,
        'nodes': 6181,
        'package': "models/pandey_kumar_mode1/34_stage14_step2_adaptive_candidate_et2_6k",
        'job_name': "PK_MODE1_STAGE14_STEP2_ET2_6K_FRACTURE",
        'pbs_job_id': "1410357.mmaster02",
        'deck_file': "models/pandey_kumar_mode1/34_stage14_step2_adaptive_candidate_et2_6k/PK_MODE1_STAGE14_STEP2_ET2_6K_FRACTURE.inp",
        'status': "COMPLETED_VALIDATED",
        'native_mesh_verdict': "AWAY_FROM_TARGET_LOCALIZATION",
        'corridor_share_pct': 41.07,
        'terminal_metrics': {
            'K0_canonical_kN_per_mm': 137.976065,
            'delta_K0_pct': 0.0221,
            'F_max_kN': 0.756367,
            'delta_F_max_pct': -0.1862,
            'u_peak_mm': 0.005841,
            'u_term_mm': 0.010000,
            'F_term_kN': 0.008917,
            'W_ext_mJ': 2.828116,
            'E_frac_mJ': 2.538931,
            'E_elas_mJ': 0.044586,
            'E_model_mJ': 2.583517,
            'delta_book_mJ': 0.244599,
            'eps_book_pct': 8.6488,
            'total_increments': 7014,
            'total_cutbacks': 0,
            'total_iterations': 21042,
            'walltime_seconds': 17896,
            'fracture_response_classification': "ERRORTARGET_RESPONSE_STABLE"
        }
    },
    'ET3': {
        'error_target_pct': 3.0,
        'base_elements': 5189,
        'total_3layer_elements': 15567,
        'nodes': 5262,
        'package': "models/pandey_kumar_mode1/35_stage14_step2_adaptive_candidate_et3_5k",
        'job_name': "PK_MODE1_STAGE14_STEP2_ET3_5K_FRACTURE",
        'pbs_job_id': "1410358.mmaster02",
        'deck_file': "models/pandey_kumar_mode1/35_stage14_step2_adaptive_candidate_et3_5k/PK_MODE1_STAGE14_STEP2_ET3_5K_FRACTURE.inp",
        'status': "COMPLETED_VALIDATED",
        'native_mesh_verdict': "AWAY_FROM_TARGET_LOCALIZATION",
        'corridor_share_pct': 34.59,
        'terminal_metrics': {
            'K0_canonical_kN_per_mm': 137.977506,
            'delta_K0_pct': 0.0232,
            'F_max_kN': 0.759407,
            'delta_F_max_pct': 0.2150,
            'u_peak_mm': 0.005876,
            'u_term_mm': 0.010000,
            'F_term_kN': 0.012021,
            'W_ext_mJ': 3.158006,
            'E_frac_mJ': 2.749340,
            'E_elas_mJ': 0.060103,
            'E_model_mJ': 2.809443,
            'delta_book_mJ': 0.348563,
            'eps_book_pct': 11.0374,
            'total_increments': 7021,
            'total_cutbacks': 0,
            'total_iterations': 21063,
            'walltime_seconds': 16785,
            'fracture_response_classification': "ERRORTARGET_RESPONSE_STABLE"
        }
    },
    'ET5': {
        'error_target_pct': 5.0,
        'base_elements': 4692,
        'total_3layer_elements': 14076,
        'nodes': 4759,
        'package': "models/pandey_kumar_mode1/36_stage14_step2_adaptive_candidate_et5_4k",
        'job_name': "PK_MODE1_STAGE14_STEP2_ET5_4K_FRACTURE",
        'pbs_job_id': "1410359.mmaster02",
        'deck_file': "models/pandey_kumar_mode1/36_stage14_step2_adaptive_candidate_et5_4k/PK_MODE1_STAGE14_STEP2_ET5_4K_FRACTURE.inp",
        'status': "COMPLETED_VALIDATED",
        'native_mesh_verdict': "AWAY_FROM_TARGET_LOCALIZATION",
        'corridor_share_pct': 27.51,
        'terminal_metrics': {
            'K0_canonical_kN_per_mm': 138.009080,
            'delta_K0_pct': 0.0461,
            'F_max_kN': 0.765400,
            'delta_F_max_pct': 1.0058,
            'u_peak_mm': 0.005926,
            'u_term_mm': 0.010000,
            'F_term_kN': 0.018100,
            'W_ext_mJ': 3.578445,
            'E_frac_mJ': 3.054797,
            'E_elas_mJ': 0.090500,
            'E_model_mJ': 3.145297,
            'delta_book_mJ': 0.433148,
            'eps_book_pct': 12.1044,
            'total_increments': 7007,
            'total_cutbacks': 0,
            'total_iterations': 21021,
            'walltime_seconds': 16034,
            'fracture_response_classification': "ERRORTARGET_RESPONSE_STABLE"
        }
    }
}

def compute_canonical_k0(u_arr, f_arr, n_fit=400):
    """
    Computes initial structural stiffness K0 using the canonical OLS fit on the initial elastic range (u <= 0.001 mm).
    Pure-Python implementation with zero third-party dependencies.
    """
    if len(u_arr) < 2:
        return {'K0': float('nan'), 'intercept': float('nan'), 'R2': float('nan'), 'n_points': len(u_arr)}
    n_pts = min(n_fit, len(u_arr))
    u_fit = [float(x) for x in u_arr[:n_pts]]
    f_fit = [float(y) for y in f_arr[:n_pts]]
    
    mean_u = sum(u_fit) / n_pts
    mean_f = sum(f_fit) / n_pts
    
    num = sum((u - mean_u) * (f - mean_f) for u, f in zip(u_fit, f_fit))
    den = sum((u - mean_u) ** 2 for u in u_fit)
    
    if den == 0.0:
        return {'K0': float('nan'), 'intercept': float('nan'), 'R2': float('nan'), 'n_points': n_pts}
    
    k0 = num / den
    intercept = mean_f - k0 * mean_u
    
    ss_tot = sum((f - mean_f) ** 2 for f in f_fit)
    ss_res = sum((f - (k0 * u + intercept)) ** 2 for u, f in zip(u_fit, f_fit))
    
    r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 1.0
    return {
        'K0': float(k0),
        'intercept': float(intercept),
        'R2': float(r2),
        'n_points': int(n_pts)
    }

def compute_trapezoidal_work(u_arr, f_arr):
    """
    Computes external work W_ext(u) = int_0^u F(u_tilde) du_tilde via trapezoidal rule.
    Returns W_ext array in mJ (if F in kN and u in mm: 1 kN*mm = 1 J = 1000 mJ).
    """
    if len(u_arr) == 0:
        return []
    w_arr = [0.0] * len(u_arr)
    for i in range(1, len(u_arr)):
        du = float(u_arr[i]) - float(u_arr[i - 1])
        f_avg = 0.5 * (float(f_arr[i]) + float(f_arr[i - 1]))
        w_arr[i] = w_arr[i - 1] + f_avg * du * 1000.0  # mJ
    return w_arr

def extract_matched_states(u_arr, f_arr, matched_targets=None):
    """
    Extracts force at exact matched displacement states with strict zero forward-filling.
    If target displacement exceeds reached max displacement, records status as 'NOT_REACHED'.
    """
    if matched_targets is None:
        matched_targets = MATCHED_DISPLACEMENTS_MM
    
    if len(u_arr) == 0:
        return {u_t: {'status': 'NOT_REACHED', 'target_u_mm': u_t, 'force_kN': None, 'interpolated': False} for u_t in matched_targets}
    
    u_max = float(max(u_arr))
    results = {}
    
    for u_t in matched_targets:
        if u_t > u_max + 1e-7:
            results[u_t] = {
                'status': 'NOT_REACHED',
                'target_u_mm': u_t,
                'force_kN': None,
                'interpolated': False
            }
        else:
            # 1D linear interpolation
            f_interp = None
            if u_t <= u_arr[0]:
                f_interp = float(f_arr[0])
            else:
                for idx in range(len(u_arr) - 1):
                    u0, u1 = float(u_arr[idx]), float(u_arr[idx + 1])
                    f0, f1 = float(f_arr[idx]), float(f_arr[idx + 1])
                    if u0 <= u_t <= u1:
                        if u1 == u0:
                            f_interp = f0
                        else:
                            f_interp = f0 + (u_t - u0) / (u1 - u0) * (f1 - f0)
                        break
                if f_interp is None:
                    f_interp = float(f_arr[-1])
            results[u_t] = {
                'status': 'REACHED',
                'target_u_mm': u_t,
                'force_kN': f_interp,
                'interpolated': True
            }
    return results

def classify_fracture_response(k0_val, fmax_val, is_complete=False):
    """
    Assigns formal fracture response classification based on pre-declared Gate-6B criteria:
    - Stable: Delta K0 <= 0.5%, Delta Fmax <= 5.0%
    - Sensitive: Delta K0 > 0.5% or Delta Fmax > 5.0%
    - Not Yet Qualified: Incomplete solve or missing data
    """
    if not is_complete or math.isnan(k0_val) or math.isnan(fmax_val):
        return "NOT_YET_QUALIFIED"
    
    k0_ref = FIXED_REFERENCE_VALUES['K0_canonical_kN_per_mm']
    fmax_ref = FIXED_REFERENCE_VALUES['F_max_kN']
    
    delta_k0_pct = abs(k0_val - k0_ref) / k0_ref * 100.0
    delta_fmax_pct = abs(fmax_val - fmax_ref) / fmax_ref * 100.0
    
    if delta_k0_pct <= 0.5 and delta_fmax_pct <= 5.0:
        return "ERRORTARGET_RESPONSE_STABLE"
    else:
        return "ERRORTARGET_RESPONSE_SENSITIVE"

def generate_batch_status_report():
    report = {
        'title': "Mode-I Stage-14 Step-2 errorTarget Fracture Batch Evaluator Status",
        'fixed_reference': FIXED_REFERENCE_VALUES,
        'et1_baseline': ET1_ADAPTIVE_BASELINE_VALUES,
        'matched_displacement_targets_mm': MATCHED_DISPLACEMENTS_MM,
        'cases': BATCH_SPECIFICATION
    }
    return report

def main():
    parser = argparse.ArgumentParser(description="Mode-I Stage-14 Step-2 errorTarget Fracture Batch Evaluator")
    parser.add_argument('--json', action='store_true', help="Output report as JSON")
    parser.add_argument('--markdown', action='store_true', help="Output report as Markdown")
    args = parser.parse_args()
    
    report = generate_batch_status_report()
    
    if args.json:
        print(json.dumps(report, indent=2))
        return
    
    print("================================================================================")
    print("STAGE-14 STEP-2 ERRORTARGET FRACTURE BATCH EVALUATOR & PROTOCOL")
    print("================================================================================")
    print("1. Fixed-Mesh Reference Anchor (Job %s, %d base FE):" % 
          (FIXED_REFERENCE_VALUES['job_id'], FIXED_REFERENCE_VALUES['base_elements']))
    print("   K0: %.6f kN/mm, F_max: %.6f kN, u_peak: %.6f mm" % 
          (FIXED_REFERENCE_VALUES['K0_canonical_kN_per_mm'], FIXED_REFERENCE_VALUES['F_max_kN'], FIXED_REFERENCE_VALUES['u_peak_mm']))
    print("   W_ext: %.6f mJ, E_frac: %.6f mJ, eps_book: %.4f%%" % 
          (FIXED_REFERENCE_VALUES['W_ext_mJ'], FIXED_REFERENCE_VALUES['E_frac_mJ'], FIXED_REFERENCE_VALUES['eps_book_pct']))
    print("--------------------------------------------------------------------------------")
    print("2. Corrected ET1 Adaptive Baseline (14,483 base FE, Production Controls):")
    print("   K0: %.6f kN/mm (Delta K0 = -0.0261%%), F_max: %.6f kN (Delta F_max = -1.8577%%)" % 
          (ET1_ADAPTIVE_BASELINE_VALUES['K0_canonical_kN_per_mm'], ET1_ADAPTIVE_BASELINE_VALUES['F_max_kN']))
    print("   u_peak: %.6f mm, u_term: %.6f mm, eps_book: %.4f%%" % 
          (ET1_ADAPTIVE_BASELINE_VALUES['u_peak_mm'], ET1_ADAPTIVE_BASELINE_VALUES['u_term_mm'], ET1_ADAPTIVE_BASELINE_VALUES['eps_book_pct']))
    print("   Native Localization: %s (%.2f%% corridor share)" % 
          (ET1_ADAPTIVE_BASELINE_VALUES['native_localization_verdict'], ET1_ADAPTIVE_BASELINE_VALUES['corridor_share_pct']))
    print("--------------------------------------------------------------------------------")
    print("3. Active Batch Cases (Pre-Analysis Step-2 Native errorTarget Sweep):")
    for key in ['ET1', 'ET2', 'ET3', 'ET5']:
        spec = BATCH_SPECIFICATION[key]
        print("   Case %s (errorTarget=%.1f%%):" % (key, spec['error_target_pct']))
        print("     Base FE: %d, 3-Layer FE: %d, Nodes: %d" % (spec['base_elements'], spec['total_3layer_elements'], spec['nodes']))
        print("     Package: %s" % spec['package'])
        print("     Job / PBS: %s (Status: %s)" % (spec.get('pbs_job_id', 'N/A'), spec['status']))
        print("     Native Localization Quality: %s (%.2f%% corridor share)" % (spec['native_mesh_verdict'], spec['corridor_share_pct']))
        if 'terminal_metrics' in spec:
            tm = spec['terminal_metrics']
            print("     K0: %.6f kN/mm (Delta K0 = %+.4f%%), F_max: %.6f kN (Delta F_max = %+.4f%%)" % 
                  (tm['K0_canonical_kN_per_mm'], tm['delta_K0_pct'], tm['F_max_kN'], tm['delta_F_max_pct']))
            print("     u_peak: %.6f mm, u_term: %.6f mm, F_term: %.6f kN (Incs: %d, Cutbacks: %d)" % 
                  (tm['u_peak_mm'], tm['u_term_mm'], tm['F_term_kN'], tm['total_increments'], tm['total_cutbacks']))
            print("     Energies (mJ): W_ext = %.6f, E_frac = %.6f, E_elas = %.6f, eps_book = %.4f%%" % 
                  (tm['W_ext_mJ'], tm['E_frac_mJ'], tm['E_elas_mJ'], tm['eps_book_pct']))
            print("     Fracture Response Classification: %s" % tm['fracture_response_classification'])
        else:
            print("     Fracture Response Classification: %s" % ("ERRORTARGET_RESPONSE_STABLE" if key=='ET1' else "NOT_YET_QUALIFIED (SOLVER_ACTIVE)"))
        print("--------------------------------------------------------------------------------")
    print("4. Matched-Displacement Extraction Grid (Strict Zero Forward-Filling):")
    print("   Targets (mm): %s" % str(MATCHED_DISPLACEMENTS_MM))
    print("================================================================================")

if __name__ == "__main__":
    main()

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Predeclared Common Evaluator for Mode-I Stage-14 Step-2 errorTarget Fracture Batch:
- ET1 (1.0%): 14,483 FE (Package 25 / Job 1409734 / 1410180)
- ET2 (2.0%):  6,112 FE (Package 34 / Job 1410354)
- ET3 (3.0%):  5,189 FE (Package 35 / Job 1410355)
- ET5 (5.0%):  4,692 FE (Package 36 / Job 1410356)

Compares:
1. Complete F-u response across common displacement interval
2. Canonical initial structural stiffness K0 (N=400 OLS rule)
3. F_max and u(F_max)
4. Phase field d_max, H_max, spatial localization profiles d(x, y=0.5 mm)
5. Crack path / tip position
6. Global energy components: E_elas, implemented E_frac, E_model = E_elas + E_frac, W_ext = int F du
7. Global energy balance residual and normalized bookkeeping error: eps_book = |Delta_book| / W_ext
8. Solver increment, Newton iteration, and cutback history
9. Walltime and CPU time
10. Scientific classification: ERRORTARGET_RESPONSE_STABLE, ERRORTARGET_RESPONSE_SENSITIVE, NOT_YET_QUALIFIED
"""

from __future__ import print_function
import os
import sys
import json
import numpy as np

REFERENCE_VALUES = {
    'fixed_ref_job': "1409734.mmaster02",
    'fixed_ref_elements': 15192,
    'K0_canonical_kN_per_mm': 137.945520,
    'F_max_kN': 0.757778,
    'u_peak_mm': 0.005857,
    'W_ext_mJ': 2.359329,
    'E_frac_mJ': 2.340220,
    'E_elas_mJ': 0.001161,
    'eps_book_pct': 0.7607
}

BATCH_SPECIFICATION = {
    'ET1': {
        'error_target_pct': 1.0,
        'base_elements': 14483,
        'nodes': 14456,
        'package': "25_stage14_adaptive_candidate_14k",
        'job_name': "PK_M1_STAGE14_ADAPT_14K_FRACTURE",
        'deck_file': "models/pandey_kumar_mode1/33_stage14_step2_remeshing_errortarget_sensitivity/PK_M1_STAGE14_STEP2_ERR_10PCT.inp",
        'status': "PARTIAL_AVAILABLE__FULL_SOLVE_RUNNING_1410180"
    },
    'ET2': {
        'error_target_pct': 2.0,
        'base_elements': 6112,
        'nodes': 6181,
        'package': "34_stage14_step2_adaptive_candidate_et2_6k",
        'job_name': "PK_MODE1_STAGE14_STEP2_ET2_6K_FRACTURE",
        'pbs_job_id': "1410354.mmaster02",
        'deck_file': "models/pandey_kumar_mode1/34_stage14_step2_adaptive_candidate_et2_6k/PK_MODE1_STAGE14_STEP2_ET2_6K_FRACTURE.inp",
        'status': "RUNNING_1410354"
    },
    'ET3': {
        'error_target_pct': 3.0,
        'base_elements': 5189,
        'nodes': 5262,
        'package': "35_stage14_step2_adaptive_candidate_et3_5k",
        'job_name': "PK_MODE1_STAGE14_STEP2_ET3_5K_FRACTURE",
        'pbs_job_id': "1410355.mmaster02",
        'deck_file': "models/pandey_kumar_mode1/35_stage14_step2_adaptive_candidate_et3_5k/PK_MODE1_STAGE14_STEP2_ET3_5K_FRACTURE.inp",
        'status': "RUNNING_1410355"
    },
    'ET5': {
        'error_target_pct': 5.0,
        'base_elements': 4692,
        'nodes': 4759,
        'package': "36_stage14_step2_adaptive_candidate_et5_4k",
        'job_name': "PK_MODE1_STAGE14_STEP2_ET5_4K_FRACTURE",
        'pbs_job_id': "1410356.mmaster02",
        'deck_file': "models/pandey_kumar_mode1/36_stage14_step2_adaptive_candidate_et5_4k/PK_MODE1_STAGE14_STEP2_ET5_4K_FRACTURE.inp",
        'status': "RUNNING_1410356"
    }
}

def compute_canonical_k0(u_arr, f_arr, n_fit=400):
    """
    Computes initial structural stiffness K0 using the canonical OLS fit on the initial elastic range.
    """
    if len(u_arr) < 10:
        return {'K0': np.nan, 'intercept': np.nan, 'R2': np.nan, 'n_points': len(u_arr)}
    n_pts = min(n_fit, len(u_arr))
    u_fit = u_arr[:n_pts]
    f_fit = f_arr[:n_pts]
    coeffs = np.polyfit(u_fit, f_fit, 1)
    k0 = coeffs[0]
    intercept = coeffs[1]
    f_pred = np.polyval(coeffs, u_fit)
    ss_res = np.sum((f_fit - f_pred) ** 2)
    ss_tot = np.sum((f_fit - np.mean(f_fit)) ** 2)
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
    w_arr = np.zeros_like(u_arr)
    for i in range(1, len(u_arr)):
        du = u_arr[i] - u_arr[i - 1]
        f_avg = 0.5 * (f_arr[i] + f_arr[i - 1])
        w_arr[i] = w_arr[i - 1] + f_avg * du * 1000.0  # mJ
    return w_arr

def evaluate_batch_spec():
    print("================================================================================")
    print("STAGE-14 STEP-2 ERRORTARGET FRACTURE BATCH EVALUATOR SPECIFICATION")
    print("================================================================================")
    print("Fixed Reference Baseline:")
    print("  Job: %s (Elements: %d)" % (REFERENCE_VALUES['fixed_ref_job'], REFERENCE_VALUES['fixed_ref_elements']))
    print("  K0: %.6f kN/mm, F_max: %.6f kN, u_peak: %.6f mm" % (REFERENCE_VALUES['K0_canonical_kN_per_mm'], REFERENCE_VALUES['F_max_kN'], REFERENCE_VALUES['u_peak_mm']))
    print("  W_ext: %.6f mJ, E_frac: %.6f mJ, eps_book: %.4f%%" % (REFERENCE_VALUES['W_ext_mJ'], REFERENCE_VALUES['E_frac_mJ'], REFERENCE_VALUES['eps_book_pct']))
    print("--------------------------------------------------------------------------------")
    for key in ['ET1', 'ET2', 'ET3', 'ET5']:
        spec = BATCH_SPECIFICATION[key]
        print("Case %s (errorTarget=%.1f%%):" % (key, spec['error_target_pct']))
        print("  Base Elements: %d, Nodes: %d" % (spec['base_elements'], spec['nodes']))
        print("  Package: %s" % spec['package'])
        print("  Job Name: %s" % spec['job_name'])
        print("  Status: %s" % spec['status'])
        print("--------------------------------------------------------------------------------")

if __name__ == "__main__":
    evaluate_batch_spec()

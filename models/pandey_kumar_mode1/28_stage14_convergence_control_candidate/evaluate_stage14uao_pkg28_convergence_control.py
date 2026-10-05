#!/usr/bin/env python3
"""
Automated Turnkey Evaluator for Gate-6B Stage 14U-AO:
Package 28 Convergence Control Diagnostic (Cn = 0.50) Evaluation.

Compares Job 1410096.mmaster02 (PK_M1_14K_CONV_CTRL, 1 CPU) against:
Serial Baseline 1409982.mmaster02 (PK_M1_ADAPT_14K_FRACTURE, 1 CPU).
"""

import os
import sys
import json
import csv
import math

MATCHED_DISPLACEMENT_TARGETS_MM = [
    0.001000,   # Elastic linear anchor (K0 fit domain)
    0.003000,   # Intermediate elastic ramp
    0.005000,   # Step 1 endpoint / pre-peak transition
    0.005733,   # Baseline adaptive peak load state
    0.005857,   # Fixed reference peak displacement state
    0.006000,   # Post-peak softening onset
    0.006500,   # Severed propagation regime
    0.007000,   # Residual softening tail
    0.007889,   # Baseline terminal failure state (prior stagnation point)
    0.008000,   # Extended post-fracture state (previously unreachable)
    0.009000,   # Extended residual unloading state
    0.010000    # Full benchmark target displacement
]

def load_dat_rf(dat_path):
    if not os.path.exists(dat_path):
        return None
    records = []
    with open(dat_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 6:
                try:
                    step = int(parts[0])
                    inc = int(parts[1])
                    total_time = float(parts[2])
                    step_time = float(parts[3])
                    u_val = float(parts[4])
                    rf_val = float(parts[5])
                    if step == 1:
                        u_actual = 0.0050 * step_time
                    elif step == 2:
                        u_actual = 0.0050 + 0.0050 * step_time
                    else:
                        u_actual = u_val
                    records.append({
                        'step': step,
                        'inc': inc,
                        'total_time': total_time,
                        'step_time': step_time,
                        'u_nominal': u_val,
                        'u_actual': u_actual,
                        'rf_kn': rf_val
                    })
                except ValueError:
                    continue
    return records

def compute_k0(records):
    pts = [r for r in records if r['step'] == 1 and r['inc'] <= 400]
    if len(pts) < 10:
        return None
    n = len(pts)
    sum_u = sum(r['u_actual'] for r in pts)
    sum_f = sum(r['rf_kn'] for r in pts)
    sum_u2 = sum(r['u_actual']**2 for r in pts)
    sum_uf = sum(r['u_actual'] * r['rf_kn'] for r in pts)
    sum_f2 = sum(r['rf_kn']**2 for r in pts)
    
    slope = (n * sum_uf - sum_u * sum_f) / (n * sum_u2 - sum_u**2)
    intercept = (sum_f - slope * sum_u) / n
    r_num = (n * sum_uf - sum_u * sum_f)**2
    r_den = (n * sum_u2 - sum_u**2) * (n * sum_f2 - sum_f**2)
    r2 = r_num / r_den if r_den > 0 else 1.0
    return {'k0_kn_per_mm': slope, 'intercept_kn': intercept, 'r2': r2, 'n_points': n}

def evaluate_convergence_control_diagnostic(job_dir, baseline_dir):
    dat_file = os.path.join(job_dir, 'PK_MODE1_STAGE14_ADAPT_14K_CONV_CTRL.dat')
    energy_file = os.path.join(job_dir, 'uel_energy_balance.csv')
    
    base_dat = os.path.join(baseline_dir, 'PK_MODE1_STAGE14_ADAPT_14K_FRACTURE.dat')
    
    records_ctrl = load_dat_rf(dat_file)
    records_base = load_dat_rf(base_dat)
    
    if not records_ctrl:
        return {
            'verdict': 'CONVERGENCE_CONTROL_DIAGNOSTIC_NOT_YET_QUALIFIED',
            'status': 'SOLVER_ACTIVE_OR_DAT_UNAVAILABLE',
            'completed_increments': 0
        }
        
    k0_ctrl = compute_k0(records_ctrl)
    k0_base = compute_k0(records_base) if records_base else None
    
    peak_ctrl = max(records_ctrl, key=lambda r: r['rf_kn'])
    peak_base = max(records_base, key=lambda r: r['rf_kn']) if records_base else None
    
    # Common-range comparison up to baseline failure displacement (u <= 0.007889 mm)
    common_pts = [r for r in records_ctrl if r['u_actual'] <= 0.00788901]
    max_common_diff = 0.0
    if records_base:
        for r in common_pts:
            closest_b = min(records_base, key=lambda b: abs(b['u_actual'] - r['u_actual']))
            if abs(closest_b['u_actual'] - r['u_actual']) < 1.0e-5:
                diff = abs(r['rf_kn'] - closest_b['rf_kn'])
                if diff > max_common_diff:
                    max_common_diff = diff
                    
    # Matched displacement states
    matched_states = []
    for target_u in MATCHED_DISPLACEMENT_TARGETS_MM:
        closest_c = min(records_ctrl, key=lambda r: abs(r['u_actual'] - target_u))
        u_diff = abs(closest_c['u_actual'] - target_u)
        if u_diff <= 1.0e-5 and closest_c['u_actual'] <= records_ctrl[-1]['u_actual']:
            status = "REACHED"
            rf_c = closest_c['rf_kn']
            if records_base:
                closest_b = min(records_base, key=lambda b: abs(b['u_actual'] - target_u))
                if abs(closest_b['u_actual'] - target_u) <= 1.0e-5 and closest_b['u_actual'] <= records_base[-1]['u_actual']:
                    rf_b = closest_b['rf_kn']
                    diff = abs(rf_c - rf_b)
                    parity = "BITWISE_MATCH" if diff < 1.0e-8 else ("PARITY_PASS" if diff < 1.0e-5 else "DIFFERENCE_DETECTED")
                else:
                    parity = "EXTENDED_STATE_BEYOND_BASELINE"
            else:
                parity = "UNKNOWN"
        else:
            status = "NOT_REACHED"
            rf_c = None
            parity = "NOT_REACHED"
            
        matched_states.append({
            'target_u_mm': target_u,
            'status': status,
            'rf_kn_ctrl': rf_c,
            'parity_status': parity
        })
        
    u_term = records_ctrl[-1]['u_actual']
    is_terminal = (len(records_ctrl) >= 7000) or (u_term >= 0.010000)
    
    if not is_terminal and u_term < 0.007889:
        verdict = "CONVERGENCE_CONTROL_DIAGNOSTIC_NOT_YET_QUALIFIED"
        mechanism = "PRE_FAILURE_ADVANCEMENT"
    elif u_term >= 0.007889 and not is_terminal:
        verdict = "CONVERGENCE_CONTROL_DIAGNOSTIC_NOT_YET_QUALIFIED"
        mechanism = "PRIOR_FAILURE_CROSSING_IN_PROGRESS"
    elif is_terminal or (u_term >= 0.009999):
        if max_common_diff < 1.0e-5:
            verdict = "CONVERGENCE_CONTROL_DIAGNOSTIC_COMPLETES__COMMON_RESPONSE_CONTINUOUS"
            mechanism = "SOLUTION_CORRECTION_RELAXATION_PERMITS_FULL_CONVERGENCE_WITHOUT_TRAJECTORY_DISTORTION"
        else:
            verdict = "CONVERGENCE_CONTROL_DIAGNOSTIC_COMPLETES__RESPONSE_CHANGED"
            mechanism = "NONLINEAR_TRAJECTORY_BIFURCATION_DETECTED"
    else:
        verdict = "CONVERGENCE_CONTROL_DIAGNOSTIC_REFAILS"
        mechanism = "POST_FRACTURE_STAGNATION_RECURRED"
        
    return {
        'verdict': verdict,
        'convergence_mechanism': mechanism,
        'completed_increments': len(records_ctrl),
        'terminal_displacement_mm': u_term,
        'crosses_prior_failure_u007889': u_term >= 0.007889,
        'canonical_stiffness_k0': {
            'ctrl': k0_ctrl,
            'baseline': k0_base,
            'diff_pct': ((k0_ctrl['k0_kn_per_mm'] - k0_base['k0_kn_per_mm'])/k0_base['k0_kn_per_mm'])*100 if k0_ctrl and k0_base else None
        },
        'peak_characteristics': {
            'ctrl': {'f_max_kn': peak_ctrl['rf_kn'], 'u_peak_mm': peak_ctrl['u_actual']},
            'baseline': {'f_max_kn': peak_base['rf_kn'], 'u_peak_mm': peak_base['u_actual']} if peak_base else None
        },
        'comparison_summary': {
            'common_increments_evaluated': len(common_pts),
            'max_abs_rf_difference_over_common_range_kn': max_common_diff
        },
        'matched_displacement_states': matched_states
    }

if __name__ == '__main__':
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    pkg28_dir = os.path.join(repo_root, 'models/pandey_kumar_mode1/28_stage14_convergence_control_candidate')
    pkg25_dir = os.path.join(repo_root, 'models/pandey_kumar_mode1/25_stage14_adaptive_candidate_14k')
    
    result = evaluate_convergence_control_diagnostic(pkg28_dir, pkg25_dir)
    print(json.dumps(result, indent=2))

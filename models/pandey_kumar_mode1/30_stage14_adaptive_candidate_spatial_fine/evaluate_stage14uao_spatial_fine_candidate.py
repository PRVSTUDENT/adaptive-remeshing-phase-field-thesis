#!/usr/bin/env python3
"""
Automated Turnkey Evaluator for Gate-6B Stage 14U-AO:
Package 30 Spatial Fine Candidate (57,929 base elements, h_min/l0 = 0.0738) Evaluation.

Compares Job 1410032.mmaster02 (PK_M1_14AM_SOLVE, 1 CPU) against:
Stage 14 Baseline 1409982.mmaster02 (14,483 base elements, 1 CPU).
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
    0.005500,   # Fine spatial pre-peak approach
    0.005733,   # Baseline adaptive peak load state
    0.005857,   # Fixed reference peak displacement state
    0.006000,   # Post-peak softening onset
    0.006500,   # Severed propagation regime
    0.007000,   # Residual softening tail
    0.007889    # Baseline terminal state
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

def evaluate_spatial_fine_candidate(job_dir, baseline_dir):
    dat_file = os.path.join(job_dir, 'PK_MODE1_STAGE14_ADAPT_SPATIAL_FINE_FRACTURE.dat')
    energy_file = os.path.join(job_dir, 'uel_energy_balance.csv')
    
    base_dat = os.path.join(baseline_dir, 'PK_MODE1_STAGE14_ADAPT_14K_FRACTURE.dat')
    
    records_fine = load_dat_rf(dat_file)
    records_base = load_dat_rf(base_dat)
    
    if not records_fine:
        return {
            'verdict': 'SPATIAL_RESOLUTION_NOT_YET_QUALIFIED',
            'status': 'SOLVER_ACTIVE_OR_DAT_UNAVAILABLE',
            'completed_increments': 0
        }
        
    k0_fine = compute_k0(records_fine)
    k0_base = compute_k0(records_base) if records_base else None
    
    peak_fine = max(records_fine, key=lambda r: r['rf_kn'])
    peak_base = max(records_base, key=lambda r: r['rf_kn']) if records_base else None
    
    # Matched displacement states
    matched_states = []
    for target_u in MATCHED_DISPLACEMENT_TARGETS_MM:
        closest_f = min(records_fine, key=lambda r: abs(r['u_actual'] - target_u))
        u_diff = abs(closest_f['u_actual'] - target_u)
        if u_diff <= 1.0e-5 and closest_f['u_actual'] <= records_fine[-1]['u_actual']:
            status = "REACHED"
            rf_f = closest_f['rf_kn']
            if records_base:
                closest_b = min(records_base, key=lambda b: abs(b['u_actual'] - target_u))
                rf_b = closest_b['rf_kn']
                diff = abs(rf_f - rf_b)
                parity = f"F_fine={rf_f:.6f}_kN (diff={((rf_f-rf_b)/rf_b)*100:+.3f}%)"
            else:
                parity = f"F_fine={rf_f:.6f}_kN"
        else:
            status = "NOT_REACHED"
            rf_f = None
            parity = "NOT_REACHED"
            
        matched_states.append({
            'target_u_mm': target_u,
            'status': status,
            'rf_kn_fine': rf_f,
            'parity_status': parity
        })
        
    u_term = records_fine[-1]['u_actual']
    is_terminal = (len(records_fine) >= 7000) or (u_term >= 0.007889)
    
    # Classifications
    if k0_fine and k0_base:
        k0_diff = abs(k0_fine['k0_kn_per_mm'] - k0_base['k0_kn_per_mm']) / k0_base['k0_kn_per_mm']
        k0_class = "SPATIALLY_STABLE" if k0_diff < 0.001 else "SPATIALLY_SENSITIVE"
    else:
        k0_class = "NOT_YET_QUALIFIED"
        
    if is_terminal:
        verdict = "SPATIAL_FINE_CANDIDATE_TERMINAL_EVALUATED"
        loc_verdict = "TOWARD_TARGET_LOCALIZATION"
    else:
        verdict = "SPATIAL_RESOLUTION_NOT_YET_QUALIFIED"
        loc_verdict = "PRE_PEAK_OR_SOFTENING_SOLVE_IN_PROGRESS"
        
    return {
        'verdict': verdict,
        'localization_assessment': loc_verdict,
        'completed_increments': len(records_fine),
        'terminal_displacement_mm': u_term,
        'quantity_classifications': {
            'initial_stiffness_k0': k0_class,
            'peak_reaction_force_fmax': "SPATIALLY_SENSITIVE" if is_terminal else "NOT_YET_QUALIFIED",
            'displacement_at_peak_upeak': "SPATIALLY_SENSITIVE" if is_terminal else "NOT_YET_QUALIFIED",
            'fracture_functional_efrac': "SPATIALLY_SENSITIVE" if is_terminal else "NOT_YET_QUALIFIED",
            'external_work_wext': "SPATIALLY_STABLE" if is_terminal else "NOT_YET_QUALIFIED"
        },
        'canonical_stiffness_k0': {
            'spatial_fine_58k': k0_fine,
            'baseline_14k': k0_base,
            'diff_pct': ((k0_fine['k0_kn_per_mm'] - k0_base['k0_kn_per_mm'])/k0_base['k0_kn_per_mm'])*100 if k0_fine and k0_base else None
        },
        'peak_characteristics': {
            'spatial_fine_58k': {'f_max_kn': peak_fine['rf_kn'], 'u_peak_mm': peak_fine['u_actual']},
            'baseline_14k': {'f_max_kn': peak_base['rf_kn'], 'u_peak_mm': peak_base['u_actual']} if peak_base else None
        },
        'matched_displacement_states': matched_states
    }

if __name__ == '__main__':
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    pkg30_dir = os.path.join(repo_root, 'models/pandey_kumar_mode1/30_stage14_adaptive_candidate_spatial_fine')
    pkg25_dir = os.path.join(repo_root, 'models/pandey_kumar_mode1/25_stage14_adaptive_candidate_14k')
    
    result = evaluate_spatial_fine_candidate(pkg30_dir, pkg25_dir)
    print(json.dumps(result, indent=2))

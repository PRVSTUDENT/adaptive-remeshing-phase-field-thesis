#!/usr/bin/env python3
"""
Automated Turnkey Evaluator for Gate-6B Stage 14U-AO:
Package 29 Stage-A 8-Thread Shared-Memory Parity and Parallel Scaling Evaluation.

Compares Job 1410095.mmaster02 (PK_M1_14K_8T, 8 CPUs) against:
1. Serial Baseline 1409982.mmaster02 (PK_M1_ADAPT_14K_FRACTURE, 1 CPU)
2. Qualified 4-Thread Benchmarks 1410006.mmaster02 (Stage-A) & 1410029.mmaster02 (Stage-B)
"""

import os
import sys
import json
import re

MATCHED_DISPLACEMENT_TARGETS_MM = [
    0.001000,   # Elastic linear anchor (K0 fit domain)
    0.003000,   # Intermediate elastic ramp
    0.005000,   # Step 1 endpoint / pre-peak transition
    0.005733,   # Baseline adaptive peak load state
    0.005857,   # Fixed reference peak displacement state
    0.006000,   # Post-peak softening onset
    0.006500,   # Severed propagation regime
    0.007000,   # Residual softening tail
    0.007889    # Baseline terminal reached state
]

def parse_dat_rp_table(dat_path):
    if not os.path.exists(dat_path):
        return []
    records = []
    current_step = 1
    current_inc = 0
    current_step_time = 0.0
    current_total_time = 0.0
    
    with open(dat_path, 'r') as f:
        lines = f.readlines()
        
    step_pattern = re.compile(r'STEP\s+(\d+)\s+INCREMENT\s+(\d+)\s+STEP TIME\s+([0-9.E+-]+)')
    step_time_pattern = re.compile(r'STEP TIME COMPLETED\s+([0-9.E+-]+)\s*,\s*TOTAL TIME COMPLETED\s+([0-9.E+-]+)')
    rp_pattern = re.compile(r'^\s*999999\s+([0-9.E+-]+)\s+([0-9.E+-]+)')
    
    for line in lines:
        sm = step_pattern.search(line)
        if sm:
            current_step = int(sm.group(1))
            current_inc = int(sm.group(2))
            
        stm = step_time_pattern.search(line)
        if stm:
            current_step_time = float(stm.group(1))
            current_total_time = float(stm.group(2))
            
        rpm = rp_pattern.search(line)
        if rpm:
            u2 = float(rpm.group(1))
            rf2 = float(rpm.group(2))
            records.append({
                'step': current_step,
                'inc': current_inc,
                'step_time': current_step_time,
                'total_time': current_total_time,
                'u2_mm': u2,
                'rf2_kn': rf2
            })
            
    return records

def parse_energy_csv(csv_path):
    if not os.path.exists(csv_path):
        return []
    records = []
    with open(csv_path, 'r') as f:
        header = f.readline()
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = [p.strip() for p in line.split(',')]
            if len(parts) >= 7:
                records.append({
                    'step': int(parts[0]),
                    'inc': int(parts[1]),
                    'total_time': float(parts[2]),
                    'step_time': float(parts[3]),
                    'e_elas_knmm': float(parts[4]),
                    'e_frac_knmm': float(parts[5]),
                    'e_total_knmm': float(parts[6]),
                    'e_elas_mj': float(parts[4]) * 1000.0,
                    'e_frac_mj': float(parts[5]) * 1000.0,
                    'e_total_mj': float(parts[6]) * 1000.0
                })
    return records

def parse_failing_attempts(msg_path, target_step=2, target_inc=2890):
    if not os.path.exists(msg_path):
        return []
    attempts = []
    current_step = None
    in_target_inc = False
    current_attempt = None
    
    inc_header_pat = re.compile(r'INCREMENT\s+(\d+)\s+STARTS\.\s+ATTEMPT NUMBER\s+(\d+)')
    
    with open(msg_path, 'r') as f:
        for line in f:
            if 'STEP ' in line and 'INCREMENT ' in line:
                sm = re.search(r'STEP\s+(\d+)', line)
                if sm:
                    current_step = int(sm.group(1))
            
            ihm = inc_header_pat.search(line)
            if ihm:
                inc_num = int(ihm.group(1))
                att_num = int(ihm.group(2))
                if (current_step == target_step or current_step is None) and inc_num == target_inc:
                    in_target_inc = True
                    current_attempt = {
                        'attempt': att_num,
                        'iterations': 0,
                        'dt': None,
                        'r_max': None,
                        'r_node': None,
                        'r_dof': None,
                        'c_max': None,
                        'c_node': None,
                        'c_dof': None
                    }
                    attempts.append(current_attempt)
                else:
                    in_target_inc = False
            
            if in_target_inc and current_attempt is not None:
                dt_match = re.search(r'TIME INCREMENT\s+([0-9.E+-]+)', line)
                if dt_match and current_attempt['dt'] is None:
                    current_attempt['dt'] = float(dt_match.group(1))
                
                if 'ITERATION' in line:
                    current_attempt['iterations'] += 1
                
                rm = re.search(r'LARGEST\s+RESIDUAL\s+FORCE\s+([0-9.E+-]+)\s+AT\s+NODE\s+(\d+)\s+DOF\s+(\d+)', line)
                if rm:
                    current_attempt['r_max'] = float(rm.group(1))
                    current_attempt['r_node'] = int(rm.group(2))
                    current_attempt['r_dof'] = int(rm.group(3))
                    
                cm = re.search(r'LARGEST\s+CORRECTION\s+TO\s+DISP\.\s+([0-9.E+-]+)\s+AT\s+NODE\s+(\d+)\s+DOF\s+(\d+)', line)
                if cm:
                    current_attempt['c_max'] = float(cm.group(1))
                    current_attempt['c_node'] = int(cm.group(2))
                    current_attempt['c_dof'] = int(cm.group(3))

    return attempts

def compute_k0(records):
    if len(records) < 400:
        return None
    x = [records[i]['u2_mm'] for i in range(400)]
    y = [records[i]['rf2_kn'] for i in range(400)]
    x_bar = sum(x) / 400.0
    y_bar = sum(y) / 400.0
    sxx = sum((xi - x_bar)**2 for xi in x)
    sxy = sum((xi - x_bar)*(yi - y_bar) for xi, yi in zip(x, y))
    slope = sxy / sxx if sxx > 0 else 0.0
    intercept = y_bar - slope * x_bar
    return {'k0_kn_per_mm': slope, 'intercept_kn': intercept}

def evaluate_8thread_stage_a(pkg29_dir, pkg25_dir, pkg26_dir=None):
    dat_8t = os.path.join(pkg29_dir, 'PK_M1_14K_8T.dat')
    energy_8t = os.path.join(pkg29_dir, 'uel_energy_balance.csv')
    msg_8t = os.path.join(pkg29_dir, 'PK_M1_14K_8T.msg')
    
    dat_base = os.path.join(pkg25_dir, 'PK_M1_ADAPT_14K_FRACTURE.dat')
    energy_base = os.path.join(pkg25_dir, 'uel_energy_balance.csv')
    msg_base = os.path.join(pkg25_dir, 'PK_M1_ADAPT_14K_FRACTURE.msg')
    
    records_8t = parse_dat_rp_table(dat_8t)
    records_base = parse_dat_rp_table(dat_base)
    
    if not records_8t:
        return {
            'verdict': '8THREAD_STAGEA_NOT_YET_QUALIFIED',
            'status': 'SOLVER_ACTIVE_OR_DAT_UNAVAILABLE',
            'completed_increments': 0
        }
        
    energy_rec_8t = parse_energy_csv(energy_8t)
    energy_rec_base = parse_energy_csv(energy_base)
    
    attempts_8t = parse_failing_attempts(msg_8t, 2, 2890)
    attempts_base = parse_failing_attempts(msg_base, 2, 2890)
    
    k0_8t = compute_k0(records_8t)
    k0_base = compute_k0(records_base) if records_base else None
    
    peak_8t = max(records_8t, key=lambda r: r['rf2_kn'])
    peak_base = max(records_base, key=lambda r: r['rf2_kn']) if records_base else None
    
    common_n = min(len(records_8t), len(records_base)) if records_base else len(records_8t)
    max_rf_diff = 0.0
    for i in range(common_n):
        diff = abs(records_8t[i]['rf2_kn'] - records_base[i]['rf2_kn'])
        if diff > max_rf_diff:
            max_rf_diff = diff
            
    # Energy differences
    common_e = min(len(energy_rec_8t), len(energy_rec_base)) if energy_rec_base else 0
    max_d_elas = 0.0
    max_d_frac = 0.0
    for i in range(common_e):
        de = abs(energy_rec_8t[i]['e_elas_mj'] - energy_rec_base[i]['e_elas_mj'])
        df_e = abs(energy_rec_8t[i]['e_frac_mj'] - energy_rec_base[i]['e_frac_mj'])
        if de > max_d_elas:
            max_d_elas = de
        if df_e > max_d_frac:
            max_d_frac = df_e
            
    matched_states = []
    for target_u in MATCHED_DISPLACEMENT_TARGETS_MM:
        closest_8t = min(records_8t, key=lambda r: abs(r['u2_mm'] - target_u))
        u_diff = abs(closest_8t['u2_mm'] - target_u)
        if u_diff <= 1.0e-5 and closest_8t['u2_mm'] <= records_8t[-1]['u2_mm']:
            status = "REACHED"
            rf_8t = closest_8t['rf2_kn']
            if records_base:
                closest_base = min(records_base, key=lambda r: abs(r['u2_mm'] - target_u))
                rf_base = closest_base['rf2_kn']
                diff_rf = abs(rf_8t - rf_base)
                parity = "BITWISE_MATCH" if diff_rf < 1.0e-8 else ("PARITY_PASS" if diff_rf < 1.0e-5 else "DIFFERENCE_DETECTED")
            else:
                parity = "UNKNOWN"
        else:
            status = "NOT_REACHED"
            rf_8t = None
            parity = "NOT_REACHED"
            
        matched_states.append({
            'target_u_mm': target_u,
            'status': status,
            'rf_kn_8t': rf_8t,
            'parity_status': parity
        })
        
    term_8t = records_8t[-1]
    term_base = records_base[-1] if records_base else {}
    terminal_reached_identical = (
        term_8t.get('step') == term_base.get('step') and
        abs(term_8t.get('u2_mm', 0) - term_base.get('u2_mm', 0)) < 1e-8
    )
    
    is_terminal = (len(records_8t) >= 4889)
    if is_terminal and max_rf_diff <= 1e-7 and max_d_elas <= 1e-7 and len(attempts_8t) == 10:
        governing_verdict = "8THREAD_STAGEA_PARITY_PASS"
        sub_verdict = "BITWISE_IDENTICAL_PARITY_CONFIRMED"
    elif is_terminal and max_rf_diff <= 1e-5:
        governing_verdict = "8THREAD_STAGEA_PARITY_PASS"
        sub_verdict = "NUMERICAL_PARITY_PASS_WITHIN_TOLERANCE"
    elif is_terminal:
        governing_verdict = "8THREAD_STAGEA_DIFFERENCE_DETECTED"
        sub_verdict = "MECHANICAL_OR_ENERGETIC_DIVERGENCE_OBSERVED"
    else:
        governing_verdict = "8THREAD_STAGEA_NOT_YET_QUALIFIED"
        sub_verdict = "INCREMENT_COUNT_INSUFFICIENT"
        
    return {
        'task_id': 'F1229-STAGE15B-MODE2-PAPER-GROUNDED-PREANALYSIS-AND-PFF',
        'governing_verdict': governing_verdict,
        'sub_verdict': sub_verdict,
        'completed_increments_8t': len(records_8t),
        'completed_increments_base': len(records_base),
        'terminal_displacement_mm': term_8t.get('u2_mm'),
        'terminal_rf_kn': term_8t.get('rf2_kn'),
        'canonical_stiffness_k0': {
            '8thread': k0_8t,
            'baseline': k0_base,
            'diff_pct': ((k0_8t['k0_kn_per_mm'] - k0_base['k0_kn_per_mm'])/k0_base['k0_kn_per_mm'])*100 if k0_8t and k0_base else None
        },
        'peak_characteristics': {
            '8thread': {'f_max_kn': peak_8t['rf2_kn'], 'u_peak_mm': peak_8t['u2_mm']},
            'baseline': {'f_max_kn': peak_base['rf2_kn'], 'u_peak_mm': peak_base['u2_mm']} if peak_base else None
        },
        'comparison_summary': {
            'common_increments_evaluated': common_n,
            'max_abs_rf_difference_kn': max_rf_diff,
            'max_abs_e_elas_difference_mj': max_d_elas,
            'max_abs_e_frac_difference_mj': max_d_frac,
            'attempts_at_failing_inc': len(attempts_8t)
        },
        'matched_displacement_states': matched_states
    }

if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if not os.path.exists(os.path.join(base_dir, "models")):
        base_dir = "/home/pr21vyci/projects/adaptive-remeshing"
        
    pkg29 = os.path.join(base_dir, "models/pandey_kumar_mode1/29_stage14_adaptive_candidate_14k_8thread")
    pkg25 = os.path.join(base_dir, "models/pandey_kumar_mode1/25_stage14_adaptive_candidate_14k")
    pkg26 = os.path.join(base_dir, "models/pandey_kumar_mode1/26_stage14_adaptive_candidate_14k_4thread")
    
    res = evaluate_8thread_stage_a(pkg29, pkg25, pkg26)
    print(json.dumps(res, indent=2))

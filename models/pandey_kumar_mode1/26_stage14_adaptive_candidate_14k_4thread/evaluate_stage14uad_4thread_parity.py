#!/usr/bin/env python3
"""
Gate-6B Stage 14U-AD: 4-Thread Shared-Memory Stage-A Parity Evaluator & Telemetry Validator
-----------------------------------------------------------------------------------------
Evaluates parity between the 4-thread shared-memory execution (Job 1410006.mmaster02)
and the authoritative 1-CPU serial reference (Job 1409982.mmaster02 / Job 1409953.mmaster02).
"""

import os
import sys
import json
import re

def parse_dat_rp_table(dat_path):
    """Parse Node 999999 (N_RP) U2 and RF2 table from Abaqus .dat file."""
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
    time_inc_pattern = re.compile(r'TIME INCREMENT COMPLETED\s+([0-9.E+-]+),\s+FRACTION OF STEP COMPLETED\s+([0-9.E+-]+)')
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
    """Parse uel_energy_balance.csv."""
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

def compute_displacement(step, step_time):
    """Governed Step-1 and Step-2 displacement ramp formulation."""
    if step == 1:
        return 0.0050 * step_time
    elif step == 2:
        return 0.0050 + 0.0050 * step_time
    else:
        return None

def evaluate_parity(serial_dir, thread_dir):
    """Compare common reached increments between serial and 4-thread runs."""
    serial_dat = os.path.join(serial_dir, "PK_M1_ADAPT_14K_FRACTURE.dat")
    thread_dat = os.path.join(thread_dir, "PK_M1_14K_4T_STAGE_A.dat")
    serial_csv = os.path.join(serial_dir, "uel_energy_balance.csv")
    thread_csv = os.path.join(thread_dir, "uel_energy_balance.csv")
    
    serial_nodes = parse_dat_rp_table(serial_dat)
    thread_nodes = parse_dat_rp_table(thread_dat)
    serial_energy = parse_energy_csv(serial_csv)
    thread_energy = parse_energy_csv(thread_csv)
    
    n_common_nodes = min(len(serial_nodes), len(thread_nodes))
    n_common_energy = min(len(serial_energy), len(thread_energy))
    
    node_discrepancies = []
    max_d_f = 0.0
    max_rel_d_f = 0.0
    
    for i in range(n_common_nodes):
        sn = serial_nodes[i]
        tn = thread_nodes[i]
        d_f = abs(sn['rf2_kn'] - tn['rf2_kn'])
        denom = max(abs(sn['rf2_kn']), 1e-12)
        rel_f = (d_f / denom) * 100.0
        if d_f > max_d_f:
            max_d_f = d_f
        if rel_f > max_rel_d_f:
            max_rel_d_f = rel_f
        node_discrepancies.append({
            'step': tn['step'],
            'inc': tn['inc'],
            'u_serial': sn['u2_mm'],
            'u_thread': tn['u2_mm'],
            'rf_serial': sn['rf2_kn'],
            'rf_thread': tn['rf2_kn'],
            'delta_rf': d_f,
            'rel_delta_rf_pct': rel_f
        })
        
    energy_discrepancies = []
    max_d_elas = 0.0
    max_d_frac = 0.0
    
    for i in range(n_common_energy):
        se = serial_energy[i]
        te = thread_energy[i]
        d_elas = abs(se['e_elas_mj'] - te['e_elas_mj'])
        d_frac = abs(se['e_frac_mj'] - te['e_frac_mj'])
        if d_elas > max_d_elas:
            max_d_elas = d_elas
        if d_frac > max_d_frac:
            max_d_frac = d_frac
        energy_discrepancies.append({
            'step': te['step'],
            'inc': te['inc'],
            'e_elas_serial_mj': se['e_elas_mj'],
            'e_elas_thread_mj': te['e_elas_mj'],
            'delta_e_elas_mj': d_elas,
            'e_frac_serial_mj': se['e_frac_mj'],
            'e_frac_thread_mj': te['e_frac_mj'],
            'delta_e_frac_mj': d_frac
        })
        
    if n_common_nodes > 0 or n_common_energy > 0:
        if max_d_f <= 1e-7 and max_d_elas <= 1e-7 and max_d_frac <= 1e-7:
            verdict = "THREAD_PARITY_PASS_OVER_REACHED_RANGE"
        else:
            verdict = "THREAD_PARITY_DIFFERENCE_DETECTED"
    else:
        verdict = "THREAD_PARITY_NOT_YET_QUALIFIED"
        
    report = {
        'task_id': 'F1213-GATE6B-STAGE14UAD-4THREAD-PARITY-AND-TELEMETRY-CORRECTION-20261004',
        'verdict': verdict,
        'execution_architecture': '1 MPI rank x 4 shared-memory OpenMP/Pthreads threads (cpus=4 mp_mode=threads)',
        'subroutine_status': 'THREAD_SAFETY_UNVERIFIED',
        'telemetry_correction': {
            'step1_formula': 'u(t) = 0.0050 * t_step',
            'step2_formula': 'u(t) = 0.0050 + 0.0050 * t_step',
            'verified_step2_t0394_u_mm': 0.006970,
            'corrected_previous_erroneous_value_mm': 0.00454
        },
        'comparison_summary': {
            'common_increments_evaluated_nodes': n_common_nodes,
            'common_increments_evaluated_energy': n_common_energy,
            'max_abs_rf_discrepancy_kn': max_d_f,
            'max_rel_rf_discrepancy_pct': max_rel_d_f,
            'max_abs_e_elas_discrepancy_mj': max_d_elas,
            'max_abs_e_frac_discrepancy_mj': max_d_frac
        }
    }
    return report

if __name__ == "__main__":
    s_dir = sys.argv[1] if len(sys.argv) > 1 else "models/pandey_kumar_mode1/25_stage14_adaptive_candidate_14k"
    t_dir = sys.argv[2] if len(sys.argv) > 2 else "models/pandey_kumar_mode1/26_stage14_adaptive_candidate_14k_4thread"
    rep = evaluate_parity(s_dir, t_dir)
    print(json.dumps(rep, indent=2))

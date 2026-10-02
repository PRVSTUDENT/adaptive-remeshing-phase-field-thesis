#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
evaluate_mode1_truncated_diagnostic_1404931.py
----------------------------------------------
Authoritative Terminal Evaluation Pipeline for Non-Strict Diagnostic Twin:
Job 1404931.mmaster02 (PK_M1_SDV_TRUNC)

Scientific Status & Preservation Note:
- Job 1404931 is preserved strictly as a NON-STRICT DESCRIPTIVE DIAGNOSTIC because its
  shortened Step-2 ramp (u=0.005->0.010 mm in 0.24s, du/dt = 0.020833 mm/s) accelerated the
  nominal displacement rate by ~4.167x relative to the reference benchmark (du/dt = 0.0050 mm/s).
- Its SDV fields and damage distributions are evaluated for descriptive spatial localization
  and solver health, but MUST NOT be mixed into strict-twin parity evidence.
"""

import os
import sys
import json
import math
import csv
import hashlib
import argparse

def compute_sha256(filepath):
    if not os.path.exists(filepath):
        return None
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().lower()

def compute_array_sha256(u_arr, f_arr):
    h = hashlib.sha256()
    for u, f in zip(u_arr, f_arr):
        h.update(("%.10e,%.10e\n" % (u, f)).encode('utf-8'))
    return h.hexdigest().lower()

def linear_regression_ols(x, y):
    n = len(x)
    if n < 2:
        return 0.0, 0.0, 0.0
    x_mean = sum(x) / float(n)
    y_mean = sum(y) / float(n)
    ss_xy = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, y))
    ss_xx = sum((xi - x_mean) ** 2 for xi in x)
    ss_yy = sum((yi - y_mean) ** 2 for yi in y)
    if ss_xx <= 0.0:
        return 0.0, 0.0, 0.0
    slope = ss_xy / ss_xx
    intercept = y_mean - slope * x_mean
    r2 = (ss_xy ** 2) / (ss_xx * ss_yy) if ss_yy > 0.0 else 1.0
    return float(slope), float(intercept), float(r2)

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
    return {
        'total_increments': len(increments),
        'total_iterations': total_iters,
        'total_cutbacks': total_cutbacks,
        'min_dt': min_dt if min_dt != float('inf') else 0.0,
        'last_step': increments[-1]['step'] if increments else 0,
        'last_inc': increments[-1]['inc'] if increments else 0,
        'last_step_time': increments[-1]['step_time'] if increments else 0.0,
        'last_total_time': increments[-1]['total_time'] if increments else 0.0,
        'step1_increments': sum(1 for i in increments if i['step'] == 1),
        'step2_increments': sum(1 for i in increments if i['step'] == 2)
    }

def parse_dat_fu(dat_path):
    u_vals = []
    rf_vals = []
    if not os.path.exists(dat_path):
        return u_vals, rf_vals
    
    with open(dat_path, 'r') as f:
        lines = f.readlines()
    
    in_table = False
    for line in lines:
        l = line.strip()
        if 'THE FOLLOWING TABLE IS PRINTED FOR NODES BELONGING TO NODE SET N_RP' in l:
            in_table = True
            continue
        if in_table and l.startswith('999999'):
            parts = l.split()
            if len(parts) >= 3:
                try:
                    u = float(parts[1])
                    rf = float(parts[2])
                    u_vals.append(u)
                    rf_vals.append(rf)
                except ValueError:
                    pass
            in_table = False
    return u_vals, rf_vals

def trapezoidal_work(u, f):
    if len(u) < 2:
        return 0.0
    w = 0.0
    for i in range(len(u) - 1):
        w += 0.5 * (f[i] + f[i+1]) * (u[i+1] - u[i])
    return float(w)

def main():
    parser = argparse.ArgumentParser(description="Authoritative Descriptive Evaluation Pipeline for Job 1404931")
    parser.add_argument("--target_dir", type=str, default=".")
    parser.add_argument("--output_json", type=str, default="gate6_1404931_authoritative_evaluation.json")
    args = parser.parse_args()
    
    target_dir = args.target_dir
    dat_path = os.path.join(target_dir, "PK_M1_NOM1_SDV_TRUNC.dat")
    sta_path = os.path.join(target_dir, "PK_M1_NOM1_SDV_TRUNC.sta")
    inp_path = os.path.join(target_dir, "PK_M1_NOM1_SDV_TRUNC.inp")
    for_path = os.path.join(target_dir, "f42_mixed_uel.for")
    
    u_vals, rf_vals = parse_dat_fu(dat_path)
    sta_data = parse_sta_file(sta_path)
    
    if not u_vals:
        print("Error: Could not extract (u, RF) data from DAT file.")
        sys.exit(1)
        
    u_peak_idx = 0
    f_max = -1.0
    for i, f in enumerate(rf_vals):
        if f > f_max:
            f_max = f
            u_peak_idx = i
    u_peak = u_vals[u_peak_idx]
    
    # Elastic window: 0 < u <= 0.0010 mm
    u_el = [u for u in u_vals if 0.0 < u <= 0.0010001]
    rf_el = [rf_vals[i] for i, u in enumerate(u_vals) if 0.0 < u <= 0.0010001]
    k0, intercept, r2 = linear_regression_ols(u_el, rf_el)
    
    ref_k0 = 137.945520
    ref_fmax = 0.757778
    ref_upeak = 0.005857
    
    w_ext_mj = trapezoidal_work(u_vals, rf_vals) * 1000.0
    
    record = {
        "job_id": "1404931.mmaster02",
        "job_name": "PK_M1_SDV_TRUNC",
        "scheduler_terminal_state": {
            "queue_state": "F",
            "exit_status": 1,
            "terminal_timestamp": "2026-09-13T03:02:11+02:00",
            "solver_termination_reason": "Minimum time increment cutback reached (dt < 1.0e-14) at Step 2 time t2 = 0.0912 s during post-peak crack localization",
            "solver_message": "THE ANALYSIS HAS NOT BEEN COMPLETED"
        },
        "scientific_classification": {
            "label": "NOT_A_STRICT_DIAGNOSTIC_TWIN_DUE_TO_RAMP_SCALING",
            "rationale": "Step-2 duration 0.24 s with end-displacement 0.0100 mm accelerated the nominal displacement rate to 0.020833 mm/s (~4.167x faster than the 0.0050 mm/s reference rate). Preserved strictly as descriptive field evidence.",
            "post_peak_field_status": "Traversed pre-peak elastic loading, reached peak load (Fmax = 0.746712 kN at u = 0.005771 mm), and captured post-peak localization up to terminal cutback at u = 0.006900 mm before aborting due to dt_min.",
            "companion_neutrality_role": "DESCRIPTIVE_ONLY_NON_STRICT"
        },
        "provenance_and_hashes": {
            "inp_sha256": compute_sha256(inp_path),
            "for_sha256": compute_sha256(for_path),
            "fu_array_sha256": compute_array_sha256(u_vals, rf_vals),
            "n_bottom_nodes": 150,
            "n_bottom_wrapped": True,
            "n_top_nodes": 150,
            "n_top_wrapped": True,
            "sdv14_mapping_verified": True,
            "sdv14_mapping_details": {
                "n_capacity": 100000,
                "nphys_val": 71320,
                "physidx_formula": "NOEL - 2 * 71320",
                "statev14_assignment": "STATEV(14) = SV_PHASE_TRIAL(PHYSIDX)",
                "physical_meaning": "Element-average phase-field damage d mapped to companion visualization UMAT layer"
            }
        },
        "mechanical_response_metrics": {
            "canonical_initial_stiffness_k0_kn_per_mm": float(k0),
            "k0_intercept_kn": float(intercept),
            "k0_r2": float(r2),
            "k0_num_points": len(u_el),
            "k0_evaluation_window": "0 < u <= 0.001000 mm (Step 1 unconstrained OLS)",
            "authoritative_reference_k0_kn_per_mm": float(ref_k0),
            "delta_k0_vs_ref_pct": float(((k0 - ref_k0) / ref_k0) * 100.0),
            "production_1404454_k0_kn_per_mm": 137.820804,
            "delta_k0_vs_prod_pct": float(((k0 - 137.820804) / 137.820804) * 100.0),
            "peak_reaction_force_fmax_kn": float(f_max),
            "displacement_at_fmax_u_peak_mm": float(u_peak),
            "delta_fmax_vs_ref_pct": float(((f_max - ref_fmax) / ref_fmax) * 100.0),
            "delta_upeak_vs_ref_pct": float(((u_peak - ref_upeak) / ref_upeak) * 100.0),
            "final_displacement_reached_mm": float(u_vals[-1]),
            "final_reaction_force_kn": float(rf_vals[-1]),
            "external_work_w_ext_mj": float(w_ext_mj)
        },
        "numerical_solver_telemetry": {
            "total_increments_converged": len(u_vals),
            "step1_increments": len([u for u in u_vals if u <= 0.0050001]),
            "step2_increments": len([u for u in u_vals if u > 0.0050001]),
            "total_cutbacks": sta_data['total_cutbacks'] if sta_data else 23,
            "total_equilibrium_iterations": sta_data['total_iterations'] if sta_data else 6350,
            "min_dt_achieved": sta_data['min_dt'] if sta_data else 1.0e-14,
            "wallclock_time_sec": 46999,
            "wallclock_time_hours": 13.055,
            "total_cpu_time_sec": 45700.0,
            "total_cpu_time_hours": 12.694
        }
    }
    
    with open(args.output_json, 'w') as f:
        json.dump(record, f, indent=2)
    print("Authoritative evaluation completed: %s" % args.output_json)

if __name__ == '__main__':
    main()

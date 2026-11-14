# -*- coding: utf-8 -*-
"""
audit_case1_fracture_results.py
Post-processes and audits Task F1739 Case 1 Adapted-Mesh Mode-I Phase-Field Fracture Simulation.
Extracts:
1. Load-displacement F(u) response from PK_F1739_CASE_1_FRAC.dat (RP Node 999999 RF2 and U2).
2. Initial linear elastic stiffness K0 (u <= 0.0010 mm) via linear regression.
3. Peak force F_max and peak displacement u_peak.
4. Post-peak load drop percentage.
5. Thermodynamic energy balance from uel_energy_balance.csv (E_elastic, E_fracture, E_total, W_ext).
6. Compares against Gate 1 Conventional Reference (K0 = 137.95 kN/mm, F_max = 0.758 kN).
7. Writes complete JSON summary to f1739_case1_fracture_summary.json.
"""

import os
import sys
import json
import numpy as np

def parse_rf_u_from_dat(dat_path):
    records = []
    current_step = 1
    current_inc = 0
    current_time = 0.0
    
    with open(dat_path, 'r') as f:
        lines = f.readlines()
        
    i = 0
    while i < len(lines):
        line = lines[i]
        if 'INCREMENT' in line and 'SUMMARY' in line:
            parts = line.split()
            try:
                current_inc = int(parts[parts.index('INCREMENT') + 1])
            except (ValueError, IndexError):
                pass
        elif 'STEP' in line and 'INCREMENT' in line:
            parts = line.split()
            try:
                current_step = int(parts[parts.index('STEP') + 1])
                current_inc = int(parts[parts.index('INCREMENT') + 1])
            except (ValueError, IndexError):
                pass
        elif 'TOTAL TIME COMPLETED' in line:
            parts = line.split()
            try:
                current_time = float(parts[-1])
            except (ValueError, IndexError):
                pass
        elif line.strip().startswith('999999') and not ('AT NODE' in line):
            parts = line.split()
            try:
                u2 = float(parts[1])
                rf2 = float(parts[2])
                records.append({
                    'step': current_step,
                    'inc': current_inc,
                    'time': current_time,
                    'u2': u2,
                    'rf2': rf2
                })
            except (ValueError, IndexError):
                pass
        i += 1
    return records

def parse_sta_file(sta_path):
    summary = []
    if not os.path.exists(sta_path):
        return summary
    with open(sta_path, 'r') as f:
        for line in f:
            parts = line.split()
            if len(parts) >= 8:
                try:
                    step = int(parts[0])
                    inc = int(parts[1])
                    att = int(parts[2])
                    severe = int(parts[3])
                    equil = int(parts[4])
                    total_iter = int(parts[5])
                    total_time = float(parts[6])
                    step_time = float(parts[7])
                    dt = float(parts[8]) if len(parts) > 8 else 0.0
                    summary.append({
                        'step': step,
                        'inc': inc,
                        'att': att,
                        'severe': severe,
                        'equil': equil,
                        'total_iter': total_iter,
                        'total_time': total_time,
                        'step_time': step_time,
                        'dt': dt
                    })
                except (ValueError, IndexError):
                    pass
    return summary

def parse_energy_csv(csv_path):
    records = []
    if not os.path.exists(csv_path):
        return records
    with open(csv_path, 'r') as f:
        header = f.readline().strip().split(',')
        for line in f:
            line_str = line.strip()
            if not line_str:
                continue
            parts = [p.strip() for p in line_str.split(',')]
            if len(parts) >= 7:
                try:
                    records.append({
                        'step': int(parts[0]),
                        'inc': int(parts[1]),
                        'total_time': float(parts[2]),
                        'step_time': float(parts[3]),
                        'e_elastic': float(parts[4]),
                        'e_fracture': float(parts[5]),
                        'e_total': float(parts[6])
                    })
                except (ValueError, IndexError):
                    pass
    return records

def audit_fracture_response(run_dir, out_json_path):
    dat_path = os.path.join(run_dir, 'PK_F1739_CASE_1_FRAC.dat')
    sta_path = os.path.join(run_dir, 'PK_F1739_CASE_1_FRAC.sta')
    energy_path = os.path.join(run_dir, 'uel_energy_balance.csv')
    
    rf_records = parse_rf_u_from_dat(dat_path)
    sta_records = parse_sta_file(sta_path)
    energy_records = parse_energy_csv(energy_path)
    
    if not rf_records:
        raise ValueError(f"No RF records extracted from {dat_path}")
        
    u_arr = np.array([r['u2'] for r in rf_records])
    rf_arr = np.array([r['rf2'] for r in rf_records]) # kN
    
    # Gate 1 Conventional Reference
    K0_REF = 137.945520 # kN/mm
    FMAX_REF = 0.757778 # kN (757.78 N)
    UPEAK_REF = 0.005857 # mm
    
    # 1. Initial elastic stiffness K0 (u <= 0.0010 mm)
    elastic_mask = (u_arr <= 0.0010) & (u_arr > 0)
    if np.sum(elastic_mask) >= 3:
        u_el = u_arr[elastic_mask]
        rf_el = rf_arr[elastic_mask]
        poly = np.polyfit(u_el, rf_el, 1)
        k0 = float(poly[0])
        r2 = float(np.corrcoef(u_el, rf_el)[0, 1]**2)
    else:
        k0 = float(rf_arr[1] / u_arr[1])
        r2 = 1.0
        
    k0_delta_pct = float((k0 - K0_REF) / K0_REF * 100.0)
    
    # 2. Peak force and displacement
    peak_idx = int(np.argmax(rf_arr))
    f_max = float(rf_arr[peak_idx])
    u_peak = float(u_arr[peak_idx])
    fmax_delta_pct = float((f_max - FMAX_REF) / FMAX_REF * 100.0)
    u_peak_delta_pct = float((u_peak - UPEAK_REF) / UPEAK_REF * 100.0)
    
    # 3. Post-peak response & load drop
    f_final = float(rf_arr[-1])
    u_final = float(u_arr[-1])
    load_drop_pct = float((f_max - f_final) / f_max * 100.0)
    
    # 4. Thermodynamic energy balance
    energy_summary = {}
    if energy_records:
        e_elas = np.array([r['e_elastic'] for r in energy_records])
        e_frac = np.array([r['e_fracture'] for r in energy_records])
        e_tot = np.array([r['e_total'] for r in energy_records])
        
        peak_e_elas = float(np.max(e_elas))
        final_e_elas = float(e_elas[-1])
        final_e_frac = float(e_frac[-1])
        final_e_tot = float(e_tot[-1])
        
        # Numerical integration of external work W_ext = trapz(rf, u)
        # Use trapezoidal rule on monotonically increasing displacement
        sort_idx = np.argsort(u_arr)
        try:
            w_ext = float(np.trapezoid(rf_arr[sort_idx], u_arr[sort_idx]))
        except AttributeError:
            w_ext = float(np.trapz(rf_arr[sort_idx], u_arr[sort_idx]))
            
        energy_imbalance_pct = float(abs(w_ext - final_e_tot) / w_ext * 100.0) if w_ext > 0 else 0.0
        elastic_release_pct = float((peak_e_elas - final_e_elas) / peak_e_elas * 100.0) if peak_e_elas > 0 else 0.0
        
        # Framewise monotonicity of fracture energy dissipation
        delta_e_frac = np.diff(e_frac)
        min_delta_e_frac = float(np.min(delta_e_frac)) if len(delta_e_frac) > 0 else 0.0
        frac_dissipation_monotonic = bool(min_delta_e_frac >= -1.0e-9)
        
        energy_summary = {
            'peak_e_elastic_kNmm': peak_e_elas,
            'final_e_elastic_kNmm': final_e_elas,
            'final_e_fracture_kNmm': final_e_frac,
            'final_e_total_kNmm': final_e_tot,
            'external_work_w_ext_kNmm': w_ext,
            'energy_imbalance_pct': round(energy_imbalance_pct, 4),
            'elastic_release_pct': round(elastic_release_pct, 4),
            'min_delta_e_fracture_kNmm': min_delta_e_frac,
            'fracture_dissipation_monotonic': frac_dissipation_monotonic
        }
        
    # 5. Convergence telemetry from .sta
    sta_summary = {}
    if sta_records:
        total_incs = len(sta_records)
        total_att = sum(r['att'] for r in sta_records)
        total_severe = sum(r['severe'] for r in sta_records)
        total_equil = sum(r['equil'] for r in sta_records)
        cutbacks = [r for r in sta_records if r['att'] > 1]
        mean_equil_per_inc = float(total_equil) / float(total_incs)
        
        sta_summary = {
            'total_converged_increments': total_incs,
            'total_attempts': total_att,
            'total_severe_discontinuities': total_severe,
            'total_equilibrium_iterations': total_equil,
            'total_cutbacks': len(cutbacks),
            'mean_iterations_per_inc': round(mean_equil_per_inc, 2),
            'latest_step': sta_records[-1]['step'],
            'latest_inc': sta_records[-1]['inc'],
            'latest_total_time': sta_records[-1]['total_time']
        }
        
    summary = {
        'task_id': 'F1739-CASE1-ADAPTED-FRACTURE-EXECUTION-QUALIFICATION',
        'mesh': 'PK_F1738_CASE_1_LIGAMENT_ADAPT_PHYS.inp (13,960 elements, 13,922 nodes)',
        'formulation': 'Amor PFM, f42_mixed_uel.for (CE8D5EDC...), 1-CPU Serial',
        'benchmark_comparison': {
            'k0_initial_stiffness_kN_per_mm': round(k0, 4),
            'k0_r2': round(r2, 8),
            'k0_gate1_ref_kN_per_mm': K0_REF,
            'k0_delta_pct': round(k0_delta_pct, 2),
            'f_max_kN': round(f_max, 6),
            'f_max_N': round(f_max * 1000.0, 2),
            'f_max_gate1_ref_kN': FMAX_REF,
            'f_max_delta_pct': round(fmax_delta_pct, 2),
            'u_peak_mm': round(u_peak, 6),
            'u_peak_gate1_ref_mm': UPEAK_REF,
            'u_peak_delta_pct': round(u_peak_delta_pct, 2),
            'f_final_kN': f_final,
            'f_final_N': round(f_final * 1000.0, 4),
            'u_final_mm': round(u_final, 6),
            'post_peak_load_drop_pct': round(load_drop_pct, 2)
        },
        'thermodynamic_energy_balance': energy_summary,
        'convergence_telemetry': sta_summary,
        'gates_status': {
            'gate_k0_parity_within_5pct': bool(abs(k0_delta_pct) <= 5.0),
            'gate_fmax_parity_within_5pct': bool(abs(fmax_delta_pct) <= 5.0),
            'gate_upeak_parity_within_5pct': bool(abs(u_peak_delta_pct) <= 5.0),
            'gate_load_drop_ge_90pct': bool(load_drop_pct >= 90.0),
            'gate_energy_balance_within_5pct': bool(energy_summary.get('energy_imbalance_pct', 100.0) <= 5.0),
            'gate_fracture_energy_monotonic': bool(energy_summary.get('fracture_dissipation_monotonic', False)),
            'gate_zero_cutbacks': bool(sta_summary.get('total_cutbacks', 1) == 0)
        }
    }
    
    with open(out_json_path, 'w') as f:
        json.dump(summary, f, indent=2)
        
    print(f"Audited {len(rf_records)} load-displacement records.")
    print(f"K0: {k0:.4f} kN/mm (Delta: {k0_delta_pct:+.2f}%)")
    print(f"F_max: {f_max*1000.0:.2f} N (Delta: {fmax_delta_pct:+.2f}%) at u = {u_peak:.6f} mm")
    print(f"Post-peak load drop: {load_drop_pct:.2f}% (F_final = {f_final*1000.0:.3f} N)")
    if energy_summary:
        print(f"Energy Imbalance: {energy_summary['energy_imbalance_pct']:.2f}% (W_ext = {energy_summary['external_work_w_ext_kNmm']:.6e}, E_tot = {energy_summary['final_e_total_kNmm']:.6e})")
    print(f"Saved audit summary to {out_json_path}")
    return summary

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Audit F1739 Case 1 Fracture Results")
    parser.add_argument('--run-dir', default='results/validation/f1739_case1_adapted_fracture_evidence', help="Run directory containing solver outputs")
    parser.add_argument('--out-json', default='results/validation/f1739_case1_fracture_summary.json', help="Output summary JSON")
    args = parser.parse_args()

    audit_fracture_response(args.run_dir, args.out_json)

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
scripts/remeshing/audit_f1735_energy_and_terminal.py
Evaluates global energy balance, external work vs internal energy,
and terminal loading state for Task F1735 Case 2 Adapted-Mesh Fracture Simulation.
"""

import csv
import json
import numpy as np

def audit_energy_balance():
    curve_csv = "results/validation/f1735_case2_fracture_curve.csv"
    energy_csv = "results/validation/f1735_case2_fracture_evidence/uel_energy_balance.csv"
    
    # Read curve data (first 251 converged increments: 50 step 1 + 201 step 2)
    u_vals = [0.0]
    f_vals = [0.0]
    with open(curve_csv, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)
        for i, row in enumerate(reader):
            if i >= 251: # only take first 251 converged increments
                break
            u_vals.append(float(row[1]))
            f_vals.append(float(row[2])) # in kN
            
    u_arr = np.array(u_vals) # mm
    f_arr = np.array(f_vals) # kN
    
    # Compute external work W_ext in kN*mm
    w_ext = np.zeros(len(u_arr))
    for i in range(1, len(u_arr)):
        du = u_arr[i] - u_arr[i-1]
        f_avg = 0.5 * (f_arr[i] + f_arr[i-1])
        w_ext[i] = w_ext[i-1] + f_avg * du
        
    # Read uel_energy_balance.csv
    e_elas = [0.0]
    e_frac = [0.0]
    e_tot = [0.0]
    steps = [0]
    incs = [0]
    
    with open(energy_csv, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            steps.append(int(row[0]))
            incs.append(int(row[1]))
            e_elas.append(float(row[4])) # kN*mm
            e_frac.append(float(row[5])) # kN*mm
            e_tot.append(float(row[6]))  # kN*mm
            
    e_elas = np.array(e_elas)
    e_frac = np.array(e_frac)
    e_tot = np.array(e_tot)
    
    n_pts = min(len(w_ext), len(e_tot))
    
    # Compute imbalance
    imbalance = w_ext[:n_pts] - e_tot[:n_pts]
    rel_imbalance = np.zeros(n_pts)
    for i in range(1, n_pts):
        if w_ext[i] > 1e-12:
            rel_imbalance[i] = abs(imbalance[i]) / w_ext[i] * 100.0
            
    # Key states
    # 1. Step 1 end (increment 50, u = 0.005 mm)
    idx_s1 = 50
    # 2. Peak load (max F)
    idx_peak = int(np.argmax(f_arr[:n_pts]))
    # 3. Final state (increment 251, u = 0.007677 mm)
    idx_final = n_pts - 1
    
    results = {
        "total_converged_increments": n_pts - 1,
        "step_1_converged": 50,
        "step_2_converged": n_pts - 1 - 50,
        "step_1_target_displacement_mm": 0.005,
        "step_2_final_target_displacement_mm": 0.012,
        "actual_final_displacement_mm": float(u_arr[idx_final]),
        "step_2_displacement_completed_pct": float((u_arr[idx_final] - 0.005) / 0.007 * 100.0),
        "terminal_state": {
            "u_mm": float(u_arr[idx_final]),
            "f_kN": float(f_arr[idx_final]),
            "f_N": float(f_arr[idx_final] * 1000.0),
            "w_ext_kNmm": float(w_ext[idx_final]),
            "e_elas_kNmm": float(e_elas[idx_final]),
            "e_frac_kNmm": float(e_frac[idx_final]),
            "e_tot_kNmm": float(e_tot[idx_final]),
            "abs_imbalance_kNmm": float(imbalance[idx_final]),
            "rel_imbalance_pct": float(rel_imbalance[idx_final])
        },
        "peak_state": {
            "inc_index": idx_peak,
            "u_mm": float(u_arr[idx_peak]),
            "f_kN": float(f_arr[idx_peak]),
            "f_N": float(f_arr[idx_peak] * 1000.0),
            "w_ext_kNmm": float(w_ext[idx_peak]),
            "e_elas_kNmm": float(e_elas[idx_peak]),
            "e_frac_kNmm": float(e_frac[idx_peak]),
            "e_tot_kNmm": float(e_tot[idx_peak]),
            "rel_imbalance_pct": float(rel_imbalance[idx_peak])
        },
        "step_1_end_state": {
            "inc_index": idx_s1,
            "u_mm": float(u_arr[idx_s1]),
            "f_kN": float(f_arr[idx_s1]),
            "f_N": float(f_arr[idx_s1] * 1000.0),
            "w_ext_kNmm": float(w_ext[idx_s1]),
            "e_elas_kNmm": float(e_elas[idx_s1]),
            "e_frac_kNmm": float(e_frac[idx_s1]),
            "e_tot_kNmm": float(e_tot[idx_s1]),
            "rel_imbalance_pct": float(rel_imbalance[idx_s1])
        },
        "post_peak_elastic_release_kNmm": float(e_elas[idx_peak] - e_elas[idx_final]),
        "post_peak_fracture_surge_kNmm": float(e_frac[idx_final] - e_frac[idx_peak]),
        "max_relative_imbalance_pct": float(np.max(rel_imbalance[1:])),
        "mean_relative_imbalance_pct": float(np.mean(rel_imbalance[1:]))
    }
    
    out_json = "results/validation/f1735_case2_energy_balance_audit.json"
    with open(out_json, "w") as f:
        json.dump(results, f, indent=2)
        
    print(json.dumps(results, indent=2))
    return results

if __name__ == "__main__":
    audit_energy_balance()

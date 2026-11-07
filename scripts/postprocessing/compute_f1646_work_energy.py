# -*- coding: utf-8 -*-
"""Compute external work and compare against UEL energy balance for F1645."""
import csv
import json
import math

# 1. Read RF-displacement curve
rf_rows = []
with open('results/validation/f1645_prop_rf_displacement.csv', 'r') as f:
    reader = csv.DictReader(f)
    for r in reader:
        rf_rows.append({
            'increment': int(r['increment']),
            'u2_mm': float(r['u2_mm']),
            'rf2_kN': float(r['rf2_kN'])
        })

# Compute trapezoidal external work: W_ext = integral RF2 du2
w_ext = 0.0
work_history = [{'increment': 1, 'u2_mm': rf_rows[0]['u2_mm'], 'rf2_kN': rf_rows[0]['rf2_kN'], 'w_ext_kNmm': 0.0}]

# At u=0, RF=0
prev_u = 0.0
prev_rf = 0.0

for r in rf_rows:
    u = r['u2_mm']
    rf = r['rf2_kN']
    du = u - prev_u
    if du > 0:
        dw = 0.5 * (rf + prev_rf) * du
        w_ext += dw
    r['w_ext_kNmm'] = w_ext
    prev_u = u
    prev_rf = rf

# 2. Read UEL energy balance
energy_rows = []
with open('results/validation/f1645_prop_uel_energy_balance.csv', 'r') as f:
    reader = csv.DictReader(f)
    for r in reader:
        energy_rows.append({
            'step': int(r['Step']),
            'increment': int(r['Increment']),
            'total_time': float(r['TotalTime']),
            'step_time': float(r['StepTime']),
            'e_elastic_kNmm': float(r['E_elastic_kNmm']),
            'e_fracture_kNmm': float(r['E_fracture_kNmm']),
            'e_total_kNmm': float(r['E_total_kNmm'])
        })

print("Total RF points: %d, Total Energy points: %d" % (len(rf_rows), len(energy_rows)))

# Compare final values
final_rf = rf_rows[-1]
final_energy = energy_rows[-1]

print("Final u2: %.7f mm" % final_rf['u2_mm'])
print("Final RF2: %.7f kN" % final_rf['rf2_kN'])
print("Final External Work W_ext: %.7e kN*mm (%.7f mJ)" % (w_ext, w_ext * 1000.0))
print("Final E_elastic:          %.7e kN*mm (%.7f mJ)" % (final_energy['e_elastic_kNmm'], final_energy['e_elastic_kNmm'] * 1000.0))
print("Final E_fracture:         %.7e kN*mm (%.7f mJ)" % (final_energy['e_fracture_kNmm'], final_energy['e_fracture_kNmm'] * 1000.0))
print("Final E_total (Ee + Ef):  %.7e kN*mm (%.7f mJ)" % (final_energy['e_total_kNmm'], final_energy['e_total_kNmm'] * 1000.0))

# Work-Energy residual
diff = abs(w_ext - final_energy['e_total_kNmm'])
rel_err = diff / final_energy['e_total_kNmm']
print("Absolute Work-Energy Residual: %.7e kN*mm" % diff)
print("Relative Work-Energy Residual: %.7e (%.4f %%)" % (rel_err, rel_err * 100.0))

# Detailed step 1 comparison
step1_last_energy = [r for r in energy_rows if r['step'] == 1][-1]
step1_last_rf = rf_rows[49] # increment 50
w_ext_step1 = step1_last_rf['w_ext_kNmm']
diff_s1 = abs(w_ext_step1 - step1_last_energy['e_total_kNmm'])
rel_err_s1 = diff_s1 / step1_last_energy['e_total_kNmm']

print("\n--- Step 1 Check (u2 = 0.0050 mm) ---")
print("Step 1 W_ext:   %.7e kN*mm" % w_ext_step1)
print("Step 1 E_total: %.7e kN*mm" % step1_last_energy['e_total_kNmm'])
print("Step 1 Rel Error: %.7e (%.4f %%)" % (rel_err_s1, rel_err_s1 * 100.0))

# Save summary
out_data = {
    'final_u2_mm': final_rf['u2_mm'],
    'final_rf2_kN': final_rf['rf2_kN'],
    'w_external_kNmm': w_ext,
    'w_external_mJ': w_ext * 1000.0,
    'e_elastic_kNmm': final_energy['e_elastic_kNmm'],
    'e_fracture_kNmm': final_energy['e_fracture_kNmm'],
    'e_total_kNmm': final_energy['e_total_kNmm'],
    'work_energy_residual_kNmm': diff,
    'work_energy_relative_error': rel_err,
    'step1_work_energy': {
        'w_external_kNmm': w_ext_step1,
        'e_total_kNmm': step1_last_energy['e_total_kNmm'],
        'relative_error': rel_err_s1
    }
}

with open('results/validation/f1646_work_energy_balance.json', 'w') as f:
    json.dump(out_data, f, indent=2)
print("Saved to results/validation/f1646_work_energy_balance.json")

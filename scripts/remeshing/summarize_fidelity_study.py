import json
import os

p = 'models/pandey_kumar_mode1/217_f1725_physics_study/f1725_physics_study_results.json'
with open(p, 'r') as f:
    d = json.load(f)

print(f"{'Case Name':<28} | {'Elems':<6} | {'Quad%':<6} | {'Lig1 N':<6} | {'Lig1 h':<7} | {'Lig2 N':<6} | {'Lig2 h':<7} | {'Bulk N':<6} | {'Bulk h':<7}")
print("-" * 98)
for k, v in d.items():
    m = v['metrics']
    print(f"{k:<28} | {m['num_elements']:<6} | {m['quad_percentage']:<6.2f} | {m['lig1_h1_h2']['count']:<6} | {m['lig1_h1_h2']['mean']:<7.2f} | {m['lig2_h2_h3']['count']:<6} | {m['lig2_h2_h3']['mean']:<7.2f} | {m['bulk']['count']:<6} | {m['bulk']['mean']:<7.2f}")


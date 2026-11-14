# audit_donor_norms.py
import os
import sys
import math
import json
import odbAccess

work_dir = "/scratch9/pr21vyci/runs/mode1_pk_f1746_case3_envelope_remesh"
odbs = [
    ("T1", "PK_SEC43_COMPANION_T1.odb"),
    ("T2", "PK_SEC43_COMPANION_T2.odb"),
    ("T3", "PK_SEC43_COMPANION_T3.odb"),
    ("S2", "PK_SEC43_PRESCRIBED_STATE2.odb"),
    ("S4", "PK_SEC43_PRESCRIBED_STATE4.odb")
]

results = {}
for sid, fname in odbs:
    fpath = os.path.join(work_dir, fname)
    odb = odbAccess.openOdb(fpath, readOnly=True)
    step = odb.steps.values()[0]
    frame = step.frames[-1]
    
    f_avg = frame.fieldOutputs['MISESAVG']
    f_evol = frame.fieldOutputs['EVOL']
    
    energy_sum = 0.0
    for v_avg, v_evol in zip(f_avg.values, f_evol.values):
        energy_sum += (v_avg.data ** 2) * v_evol.data
    norm_u = math.sqrt(energy_sum)
    mean_elem_norm = norm_u / math.sqrt(len(f_avg.values))
    
    results[sid] = {
        'total_solution_energy_norm': norm_u,
        'mean_element_energy_norm': mean_elem_norm,
        'element_count': len(f_avg.values),
        'frame_id': frame.frameId,
        'frame_desc': frame.description,
        'frame_value': frame.frameValue
    }
    odb.close()

out_path = os.path.join(work_dir, "audit_donor_norms_receipt.json")
with open(out_path, 'w') as f:
    json.dump(results, f, indent=2)

print("AUDIT_DONOR_NORMS_COMPLETE")
for sid in sorted(results.keys()):
    print("%s: norm_u = %.6f MPa*mm, mean_elem = %.6f MPa*mm (Frame: %s, Val: %.4f)" % 
          (sid, results[sid]['total_solution_energy_norm'], results[sid]['mean_element_energy_norm'],
           results[sid]['frame_id'], results[sid]['frame_value']))

# -*- coding: utf-8 -*-
"""
export_envelope_map.py

Runs on the cluster with Abaqus Python to extract per-element envelope error
eta_hat_e^(env) and dominant donor state for all 3,923 elements, saving to JSON.
"""
from __future__ import print_function
import os
import sys
import math
import json
import odbAccess

def export_map(work_dir, out_json):
    odbs = {
        'T1': os.path.join(work_dir, 'PK_SEC43_COMPANION_T1.odb'),
        'T2': os.path.join(work_dir, 'PK_SEC43_COMPANION_T2.odb'),
        'T3': os.path.join(work_dir, 'PK_SEC43_COMPANION_T3.odb'),
        'S2': os.path.join(work_dir, 'PK_SEC43_PRESCRIBED_STATE2.odb'),
        'S4': os.path.join(work_dir, 'PK_SEC43_PRESCRIBED_STATE4.odb')
    }

    state_data = {}
    element_volumes = {}

    for sid, p in sorted(odbs.items()):
        odb = odbAccess.openOdb(p, readOnly=True)
        step = odb.steps.values()[0]
        frame = step.frames[-1]
        
        f_eri = frame.fieldOutputs['MISESERI']
        f_avg = frame.fieldOutputs['MISESAVG']
        f_evol = frame.fieldOutputs['EVOL']
        
        d = {}
        for v_eri, v_avg, v_evol in zip(f_eri.values, f_avg.values, f_evol.values):
            lbl = v_eri.elementLabel
            eri = float(v_eri.data)
            avg = float(v_avg.data)
            evol = float(v_evol.data)
            element_volumes[lbl] = evol
            d[lbl] = {'eri': eri, 'avg': avg, 'evol': evol}
            
        odb.close()
        state_data[sid] = d

    n_elem = len(element_volumes)
    assert n_elem == 3923, "Element count mismatch: %d" % n_elem

    # Compute global solution energy norm ||u||_k for each state
    global_norms = {}
    normalized_errors = {sid: {} for sid in state_data}
    
    for sid, d in state_data.items():
        energy_sum = sum((d[lbl]['avg'] ** 2) * element_volumes[lbl] for lbl in d)
        norm_u = math.sqrt(energy_sum)
        mean_elem_norm = norm_u / math.sqrt(n_elem)
        global_norms[sid] = {
            'total_solution_energy_norm': norm_u,
            'mean_element_energy_norm': mean_elem_norm
        }
        
        for lbl in d:
            eri = d[lbl]['eri']
            evol = element_volumes[lbl]
            elem_err_norm = eri * math.sqrt(evol)
            eta_hat = elem_err_norm / mean_elem_norm if mean_elem_norm > 1e-12 else 0.0
            normalized_errors[sid][lbl] = eta_hat

    # Compute unified envelope
    elem_map = {}
    for lbl in element_volumes:
        etas = {sid: normalized_errors[sid][lbl] for sid in state_data}
        best_sid = max(etas, key=etas.get)
        elem_map[str(lbl)] = {
            'eta': round(etas[best_sid], 6),
            'dominant_state': best_sid
        }

    out_data = {
        'total_elements': n_elem,
        'global_norms': global_norms,
        'elements': elem_map
    }

    with open(out_json, 'w') as f:
        json.dump(out_data, f, indent=2)
    print("Successfully exported envelope map to %s (%d elements)" % (out_json, len(elem_map)))

if __name__ == '__main__':
    work_dir = sys.argv[1] if len(sys.argv) > 1 else '.'
    out_json = sys.argv[2] if len(sys.argv) > 2 else 'f1745_element_envelope_map.json'
    export_map(work_dir, out_json)

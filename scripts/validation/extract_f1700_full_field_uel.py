# -*- coding: utf-8 -*-
"""
extract_f1700_full_field_uel.py
Extracts full-field UEL nodal displacements, reaction forces, integration point
strains, and solution-dependent state variables (damage SDV1, degradation SDV15)
from authentic restart extraction ODBs on the cluster for States 2, 4, and 5.
"""
from __future__ import print_function
import os
import sys
import json
import math
from odbAccess import openOdb

STATES = {
    'STATE2': {
        'name': 'State 2: Hole Arrest',
        'odb': '/scratch9/pr21vyci/runs/mode1_pk_sec43_staggered_job1/test_restart_read/RESTART_STATE2.odb',
        'nominal_uy': 0.200,
        'step': 1,
        'inc': 400
    },
    'STATE4': {
        'name': 'State 4: Secondary Mid-Propagation',
        'odb': '/scratch9/pr21vyci/runs/mode1_pk_sec43_staggered_job1/test_restart_read/RESTART_STATE4.odb',
        'nominal_uy': 0.300,
        'step': 1,
        'inc': 600
    },
    'STATE5': {
        'name': 'State 5: Terminal Dual Severance',
        'odb': '/scratch9/pr21vyci/runs/mode1_pk_sec43_staggered_job1/test_restart_read/RESTART_STATE5.odb',
        'nominal_uy': 1.500,
        'step': 2,
        'inc': 2500
    }
}

OUT_JSON = '/scratch9/pr21vyci/runs/mode1_pk_sec43_staggered_job1/test_restart_read/f1700_extracted_uel_full_field.json'

def extract_state_data(state_key, state_info):
    odb_path = state_info['odb']
    if not os.path.exists(odb_path):
        raise RuntimeError("ODB not found: " + odb_path)
    
    print("Opening " + odb_path + "...")
    odb = openOdb(odb_path, readOnly=True)
    step = odb.steps['EXTRACT']
    frame = step.frames[0]
    
    # 1. Nodal Displacements
    fo_u = frame.fieldOutputs['U']
    u_dict = {}
    sum_u2 = 0.0
    max_u_mag = 0.0
    for val in fo_u.values:
        nl = val.nodeLabel
        u1 = float(val.data[0])
        u2 = float(val.data[1])
        u_dict[nl] = [u1, u2]
        mag = math.sqrt(u1*u1 + u2*u2)
        sum_u2 += mag*mag
        if mag > max_u_mag:
            max_u_mag = mag
    
    l2_u = math.sqrt(sum_u2)
    
    # 2. Reaction Forces
    rf_dict = {}
    fo_rf = frame.fieldOutputs['RF']
    for val in fo_rf.values:
        nl = val.nodeLabel
        rf1 = float(val.data[0])
        rf2 = float(val.data[1])
        if abs(rf1) > 1e-12 or abs(rf2) > 1e-12:
            rf_dict[nl] = [rf1, rf2]
            
    rp_u = u_dict.get(4040, [0.0, 0.0])
    rp_rf = rf_dict.get(4040, [0.0, 0.0])
    
    # 3. Element / IP Fields
    fo_d = frame.fieldOutputs['SDV1'] if 'SDV1' in frame.fieldOutputs else None
    fo_g = frame.fieldOutputs['SDV15'] if 'SDV15' in frame.fieldOutputs else None
    fo_e = frame.fieldOutputs['E'] if 'E' in frame.fieldOutputs else None
    fo_s = frame.fieldOutputs['S'] if 'S' in frame.fieldOutputs else None
    
    # Per-element aggregated damage and degradation
    elem_damage = {}
    elem_degradation = {}
    elem_strains = {}
    
    d_all = []
    g_all = []
    e11_all = []
    e22_all = []
    e12_all = []
    
    if fo_d:
        for val in fo_d.values:
            el = val.elementLabel
            d_val = float(val.data)
            d_all.append(d_val)
            if el not in elem_damage:
                elem_damage[el] = []
            elem_damage[el].append(d_val)
            
    if fo_g:
        for val in fo_g.values:
            el = val.elementLabel
            g_val = float(val.data)
            g_all.append(g_val)
            if el not in elem_degradation:
                elem_degradation[el] = []
            elem_degradation[el].append(g_val)
            
    if fo_e:
        for val in fo_e.values:
            el = val.elementLabel
            e11 = float(val.data[0])
            e22 = float(val.data[1])
            e12 = float(val.data[3]) if len(val.data) > 3 else 0.0
            e11_all.append(e11)
            e22_all.append(e22)
            e12_all.append(e12)
            if el not in elem_strains:
                elem_strains[el] = []
            elem_strains[el].append([e11, e22, e12])
            
    # Compute element averages
    elem_avg_d = {el: sum(vals)/float(len(vals)) for el, vals in elem_damage.items()}
    elem_avg_g = {el: sum(vals)/float(len(vals)) for el, vals in elem_degradation.items()}
    elem_avg_e = {el: [
        sum(v[0] for v in vals)/float(len(vals)),
        sum(v[1] for v in vals)/float(len(vals)),
        sum(v[2] for v in vals)/float(len(vals))
    ] for el, vals in elem_strains.items()}
    
    # Counts of damaged elements
    cnt_d_05 = sum(1 for v in elem_avg_d.values() if v >= 0.50)
    cnt_d_09 = sum(1 for v in elem_avg_d.values() if v >= 0.90)
    cnt_d_099 = sum(1 for v in elem_avg_d.values() if v >= 0.99)
    
    odb.close()
    
    return {
        'state_name': state_info['name'],
        'step_inc': 'Step %d Inc %d' % (state_info['step'], state_info['inc']),
        'nominal_uy_mm': state_info['nominal_uy'],
        'rp_displacement_mm': rp_u,
        'rp_reaction_force_kN': [rp_rf[0]/1000.0, rp_rf[1]/1000.0],
        'rp_reaction_force_N': rp_rf,
        'num_nodes': len(u_dict),
        'num_elements': len(elem_avg_d),
        'num_ips': len(d_all),
        'displacement_l2_norm': l2_u,
        'displacement_max_mag': max_u_mag,
        'u1_min': min(v[0] for v in u_dict.values()),
        'u1_max': max(v[0] for v in u_dict.values()),
        'u2_min': min(v[1] for v in u_dict.values()),
        'u2_max': max(v[1] for v in u_dict.values()),
        'damage_min': min(d_all) if d_all else 0.0,
        'damage_max': max(d_all) if d_all else 0.0,
        'degradation_min': min(g_all) if g_all else 1.0,
        'degradation_max': max(g_all) if g_all else 1.0,
        'num_elems_d_ge_05': cnt_d_05,
        'num_elems_d_ge_09': cnt_d_09,
        'num_elems_d_ge_099': cnt_d_099,
        'e11_max_abs': max(abs(e) for e in e11_all) if e11_all else 0.0,
        'e22_max_abs': max(abs(e) for e in e22_all) if e22_all else 0.0,
        'e12_max_abs': max(abs(e) for e in e12_all) if e12_all else 0.0,
        'nodal_displacements': u_dict,
        'element_avg_damage': elem_avg_d,
        'element_avg_degradation': elem_avg_g,
        'element_avg_strains': elem_avg_e
    }

def main():
    results = {}
    for sk in ['STATE2', 'STATE4', 'STATE5']:
        print("Extracting " + sk + "...")
        results[sk] = extract_state_data(sk, STATES[sk])
        
    print("Writing extracted data to " + OUT_JSON + "...")
    with open(OUT_JSON, 'w') as f:
        json.dump(results, f, indent=2)
    print("SUCCESS: Full-field UEL state extracted and saved.")

if __name__ == '__main__':
    main()

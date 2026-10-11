import os
import sys
import json
from odbAccess import openOdb

BASE_DIR = '/scratch9/pr21vyci/runs/mode1_method_b_f1408'
CASES = {
    '1S': os.path.join(BASE_DIR, '01_pre_1s', 'M1_PRE_1S.odb'),
    '2S': os.path.join(BASE_DIR, '02_pre_2s', 'M1_PRE_2S.odb'),
    '4S': os.path.join(BASE_DIR, '03_pre_4s', 'M1_PRE_4S.odb')
}

summary = {}

for case_name, odb_path in CASES.items():
    print("=== Processing %s: %s ===" % (case_name, odb_path))
    if not os.path.exists(odb_path):
        print("ERROR: ODB does not exist: %s" % odb_path)
        continue
        
    odb = openOdb(path=odb_path, readOnly=True)
    steps = list(odb.steps.keys())
    print("Steps: %s" % str(steps))
    
    last_step_name = steps[-1]
    last_step = odb.steps[last_step_name]
    last_frame = last_step.frames[-1]
    
    print("Last step: %s, Total frames in last step: %d" % (last_step_name, len(last_step.frames)))
    print("Available field outputs in last frame: %s" % str(list(last_frame.fieldOutputs.keys())))
    
    # Extract terminal displacement and reaction force at node 999999 from LAST frame
    u_val = None
    rf_val = None
    if 'U' in last_frame.fieldOutputs:
        u_field = last_frame.fieldOutputs['U']
        for val in u_field.values:
            if val.nodeLabel == 999999:
                u_val = float(val.data[1])
                break
    if 'RF' in last_frame.fieldOutputs:
        rf_field = last_frame.fieldOutputs['RF']
        for val in rf_field.values:
            if val.nodeLabel == 999999:
                rf_val = float(val.data[1])
                break
                
    # Extract MISESERI in last frame
    miseseri_dict = {}
    if 'MISESERI' in last_frame.fieldOutputs:
        m_field = last_frame.fieldOutputs['MISESERI']
        for val in m_field.values:
            miseseri_dict[val.elementLabel] = float(val.data)
        print("Extracted %d MISESERI element values" % len(miseseri_dict))
    else:
        print("WARNING: MISESERI not in last frame field outputs!")
        
    # Extract SDV14 (damage d) in last frame if available
    damage_dict = {}
    for dkey in ['SDV_SDV14', 'SDV14', 'SDV']:
        if dkey in last_frame.fieldOutputs:
            d_field = last_frame.fieldOutputs[dkey]
            for val in d_field.values:
                # If SDV is an array, take index 13 (SDV14)
                if hasattr(val.data, '__getitem__'):
                    damage_dict[val.elementLabel] = float(val.data[13])
                else:
                    damage_dict[val.elementLabel] = float(val.data)
            print("Extracted %d damage values (max=%f)" % (len(damage_dict), max(damage_dict.values()) if damage_dict else 0.0))
            break
            
    odb.close()
    
    summary[case_name] = {
        'steps': steps,
        'terminal_u2': u_val,
        'terminal_rf2': rf_val,
        'miseseri_count': len(miseseri_dict),
        'miseseri_sample': {k: miseseri_dict[k] for k in sorted(miseseri_dict.keys())[:10]} if miseseri_dict else {},
        'damage_max': max(damage_dict.values()) if damage_dict else None,
        'miseseri_dict': miseseri_dict
    }

# Cross-case comparison
comparison = {}
if '1S' in summary and '2S' in summary and '4S' in summary:
    u_1s = summary['1S']['terminal_u2']
    u_2s = summary['2S']['terminal_u2']
    u_4s = summary['4S']['terminal_u2']
    
    rf_1s = summary['1S']['terminal_rf2']
    rf_2s = summary['2S']['terminal_rf2']
    rf_4s = summary['4S']['terminal_rf2']
    
    print("\n=== TERMINAL QUANTITIES COMPARISON ===")
    print("1S: U2 = %s mm, RF2 = %s kN" % (str(u_1s), str(rf_1s)))
    print("2S: U2 = %s mm, RF2 = %s kN" % (str(u_2s), str(rf_2s)))
    print("4S: U2 = %s mm, RF2 = %s kN" % (str(u_4s), str(rf_4s)))
    
    delta_rf_2s_1s = abs(rf_2s - rf_1s) if (rf_2s is not None and rf_1s is not None) else None
    delta_rf_4s_1s = abs(rf_4s - rf_1s) if (rf_4s is not None and rf_1s is not None) else None
    rel_rf_2s = delta_rf_2s_1s / abs(rf_1s) * 100.0 if (rf_1s and delta_rf_2s_1s is not None) else 0.0
    rel_rf_4s = delta_rf_4s_1s / abs(rf_1s) * 100.0 if (rf_1s and delta_rf_4s_1s is not None) else 0.0
    
    if delta_rf_2s_1s is not None:
        print("Delta RF (2S vs 1S): %e kN (%.6f%%)" % (delta_rf_2s_1s, rel_rf_2s))
    if delta_rf_4s_1s is not None:
        print("Delta RF (4S vs 1S): %e kN (%.6f%%)" % (delta_rf_4s_1s, rel_rf_4s))
    
    # Compare MISESERI fields element-by-element
    m_1s = summary['1S']['miseseri_dict']
    m_2s = summary['2S']['miseseri_dict']
    m_4s = summary['4S']['miseseri_dict']
    
    common_elems = set(m_1s.keys()) & set(m_2s.keys()) & set(m_4s.keys())
    print("Common MISESERI elements across 1S, 2S, 4S: %d" % len(common_elems))
    
    max_diff_2s_1s = 0.0
    max_diff_4s_1s = 0.0
    diffs_2s = []
    diffs_4s = []
    
    for el in common_elems:
        d2 = abs(m_2s[el] - m_1s[el])
        d4 = abs(m_4s[el] - m_1s[el])
        diffs_2s.append(d2)
        diffs_4s.append(d4)
        if d2 > max_diff_2s_1s: max_diff_2s_1s = d2
        if d4 > max_diff_4s_1s: max_diff_4s_1s = d4
        
    print("Max |MISESERI(2S) - MISESERI(1S)|: %e" % max_diff_2s_1s)
    print("Max |MISESERI(4S) - MISESERI(1S)|: %e" % max_diff_4s_1s)
    print("Mean |MISESERI(2S) - MISESERI(1S)|: %e" % (sum(diffs_2s)/len(diffs_2s) if diffs_2s else 0.0))
    print("Mean |MISESERI(4S) - MISESERI(1S)|: %e" % (sum(diffs_4s)/len(diffs_4s) if diffs_4s else 0.0))
    
    comparison = {
        'terminal_u2': {'1S': u_1s, '2S': u_2s, '4S': u_4s},
        'terminal_rf2': {'1S': rf_1s, '2S': rf_2s, '4S': rf_4s},
        'delta_rf_2s_vs_1s': delta_rf_2s_1s,
        'rel_rf_2s_vs_1s_pct': rel_rf_2s,
        'delta_rf_4s_vs_1s': delta_rf_4s_1s,
        'rel_rf_4s_vs_1s_pct': rel_rf_4s,
        'common_miseseri_elements': len(common_elems),
        'max_diff_miseseri_2s_1s': max_diff_2s_1s,
        'max_diff_miseseri_4s_1s': max_diff_4s_1s,
        'mean_diff_miseseri_2s_1s': sum(diffs_2s)/len(diffs_2s) if diffs_2s else 0.0,
        'mean_diff_miseseri_4s_1s': sum(diffs_4s)/len(diffs_4s) if diffs_4s else 0.0
    }

# Remove heavy dicts from summary before dumping to json
for k in summary:
    del summary[k]['miseseri_dict']
    
output_data = {
    'cases': summary,
    'comparison': comparison
}

out_json = os.path.join(BASE_DIR, 'METHOD_B_PRE_COMPARISON_SUMMARY.json')
with open(out_json, 'w') as f:
    json.dump(output_data, f, indent=2)

print("\nSaved comparison summary to: %s" % out_json)

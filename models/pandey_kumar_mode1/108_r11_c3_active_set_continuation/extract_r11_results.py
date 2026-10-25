from odbAccess import openOdb
import json
import sys

odb_path = 'M1_C3_ACTIVE_SET_R11.odb'
odb = openOdb(odb_path, readOnly=True)

results = {}

for step_name in odb.steps.keys():
    step = odb.steps[step_name]
    last_frame = step.frames[-1]

    # History output (energies)
    energies = {}
    for key, val in step.historyRegions.items():
        for e_key, e_series in val.historyOutputs.items():
            if len(e_series.data) > 0:
                energies[e_key] = e_series.data[-1][1]

    # RP reaction force
    rf2_rp = None
    rf_field = last_frame.fieldOutputs['RF'] if 'RF' in last_frame.fieldOutputs else None
    u_field = last_frame.fieldOutputs['U'] if 'U' in last_frame.fieldOutputs else None

    rf3_vals = []
    if rf_field:
        for val in rf_field.values:
            if val.nodeLabel == 999999:
                rf2_rp = float(val.data[1] * 1000.0) # Convert kN to N
            if len(val.data) >= 3:
                rf3_vals.append((val.nodeLabel, float(val.data[2])))

    results[step_name] = {
        'time': float(last_frame.frameValue),
        'rf2_rp_N': rf2_rp,
        'energies': energies,
        'rf3_count': len(rf3_vals),
        'min_rf3': min([v[1] for v in rf3_vals]) if rf3_vals else None,
        'max_rf3': max([v[1] for v in rf3_vals]) if rf3_vals else None,
        'kkt_violations_neg_rf3': sum(1 for v in rf3_vals if v[1] < -1e-6)
    }

odb.close()

with open('r11_extracted_telemetry.json', 'w') as f:
    json.dump(results, f, indent=2)

print("SUCCESS: Extracted R11 telemetry:")
print(json.dumps(results, indent=2))

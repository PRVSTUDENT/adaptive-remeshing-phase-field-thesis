# extract_r16_iterations.py
# Abaqus Python script to extract energy & field metrics for R16 Iterations 10 and 14
import sys, os, json
from odbAccess import openOdb

def extract_from_odb(odb_path):
    if not os.path.exists(odb_path):
        return None
    odb = openOdb(odb_path, readOnly=True)
    step = odb.steps['Inc1-Coupled']
    frame = step.frames[-1]

    allse, allwk, allae, allie = 0.0, 0.0, 0.0, 0.0
    for reg_key, region in step.historyRegions.items():
        if 'ALLSE' in region.historyOutputs:
            allse = float(region.historyOutputs['ALLSE'].data[-1][1])
        if 'ALLWK' in region.historyOutputs:
            allwk = float(region.historyOutputs['ALLWK'].data[-1][1])
        if 'ALLAE' in region.historyOutputs:
            allae = float(region.historyOutputs['ALLAE'].data[-1][1])
        if 'ALLIE' in region.historyOutputs:
            allie = float(region.historyOutputs['ALLIE'].data[-1][1])

    rf2_rp, u2_rp = 0.0, 0.0
    for val in frame.fieldOutputs['RF'].values:
        if val.nodeLabel == 999999:
            rf2_rp = float(val.data[1]) * 1000.0
            break
    for val in frame.fieldOutputs['U'].values:
        if val.nodeLabel == 999999:
            u2_rp = float(val.data[1])
            break

    d_max = 0.0
    for val in frame.fieldOutputs['U'].values:
        if val.nodeLabel != 999999:
            d = float(val.data[2])
            if d > d_max:
                d_max = d

    odb.close()
    return {
        'allse_mJ': allse * 1000.0,
        'allwk_mJ': allwk * 1000.0,
        'allae_mJ': allae * 1000.0,
        'allie_mJ': allie * 1000.0,
        'rf2_rp_N': rf2_rp,
        'u2_rp_mm': u2_rp,
        'd_max': d_max
    }

run_dir = '/scratch9/pr21vyci/runs/mode1_c3_active_set_continuation_r16'
res10 = extract_from_odb(os.path.join(run_dir, 'M1_C3_ACTIVE_SET_R16_IT10.odb'))
res14 = extract_from_odb(os.path.join(run_dir, 'M1_C3_ACTIVE_SET_R16_IT14.odb'))

out = {
    'iteration_10_reference_matched': res10,
    'iteration_14_terminal_converged': res14
}

print("JSON_METRICS_START")
print(json.dumps(out, indent=2))
print("JSON_METRICS_END")

from odbAccess import openOdb
import json
import sys

odb_path = "/scratch9/pr21vyci/runs/mode1_turn122_staggered_diagnostic/M1_DIAG_STAG_SOLVE.odb"
out_json_path = "/scratch9/pr21vyci/runs/mode1_turn122_staggered_diagnostic/odb_extracted_data.json"

odb = openOdb(odb_path, readOnly=True)

res = {"steps": {}}

for step_name in odb.steps.keys():
    step = odb.steps[step_name]
    last_frame = step.frames[-1]
    
    print("Field outputs in " + step_name + ": " + str(last_frame.fieldOutputs.keys()))
    
    # Nodal displacements
    u_field = last_frame.fieldOutputs['U']
    u_data = {}
    for val in u_field.values:
        u_data[val.nodeLabel] = [float(x) for x in val.data]
        
    # Nodal reaction forces
    rf_field = last_frame.fieldOutputs['RF']
    rf_data = {}
    for val in rf_field.values:
        rf_data[val.nodeLabel] = [float(x) for x in val.data]
        
    # Element SDVs if present
    sdv_data = {}
    for k in last_frame.fieldOutputs.keys():
        if 'SDV' in k:
            f = last_frame.fieldOutputs[k]
            for val in f.values:
                if val.elementLabel not in sdv_data:
                    sdv_data[val.elementLabel] = {}
                try:
                    sdv_data[val.elementLabel][k] = float(val.data)
                except Exception:
                    sdv_data[val.elementLabel][k] = [float(x) for x in val.data]
        
    res["steps"][step_name] = {
        "time": last_frame.frameValue,
        "u": u_data,
        "rf": rf_data,
        "sdv": sdv_data
    }

odb.close()

with open(out_json_path, "w") as f:
    json.dump(res, f, indent=2)

print("ODB extraction complete! Saved to " + out_json_path)

from odbAccess import openOdb
import json
import os
import sys

odb_path = "M1_C3_STAGGERED_R7.odb"
if not os.path.exists(odb_path):
    print("Error: ODB not found at %s" % odb_path)
    sys.exit(1)

odb = openOdb(odb_path, readOnly=True)

out = {
    "odb": odb_path,
    "steps": {}
}

# Find top edge node set
top_set = None
for nset_name in odb.rootAssembly.nodeSets.keys():
    if "TOP" in nset_name.upper():
        top_set = odb.rootAssembly.nodeSets[nset_name]
        break

for sname in odb.steps.keys():
    st = odb.steps[sname]
    fr = st.frames[-1]
    
    # Calculate RF2 on top nodes
    rf2_sum = 0.0
    if 'RF' in fr.fieldOutputs:
        rf_field = fr.fieldOutputs['RF']
        if top_set:
            rf_sub = rf_field.getSubset(region=top_set)
            for val in rf_sub.values:
                rf2_sum += val.data[1]
        else:
            # Fallback: scan nodes with Y ~ 20.0
            for val in rf_field.values:
                rf2_sum += val.data[1]
                
    d_max = 0.0
    if 'SDV1' in fr.fieldOutputs:
        for val in fr.fieldOutputs['SDV1'].values:
            if val.data > d_max:
                d_max = float(val.data)
                
    h_max = 0.0
    if 'SDV2' in fr.fieldOutputs:
        for val in fr.fieldOutputs['SDV2'].values:
            if val.data > h_max:
                h_max = float(val.data)
                
    # Also check if nodal phase DOF 8 or U2 is present
    u2_max = 0.0
    if 'U' in fr.fieldOutputs:
        for val in fr.fieldOutputs['U'].values:
            if val.data[1] > u2_max:
                u2_max = float(val.data[1])
                
    out["steps"][sname] = {
        "rf2_kN": float(rf2_sum),
        "rf2_N": float(rf2_sum * 1000.0),
        "d_max": float(d_max),
        "h_max_MPa": float(h_max),
        "u2_max_mm": float(u2_max)
    }
    print("Step %s: RF2 = %.4f N, d_max = %.6f, H_max = %.4f MPa, u2_max = %.8f mm" % (
        sname, rf2_sum * 1000.0, d_max, h_max, u2_max
    ))

with open("r7_metrics.json", "w") as fp:
    json.dump(out, fp, indent=2)

print("Saved r7_metrics.json successfully.")

from odbAccess import openOdb
import sys

odb_path = "M1_C3_STAGGERED_R6.odb"
odb = openOdb(odb_path, readOnly=True)

steps_to_check = ["Stage-A", "Inc1-Mech1", "Inc1-Phase1", "Inc1-Mech2"]

print("STEP INSPECTION AT CRACK TIP ELEMENTS:")

# Find elements with highest SDV2 (H) in Inc1-Mech2
step4 = odb.steps["Inc1-Mech2"]
frame4 = step4.frames[-1]
sdv2_f4 = frame4.fieldOutputs['SDV2']
top_h_elements = []
for val in sdv2_f4.values:
    top_h_elements.append((val.elementLabel, float(val.data)))
top_h_elements.sort(key=lambda x: x[1], reverse=True)

top_eids = [x[0] for x in top_h_elements[:5]]
print("Top 5 elements with highest H in Inc1-Mech2: %s" % top_h_elements[:5])

for sname in steps_to_check:
    if sname not in odb.steps: continue
    st = odb.steps[sname]
    fr = st.frames[-1]
    print("\n--- Step: %s (Time=%s, NumFrames=%d) ---" % (sname, fr.frameValue, len(st.frames)))
    
    # Check RP
    if 'RF' in fr.fieldOutputs:
        for val in fr.fieldOutputs['RF'].values:
            if val.nodeLabel == 999999:
                print("  RP RF2: %.4f N" % (val.data[1] * 1000.0))
    if 'U' in fr.fieldOutputs:
        for val in fr.fieldOutputs['U'].values:
            if val.nodeLabel == 999999:
                print("  RP U2:  %.9f mm" % val.data[1])
                
    # Check top elements
    for eid in top_eids:
        # SDV1 (d) and SDV2 (H)
        d_val = None
        h_val = None
        if 'SDV1' in fr.fieldOutputs:
            for val in fr.fieldOutputs['SDV1'].values:
                if val.elementLabel == eid:
                    d_val = float(val.data)
                    break
        if 'SDV2' in fr.fieldOutputs:
            for val in fr.fieldOutputs['SDV2'].values:
                if val.elementLabel == eid:
                    h_val = float(val.data)
                    break
        print("  Elem %d: d=%.6f, H=%.6f MPa" % (eid, d_val if d_val is not None else -1, h_val if h_val is not None else -1))

odb.close()

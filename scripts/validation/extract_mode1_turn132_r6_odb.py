from odbAccess import openOdb
import json
import os
import sys

odb_path = "M1_C3_STAGGERED_R6.odb"
if not os.path.exists(odb_path):
    print("Error: ODB not found at %s" % odb_path)
    sys.exit(1)

odb = openOdb(odb_path, readOnly=True)

results = {
    "odb_path": odb_path,
    "steps": {},
    "step_order": []
}

step_names = [
    "Stage-A",
    "Inc1-Mech1", "Inc1-Phase1", "Inc1-Mech2",
    "Inc2-Mech1", "Inc2-Phase1", "Inc2-Mech2",
    "Inc3-Mech1", "Inc3-Phase1", "Inc3-Mech2",
    "Inc4-Mech1", "Inc4-Phase1", "Inc4-Mech2",
    "Inc5-Mech1", "Inc5-Phase1", "Inc5-Mech2"
]

for step_name in step_names:
    if step_name not in odb.steps:
        print("Warning: Step %s not in ODB" % step_name)
        continue

    results["step_order"].append(step_name)
    step = odb.steps[step_name]
    num_frames = len(step.frames)
    frame = step.frames[-1]

    # 1. SDV1 (phase field d)
    d_max = -1.0
    d_min = 2.0
    if 'SDV1' in frame.fieldOutputs:
        sdv1 = frame.fieldOutputs['SDV1']
        for val in sdv1.values:
            d = float(val.data)
            if d > d_max:
                d_max = d
            if d < d_min:
                d_min = d

    # 2. SDV2 (history field H)
    h_max = -1.0
    h_min = 1e30
    if 'SDV2' in frame.fieldOutputs:
        sdv2 = frame.fieldOutputs['SDV2']
        for val in sdv2.values:
            h = float(val.data)
            if h > h_max:
                h_max = h
            if h < h_min:
                h_min = h

    # 3. Displacements U
    rp_u2 = 0.0
    if 'U' in frame.fieldOutputs:
        u = frame.fieldOutputs['U']
        for val in u.values:
            if val.nodeLabel == 999999:
                rp_u2 = float(val.data[1])

    # 4. Reaction forces RF
    rp_rf2 = 0.0
    max_interior_rf = 0.0
    num_interior_rf = 0
    if 'RF' in frame.fieldOutputs:
        rf = frame.fieldOutputs['RF']
        for val in rf.values:
            if val.nodeLabel == 999999:
                rp_rf2 = float(val.data[1])
            elif val.nodeLabel <= 2769:
                rf1 = abs(float(val.data[0])) if len(val.data) > 0 else 0.0
                rf2 = abs(float(val.data[1])) if len(val.data) > 1 else 0.0
                mag = max(rf1, rf2)
                if mag > 1e-6:
                    num_interior_rf += 1
                if mag > max_interior_rf:
                    max_interior_rf = mag

    results["steps"][step_name] = {
        "num_frames": num_frames,
        "frame_time": float(frame.frameValue),
        "rp_u2": rp_u2,
        "rp_rf2_kN": rp_rf2,
        "rp_rf2_N": rp_rf2 * 1000.0,
        "d_max": d_max,
        "d_min": d_min,
        "h_max": h_max,
        "h_min": h_min,
        "max_interior_rf_kN": max_interior_rf,
        "max_interior_rf_N": max_interior_rf * 1000.0,
        "num_interior_rf_nodes_gt_1uN": num_interior_rf
    }

odb.close()

with open("r6_extracted_telemetry.json", "w") as f:
    json.dump(results, f, indent=2)

print("R6 Extraction completed successfully; written to r6_extracted_telemetry.json")

# -*- coding: utf-8 -*-
"""
Fast, robust Abaqus Python script to extract d and H fields at matched displacement states
for the five Mode-I fixed-mesh levels.
"""
from odbAccess import openOdb
import sys
import os
import json

ODBS = [
    {
        "id": "h0030",
        "h_mm": 0.00300,
        "pbs_id": "1401527.mmaster02",
        "path": "/home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/11_fixed_convergence_h0030/PK_M1_FIX_H0030_VIS.odb"
    },
    {
        "id": "h0020",
        "h_mm": 0.00200,
        "pbs_id": "1401528.mmaster02",
        "path": "/home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/12_fixed_convergence_h0020/PK_M1_FIX_H0020_VIS.odb"
    },
    {
        "id": "h0015",
        "h_mm": 0.00150,
        "pbs_id": "1401529.mmaster02",
        "path": "/home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/13_fixed_convergence_h0015/PK_M1_FIX_H0015_VIS.odb"
    },
    {
        "id": "h00125",
        "h_mm": 0.00125,
        "pbs_id": "1402827.mmaster02",
        "path": "/home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/17_fixed_convergence_h00125_serial/PK_M1_FIX_H00125.odb"
    },
    {
        "id": "h00100",
        "h_mm": 0.00100,
        "pbs_id": "1402828.mmaster02",
        "path": "/home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/18_fixed_convergence_h00100_serial/PK_M1_FIX_H00100.odb"
    }
]

TARGET_DISPLACEMENTS = [0.0050, 0.0056, 0.0060, 0.0070]

def analyze_odb(entry):
    path = entry["path"]
    cid = entry["id"]
    if not os.path.exists(path):
        print("ODB not found: " + path)
        return {"error": "File not found: " + path}

    print("\n========================================================")
    print("Analyzing ODB: %s (h = %.5f mm, path: %s)" % (cid, entry["h_mm"], path))
    print("========================================================")
    odb = openOdb(path=path, readOnly=True)

    # Quickly index all available frames across steps
    candidates = []
    for step_name in odb.steps.keys():
        step = odb.steps[step_name]
        is_step1 = ('Step-1' in step_name) or ('1' in step_name and '2' not in step_name)
        for f_idx, f in enumerate(step.frames):
            t = f.frameValue
            u_app = t * 0.005 if is_step1 else 0.005 + t * 0.005
            candidates.append({
                "step_name": step_name,
                "frame_idx": f_idx,
                "u_applied_mm": u_app,
                "frame": f
            })

    print("Indexed %d total frames across %d steps." % (len(candidates), len(odb.steps)))

    # Select single closest frame for each target displacement
    matched_frames = []
    for td in TARGET_DISPLACEMENTS:
        best = min(candidates, key=lambda c: abs(c["u_applied_mm"] - td))
        matched_frames.append((td, best))
        print("Target u=%.4f mm -> Best match: %s frame %d at u=%.6f mm (diff: %.2e mm)" %
              (td, best["step_name"], best["frame_idx"], best["u_applied_mm"],
               abs(best["u_applied_mm"] - td)))

    # Also add the final frame
    final_cand = candidates[-1]
    matched_frames.append(("final", final_cand))
    print("Final frame -> %s frame %d at u=%.6f mm" %
          (final_cand["step_name"], final_cand["frame_idx"], final_cand["u_applied_mm"]))

    # Inspect field outputs in the first matched frame
    sample_frame = matched_frames[0][1]["frame"]
    field_keys = list(sample_frame.fieldOutputs.keys())
    print("Field outputs in ODB: " + str(field_keys))

    # Identify phase and history field keys
    d_key = None
    h_key = None
    if 'SDV1' in field_keys:
        d_key = 'SDV1'
    elif 'SDV' in field_keys:
        d_key = 'SDV'

    if 'SDV2' in field_keys:
        h_key = 'SDV2'
    elif 'SDV16' in field_keys:
        h_key = 'SDV16'

    print("Resolved field mapping: d -> %s, H -> %s" % (d_key, h_key))

    records = []
    ligament_profiles = {}

    for label, c_info in matched_frames:
        frame = c_info["frame"]
        u_actual = c_info["u_applied_mm"]
        f_idx = c_info["frame_idx"]
        s_name = c_info["step_name"]

        d_vals = []
        h_vals = []

        if d_key and d_key in frame.fieldOutputs:
            d_field = frame.fieldOutputs[d_key]
            for v in d_field.values:
                val = v.data
                if isinstance(val, (list, tuple)):
                    d_vals.append(float(val[0]))
                else:
                    d_vals.append(float(val))

        if h_key and h_key in frame.fieldOutputs:
            h_field = frame.fieldOutputs[h_key]
            for v in h_field.values:
                val = v.data
                if isinstance(val, (list, tuple)):
                    h_vals.append(float(val[1] if len(val) > 1 else val[0]))
                else:
                    h_vals.append(float(val))

        d_min = min(d_vals) if d_vals else 0.0
        d_max = max(d_vals) if d_vals else 0.0
        h_max = max(h_vals) if h_vals else 0.0
        overshoot_count = sum(1 for v in d_vals if v > 1.00001)
        undershoot_count = sum(1 for v in d_vals if v < -1e-5)

        rec = {
            "target_label": str(label),
            "step": s_name,
            "frame_idx": f_idx,
            "u_applied_mm": round(u_actual, 7),
            "d_min": round(d_min, 6),
            "d_max": round(d_max, 6),
            "h_max": round(h_max, 6),
            "overshoot_d_gt_1_count": overshoot_count,
            "undershoot_d_lt_0_count": undershoot_count,
            "total_integration_points": len(d_vals)
        }
        records.append(rec)
        print("  [%s] u=%.6f mm | d_min=%.6f, d_max=%.6f, H_max=%.6e | overshoots(d>1)=%d" %
              (str(label), u_actual, d_min, d_max, h_max, overshoot_count))

    # Extract ligament profile at peak displacement state
    # Sample element centroid x-coordinates and d values near y=0.5
    peak_rec = matched_frames[1][1] # u approx 0.0056 mm
    peak_frame = peak_rec["frame"]
    ligament_d = []
    if d_key and d_key in peak_frame.fieldOutputs:
        d_field = peak_frame.fieldOutputs[d_key]
        root_assembly = odb.rootAssembly
        instance = root_assembly.instances.values()[0]
        # Map element centroids along ligament y in [0.495, 0.505], x >= 0.5
        for v in d_field.values:
            el_label = v.elementLabel
            if el_label:
                # Find element in instance
                try:
                    el = instance.getElementFromLabel(el_label)
                    # compute centroid
                    conn = el.connectivity
                    nodes = [instance.getNodeFromLabel(nl) for nl in conn]
                    xc = sum(n.coordinates[0] for n in nodes) / len(nodes)
                    yc = sum(n.coordinates[1] for n in nodes) / len(nodes)
                    if abs(yc - 0.500) < (entry["h_mm"] * 1.5) and xc >= 0.499:
                        val = float(v.data[0] if isinstance(v.data, (list, tuple)) else v.data)
                        ligament_d.append({"x_mm": round(xc, 5), "y_mm": round(yc, 5), "d": round(val, 6)})
                except:
                    pass

    # Sort ligament points by x
    ligament_d.sort(key=lambda item: item["x_mm"])
    print("Extracted %d ligament points near y=0.5 at u=%.6f mm" %
          (len(ligament_d), peak_rec["u_applied_mm"]))

    odb.close()
    return {
        "id": cid,
        "h_mm": entry["h_mm"],
        "pbs_id": entry["pbs_id"],
        "records": records,
        "ligament_profile_at_peak_sample": ligament_d[:15] # sample first 15 points along ligament
    }

def main():
    results = {}
    for entry in ODBS:
        res = analyze_odb(entry)
        results[entry["id"]] = res

    out_path = '/home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/odb_field_extraction_gate2.json'
    with open(out_path, 'w') as f:
        json.dump(results, f, indent=2)
    print("\n========================================================")
    print("SUCCESS: Saved comprehensive ODB field extractions to:")
    print(out_path)
    print("========================================================")

if __name__ == '__main__':
    main()

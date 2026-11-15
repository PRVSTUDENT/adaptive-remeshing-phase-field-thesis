"""
Fast vectorized audit script for Case 1 Mode-I coupled fracture physics.
Audits all frames in PK_F1728_CASE_1_PROD.odb:
1. SDV1 (d) bounds in [0, 1] and negative/overshoot counts.
2. SDV2 (H) and SDV1 (d) monotonicity across successive frames.
3. Crack connectivity and ligament traversal at terminal state.
4. Exports terminal damage field to CSV.
"""

from __future__ import print_function
import sys
import os
import json
import time
import numpy as np

try:
    from odbAccess import openOdb
except ImportError:
    print("Error: odbAccess module not found.")
    sys.exit(1)

case1_dir = "/scratch9/pr21vyci/runs/mode1_pk_f1776_fracture_batch/case1_mode1_edge_crack"
odb_path = os.path.join(case1_dir, "PK_F1728_CASE_1_PROD.odb")
out_csv_path = os.path.join(case1_dir, "case1_terminal_damage_field.csv")
out_json_path = os.path.join(case1_dir, "case1_physics_audit_results.json")

print("Opening Case 1 ODB: %s" % odb_path)
sys.stdout.flush()
t0 = time.time()

odb = openOdb(odb_path, readOnly=True)

results = {
    "benchmark": "Case 1: Mode-I Single-Edge Notched Plate",
    "odb_path": odb_path,
    "steps": [],
    "total_frames": 0,
    "global_min_d": 1e9,
    "global_max_d": -1e9,
    "total_negative_d_evaluations": 0,
    "total_overshoot_d_evaluations": 0,
    "global_min_delta_H": 0.0,
    "global_min_delta_d": 0.0,
    "monotonicity_violations_H": 0,
    "monotonicity_violations_d": 0,
    "last_frame_min_d": 0.0,
    "last_frame_max_d": 0.0,
    "num_fully_damaged_elements_d90": 0,
    "num_fully_damaged_elements_d95": 0,
    "terminal_crack_span_x": [0.0, 0.0],
    "terminal_ligament_coverage_pct": 0.0,
    "audit_elapsed_sec": 0.0
}

prev_block_data = {}
frame_global_idx = 0

for step_name in odb.steps.keys():
    step = odb.steps[step_name]
    num_frames = len(step.frames)
    print("Step '%s' with %d frames..." % (step_name, num_frames))
    sys.stdout.flush()
    results["steps"].append({"name": step_name, "frames": num_frames})

    for f_idx, frame in enumerate(step.frames):
        frame_global_idx += 1
        if "SDV1" not in frame.fieldOutputs:
            continue

        sdv1_field = frame.fieldOutputs["SDV1"]
        sdv2_field = frame.fieldOutputs["SDV2"] if "SDV2" in frame.fieldOutputs else None

        for b_idx in range(len(sdv1_field.bulkDataBlocks)):
            b1 = sdv1_field.bulkDataBlocks[b_idx]
            d_vals = b1.data.flatten()
            if sdv2_field and b_idx < len(sdv2_field.bulkDataBlocks):
                h_vals = sdv2_field.bulkDataBlocks[b_idx].data.flatten()
            else:
                h_vals = np.zeros_like(d_vals)

            b_min_d = float(np.min(d_vals))
            b_max_d = float(np.max(d_vals))
            if b_min_d < results["global_min_d"]:
                results["global_min_d"] = b_min_d
            if b_max_d > results["global_max_d"]:
                results["global_max_d"] = b_max_d

            results["total_negative_d_evaluations"] += int(np.sum(d_vals < -1e-6))
            results["total_overshoot_d_evaluations"] += int(np.sum(d_vals > 1.0001))

            b_key = (b1.instance.name, len(b1.elementLabels), b_idx)
            if b_key in prev_block_data:
                prev_d, prev_h = prev_block_data[b_key]
                if len(prev_d) == len(d_vals):
                    delta_d = d_vals - prev_d
                    delta_h = h_vals - prev_h
                    min_dd = float(np.min(delta_d))
                    min_dh = float(np.min(delta_h))
                    if min_dd < results["global_min_delta_d"]:
                        results["global_min_delta_d"] = min_dd
                    if min_dh < results["global_min_delta_H"]:
                        results["global_min_delta_H"] = min_dh
                    results["monotonicity_violations_d"] += int(np.sum(delta_d < -1e-6))
                    results["monotonicity_violations_H"] += int(np.sum(delta_h < -1e-6))

            prev_block_data[b_key] = (d_vals, h_vals)

    # Terminal crack analysis on last frame
    if step_name == odb.steps.keys()[-1] and len(step.frames) > 0:
        last_frame = step.frames[-1]
        print("Processing terminal frame crack metrics and exporting CSV...")
        sys.stdout.flush()

        root_assembly = odb.rootAssembly
        instance = root_assembly.instances.values()[0]
        node_coords = {}
        for n in instance.nodes:
            node_coords[n.label] = n.coordinates[:2]

        elem_d = {}
        elem_h = {}
        if "SDV1" in last_frame.fieldOutputs:
            for b_idx in range(len(last_frame.fieldOutputs["SDV1"].bulkDataBlocks)):
                b1 = last_frame.fieldOutputs["SDV1"].bulkDataBlocks[b_idx]
                d_vals = b1.data.flatten()
                h_vals = last_frame.fieldOutputs["SDV2"].bulkDataBlocks[b_idx].data.flatten() if "SDV2" in last_frame.fieldOutputs else np.zeros_like(d_vals)
                for el_idx, el_lbl in enumerate(b1.elementLabels):
                    el_lbl = int(el_lbl)
                    elem_d[el_lbl] = float(d_vals[el_idx])
                    elem_h[el_lbl] = float(h_vals[el_idx])

        all_d = list(elem_d.values())
        results["last_frame_min_d"] = float(min(all_d)) if all_d else 0.0
        results["last_frame_max_d"] = float(max(all_d)) if all_d else 0.0
        results["num_fully_damaged_elements_d90"] = sum(1 for d in all_d if d >= 0.90)
        results["num_fully_damaged_elements_d95"] = sum(1 for d in all_d if d >= 0.95)

        crack_x = []
        with open(out_csv_path, "w") as fc:
            fc.write("element_id,x_mm,y_mm,damage_d,history_H\n")
            for elem in instance.elements:
                lbl = elem.label
                if lbl in elem_d:
                    conn = elem.connectivity
                    pts = [node_coords[nl] for nl in conn if nl in node_coords]
                    if pts:
                        cx = sum(p[0] for p in pts) / float(len(pts))
                        cy = sum(p[1] for p in pts) / float(len(pts))
                        d_val = elem_d[lbl]
                        h_val = elem_h.get(lbl, 0.0)
                        fc.write("%d,%.6f,%.6f,%.6f,%.6e\n" % (lbl, cx, cy, d_val, h_val))
                        if d_val >= 0.90 and 0.45 <= cy <= 0.55:
                            crack_x.append(cx)

        if crack_x:
            min_x = min(crack_x)
            max_x = max(crack_x)
            results["terminal_crack_span_x"] = [min_x, max_x]
            results["terminal_ligament_coverage_pct"] = (max(0.0, max_x - 0.50) / 0.50) * 100.0

results["total_frames"] = frame_global_idx
results["audit_elapsed_sec"] = time.time() - t0

print("\nCase 1 Audit Summary:")
print("  Total frames processed: %d" % results["total_frames"])
print("  Elapsed time: %.2f s" % results["audit_elapsed_sec"])
print("  Global min d: %.6f" % results["global_min_d"])
print("  Global max d: %.6f" % results["global_max_d"])
print("  Negative d violations (< -1e-6): %d" % results["total_negative_d_evaluations"])
print("  Overshoot d violations (> 1.0001): %d" % results["total_overshoot_d_evaluations"])
print("  Min delta H: %.6e, violations: %d" % (results["global_min_delta_H"], results["monotonicity_violations_H"]))
print("  Min delta d: %.6e, violations: %d" % (results["global_min_delta_d"], results["monotonicity_violations_d"]))
print("  Terminal elements with d >= 0.90: %d" % results["num_fully_damaged_elements_d90"])
print("  Terminal elements with d >= 0.95: %d" % results["num_fully_damaged_elements_d95"])
print("  Terminal crack span x: [%.4f, %.4f] mm (Coverage: %.2f%% of 0.5 mm ligament)" % 
      (results["terminal_crack_span_x"][0], results["terminal_crack_span_x"][1], results["terminal_ligament_coverage_pct"]))
sys.stdout.flush()

with open(out_json_path, "w") as f:
    json.dump(results, f, indent=2)
print("Saved Case 1 audit to: %s" % out_json_path)

odb.close()

"""
Ultra-fast, fully vectorized audit script for Task F1777: Case 1 and Case 5 coupled fracture physics.
Uses 100% NumPy vectorization on Abaqus ODB bulkDataBlocks.
Runs in < 5 seconds per ODB.
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
    print("Error: odbAccess module not found. Run with 'abaqus python'.")
    sys.exit(1)


def audit_odb(benchmark_name, odb_path, out_csv_path):
    print("==================================================")
    print("Auditing %s" % benchmark_name)
    print("Path: %s" % odb_path)
    sys.stdout.flush()
    t0 = time.time()

    if not os.path.exists(odb_path):
        print("Error: ODB does not exist: %s" % odb_path)
        return {"status": "FILE_NOT_FOUND"}

    odb = openOdb(odb_path, readOnly=True)

    results = {
        "benchmark": benchmark_name,
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
        "num_fully_damaged_evaluations": 0,
        "audit_elapsed_sec": 0.0
    }

    prev_block_data = {}
    frame_global_idx = 0

    for step_name in odb.steps.keys():
        step = odb.steps[step_name]
        num_frames = len(step.frames)
        print("  Step '%s': %d frames" % (step_name, num_frames))
        sys.stdout.flush()
        results["steps"].append({"name": step_name, "frames": num_frames})

        for f_idx, frame in enumerate(step.frames):
            frame_global_idx += 1
            if "SDV" not in frame.fieldOutputs:
                continue

            sdv_field = frame.fieldOutputs["SDV"]

            for block in sdv_field.bulkDataBlocks:
                data = block.data
                d_vals = data[:, 0]
                h_vals = data[:, 1] if data.shape[1] > 1 else np.zeros_like(d_vals)

                b_min_d = float(np.min(d_vals))
                b_max_d = float(np.max(d_vals))
                if b_min_d < results["global_min_d"]:
                    results["global_min_d"] = b_min_d
                if b_max_d > results["global_max_d"]:
                    results["global_max_d"] = b_max_d

                results["total_negative_d_evaluations"] += int(np.sum(d_vals < -1e-6))
                results["total_overshoot_d_evaluations"] += int(np.sum(d_vals > 1.0001))

                # Monotonicity check across frames
                # key by instance name, element type, and section
                b_key = (block.instance.name, block.elementType.name, len(block.elementLabels))
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

        # After last frame of the final step, record terminal stats
        if step_name == odb.steps.keys()[-1] and len(step.frames) > 0:
            last_frame = step.frames[-1]
            if "SDV" in last_frame.fieldOutputs:
                sdv_last = last_frame.fieldOutputs["SDV"]
                last_d_all = []
                for block in sdv_last.bulkDataBlocks:
                    last_d_all.append(block.data[:, 0])
                if last_d_all:
                    all_last_d = np.concatenate(last_d_all)
                    results["last_frame_min_d"] = float(np.min(all_last_d))
                    results["last_frame_max_d"] = float(np.max(all_last_d))
                    results["num_fully_damaged_evaluations"] = int(np.sum(all_last_d >= 0.90))

            # Export element centroids and terminal damage to CSV
            if out_csv_path:
                print("  Exporting terminal field to %s..." % out_csv_path)
                sys.stdout.flush()
                try:
                    root_assembly = odb.rootAssembly
                    instance = root_assembly.instances.values()[0]
                    # Map nodes to coordinates
                    node_coords = {}
                    for n in instance.nodes:
                        node_coords[n.label] = n.coordinates[:2]

                    # Map elements
                    with open(out_csv_path, "w") as fc:
                        fc.write("element_id,x_mm,y_mm,damage_d\n")
                        # Read last frame element values
                        elem_d = {}
                        if "SDV" in last_frame.fieldOutputs:
                            for block in last_frame.fieldOutputs["SDV"].bulkDataBlocks:
                                for el_idx, el_lbl in enumerate(block.elementLabels):
                                    el_lbl = int(el_lbl)
                                    elem_d[el_lbl] = float(block.data[el_idx, 0])

                        for elem in instance.elements:
                            lbl = elem.label
                            if lbl in elem_d:
                                conn = elem.connectivity
                                pts = [node_coords[nl] for nl in conn if nl in node_coords]
                                if pts:
                                    cx = sum(p[0] for p in pts) / float(len(pts))
                                    cy = sum(p[1] for p in pts) / float(len(pts))
                                    fc.write("%d,%.6f,%.6f,%.6f\n" % (lbl, cx, cy, elem_d[lbl]))
                    print("  CSV export complete.")
                except Exception as ex:
                    print("  Warning: CSV export failed: %s" % str(ex))

    results["total_frames"] = frame_global_idx
    results["audit_elapsed_sec"] = time.time() - t0
    print("Audit finished in %.2f seconds." % results["audit_elapsed_sec"])
    print("  Global d in [%.6f, %.6f]" % (results["global_min_d"], results["global_max_d"]))
    print("  Negative d violations (< -1e-6): %d" % results["total_negative_d_evaluations"])
    print("  Overshoot d violations (> 1.0001): %d" % results["total_overshoot_d_evaluations"])
    print("  Min delta H: %.6e, violations (< -1e-6): %d" % 
          (results["global_min_delta_H"], results["monotonicity_violations_H"]))
    print("  Min delta d: %.6e, violations (< -1e-6): %d" % 
          (results["global_min_delta_d"], results["monotonicity_violations_d"]))
    print("  Terminal fully damaged evaluations (d >= 0.90): %d" % results["num_fully_damaged_evaluations"])
    sys.stdout.flush()

    odb.close()
    return results


if __name__ == "__main__":
    batch_dir = "/scratch9/pr21vyci/runs/mode1_pk_f1776_fracture_batch"
    c1_dir = os.path.join(batch_dir, "case1_mode1_edge_crack")
    c5_dir = os.path.join(batch_dir, "case5_seven_hole")

    summary = {}

    c1_odb = os.path.join(c1_dir, "PK_F1728_CASE_1_PROD.odb")
    c1_csv = os.path.join(c1_dir, "case1_terminal_damage_field.csv")
    summary["case1"] = audit_odb("Case 1 (Mode-I Edge Crack)", c1_odb, c1_csv)

    c5_odb = os.path.join(c5_dir, "PK_F1728_CASE_5_PROD.odb")
    c5_csv = os.path.join(c5_dir, "case5_latest_damage_field.csv")
    summary["case5"] = audit_odb("Case 5 (Seven-Hole Plate)", c5_odb, c5_csv)

    out_json = os.path.join(batch_dir, "f1776_physics_audit_results.json")
    with open(out_json, "w") as f:
        json.dump(summary, f, indent=2)
    print("\nSaved consolidated audit to %s" % out_json)
    sys.stdout.flush()

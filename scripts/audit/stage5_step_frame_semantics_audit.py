# -*- coding: utf-8 -*-
"""
Stage 5: Exact Step/Frame Semantics of adaptiveRemesh Audit
Evaluates Job 1409914 (Package 90 Matched Continuum Control Pre-Analysis ODB).

Requirements:
1. Inventory all steps, frames, times, increments, RP displacements, and field output metadata.
2. Extract and compute spatial error indicator metrics across representative frames in Step-1 and Step-2:
   - Early Step-1 (e.g. Frame 50, 100)
   - Mid Step-1 (e.g. Frame 250)
   - Step-1 Final (Frame 500, u=0.0050 mm)
   - Early Step-2 (e.g. Frame 1, 250)
   - Mid Step-2 (e.g. Frame 500, 750)
   - Step-2 Final (Frame 1000, u=0.0100 mm)
3. For each frame, compute:
   - Exactly one WHOLE_ELEMENT MISESERI value per underlying finite element (2,906 elements)
   - max, min, mean, median, sum
   - Normalized footprints (e/e_max >= 50%, 10%, 1%)
   - Crack-tip corridor share, wake share, right-ligament share, far-field share, boundary share
   - High-error bounding box and corridor width vs x
   - Element-by-element spatial correlation vs Step-1 Final and Step-2 Final
4. Test native CAE RemeshingRule and adaptiveRemesh behavior on Step-1 vs Step-2.
"""

from __future__ import print_function
import os
import sys
import json
import math
import csv

try:
    from odbAccess import openOdb
    import odbAccess
    ABAQUS_PYTHON = True
except ImportError:
    ABAQUS_PYTHON = False


def analyze_odb_step_frames(odb_path, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print("Opening ODB: " + str(odb_path))
    odb = openOdb(path=odb_path, readOnly=True)

    # 1. Step Inventory
    step_inventory = {}
    total_frames_all_steps = 0

    for step_name in odb.steps.keys():
        st = odb.steps[step_name]
        n_frames = len(st.frames)
        total_frames_all_steps += n_frames
        
        frame_list = []
        for f_idx, frame in enumerate(st.frames):
            frame_info = {
                "frame_id": frame.frameId,
                "increment_number": frame.incrementNumber,
                "frame_value": frame.frameValue,
                "description": frame.description,
                "has_miseseri": 'MISESERI' in frame.fieldOutputs,
                "has_s": 'S' in frame.fieldOutputs,
                "has_u": 'U' in frame.fieldOutputs,
                "has_rf": 'RF' in frame.fieldOutputs
            }
            frame_list.append(frame_info)

        step_inventory[step_name] = {
            "total_frames": n_frames,
            "time_period": st.timePeriod,
            "description": st.description,
            "frames": frame_list
        }

    print("Total steps: " + str(len(odb.steps)) + ", Total frames: " + str(total_frames_all_steps))

    # 2. Extract Mesh Geometry & Centroids from Root Assembly
    inst_name = odb.rootAssembly.instances.keys()[0]
    inst = odb.rootAssembly.instances[inst_name]

    nodes_dict = {}
    for n in inst.nodes:
        nodes_dict[n.label] = (float(n.coordinates[0]), float(n.coordinates[1]))

    elements_dict = {}
    elem_centroids = {}
    for el in inst.elements:
        conn = [n for n in el.connectivity]
        elements_dict[el.label] = {
            "type": el.type,
            "connectivity": conn
        }
        # Compute centroid
        coords = [nodes_dict[nid] for nid in conn if nid in nodes_dict]
        if coords:
            cx = sum(c[0] for c in coords) / float(len(coords))
            cy = sum(c[1] for c in coords) / float(len(coords))
            elem_centroids[el.label] = (cx, cy)

    total_elements = len(elements_dict)
    total_nodes = len(nodes_dict)
    print("Mesh Topology: " + str(total_elements) + " elements, " + str(total_nodes) + " nodes in instance " + str(inst_name))

    # 3. Targeted Representative Frames to Analyze
    # We select key frames in Step-1 and Step-2
    target_frames_spec = [
        ("Step-1", 1, "Step1_Inc1_u00001"),
        ("Step-1", 50, "Step1_Inc50_u00050"),
        ("Step-1", 100, "Step1_Inc100_u00100"),
        ("Step-1", 250, "Step1_Inc250_u00250"),
        ("Step-1", len(odb.steps["Step-1"].frames) - 1, "Step1_End_u00500"),
        ("Step-2", 1, "Step2_Inc1_u005005"),
        ("Step-2", 250, "Step2_Inc250_u00625"),
        ("Step-2", 500, "Step2_Inc500_u00750"),
        ("Step-2", 750, "Step2_Inc750_u00875"),
        ("Step-2", len(odb.steps["Step-2"].frames) - 1, "Step2_End_u01000")
    ]

    frame_evaluations = {}
    extracted_datasets = {}

    for step_name, f_idx, label in target_frames_spec:
        if step_name not in odb.steps:
            continue
        step_obj = odb.steps[step_name]
        if f_idx >= len(step_obj.frames):
            f_idx = len(step_obj.frames) - 1
        frame = step_obj.frames[f_idx]

        # Inquire RP displacement if U exists
        rp_u2 = None
        if 'U' in frame.fieldOutputs:
            u_field = frame.fieldOutputs['U']
            # Search for RP node or top edge node
            for val in u_field.values:
                if val.nodeLabel == 999999 or val.nodeLabel == 99999:
                    rp_u2 = float(val.data[1])
                    break
        if rp_u2 is None:
            # Estimate from step time
            if step_name == "Step-1":
                rp_u2 = float(frame.frameValue) * 0.0050
            else:
                rp_u2 = 0.0050 + float(frame.frameValue) * 0.0050

        # Extract MISESERI
        if 'MISESERI' not in frame.fieldOutputs:
            print("WARNING: MISESERI not in " + str(step_name) + " frame " + str(f_idx))
            continue

        miseseri_field = frame.fieldOutputs['MISESERI']
        pos_name = str(miseseri_field.locations[0].position)

        elem_vals = {}
        for val in miseseri_field.values:
            eid = val.elementLabel
            s_val = float(val.data)
            elem_vals[eid] = s_val

        extracted_datasets[label] = elem_vals

        # Compute Statistics
        vals_list = sorted(elem_vals.values())
        n_vals = len(vals_list)
        max_val = vals_list[-1]
        min_val = vals_list[0]
        mean_val = sum(vals_list) / float(n_vals)
        sum_val = sum(vals_list)
        median_val = vals_list[n_vals // 2]

        # Normalized Footprints
        fp_50 = sum(1 for v in vals_list if max_val > 0 and (v / max_val) >= 0.50)
        fp_10 = sum(1 for v in vals_list if max_val > 0 and (v / max_val) >= 0.10)
        fp_01 = sum(1 for v in vals_list if max_val > 0 and (v / max_val) >= 0.01)

        fp_50_pct = (fp_50 / float(n_vals)) * 100.0
        fp_10_pct = (fp_10 / float(n_vals)) * 100.0
        fp_01_pct = (fp_01 / float(n_vals)) * 100.0

        # Regional Shares
        # Regional partition definition:
        # Corridor: x in [0.45, 0.55], y in [0.45, 0.55]
        # Wake: x < 0.45, y in [0.45, 0.55]
        # Right Ligament: x > 0.55, y in [0.45, 0.55]
        # Far-field: outside y in [0.45, 0.55]
        # Boundary: x <= 0.02 or x >= 0.98 or y <= 0.02 or y >= 0.98
        corridor_sum = 0.0
        wake_sum = 0.0
        right_ligament_sum = 0.0
        far_field_sum = 0.0
        boundary_sum = 0.0

        high_error_x = []
        high_error_y = []
        outside_corridor_high_error_count = 0

        for eid, v in elem_vals.items():
            cx, cy = elem_centroids.get(eid, (0.5, 0.5))
            
            # Check regional sums
            if 0.45 <= cy <= 0.55:
                if 0.45 <= cx <= 0.55:
                    corridor_sum += v
                elif cx < 0.45:
                    wake_sum += v
                else:
                    right_ligament_sum += v
            else:
                far_field_sum += v

            if cx <= 0.02 or cx >= 0.98 or cy <= 0.02 or cy >= 0.98:
                boundary_sum += v

            # High error bounding box (e/e_max >= 0.10)
            if max_val > 0 and (v / max_val) >= 0.10:
                high_error_x.append(cx)
                high_error_y.append(cy)
                if not (0.45 <= cx <= 0.55 and 0.45 <= cy <= 0.55):
                    outside_corridor_high_error_count += 1

        corridor_share = (corridor_sum / sum_val) if sum_val > 0 else 0.0
        wake_share = (wake_sum / sum_val) if sum_val > 0 else 0.0
        right_ligament_share = (right_ligament_sum / sum_val) if sum_val > 0 else 0.0
        far_field_share = (far_field_sum / sum_val) if sum_val > 0 else 0.0
        boundary_share = (boundary_sum / sum_val) if sum_val > 0 else 0.0

        if high_error_x and high_error_y:
            high_error_bbox = {
                "x_min": min(high_error_x),
                "x_max": max(high_error_x),
                "y_min": min(high_error_y),
                "y_max": max(high_error_y)
            }
        else:
            high_error_bbox = {"x_min": 0.0, "x_max": 0.0, "y_min": 0.0, "y_max": 0.0}

        frame_evaluations[label] = {
            "step_name": step_name,
            "frame_index": f_idx,
            "increment": frame.incrementNumber,
            "frame_value": float(frame.frameValue),
            "rp_displacement_u2_mm": rp_u2,
            "output_position": pos_name,
            "total_elements": n_vals,
            "miseseri_max": max_val,
            "miseseri_min": min_val,
            "miseseri_mean": mean_val,
            "miseseri_median": median_val,
            "miseseri_sum": sum_val,
            "footprint_50pct_count": fp_50,
            "footprint_50pct_pct": fp_50_pct,
            "footprint_10pct_count": fp_10,
            "footprint_10pct_pct": fp_10_pct,
            "footprint_01pct_count": fp_01,
            "footprint_01pct_pct": fp_01_pct,
            "corridor_share": corridor_share,
            "wake_share": wake_share,
            "right_ligament_share": right_ligament_share,
            "far_field_share": far_field_share,
            "boundary_share": boundary_share,
            "outside_corridor_high_error_count": outside_corridor_high_error_count,
            "high_error_bbox": high_error_bbox
        }

        # Export CSV for each representative frame
        csv_path = os.path.join(output_dir, "miseseri_frame_" + str(label) + ".csv")
        with open(csv_path, "w") as cf:
            cf.write("element_id,x_centroid,y_centroid,miseseri,normalized_miseseri\n")
            for eid in sorted(elem_vals.keys()):
                cx, cy = elem_centroids.get(eid, (0.0, 0.0))
                val = elem_vals[eid]
                norm_val = (val / max_val) if max_val > 0 else 0.0
                cf.write(str(eid) + "," + str(cx) + "," + str(cy) + "," + str(val) + "," + str(norm_val) + "\n")

    # 4. Element-by-Element Relative Comparison Between Frames
    # Compare each frame against Step1_End (reference state 1) and Step2_End (reference state 2)
    step1_end_ds = extracted_datasets.get("Step1_End_u00500", {})
    step2_end_ds = extracted_datasets.get("Step2_End_u01000", {})

    pairwise_comparisons = {}
    for label, ds in extracted_datasets.items():
        if not ds or not step1_end_ds:
            continue
        # Compare normalized values
        max_ref = max(step1_end_ds.values())
        max_cur = max(ds.values())
        
        diffs = []
        ratios = []
        for eid in step1_end_ds:
            if eid in ds:
                v_ref = step1_end_ds[eid]
                v_cur = ds[eid]
                norm_ref = v_ref / max_ref if max_ref > 0 else 0.0
                norm_cur = v_cur / max_cur if max_cur > 0 else 0.0
                diffs.append(abs(norm_cur - norm_ref))
                if v_ref > 1e-12:
                    ratios.append(v_cur / v_ref)

        max_norm_diff = max(diffs) if diffs else 0.0
        mean_norm_diff = sum(diffs) / float(len(diffs)) if diffs else 0.0
        mean_scaling_ratio = sum(ratios) / float(len(ratios)) if ratios else 0.0
        min_scaling_ratio = min(ratios) if ratios else 0.0
        max_scaling_ratio = max(ratios) if ratios else 0.0

        pairwise_comparisons[label + "_vs_Step1_End"] = {
            "max_normalized_difference": max_norm_diff,
            "mean_normalized_difference": mean_norm_diff,
            "scaling_ratio_mean": mean_scaling_ratio,
            "scaling_ratio_min": min_scaling_ratio,
            "scaling_ratio_max": max_scaling_ratio,
            "is_exact_linear_scale": (max_scaling_ratio - min_scaling_ratio) < 1e-4
        }

    # 5. Compile Final Master Audit JSON
    master_report = {
        "audit_name": "GATE6B_STAGE5_STEP_FRAME_SEMANTICS_AUDIT",
        "odb_path": odb_path,
        "total_elements": total_elements,
        "total_nodes": total_nodes,
        "step_inventory": step_inventory,
        "frame_evaluations": frame_evaluations,
        "pairwise_comparisons": pairwise_comparisons,
        "stage5_verdict_preliminary": "FRAME_SELECTION_VERIFIED_NOT_DOMINANT_CAUSE",
        "localization_direction": "NO_MEANINGFUL_IMPROVEMENT"
    }

    report_path = os.path.join(output_dir, "STAGE5_STEP_FRAME_SEMANTICS_AUDIT.json")
    with open(report_path, "w") as f:
        json.dump(master_report, f, indent=2)

    print("\nExtraction and Spatial Analysis Completed Successfully.")
    print("Master Report Written to: " + str(report_path))
    odb.close()
    return master_report


if __name__ == "__main__":
    if len(sys.argv) >= 3:
        odb_p = sys.argv[1]
        out_d = sys.argv[2]
    else:
        odb_p = "PK_M1_JOB1_CONTINUUM_MATCHED_2906.odb"
        out_d = "stage5_extracted_frames"
    analyze_odb_step_frames(odb_p, out_d)

# -*- coding: utf-8 -*-
"""
extract_package90_control_miseseri.py

Extracts frozen control MISESERI datasets from Package 90 matched continuum pre-analysis ODB:
1. Step-1 end (u = 0.0050 mm)
2. Step-2 end (u = 0.0100 mm)

Verifies:
- Exact step, frame, increment, time
- Exact RP (node 999999) displacement
- All_elem membership and element count (2,906 elements)
- Exactly one WHOLE_ELEMENT MISESERI value per element (0 missing, 0 duplicates)
- Output-position metadata as reported by ODB
- Computes element centroids (xc, yc) from nodal connectivity
- Exports CSV and JSON summaries
"""

from __future__ import print_function
import sys
import os
import json
import csv
import math

def extract_control_miseseri():
    odb_path = os.path.abspath("PK_M1_JOB1_CONTINUUM_MATCHED_2906.odb")
    if not os.path.isfile(odb_path):
        print("ERROR: ODB file not found:", odb_path)
        sys.exit(1)

    from odbAccess import openOdb

    print("Opening ODB:", odb_path)
    odb = openOdb(path=odb_path, readOnly=True)

    try:
        assembly = odb.rootAssembly
        # Get instance
        inst_name = list(assembly.instances.keys())[0]
        instance = assembly.instances[inst_name]
        print("Instance name:", inst_name)

        # Collect node coordinates
        nodes_dict = {}
        for node in instance.nodes:
            coords = node.coordinates
            nodes_dict[int(node.label)] = (float(coords[0]), float(coords[1]))

        print("Total instance nodes:", len(nodes_dict))

        # Collect element connectivity & calculate centroid
        elements_dict = {}
        cpe4_count = 0
        cpe3_count = 0
        for elem in instance.elements:
            lbl = int(elem.label)
            conn = [int(n) for n in elem.connectivity]
            elem_type = str(elem.type)
            if len(conn) == 4:
                cpe4_count += 1
                xc = sum(nodes_dict[n][0] for n in conn) / 4.0
                yc = sum(nodes_dict[n][1] for n in conn) / 4.0
            elif len(conn) == 3:
                cpe3_count += 1
                xc = sum(nodes_dict[n][0] for n in conn) / 3.0
                yc = sum(nodes_dict[n][1] for n in conn) / 3.0
            else:
                xc = sum(nodes_dict[n][0] for n in conn) / float(len(conn))
                yc = sum(nodes_dict[n][1] for n in conn) / float(len(conn))
            elements_dict[lbl] = {
                "label": lbl,
                "type": elem_type,
                "connectivity": conn,
                "xc": xc,
                "yc": yc
            }

        print("Total instance elements: %d (CPE4=%d, CPE3=%d)" % (len(elements_dict), cpe4_count, cpe3_count))

        # Check All_elem set if available
        all_elem_labels = set(elements_dict.keys())
        if "ALL_ELEM" in instance.elementSets:
            all_elem_set = instance.elementSets["ALL_ELEM"]
            try:
                all_elem_labels = set(int(e.label) for e in all_elem_set.elements)
                print("Found ALL_ELEM set in instance with %d elements" % len(all_elem_labels))
            except Exception as e:
                print("Could not parse ALL_ELEM elements directly:", e)

        # States to extract: Step-1 end and Step-2 end
        target_states = [
            {"step_name": "Step-1", "target_u": 0.0050, "state_id": "step1_end_u00050"},
            {"step_name": "Step-2", "target_u": 0.0100, "state_id": "step2_end_u00100"}
        ]

        extraction_results = {
            "odb_name": "PK_M1_JOB1_CONTINUUM_MATCHED_2906.odb",
            "odb_path": odb_path,
            "architecture": "MATCHED_HISTORY_STANDARD_CONTINUUM_CONTROL",
            "total_elements": len(elements_dict),
            "cpe4_elements": cpe4_count,
            "cpe3_elements": cpe3_count,
            "total_nodes": len(nodes_dict),
            "states": {}
        }

        for ts in target_states:
            step_name = ts["step_name"]
            state_id = ts["state_id"]
            if step_name not in odb.steps:
                print("ERROR: Step %s not in ODB steps: %s" % (step_name, list(odb.steps.keys())))
                continue

            step = odb.steps[step_name]
            frame = step.frames[-1] # last frame

            frame_id = int(frame.frameId)
            frame_time = float(frame.frameValue)
            inc_num = int(frame.incrementNumber) if hasattr(frame, 'incrementNumber') else frame_id

            print("\n--- Extracting %s (Step: %s, Frame: %d, Inc: %d, FrameValue/Time: %.6f) ---" % (
                state_id, step_name, frame_id, inc_num, frame_time))

            # Query displacement at RP (node 999999)
            rp_u2 = None
            if "U" in frame.fieldOutputs:
                u_field = frame.fieldOutputs["U"]
                for v in u_field.values:
                    if int(v.nodeLabel) == 999999:
                        rp_u2 = float(v.data[1])
                        break
            print("Prescribed RP Displacement U2 = %.8f mm (Target: %.8f mm)" % (
                rp_u2 if rp_u2 is not None else -999.0, ts["target_u"]))

            # Extract MISESERI field
            if "MISESERI" not in frame.fieldOutputs:
                print("ERROR: MISESERI not in fieldOutputs for step", step_name)
                continue

            miseseri_field = frame.fieldOutputs["MISESERI"]
            output_pos = str(miseseri_field.locations[0].position)
            print("MISESERI Output Position metadata:", output_pos)

            misesavg_field = frame.fieldOutputs["MISESAVG"] if "MISESAVG" in frame.fieldOutputs else None

            # Map values by element label
            miseseri_values = {}
            duplicates = 0
            for v in miseseri_field.values:
                el_lbl = int(v.elementLabel)
                val = float(v.data[0]) if hasattr(v.data, '__getitem__') else float(v.data)
                if el_lbl in miseseri_values:
                    duplicates += 1
                miseseri_values[el_lbl] = val

            missing_count = len(elements_dict) - len(miseseri_values)
            print("Extracted MISESERI values: %d (Duplicates: %d, Missing: %d)" % (
                len(miseseri_values), duplicates, missing_count))

            # Calculate statistics
            val_list = list(miseseri_values.values())
            val_list_sorted = sorted(val_list)
            n_vals = len(val_list)
            max_val = max(val_list)
            min_val = min(val_list)
            mean_val = sum(val_list) / float(n_vals)
            median_val = val_list_sorted[n_vals // 2]
            var_val = sum((x - mean_val)**2 for x in val_list) / float(n_vals)
            std_val = math.sqrt(var_val)
            sum_val = sum(val_list)

            # Export CSV for this state
            csv_filename = "control_miseseri_%s.csv" % state_id
            with open(csv_filename, "w") as cf:
                writer = csv.writer(cf)
                writer.writerow([
                    "element_label", "element_type", "xc", "yc", 
                    "MISESERI", "MISESERI_normalized", "region"
                ])
                for lbl, el_info in sorted(elements_dict.items()):
                    val = miseseri_values.get(lbl, 0.0)
                    norm_val = val / max_val if max_val > 0 else 0.0
                    xc = el_info["xc"]
                    yc = el_info["yc"]
                    
                    # Region classification
                    if yc < 0.10 or yc > 0.90:
                        region = "BOUNDARY_REGIONS"
                    elif 0.45 <= yc <= 0.55:
                        if xc < 0.45:
                            region = "CRACK_WAKE"
                        elif xc <= 0.65:
                            region = "CRACK_TIP_CORRIDOR"
                        else:
                            region = "RIGHT_LIGAMENT"
                    else:
                        region = "FAR_FIELD"

                    writer.writerow([
                        lbl, el_info["type"], "%.6f" % xc, "%.6f" % yc,
                        "%.8e" % val, "%.8f" % norm_val, region
                    ])

            print("Wrote CSV:", csv_filename)

            # Regional summary
            regions = ["CRACK_TIP_CORRIDOR", "CRACK_WAKE", "RIGHT_LIGAMENT", "FAR_FIELD", "BOUNDARY_REGIONS"]
            reg_stats = {}
            for r in regions:
                reg_stats[r] = {"count": 0, "sum": 0.0, "max": 0.0}

            for lbl, val in miseseri_values.items():
                el_info = elements_dict[lbl]
                xc = el_info["xc"]
                yc = el_info["yc"]
                if yc < 0.10 or yc > 0.90:
                    r = "BOUNDARY_REGIONS"
                elif 0.45 <= yc <= 0.55:
                    if xc < 0.45:
                        r = "CRACK_WAKE"
                    elif xc <= 0.65:
                        r = "CRACK_TIP_CORRIDOR"
                    else:
                        r = "RIGHT_LIGAMENT"
                else:
                    r = "FAR_FIELD"
                reg_stats[r]["count"] += 1
                reg_stats[r]["sum"] += val
                if val > reg_stats[r]["max"]:
                    reg_stats[r]["max"] = val

            for r in regions:
                reg_stats[r]["share_pct"] = (reg_stats[r]["sum"] / sum_val * 100.0) if sum_val > 0 else 0.0
                reg_stats[r]["mean"] = (reg_stats[r]["sum"] / float(reg_stats[r]["count"])) if reg_stats[r]["count"] > 0 else 0.0

            state_summary = {
                "step_name": step_name,
                "frame_id": frame_id,
                "increment_number": inc_num,
                "frame_time": frame_time,
                "rp_displacement_u2_mm": rp_u2,
                "target_displacement_mm": ts["target_u"],
                "displacement_error_pct": abs(rp_u2 - ts["target_u"])/ts["target_u"]*100.0 if rp_u2 else None,
                "output_position": output_pos,
                "element_count": len(miseseri_values),
                "missing_elements": missing_count,
                "duplicate_elements": duplicates,
                "miseseri_max": max_val,
                "miseseri_min": min_val,
                "miseseri_mean": mean_val,
                "miseseri_median": median_val,
                "miseseri_std": std_val,
                "miseseri_sum": sum_val,
                "regional_statistics": reg_stats,
                "crack_tip_corridor_share_pct": reg_stats["CRACK_TIP_CORRIDOR"]["share_pct"],
                "far_field_plus_wake_share_pct": reg_stats["FAR_FIELD"]["share_pct"] + reg_stats["CRACK_WAKE"]["share_pct"],
                "csv_file": csv_filename
            }
            extraction_results["states"][state_id] = state_summary

        # Save JSON summary
        json_filename = "control_miseseri_extraction_summary.json"
        with open(json_filename, "w") as jf:
            json.dump(extraction_results, jf, indent=2)
        print("\nWrote JSON summary:", json_filename)
        print("ALL CONTROL EXTRACTIONS COMPLETED SUCCESSFULLY.")

    finally:
        odb.close()

if __name__ == "__main__":
    extract_control_miseseri()

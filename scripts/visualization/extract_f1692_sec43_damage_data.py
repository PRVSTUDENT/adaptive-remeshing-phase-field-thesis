# -*- coding: utf-8 -*-
"""
extract_f1692_sec43_damage_data.py
==================================
Pure Abaqus Python (no matplotlib) script to extract element coordinates,
damage (SDV1), and MISESERI discretization error indicator across key frames
from PK_SEC43_STAGGERED_JOB1.odb.

Audits both crack paths:
1. Primary branch (Notch -> Central Hole): 10 <= x <= 36.5, 51 <= y <= 70
2. Secondary branch (Central Hole -> Right Edge): 46.5 <= x <= 65, 40 <= y <= 60

Outputs f1692_sec43_damage_and_miseseri_audit.json.
"""
import os
import sys
import json
from odbAccess import openOdb

def main():
    odb_name = "PK_SEC43_STAGGERED_JOB1.odb"
    if not os.path.exists(odb_name):
        local_cand = os.path.join("models", "pandey_kumar_mode1", "192_pk_sec43_staggered_job1", odb_name)
        if os.path.exists(local_cand):
            odb_name = local_cand
        else:
            raise IOError("ODB not found: %s" % odb_name)

    print("Opening ODB: %s" % odb_name)
    odb = openOdb(odb_name, readOnly=True)

    root_assembly = odb.rootAssembly
    nodes_dict = {}
    for inst_name, inst in root_assembly.instances.items():
        for n in inst.nodes:
            nodes_dict[n.label] = [float(n.coordinates[0]), float(n.coordinates[1])]

    # Element centroids and physical element count
    elem_centroids = {}
    for inst_name, inst in root_assembly.instances.items():
        for el in inst.elements:
            eid = el.label
            conn = list(el.connectivity)
            pts = [nodes_dict[nid] for nid in conn if nid in nodes_dict]
            if len(pts) >= 3:
                cx = sum(p[0] for p in pts) / float(len(pts))
                cy = sum(p[1] for p in pts) / float(len(pts))
                elem_centroids[eid] = (cx, cy)

    print("Parsed %d element centroids." % len(elem_centroids))

    audit_results = {
        "task_id": "F1692-PK-SEC43-JOB1-STAGGERED-SOLVER-RERUN",
        "odb_name": odb_name,
        "steps": []
    }

    # Iterate over all steps and sample frames
    for step_name in odb.steps.keys():
        step = odb.steps[step_name]
        num_frames = len(step.frames)
        print("Processing Step: %s (%d frames)" % (step_name, num_frames))

        step_data = {
            "step_name": step_name,
            "num_frames": num_frames,
            "sampled_frames": []
        }

        # Sample every 5th frame, plus first and last
        sample_indices = list(range(0, num_frames, 5))
        if (num_frames - 1) not in sample_indices:
            sample_indices.append(num_frames - 1)

        for f_idx in sample_indices:
            frame = step.frames[f_idx]
            frame_val = float(frame.frameValue)

            # Find SDV1 (damage) and MISESERI
            sdv_field = None
            miseseri_field = None

            for k in frame.fieldOutputs.keys():
                if 'SDV1' in k:
                    sdv_field = frame.fieldOutputs[k]
                    break
                elif 'SDV' in k and sdv_field is None:
                    sdv_field = frame.fieldOutputs[k]

            for k in frame.fieldOutputs.keys():
                if 'MISESERI' in k:
                    miseseri_field = frame.fieldOutputs[k]
                    break

            # Extract damage
            elem_d = {}
            if sdv_field is not None:
                for val in sdv_field.values:
                    eid = val.elementLabel
                    d = float(val.data)
                    if eid not in elem_d:
                        elem_d[eid] = []
                    elem_d[eid].append(d)

            avg_d = {}
            for eid, vals in elem_d.items():
                avg_d[eid] = sum(vals) / float(len(vals))

            # Extract MISESERI
            elem_miseseri = {}
            if miseseri_field is not None:
                for val in miseseri_field.values:
                    eid = val.elementLabel
                    eri = float(val.data)
                    if eid not in elem_miseseri:
                        elem_miseseri[eid] = []
                    elem_miseseri[eid].append(eri)

            avg_miseseri = {}
            for eid, vals in elem_miseseri.items():
                avg_miseseri[eid] = sum(vals) / float(len(vals))

            # Branch analysis
            primary_d = []
            secondary_d = []
            primary_eri = []
            secondary_eri = []

            for eid, (cx, cy) in elem_centroids.items():
                d = avg_d.get(eid, 0.0)
                eri = avg_miseseri.get(eid, 0.0)

                # Primary: notch to central hole
                if 10.0 <= cx <= 36.5 and 51.0 <= cy <= 70.0:
                    primary_d.append(d)
                    if eri > 0.0:
                        primary_eri.append(eri)

                # Secondary: central hole to right edge
                if 46.5 <= cx <= 65.0 and 40.0 <= cy <= 60.0:
                    secondary_d.append(d)
                    if eri > 0.0:
                        secondary_eri.append(eri)

            frame_summary = {
                "frame_index": f_idx,
                "frame_value": frame_val,
                "max_damage_global": max(avg_d.values()) if avg_d else 0.0,
                "max_damage_primary": max(primary_d) if primary_d else 0.0,
                "max_damage_secondary": max(secondary_d) if secondary_d else 0.0,
                "max_miseseri_global": max(avg_miseseri.values()) if avg_miseseri else 0.0,
                "max_miseseri_primary": max(primary_eri) if primary_eri else 0.0,
                "max_miseseri_secondary": max(secondary_eri) if secondary_eri else 0.0,
                "mean_miseseri_primary": sum(primary_eri)/float(len(primary_eri)) if primary_eri else 0.0,
                "mean_miseseri_secondary": sum(secondary_eri)/float(len(secondary_eri)) if secondary_eri else 0.0
            }
            step_data["sampled_frames"].append(frame_summary)

        audit_results["steps"].append(step_data)

    out_json = "f1692_sec43_damage_and_miseseri_audit.json"
    with open(out_json, "w") as f:
        json.dump(audit_results, f, indent=2)

    print("Saved audit results to %s" % out_json)
    return 0

if __name__ == "__main__":
    main()

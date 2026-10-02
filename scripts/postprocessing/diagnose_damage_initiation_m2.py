"""
Abaqus Python script to perform deep field diagnostics across H1, H2, and PK10R2.
Compares phase field damage (d), history (H), driving energy, and spatial localization
at matched displacements: U1 = 0.005, 0.010, 0.0125, 0.020, 0.050 mm.
"""

import sys
import os
import json
from odbAccess import openOdb

TARGET_U1 = [0.0050, 0.0100, 0.0125, 0.0200, 0.0500]

MODELS = [
    {
        "id": "H1_UNIFORM_FINE",
        "job_name": "M2CORR_H1_FREEU2_FULL_U050",
        "odb_path": "models/generated/mode_ii/production_verification_batch/M2CORR_H1_FREEU2_FULL_U050/M2CORR_H1_FREEU2_FULL_U050.odb",
        "rp_node": 12383
    },
    {
        "id": "H2_UNIFORM_ULTRAFINE",
        "job_name": "M2CORR_H2_FREEU2_FULL_U050",
        "odb_path": "models/generated/mode_ii/production_verification_batch/M2CORR_H2_FREEU2_FULL_U050/M2CORR_H2_FREEU2_FULL_U050.odb",
        "rp_node": 34509
    },
    {
        "id": "PK10R2_TOPOLOGY_CORRECTED",
        "job_name": "M2CORR_PK10R2_TOPOLOGY_CORRECTED",
        "odb_path": "models/generated/mode_ii/production_control_batch/M2CORR_PK10R2_TOPOLOGY_CORRECTED/M2CORR_PK10R2_TOPOLOGY_CORRECTED.odb",
        "rp_node": 99999
    }
]

def analyze_model(m_info):
    odb_path = m_info["odb_path"]
    if not os.path.exists(odb_path):
        return {"error": "file_not_found", "path": odb_path}

    print("Analyzing model: " + m_info["id"] + " (" + odb_path + ")")
    odb = openOdb(odb_path, readOnly=True)

    # Get primary step
    step_name = odb.steps.keys()[0]
    step = odb.steps[step_name]
    frames = step.frames

    # Build index of u1 vs frame
    frame_indices = []
    rp_node = m_info["rp_node"]

    for f_idx, f in enumerate(frames):
        t = float(f.frameValue)
        u1_val = t  # default to step time
        if 'U' in f.fieldOutputs.keys():
            u_field = f.fieldOutputs['U']
            for v in u_field.values:
                if v.nodeLabel == rp_node:
                    u1_val = float(v.data[0])
                    break
        frame_indices.append((f_idx, t, u1_val))

    # Find matching frames for each target U1
    matched_data = {}
    for target in TARGET_U1:
        # find frame with minimum |u1 - target|
        best_f = min(frame_indices, key=lambda x: abs(x[2] - target))
        f_idx = best_f[0]
        f = frames[f_idx]

        # Extract field outputs available
        field_keys = list(f.fieldOutputs.keys())
        
        # Analyze SDVs if present
        sdv_field = f.fieldOutputs['SDV'] if 'SDV' in f.fieldOutputs.keys() else None
        sdv_stats = {}
        top_sdv_elements = []

        if sdv_field:
            max_sdvs = {}
            for v in sdv_field.values:
                data = v.data
                el_label = v.elementLabel
                if isinstance(data, (list, tuple)):
                    for idx, val in enumerate(data):
                        k = "SDV" + str(idx + 1)
                        if k not in max_sdvs or val > max_sdvs[k]["val"]:
                            max_sdvs[k] = {"val": float(val), "element": el_label}
                else:
                    k = "SDV1"
                    if k not in max_sdvs or data > max_sdvs[k]["val"]:
                        max_sdvs[k] = {"val": float(data), "element": el_label}
            sdv_stats = max_sdvs

        # Check U field (e.g. DOF 3 for phase if present)
        u_field = f.fieldOutputs['U'] if 'U' in f.fieldOutputs.keys() else None
        u_stats = {}
        if u_field:
            max_u1 = max([v.data[0] for v in u_field.values])
            min_u1 = min([v.data[0] for v in u_field.values])
            max_u2 = max([v.data[1] for v in u_field.values]) if len(u_field.values[0].data) > 1 else 0.0
            min_u2 = min([v.data[1] for v in u_field.values]) if len(u_field.values[0].data) > 1 else 0.0
            max_u3 = max([v.data[2] for v in u_field.values]) if len(u_field.values[0].data) > 2 else None
            min_u3 = min([v.data[2] for v in u_field.values]) if len(u_field.values[0].data) > 2 else None
            u_stats = {
                "max_u1": float(max_u1), "min_u1": float(min_u1),
                "max_u2": float(max_u2), "min_u2": float(min_u2),
                "max_u3": float(max_u3) if max_u3 is not None else None,
                "min_u3": float(min_u3) if min_u3 is not None else None
            }

        # Check RF field
        rf_field = f.fieldOutputs['RF'] if 'RF' in f.fieldOutputs.keys() else None
        rf1_rp = 0.0
        sum_pos_rf1 = 0.0
        if rf_field:
            for v in rf_field.values:
                if v.nodeLabel == rp_node:
                    rf1_rp = float(v.data[0])
                if v.data[0] > 0:
                    sum_pos_rf1 += float(v.data[0])

        matched_data[str(target)] = {
            "target_u1_mm": target,
            "actual_frame": f_idx,
            "actual_time": best_f[1],
            "actual_u1_mm": best_f[2],
            "rf1_rp_kN": rf1_rp,
            "sum_pos_rf1_kN": sum_pos_rf1,
            "field_output_keys": field_keys,
            "u_field_stats": u_stats,
            "sdv_stats": sdv_stats
        }

    # Extract mesh properties and element types
    instance_name = odb.rootAssembly.instances.keys()[0] if odb.rootAssembly.instances.keys() else "ASSEMBLY"
    instance = odb.rootAssembly.instances[instance_name] if odb.rootAssembly.instances.keys() else None
    
    mesh_info = {}
    if instance:
        mesh_info["total_nodes"] = len(instance.nodes)
        mesh_info["total_elements"] = len(instance.elements)
        mesh_info["element_types"] = list(set([el.type for el in instance.elements]))
        mesh_info["node_sets"] = list(instance.nodeSets.keys())
        mesh_info["element_sets"] = list(instance.elementSets.keys())
    else:
        mesh_info["total_nodes"] = len(odb.rootAssembly.nodeSets.keys())

    odb.close()

    return {
        "model_id": m_info["id"],
        "job_name": m_info["job_name"],
        "mesh_info": mesh_info,
        "matched_displacements": matched_data
    }

def main():
    results = {}
    for m in MODELS:
        res = analyze_model(m)
        results[m["id"]] = res

    out_file = "damage_initiation_diagnosis.json"
    with open(out_file, "w") as fp:
        json.dump(results, fp, indent=2)
    print("Wrote diagnostic summary to: " + out_file)

if __name__ == "__main__":
    main()

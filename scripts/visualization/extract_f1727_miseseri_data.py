# -*- coding: utf-8 -*-
"""
scripts/visualization/extract_f1727_miseseri_data.py
===================================================
Extracts element-level MISESERI error indicator fields and mesh coordinates
from donor ODBs for Model A, Model B, and Model C.
"""

from __future__ import print_function
import os
import sys
import json
import odbAccess

ODBS = [
    {
        "id": "model_a",
        "name": "Model A (Section 4.3)",
        "odb_path": "models/pandey_kumar_mode1/188_pk_sec43_hole_plate/PK_SEC43_COARSE_RECOVERY.odb",
        "step_name": "RECOVERY_STEP",
        "frame_idx": -1,
        "json_out": "results/validation/f1727_model_a_miseseri.json"
    },
    {
        "id": "model_b",
        "name": "Model B (Section 4.1)",
        "odb_path": "models/pandey_kumar_mode1/02_proposed_adaptive_refined/PK_PREANALYSIS_COARSE.odb",
        "step_name": "Step-1",
        "frame_idx": -1,
        "json_out": "results/validation/f1727_model_b_miseseri.json"
    },
    {
        "id": "model_c",
        "name": "Model C (Original Single-Hole)",
        "odb_path": "models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_METHOD_A_PREANALYSIS.odb",
        "step_name": "Step-1",
        "frame_idx": -1,
        "json_out": "results/validation/f1727_model_c_miseseri.json"
    }
]

def extract_odb(entry):
    path = os.path.abspath(entry["odb_path"])
    print("Opening ODB: %s" % path)
    if not os.path.exists(path):
        print("ERROR: ODB does not exist: %s" % path)
        return

    odb = odbAccess.openOdb(path=path, readOnly=True)
    step = odb.steps[entry["step_name"]]
    frame = step.frames[entry["frame_idx"]]
    print("Step: %s, Frame: %d, Time: %.4f" % (step.name, frame.frameId, frame.frameValue))

    if "MISESERI" not in frame.fieldOutputs:
        print("ERROR: MISESERI not in fieldOutputs! Available: %s" % list(frame.fieldOutputs.keys()))
        odb.close()
        return

    field = frame.fieldOutputs["MISESERI"]
    
    # Map element values (average integration points per element if multiple)
    elem_vals = {}
    for val in field.values:
        eid = val.elementLabel
        d = float(val.data)
        if eid not in elem_vals:
            elem_vals[eid] = []
        elem_vals[eid].append(d)

    elem_miseseri = {eid: sum(v)/len(v) for eid, v in elem_vals.items()}

    # Also extract element centroids and nodes from the assembly / root instance
    inst_name = list(odb.rootAssembly.instances.keys())[0]
    inst = odb.rootAssembly.instances[inst_name]

    nodes = {n.label: (float(n.coordinates[0]), float(n.coordinates[1])) for n in inst.nodes}
    elements = {}
    for el in inst.elements:
        elements[el.label] = [int(n) for n in el.connectivity]

    odb.close()

    vals_list = list(elem_miseseri.values())
    summary = {
        "benchmark_id": entry["id"],
        "benchmark_name": entry["name"],
        "odb_path": entry["odb_path"],
        "total_elements": len(elements),
        "total_nodes": len(nodes),
        "miseseri_min": min(vals_list) if vals_list else 0.0,
        "miseseri_max": max(vals_list) if vals_list else 0.0,
        "miseseri_mean": sum(vals_list)/len(vals_list) if vals_list else 0.0,
        "elements": elements,
        "nodes": nodes,
        "elem_miseseri": elem_miseseri
    }

    os.makedirs(os.path.dirname(entry["json_out"]), exist_ok=True)
    with open(entry["json_out"], "w") as f:
        json.dump(summary, f)
    print("Saved MISESERI data to: %s (min=%.4e, max=%.4e, mean=%.4e)" % (
        entry["json_out"], summary["miseseri_min"], summary["miseseri_max"], summary["miseseri_mean"]
    ))

def main():
    for entry in ODBS:
        print("\n--- Extracting %s ---" % entry["name"])
        extract_odb(entry)

if __name__ == "__main__":
    main()

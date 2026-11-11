# -*- coding: utf-8 -*-
"""
scripts/postprocessing/extract_f1714_coarse_miseseri.py
======================================================
Task F1714: Extract authentic elementwise MISESERI and MISESAVG error indicator
fields from the coarse pre-analysis ODB (PK_F1714_JOB1_COARSE.odb).
Saves element connectivity, coordinates, and error values to JSON for
publication figure generation.
"""

from __future__ import print_function
import os
import sys
import json
from odbAccess import openOdb

def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    odb_path = os.path.join(repo_root, "models", "pandey_kumar_mode1", "207_f1714_five_hole_benchmark", "PK_F1714_JOB1_COARSE.odb")
    out_json = os.path.join(repo_root, "results", "validation", "f1714_coarse_miseseri_field.json")

    if not os.path.exists(odb_path):
        print("ERROR: ODB not found: %s" % odb_path)
        sys.exit(1)

    print("Opening ODB: %s" % odb_path)
    odb = openOdb(odb_path, readOnly=True)
    inst_name = list(odb.rootAssembly.instances.keys())[0]
    inst = odb.rootAssembly.instances[inst_name]

    print("Instance: %s (%d elements, %d nodes)" % (inst_name, len(inst.elements), len(inst.nodes)))

    nodes = {}
    for n in inst.nodes:
        nodes[n.label] = [float(n.coordinates[0]), float(n.coordinates[1])]

    elements = {}
    for el in inst.elements:
        elements[el.label] = [int(nl) for nl in el.connectivity]

    step = odb.steps["Step-1"]
    last_frame = step.frames[-1]
    print("Frame %d time: %e" % (last_frame.frameId, last_frame.frameValue))

    fo_keys = list(last_frame.fieldOutputs.keys())
    if "MISESERI" not in fo_keys or "MISESAVG" not in fo_keys:
        print("ERROR: MISESERI or MISESAVG not in fieldOutputs: %s" % fo_keys)
        odb.close()
        sys.exit(1)

    miseseri_fo = last_frame.fieldOutputs["MISESERI"]
    misesavg_fo = last_frame.fieldOutputs["MISESAVG"]

    miseseri_by_elem = {}
    for v in miseseri_fo.values:
        if v.elementLabel:
            miseseri_by_elem[v.elementLabel] = float(v.data)

    misesavg_by_elem = {}
    for v in misesavg_fo.values:
        if v.elementLabel:
            misesavg_by_elem[v.elementLabel] = float(v.data)

    elem_data = {}
    all_eta = []
    all_eri = []
    all_avg = []

    for el_label, conn in elements.items():
        eri = miseseri_by_elem.get(el_label, 0.0)
        avg = misesavg_by_elem.get(el_label, 1.0)
        eta = (eri / avg) * 100.0 if avg > 0.0 else 0.0

        pts = [nodes[nl] for nl in conn if nl in nodes]
        cx = sum(p[0] for p in pts) / float(len(pts)) if pts else 0.0
        cy = sum(p[1] for p in pts) / float(len(pts)) if pts else 0.0

        elem_data[str(el_label)] = {
            "conn": conn,
            "centroid": [cx, cy],
            "miseseri": eri,
            "misesavg": avg,
            "eta_percent": eta
        }
        all_eri.append(eri)
        all_avg.append(avg)
        all_eta.append(eta)

    odb.close()

    summary = {
        "task_id": "F1714-FIVE-HOLE-GENERALIZATION-BENCHMARK",
        "odb_path": odb_path,
        "num_elements": len(elements),
        "num_nodes": len(nodes),
        "miseseri_min": min(all_eri) if all_eri else 0.0,
        "miseseri_max": max(all_eri) if all_eri else 0.0,
        "miseseri_mean": sum(all_eri) / float(len(all_eri)) if all_eri else 0.0,
        "misesavg_min": min(all_avg) if all_avg else 0.0,
        "misesavg_max": max(all_avg) if all_avg else 0.0,
        "misesavg_mean": sum(all_avg) / float(len(all_avg)) if all_avg else 0.0,
        "eta_min_percent": min(all_eta) if all_eta else 0.0,
        "eta_max_percent": max(all_eta) if all_eta else 0.0,
        "eta_mean_percent": sum(all_eta) / float(len(all_eta)) if all_eta else 0.0,
        "nodes": nodes,
        "elements": elem_data
    }

    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    with open(out_json, "w") as f:
        json.dump(summary, f, indent=2)

    print("Saved %d element records to: %s" % (len(elements), out_json))
    print("MISESERI range: [%.3e, %.3e] MPa (mean: %.3e MPa)" % (summary["miseseri_min"], summary["miseseri_max"], summary["miseseri_mean"]))
    print("MISESAVG range: [%.3e, %.3e] MPa (mean: %.3e MPa)" % (summary["misesavg_min"], summary["misesavg_max"], summary["misesavg_mean"]))
    print("eta_e range: [%.3e%%, %.3e%%] (mean: %.3e%%)" % (summary["eta_min_percent"], summary["eta_max_percent"], summary["eta_mean_percent"]))

if __name__ == "__main__":
    main()

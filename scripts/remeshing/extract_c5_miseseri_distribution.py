#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
extract_c5_miseseri_distribution.py
===================================
Abaqus Python script to extract authentic Abaqus MISESERI and MISESAVG field outputs
from the C5 companion-continuum linear-elastic ODB (M1_C5_COMPANION_MISESERI.odb).

Evaluates:
- Elementwise MISESERI (recovered stress error indicator in kN/mm^2)
- Elementwise MISESAVG (average Mises stress in kN/mm^2)
- Relative error indicator eta_e = MISESERI_e / MISESAVG_e
- Element centroids (xc, yc) from authentic 12,996 C5 quads
- High-error elements for refinement marking in Cycle C6 (eta >= 0.15)
- Spatial distribution, peak error coordinates, and element quality diagnostics.

Usage:
    abaqus python extract_c5_miseseri_distribution.py [--odb PATH] [--out-dir PATH] [--threshold 0.15]

Task: F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE
Protocol Version: 2
"""

from __future__ import print_function, division
import csv
import json
import math
import os
import sys

def extract_miseseri(odb_path, output_dir, threshold_eta=0.15):
    from odbAccess import openOdb

    print("Opening C5 companion ODB: %s" % odb_path)
    if not os.path.exists(odb_path):
        raise RuntimeError("ODB not found: %s" % odb_path)

    odb = openOdb(odb_path, readOnly=True)
    step_name = 'STATIC_ELASTIC'
    if step_name not in odb.steps:
        # Fall back to last step
        step_name = odb.steps.keys()[-1]

    step = odb.steps[step_name]
    frame = step.frames[-1]

    # Node coordinates lookup
    root_assembly = odb.rootAssembly
    instance = root_assembly.instances[root_assembly.instances.keys()[0]] if root_assembly.instances else None

    node_coords = {}
    if instance:
        for node in instance.nodes:
            node_coords[node.label] = (float(node.coordinates[0]), float(node.coordinates[1]))
    else:
        for node in root_assembly.nodes:
            node_coords[node.label] = (float(node.coordinates[0]), float(node.coordinates[1]))

    # Element centroids lookup
    elem_centroids = {}
    elements_source = instance.elements if instance else root_assembly.elements
    for elem in elements_source:
        conn = elem.connectivity
        xs = [node_coords[nl][0] for nl in conn if nl in node_coords]
        ys = [node_coords[nl][1] for nl in conn if nl in node_coords]
        if xs and ys:
            elem_centroids[elem.label] = (sum(xs) / float(len(xs)), sum(ys) / float(len(ys)))

    # Extract MISESERI, MISESAVG, EVOL
    if 'MISESERI' not in frame.fieldOutputs:
        raise RuntimeError("MISESERI field not found in ODB!")
    if 'MISESAVG' not in frame.fieldOutputs:
        raise RuntimeError("MISESAVG field not found in ODB!")

    miseseri_field = frame.fieldOutputs['MISESERI']
    misesavg_field = frame.fieldOutputs['MISESAVG']
    evol_field = frame.fieldOutputs.get('EVOL', None)

    miseseri_map = {}
    for val in miseseri_field.values:
        miseseri_map[val.elementLabel] = float(val.data)

    misesavg_map = {}
    for val in misesavg_field.values:
        misesavg_map[val.elementLabel] = float(val.data)

    evol_map = {}
    if evol_field:
        for val in evol_field.values:
            evol_map[val.elementLabel] = float(val.data)

    records = []
    max_eri = -1.0
    max_eri_elem = None
    max_eta = -1.0
    max_eta_elem = None
    marked_count = 0

    for elabel in sorted(miseseri_map.keys()):
        eri = miseseri_map[elabel]
        avg = misesavg_map.get(elabel, 0.0)
        evol = evol_map.get(elabel, 0.0)
        eta = (eri / avg) if avg > 1e-6 else 0.0
        cent = elem_centroids.get(elabel, (0.0, 0.0))
        refine_mark = 1 if eta >= threshold_eta else 0

        if refine_mark == 1:
            marked_count += 1

        if eri > max_eri:
            max_eri = eri
            max_eri_elem = elabel
        if eta > max_eta:
            max_eta = eta
            max_eta_elem = elabel

        records.append({
            "element_id": elabel,
            "xc": cent[0],
            "yc": cent[1],
            "miseseri_kNmm2": eri,
            "misesavg_kNmm2": avg,
            "eta_relative_error": eta,
            "evol_mm3": evol,
            "refine_mark": refine_mark
        })

    total_elems = len(records)
    pct_marked = (marked_count / float(total_elems) * 100.0) if total_elems > 0 else 0.0

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    csv_path = os.path.join(output_dir, "c5_companion_miseseri_distribution.csv")
    with open(csv_path, "w") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "element_id", "xc", "yc", "miseseri_kNmm2", "misesavg_kNmm2",
            "eta_relative_error", "evol_mm3", "refine_mark"
        ], lineterminator="\n")
        writer.writeheader()
        for r in records:
            writer.writerow(r)

    summary = {
        "schema": 1,
        "job_name": "M1_C5_COMPANION_MISESERI",
        "odb_path": odb_path,
        "step_name": step_name,
        "total_elements": total_elems,
        "threshold_eta": threshold_eta,
        "marked_elements_count": marked_count,
        "marked_percentage": pct_marked,
        "peak_miseseri": {
            "element_id": max_eri_elem,
            "miseseri_kNmm2": max_eri,
            "centroid_mm": {
                "x": elem_centroids.get(max_eri_elem, (0.0, 0.0))[0],
                "y": elem_centroids.get(max_eri_elem, (0.0, 0.0))[1]
            }
        },
        "peak_relative_error": {
            "element_id": max_eta_elem,
            "eta": max_eta,
            "centroid_mm": {
                "x": elem_centroids.get(max_eta_elem, (0.0, 0.0))[0],
                "y": elem_centroids.get(max_eta_elem, (0.0, 0.0))[1]
            }
        },
        "refinement_metrics": {
            "threshold_eta": threshold_eta,
            "elements_above_threshold": marked_count,
            "pct_above_threshold": pct_marked,
            "adaptation_recommendation": "ADVANCE_CYCLE_C6_REFINEMENT" if marked_count > 0 else "NO_REFINEMENT_NEEDED"
        }
    }

    summary_path = os.path.join(output_dir, "c5_miseseri_extraction_summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    odb.close()
    print("MISESERI extraction complete.")
    print("  Total elements: %d" % total_elems)
    print("  Marked elements (eta >= %.2f): %d (%.2f%%)" % (threshold_eta, marked_count, pct_marked))
    print("  Peak MISESERI: %.4f kN/mm^2 at elem %s" % (max_eri, max_eri_elem))
    print("  Peak eta: %.4f at elem %s" % (max_eta, max_eta_elem))
    return summary


if __name__ == "__main__":
    odb_arg = "M1_C5_COMPANION_MISESERI.odb"
    out_arg = "."
    thresh_arg = 0.15

    for i, a in enumerate(sys.argv):
        if a == "--odb" and i + 1 < len(sys.argv):
            odb_arg = sys.argv[i + 1]
        elif a == "--out-dir" and i + 1 < len(sys.argv):
            out_arg = sys.argv[i + 1]
        elif a == "--threshold" and i + 1 < len(sys.argv):
            thresh_arg = float(sys.argv[i + 1])

    extract_miseseri(odb_arg, out_arg, thresh_arg)

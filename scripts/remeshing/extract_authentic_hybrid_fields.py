# -*- coding: utf-8 -*-
"""
scripts/remeshing/extract_authentic_hybrid_fields.py
====================================================
Task: F1666 - Generalized 2D Hybrid Adaptive Remeshing
Extracts authentic donor phase-field damage and recovery stress error,
and computes the hybrid sizing field:
    h_hybrid(x, y) = min(h_MISESERI(x, y), h_damage(x, y))
"""

from __future__ import print_function
import os
import sys
import json
import math

try:
    from odbAccess import openOdb
except ImportError:
    print("This script must be executed via 'abaqus python'.")
    sys.exit(1)

def main():
    print("======================================================================")
    print("TASK F1666: AUTHENTIC HYBRID SIZING FIELD EXTRACTION")
    print("======================================================================")

    # 1. Open Job 1 coarse ODB
    job1_odb_path = os.path.abspath("models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_COARSE_JOB1.odb")
    if not os.path.exists(job1_odb_path):
        raise RuntimeError("Job 1 ODB not found: %s" % job1_odb_path)

    print("Opening Job 1 ODB: %s" % job1_odb_path)
    odb_donor = openOdb(job1_odb_path, readOnly=True)
    inst_donor = odb_donor.rootAssembly.instances['PART-1-1']
    donor_nodes = {n.label: (float(n.coordinates[0]), float(n.coordinates[1])) for n in inst_donor.nodes}

    # Physical elements are Layer 3 (5813 to 8718)
    vis_elems = [el for el in inst_donor.elements if 5813 <= el.label <= 8718]
    step2 = odb_donor.steps['Step-2']
    term_frame = step2.frames[-1]
    sdv1_field = term_frame.fieldOutputs['SDV1']

    el_damage_map = {}
    for val in sdv1_field.values:
        el_lbl = val.elementLabel
        if 5813 <= el_lbl <= 8718:
            if el_lbl not in el_damage_map:
                el_damage_map[el_lbl] = []
            el_damage_map[el_lbl].append(float(val.data))

    donor_data = []
    for el in vis_elems:
        pts = [donor_nodes[nid] for nid in el.connectivity]
        cx = sum([p[0] for p in pts]) / float(len(pts))
        cy = sum([p[1] for p in pts]) / float(len(pts))
        d_vals = el_damage_map.get(el.label, [0.0])
        d_max = max(d_vals)
        d_mean = sum(d_vals) / float(len(d_vals))
        donor_data.append({
            "phys_label": el.label - 5812,
            "cx": cx,
            "cy": cy,
            "connectivity": [int(nid) for nid in el.connectivity],
            "d_max": d_max,
            "d_mean": d_mean
        })

    odb_donor.close()
    print("Extracted %d donor physical elements." % len(donor_data))
    d_max_all = [d["d_max"] for d in donor_data]
    print("  Donor damage: min=%.4e, max=%.4f, count d>=0.80: %d, count d>=0.10: %d" % (
        min(d_max_all), max(d_max_all),
        sum(1 for d in d_max_all if d >= 0.80),
        sum(1 for d in d_max_all if d >= 0.10)
    ))

    # 2. Open Recovery ODB
    rec_odb_path = os.path.abspath("PK_HOLE_F1661_RECOVERY.odb")
    if not os.path.exists(rec_odb_path):
        raise RuntimeError("Recovery ODB not found: %s" % rec_odb_path)

    print("Opening Recovery ODB: %s" % rec_odb_path)
    odb_rec = openOdb(rec_odb_path, readOnly=True)
    inst_rec = odb_rec.rootAssembly.instances['PLATE-1']
    rec_nodes = {n.label: (float(n.coordinates[0]), float(n.coordinates[1])) for n in inst_rec.nodes}
    rec_elems = inst_rec.elements

    frame_rec = odb_rec.steps['Step-1'].frames[-1]
    miseseri_field = frame_rec.fieldOutputs['MISESERI']
    misesavg_field = frame_rec.fieldOutputs['MISESAVG']

    miseseri_map = {val.elementLabel: float(val.data) for val in miseseri_field.values}
    misesavg_map = {val.elementLabel: float(val.data) for val in misesavg_field.values}

    recovery_data = []
    for el in rec_elems:
        pts = [rec_nodes[nid] for nid in el.connectivity]
        cx = sum([p[0] for p in pts]) / float(len(pts))
        cy = sum([p[1] for p in pts]) / float(len(pts))
        meri = miseseri_map.get(el.label, 0.0)
        mavg = misesavg_map.get(el.label, 1.0)
        eta = (meri / max(mavg, 1e-9)) * 100.0
        recovery_data.append({
            "label": el.label,
            "cx": cx,
            "cy": cy,
            "connectivity": [int(nid) for nid in el.connectivity],
            "miseseri": meri,
            "misesavg": mavg,
            "eta_pct": eta
        })

    odb_rec.close()
    print("Extracted %d recovery elements." % len(recovery_data))
    etas = [r["eta_pct"] for r in recovery_data]
    print("  Recovery eta: min=%.2f%%, median=%.2f%%, max=%.2f%%, eta>5.0%%: %d (%.2f%%)" % (
        min(etas), sorted(etas)[len(etas)//2], max(etas),
        sum(1 for e in etas if e > 5.0), 100.0 * sum(1 for e in etas if e > 5.0) / len(etas)
    ))

    # 3. Export JSON
    out_json = os.path.abspath("models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_F1666_HYBRID_SIZING_FIELD.json")
    payload = {
        "donor_nodes": donor_nodes,
        "donor_elements": donor_data,
        "recovery_nodes": rec_nodes,
        "recovery_elements": recovery_data
    }
    with open(out_json, "w") as f:
        json.dump(payload, f)
    print("Exported hybrid sizing field to: %s (%d bytes)" % (out_json, os.path.getsize(out_json)))

if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
extract_f1699_states.py
=======================
Extracts full-field accepted UEL state data from:
  /scratch9/pr21vyci/runs/mode1_pk_sec43_staggered_job1/PK_SEC43_STAGGERED_JOB1.odb
for Task F1699 (Gate A: Full-field same-state UEL recovery).

Target States:
  - State 2: Primary Propagation / Hole Arrest (Step-1, Frame 40, uy = 0.200 mm)
  - State 4: Secondary Mid-Propagation (Step-1, Frame 60, uy = 0.300 mm)
  - State 5: Terminal Dual Severance (Step-2, Frame 250, uy = 1.500 mm)

Extracted Quantities per State:
  - Nodal displacements U1, U2 for all 4,040 nodes
  - Element damage d = SDV1 for all 3,923 elements
  - Reaction forces RF1, RF2
  - Node coordinates (x, y)
  - Element connectivity and centroids
"""

from __future__ import print_function
import os
import sys
import json
import math
from odbAccess import openOdb

def main():
    odb_path = "/scratch9/pr21vyci/runs/mode1_pk_sec43_staggered_job1/PK_SEC43_STAGGERED_JOB1.odb"
    if len(sys.argv) > 1:
        odb_path = sys.argv[1]

    print("Opening ODB: %s" % odb_path)
    odb = openOdb(odb_path, readOnly=True)

    root_assembly = odb.rootAssembly
    inst_name = list(root_assembly.instances.keys())[0]
    inst = root_assembly.instances[inst_name]
    print("Instance: %s (%d elements, %d nodes)" % (inst_name, len(inst.elements), len(inst.nodes)))

    # Node coordinates
    nodes_dict = {}
    for n in inst.nodes:
        nodes_dict[n.label] = (round(float(n.coordinates[0]), 6), round(float(n.coordinates[1]), 6))

    # Parse physical elements (labels 1..3923 or facsimile elements 7847..11769)
    # The mesh has 3 layers of 3923 elements each:
    #   Layer 1: Phase UEL (1..3923)
    #   Layer 2: Disp UEL (3924..7846)
    #   Layer 3: Facsimile standard elements (7847..11769)
    n_phys = 3923
    phys_connectivity = {}
    phys_centroids = {}
    for el in inst.elements:
        raw_eid = el.label
        if 7847 <= raw_eid <= 11769:
            peid = raw_eid - 7846
            conn = list(el.connectivity)
            phys_connectivity[peid] = conn
            pts = [nodes_dict[nid] for nid in conn if nid in nodes_dict]
            cx = round(sum(p[0] for p in pts) / float(len(pts)), 6)
            cy = round(sum(p[1] for p in pts) / float(len(pts)), 6)
            phys_centroids[peid] = (cx, cy)
        else:
            peid_direct = raw_eid
            if 1 <= peid_direct <= n_phys and peid_direct not in phys_connectivity:
                conn = list(el.connectivity)
                phys_connectivity[peid_direct] = conn
                pts = [nodes_dict[nid] for nid in conn if nid in nodes_dict]
                cx = round(sum(p[0] for p in pts) / float(len(pts)), 6)
                cy = round(sum(p[1] for p in pts) / float(len(pts)), 6)
                phys_centroids[peid_direct] = (cx, cy)

    print("Parsed %d physical elements and %d nodes." % (len(phys_connectivity), len(nodes_dict)))

    targets = [
        {
            "state_key": "state_2_hole_arrest",
            "name": "State 2: Primary Propagation (Hole Arrest)",
            "step_name": "Step-1",
            "frame_idx": 40,
            "uy_nom": 0.200
        },
        {
            "state_key": "state_4_sec_midprop",
            "name": "State 4: Secondary Mid-Propagation",
            "step_name": "Step-1",
            "frame_idx": 60,
            "uy_nom": 0.300
        },
        {
            "state_key": "state_5_terminal",
            "name": "State 5: Terminal Dual Severance",
            "step_name": "Step-2",
            "frame_idx": 250,
            "uy_nom": 1.500
        }
    ]

    states_data = {}

    for tgt in targets:
        s_name = tgt["step_name"]
        f_idx = tgt["frame_idx"]
        s_key = tgt["state_key"]
        print("\nProcessing %s (%s, Frame %d)..." % (tgt["name"], s_name, f_idx))

        step = odb.steps[s_name]
        if f_idx >= len(step.frames):
            f_idx = len(step.frames) - 1
        frame = step.frames[f_idx]
        frame_val = float(frame.frameValue)
        total_time = frame_val if s_name == "Step-1" else 1.0 + frame_val

        # 1. Nodal displacements U
        u_dict = {}
        if "U" in frame.fieldOutputs:
            u_field = frame.fieldOutputs["U"]
            for val in u_field.values:
                nl = val.nodeLabel
                # We only need nodes 1..4040
                if 1 <= nl <= 4040:
                    u_dict[nl] = [round(float(val.data[0]), 8), round(float(val.data[1]), 8)]

        # 2. Reaction forces RF
        rf_total_y = 0.0
        rf_dict = {}
        if "RF" in frame.fieldOutputs:
            rf_field = frame.fieldOutputs["RF"]
            for val in rf_field.values:
                nl = val.nodeLabel
                if abs(val.data[0]) > 1e-6 or abs(val.data[1]) > 1e-6:
                    rf_dict[nl] = [round(float(val.data[0]), 6), round(float(val.data[1]), 6)]
                # Sum RF_y on upper hole nodes (y around 100) or RP
                if nl == 999999 or (nl in nodes_dict and nodes_dict[nl][1] > 94.0):
                    rf_total_y += float(val.data[1])

        # 3. Damage SDV1
        sdv1_field = None
        for k in frame.fieldOutputs.keys():
            if 'SDV1' in k:
                sdv1_field = frame.fieldOutputs[k]
                break
            elif 'SDV' in k and sdv1_field is None:
                sdv1_field = frame.fieldOutputs[k]

        elem_damage = {}
        if sdv1_field is not None:
            raw_elem_d = {}
            for val in sdv1_field.values:
                raw_eid = val.elementLabel
                # Map to physical ID
                peid = (raw_eid - 1) % n_phys + 1
                d_val = float(val.data)
                if peid not in raw_elem_d:
                    raw_elem_d[peid] = []
                raw_elem_d[peid].append(d_val)
            for peid in range(1, n_phys + 1):
                if peid in raw_elem_d:
                    vals = raw_elem_d[peid]
                    elem_damage[peid] = round(sum(vals) / float(len(vals)), 6)
                else:
                    elem_damage[peid] = 0.0

        max_u = max([math.hypot(v[0], v[1]) for v in u_dict.values()]) if u_dict else 0.0
        max_d = max(elem_damage.values()) if elem_damage else 0.0
        print("  Extracted: %d node Us (max=%.4f mm), %d elem damages (max=%.4f), RF_y=%.4f kN" % (
            len(u_dict), max_u, len(elem_damage), max_d, rf_total_y / 1000.0 if abs(rf_total_y) > 100 else rf_total_y
        ))

        states_data[s_key] = {
            "state_key": s_key,
            "name": tgt["name"],
            "step_name": s_name,
            "frame_idx": f_idx,
            "frame_value": frame_val,
            "total_time": total_time,
            "uy_nom_mm": tgt["uy_nom"],
            "rf_total_y_kN": round(rf_total_y / 1000.0 if abs(rf_total_y) > 100 else rf_total_y, 6),
            "max_u_mag_mm": round(max_u, 6),
            "max_damage": round(max_d, 6),
            "nodal_displacements": u_dict,
            "element_damage": elem_damage
        }

    out_record = {
        "benchmark": "Pandey & Kumar (2025) Section 4.3 holed plate",
        "job_name": "PK_SEC43_STAGGERED_JOB1",
        "pbs_job_id": "1421286.mmaster02",
        "source_odb": odb_path,
        "nodes_dict": nodes_dict,
        "phys_connectivity": phys_connectivity,
        "phys_centroids": phys_centroids,
        "states": states_data
    }

    out_file = "/scratch9/pr21vyci/runs/mode1_pk_sec43_staggered_job1/f1699_uel_accepted_states.json"
    print("\nWriting extracted data to %s..." % out_file)
    with open(out_file, "w") as fp:
        json.dump(out_record, fp)
    print("Done. File size: %d bytes" % os.path.getsize(out_file))

    odb.close()
    return 0

if __name__ == "__main__":
    main()

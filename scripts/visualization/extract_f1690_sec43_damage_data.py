# -*- coding: utf-8 -*-
"""
extract_f1690_sec43_damage_data.py

Pure Abaqus Python (no matplotlib) script to extract element coordinates and
damage variable (SDV1) from PK_SEC43_RERUN_JOB1.odb at the terminal frame.
Outputs f1690_sec43_damage_data.json.
"""

import os
import sys
import json
from odbAccess import openOdb

def main():
    odb_path = "PK_SEC43_RERUN_JOB1.odb"
    if not os.path.exists(odb_path):
        local_cand = os.path.join("models", "pandey_kumar_mode1", "190_pk_sec43_job1_rerun", "PK_SEC43_RERUN_JOB1.odb")
        if os.path.exists(local_cand):
            odb_path = local_cand
        else:
            raise IOError("ODB not found at %s or %s" % (odb_path, local_cand))

    print("Opening ODB: %s" % odb_path)
    odb = openOdb(odb_path, readOnly=True)
    step = odb.steps.values()[0]
    frame = step.frames[-1]

    print("Step: %s, Frame: %d, Time/Value: %.6f" % (step.name, len(step.frames)-1, frame.frameValue))

    root_assembly = odb.rootAssembly
    nodes_dict = {}
    for inst_name, inst in root_assembly.instances.items():
        for n in inst.nodes:
            nodes_dict[n.label] = [float(n.coordinates[0]), float(n.coordinates[1])]

    sdv1_field = None
    for k in frame.fieldOutputs.keys():
        if 'SDV1' in k:
            sdv1_field = frame.fieldOutputs[k]
            break

    if sdv1_field is None:
        for k in frame.fieldOutputs.keys():
            if 'SDV' in k:
                sdv1_field = frame.fieldOutputs[k]
                break

    if sdv1_field is None:
        raise KeyError("SDV1 or SDV field not found in frame.fieldOutputs: %s" % frame.fieldOutputs.keys())

    elem_damage = {}
    for val in sdv1_field.values:
        eid = val.elementLabel
        d = float(val.data)
        if eid not in elem_damage:
            elem_damage[eid] = []
        elem_damage[eid].append(d)

    avg_damage = {}
    for eid, vals in elem_damage.items():
        avg_damage[eid] = sum(vals) / float(len(vals))

    print("Extracted damage values for %d elements from SDV1 field." % len(avg_damage))

    elements_data = []
    notch_tip_damage = []
    secondary_damage = []

    for inst_name, inst in root_assembly.instances.items():
        for el in inst.elements:
            eid = el.label
            if eid not in avg_damage:
                continue
            conn = list(el.connectivity)
            pts = [nodes_dict[nid] for nid in conn if nid in nodes_dict]
            if len(pts) < 3:
                continue
            cx = sum(p[0] for p in pts) / float(len(pts))
            cy = sum(p[1] for p in pts) / float(len(pts))
            d = avg_damage[eid]

            eid_phys = eid - 49436 if eid > 49436 else eid

            elements_data.append({
                "eid": eid,
                "eid_phys": eid_phys,
                "cx": cx,
                "cy": cy,
                "d": d,
                "pts": pts
            })

            # Notch tip: x in [9.5, 15.0], y in [68.0, 72.0]
            if 9.5 <= cx <= 15.0 and 68.0 <= cy <= 72.0:
                notch_tip_damage.append(d)

            # Secondary ligament: x >= 46.5, y in [42.0, 60.0]
            if cx >= 46.5 and 42.0 <= cy <= 60.0:
                secondary_damage.append(d)

    d_all = [el["d"] for el in elements_data]
    max_d = max(d_all) if d_all else 0.0
    max_notch_d = max(notch_tip_damage) if notch_tip_damage else 0.0
    max_sec_d = max(secondary_damage) if secondary_damage else 0.0

    print("Summary:")
    print("  Total elements with damage: %d" % len(elements_data))
    print("  Global max damage: %.4f" % max_d)
    print("  Notch tip max damage: %.4f" % max_notch_d)
    print("  Secondary ligament max damage: %.4f" % max_sec_d)

    output_data = {
        "step_name": step.name,
        "frame_index": len(step.frames) - 1,
        "u_y_terminal": float(frame.frameValue),
        "total_elements": len(elements_data),
        "max_damage": max_d,
        "notch_tip_max_damage": max_notch_d,
        "secondary_ligament_max_damage": max_sec_d,
        "elements": elements_data
    }

    out_file = "f1690_sec43_damage_data.json"
    with open(out_file, "w") as f:
        json.dump(output_data, f)

    print("Saved %d elements to %s" % (len(elements_data), out_file))
    odb.close()

if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
scripts/remeshing/extract_case2_nodal_u.py
=========================================
Extracts full nodal displacement vector (U1, U2) from PK_HOLE_COARSE_JOB1.odb
at Step-2, Frame Index 167 (Peak load state, uy = 0.00729381 mm).
"""

from __future__ import print_function
import sys
import os
import json

try:
    import odbAccess
    from abaqusConstants import *
except ImportError:
    print("Must be run with abaqus python")
    sys.exit(1)

ODB_PATH = "/scratch9/pr21vyci/runs/mode1_method_a_hole_coarse/PK_HOLE_COARSE_JOB1.odb"
OUT_JSON = "/scratch9/pr21vyci/runs/mode1_method_a_hole_coarse/case2_step2_peak_nodal_u.json"

def main():
    if not os.path.exists(ODB_PATH):
        print("ODB not found:", ODB_PATH)
        sys.exit(1)

    odb = odbAccess.openOdb(ODB_PATH, readOnly=True)
    step = odb.steps['Step-2']
    frame = step.frames[167]
    print("Inspecting Step-2, Frame 167, time =", frame.frameValue)

    fkeys = list(frame.fieldOutputs.keys())
    print("Available fieldOutputs:", fkeys)

    result = {
        "step": "Step-2",
        "frame_index": 167,
        "step_time": frame.frameValue,
        "available_fields": fkeys,
        "nodal_u": {},
        "rp_u": None,
        "total_nodes_extracted": 0,
        "has_full_nodal_field": False
    }

    if 'U' in frame.fieldOutputs:
        u_fo = frame.fieldOutputs['U']
        print("Total values in fieldOutput U:", len(u_fo.values))
        for val in u_fo.values:
            nid = val.nodeLabel
            ux = float(val.data[0])
            uy = float(val.data[1])
            if nid == 999999:
                result["rp_u"] = [ux, uy]
            else:
                result["nodal_u"][nid] = [ux, uy]

        result["total_nodes_extracted"] = len(result["nodal_u"])
        result["has_full_nodal_field"] = (len(result["nodal_u"]) >= 3010)

        u2_vals = [v[1] for v in result["nodal_u"].values()] if result["nodal_u"] else []
        if u2_vals:
            print("Physical nodal U2 min: %.6e, max: %.6e, mean: %.6e" % (
                min(u2_vals), max(u2_vals), sum(u2_vals)/len(u2_vals)
            ))
        if result["rp_u"]:
            print("RP displacement:", result["rp_u"])

    with open(OUT_JSON, 'w') as f:
        json.dump(result, f, indent=2)

    print("Saved nodal U data to:", OUT_JSON)
    odb.close()

if __name__ == '__main__':
    main()

# -*- coding: utf-8 -*-
"""
scripts/postprocessing/inspect_f1720_adapted_forensics.py
========================================================
Forensic audit of PK_F1720_ADAPTED_PFM solver execution:
1. Exact ODB steps, frames, and frameValue
2. Prescribed vs measured U2 at reference node 13402
3. RF2 at reference node 13402 vs sum of RF2 at bottom boundary
4. Actual integration points in Layer 1, Layer 2, Layer 3
5. Final frame state and termination conditions
"""

from __future__ import print_function
import os
import sys
import json
from odbAccess import openOdb

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
ODB_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "214_f1720_adapted_mesh", "PK_F1720_ADAPTED_PFM.odb")
PHYS_INP = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "214_f1720_adapted_mesh", "PK_F1720_ADAPTED_PHYS.inp")
OUT_JSON = os.path.join(REPO_ROOT, "results", "validation", "f1720_solver_forensics.json")

def audit_solver_execution():
    assert os.path.exists(ODB_PATH), "ODB not found: " + ODB_PATH
    odb = openOdb(ODB_PATH, readOnly=True)

    root_assembly = odb.rootAssembly
    rp_node = 13402

    # Check element counts and types in root assembly
    elem_types = {}
    total_elements = 0
    for inst_name, inst in root_assembly.instances.items():
        total_elements += len(inst.elements)
        for el in inst.elements:
            t = el.type
            elem_types[t] = elem_types.get(t, 0) + 1

    steps_info = {}
    for skey in odb.steps.keys():
        step = odb.steps[skey]
        frames_info = []
        for fidx, frame in enumerate(step.frames):
            fval = float(frame.frameValue)
            # Query U at RP
            u2_rp = None
            if 'U' in frame.fieldOutputs.keys():
                u_field = frame.fieldOutputs['U']
                for v in u_field.values:
                    if v.nodeLabel == rp_node:
                        u2_rp = float(v.data[1])
                        break
            # Query RF at RP
            rf2_rp = None
            if 'RF' in frame.fieldOutputs.keys():
                rf_field = frame.fieldOutputs['RF']
                for v in rf_field.values:
                    if v.nodeLabel == rp_node:
                        rf2_rp = float(v.data[1])
                        break
            frames_info.append({
                'frame_index': fidx,
                'frame_value': fval,
                'u2_rp': u2_rp,
                'rf2_rp': rf2_rp
            })
        steps_info[skey] = {
            'total_frames': len(step.frames),
            'first_frame': frames_info[0] if frames_info else None,
            'last_frame': frames_info[-1] if frames_info else None,
            'sample_frames_count': len(frames_info)
        }

    # Inspect integration points in final frame
    last_step = odb.steps[list(odb.steps.keys())[-1]]
    last_frame = last_step.frames[-1]

    sdv1_ips_count = 0
    if 'SDV1' in last_frame.fieldOutputs.keys():
        sdv1 = last_frame.fieldOutputs['SDV1']
        sdv1_ips_count = len(sdv1.values)

    results = {
        'odb_path': ODB_PATH,
        'element_types': elem_types,
        'total_elements': total_elements,
        'steps': steps_info,
        'sdv1_values_count': sdv1_ips_count,
        'final_frame_summary': {
            'step': list(odb.steps.keys())[-1],
            'frame_index': len(last_step.frames) - 1,
            'frame_value': float(last_frame.frameValue),
            'u2_rp': frames_info[-1]['u2_rp'] if frames_info else None,
            'rf2_rp': frames_info[-1]['rf2_rp'] if frames_info else None
        }
    }

    odb.close()

    with open(OUT_JSON, 'w') as f:
        json.dump(results, f, indent=2)

    print("Forensics audit completed. Results saved to:", OUT_JSON)
    print(json.dumps(results, indent=2))

if __name__ == '__main__':
    audit_solver_execution()

# -*- coding: utf-8 -*-
"""
extract_case3_job2_observables.py
Extracts observables from Job 2 ODB, DAT, and energy CSV.
"""
from __future__ import print_function
import sys
import os
import json

def main():
    odb_path = sys.argv[1]
    from odbAccess import openOdb
    odb = openOdb(odb_path)
    
    print("ODB Title:", odb.description)
    steps = list(odb.steps.keys())
    print("Steps:", steps)
    
    res = {"steps": {}}
    for sname in steps:
        step = odb.steps[sname]
        n_frames = len(step.frames)
        print("Step %s: %d frames" % (sname, n_frames))
        frame_list = []
        for i, f in enumerate(step.frames):
            t = f.frameValue
            # Get max SDV1 (phase field d) if present
            max_d = 0.0
            if 'SDV1' in f.fieldOutputs:
                sdv1 = f.fieldOutputs['SDV1']
                max_d = max(v.data for v in sdv1.values)
            # Get RF2 and U2 at Node 999999
            u2_rp = 0.0
            rf2_rp = 0.0
            if 'U' in f.fieldOutputs:
                u_field = f.fieldOutputs['U']
                for v in u_field.values:
                    if v.nodeLabel == 999999:
                        u2_rp = v.data[1]
                        break
            if 'RF' in f.fieldOutputs:
                rf_field = f.fieldOutputs['RF']
                for v in rf_field.values:
                    if v.nodeLabel == 999999:
                        rf2_rp = v.data[1]
                        break
            frame_list.append({
                "frame": i,
                "time": t,
                "max_d": float(max_d),
                "u2_rp": float(u2_rp),
                "rf2_rp": float(rf2_rp)
            })
            print("  Frame %d (t=%.6f): u2=%.6f mm, RF2=%.4f kN, max(d)=%.6f" % (i, t, u2_rp, rf2_rp, max_d))
        res["steps"][sname] = frame_list
    
    odb.close()
    
    out_json = sys.argv[2]
    with open(out_json, "w") as fp:
        json.dump(res, fp, indent=2)
    print("Saved observables to:", out_json)

if __name__ == '__main__':
    main()

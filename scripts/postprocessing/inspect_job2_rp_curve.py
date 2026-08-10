#!/usr/bin/env python
import sys
import os
import json

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
val_dir = os.path.join(repo_root, "scripts", "validation")
if val_dir not in sys.path:
    sys.path.insert(0, val_dir)

from odbAccess import openOdb

def inspect_rp_curve(odb_path):
    print("=== Inspecting RP Curve for " + odb_path + " ===")
    odb = openOdb(odb_path, readOnly=True)
    rp_set = odb.rootAssembly.nodeSets['RP']

    curve = []
    for sname in sorted(odb.steps.keys()):
        step = odb.steps[sname]
        for f in step.frames:
            u1 = 0.0
            rf1 = 0.0
            if 'U' in f.fieldOutputs:
                sub_u = f.fieldOutputs['U'].getSubset(region=rp_set)
                if sub_u.values:
                    u1 = float(sub_u.values[0].data[0])
            if 'RF' in f.fieldOutputs:
                sub_rf = f.fieldOutputs['RF'].getSubset(region=rp_set)
                if sub_rf.values:
                    rf1 = float(sub_rf.values[0].data[0])
            curve.append((sname, f.frameId, float(f.frameValue), u1, rf1))

    print("Total frames extracted: %d" % len(curve))
    print("First 5 frames:")
    for pt in curve[:5]:
        print("  Step %s frame %d time %.4f: U1=%.6f mm, RF1=%.6f kN" % pt)
    print("Last 5 frames:")
    for pt in curve[-5:]:
        print("  Step %s frame %d time %.4f: U1=%.6f mm, RF1=%.6f kN" % pt)

    # Check SDV outputs on U1 elements (Layer 1) vs U2 elements (Layer 2)
    f_last = odb.steps[sorted(odb.steps.keys())[-1]].frames[-1]
    if 'SDV15' in f_last.fieldOutputs:
        sdv15 = f_last.fieldOutputs['SDV15']
        v15_all = [float(v.data[0] if hasattr(v.data, '__getitem__') else v.data) for v in sdv15.values]
        print("Final frame SDV15: min=%.6f, max=%.6f, count=%d" % (min(v15_all), max(v15_all), len(v15_all)))

    if 'SDV1' in f_last.fieldOutputs:
        sdv1 = f_last.fieldOutputs['SDV1']
        v1_all = [float(v.data[0] if hasattr(v.data, '__getitem__') else v.data) for v in sdv1.values]
        print("Final frame SDV1: min=%.6f, max=%.6f, count=%d" % (min(v1_all), max(v1_all), len(v1_all)))

    odb.close()

if __name__ == "__main__":
    odb_path = sys.argv[1] if len(sys.argv) > 1 else "models/generated/mode_ii/verification_batch/M2REF_H0_EXACT_FRACFIX_REPRO/M2REF_H0_EXACT_FRACFIX_REPRO.odb"
    inspect_rp_curve(odb_path)

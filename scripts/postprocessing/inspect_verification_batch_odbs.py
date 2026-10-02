#!/usr/bin/env python
"""Inspection script for Mode-II Verification Batch ODBs (Job 1386248 & Job 1386249).
Runs under Abaqus Python (Python 2.7 / 3).
"""

from __future__ import print_function
import sys
import os
import json
import math
from odbAccess import openOdb

def inspect_odb(odb_path, label):
    print("==========================================================")
    print("=== Inspecting " + label + " (" + odb_path + ") ===")
    print("==========================================================")
    if not os.path.exists(odb_path):
        print("ERROR: File does not exist: " + odb_path)
        return

    odb = openOdb(odb_path, readOnly=True)
    root = odb.rootAssembly

    rp = None
    if 'RP' in root.nodeSets:
        rp = root.nodeSets['RP']
    else:
        for inst in root.instances.values():
            if 'RP' in inst.nodeSets:
                rp = inst.nodeSets['RP']
                break

    steps = sorted(odb.steps.keys())
    print("Steps in ODB:", steps)

    last_step = odb.steps[steps[-1]]
    last_frame = last_step.frames[-1]
    print("Total frames in last step:", len(last_step.frames))
    print("Field outputs in last frame:", sorted(last_frame.fieldOutputs.keys()))

    # Inspect SDV14, SDV15, SDV16 in last frame
    for sdv_name in ['SDV14', 'SDV15', 'SDV16']:
        if sdv_name in last_frame.fieldOutputs:
            sub = last_frame.fieldOutputs[sdv_name]
            vals = [float(v.data[0]) if hasattr(v.data, '__getitem__') else float(v.data) for v in sub.values]
            min_v = min(vals)
            max_v = max(vals)
            avg_v = sum(vals) / float(len(vals))
            print("%s: min = %.6f, max = %.6f, mean = %.6f (count=%d)" % (sdv_name, min_v, max_v, avg_v, len(vals)))
        else:
            print("%s: NOT FOUND" % sdv_name)

    # Frame-by-frame RP output and SDV evolution
    u_all, rf_all, d14_max_all, d15_max_all, d16_max_all = [], [], [], [], []
    d14_min_all, d15_min_all, d16_min_all = [], [], []

    for sname in steps:
        step = odb.steps[sname]
        for f in step.frames:
            u_val, rf_val = None, None
            if 'U' in f.fieldOutputs and rp:
                usub = f.fieldOutputs['U'].getSubset(region=rp)
                if len(usub.values) > 0:
                    u_val = float(usub.values[0].data[0])
            if 'RF' in f.fieldOutputs and rp:
                rfsub = f.fieldOutputs['RF'].getSubset(region=rp)
                if len(rfsub.values) > 0:
                    rf_val = float(rfsub.values[0].data[0])

            def get_sdv_range(var_name):
                if var_name in f.fieldOutputs:
                    sub = f.fieldOutputs[var_name]
                    if len(sub.values) > 0:
                        vlist = [float(v.data[0]) if hasattr(v.data, '__getitem__') else float(v.data) for v in sub.values]
                        return min(vlist), max(vlist)
                return 0.0, 0.0

            d14_min, d14_max = get_sdv_range('SDV14')
            d15_min, d15_max = get_sdv_range('SDV15')
            d16_min, d16_max = get_sdv_range('SDV16')

            if u_val is not None and rf_val is not None:
                u_all.append(u_val)
                rf_all.append(rf_val)
                d14_max_all.append(d14_max)
                d15_max_all.append(d15_max)
                d16_max_all.append(d16_max)
                d14_min_all.append(d14_min)
                d15_min_all.append(d15_min)
                d16_min_all.append(d16_min)

    peak_rf1 = max(rf_all) if rf_all else 0.0
    idx_peak = rf_all.index(peak_rf1) if rf_all else 0
    u1_at_peak = u_all[idx_peak] if u_all else 0.0
    final_rf1 = rf_all[-1] if rf_all else 0.0
    final_u1 = u_all[-1] if u_all else 0.0

    print("Initial U1: %.6f mm, Initial RF1: %.6f kN" % (u_all[0] if u_all else 0.0, rf_all[0] if rf_all else 0.0))
    print("Peak RF1: %.6f kN at U1 = %.6f mm" % (peak_rf1, u1_at_peak))
    print("Final RF1: %.6f kN at U1 = %.6f mm" % (final_rf1, final_u1))
    print("SDV14 (disp layer) min/max range across frames: [%.6f, %.6f]" % (min(d14_min_all) if d14_min_all else 0.0, max(d14_max_all) if d14_max_all else 0.0))
    print("SDV15 (phase layer) min/max range across frames: [%.6f, %.6f]" % (min(d15_min_all) if d15_min_all else 0.0, max(d15_max_all) if d15_max_all else 0.0))
    print("SDV16 (history) min/max range across frames: [%.6f, %.6f]" % (min(d16_min_all) if d16_min_all else 0.0, max(d16_max_all) if d16_max_all else 0.0))

    # Initial stiffness regression over u in [0.0002, 0.0020]
    u_sel = [u for u in u_all if 0.0002 <= u <= 0.0020]
    rf_sel = [rf for u, rf in zip(u_all, rf_all) if 0.0002 <= u <= 0.0020]
    if len(u_sel) >= 2:
        mean_u = sum(u_sel) / len(u_sel)
        mean_rf = sum(rf_sel) / len(rf_sel)
        num = sum((u - mean_u) * (rf - mean_rf) for u, rf in zip(u_sel, rf_sel))
        den = sum((u - mean_u)**2 for u in u_sel)
        k_stiff = num / den if den != 0 else 0.0
        print("Initial linear shear stiffness K = %.6f kN/mm (n=%d points)" % (k_stiff, len(u_sel)))
    else:
        print("Initial shear stiffness K = unable to compute (insufficient points in [0.0002, 0.0020])")

    # Damage decreases / Irreversibility check
    damage_decreases = [d15_max_all[i] - d15_max_all[i-1] for i in range(1, len(d15_max_all)) if d15_max_all[i] < d15_max_all[i-1]]
    max_neg_dd = min(damage_decreases) if damage_decreases else 0.0
    print("Max framewise damage decrease: %.8f (count=%d)" % (max_neg_dd, len(damage_decreases)))
    print("Irreversibility satisfied: %s" % (max_neg_dd >= -1e-8))

    odb.close()

if __name__ == '__main__':
    base_dir = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/verification_batch"
    inspect_odb(os.path.join(base_dir, "M2REF_ONEEL_FRACFIX_VERIFY/M2REF_ONEEL_FRACFIX_VERIFY.odb"), "Job 1386248 (M2REF_ONEEL_FRACFIX_VERIFY)")
    inspect_odb(os.path.join(base_dir, "M2REF_H0_FRACFIX_REPRO/M2REF_H0_FRACFIX_REPRO.odb"), "Job 1386249 (M2REF_H0_FRACFIX_REPRO)")

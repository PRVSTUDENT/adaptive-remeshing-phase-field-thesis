#!/usr/bin/env python
"""Pointwise Irreversibility and Producer Ownership Auditor for Abaqus ODBs.
Runs under Abaqus Python (Python 2.7 / 3).
Audits SDV15 (phase field) and SDV16 (history) pointwise across all frames.
Also audits pointwise SDV14 - SDV15 differences.
"""

from __future__ import print_function
import sys
import os
import json
import math
from odbAccess import openOdb

def audit_odb_pointwise(odb_path, label):
    print("==========================================================")
    print("=== Pointwise Audit for " + label + " (" + odb_path + ") ===")
    print("==========================================================")
    if not os.path.exists(odb_path):
        print("ERROR: File does not exist: " + odb_path)
        return None

    odb = openOdb(odb_path, readOnly=True)
    root = odb.rootAssembly
    steps = sorted(odb.steps.keys())

    # Build sequence of frames
    all_frames = []
    for sname in steps:
        step = odb.steps[sname]
        for f in step.frames:
            all_frames.append((sname, f.frameId, f.frameValue, f))

    n_frames = len(all_frames)
    print("Total frames to audit: %d across steps %s" % (n_frames, steps))

    # We will track SDV14, SDV15, SDV16 by key: (instance_name, element_label, integration_point)
    # Stored as dict of lists: key -> list of float values (one per frame)
    sdv14_history = {}
    sdv15_history = {}
    sdv16_history = {}

    for sname, fid, fval, f in all_frames:
        for sdv_name, target_dict in [('SDV14', sdv14_history), ('SDV15', sdv15_history), ('SDV16', sdv16_history)]:
            if sdv_name in f.fieldOutputs:
                sub = f.fieldOutputs[sdv_name]
                for v in sub.values:
                    inst_name = v.instance.name if v.instance else "ASSEMBLY"
                    el_lbl = v.elementLabel
                    ip_num = v.integrationPoint if v.integrationPoint is not None else 1
                    key = (inst_name, el_lbl, ip_num)
                    
                    val = float(v.data[0]) if hasattr(v.data, '__getitem__') else float(v.data)
                    if key not in target_dict:
                        target_dict[key] = []
                    target_dict[key].append(val)

    # 1. Audit Pointwise SDV15 Irreversibility
    keys15 = sorted(sdv15_history.keys())
    total_sequences15 = len(keys15)
    total_transitions15 = 0
    neg_transitions15 = 0
    neg_gt_1e8_15 = 0
    neg_gt_1e6_15 = 0
    worst_dec15 = 0.0
    sum_neg_dec15 = 0.0
    worst_loc15 = None

    for key in keys15:
        vals = sdv15_history[key]
        for idx in range(1, len(vals)):
            total_transitions15 += 1
            diff = vals[idx] - vals[idx-1]
            if diff < 0.0:
                neg_transitions15 += 1
                abs_dec = abs(diff)
                sum_neg_dec15 += abs_dec
                if diff < worst_dec15:
                    worst_dec15 = diff
                    worst_loc15 = (key, idx, vals[idx-1], vals[idx])
                if abs_dec > 1.0e-8:
                    neg_gt_1e8_15 += 1
                if abs_dec > 1.0e-6:
                    neg_gt_1e6_15 += 1

    mean_neg_dec15 = (sum_neg_dec15 / float(neg_transitions15)) if neg_transitions15 > 0 else 0.0

    print("\n--- SDV15 Pointwise Irreversibility Audit ---")
    print("Total tracked IP sequences: %d" % total_sequences15)
    print("Total framewise IP transitions: %d" % total_transitions15)
    print("Negative transitions (d_k < d_{k-1}): %d" % neg_transitions15)
    print("Negative transitions > 1e-8: %d" % neg_gt_1e8_15)
    print("Negative transitions > 1e-6: %d" % neg_gt_1e6_15)
    print("Worst decrease: %.10f" % worst_dec15)
    print("Mean negative decrease: %.10f" % mean_neg_dec15)
    if worst_loc15:
        print("Worst decrease location: Inst=%s, Elem=%d, IP=%d at frame_idx %d (val %f -> %f)" % 
              (worst_loc15[0][0], worst_loc15[0][1], worst_loc15[0][2], worst_loc15[1], worst_loc15[2], worst_loc15[3]))

    # 2. Audit Pointwise SDV16 History Monotonicity
    keys16 = sorted(sdv16_history.keys())
    total_sequences16 = len(keys16)
    total_transitions16 = 0
    neg_transitions16 = 0
    neg_gt_1e8_16 = 0
    neg_gt_1e6_16 = 0
    worst_dec16 = 0.0
    sum_neg_dec16 = 0.0
    worst_loc16 = None

    for key in keys16:
        vals = sdv16_history[key]
        for idx in range(1, len(vals)):
            total_transitions16 += 1
            diff = vals[idx] - vals[idx-1]
            if diff < 0.0:
                neg_transitions16 += 1
                abs_dec = abs(diff)
                sum_neg_dec16 += abs_dec
                if diff < worst_dec16:
                    worst_dec16 = diff
                    worst_loc16 = (key, idx, vals[idx-1], vals[idx])
                if abs_dec > 1.0e-8:
                    neg_gt_1e8_16 += 1
                if abs_dec > 1.0e-6:
                    neg_gt_1e6_16 += 1

    mean_neg_dec16 = (sum_neg_dec16 / float(neg_transitions16)) if neg_transitions16 > 0 else 0.0

    print("\n--- SDV16 Pointwise History Monotonicity Audit ---")
    print("Total tracked IP sequences: %d" % total_sequences16)
    print("Total framewise IP transitions: %d" % total_transitions16)
    print("Negative transitions (H_k < H_{k-1}): %d" % neg_transitions16)
    print("Negative transitions > 1e-8: %d" % neg_gt_1e8_16)
    print("Negative transitions > 1e-6: %d" % neg_gt_1e6_16)
    print("Worst decrease: %.10f" % worst_dec16)
    print("Mean negative decrease: %.10f" % mean_neg_dec16)

    # 3. Audit Pointwise SDV14 vs SDV15 Agreement across all frames
    diff_sdv14_15 = []
    unequal_gt_1e6 = 0
    common_keys = sorted(set(sdv14_history.keys()).intersection(set(sdv15_history.keys())))

    for key in common_keys:
        v14_list = sdv14_history[key]
        v15_list = sdv15_history[key]
        for v14, v15 in zip(v14_list, v15_list):
            diff = abs(v14 - v15)
            diff_sdv14_15.append(diff)
            if diff > 1.0e-6:
                unequal_gt_1e6 += 1

    max_abs_diff_14_15 = max(diff_sdv14_15) if diff_sdv14_15 else 0.0
    mean_abs_diff_14_15 = (sum(diff_sdv14_15) / float(len(diff_sdv14_15))) if diff_sdv14_15 else 0.0

    print("\n--- Pointwise SDV14 vs SDV15 Agreement Audit ---")
    print("Total evaluated (frame, IP) sample points: %d" % len(diff_sdv14_15))
    print("Max absolute difference |SDV14 - SDV15|: %.10f" % max_abs_diff_14_15)
    print("Mean absolute difference |SDV14 - SDV15|: %.10f" % mean_abs_diff_14_15)
    print("Unequal points above tolerance 1e-6: %d" % unequal_gt_1e6)

    odb.close()

    result_summary = {
        "label": label,
        "odb_path": odb_path,
        "sdv15_pointwise": {
            "total_sequences": total_sequences15,
            "total_transitions": total_transitions15,
            "negative_transitions": neg_transitions15,
            "negative_transitions_gt_1e8": neg_gt_1e8_15,
            "negative_transitions_gt_1e6": neg_gt_1e6_15,
            "worst_decrease": worst_dec15,
            "mean_negative_decrease": mean_neg_dec15,
        },
        "sdv16_pointwise": {
            "total_sequences": total_sequences16,
            "total_transitions": total_transitions16,
            "negative_transitions": neg_transitions16,
            "negative_transitions_gt_1e8": neg_gt_1e8_16,
            "negative_transitions_gt_1e6": neg_gt_1e6_16,
            "worst_decrease": worst_dec16,
            "mean_negative_decrease": mean_neg_dec16,
        },
        "sdv14_vs_sdv15": {
            "total_samples": len(diff_sdv14_15),
            "max_abs_difference": max_abs_diff_14_15,
            "mean_abs_difference": mean_abs_diff_14_15,
            "unequal_points_gt_1e6": unequal_gt_1e6,
        }
    }
    return result_summary

if __name__ == '__main__':
    base_dir = '/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/verification_batch'
    res_oneel = audit_odb_pointwise(os.path.join(base_dir, 'M2REF_ONEEL_FRACFIX_VERIFY/M2REF_ONEEL_FRACFIX_VERIFY.odb'), 'Job 1386248 (ONEEL)')
    res_h0 = audit_odb_pointwise(os.path.join(base_dir, 'M2REF_H0_FRACFIX_REPRO/M2REF_H0_FRACFIX_REPRO.odb'), 'Job 1386249 (H0)')
    
    out_json = "/tmp/pointwise_irreversibility_results.json"
    with open(out_json, "w") as f:
        json.dump({"ONEEL": res_oneel, "H0": res_h0}, f, indent=2)
    print("\nWrote summary JSON to " + out_json)

#!/usr/bin/env python
"""Hardened Pointwise Irreversibility and Producer Ownership Auditor for Abaqus ODBs.
Runs under Abaqus Python (Python 2.7 / 3).
Audits SDV15 (phase field) and SDV16 (history) pointwise across all frames.
Audits pointwise SDV14 vs SDV15 agreement.
Explicitly keys every value by (step_name, frame_id, instance, element_label, integration_point).
Fails closed on missing fields, empty outputs, duplicate keys, or inconsistent frame coverage.
"""

from __future__ import print_function
import sys
import os
import json

def audit_odb_pointwise(odb_path, label):
    print("==========================================================")
    print("=== Pointwise Audit for " + label + " (" + odb_path + ") ===")
    print("==========================================================")
    if not os.path.exists(odb_path):
        raise ValueError("ERROR: File does not exist: " + odb_path)

    from odbAccess import openOdb
    odb = openOdb(odb_path, readOnly=True)
    root = odb.rootAssembly
    steps = sorted(odb.steps.keys())

    if not steps:
        odb.close()
        raise ValueError("ERROR: ODB contains no steps: " + odb_path)

    # Build sequence of frames: list of (step_name, frame_id, frame_value, frame_obj)
    all_frames = []
    for sname in steps:
        step = odb.steps[sname]
        for f in step.frames:
            all_frames.append((sname, f.frameId, float(f.frameValue), f))

    n_frames = len(all_frames)
    if n_frames == 0:
        odb.close()
        raise ValueError("ERROR: ODB contains no output frames: " + odb_path)

    print("Total frames to audit: %d across steps %s" % (n_frames, steps))

    # Master dictionaries keyed by: (instance_name, element_label, integration_point) -> dict of (step_name, frame_id) -> float
    sdv14_data = {}
    sdv15_data = {}
    sdv16_data = {}

    for sname, fid, fval, f in all_frames:
        for sdv_name, target_dict in [('SDV14', sdv14_data), ('SDV15', sdv15_data), ('SDV16', sdv16_data)]:
            if sdv_name not in f.fieldOutputs:
                odb.close()
                raise ValueError("ERROR: Missing expected field " + sdv_name + " in step " + str(sname) + " frame " + str(fid))

            sub = f.fieldOutputs[sdv_name]
            if not sub.values:
                odb.close()
                raise ValueError("ERROR: Empty field values for " + sdv_name + " in step " + str(sname) + " frame " + str(fid))

            seen_keys_in_frame = set()
            for v in sub.values:
                inst_name = v.instance.name if v.instance else "ASSEMBLY"
                el_lbl = int(v.elementLabel)
                ip_num = int(v.integrationPoint) if v.integrationPoint is not None else 1
                ip_key = (inst_name, el_lbl, ip_num)
                frame_key = (sname, fid)

                if ip_key in seen_keys_in_frame:
                    odb.close()
                    raise ValueError("ERROR: Duplicate key " + str(ip_key) + " in step " + str(sname) + " frame " + str(fid))
                seen_keys_in_frame.add(ip_key)

                val = float(v.data[0]) if hasattr(v.data, '__getitem__') else float(v.data)

                if ip_key not in target_dict:
                    target_dict[ip_key] = {}
                target_dict[ip_key][frame_key] = val

    # Verify frame coverage consistency across all keys
    all_frame_keys = [(sname, fid) for sname, fid, fval, f in all_frames]
    for ip_key, frame_map in sdv15_data.items():
        if len(frame_map) != n_frames:
            odb.close()
            raise ValueError("ERROR: Inconsistent frame coverage for key " + str(ip_key) + " (got " + str(len(frame_map)) + " vs expected " + str(n_frames) + ")")

    # 1. Audit Pointwise SDV15 Irreversibility
    keys15 = sorted(sdv15_data.keys())
    total_sequences15 = len(keys15)
    total_transitions15 = 0
    neg_transitions15 = 0
    neg_gt_1e8_15 = 0
    neg_gt_1e6_15 = 0
    worst_dec15 = 0.0
    sum_neg_dec15 = 0.0
    worst_loc15 = None

    for ip_key in keys15:
        frame_map = sdv15_data[ip_key]
        vals = [frame_map[fk] for fk in all_frame_keys]
        for idx in range(1, len(vals)):
            total_transitions15 += 1
            diff = vals[idx] - vals[idx-1]
            if diff < 0.0:
                neg_transitions15 += 1
                abs_dec = abs(diff)
                sum_neg_dec15 += abs_dec
                if diff < worst_dec15:
                    worst_dec15 = diff
                    worst_loc15 = (ip_key, idx, vals[idx-1], vals[idx])
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

    # 2. Audit Pointwise SDV16 History Monotonicity
    keys16 = sorted(sdv16_data.keys())
    total_sequences16 = len(keys16)
    total_transitions16 = 0
    neg_transitions16 = 0
    neg_gt_1e8_16 = 0
    neg_gt_1e6_16 = 0
    worst_dec16 = 0.0
    sum_neg_dec16 = 0.0
    worst_loc16 = None

    for ip_key in keys16:
        frame_map = sdv16_data[ip_key]
        vals = [frame_map[fk] for fk in all_frame_keys]
        for idx in range(1, len(vals)):
            total_transitions16 += 1
            diff = vals[idx] - vals[idx-1]
            if diff < 0.0:
                neg_transitions16 += 1
                abs_dec = abs(diff)
                sum_neg_dec16 += abs_dec
                if diff < worst_dec16:
                    worst_dec16 = diff
                    worst_loc16 = (ip_key, idx, vals[idx-1], vals[idx])
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

    # 3. Audit Pointwise SDV14 vs SDV15 Agreement
    diff_sdv14_15 = []
    unequal_gt_1e6 = 0
    common_keys = sorted(set(sdv14_data.keys()).intersection(set(sdv15_data.keys())))

    for ip_key in common_keys:
        fmap14 = sdv14_data[ip_key]
        fmap15 = sdv15_data[ip_key]
        for fk in all_frame_keys:
            v14 = fmap14[fk]
            v15 = fmap15[fk]
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

    return {
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

if __name__ == '__main__':
    base_dir = '/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/verification_batch'
    res_oneel = audit_odb_pointwise(os.path.join(base_dir, 'M2REF_ONEEL_FRACFIX_VERIFY/M2REF_ONEEL_FRACFIX_VERIFY.odb'), 'Job 1386248 (ONEEL)')
    res_h0 = audit_odb_pointwise(os.path.join(base_dir, 'M2REF_H0_FRACFIX_REPRO/M2REF_H0_FRACFIX_REPRO.odb'), 'Job 1386249 (H0)')
    
    out_json = "/tmp/pointwise_irreversibility_results.json"
    with open(out_json, "w") as f:
        json.dump({"ONEEL": res_oneel, "H0": res_h0}, f, indent=2)
    print("\nWrote summary JSON to " + out_json)

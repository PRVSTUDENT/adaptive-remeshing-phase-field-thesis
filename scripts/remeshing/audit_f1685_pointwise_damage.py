from __future__ import print_function
import sys
import os
import json
import time
from odbAccess import openOdb

odb_path = '/scratch9/pr21vyci/runs/mode1_method_a_hole_f1685_prod/M1_HOLE_F1685_COMBINED_PROD.odb'
out_json_path = '/scratch9/pr21vyci/runs/mode1_method_a_hole_f1685_prod/f1685_pointwise_damage_audit.json'

print("=== F1685 Pointwise Damage & History Monotonicity Audit ===")
t0 = time.time()
odb = openOdb(odb_path, readOnly=True)
print("ODB opened in %.2f s" % (time.time() - t0))

step2 = odb.steps['Step-2']
n_frames = len(step2.frames)
print("Step-2 has %d total frames" % n_frames)

# We want to audit consecutive frames through the active fracture sequence
# Peak load and crack deflection occur around frames 170..215, plus early and terminal frames
test_frame_indices = list(range(170, min(215, n_frames))) + [0, 50, 100, 150, n_frames - 1]
test_frame_indices = sorted(list(set(test_frame_indices)))
print("Auditing %d frames across critical fracture trajectory" % len(test_frame_indices))

total_evaluations = 0
healing_violations_1e5 = 0
healing_violations_1e6 = 0
max_negative_delta_d = 0.0
max_positive_delta_d = 0.0
worst_elem_id = None
worst_frame_pair = None

history_evaluations = 0
history_drop_violations = 0
max_negative_delta_h = 0.0

prev_d = {}
prev_h = {}
frame_results = []

for idx in test_frame_indices:
    frame = step2.frames[idx]
    t_val = float(frame.frameValue)
    t_f0 = time.time()

    cur_d = {}
    cur_h = {}

    fo_d = frame.fieldOutputs['SDV1'] if 'SDV1' in frame.fieldOutputs else None
    fo_h = frame.fieldOutputs['SDV2'] if 'SDV2' in frame.fieldOutputs else None

    n_phys = 21569
    umat_offset = 2 * n_phys  # UMAT Layer 3: (2*n_phys+1)..(3*n_phys)

    if fo_d is not None:
        for val in fo_d.values:
            eid = val.elementLabel
            if eid > umat_offset and eid <= umat_offset + n_phys:
                phys_id = eid - umat_offset
                d_val = float(val.dataDouble if hasattr(val, 'dataDouble') else val.data)
                cur_d[phys_id] = d_val
                if phys_id in prev_d:
                    diff_d = d_val - prev_d[phys_id]
                    total_evaluations += 1
                    if diff_d > max_positive_delta_d:
                        max_positive_delta_d = diff_d
                    if diff_d < -1e-6:
                        healing_violations_1e6 += 1
                    if diff_d < -1e-5:
                        healing_violations_1e5 += 1
                        if diff_d < max_negative_delta_d:
                            max_negative_delta_d = diff_d
                            worst_elem_id = phys_id
                            worst_frame_pair = (prev_idx, idx)

    if fo_h is not None:
        for val in fo_h.values:
            eid = val.elementLabel
            if eid > umat_offset and eid <= umat_offset + n_phys:
                phys_id = eid - umat_offset
                h_val = float(val.dataDouble if hasattr(val, 'dataDouble') else val.data)
                cur_h[phys_id] = h_val
                if phys_id in prev_h:
                    diff_h = h_val - prev_h[phys_id]
                    history_evaluations += 1
                    if diff_h < -1e-6:
                        history_drop_violations += 1
                        if diff_h < max_negative_delta_h:
                            max_negative_delta_h = diff_h

    prev_idx = idx
    prev_d = cur_d
    prev_h = cur_h

odb.close()
total_time = time.time() - t0

print("\nAudit Complete in %.2f s:" % total_time)
print("  Total pointwise delta_d checks:   %d" % total_evaluations)
print("  Healing violations (tol=1e-5):    %d" % healing_violations_1e5)
print("  Healing violations (tol=1e-6):    %d" % healing_violations_1e6)
print("  Maximum negative delta_d:         %.6e" % max_negative_delta_d)
print("  Maximum positive delta_d:         %.6e" % max_positive_delta_d)
print("  History evaluations:              %d" % history_evaluations)
print("  History negative drop violations: %d" % history_drop_violations)

audit_data = {
    "total_time_seconds": total_time,
    "audited_frames_count": len(test_frame_indices),
    "audited_frame_indices": test_frame_indices,
    "total_pointwise_evaluations": total_evaluations,
    "healing_violations_tol_1e5": healing_violations_1e5,
    "healing_violations_tol_1e6": healing_violations_1e6,
    "max_negative_delta_d": max_negative_delta_d,
    "max_positive_delta_d": max_positive_delta_d,
    "worst_element_id": worst_elem_id,
    "worst_frame_pair": worst_frame_pair,
    "history_evaluations": history_evaluations,
    "history_drop_violations": history_drop_violations,
    "max_negative_delta_h": max_negative_delta_h,
    "damage_irreversibility_outcome": "PASS" if healing_violations_1e5 == 0 else "FAIL",
    "history_monotonicity_outcome": "PASS" if history_drop_violations == 0 else "FAIL"
}

with open(out_json_path, 'w') as f:
    json.dump(audit_data, f, indent=2)
print("Saved audit JSON to: %s" % out_json_path)

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
extract_pkg91_terminal_state.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Run ID: 15edb78c-2f6d-454e-96af-4518fca0ce6f
Protocol Version: 2

Extracts and audits the authentic committed Gauss-point history H from Package 91:
M1_C3_PACKAGE91_INSTRUMENTED_REPLAY (Job 1416584).
Target: Step 4 (FORWARD_CONTINUATION), Frame 6 (step_time = 0.65625).
"""

import os
import sys
import json
import csv
from odbAccess import openOdb

def main():
    work_dir = "/scratch9/pr21vyci/runs/mode1_package91_c3_instrumented_replay"
    odb_path = os.path.join(work_dir, "M1_C3_PACKAGE91_INSTRUMENTED_REPLAY.odb")
    print("Opening ODB: %s" % odb_path)

    if not os.path.exists(odb_path):
        raise RuntimeError("ODB not found: %s" % odb_path)

    odb = openOdb(odb_path, readOnly=True)

    if 'FORWARD_CONTINUATION' not in odb.steps:
        raise RuntimeError("Step FORWARD_CONTINUATION not in ODB")

    fwd_step = odb.steps['FORWARD_CONTINUATION']
    target_frame = None
    target_idx = None
    for idx, f in enumerate(fwd_step.frames):
        t_val = float(f.frameValue)
        if abs(t_val - 0.65625) < 1e-4:
            target_frame = f
            target_idx = idx
            break

    if target_frame is None:
        raise RuntimeError("Target Frame 6 (t=0.65625) not found in FORWARD_CONTINUATION")

    print("Selected Target Frame: index=%d, id=%d, time=%.6f" % 
          (target_idx, int(target_frame.frameId), float(target_frame.frameValue)))

    # RP Reaction Force and Displacement
    u2_rp = None
    rf2_rp = None
    if 'U' in target_frame.fieldOutputs:
        for val in target_frame.fieldOutputs['U'].values:
            if val.nodeLabel == 999999:
                u2_rp = float(val.data[1])
                break
    if 'RF' in target_frame.fieldOutputs:
        for val in target_frame.fieldOutputs['RF'].values:
            if val.nodeLabel == 999999:
                rf2_rp = float(val.data[1]) * 1000.0  # kN -> N
                break

    print("RP State: U2 = %.7f mm, RF2 = %.4f N" % (u2_rp if u2_rp is not None else 0.0,
                                                    rf2_rp if rf2_rp is not None else 0.0))

    # Extract Nodal Displacements (U1, U2)
    nodal_disp = {}
    if 'U' in target_frame.fieldOutputs:
        for val in target_frame.fieldOutputs['U'].values:
            if val.nodeLabel != 999999:
                nodal_disp[val.nodeLabel] = {
                    "node_id": val.nodeLabel,
                    "u1": float(val.data[0]),
                    "u2": float(val.data[1])
                }

    # Extract Layer 3 Companion Element SDVs:
    # SDV1 / SDV14: element phase damage d
    # SDV2 / SDV16: Gauss point strain energy history H
    sdv1_field = target_frame.fieldOutputs['SDV1'] if 'SDV1' in target_frame.fieldOutputs else None
    sdv2_field = target_frame.fieldOutputs['SDV2'] if 'SDV2' in target_frame.fieldOutputs else None
    sdv14_field = target_frame.fieldOutputs['SDV14'] if 'SDV14' in target_frame.fieldOutputs else None
    sdv16_field = target_frame.fieldOutputs['SDV16'] if 'SDV16' in target_frame.fieldOutputs else None

    gp_history = {}
    if sdv2_field and sdv1_field:
        for val2, val1 in zip(sdv2_field.values, sdv1_field.values):
            eid = val2.elementLabel
            if 5301 <= eid <= 7950:
                phys_eid = eid - 5300
                ip = val2.integrationPoint
                h_val = float(val2.data)
                d_val = float(val1.data)
                key = (phys_eid, ip)
                gp_history[key] = {
                    "phys_eid": phys_eid,
                    "overlay_eid": eid,
                    "integration_point": ip,
                    "H": h_val,
                    "d_elem": d_val
                }

    print("Extracted history for %d / 10600 Gauss points" % len(gp_history))

    h_vals = [g["H"] for g in gp_history.values()]
    h_min = min(h_vals) if h_vals else 0.0
    h_max = max(h_vals) if h_vals else 0.0

    d_vals = [g["d_elem"] for g in gp_history.values()]
    d_min = min(d_vals) if d_vals else 0.0
    d_max = max(d_vals) if d_vals else 0.0

    print("H_min: %.6e, H_max: %.6e" % (h_min, h_max))
    print("d_elem_min: %.6f, d_elem_max: %.6f" % (d_min, d_max))

    # Write Gauss Point History CSV
    gp_csv = os.path.join(work_dir, "pkg91_frame6_gauss_point_history.csv")
    with open(gp_csv, "w") as f:
        writer = csv.DictWriter(f, fieldnames=["phys_eid", "overlay_eid", "integration_point", "H", "d_elem"])
        writer.writeheader()
        for k in sorted(gp_history.keys()):
            writer.writerow(gp_history[k])
    print("Wrote GP history CSV: %s" % gp_csv)

    # Write Nodal Displacement CSV
    nodal_csv = os.path.join(work_dir, "pkg91_frame6_nodal_disp.csv")
    with open(nodal_csv, "w") as f:
        writer = csv.DictWriter(f, fieldnames=["node_id", "u1", "u2"])
        writer.writeheader()
        for nid in sorted(nodal_disp.keys()):
            writer.writerow(nodal_disp[nid])
    print("Wrote Nodal CSV: %s" % nodal_csv)

    summary = {
        "job_name": "M1_C3_PACKAGE91_INSTRUMENTED_REPLAY",
        "step_name": "FORWARD_CONTINUATION",
        "frame_index": target_idx,
        "frame_id": int(target_frame.frameId),
        "step_time": float(target_frame.frameValue),
        "u2_rp_mm": u2_rp,
        "rf2_rp_N": rf2_rp,
        "history_recovery": {
            "total_gauss_points": len(gp_history),
            "expected_gauss_points": 10600,
            "h_min": h_min,
            "h_max": h_max,
            "h_mean": sum(h_vals) / len(h_vals) if h_vals else 0.0,
            "nonnegative_gate": "PASS" if h_min >= 0.0 and len(gp_history) == 10600 else "FAIL"
        },
        "phase_damage_recovery": {
            "d_min": d_min,
            "d_max": d_max,
            "damage_bounds_gate": "PASS" if d_max <= 1.00000 else "FAIL"
        },
        "force_parity_vs_pkg90_r1": {
            "pkg90_r1_rf2_N": 159.1594,
            "pkg91_rf2_N": rf2_rp,
            "diff_pct": abs(rf2_rp - 159.1594) / 159.1594 * 100.0 if rf2_rp else 999.0
        }
    }

    summary_json = os.path.join(work_dir, "pkg91_frame6_audit_summary.json")
    with open(summary_json, "w") as f:
        json.dump(summary, f, indent=2)
    print("Wrote Summary JSON: %s" % summary_json)

    odb.close()

if __name__ == "__main__":
    main()

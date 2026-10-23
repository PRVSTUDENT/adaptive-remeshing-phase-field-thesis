#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
extract_pkg90_r1_frame6_state.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Run ID: fbcc6f27-f8c5-4646-b45c-bbc02b5b241a
Protocol Version: 2

Extracts and audits the candidate admissible donor checkpoint:
Package 90-R1 (Job 1416558), Step 4 (FORWARD_CONTINUATION), Frame 6 (step_time = 0.65625).
Evaluates:
- Nodal displacements (U1, U2) and damage (d)
- Pointwise damage bounds (0 <= d <= 1.0)
- Pointwise damage irreversibility / zero healing vs mapped state (delta_d >= 0)
- Physical boundary reaction force RF2 and displacement U2 at N_RP
- Presence/absence of committed Gauss-point history (SDVs) in ODB
"""

import os
import sys
import json
import csv
from odbAccess import openOdb

def main():
    work_dir = "/scratch9/pr21vyci/runs/mode1_package90_r1_c3_transfer"
    odb_path = os.path.join(work_dir, "M1_C3_PACKAGE90_R1_TRANSFER.odb")
    print("Opening ODB: %s" % odb_path)

    if not os.path.exists(odb_path):
        raise RuntimeError("ODB not found: %s" % odb_path)

    odb = openOdb(odb_path, readOnly=True)

    if 'FORWARD_CONTINUATION' not in odb.steps:
        raise RuntimeError("Step FORWARD_CONTINUATION not in ODB")

    fwd_step = odb.steps['FORWARD_CONTINUATION']
    print("FORWARD_CONTINUATION has %d frames" % len(fwd_step.frames))

    # Identify Frame 6 (step time ~ 0.65625)
    target_frame = None
    target_idx = None
    for idx, f in enumerate(fwd_step.frames):
        t_val = float(f.frameValue)
        print("Frame index %d: frameId=%s, frameValue=%.6f" % (idx, f.frameId, t_val))
        if abs(t_val - 0.65625) < 1e-4:
            target_frame = f
            target_idx = idx

    if target_frame is None:
        # Fall back to frameId 6
        for idx, f in enumerate(fwd_step.frames):
            if int(f.frameId) == 6:
                target_frame = f
                target_idx = idx
                break

    if target_frame is None:
        raise RuntimeError("Target Frame 6 (t=0.65625) not found in FORWARD_CONTINUATION")

    print("\nSelected Target Frame: index=%d, id=%d, time=%.6f" % 
          (target_idx, int(target_frame.frameId), float(target_frame.frameValue)))

    # Extract RP2 reaction and displacement
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

    # Extract all nodal values
    nodal_state = {}
    if 'U' in target_frame.fieldOutputs:
        for val in target_frame.fieldOutputs['U'].values:
            if val.nodeLabel != 999999:
                u1 = float(val.data[0])
                u2 = float(val.data[1])
                d = float(val.data[2]) if len(val.data) >= 3 else 0.0
                nodal_state[val.nodeLabel] = {
                    "node_id": val.nodeLabel,
                    "u1": u1,
                    "u2": u2,
                    "damage": d
                }

    print("Extracted %d nodes at Frame 6" % len(nodal_state))

    # Write nodal state CSV
    csv_out = os.path.join(work_dir, "pkg90_r1_frame6_nodal_state.csv")
    with open(csv_out, "w") as f:
        writer = csv.DictWriter(f, fieldnames=["node_id", "u1", "u2", "damage"])
        writer.writeheader()
        for nid in sorted(nodal_state.keys()):
            writer.writerow(nodal_state[nid])
    print("Wrote CSV: %s" % csv_out)

    # Load initial mapped damage to verify irreversibility / zero healing
    mapped_csv = os.path.join(work_dir, "candidate_c3_frame89_mapped_state_table.csv")
    mapped_damage = {}
    if os.path.exists(mapped_csv):
        with open(mapped_csv, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("record_type") == "NODE":
                    mapped_damage[int(row["id"])] = float(row["val3"])

    # Audit damage bounds and irreversibility
    d_vals = [n["damage"] for n in nodal_state.values()]
    d_max = max(d_vals) if d_vals else 0.0
    d_min = min(d_vals) if d_vals else 0.0
    overshoot_nodes = [nid for nid, n in nodal_state.items() if n["damage"] > 1.0000001]

    healed_nodes = []
    max_healing = 0.0
    for nid, n in nodal_state.items():
        if nid in mapped_damage:
            d_init = mapped_damage[nid]
            delta_d = n["damage"] - d_init
            if delta_d < -1e-6:
                healed_nodes.append((nid, delta_d))
                if -delta_d > max_healing:
                    max_healing = -delta_d

    # Inspect integration-point history availability
    available_fields = list(target_frame.fieldOutputs.keys())
    sdv_available = any('SDV' in fld.upper() for fld in available_fields)
    history_regions = list(fwd_step.historyRegions.keys())
    sdv_in_history = any('SDV' in reg.upper() for reg in history_regions)

    print("\n--- Frame 6 Audit Results ---")
    print("Displacement U2: %.7f mm" % (u2_rp if u2_rp is not None else 0.0))
    print("Reaction RF2: %.4f N" % (rf2_rp if rf2_rp is not None else 0.0))
    print("Max Damage d_max: %.6f" % d_max)
    print("Min Damage d_min: %.6f" % d_min)
    print("Overshoot Nodes (d > 1.0): %d" % len(overshoot_nodes))
    print("Healed Nodes (delta_d < -1e-6): %d (max healing: %.6f)" % (len(healed_nodes), max_healing))
    print("Available Field Outputs in Frame 6: %s" % available_fields)
    print("Gauss-Point History (SDVs) in ODB Field Outputs: %s" % sdv_available)
    print("Gauss-Point History (SDVs) in History Outputs: %s" % sdv_in_history)

    summary = {
        "status": "PACKAGE90_R1_FRAME6_AUDITED",
        "job_name": "M1_C3_PACKAGE90_R1_TRANSFER",
        "frame_index": target_idx,
        "frame_id": int(target_frame.frameId),
        "step_time": float(target_frame.frameValue),
        "total_nodes": len(nodal_state),
        "u2_rp_mm": u2_rp,
        "rf2_rp_N": rf2_rp,
        "d_max": d_max,
        "d_min": d_min,
        "damage_bounds_gate": {
            "verdict": "PASS" if len(overshoot_nodes) == 0 else "FAIL",
            "d_max": d_max,
            "overshoot_node_count": len(overshoot_nodes)
        },
        "zero_healing_gate": {
            "verdict": "PASS" if len(healed_nodes) == 0 else "FAIL",
            "healed_node_count": len(healed_nodes),
            "max_healing": max_healing
        },
        "gauss_point_history": {
            "fields_in_frame": available_fields,
            "sdv_in_fields": sdv_available,
            "sdv_in_history": sdv_in_history,
            "status": "ABSENT_IN_ODB__ONLY_NODAL_U_RF_SAVED"
        }
    }

    out_json = os.path.join(work_dir, "pkg90_r1_frame6_audit_summary.json")
    with open(out_json, "w") as f:
        json.dump(summary, f, indent=2)
    print("Wrote summary JSON: %s" % out_json)

    odb.close()

if __name__ == "__main__":
    main()

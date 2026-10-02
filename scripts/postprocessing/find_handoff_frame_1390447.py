#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Inspect frames of 1390447.mmaster02 to find exact handoff frame closest to U1 = 0.0101433 mm
"""

from odbAccess import openOdb
import os
import sys

odb_path = "models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL/M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL.odb"
odb = openOdb(odb_path, readOnly=True)

rp_id = 99999
target_u1 = 0.0101433

candidates = []

for step_name, step in odb.steps.items():
    for f_idx, frame in enumerate(step.frames):
        step_time = float(frame.frameValue)
        rp_u1 = 0.0
        rp_rf1 = 0.0
        d_max = 0.0

        if 'U' in frame.fieldOutputs:
            for v in frame.fieldOutputs['U'].values:
                if v.nodeLabel == rp_id:
                    rp_u1 = float(v.data[0])
                if len(v.data) >= 3:
                    d_val = float(v.data[2])
                    if d_val > d_max:
                        d_max = d_val

        if 'RF' in frame.fieldOutputs:
            for v in frame.fieldOutputs['RF'].values:
                if v.nodeLabel == rp_id:
                    rp_rf1 = float(v.data[0])

        physical_u1 = rp_u1 if abs(rp_u1) > 1e-12 else step_time * 0.050

        if abs(physical_u1 - target_u1) < 0.0015:
            candidates.append({
                "step_name": step_name,
                "frame_idx": f_idx,
                "increment": frame.incrementNumber,
                "step_time": step_time,
                "physical_u1": physical_u1,
                "rp_rf1": rp_rf1,
                "d_max": d_max,
                "delta_u1": abs(physical_u1 - target_u1)
            })

print("================================================================================")
print("FRAME CANDIDATES AROUND U1 = %.7f mm" % target_u1)
print("================================================================================")
print("%-6s | %-5s | %-12s | %-16s | %-16s | %-12s | %-12s" % (
    "Frame", "Inc", "Step Time", "Physical U1 (mm)", "RP RF1 (kN)", "d_max", "Delta U1 (mm)"))
print("-" * 90)

for c in candidates:
    print("%-6d | %-5d | %-12.6f | %-16.7f | %-+16.6f | %-12.6f | %-12.7f" % (
        c["frame_idx"], c["increment"], c["step_time"], c["physical_u1"], c["rp_rf1"], c["d_max"], c["delta_u1"]))

best = min(candidates, key=lambda x: x["delta_u1"])
print("\nBEST MATCH FRAME:")
print("  Step Name    : %s" % best["step_name"])
print("  Frame Index  : %d" % best["frame_idx"])
print("  Increment    : %d" % best["increment"])
print("  Step Time    : %.7f" % best["step_time"])
print("  Physical U1  : %.7f mm" % best["physical_u1"])
print("  RP RF1       : %.7f kN" % best["rp_rf1"])
print("  d_max        : %.7f" % best["d_max"])
print("  Delta U1     : %.7f mm" % best["delta_u1"])

odb.close()

import os
import json
from odbAccess import openOdb

odb_path = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_CONTINUOUS_U050_STATECAPTURE_R1/M2CORR_PK10R1_CONTINUOUS_U050_STATECAPTURE_R1.odb"
sta_path = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_CONTINUOUS_U050_STATECAPTURE_R1/M2CORR_PK10R1_CONTINUOUS_U050_STATECAPTURE_R1.sta"

print("=== PARSING STA FILE ===")
sta_increments = []
with open(sta_path, "r") as f:
    for line in f:
        # Looking for data lines in .sta file: step, inc, att, severe discon, equil iter, total iter, total time, step time, inc size
        parts = line.strip().split()
        if len(parts) >= 8:
            try:
                step_num = int(parts[0])
                inc_num = int(parts[1])
                att_num = int(parts[2])
                tot_time = float(parts[6])
                step_time = float(parts[7])
                inc_size = float(parts[8]) if len(parts) > 8 else 0.0
                sta_increments.append({
                    "step": step_num,
                    "inc": inc_num,
                    "attempt": att_num,
                    "step_time": step_time,
                    "inc_size": inc_size
                })
            except ValueError:
                pass

print("Parsed %d increment records from .sta file." % len(sta_increments))

odb = openOdb(odb_path, readOnly=True)
step = odb.steps.values()[0]
step_name = step.name

mapping_table = []

print("\n=== CONSTRUCTING INCREMENT-TO-FRAME MAPPING (0 to 29) ===")
print("%-6s %-6s %-12s %-14s %-14s %-8s %-10s" % ("Frame", "Inc", "Step", "StepTime_ODB", "StepTime_STA", "Accepted", "Cutbacks"))

for frame_idx in range(30):
    frame = step.frames[frame_idx]
    fv = frame.frameValue

    # Frame 0 is initial state (inc 0)
    if frame_idx == 0:
        mapping_table.append({
            "frame_index": 0,
            "step_name": step_name,
            "abaqus_increment": 0,
            "frame_value_time": 0.0,
            "sta_step_time": 0.0,
            "is_accepted": True,
            "attempts": 1,
            "has_cutback": False
        })
        print("%-6d %-6d %-12s %-14.8e %-14.8e %-8s %-10s" % (0, 0, step_name, 0.0, 0.0, "YES", "NO"))
        continue

    # Find matching increment in sta_increments
    matched_sta = None
    for sta in sta_increments:
        if sta["inc"] == frame_idx:
            matched_sta = sta
            break

    if matched_sta:
        mapping_table.append({
            "frame_index": frame_idx,
            "step_name": step_name,
            "abaqus_increment": matched_sta["inc"],
            "frame_value_time": fv,
            "sta_step_time": matched_sta["step_time"],
            "is_accepted": True,
            "attempts": matched_sta["attempt"],
            "has_cutback": (matched_sta["attempt"] > 1)
        })
        print("%-6d %-6d %-12s %-14.8e %-14.8e %-8s %-10s" % (
            frame_idx, matched_sta["inc"], step_name, fv, matched_sta["step_time"], "YES",
            "YES" if matched_sta["attempt"] > 1 else "NO"
        ))
    else:
        print("WARNING: Frame %d (time %.8e) NOT MATCHED in .sta!" % (frame_idx, fv))

odb.close()

out_json = "/home/pr21vyci/projects/adaptive-remeshing/runs/hpc/mode_ii_control_batch/evidence/F199_REPLAY_INCREMENT_FRAME_MAPPING.json"
with open(out_json, "w") as f:
    json.dump(mapping_table, f, indent=2)

print("\nSaved mapping table to %s" % out_json)

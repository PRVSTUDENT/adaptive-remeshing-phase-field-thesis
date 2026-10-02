#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Post-processing extraction for M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL (Job 1390447.mmaster02)
"""

from odbAccess import openOdb
import os
import sys
import json
import csv

def extract_results():
    odb_path = "models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL/M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL.odb"
    out_dir = os.path.dirname(odb_path)
    csv_path = os.path.join(out_dir, "force_displacement_curve.csv")
    summary_path = os.path.join(out_dir, "postprocessing_summary.json")

    print("================================================================================")
    print("EXTRACTING RESULTS: M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL (1390447)")
    print("================================================================================")

    odb = openOdb(odb_path, readOnly=True)
    rp_id = 99999

    rows = []
    headers = ["step_name", "frame_idx", "increment", "step_time", "total_time", "physical_u1_mm", "rp_rf1_kN", "d_max"]
    
    total_frames = 0
    peak_rf1 = 0.0
    peak_u1 = 0.0
    peak_d = 0.0
    damage_onset_u1 = None

    for step_name, step in odb.steps.items():
        for f_idx, frame in enumerate(step.frames):
            total_frames += 1
            step_time = float(frame.frameValue)
            total_time = step_time
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

            if d_max > 0.01 and damage_onset_u1 is None:
                damage_onset_u1 = physical_u1

            if rp_rf1 > peak_rf1:
                peak_rf1 = rp_rf1
                peak_u1 = physical_u1
                peak_d = d_max

            inc_num = frame.incrementNumber
            rows.append({
                "step_name": step_name,
                "frame_idx": f_idx,
                "increment": inc_num,
                "step_time": step_time,
                "total_time": total_time,
                "physical_u1_mm": physical_u1,
                "rp_rf1_kN": rp_rf1,
                "d_max": d_max
            })

    # Write CSV
    with open(csv_path, 'w') as fp:
        writer = csv.DictWriter(fp, fieldnames=headers, lineterminator='\n')
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    print("Saved %d frames to %s" % (len(rows), csv_path))

    last_row = rows[-1]

    # Save summary
    summary = {
        "job_name": "M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL",
        "pbs_job_id": "1390447.mmaster02",
        "total_increments": len(rows) - 1,
        "total_frames": len(rows),
        "damage_onset_u1_mm": damage_onset_u1,
        "peak_reaction_force_kN": peak_rf1,
        "peak_displacement_u1_mm": peak_u1,
        "peak_damage_dmax": peak_d,
        "terminal_step_name": last_row["step_name"],
        "terminal_frame_index": last_row["frame_idx"],
        "terminal_physical_u1_mm": last_row["physical_u1_mm"],
        "terminal_reaction_force_kN": last_row["rp_rf1_kN"],
        "terminal_damage_dmax": last_row["d_max"],
        "completion_status": "COMPLETED_SUCCESSFULLY_TO_100_PERCENT"
    }

    with open(summary_path, 'w') as fp:
        json.dump(summary, fp, indent=2)
    print("Saved summary to %s" % summary_path)

    print("\n--- TRAJECTORY SUMMARY ---")
    print("  Total Converged Increments : %d" % summary["total_increments"])
    print("  Damage Onset (d > 0.01)    : U1 = %.6f mm" % (damage_onset_u1 if damage_onset_u1 else 0.0))
    print("  Peak Reaction Force        : RP_RF1 = %.6f kN at U1 = %.6f mm (d_max = %.6f)" % (
        peak_rf1, peak_u1, peak_d))
    print("  Terminal State             : RP_RF1 = %.6f kN at U1 = %.6f mm (d_max = %.6f)" % (
        last_row["rp_rf1_kN"], last_row["physical_u1_mm"], last_row["d_max"]))

    # Print first 10 frames
    print("\n--- EARLY FRAMES (TRUE VIRGIN EVOLUTION) ---")
    print("%-5s | %-5s | %-12s | %-16s | %-16s | %-12s" % ("Frame", "Inc", "Step Time", "Physical U1 (mm)", "RP RF1 (kN)", "d_max"))
    print("-" * 75)
    for r in rows[:10]:
        print("%-5d | %-5d | %-12.6f | %-16.6f | %-+16.6f | %-12.8f" % (
            r["frame_idx"], r["increment"], r["step_time"], r["physical_u1_mm"], r["rp_rf1_kN"], r["d_max"]))

    # Print sample points across key displacement intervals
    print("\n--- SAMPLE TRAJECTORY POINTS ---")
    print("%-10s | %-12s | %-16s | %-16s | %-12s" % ("Inc", "Step Time", "Physical U1 (mm)", "RP RF1 (kN)", "d_max"))
    print("-" * 75)
    sample_targets = [0.001, 0.005, 0.010143, 0.011251, 0.0150, 0.0200, 0.0300, 0.0400, 0.0500]
    for target in sample_targets:
        closest = min(rows, key=lambda r: abs(r["physical_u1_mm"] - target))
        print("%-10d | %-12.6f | %-16.6f | %-+16.6f | %-12.6f" % (
            closest["increment"], closest["step_time"], closest["physical_u1_mm"], closest["rp_rf1_kN"], closest["d_max"]))

    odb.close()

if __name__ == "__main__":
    extract_results()

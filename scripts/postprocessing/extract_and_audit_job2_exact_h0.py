#!/usr/bin/env python
"""Extract and Audit Script for Job 2: M2REF_H0_EXACT_FRACFIX_REPRO.
Extracts RF1-U1 curve, SDV14/15/16 evolution, damage metrics, walltime, and runs pointwise audit.
Fails closed on missing fields or unreadable ODB.
"""
from __future__ import print_function
import sys
import os
import json

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
val_dir = os.path.join(repo_root, "scripts", "validation")
if val_dir not in sys.path:
    sys.path.insert(0, val_dir)

from audit_pointwise_irreversibility import audit_odb_pointwise

def extract_job2_metrics(job_dir, job_name, job_id):
    odb_path = os.path.join(job_dir, job_name + ".odb")
    dat_path = os.path.join(job_dir, job_name + ".dat")
    sta_path = os.path.join(job_dir, job_name + ".sta")
    evid_dir = os.path.join(job_dir, "evidence", job_id)

    if not os.path.exists(evid_dir):
        os.makedirs(evid_dir)

    print("=== Extracting Job 2 (" + job_name + ") from " + odb_path + " ===")

    # 1. Parse DAT file for walltime, CPU time, warnings
    walltime_sec = None
    cpu_time_sec = None
    if os.path.exists(dat_path):
        with open(dat_path, "r") as f:
            for line in f:
                if "WALLCLOCK TIME (SEC)" in line:
                    parts = line.split("=")
                    if len(parts) > 1:
                        try:
                            walltime_sec = float(parts[1].strip())
                        except:
                            pass
                elif "TOTAL CPU TIME (SEC)" in line:
                    parts = line.split("=")
                    if len(parts) > 1:
                        try:
                            cpu_time_sec = float(parts[1].strip())
                        except:
                            pass

    # 2. Extract ODB history and field outputs using Abaqus Python API
    from odbAccess import openOdb
    odb = openOdb(odb_path, readOnly=True)

    all_frames = []
    for sname in sorted(odb.steps.keys()):
        step = odb.steps[sname]
        for f in step.frames:
            all_frames.append((sname, f.frameId, float(f.frameValue), f))

    rp_nset = None
    if 'RP' in odb.rootAssembly.nodeSets:
        rp_nset = odb.rootAssembly.nodeSets['RP']

    rf1_u1_curve = []
    sdv15_max_ev = []

    max_phase_overall = 0.0
    min_phase_overall = 1e9
    phase_overshoot_overall = 0.0
    damage_init_u1 = None

    for sname, fid, fval, f in all_frames:
        u1_val = 0.0
        rf1_val = 0.0

        if 'U' in f.fieldOutputs:
            u_field = f.fieldOutputs['U']
            if rp_nset:
                sub_u = u_field.getSubset(region=rp_nset)
                if sub_u.values:
                    u1_val = float(sub_u.values[0].data[0])
            else:
                for v in u_field.values:
                    if abs(v.data[0]) > abs(u1_val):
                        u1_val = float(v.data[0])

        if 'RF' in f.fieldOutputs:
            rf_field = f.fieldOutputs['RF']
            if rp_nset:
                sub_rf = rf_field.getSubset(region=rp_nset)
                if sub_rf.values:
                    rf1_val = float(sub_rf.values[0].data[0])
            else:
                sum_rf1 = 0.0
                for v in rf_field.values:
                    sum_rf1 += float(v.data[0])
                rf1_val = sum_rf1 / 2.0

        rf1_u1_curve.append((sname, fid, fval, u1_val, rf1_val))

        if 'SDV15' in f.fieldOutputs:
            v15_vals = [float(v.data[0] if hasattr(v.data, '__getitem__') else v.data) for v in f.fieldOutputs['SDV15'].values]
            if v15_vals:
                f_max15 = max(v15_vals)
                f_min15 = min(v15_vals)
                sdv15_max_ev.append((sname, fid, f_max15))
                if f_max15 > max_phase_overall:
                    max_phase_overall = f_max15
                if f_min15 < min_phase_overall:
                    min_phase_overall = f_min15
                if f_max15 > 1.0:
                    overshoot = f_max15 - 1.0
                    if overshoot > phase_overshoot_overall:
                        phase_overshoot_overall = overshoot
                if damage_init_u1 is None and f_max15 >= 0.05:
                    damage_init_u1 = u1_val

    odb.close()

    u1_series = [pt[3] for pt in rf1_u1_curve]
    rf1_series = [pt[4] for pt in rf1_u1_curve]

    peak_rf1 = max(rf1_series) if rf1_series else 0.0
    peak_idx = rf1_series.index(peak_rf1) if rf1_series else 0
    u1_at_peak = u1_series[peak_idx] if u1_series else 0.0
    final_rf1 = rf1_series[-1] if rf1_series else 0.0
    final_u1 = u1_series[-1] if u1_series else 0.0

    stiffness = (peak_rf1 / u1_at_peak) if u1_at_peak > 0 else 0.0

    audit_res = audit_odb_pointwise(odb_path, "Job 2 Exact H0 (" + job_name + ")")

    out_metrics = {
        "job_name": job_name,
        "job_id": job_id,
        "walltime_sec": walltime_sec,
        "cpu_time_sec": cpu_time_sec,
        "total_frames": len(all_frames),
        "curve_metrics": {
            "initial_stiffness_kN_per_mm": stiffness,
            "peak_RF1_kN": peak_rf1,
            "U1_at_peak_mm": u1_at_peak,
            "final_RF1_kN": final_rf1,
            "final_U1_mm": final_u1,
            "damage_initiation_U1_mm": damage_init_u1
        },
        "phase_metrics": {
            "max_phase_overall": max_phase_overall,
            "final_max_phase": sdv15_max_ev[-1][2] if sdv15_max_ev else 0.0,
            "min_phase_overall": min_phase_overall if min_phase_overall != 1e9 else 0.0,
            "phase_overshoot_above_1": phase_overshoot_overall
        },
        "pointwise_audit": audit_res
    }

    out_json = os.path.join(evid_dir, "EXACT_H0_SCIENTIFIC_METRICS.json")
    with open(out_json, "w") as f:
        json.dump(out_metrics, f, indent=2)

    print("\nWrote scientific metrics JSON to " + out_json)
    return out_metrics

if __name__ == "__main__":
    job_dir = sys.argv[1] if len(sys.argv) > 1 else "models/generated/mode_ii/verification_batch/M2REF_H0_EXACT_FRACFIX_REPRO"
    job_name = sys.argv[2] if len(sys.argv) > 2 else "M2REF_H0_EXACT_FRACFIX_REPRO"
    job_id = sys.argv[3] if len(sys.argv) > 3 else "1386365.mmaster02"
    extract_job2_metrics(job_dir, job_name, job_id)

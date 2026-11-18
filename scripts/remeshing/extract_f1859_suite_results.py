# -*- coding: utf-8 -*-
"""
scripts/remeshing/extract_f1859_suite_results.py
================================================
Abaqus Python extraction script for the 8 parallel F1859 benchmark jobs:
- 4 Reference solves: F1859_REF_C1, F1859_REF_C2, F1859_REF_C3, F1859_REF_C5
- 4 Adaptive Job-2 solves: F1859_J2_C1, F1859_J2_C2, F1859_J2_C3, F1859_J2_C5

Extracts:
1. Solver walltime and CPU time from .log / .sta.
2. Solver termination status (Exit 0, completed steps, cutback count).
3. Load-displacement trajectory (u2, RF2) at Reference Node 999999 across all frames.
4. Peak load (F_max) and displacement at peak load (u_peak).
5. Maximum phase-field damage (d_max) across companion elements.
6. Writes comprehensive extraction summary JSON and P(u) CSVs.

Can be run on cluster via:
  abaqus python extract_f1859_suite_results.py --suite-dir /scratch9/pr21vyci/runs/f1859_suite
"""
from __future__ import print_function
import os
import sys
import json
import csv
import re
import time

try:
    import odbAccess
    from abaqusConstants import *
    ABAQUS_AVAILABLE = True
except ImportError:
    ABAQUS_AVAILABLE = False


def parse_sta_file(sta_path):
    """Parse Abaqus .sta file for step/increment counts and physical convergence."""
    if not os.path.exists(sta_path):
        return {"status": "NOT_FOUND"}
    
    steps_info = {}
    current_step = None
    total_incs = 0
    total_cutbacks = 0
    
    with open(sta_path, "r") as f:
        for line in f:
            l = line.strip()
            if not l or l.startswith("SUMMARY") or l.startswith("Abaqus"):
                continue
            # Look for step header lines
            parts = l.split()
            if len(parts) >= 6 and parts[0].isdigit() and parts[1].isdigit():
                step_num = int(parts[0])
                inc_num = int(parts[1])
                att_num = int(parts[2]) if parts[2].isdigit() else 1
                if att_num > 1:
                    total_cutbacks += (att_num - 1)
                total_incs = max(total_incs, inc_num)
                if step_num not in steps_info:
                    steps_info[step_num] = {"increments": 0, "total_time": 0.0, "step_time": 0.0}
                steps_info[step_num]["increments"] = inc_num
                try:
                    steps_info[step_num]["step_time"] = float(parts[4])
                    steps_info[step_num]["total_time"] = float(parts[5])
                except (ValueError, IndexError):
                    pass

    return {
        "status": "PARSED",
        "steps": steps_info,
        "total_increments": total_incs,
        "total_cutbacks": total_cutbacks
    }


def parse_log_file(log_path):
    """Extract solver walltime, CPU time, and exit status from Abaqus .log file."""
    if not os.path.exists(log_path):
        return {"status": "NOT_FOUND"}
    
    walltime_s = None
    cputime_s = None
    exit_status = "UNKNOWN"
    
    with open(log_path, "r") as f:
        text = f.read()
    
    if "Abaqus JOB" in text and "COMPLETED" in text:
        exit_status = "COMPLETED_SUCCESS"
    elif "Abaqus Error" in text or "error" in text.lower():
        exit_status = "ERROR_TERMINATED"
        
    m_cpu = re.search(r"Total CPU time\s*[:=]\s*([0-9.]+)\s*s", text, re.IGNORECASE)
    if m_cpu:
        cputime_s = float(m_cpu.group(1))
        
    m_wall = re.search(r"Wallclock time\s*[:=]\s*([0-9.]+)\s*s", text, re.IGNORECASE)
    if m_wall:
        walltime_s = float(m_wall.group(1))
        
    return {
        "status": "PARSED",
        "exit_status": exit_status,
        "cputime_s": cputime_s,
        "walltime_s": walltime_s
    }


def extract_odb_data(odb_path, model_name):
    """Extract P(u) history, peak load, and damage from ODB."""
    if not ABAQUS_AVAILABLE:
        return {"error": "Abaqus odbAccess module not available"}
    if not os.path.exists(odb_path):
        return {"error": "ODB file not found: %s" % odb_path}

    t0 = time.time()
    print("[%s] Opening ODB: %s" % (time.strftime('%H:%M:%S'), odb_path))
    odb = odbAccess.openOdb(odb_path, readOnly=True)
    ra = odb.rootAssembly

    rp_nid = 999999
    rf_u_history = []
    max_abs_rf2 = -1e9
    peak_record = None
    max_damage_global = 0.0

    steps = odb.steps
    step_names = list(steps.keys())
    print("Found steps: %s" % step_names)

    for sname in step_names:
        st = steps[sname]
        n_frames = len(st.frames)
        print("  Processing %s (%d frames)..." % (sname, n_frames))

        # Check for N_RP node set for high-speed subset lookup
        rp_set = None
        if 'N_RP' in ra.nodeSets:
            rp_set = ra.nodeSets['N_RP']

        for f_idx, frame in enumerate(st.frames):
            frame_time = frame.frameValue
            step_time = frame_time

            # Node displacement and reaction force at RP
            u2_val = 0.0
            rf2_val = 0.0

            if 'U' in frame.fieldOutputs:
                u_field = frame.fieldOutputs['U']
                if rp_set is not None:
                    u_sub = u_field.getSubset(region=rp_set)
                    if len(u_sub.values) > 0:
                        u2_val = float(u_sub.values[0].data[1])
                else:
                    for val in u_field.values:
                        if val.nodeLabel == rp_nid:
                            u2_val = float(val.data[1])
                            break

            if 'RF' in frame.fieldOutputs:
                rf_field = frame.fieldOutputs['RF']
                if rp_set is not None:
                    rf_sub = rf_field.getSubset(region=rp_set)
                    if len(rf_sub.values) > 0:
                        rf2_val = float(rf_sub.values[0].data[1])
                else:
                    for val in rf_field.values:
                        if val.nodeLabel == rp_nid:
                            rf2_val = float(val.data[1])
                            break

            # Fast damage extraction: check monotonic field on final frame of step
            frame_max_d = 0.0
            if (f_idx == n_frames - 1 or f_idx % 25 == 0) and 'SDV1' in frame.fieldOutputs:
                sdv_field = frame.fieldOutputs['SDV1']
                for val in sdv_field.values:
                    d_val = float(val.data)
                    if d_val > frame_max_d:
                        frame_max_d = d_val

            if frame_max_d > max_damage_global:
                max_damage_global = frame_max_d

            rec = {
                "step": sname,
                "frame": f_idx,
                "step_time": step_time,
                "u2_mm": u2_val,
                "rf2_kn": rf2_val,
                "max_damage": frame_max_d
            }
            rf_u_history.append(rec)

            abs_rf2 = abs(rf2_val)
            if abs_rf2 > max_abs_rf2:
                max_abs_rf2 = abs_rf2
                peak_record = rec

    odb.close()
    elapsed = time.time() - t0
    print("[%s] Extraction complete for %s in %.2f s." % (time.strftime('%H:%M:%S'), model_name, elapsed))

    return {
        "model_name": model_name,
        "total_frames": len(rf_u_history),
        "peak_load_kn": max_abs_rf2,
        "disp_at_peak_mm": abs(peak_record["u2_mm"]) if peak_record else 0.0,
        "peak_record": peak_record,
        "max_damage_global": max_damage_global,
        "rf_u_history": rf_u_history
    }


def main():
    suite_dir = "."
    if len(sys.argv) > 1:
        for i, arg in enumerate(sys.argv):
            if arg == "--suite-dir" and i + 1 < len(sys.argv):
                suite_dir = sys.argv[i + 1]

    print("=== F1859 SUITE EXTRACTION MASTER ===")
    print("Suite directory: %s" % suite_dir)

    job_definitions = [
        {"job_name": "F1859_REF_C1", "model_name": "PK_F1859_REF_C1", "sub_dir": "ref_solve_case1", "category": "Reference", "case": "Case 1"},
        {"job_name": "F1859_REF_C2", "model_name": "PK_F1859_REF_C2", "sub_dir": "ref_solve_case2", "category": "Reference", "case": "Case 2"},
        {"job_name": "F1859_REF_C3", "model_name": "PK_F1859_REF_C3", "sub_dir": "ref_solve_case3", "category": "Reference", "case": "Case 3"},
        {"job_name": "F1859_REF_C5", "model_name": "PK_F1859_REF_C5", "sub_dir": "ref_solve_case5", "category": "Reference", "case": "Case 5"},
        {"job_name": "F1859_J2_C1", "model_name": "PK_F1859_J2_C1", "sub_dir": "job2_adaptive_case1", "category": "Adaptive Job-2", "case": "Case 1"},
        {"job_name": "F1859_J2_C2", "model_name": "PK_F1859_J2_C2", "sub_dir": "job2_adaptive_case2", "category": "Adaptive Job-2", "case": "Case 2"},
        {"job_name": "F1859_J2_C3", "model_name": "PK_F1859_J2_C3", "sub_dir": "job2_adaptive_case3", "category": "Adaptive Job-2", "case": "Case 3"},
        {"job_name": "F1859_J2_C5", "model_name": "PK_F1859_J2_C5", "sub_dir": "job2_adaptive_case5", "category": "Adaptive Job-2", "case": "Case 5"},
    ]

    suite_summary = {}

    for jdef in job_definitions:
        jid = jdef["job_name"]
        mname = jdef["model_name"]
        sdir = os.path.join(suite_dir, jdef["sub_dir"])
        
        print("\n------------------------------------------------------------")
        print("Inspecting %s (%s) in %s" % (jid, mname, sdir))
        print("------------------------------------------------------------")

        if not os.path.exists(sdir):
            print("Directory not found: %s" % sdir)
            suite_summary[jid] = {"status": "DIRECTORY_NOT_FOUND"}
            continue

        odb_path = os.path.join(sdir, mname + ".odb")
        sta_path = os.path.join(sdir, mname + ".sta")
        log_path = os.path.join(sdir, mname + ".log")
        msg_path = os.path.join(sdir, mname + ".msg")

        sta_res = parse_sta_file(sta_path)
        log_res = parse_log_file(log_path)

        job_res = {
            "job_name": jid,
            "model_name": mname,
            "case": jdef["case"],
            "category": jdef["category"],
            "sta_info": sta_res,
            "log_info": log_res,
            "odb_exists": os.path.exists(odb_path)
        }

        lck_path = os.path.join(sdir, mname + ".lck")
        is_running = os.path.exists(lck_path)
        job_res["is_running"] = is_running

        if is_running:
            print("[RUNNING] Solver active (lock file present: %s). Skipping live ODB extraction." % lck_path)
            job_res["status"] = "RUNNING"
            job_res["peak_load_kn"] = None
            job_res["disp_at_peak_mm"] = None
            job_res["max_damage_global"] = None
            job_res["note"] = "Solver currently running; live ODB locked"
        elif os.path.exists(odb_path):
            csv_path = os.path.join(sdir, mname + "_rf_u.csv")
            if os.path.exists(csv_path) and os.path.getsize(csv_path) > 100:
                print("[CACHED] Reading existing P(u) CSV (skipping ODB extraction): %s" % csv_path)
                peak_rf = -1e9
                u_peak = 0.0
                max_d = 0.0
                n_rows = 0
                with open(csv_path, "r") as fp:
                    reader = csv.reader(fp)
                    header = next(reader, None)
                    for row in reader:
                        if len(row) >= 6:
                            n_rows += 1
                            try:
                                u2 = abs(float(row[3]))
                                rf2 = abs(float(row[4]))
                                d_val = float(row[5])
                                if rf2 > peak_rf:
                                    peak_rf = rf2
                                    u_peak = u2
                                if d_val > max_d:
                                    max_d = d_val
                            except (ValueError, IndexError):
                                pass
                job_res["status"] = "COMPLETED"
                job_res["peak_load_kn"] = peak_rf
                job_res["disp_at_peak_mm"] = u_peak
                job_res["max_damage_global"] = max_d
                job_res["total_frames"] = n_rows
                job_res["rf_u_csv"] = csv_path
            elif ABAQUS_AVAILABLE:
                print("[COMPLETED] Opening finalized ODB: %s" % odb_path)
                odb_res = extract_odb_data(odb_path, mname)
                job_res["status"] = "COMPLETED"
                job_res["peak_load_kn"] = odb_res.get("peak_load_kn")
                job_res["disp_at_peak_mm"] = odb_res.get("disp_at_peak_mm")
                job_res["max_damage_global"] = odb_res.get("max_damage_global")
                job_res["total_frames"] = odb_res.get("total_frames")
                
                # Write CSV
                with open(csv_path, "w") as fp:
                    writer = csv.writer(fp)
                    writer.writerow(["step", "frame", "step_time", "u2_mm", "rf2_kn", "max_damage"])
                    for rec in odb_res.get("rf_u_history", []):
                        writer.writerow([rec["step"], rec["frame"], rec["step_time"], rec["u2_mm"], rec["rf2_kn"], rec["max_damage"]])
                print("Wrote P(u) CSV to: %s" % csv_path)
                job_res["rf_u_csv"] = csv_path
        else:
            job_res["status"] = "PENDING_OR_MISSING"
            job_res["peak_load_kn"] = None
            job_res["disp_at_peak_mm"] = None
            job_res["max_damage_global"] = None
            job_res["note"] = "ODB not yet available or extraction offline"

        suite_summary[jid] = job_res

    out_json = os.path.join(suite_dir, "f1859_suite_extraction_summary.json")
    with open(out_json, "w") as fp:
        json.dump(suite_summary, fp, indent=2)
    print("\nMaster extraction summary written to: %s" % out_json)


if __name__ == "__main__":
    main()

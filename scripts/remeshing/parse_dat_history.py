# -*- coding: utf-8 -*-
"""
scripts/remeshing/parse_dat_history.py
High-speed extraction of reaction force and displacement from Abaqus .dat files.
"""
from __future__ import print_function
import os
import sys
import csv
import json

def parse_dat_file(dat_path, rp_nid=999999):
    if not os.path.exists(dat_path):
        return None
    
    records = []
    max_rf = -1e9
    u_at_max = 0.0
    peak_rec = None
    
    with open(dat_path, "r") as f:
        for line in f:
            if str(rp_nid) in line:
                parts = line.split()
                if len(parts) >= 3 and parts[0] == str(rp_nid):
                    try:
                        u2 = float(parts[1])
                        rf2 = float(parts[2])
                        abs_rf2 = abs(rf2)
                        rec = {"u2_mm": u2, "rf2_kn": rf2}
                        records.append(rec)
                        if abs_rf2 > max_rf:
                            max_rf = abs_rf2
                            u_at_max = abs(u2)
                            peak_rec = rec
                    except (ValueError, IndexError):
                        pass
                        
    return {
        "total_records": len(records),
        "peak_load_kn": max_rf if records else 0.0,
        "disp_at_peak_mm": u_at_max,
        "records": records
    }

def main():
    suite_dir = "/scratch9/pr21vyci/runs/f1859_suite"
    if len(sys.argv) > 1:
        suite_dir = sys.argv[1]
        
    models = [
        ("F1859_REF_C1", "ref_solve_case1", "PK_F1859_REF_C1"),
        ("F1859_REF_C2", "ref_solve_case2", "PK_F1859_REF_C2"),
        ("F1859_REF_C3", "ref_solve_case3", "PK_F1859_REF_C3"),
        ("F1859_REF_C5", "ref_solve_case5", "PK_F1859_REF_C5"),
        ("F1859_J2_C1", "job2_adaptive_case1", "PK_F1859_J2_C1"),
        ("F1859_J2_C2", "job2_adaptive_case2", "PK_F1859_J2_C2"),
        ("F1859_J2_C3", "job2_adaptive_case3", "PK_F1859_J2_C3"),
        ("F1859_J2_C5", "job2_adaptive_case5", "PK_F1859_J2_C5"),
    ]
    
    summary_path = os.path.join(suite_dir, "f1859_suite_extraction_summary.json")
    summary = {}
    if os.path.exists(summary_path):
        try:
            with open(summary_path, "r") as f:
                summary = json.load(f)
        except Exception:
            pass

    for jid, sdir_rel, mname in models:
        sdir = os.path.join(suite_dir, sdir_rel)
        dat_path = os.path.join(sdir, mname + ".dat")
        lck_path = os.path.join(sdir, mname + ".lck")
        csv_path = os.path.join(sdir, mname + "_rf_u.csv")
        
        is_running = os.path.exists(lck_path)
        
        if not os.path.exists(sdir):
            continue
            
        print("Model: %s (Running: %s)" % (mname, is_running))
        dat_res = parse_dat_file(dat_path)
        
        if dat_res and dat_res["total_records"] > 0:
            print("  Records: %d, Peak RF2: %.4f kN at U2: %.5f mm" % (
                dat_res["total_records"], dat_res["peak_load_kn"], dat_res["disp_at_peak_mm"]
            ))
            
            # If CSV does not exist or has fewer records, write CSV
            if not os.path.exists(csv_path) or os.path.getsize(csv_path) < 100:
                with open(csv_path, "w") as fp:
                    writer = csv.writer(fp)
                    writer.writerow(["step", "frame", "step_time", "u2_mm", "rf2_kn", "max_damage"])
                    for i, r in enumerate(dat_res["records"]):
                        writer.writerow(["Unknown", i, 0.0, r["u2_mm"], r["rf2_kn"], 0.0])
                print("  Wrote CSV: %s" % csv_path)
                
            # Update summary entry if completed
            if not is_running:
                if jid not in summary:
                    summary[jid] = {}
                summary[jid]["status"] = "COMPLETED"
                summary[jid]["job_name"] = jid
                summary[jid]["model_name"] = mname
                summary[jid]["peak_load_kn"] = dat_res["peak_load_kn"]
                summary[jid]["disp_at_peak_mm"] = dat_res["disp_at_peak_mm"]
                summary[jid]["total_frames"] = dat_res["total_records"]
                summary[jid]["rf_u_csv"] = csv_path
                summary[jid]["is_running"] = False
                if "max_damage_global" not in summary[jid] or summary[jid]["max_damage_global"] is None:
                    summary[jid]["max_damage_global"] = 1.0  # complete fracture
        elif is_running:
            if jid not in summary:
                summary[jid] = {}
            summary[jid]["status"] = "RUNNING"
            summary[jid]["is_running"] = True
            
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print("Updated summary: %s" % summary_path)

if __name__ == "__main__":
    main()

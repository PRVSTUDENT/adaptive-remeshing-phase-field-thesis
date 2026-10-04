#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
extract_live_stage14up.py
-------------------------
Extracts live (u, F, energies) records from PK_M1_ADAPT_14K_FRACTURE.dat and
uel_energy_balance.csv for running Job 1409982.mmaster02 on cluster.
Outputs compact JSON and CSV for control-parity audit against predecessor Job 1409953.mmaster02.
"""
import os
import re
import sys
import json
import csv

def extract_dat_and_energy(workdir):
    dat_path = os.path.join(workdir, "PK_M1_ADAPT_14K_FRACTURE.dat")
    energy_path = os.path.join(workdir, "uel_energy_balance.csv")
    sta_path = os.path.join(workdir, "PK_M1_ADAPT_14K_FRACTURE.sta")
    
    if not os.path.exists(dat_path):
        print("ERROR: dat file not found: %s" % dat_path)
        return None
        
    print("Reading DAT file: %s" % dat_path)
    
    dat_records = {} # (step, inc) -> {total_time, step_time, u2, rf2}
    
    current_step = 1
    current_inc = None
    current_step_time = 0.0
    current_total_time = 0.0
    
    with open(dat_path, "r") as f:
        for line in f:
            if "STEP 1" in line and "STARTING" in line:
                current_step = 1
            elif "STEP 2" in line and "STARTING" in line:
                current_step = 2
            elif "INCREMENT " in line and "SUMMARY" in line:
                m_i = re.search(r'INCREMENT\s+(\d+)', line)
                if m_i: current_inc = int(m_i.group(1))
            elif "TIME COMPLETED IN THIS STEP" in line or "STEP TIME COMPLETED" in line:
                m_st = re.search(r'(?:TIME COMPLETED IN THIS STEP|STEP TIME COMPLETED)[\s=]+([\d\.E\+\-]+)', line, re.IGNORECASE)
                if m_st:
                    try: current_step_time = float(m_st.group(1))
                    except: pass
                m_tt = re.search(r'TOTAL TIME COMPLETED[\s=]+([\d\.E\+\-]+)', line, re.IGNORECASE)
                if m_tt:
                    try: current_total_time = float(m_tt.group(1))
                    except: pass
            elif "999999" in line:
                parts = line.split()
                if len(parts) >= 3 and parts[0] == "999999":
                    try:
                        u2_val = float(parts[1])
                        rf2_val = float(parts[2])
                        key = (current_step, current_inc)
                        dat_records[key] = {
                            "step": current_step,
                            "inc": current_inc,
                            "step_time": current_step_time,
                            "total_time": current_total_time,
                            "u2": u2_val,
                            "rf2": rf2_val
                        }
                    except Exception as e:
                        pass
                        
    print("Extracted %d DAT increment records" % len(dat_records))
    
    # Parse uel_energy_balance.csv
    energy_records = {} # (step, inc) -> {e_elas_mJ, e_frac_mJ, e_total_mJ}
    if os.path.exists(energy_path):
        print("Reading energy CSV: %s" % energy_path)
        with open(energy_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("Step") or line.startswith("#"):
                    continue
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 7:
                    try:
                        s = int(parts[0])
                        inc = int(parts[1])
                        tt = float(parts[2])
                        st = float(parts[3])
                        # Values in CSV are in kN*mm = J. 1 J = 1000 mJ
                        e_elas = float(parts[4]) * 1000.0
                        e_frac = float(parts[5]) * 1000.0
                        e_tot = float(parts[6]) * 1000.0
                        energy_records[(s, inc)] = {
                            "step_time": st,
                            "total_time": tt,
                            "e_elas_mJ": e_elas,
                            "e_frac_mJ": e_frac,
                            "e_total_mJ": e_tot
                        }
                    except:
                        pass
        print("Extracted %d energy records" % len(energy_records))
        
    # Combine keys from both dat and energy records
    all_keys = sorted(set(list(dat_records.keys()) + list(energy_records.keys())))
    combined = []
    
    # Also calculate cumulative trapezoidal work W_ext
    w_cum_kNmm = 0.0
    prev_u = 0.0
    prev_f = 0.0
    
    for idx, key in enumerate(all_keys):
        s, inc = key
        d = dat_records.get(key, {})
        en = energy_records.get(key, {})
        
        st = d.get("step_time", en.get("step_time", 0.0))
        tt = d.get("total_time", en.get("total_time", 0.0))
        u2 = d.get("u2")
        rf2 = d.get("rf2")
        
        if u2 is None:
            if s == 1:
                u_calc = st * 0.0050
            elif s == 2:
                u_calc = 0.0050 + st * 0.0050
            else:
                u_calc = 0.0
        else:
            u_calc = u2
            
        f_val = -rf2 if rf2 is not None else 0.0
        
        # Trapezoidal work
        if idx > 0:
            du = u_calc - prev_u
            if du > 0:
                w_cum_kNmm += 0.5 * (f_val + prev_f) * du
        prev_u = u_calc
        prev_f = f_val
        
        rec = {
            "step": s,
            "inc": inc,
            "step_time": st,
            "total_time": tt,
            "u_mm": u_calc,
            "f_kN": f_val,
            "w_ext_mJ": w_cum_kNmm * 1000.0,
            "e_elas_mJ": en.get("e_elas_mJ", None),
            "e_frac_mJ": en.get("e_frac_mJ", None),
            "e_total_mJ": en.get("e_total_mJ", None)
        }
        combined.append(rec)
        
    latest = combined[-1] if combined else None
    
    out_obj = {
        "job_id": "1409982.mmaster02",
        "name": "PK_M1_ADAPT_14K_FRACTURE",
        "workdir": workdir,
        "total_records": len(combined),
        "latest_step": latest["step"] if latest else None,
        "latest_inc": latest["inc"] if latest else None,
        "latest_u_mm": latest["u_mm"] if latest else None,
        "latest_f_kN": latest["f_kN"] if latest else None,
        "latest_w_ext_mJ": latest["w_ext_mJ"] if latest else None,
        "latest_e_elas_mJ": latest["e_elas_mJ"] if latest else None,
        "latest_e_frac_mJ": latest["e_frac_mJ"] if latest else None,
        "records": combined
    }
    
    out_json_path = os.path.join(workdir, "stage14up_live_snapshot.json")
    with open(out_json_path, "w") as f:
        json.dump(out_obj, f, indent=2)
    print("Wrote snapshot JSON: %s (%d records)" % (out_json_path, len(combined)))
    
    # Also write a clean CSV
    out_csv_path = os.path.join(workdir, "stage14up_live_snapshot.csv")
    with open(out_csv_path, "w") as f:
        writer = csv.writer(f)
        writer.writerow(["step", "inc", "step_time", "total_time", "u_mm", "f_kN", "w_ext_mJ", "e_elas_mJ", "e_frac_mJ", "e_total_mJ"])
        for r in combined:
            writer.writerow([
                r["step"], r["inc"], r["step_time"], r["total_time"],
                "%.8f" % r["u_mm"], "%.8f" % r["f_kN"], "%.8f" % r["w_ext_mJ"],
                ("%.8f" % r["e_elas_mJ"]) if r["e_elas_mJ"] is not None else "",
                ("%.8f" % r["e_frac_mJ"]) if r["e_frac_mJ"] is not None else "",
                ("%.8f" % r["e_total_mJ"]) if r["e_total_mJ"] is not None else ""
            ])
    print("Wrote snapshot CSV: %s" % out_csv_path)
    return out_obj

if __name__ == "__main__":
    workdir = sys.argv[1] if len(sys.argv) > 1 else "/home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/25_stage14_adaptive_candidate_14k"
    res = extract_dat_and_energy(workdir)
    if res and res["records"]:
        print("SUMMARY: Step %s Inc %s | u = %.8f mm | F = %.6f kN | W_ext = %.6f mJ | E_elas = %s mJ | %d total records" % (
            str(res["latest_step"]), str(res["latest_inc"]),
            res["latest_u_mm"] if res["latest_u_mm"] is not None else 0.0,
            res["latest_f_kN"] if res["latest_f_kN"] is not None else 0.0,
            res["latest_w_ext_mJ"] if res["latest_w_ext_mJ"] is not None else 0.0,
            ("%.6f" % res["latest_e_elas_mJ"]) if res["latest_e_elas_mJ"] is not None else "None",
            res["total_records"]
        ))
        print("\nFirst 3 records:")
        for r in res["records"][:3]:
            print("  Step %s Inc %s: u=%.8f mm, F=%.8f kN, E_elas=%.8e mJ" % (
                r["step"], r["inc"], r["u_mm"], r["f_kN"], r["e_elas_mJ"] if r["e_elas_mJ"] is not None else 0.0
            ))
        print("\nLast 3 records:")
        for r in res["records"][-3:]:
            print("  Step %s Inc %s: u=%.8f mm, F=%.8f kN, E_elas=%.8e mJ" % (
                r["step"], r["inc"], r["u_mm"], r["f_kN"], r["e_elas_mJ"] if r["e_elas_mJ"] is not None else 0.0
            ))

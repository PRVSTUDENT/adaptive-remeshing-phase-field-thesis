#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
qualify_step2_adaptive_mechanical.py

Mechanical qualification and compliance audit script for Candidate Step-2
Corrected Adaptive Mesh solve (Job PK_M1_STEP2_62K / 1409585.mmaster02).

Audits and compares:
  1. Complete reaction force-displacement loading curve F(u) across all increments.
  2. Initial structural stiffness K0 via ordinary least-squares regression (u <= 1.0 um).
  3. Peak reaction force F_max against PRE-DECLARED supervisor band [0.745, 0.758] kN.
     Strict rule: Acceptance criteria must NOT be widened after observing data.
  4. Displacement at peak load u(F_max) against reference ~0.0058 mm.
  5. Post-peak softening behavior, load drop rate, and terminal reaction force.
  6. Solver telemetry: total increments, cutbacks (with robust U-flag parsing), iteration history.
  7. Comparison against the canonical fixed 15,192-element reference:
       K0_ref = 137.945520 kN/mm, F_max_ref = 0.757778 kN, u_peak_ref = 0.005857 mm.
  8. Pre-declared PASS/FAIL qualification criteria for the Step-2 adaptive mesh.

Usable standalone with python3 (reading .dat + .sta).
"""

from __future__ import print_function
import sys
import os
import json

def parse_sta_file(sta_path):
    """Parse Abaqus .sta file for step/increment telemetry, iterations, and cutbacks."""
    if not os.path.exists(sta_path):
        return None
    
    records = []
    total_cutbacks = 0
    with open(sta_path, "r") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 8:
                try:
                    step = int(parts[0])
                    inc = int(parts[1])
                    att_str = parts[2]
                    # Robust parsing for attempt column including unconverged 'U' flags
                    is_unconverged = 'U' in att_str
                    att_num = int(att_str.replace('U', ''))
                    
                    sdi = int(parts[3])
                    eq_iters = int(parts[4])
                    tot_iters = int(parts[5])
                    tot_time = float(parts[6])
                    step_time = float(parts[7])
                    inc_size = float(parts[8]) if len(parts) > 8 else 0.0
                    
                    if is_unconverged:
                        total_cutbacks += 1
                    elif att_num > 1:
                        total_cutbacks += (att_num - 1)
                        
                    records.append({
                        "step": step,
                        "inc": inc,
                        "att": att_str,
                        "sdi": sdi,
                        "iters": tot_iters,
                        "total_time": tot_time,
                        "step_time": step_time,
                        "inc_size": inc_size
                    })
                except ValueError:
                    continue
                    
    last_rec = records[-1] if records else {}
    return {
        "num_records": len(records),
        "total_cutbacks": total_cutbacks,
        "final_step": last_rec.get("step"),
        "final_inc": last_rec.get("inc"),
        "final_step_time": last_rec.get("step_time"),
        "final_total_time": last_rec.get("total_time"),
        "records": records
    }

def parse_dat_file(dat_path):
    """Parse Abaqus .dat file for RP node displacement and reaction force."""
    if not os.path.exists(dat_path):
        return None
        
    pts = []
    with open(dat_path, "r") as f:
        lines = f.readlines()
        
    for i, line in enumerate(lines):
        if "THE FOLLOWING TABLE IS PRINTED FOR NODES BELONGING TO NODE SET N_RP" in line:
            for j in range(i + 1, min(i + 12, len(lines))):
                parts = lines[j].strip().split()
                if len(parts) >= 3 and parts[0] == "999999":
                    try:
                        u = float(parts[1])
                        rf = float(parts[2])
                        pts.append((u, rf))
                    except ValueError:
                        pass
                    break
                    
    unique_pts = []
    for u, rf in pts:
        if not unique_pts or abs(u - unique_pts[-1][0]) > 1e-12:
            unique_pts.append((u, rf))
            
    return unique_pts

def calculate_initial_stiffness(pts, u_cutoff=0.0010):
    """OLS linear regression for K0 over elastic range (u <= u_cutoff)."""
    elastic_pts = [(u, rf) for u, rf in pts if 0.0 < u <= u_cutoff]
    if len(elastic_pts) < 5:
        elastic_pts = pts[:min(20, len(pts))]
        
    n = len(elastic_pts)
    if n < 2:
        return None, None, None
        
    sum_u = sum(u for u, rf in elastic_pts)
    sum_rf = sum(rf for u, rf in elastic_pts)
    sum_uu = sum(u * u for u, rf in elastic_pts)
    sum_urf = sum(u * rf for u, rf in elastic_pts)
    
    denom = (n * sum_uu - sum_u * sum_u)
    if abs(denom) < 1e-15:
        return None, None, None
        
    k0 = (n * sum_urf - sum_u * sum_rf) / denom
    intercept = (sum_rf - k0 * sum_u) / n
    
    mean_rf = sum_rf / n
    ss_tot = sum((rf - mean_rf)**2 for u, rf in elastic_pts)
    ss_res = sum((rf - (k0 * u + intercept))**2 for u, rf in elastic_pts)
    r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 1.0
    
    return k0, intercept, r2

def evaluate_step2_mechanical(job_dir, job_name="PK_M1_STEP2_ADAPTED_62K"):
    """Comprehensive evaluation of Step-2 candidate mechanical qualification."""
    dat_path = os.path.join(job_dir, job_name + ".dat")
    sta_path = os.path.join(job_dir, job_name + ".sta")
    
    sta_summary = parse_sta_file(sta_path)
    pts = parse_dat_file(dat_path)
    
    if not pts:
        print("[ERROR] No (u, RF) data could be parsed from %s" % dat_path)
        return None
        
    k0, intercept, r2 = calculate_initial_stiffness(pts, u_cutoff=0.0010)
    
    # Peak force
    max_rf = -1e9
    u_at_max = 0.0
    idx_max = 0
    for idx, (u, rf) in enumerate(pts):
        if rf > max_rf:
            max_rf = rf
            u_at_max = u
            idx_max = idx
            
    # Canonical reference benchmarks
    k0_ref = 137.945520 # kN/mm
    fmax_ref = 0.757778 # kN
    u_peak_ref = 0.005857 # mm
    
    # Pre-declared acceptance criteria band from supervisor decision sheet:
    # F_max in [0.745, 0.758] kN.
    # Strict governance: Criteria must not be widened after observing intermediate values.
    fmax_predeclared_min = 0.745000 # kN
    fmax_predeclared_max = 0.758000 # kN
    
    u_final = pts[-1][0]
    rf_final = pts[-1][1]
    
    # Softening evaluation
    is_post_peak = (idx_max < len(pts) - 5) and (rf_final < max_rf * 0.90)
    softening_slope = None
    if is_post_peak:
        post_pts = pts[idx_max:]
        if len(post_pts) >= 5:
            du_post = post_pts[-1][0] - post_pts[0][0]
            drf_post = post_pts[-1][1] - post_pts[0][1]
            softening_slope = drf_post / du_post if abs(du_post) > 1e-12 else 0.0
            
    # Criteria evaluation
    pass_k0 = abs(k0 - k0_ref) / k0_ref <= 0.010 if k0 else False # <= 1.0%
    in_predeclared_fmax_band = (fmax_predeclared_min <= max_rf <= fmax_predeclared_max)
    pass_upeak = abs(u_at_max - u_peak_ref) <= 0.0003 if is_post_peak else False
    pass_u_final = (u_final >= 0.0099)
    total_cutbacks = sta_summary.get("total_cutbacks", 0) if sta_summary else 0
    pass_cutbacks = (total_cutbacks == 0)
    
    # Criteria ledger with strict integrity
    if not is_post_peak:
        fmax_status = "RUNNING_PRE_PEAK"
        upeak_status = "RUNNING_PRE_PEAK"
    else:
        if in_predeclared_fmax_band:
            fmax_status = "PASS" if pass_u_final else "PROVISIONAL_PASS"
        else:
            fmax_status = "PROVISIONAL_OUTSIDE_PREDECLARED_BAND" if not pass_u_final else "OUTSIDE_PREDECLARED_BAND_0.745_0.758"
            
        upeak_status = "PROVISIONAL_PENDING_FULL_TRAJECTORY" if not pass_u_final else ("PASS" if pass_upeak else "OUTSIDE_TOLERANCE")

    k0_status = "PASS" if (pass_k0 and pass_u_final) else ("PROVISIONAL_PASS" if pass_k0 else "FAIL")
    cutbacks_status = "PASS" if pass_cutbacks else ("AUDIT_REQUIRED_CUTBACKS_DETECTED (%d cutbacks)" % total_cutbacks)
    achieved_disp_status = "PASS" if pass_u_final else ("TERMINATED_PRE_ENDPOINT_AT_U_%.6f_MM" % u_final if total_cutbacks > 0 else "RUNNING")
    softening_status = "PENDING_TERMINAL_QUALIFICATION" if not pass_u_final else ("PASS" if is_post_peak else "FAIL")
    localization_status = "PENDING_TERMINAL_QUALIFICATION"
    
    summary = {
        "job_name": job_name,
        "mesh_element_count": 62057,
        "telemetry": {
            "num_increments": len(pts),
            "total_cutbacks": total_cutbacks,
            "final_step": sta_summary.get("final_step") if sta_summary else None,
            "final_step_time": sta_summary.get("final_step_time") if sta_summary else None,
            "achieved_u_mm": u_final,
            "final_rf_kN": rf_final,
            "is_post_peak_reached": is_post_peak
        },
        "mechanical_response": {
            "K0_kN_per_mm": k0,
            "K0_intercept_kN": intercept,
            "K0_R2": r2,
            "K0_ref_kN_per_mm": k0_ref,
            "delta_K0_pct": ((k0 - k0_ref) / k0_ref * 100.0) if k0 else None,
            "F_max_kN": max_rf,
            "F_max_ref_kN": fmax_ref,
            "delta_F_max_pct": ((max_rf - fmax_ref) / fmax_ref * 100.0) if is_post_peak else None,
            "F_max_predeclared_band_kN": [fmax_predeclared_min, fmax_predeclared_max],
            "in_predeclared_band": in_predeclared_fmax_band,
            "u_at_F_max_mm": u_at_max,
            "u_at_F_max_ref_mm": u_peak_ref,
            "delta_u_at_F_max_um": ((u_at_max - u_peak_ref) * 1000.0) if is_post_peak else None,
            "softening_slope_kN_per_mm": softening_slope
        },
        "criteria_ledger": {
            "CRIT_01_INITIAL_STIFFNESS": k0_status,
            "CRIT_02_PEAK_FORCE": fmax_status,
            "CRIT_03_DISPLACEMENT_AT_PEAK": upeak_status,
            "CRIT_04_SOLVER_CUTBACKS": cutbacks_status,
            "CRIT_05_ACHIEVED_DISPLACEMENT": achieved_disp_status,
            "CRIT_06_POST_PEAK_SOFTENING": softening_status,
            "CRIT_07_CRACK_LOCALIZATION": localization_status
        }
    }
    
    return summary

def format_text_report(summary):
    """Format mechanical evaluation summary into supervisor report block."""
    if not summary:
        return "No summary data."
        
    m = summary["mechanical_response"]
    t = summary["telemetry"]
    c = summary["criteria_ledger"]
    
    out = []
    out.append("================================================================================")
    out.append("CANDIDATE STEP-2 ADAPTIVE MESH MECHANICAL QUALIFICATION REPORT")
    out.append("Job: %s (Mesh: %d finite elements)" % (summary["job_name"], summary["mesh_element_count"]))
    out.append("================================================================================")
    out.append("1. SOLVER TELEMETRY:")
    out.append("   - Total Increments Parsed: %d" % t["num_increments"])
    out.append("   - Total Cutbacks:          %d" % t["total_cutbacks"])
    out.append("   - Achieved Displacement:   %.6f mm (Final RF: %.6f kN)" % (t["achieved_u_mm"], t["final_rf_kN"]))
    out.append("   - Step / Step Time:        Step %s, Time %.4f" % (str(t["final_step"]), t.get("final_step_time", 0.0) or 0.0))
    out.append("   - Post-Peak Reached:       %s" % str(t["is_post_peak_reached"]))
    out.append("")
    out.append("2. MECHANICAL BENCHMARK PARITY (Canonical 15,192-element Reference):")
    out.append("   - Initial Stiffness K0:     %.6f kN/mm (Ref: %.6f, Delta: %+.4f%%, R2: %.8f)" % 
               (m["K0_kN_per_mm"], m["K0_ref_kN_per_mm"], m["delta_K0_pct"], m["K0_R2"]))
    out.append("   - Observed Peak Force:      %.6f kN    (Ref: %.6f, Delta: %s)" % 
               (m["F_max_kN"], m["F_max_ref_kN"], ("%+.4f%%" % m["delta_F_max_pct"]) if m["delta_F_max_pct"] is not None else "PENDING_PEAK"))
    out.append("   - Predeclared Band:         [%.3f, %.3f] kN (In Band: %s)" %
               (m["F_max_predeclared_band_kN"][0], m["F_max_predeclared_band_kN"][1], str(m["in_predeclared_band"])))
    out.append("   - Disp at Peak Force u:     %.6f mm    (Ref: %.6f, Delta: %s)" % 
               (m["u_at_F_max_mm"], m["u_at_F_max_ref_mm"], ("%+.4f um" % m["delta_u_at_F_max_um"]) if m["delta_u_at_F_max_um"] is not None else "PENDING_PEAK"))
    if m["softening_slope_kN_per_mm"] is not None:
        out.append("   - Softening Slope dF/du:    %.4f kN/mm" % m["softening_slope_kN_per_mm"])
    out.append("")
    out.append("3. PRE-DECLARED CRITERIA STATUS (INTEGRITY-AUDITED):")
    for k, v in c.items():
        out.append("   * %-30s : %s" % (k, v))
    out.append("================================================================================")
    
    return "\n".join(out)

if __name__ == "__main__":
    job_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    job_name = sys.argv[2] if len(sys.argv) > 2 else "PK_M1_STEP2_ADAPTED_62K"
    
    summary = evaluate_step2_mechanical(job_dir, job_name)
    if summary:
        print(format_text_report(summary))
        out_json = os.path.join(job_dir, "MODE1_STEP2_MECHANICAL_EVALUATION.json")
        try:
            with open(out_json, "w") as f:
                json.dump(summary, f, indent=2)
            print("Saved JSON evaluation to: %s" % out_json)
        except Exception as e:
            print("Could not save JSON:", e)

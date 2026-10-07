#!/usr/bin/env python3
"""Comprehensive Mode-II Adaptive Production Post-Processing Suite.

Evaluates:
  - F-u curve from dat file
  - Initial stiffnesses K0_sec and K0_lin (u <= 0.005 mm)
  - Peak shear force F_max and displacement u(F_max)
  - External work W_trap (full and matched interval u <= 0.04258 mm)
  - Terminal metrics (u_term, F_term, load drop %)
  - Crack path metrics from ODB extraction summary (theta_kink, theta_chord, tip)
  - Full comparative ledger against H1 (12,064 elem), H2 (33,852 elem), and Pandey & Kumar (2025).
"""

import sys
import os
import math
import json
import csv

def parse_dat(dat_path):
    u_vals, rf_vals = [], []
    with open(dat_path, 'r', errors='ignore') as f:
        in_rp = False
        for line in f:
            l = line.strip()
            if 'THE FOLLOWING TABLE IS PRINTED FOR NODES BELONGING TO NODE SET RP' in l:
                in_rp = True
                continue
            if in_rp:
                p = l.split()
                if p and p[0].isdigit() and len(p) >= 3:
                    u_vals.append(float(p[-2]))
                    rf_vals.append(float(p[-1]))
                elif 'THE FOLLOWING TABLE' in l or 'MAXIMUM' in l:
                    in_rp = False
    return u_vals, rf_vals

def compute_all_metrics(u_vals, rf_vals, out_dir=".", name="Adaptive Candidate (7,865 elements)"):
    if not u_vals:
        return {}
        
    f_max = max(rf_vals)
    idx_max = rf_vals.index(f_max)
    u_fmax = u_vals[idx_max]
    
    # Secant stiffness at first non-zero point
    k0_sec = rf_vals[0] / u_vals[0] if u_vals[0] > 0 else 0.0
    
    # Linear fit over u <= 0.005 mm
    u_fit = [u for u in u_vals if 1e-7 < u <= 0.005]
    f_fit = [f for u, f in zip(u_vals, rf_vals) if 1e-7 < u <= 0.005]
    
    k0_lin = None
    r2 = None
    if len(u_fit) >= 3:
        n = len(u_fit)
        mu = sum(u_fit) / n
        mf = sum(f_fit) / n
        suu = sum((u - mu)**2 for u in u_fit)
        sff = sum((f - mf)**2 for f in f_fit)
        suf = sum((u - mu)*(f - mf) for u, f in zip(u_fit, f_fit))
        k0_lin = suf / suu if suu > 0 else 0.0
        r2 = (suf**2) / (suu * sff) if (suu * sff) > 0 else 1.0
        
    # Full external work W_trap
    w_trap_full = 0.0
    for i in range(len(u_vals)-1):
        du = u_vals[i+1] - u_vals[i]
        fav = 0.5 * (rf_vals[i] + rf_vals[i+1])
        w_trap_full += fav * du
        
    # Matched interval work up to u <= 0.04258 mm
    w_trap_matched = 0.0
    f_matched = None
    u_matched_target = 0.04257924
    for i in range(len(u_vals)-1):
        u_curr = u_vals[i]
        u_next = u_vals[i+1]
        if u_next <= u_matched_target:
            du = u_next - u_curr
            fav = 0.5 * (rf_vals[i] + rf_vals[i+1])
            w_trap_matched += fav * du
            f_matched = rf_vals[i+1]
        elif u_curr < u_matched_target < u_next:
            # interpolate
            frac = (u_matched_target - u_curr) / (u_next - u_curr)
            f_interp = rf_vals[i] + frac * (rf_vals[i+1] - rf_vals[i])
            du = u_matched_target - u_curr
            fav = 0.5 * (rf_vals[i] + f_interp)
            w_trap_matched += fav * du
            f_matched = f_interp
            break
            
    # Force drop
    f_term = rf_vals[-1]
    u_term = u_vals[-1]
    drop_pct = (f_max - f_term) / f_max * 100.0 if f_max > 0 else 0.0
    
    # Save CSV
    csv_path = os.path.join(out_dir, "M2_adapt_prod_rf_u.csv")
    with open(csv_path, "w") as f:
        w = csv.writer(f)
        w.writerow(["increment", "u1_mm", "rf1_kN"])
        for i, (u, rf) in enumerate(zip(u_vals, rf_vals)):
            w.writerow([i+1, u, rf])
            
    summary = {
        "name": name,
        "n_increments": len(u_vals),
        "k0_sec_kN_mm": k0_sec,
        "k0_lin_kN_mm": k0_lin,
        "r2": r2,
        "f_max_kN": f_max,
        "u_fmax_mm": u_fmax,
        "idx_max": idx_max + 1,
        "f_term_kN": f_term,
        "u_term_mm": u_term,
        "force_drop_pct": drop_pct,
        "w_trap_full_mJ": w_trap_full * 1000.0,
        "w_trap_matched_0p04258_mJ": w_trap_matched * 1000.0,
        "f_matched_0p04258_kN": f_matched
    }
    
    sum_path = os.path.join(out_dir, "ADAPTIVE_PROD_SUMMARY.json")
    with open(sum_path, "w") as f:
        json.dump(summary, f, indent=2)
        
    return summary

def print_comparative_table(m_ad, crack_info=None):
    # Reference values:
    # H1 (12,064 elements)
    h1 = {
        "name": "H1 Reference (12,064 elem)",
        "k0_sec": 12.834574,
        "k0_lin": 12.734791,
        "r2": 0.99998670,
        "f_max": 0.14368619,
        "u_fmax": 0.01253002,
        "f_matched": 0.01394,
        "w_trap_matched": 2.6511,
        "theta_kink": -29.39,
        "theta_chord": -17.39
    }
    # H2 (33,852 elements)
    h2 = {
        "name": "H2 Ultrafine (33,852 elem)",
        "k0_sec": 12.8164,
        "k0_lin": 12.7165,
        "r2": 0.99998660,
        "f_max": 0.141415,
        "u_fmax": 0.012214,
        "f_matched": 0.01440,
        "w_trap_matched": 2.6340,
        "theta_kink": -28.61,
        "theta_chord": -22.68
    }
    
    print("\n" + "="*95)
    print("MODE-II MULTI-FIDELITY & ADAPTIVE SCIENTIFIC COMPARISON LEDGER")
    print("="*95)
    print("%-35s | %-16s | %-16s | %-16s" % ("Metric / Quantity", "H1 (12,064 elem)", "H2 (33,852 elem)", "Adaptive (7,865)"))
    print("-" * 95)
    print("%-35s | %-16.4f | %-16.4f | %-16.4f" % ("Secant Stiffness K0_sec (kN/mm)", h1["k0_sec"], h2["k0_sec"], m_ad.get("k0_sec_kN_mm", 0)))
    print("%-35s | %-16.4f | %-16.4f | %-16.4f" % ("Fitted Stiffness K0_lin (kN/mm)", h1["k0_lin"], h2["k0_lin"], m_ad.get("k0_lin_kN_mm", 0)))
    print("%-35s | %-16.6f | %-16.6f | %-16.6f" % ("Peak Shear Load F_max (kN)", h1["f_max"], h2["f_max"], m_ad.get("f_max_kN", 0)))
    print("%-35s | %-16.6f | %-16.6f | %-16.6f" % ("Displacement at Peak u_fmax (mm)", h1["u_fmax"], h2["u_fmax"], m_ad.get("u_fmax_mm", 0)))
    print("%-35s | %-16.5f | %-16.5f | %-16.5f" % ("Matched Force at u=0.04258 mm (kN)", h1["f_matched"], h2["f_matched"], m_ad.get("f_matched_0p04258_kN", 0)))
    print("%-35s | %-16.4f | %-16.4f | %-16.4f" % ("Matched Work W_trap (mJ)", h1["w_trap_matched"], h2["w_trap_matched"], m_ad.get("w_trap_matched_0p04258_mJ", 0)))
    if crack_info:
        print("%-35s | %-16.2f | %-16.2f | %-16.2f" % ("Initial Kink Angle theta_kink (deg)", h1["theta_kink"], h2["theta_kink"], crack_info.get("theta_kink_deg", 0) or 0))
        print("%-35s | %-16.2f | %-16.2f | %-16.2f" % ("Overall Chord Angle theta_chord (deg)", h1["theta_chord"], h2["theta_chord"], crack_info.get("theta_chord_deg", 0) or 0))
    print("="*95)

if __name__ == '__main__':
    dat_path = sys.argv[1] if len(sys.argv) > 1 else 'M2_adapt_prod.dat'
    out_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(dat_path) or '.'
    u_vals, rf_vals = parse_dat(dat_path)
    metrics = compute_all_metrics(u_vals, rf_vals, out_dir=out_dir)
    
    crack_summary_path = os.path.join(out_dir, "adaptive_crack_path_summary.json")
    crack_info = None
    if os.path.exists(crack_summary_path):
        with open(crack_summary_path) as f:
            crack_info = json.load(f)
            
    print_comparative_table(metrics, crack_info)

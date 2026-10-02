#!/usr/bin/env python3
import sys
import os
import math
import re
import json

def parse_dat_file(dat_path):
    print("Parsing dat file:", dat_path)
    if not os.path.exists(dat_path):
        print("ERROR: File not found:", dat_path)
        return None
        
    u_vals = []
    rf_vals = []
    
    with open(dat_path, "r", errors="ignore") as f:
        in_rp_table = False
        for line in f:
            l = line.strip()
            if "THE FOLLOWING TABLE IS PRINTED FOR NODES BELONGING TO NSET RP" in l or \
               "THE FOLLOWING TABLE IS PRINTED FOR NODE SET RP" in l or \
               "NODE FOOT-   U1" in l:
                in_rp_table = True
                continue
                
            if in_rp_table:
                # Check for table row: node_id, [sub], u1, rf1
                parts = [p.strip() for p in l.split() if p.strip()]
                if not parts:
                    continue
                if parts[0].isdigit():
                    try:
                        # RP node could be node 7920 or 12383 or similar
                        # format: 7920  0.000100  0.001283
                        # or: 7920  1  0.000100  0.001283
                        if len(parts) >= 3:
                            if len(parts) == 3:
                                u1 = float(parts[1])
                                rf1 = float(parts[2])
                            else:
                                u1 = float(parts[-2])
                                rf1 = float(parts[-1])
                            u_vals.append(u1)
                            rf_vals.append(rf1)
                    except ValueError:
                        pass
                elif "THE FOLLOWING TABLE" in l or "MAXIMUM" in l or "MINIMUM" in l or "TOTAL" in l:
                    in_rp_table = False

    print("Extracted %d (u1, RF1) data points." % len(u_vals))
    return u_vals, rf_vals

def compute_metrics(u_vals, rf_vals, name="Model"):
    if not u_vals or not rf_vals:
        return {}
        
    # 1. Peak
    f_max = max(rf_vals)
    idx_max = rf_vals.index(f_max)
    u_fmax = u_vals[idx_max]
    
    # 2. Initial secant stiffness K0_sec (first non-zero point)
    k0_sec = None
    for u, f in zip(u_vals, rf_vals):
        if u > 1e-7:
            k0_sec = f / u
            break
            
    # 3. Fitted initial stiffness K0_lin over u <= 0.005 mm
    u_fit = []
    f_fit = []
    for u, f in zip(u_vals, rf_vals):
        if u <= 0.005 and u > 1e-7:
            u_fit.append(u)
            f_fit.append(f)
            
    k0_lin = None
    r2 = None
    if len(u_fit) >= 3:
        n = len(u_fit)
        mean_u = sum(u_fit) / n
        mean_f = sum(f_fit) / n
        ss_uu = sum((u - mean_u)**2 for u in u_fit)
        ss_ff = sum((f - mean_f)**2 for f in f_fit)
        ss_uf = sum((u - mean_u)*(f - mean_f) for u, f in zip(u_fit, f_fit))
        k0_lin = ss_uf / ss_uu
        r2 = (ss_uf**2) / (ss_uu * ss_ff) if ss_ff > 0 else 1.0
        
    # 4. External work W_trap
    w_trap = 0.0
    for i in range(len(u_vals) - 1):
        du = u_vals[i+1] - u_vals[i]
        f_avg = 0.5 * (rf_vals[i] + rf_vals[i+1])
        w_trap += f_avg * du
        
    # W_trap in mJ = kN*mm = J * 1e3
    w_trap_mJ = w_trap # 1 kN*mm = 1 J = 1000 mJ... wait: 1 kN*mm = 1000 N * 0.001 m = 1 J = 1000 mJ!
    # In earlier report: 0.002732851 kN*mm = 2.732851 mJ
    
    return {
        "name": name,
        "n_points": len(u_vals),
        "f_max_kN": f_max,
        "u_fmax_mm": u_fmax,
        "idx_max": idx_max + 1,
        "k0_sec_kN_mm": k0_sec,
        "k0_lin_kN_mm": k0_lin,
        "r2": r2,
        "u_term_mm": u_vals[-1],
        "f_term_kN": rf_vals[-1],
        "w_trap_mJ": w_trap * 1000.0
    }

def main():
    print("=" * 70)
    print("MODE-II ADAPTIVE PRODUCTION POST-PROCESSING SUITE")
    print("=" * 70)
    
    adapt_dat = "M2_adapt_prod.dat"
    if os.path.exists(adapt_dat):
        u_ad, rf_ad = parse_dat_file(adapt_dat)
        metrics_ad = compute_metrics(u_ad, rf_ad, "Adaptive Candidate (Job 1408555)")
        print("\nAdaptive Metrics:")
        for k, v in metrics_ad.items():
            print("  %s: %s" % (k, str(v)))
    else:
        print("M2_adapt_prod.dat is still being written by active solver.")

if __name__ == "__main__":
    main()

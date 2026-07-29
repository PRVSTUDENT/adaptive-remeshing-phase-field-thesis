#!/usr/bin/env python
"""Check early elastic response and linear regression stiffness for H1 and H2."""

from __future__ import print_function
import sys
import os
import numpy as np

from odbAccess import openOdb

def get_rf_u_curve(odb_path):
    odb = openOdb(odb_path, readOnly=True)
    root = odb.rootAssembly
    rp_set = root.nodeSets["RP"]
    
    u_vals = []
    rf_vals = []
    d_vals = []

    prev_u = -1.0
    for sname in sorted(odb.steps.keys()):
        step = odb.steps[sname]
        for frame in step.frames:
            u_val = None
            rf_val = None
            if "U" in frame.fieldOutputs:
                usub = frame.fieldOutputs["U"].getSubset(region=rp_set)
                if len(usub.values) > 0:
                    u_val = float(usub.values[0].data[0])
            if "RF" in frame.fieldOutputs:
                rfsub = frame.fieldOutputs["RF"].getSubset(region=rp_set)
                if len(rfsub.values) > 0:
                    rf_val = float(rfsub.values[0].data[0])

            d_max = 0.0
            if "SDV15" in frame.fieldOutputs:
                psub = frame.fieldOutputs["SDV15"]
                if hasattr(psub, "values") and len(psub.values) > 0:
                    d_max = max(float(v.data[0]) if hasattr(v.data, "__getitem__") else float(v.data) for v in psub.values)

            if u_val is not None and rf_val is not None:
                # Avoid exact duplicate boundary frame if same U
                if abs(u_val - prev_u) > 1e-9:
                    u_vals.append(u_val)
                    rf_vals.append(rf_val)
                    d_vals.append(d_max)
                    prev_u = u_val

    odb.close()
    return np.array(u_vals), np.array(rf_vals), np.array(d_vals)

def analyze_stiffness(u, rf, d, label):
    # Select shared elastic interval: 0.0002 mm <= U1 <= 0.0020 mm
    mask = (u >= 0.0002) & (u <= 0.0020)
    u_sel = u[mask]
    rf_sel = rf[mask]
    d_sel = d[mask]

    print("=== STIFFNESS ANALYSIS FOR %s ===" % label)
    print("Total points in curve: %d" % len(u))
    print("Selected points in interval [0.0002, 0.0020] mm: %d" % len(u_sel))
    if len(u_sel) > 1:
        # Linear regression: RF1 = K * U1 + C
        p = np.polyfit(u_sel, rf_sel, 1)
        k_fit = p[0]
        c_fit = p[1]
        
        # Calculate R^2
        rf_pred = k_fit * u_sel + c_fit
        ss_res = np.sum((rf_sel - rf_pred)**2)
        ss_tot = np.sum((rf_sel - np.mean(rf_sel))**2)
        r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 1.0

        max_d_in_interval = np.max(d_sel) if len(d_sel) > 0 else 0.0

        print("Fitted Slope (K_stiffness): %.6f kN/mm" % k_fit)
        print("Fitted Intercept (C): %.8f kN" % c_fit)
        print("R-squared: %.8f" % r2)
        print("Max damage d in interval: %.6f" % max_d_in_interval)
        print("First 5 selected (U1, RF1) pairs:")
        for i in range(min(5, len(u_sel))):
            print("  U1 = %.6f mm, RF1 = %.6f kN" % (u_sel[i], rf_sel[i]))
    else:
        print("WARN: Not enough points in interval!")
    print("")

def main():
    h1_path = "/scratch/pr21vyci/adaptive-remeshing/runs/mode_ii_h1_sweep_u020_1379482.mmaster02/m2h1_u020.odb"
    h2_path = "/scratch/pr21vyci/adaptive-remeshing/runs/mode_ii_h2_serial_1379578.mmaster02/ModeII_H2_uniform_serial.odb"

    u1, rf1, d1 = get_rf_u_curve(h1_path)
    analyze_stiffness(u1, rf1, d1, "H1 U020 (1379482.mmaster02)")

    u2, rf2, d2 = get_rf_u_curve(h2_path)
    analyze_stiffness(u2, rf2, d2, "H2 UNIFORM (1379578.mmaster02)")

if __name__ == "__main__":
    main()

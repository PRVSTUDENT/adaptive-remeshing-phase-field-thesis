#!/usr/bin/env python3
"""
Inspect Job-1_UEL.dat reaction force history.
"""
import sys
import os

dat_path = sys.argv[1] if len(sys.argv) >= 2 else "/home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode2/06_paper_grounded_uel_preanalysis/Job-1_UEL.dat"

if not os.path.exists(dat_path):
    print("File not found:", dat_path)
    sys.exit(1)

u_vals = []
rf_vals = []
with open(dat_path, 'r') as f:
    for line in f:
        l = line.strip()
        if l.startswith('999999'):
            parts = [p.strip() for p in l.split() if p.strip()]
            if len(parts) >= 3:
                try:
                    u = float(parts[1])
                    rf = float(parts[2])
                    u_vals.append(u)
                    rf_vals.append(rf)
                except ValueError:
                    pass

print("Extracted %d RF1-U1 points from %s" % (len(u_vals), dat_path))
if u_vals:
    rf_max = max(rf_vals)
    idx_max = rf_vals.index(rf_max)
    u_peak = u_vals[idx_max]
    print("Peak Reaction Force: F_max = %.6f kN at u = %.6f mm" % (rf_max, u_peak))
    print("Latest Reached State: F = %.6f kN at u = %.6f mm" % (rf_vals[-1], u_vals[-1]))
    print("\nLast 10 points:")
    for u, rf in zip(u_vals[-10:], rf_vals[-10:]):
        print("  u = %.6f mm, RF1 = %.6f kN" % (u, rf))

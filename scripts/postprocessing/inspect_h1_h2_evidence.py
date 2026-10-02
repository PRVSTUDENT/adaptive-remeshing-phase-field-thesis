#!/usr/bin/env python3
"""
Inspect H1 (1389686) and H2 (1389687) trajectories and .dat reaction forces
"""

import os
import glob

def find_h1_h2():
    # Search for H1 and H2 results on cluster
    dirs = glob.glob("/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/**", recursive=True)
    h1_files = glob.glob("/home/pr21vyci/projects/adaptive-remeshing/**/M2CORR_H1*.*", recursive=True)
    h2_files = glob.glob("/home/pr21vyci/projects/adaptive-remeshing/**/M2CORR_H2*.*", recursive=True)
    
    print("Found H1 files:", h1_files[:5])
    print("Found H2 files:", h2_files[:5])
    
    for f in h1_files:
        if f.endswith(".dat") or f.endswith(".csv"):
            print(f"H1 evidence file: {f}")
            with open(f, "r", errors="ignore") as fp:
                for _ in range(15):
                    print("  ", fp.readline().rstrip())

if __name__ == "__main__":
    find_h1_h2()

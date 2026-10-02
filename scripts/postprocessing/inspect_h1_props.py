#!/usr/bin/env python3
"""
Inspect H1 and H2 geometry, dimensions, and UEL properties
"""

import os

def check_h1_props():
    h1_inp = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_verification_batch/M2CORR_H1_FREEU2_FULL_U050/M2CORR_H1_FREEU2_FULL_U050.inp"
    pk_inp = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R2_TOPOLOGY_CORRECTED/M2CORR_PK10R2_TOPOLOGY_CORRECTED.inp"
    
    print("=== H1 INP Header & Properties ===")
    with open(h1_inp, "r") as f:
        for _ in range(50):
            print(f.readline().rstrip())
            
    print("\n=== H1 UEL Properties ===")
    with open(h1_inp, "r") as f:
        for l in f:
            if "*UEL PROPERTY" in l.upper():
                print(l.rstrip())
                print(next(f).rstrip())

    print("\n=== PK10R2 UEL Properties ===")
    with open(pk_inp, "r") as f:
        for l in f:
            if "*UEL PROPERTY" in l.upper():
                print(l.rstrip())
                print(next(f).rstrip())

if __name__ == "__main__":
    check_h1_props()

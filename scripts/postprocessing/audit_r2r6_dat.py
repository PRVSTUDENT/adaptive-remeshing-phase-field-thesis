#!/usr/bin/env python3
from pathlib import Path

def audit_dat():
    dat_path = Path("/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R6/M2STATE_FRACFIX_RESTART2R6.dat")
    with open(dat_path, "r", errors="ignore") as f:
        lines = f.readlines()
        
    print(f"Total DAT lines: {len(lines)}")
    warnings = []
    errors = []
    fatals = []
    distorteds = []
    for idx, line in enumerate(lines):
        ll = line.lower()
        if "warning" in ll:
            warnings.append((idx+1, line.strip()))
        if "error" in ll:
            errors.append((idx+1, line.strip()))
        if "fatal" in ll:
            fatals.append((idx+1, line.strip()))
        if "distorted" in ll:
            distorteds.append((idx+1, line.strip()))
            
    print(f"Warnings found: {len(warnings)}")
    for w in warnings:
        print(f"  Line {w[0]}: {w[1]}")
    print(f"Errors found: {len(errors)}")
    for e in errors:
        print(f"  Line {e[0]}: {e[1]}")
    print(f"Fatals found: {len(fatals)}")
    print(f"Distorted elements warnings found: {len(distorteds)}")

if __name__ == "__main__":
    audit_dat()

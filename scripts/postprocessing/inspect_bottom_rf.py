#!/usr/bin/env python3
"""
Inspect lines around line 6386 in .dat
"""

def print_table_lines():
    dat_path = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R2_TOPOLOGY_CORRECTED/M2CORR_PK10R2_TOPOLOGY_CORRECTED.dat"
    with open(dat_path, "r", errors="ignore") as f:
        lines = [f.readline() for _ in range(6450)]
    for idx, l in enumerate(lines[6375:6430]):
        print(f"[{6376+idx}] {l.rstrip()}")

if __name__ == "__main__":
    print_table_lines()

#!/usr/bin/env python3
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
csv_path = ROOT / "models/generated/mode_ii/nonmatching_transfer_benchmarks/TARGET_NM1_RESTART/TARGET_NM1_INC29_PRIMARY_STATE.csv"
state_inp_path = ROOT / "models/generated/mode_ii/nonmatching_transfer_benchmarks/TARGET_NM1_RESTART/TARGET_NM1_INC29_STATE_INSTALL_BOUNDARY.inp"
u3_inp_path = ROOT / "models/generated/mode_ii/nonmatching_transfer_benchmarks/TARGET_NM1_RESTART/TARGET_NM1_INC29_U3_ONLY_BOUNDARY.inp"

print("=== RP NODE AUDIT (Node 6562) ===")

# 1. Check CSV
with open(csv_path) as f:
    reader = csv.DictReader(f)
    for r in reader:
        if r["target_node_id"] == "6562":
            print(f"CSV entry for RP node 6562:")
            for k, v in r.items():
                print(f"  {k}: {v}")

# 2. Check STATE_INSTALL INP
print("\nSTATE_INSTALL INP entries for 6562:")
with open(state_inp_path) as f:
    for line in f:
        if line.strip().startswith("6562,"):
            print(f"  {line.strip()}")

# 3. Check U3_ONLY INP
print("\nU3_ONLY INP entries for 6562:")
with open(u3_inp_path) as f:
    for line in f:
        if line.strip().startswith("6562,"):
            print(f"  {line.strip()}")

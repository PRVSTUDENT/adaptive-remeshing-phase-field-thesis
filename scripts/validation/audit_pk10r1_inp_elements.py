#!/usr/bin/env python3
import sys
from pathlib import Path
from collections import Counter

inp_path = Path("models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_CONTINUOUS_U050/M2CORR_PK10R1_CONTINUOUS_U050.inp")
if not inp_path.exists():
    inp_path = Path("projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_CONTINUOUS_U050/M2CORR_PK10R1_CONTINUOUS_U050.inp")

type_counts = Counter()
nodes = {}
elements = {}

current_type = None
in_node = False
in_elem = False

with open(inp_path, "r", encoding="utf-8", errors="ignore") as f:
    for line in f:
        l = line.strip()
        if not l or l.startswith("**"):
            continue
        if l.startswith("*"):
            in_node = False
            in_elem = False
            current_type = None

        if l.upper().startswith("*NODE"):
            in_node = True
            continue

        if l.upper().startswith("*ELEMENT"):
            in_elem = True
            for part in l.split(","):
                if "TYPE=" in part.upper():
                    current_type = part.split("=")[1].strip().upper()
                    break
            continue

        if in_node:
            parts = [p.strip() for p in l.split(",")]
            if len(parts) >= 3:
                try:
                    nid = int(parts[0])
                    nodes[nid] = (float(parts[1]), float(parts[2]))
                except ValueError:
                    pass

        if in_elem and current_type:
            parts = [p.strip() for p in l.split(",")]
            if len(parts) >= 4:
                try:
                    eid = int(parts[0])
                    type_counts[current_type] += 1
                except ValueError:
                    pass

print("=== PK10R1 INP AUDIT ===")
print(f"Total Nodes: {len(nodes)}")
print("Element Counts by Type:")
for t, count in sorted(type_counts.items()):
    print(f"  {t}: {count}")
print(f"Total Elements in INP: {sum(type_counts.values())}")

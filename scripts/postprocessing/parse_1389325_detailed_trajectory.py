#!/usr/bin/env python3
import re
import json
from pathlib import Path
import numpy as np

dat_path = Path("runs/hpc/mode_ii_state_transfer/evidence/1389325.mmaster02/M2STATE_FRACFIX_RESTART2R13.dat")
text = dat_path.read_text(encoding="utf-8", errors="ignore")
lines = text.splitlines()

# Find all INCREMENT blocks
inc_blocks = []
current_inc = None
current_step = None

for i, l in enumerate(lines):
    m_inc = re.search(r"INCREMENT\s+(\d+)\s+STARTS.*STEP\s+(\d+)", l)
    if m_inc:
        current_inc = int(m_inc.group(1))
        current_step = int(m_inc.group(2))
    elif "THE ANALYSIS HAS BEEN COMPLETED" in l or "INCREMENT" in l:
        pass

# Parse all node 99999 occurrences
rp_lines = []
for i, l in enumerate(lines):
    if l.strip().startswith("99999"):
        parts = l.split()
        if len(parts) >= 3:
            try:
                u1 = float(parts[1])
                rf1 = float(parts[2])
                rp_lines.append((i, u1, rf1))
            except ValueError:
                pass

print(f"Total RP records: {len(rp_lines)}")

# For each RP record, search backward/forward for MAXIMUM table
records = []
for idx, (line_idx, u1, rf1) in enumerate(rp_lines):
    # Search around line_idx for MAXIMUM
    max_d = 0.0
    for j in range(line_idx, min(len(lines), line_idx + 30)):
        if "MAXIMUM" in lines[j]:
            parts = lines[j].split()
            # columns: MAXIMUM U1 U2 U3 RF1 RF2 RF3
            for p in parts[1:]:
                try:
                    val = float(p)
                    # U3 is phase d
                    if 0.0 <= val <= 1.0 and val > max_d and val != u1:
                        max_d = val
                except ValueError:
                    pass
            break
    records.append({
        "inc_idx": idx,
        "u1_mm": u1,
        "rf1_kN": rf1,
        "rf1_N": rf1 * 1000.0,
        "max_d": max_d
    })

print(f"{'Idx':>4} {'U1 (mm)':>10} {'RF1 (kN)':>12} {'RF1 (N)':>10} {'d_max':>10}")
for r in records:
    print(f"{r['inc_idx']:>4d} {r['u1_mm']:>10.6f} {r['rf1_kN']:>12.6f} {r['rf1_N']:>10.2f} {r['max_d']:>10.4f}")

# Save detailed trajectory JSON
out_json = Path("runs/hpc/mode_ii_state_transfer/evidence/1389325.mmaster02/JOB_1389325_DETAILED_TRAJECTORY.json")
out_json.write_text(json.dumps(records, indent=2), encoding="utf-8")
print(f"Saved {out_json}")

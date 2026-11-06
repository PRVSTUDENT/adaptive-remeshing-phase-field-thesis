# -*- coding: utf-8 -*-
"""Extract load-displacement table from f1644_adapted_PK_HOLE_METHOD_A_ADAPT.dat."""
import re
import csv
from pathlib import Path

dat_path = Path("results/validation/f1644_adapted_PK_HOLE_METHOD_A_ADAPT.dat")
out_csv = Path("results/validation/f1644_adapted_rf_displacement.csv")

inc_pattern = re.compile(r"^\s*INCREMENT\s+(\d+)\s+SUMMARY")
step_pattern = re.compile(r"^\s*STEP\s+(\d+)\s+INCREMENT\s+(\d+)")
rp_pattern = re.compile(r"^\s*999999\s+([0-9.E+-]+)\s+([0-9.E+-]+)")

rows = []
current_inc = 0

with open(dat_path, "r", encoding="utf-8") as f:
    for line in f:
        m_step = step_pattern.search(line)
        if m_step:
            current_inc = int(m_step.group(2))
            continue
        m_inc = inc_pattern.search(line)
        if m_inc:
            current_inc = int(m_inc.group(1))
            continue
        m_rp = rp_pattern.search(line)
        if m_rp:
            u2 = float(m_rp.group(1))
            rf2 = float(m_rp.group(2))
            rows.append({
                "increment": current_inc,
                "u2_mm": u2,
                "rf2_kN": rf2
            })

with open(out_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["increment", "u2_mm", "rf2_kN"])
    writer.writeheader()
    writer.writerows(rows)

print(f"Extracted {len(rows)} load-displacement points to {out_csv}")
if rows:
    print(f"First: inc {rows[0]['increment']}, u2={rows[0]['u2_mm']}, rf2={rows[0]['rf2_kN']}")
    print(f"Last:  inc {rows[-1]['increment']}, u2={rows[-1]['u2_mm']}, rf2={rows[-1]['rf2_kN']}")

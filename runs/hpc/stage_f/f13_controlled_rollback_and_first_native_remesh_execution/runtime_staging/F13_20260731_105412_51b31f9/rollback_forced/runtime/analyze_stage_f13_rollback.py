#!/usr/bin/env python3
"""Summarize bounded F13 UEL rollback calls without requiring Abaqus Python."""
import argparse, json
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument("--calls", required=True)
p.add_argument("--output", required=True)
p.add_argument("--role", choices=("control", "forced"), required=True)
a = p.parse_args()
rows = []
for line in Path(a.calls).read_text(errors="replace").splitlines():
    cols = line.split()
    if len(cols) >= 21:
        rows.append(cols)
requests = [r for r in rows if float(r[9]) < float(r[8])]
penalty = [r for r in rows if float(r[18]) > 0.5]
reduced = [r for r in rows if float(r[4]) <= 0.015]
if a.role == "forced" and not requests:
    classification = "penalty_rollback_cutback_not_triggered"
elif a.role == "forced" and requests and not penalty:
    classification = "penalty_rollback_exercised_penalty_inactive"
elif a.role == "forced":
    classification = "penalty_rollback_inconclusive"
else:
    classification = "conservative_rollback_control_completed"
out = {"role": a.role, "bounded_call_count": len(rows),
       "diagnostic_pnewdt_request_count": len(requests),
       "penalty_active_call_count": len(penalty), "reduced_dtime_call_count": len(reduced),
       "classification": classification, "log_present": True}
Path(a.output).write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")

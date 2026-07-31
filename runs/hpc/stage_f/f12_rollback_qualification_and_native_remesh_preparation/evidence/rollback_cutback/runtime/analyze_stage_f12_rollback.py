#!/usr/bin/env python3
"""Classify bounded UEL-call and Abaqus message evidence for F12 rollback."""
import argparse, csv, json, re
from pathlib import Path

FIELDS = ["kstep", "kinc", "time1", "time2", "dtime", "call", "jelem", "ip",
          "lflag1", "lflag3", "lflag4", "nodal_phase", "received_svars_phase",
          "prior_phase", "trial_phase", "gap", "history", "penalty_energy",
          "penalty_residual", "penalty_tangent", "pnewdt"]


def read_calls(path):
    rows = []
    for line in path.read_text(errors="replace").splitlines():
        values = line.split()
        if len(values) != len(FIELDS):
            continue
        row = dict(zip(FIELDS, values))
        for key in FIELDS:
            row[key] = int(row[key]) if key in {"kstep", "kinc", "call", "jelem", "ip", "lflag1", "lflag3", "lflag4"} else float(row[key].replace("D", "E"))
        rows.append(row)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--calls", type=Path, required=True)
    ap.add_argument("--message", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--role", choices=["reference", "cutback"], required=True)
    a = ap.parse_args()
    rows = read_calls(a.calls)
    msg = a.message.read_text(errors="replace") if a.message.exists() else ""
    text_cutbacks = len(re.findall(r"cutback|time increment required is less|attempts made for this increment", msg, re.I))
    attempts = {}
    for row in rows:
        attempts.setdefault((row["kstep"], row["kinc"]), []).append(row)
    reductions = []
    for key, group in attempts.items():
        dts = []
        for row in group:
            if not dts or row["dtime"] != dts[-1]: dts.append(row["dtime"])
        for before, after in zip(dts, dts[1:]):
            if after < before: reductions.append({"kstep": key[0], "kinc": key[1], "original_dtime": before, "reduced_dtime": after})
    violations = []
    tol = 1.0e-12
    for red in reductions:
        group = attempts[(red["kstep"], red["kinc"])]
        retry = next((x for x in group if x["dtime"] == red["reduced_dtime"]), None)
        rejected = next((x for x in group if x["dtime"] == red["original_dtime"]), None)
        if retry and rejected:
            if abs(retry["received_svars_phase"] - retry["prior_phase"]) > tol: violations.append("phase_not_restored")
            if retry["history"] + tol < 0.0: violations.append("invalid_restored_history")
            if retry["penalty_energy"] > tol: violations.append("penalty_state_retained")
    exercised = bool(reductions and text_cutbacks)
    classification = ("penalty_rollback_qualified" if exercised and not violations else
                      "penalty_rollback_not_exercised" if not exercised else
                      "penalty_rollback_state_retention_failure")
    result = {"role": a.role, "bounded_call_count": len(rows), "text_cutback_signals": text_cutbacks,
              "cutback_count": len(reductions), "rejected_increment_attempts": reductions,
              "rollback_violations": sorted(set(violations)), "classification": classification,
              "floating_point_policy": 1.0e-12}
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return 0

if __name__ == "__main__": raise SystemExit(main())

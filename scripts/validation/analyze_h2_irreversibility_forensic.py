#!/usr/bin/env python3
"""Analyze Stage-F7 fixed-key extraction and create lightweight decisions."""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    json.loads(path.read_text(encoding="utf-8"))


def curve(path: Path):
    """Read only the declared numeric response columns.

    Production curves also contain textual provenance columns such as
    ``step=Step-1``.  Those are intentionally preserved in the CSV and must
    never be passed through ``float``.
    """
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        fields = set(reader.fieldnames or [])
        if {"u1", "rf1"} <= fields:
            u_col, rf_col = "u1", "rf1"
        elif {"rp_u1", "rp_rf1"} <= fields:
            u_col, rf_col = "rp_u1", "rp_rf1"
        else:
            raise ValueError(
                "missing explicit response schema; expected u1/rf1 or rp_u1/rp_rf1"
            )
        return [
            {"u1": float(row[u_col]), "rf1": float(row[rf_col])}
            for row in reader
            if row[u_col] not in ("", None) and row[rf_col] not in ("", None)
        ]


def interp(xs, ys, x):
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    lo = 0
    while lo + 1 < len(xs) and xs[lo + 1] < x:
        lo += 1
    ratio = (x - xs[lo]) / (xs[lo + 1] - xs[lo])
    return ys[lo] + ratio * (ys[lo + 1] - ys[lo])


def compare_curves(h1, h2):
    x1, y1 = [r["u1"] for r in h1], [r["rf1"] for r in h1]
    x2, y2 = [r["u1"] for r in h2], [r["rf1"] for r in h2]
    xmax = min(x1[-1], x2[-1])
    grid = [xmax * i / 200.0 for i in range(201)]
    a = [interp(x1, y1, x) for x in grid]
    b = [interp(x2, y2, x) for x in grid]
    denom = math.sqrt(sum(v * v for v in a)) or 1.0
    nrmse = math.sqrt(sum((u - v) ** 2 for u, v in zip(a, b))) / denom
    peak_start = max(x1[y1.index(max(y1))], x2[y2.index(max(y2))])
    ids = [i for i, x in enumerate(grid) if x >= peak_start]
    pden = math.sqrt(sum(a[i] ** 2 for i in ids)) or 1.0
    post = math.sqrt(sum((a[i] - b[i]) ** 2 for i in ids)) / pden
    return nrmse, post


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--h1-curve", type=Path, required=True)
    parser.add_argument("--h2-curve", type=Path, required=True)
    args = parser.parse_args()
    out = args.input_dir
    schema = load_json(out / "H2_ODB_FIELD_SCHEMA.json")
    summary = load_json(out / "H2_LOCAL_DELTA_SUMMARY.json")
    history_raw = load_json(out / "H2_HISTORY_VARIABLE_AUDIT_RAW.json")
    precision = str(schema.get("odb_precision", "not_exposed"))
    precision_policy = {
        "odb_precision": precision,
        "predeclared_reporting_tiers": [0, 1e-8, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3],
        "acceptance_rule": "strict fixed-key pass requires zero negative deltas; precision tiers are diagnostic only",
    }
    strict = int(summary["strict_negative_count"])
    minimum = summary.get("global_minimum_delta")
    overshoot_only = False
    record = summary.get("minimum_record") or {}
    if record:
        overshoot_only = record.get("previous_damage", 0) > 1 and record.get("current_damage", 0) >= 1
    if not summary.get("audit_complete"):
        classification = "h2_irreversibility_audit_incomplete"
    elif strict == 0:
        classification = "h2_irreversibility_strict_pass"
    elif overshoot_only and summary.get("affected_material_point_count") == 1:
        classification = "h2_irreversibility_overshoot_relaxation_only"
    else:
        classification = "h2_irreversibility_true_local_violation"

    h1 = curve(args.h1_curve)
    h2 = curve(args.h2_curve)
    nrmse, post_nrmse = compare_curves(h1, h2)
    h1_peak = max(h1, key=lambda r: r["rf1"])
    h2_peak = max(h2, key=lambda r: r["rf1"])
    comparison = {
        "h1_peak_rf1_kN": h1_peak["rf1"],
        "h2_peak_rf1_kN": h2_peak["rf1"],
        "peak_force_relative_difference_percent": 100 * (h2_peak["rf1"] / h1_peak["rf1"] - 1),
        "peak_displacement_difference_mm": h2_peak["u1"] - h1_peak["u1"],
        "h1_final_rf1_kN": h1[-1]["rf1"],
        "h2_final_rf1_kN": h2[-1]["rf1"],
        "final_force_relative_difference_percent": 100 * (h2[-1]["rf1"] / h1[-1]["rf1"] - 1),
        "common_grid_rf_u_nrmse": nrmse,
        "post_peak_rf_u_nrmse": post_nrmse,
        "local_damage_convergence_inferred": False,
    }
    envelope = {
        "diagnostic_only": True,
        "original_global_maximum_history_changed": strict > 0,
        "does_not_change_rf_u_response": True,
        "automatic_pass_prohibited": True,
    }
    history = dict(history_raw)
    history["source_interpretation"] = (
        "SDV14 is audited as a candidate driving/history field; final semantic "
        "meaning remains tied to the frozen Fortran variable map."
    )
    status = {
        "job_name": "M2H2IRR1",
        "pbs_job_id": __import__("os").environ.get("PBS_JOBID", "unknown"),
        "classification": classification,
        "audit_complete": summary.get("audit_complete"),
        "frames_audited": summary.get("frames_audited"),
        "material_points_last_frame": load_json(out / "H2_AUTHORITATIVE_POPULATION.json").get("key_count_last_frame"),
        "strict_negative_count": strict,
        "largest_fixed_point_decrease": minimum,
        "overshoot_relaxation_only": overshoot_only,
        "visualization_mapping_artifact": False,
        "solver_execution_count": 0,
        "final_exit_code": 0,
    }
    thresholds = summary["threshold_counts"]
    with (out / "H2_LOCAL_DELTA_THRESHOLDS.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["threshold", "negative_count"])
        for key in sorted(thresholds, key=float):
            writer.writerow([key, thresholds[key]])
    dump(out / "H2_HISTORY_VARIABLE_AUDIT.json", history)
    dump(out / "H2_MONOTONE_ENVELOPE_DIAGNOSTIC.json", envelope)
    dump(out / "H2_H1_GLOBAL_COMPARISON.json", comparison)
    dump(out / "H2_IRREVERSIBILITY_FORENSIC_STATUS.json", status)
    dump(out / "H2_NUMERICAL_PRECISION_POLICY.json", precision_policy)
    decision = f"""# H2 irreversibility forensic decision

Classification: `{classification}`

The complete fixed-key audit processed {summary.get('frames_audited')} frames.
It found {strict} strict negative local increments; the minimum was
`{minimum}`. Reporting tiers remain diagnostic and do not redefine the
acceptance gate. The monotone envelope is diagnostic only and cannot promote
the F6 result automatically.

Global H1--H2 RF--U agreement is reported separately. It does not establish
local phase-field convergence.
"""
    (out / "H2_IRREVERSIBILITY_DECISION.md").write_text(decision, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

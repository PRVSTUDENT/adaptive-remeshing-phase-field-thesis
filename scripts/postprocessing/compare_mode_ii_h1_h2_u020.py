#!/usr/bin/env python3
"""Compare frozen H1 u020 and Stage F6 H2 u020 response curves."""
import argparse
import csv
import json
import math
from pathlib import Path


def read_curve(path):
    rows = []
    with path.open(encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            u = float(row.get("u1", row.get("rp_u1")))
            rf = float(row.get("rf1", row.get("rf1_kN")))
            d = float(row.get("d_max", 0.0) or 0.0)
            if not rows or abs(u - rows[-1][0]) > 1.0e-12:
                rows.append((u, rf, d))
    return sorted(rows)


def interp(rows, x):
    if x <= rows[0][0]:
        return rows[0][1]
    if x >= rows[-1][0]:
        return rows[-1][1]
    for left, right in zip(rows, rows[1:]):
        if left[0] <= x <= right[0]:
            t = (x - left[0]) / (right[0] - left[0])
            return left[1] + t * (right[1] - left[1])
    raise ValueError(x)


def curve_nrmse(reference, candidate, u_min=0.0, u_max=0.020):
    grid = [r[0] for r in reference if u_min <= r[0] <= u_max]
    errors = [interp(candidate, u) - interp(reference, u) for u in grid]
    rmse = math.sqrt(sum(e * e for e in errors) / len(errors))
    values = [interp(reference, u) for u in grid]
    scale = max(values) - min(values)
    return rmse / scale if scale else None


def rel(candidate, reference):
    return (candidate - reference) / reference * 100.0


def compare(h1_summary, h2_summary, h1_curve, h2_curve):
    h1 = json.loads(h1_summary.read_text())
    h2 = json.loads(h2_summary.read_text())
    h1_data = h1.get("extracted_data", h1)
    h2_data = h2.get("extracted_data", h2)
    k1 = h1_data["initial_stiffness_kN_mm"]
    k2 = h2_data["initial_stiffness_kN_mm"]
    p1 = h1_data["peak_rf1"]
    p2 = h2_data["peak_rf1"]
    f1 = h1_data["final_rf1"]
    f2 = h2_data["final_rf1"]
    return {
        "classification": "stage_f6_h1_h2_u020_comparison",
        "h1": h1_data,
        "h2": h2_data,
        "stiffness_relative_difference_percent": rel(k2, k1),
        "peak_force_relative_difference_percent": rel(p2, p1),
        "peak_displacement_difference_mm": (
            h2_data["u1_at_peak_rf1"] - h1_data["u1_at_peak_rf1"]),
        "final_force_relative_difference_percent": rel(f2, f1),
        "common_grid_rf_u_nrmse": curve_nrmse(
            read_curve(h1_curve), read_curve(h2_curve)),
        "postpeak_rf_u_nrmse": curve_nrmse(
            read_curve(h1_curve), read_curve(h2_curve), 0.012, 0.020),
        "h2_frozen_reference_eligible": False,
        "claim_boundary": (
            "RF-U agreement does not by itself establish crack-path convergence."
        ),
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--h1-summary", type=Path, required=True)
    p.add_argument("--h2-summary", type=Path, required=True)
    p.add_argument("--h1-curve", type=Path, required=True)
    p.add_argument("--h2-curve", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    result = compare(a.h1_summary, a.h2_summary, a.h1_curve, a.h2_curve)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()

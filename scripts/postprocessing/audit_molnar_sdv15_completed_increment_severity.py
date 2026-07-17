#!/usr/bin/env python3
"""Audit severity of completed-increment SDV15 decreases."""

import argparse
import csv
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path


BINS = [
    ("(1e-12,1e-10]", 1.0e-12, 1.0e-10),
    ("(1e-10,1e-8]", 1.0e-10, 1.0e-8),
    ("(1e-8,1e-6]", 1.0e-8, 1.0e-6),
    ("(1e-6,1e-5]", 1.0e-6, 1.0e-5),
    ("(1e-5,1e-4]", 1.0e-5, 1.0e-4),
    (">1e-4", 1.0e-4, math.inf),
]


def f(value, default=math.nan):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def i(value, default=None):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def displacement_from_total_time(total_time):
    if total_time <= 1.0:
        return 0.005 * total_time
    return 0.005 + 0.002 * (total_time - 1.0)


def parse_nodes_and_u1_elements(inp_path):
    nodes = {}
    u1_elements = {}
    mode = None
    with inp_path.open(encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("**"):
                continue
            lower = line.lower()
            if lower.startswith("*node"):
                mode = "node"
                continue
            if lower.startswith("*element"):
                mode = "u1" if "type=u1" in lower else None
                continue
            if line.startswith("*"):
                mode = None
                continue
            parts = [part.strip() for part in line.split(",") if part.strip()]
            if mode == "node" and len(parts) >= 3:
                nodes[int(parts[0])] = (float(parts[1]), float(parts[2]))
            elif mode == "u1" and len(parts) >= 5:
                u1_elements[int(parts[0])] = tuple(int(part) for part in parts[1:5])
    return nodes, u1_elements


def centroid(nodes, element_nodes):
    coords = [nodes[n] for n in element_nodes if n in nodes]
    if not coords:
        return math.nan, math.nan
    return sum(x for x, _ in coords) / len(coords), sum(y for _, y in coords) / len(coords)


def percentile(values, pct):
    if not values:
        return math.nan
    ordered = sorted(values)
    pos = (len(ordered) - 1) * pct / 100.0
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return ordered[lo]
    return ordered[lo] * (hi - pos) + ordered[hi] * (pos - lo)


def bin_name(value):
    for name, low, high in BINS:
        if value > low and value <= high:
            return name
    if value <= 1.0e-12:
        return "<=1e-12"
    return ">1e-4"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--transitions", required=True)
    parser.add_argument("--inp", required=True)
    parser.add_argument("--outdir", required=True)
    parser.add_argument("--peak-u2", type=float, default=0.006110)
    parser.add_argument("--numerical-tolerance", type=float, default=1.0e-6)
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    nodes, elements = parse_nodes_and_u1_elements(Path(args.inp))

    rows = []
    with Path(args.transitions).open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            drop = f(row["phase_drop"])
            prev_phase = f(row["previous_phase_after_u1"])
            curr_phase = f(row["current_phase_after_u1"])
            curr_time = f(row["current_time2"])
            u2 = displacement_from_total_time(curr_time)
            phys = i(row["physical_element"])
            x, y = centroid(nodes, elements.get(phys, ()))
            rel = drop / abs(prev_phase) if prev_phase and not math.isnan(prev_phase) else math.nan
            enriched = dict(row)
            enriched.update({
                "current_u2_mm": u2,
                "centroid_x": x,
                "centroid_y": y,
                "abs_centroid_y": abs(y) if not math.isnan(y) else math.nan,
                "relative_drop": rel,
                "magnitude_bin": bin_name(drop),
                "before_or_at_peak": u2 <= args.peak_u2,
                "after_peak": u2 > args.peak_u2,
                "phase_overshoot_in_transition": prev_phase > 1.0 or curr_phase > 1.0,
                "near_crack_axis_abs_y_le_0p02": abs(y) <= 0.02 if not math.isnan(y) else False,
                "near_notch_left_half_x_le_0": x <= 0.0 if not math.isnan(x) else False,
            })
            rows.append(enriched)

    drops = [f(r["phase_drop"]) for r in rows]
    rel_drops = [f(r["relative_drop"]) for r in rows if not math.isnan(f(r["relative_drop"]))]
    locations = {(r["physical_element"], r["source_storage_ip"]) for r in rows}
    repeated = Counter((r["physical_element"], r["source_storage_ip"]) for r in rows)
    largest = max(rows, key=lambda r: f(r["phase_drop"])) if rows else {}

    tolerance_counts = {}
    for tol in (1.0e-10, 1.0e-8, 1.0e-6, 1.0e-5):
        tolerance_counts[str(tol)] = sum(1 for value in drops if value > tol)

    if rows and max(drops) <= args.numerical_tolerance:
        decision = "sdv15_completed_increment_numerical_tolerance_effect"
    elif rows:
        decision = "sdv15_completed_increment_irreversibility_violation"
    else:
        decision = "sdv15_completed_increment_review_incomplete"

    fieldnames = list(rows[0].keys()) if rows else []
    with (outdir / "sdv15_completed_increment_severity_audit.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "decision": decision,
        "numerical_tolerance_for_decision": args.numerical_tolerance,
        "transition_count": len(rows),
        "unique_affected_element_ip_locations": len(locations),
        "repeated_location_count": sum(1 for count in repeated.values() if count > 1),
        "max_decrease": max(drops) if drops else math.nan,
        "mean_decrease": statistics.mean(drops) if drops else math.nan,
        "median_decrease": statistics.median(drops) if drops else math.nan,
        "percentiles": {str(p): percentile(drops, p) for p in (50, 75, 90, 95, 99, 99.9)},
        "relative_drop_percentiles": {str(p): percentile(rel_drops, p) for p in (50, 75, 90, 95, 99, 99.9)},
        "magnitude_bins": dict(Counter(r["magnitude_bin"] for r in rows)),
        "tolerance_sensitivity_counts": tolerance_counts,
        "before_or_at_peak_count": sum(1 for r in rows if r["before_or_at_peak"]),
        "after_peak_count": sum(1 for r in rows if r["after_peak"]),
        "phase_overshoot_transition_count": sum(1 for r in rows if r["phase_overshoot_in_transition"]),
        "near_crack_axis_abs_y_le_0p02_count": sum(1 for r in rows if r["near_crack_axis_abs_y_le_0p02"]),
        "near_notch_left_half_x_le_0_count": sum(1 for r in rows if r["near_notch_left_half_x_le_0"]),
        "sdv16_decrease_count": sum(1 for r in rows if f(r["sdv16_drop"]) > 1.0e-10),
        "largest_transition": largest,
    }
    (outdir / "sdv15_completed_increment_severity_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    top_locations = repeated.most_common(25)
    with (outdir / "sdv15_completed_increment_repeated_locations.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["physical_element", "source_storage_ip", "transition_count"])
        writer.writeheader()
        for (phys, ip), count in top_locations:
            writer.writerow({"physical_element": phys, "source_storage_ip": ip, "transition_count": count})

    report = [
        "# SDV15 Completed-Increment Severity Audit",
        "",
        "Decision: `%s`" % decision,
        "",
        "This is a no-solution audit of the completed-increment transition table.",
        "It does not authorize or require a new Abaqus/PBS run.",
        "",
        "## Key Counts",
        "",
        "- Unique violating transitions: `%d`" % len(rows),
        "- Unique affected element/IP locations: `%d`" % len(locations),
        "- Repeated affected locations: `%d`" % summary["repeated_location_count"],
        "- Before or at peak displacement: `%d`" % summary["before_or_at_peak_count"],
        "- After peak displacement: `%d`" % summary["after_peak_count"],
        "- Coincident with SDV15 overshoot above one: `%d`" % summary["phase_overshoot_transition_count"],
        "- SDV16 decreases over same transitions: `%d`" % summary["sdv16_decrease_count"],
        "",
        "## Magnitudes",
        "",
        "- Max decrease: `%s`" % summary["max_decrease"],
        "- Mean decrease: `%s`" % summary["mean_decrease"],
        "- Median decrease: `%s`" % summary["median_decrease"],
        "- Magnitude bins: `%s`" % summary["magnitude_bins"],
        "- Tolerance sensitivity: `%s`" % summary["tolerance_sensitivity_counts"],
        "",
        "## Largest Transition",
        "",
        "```json",
        json.dumps(largest, indent=2, sort_keys=True),
        "```",
        "",
        "## Spatial Proxy",
        "",
        "Coordinates are U1 element centroids from the diagnostic input deck.",
        "The crack-corridor proxy is `abs(centroid_y) <= 0.02`; the notch-side proxy is `centroid_x <= 0`.",
        "",
        "- Near crack-axis proxy count: `%d`" % summary["near_crack_axis_abs_y_le_0p02_count"],
        "- Notch-side proxy count: `%d`" % summary["near_notch_left_half_x_le_0_count"],
        "",
    ]
    (outdir / "SDV15_COMPLETED_INCREMENT_SEVERITY_AUDIT.md").write_text("\n".join(report), encoding="utf-8")


if __name__ == "__main__":
    main()

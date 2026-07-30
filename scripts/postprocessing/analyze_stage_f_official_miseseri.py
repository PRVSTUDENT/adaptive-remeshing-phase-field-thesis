#!/usr/bin/env python3
"""Create deterministic statistics and plots from official job 1379893 CSV."""
from __future__ import print_function

import argparse
import csv
import hashlib
import json
import math
import os

EXPECTED_SHA = "49b0c5f7a784f361e846a7100370d5909e4e9e3faaa9c40694a40375c2e43ac5"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def percentile(values, pct):
    ordered = sorted(values)
    pos = (len(ordered) - 1) * pct / 100.0
    low, high = int(math.floor(pos)), int(math.ceil(pos))
    if low == high:
        return ordered[low]
    return ordered[low] * (high - pos) + ordered[high] * (pos - low)


def analyze(path):
    if sha256(path) != EXPECTED_SHA:
        raise ValueError("official CSV SHA-256 mismatch")
    rows = []
    with open(path, newline="") as stream:
        for row in csv.DictReader(stream):
            rows.append({
                "x": float(row["centroid_x"]),
                "y": float(row["centroid_y"]),
                "value": float(row["MISESERI"]),
            })
    values = [r["value"] for r in rows]
    if len(values) != 3930 or not all(math.isfinite(v) and v > 0 for v in values):
        raise ValueError("official MISESERI row/finite/positive contract failed")
    stats = {
        "source_job_id": "1379893.mmaster02",
        "source_csv_sha256": EXPECTED_SHA,
        "count": len(values),
        "min": min(values),
        "max": max(values),
        "mean": sum(values) / len(values),
        "median": percentile(values, 50),
    }
    for pct in (75, 90, 95, 99):
        threshold = percentile(values, pct)
        selected = [r for r in rows if r["value"] >= threshold]
        stats["p%d" % pct] = threshold
        stats["above_p%d" % pct] = {
            "threshold": threshold,
            "count": len(selected),
            "percentage": 100.0 * len(selected) / len(rows),
            "bounding_box": {
                "xmin": min(r["x"] for r in selected),
                "xmax": max(r["x"] for r in selected),
                "ymin": min(r["y"] for r in selected),
                "ymax": max(r["y"] for r in selected),
            },
            "hotspot_distance_from_notch_tip": {
                "assumed_notch_tip": [0.0, 0.0],
                "min": min(math.hypot(r["x"], r["y"]) for r in selected),
                "max": max(math.hypot(r["x"], r["y"]) for r in selected),
            },
        }
    stats["connected_regions"] = {
        "status": "not_computed",
        "reason": "CSV contains centroids/connectivity labels but no element-neighbor graph"
    }
    return rows, stats


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path")
    parser.add_argument("--json", required=True)
    parser.add_argument("--table", required=True)
    parser.add_argument("--spatial", required=True)
    parser.add_argument("--histogram", required=True)
    args = parser.parse_args()
    rows, stats = analyze(args.csv_path)
    for path in (args.json, args.table, args.spatial, args.histogram):
        parent = os.path.dirname(path)
        if parent and not os.path.isdir(parent):
            os.makedirs(parent)
    with open(args.json, "w") as stream:
        json.dump(stats, stream, indent=2, sort_keys=True)
        stream.write("\n")
    with open(args.table, "w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["metric", "value", "count_above", "percentage_above"])
        for key in ("count", "min", "max", "mean", "median", "p75", "p90", "p95", "p99"):
            above = stats.get("above_" + key, {})
            writer.writerow([key, stats[key], above.get("count", ""), above.get("percentage", "")])
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7, 5))
    points = ax.scatter([r["x"] for r in rows], [r["y"] for r in rows],
                        c=[r["value"] for r in rows], s=8, cmap="viridis")
    ax.set(xlabel="centroid x [mm]", ylabel="centroid y [mm]",
           title="Official PBS MISESERI field (job 1379893)")
    fig.colorbar(points, ax=ax, label="MISESERI")
    fig.tight_layout()
    fig.savefig(args.spatial, dpi=180)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.hist([r["value"] for r in rows], bins=80)
    ax.set(xlabel="MISESERI", ylabel="element count",
           title="Official PBS MISESERI distribution (job 1379893)")
    fig.tight_layout()
    fig.savefig(args.histogram, dpi=180)
    plt.close(fig)
    print(json.dumps({"count": stats["count"], "status": "pass"}))


if __name__ == "__main__":
    main()

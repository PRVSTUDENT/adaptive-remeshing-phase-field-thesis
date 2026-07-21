#!/usr/bin/env python3
"""Quantitative crack-path metrics from matched-state SDV15 CSVs."""
from __future__ import print_function

import argparse
import csv
import json
import math
import os
from pathlib import Path


def load_csv(path):
    rows = []
    with open(path) as f:
        r = csv.DictReader(f)
        for row in r:
            try:
                x = row.get("centroid_x")
                y = row.get("centroid_y")
                if x in (None, "", "None") or y in (None, "", "None"):
                    continue
                rows.append(
                    {
                        "label": int(float(row["element_label"])),
                        "x": float(x),
                        "y": float(y),
                        "sdv15": float(row["SDV15"]),
                        "area": float(row["EVOL"]) if row.get("EVOL") not in (None, "", "None") else None,
                    }
                )
            except Exception:
                continue
    return rows


def damaged(rows, thr):
    return [r for r in rows if r["sdv15"] >= thr]


def centerline(dmg):
    """For each unique x bin, take mean y of damaged elements (simple skeleton)."""
    if not dmg:
        return []
    bins = {}
    for r in dmg:
        xb = round(r["x"], 4)
        bins.setdefault(xb, []).append(r["y"])
    line = sorted((x, sum(ys) / len(ys)) for x, ys in bins.items())
    return line


def tip(dmg):
    if not dmg:
        return None
    # furthest +x in damaged set (crack grows right from notch tip ~0)
    r = max(dmg, key=lambda t: t["x"])
    return {"x": r["x"], "y": r["y"]}


def initiation(dmg):
    if not dmg:
        return None
    # nearest to notch tip (0,0) among damaged
    r = min(dmg, key=lambda t: math.hypot(t["x"], t["y"]))
    return {"x": r["x"], "y": r["y"]}


def extension(dmg):
    if not dmg:
        return 0.0
    xs = [r["x"] for r in dmg]
    return max(xs) - min(xs)


def damaged_area(dmg):
    areas = [r["area"] for r in dmg if r["area"] is not None]
    if not areas:
        return None
    return sum(areas)


def line_distances(a, b):
    """Mean/max distance from each point of a to nearest on b, and Hausdorff."""
    if not a or not b:
        return {"mean_ab": None, "max_ab": None, "hausdorff": None}

    def nn(p, line):
        return min(math.hypot(p[0] - q[0], p[1] - q[1]) for q in line)

    d_ab = [nn(p, b) for p in a]
    d_ba = [nn(p, a) for p in b]
    return {
        "mean_ab": sum(d_ab) / len(d_ab),
        "max_ab": max(d_ab),
        "mean_ba": sum(d_ba) / len(d_ba),
        "max_ba": max(d_ba),
        "hausdorff": max(max(d_ab), max(d_ba)),
    }


def metrics_for_csv(path, thr, n_total_guess=None):
    rows = load_csv(path)
    dmg = damaged(rows, thr)
    cl = centerline(dmg)
    area = damaged_area(dmg)
    n = len(rows) if rows else 0
    return {
        "threshold": thr,
        "n_elements_with_coords": n,
        "n_damaged": len(dmg),
        "damaged_fraction": (len(dmg) / float(n)) if n else None,
        "damaged_area": area,
        "initiation": initiation(dmg),
        "tip": tip(dmg),
        "extension": extension(dmg),
        "centerline_n": len(cl),
        "centerline": cl[:200],  # cap size in JSON
        "centerline_full_n": len(cl),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--extraction-root", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    root = Path(args.extraction_root)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "figures").mkdir(exist_ok=True)

    models = ["H1", "C2F_V3", "C2F_V3_REPEAT"]
    u_tags = ["0p004", "0p005", "0p0058", "0p0062", "0p007"]
    u_vals = [0.004, 0.005, 0.0058, 0.0062, 0.007]
    thresholds = [0.5, 0.95]

    rows_csv = []
    all_metrics = {}

    for model in models:
        all_metrics[model] = {}
        for u_tag, u in zip(u_tags, u_vals):
            # find matching file
            candidates = list((root / model).glob("SDV15_U_*.csv"))
            path = None
            for c in candidates:
                if u_tag in c.name or ("U_%s" % str(u).replace(".", "p")) in c.name:
                    path = c
                    break
            if path is None and candidates:
                # fuzzy: EXTRACTION may use 0p0040
                for c in candidates:
                    if str(u).replace(".", "p") in c.name.replace("0p0040", "0p004"):
                        path = c
                        break
            if path is None:
                # try exact from extract script naming SDV15_U_0p004.csv style
                for c in candidates:
                    if ("%.4f" % u).replace(".", "p") in c.name or ("%.3f" % u).replace(".", "p") in c.name:
                        path = c
                        break
            if path is None:
                # list and pick by index order of sorted
                sorted_c = sorted(candidates)
                if len(sorted_c) == len(u_vals):
                    path = sorted_c[u_vals.index(u)]
            if path is None or not path.is_file():
                all_metrics[model][str(u)] = {"error": "missing_csv"}
                continue
            all_metrics[model][str(u)] = {}
            for thr in thresholds:
                m = metrics_for_csv(str(path), thr)
                m["csv"] = str(path)
                m["U"] = u
                m["model"] = model
                all_metrics[model][str(u)][str(thr)] = m
                rows_csv.append(
                    {
                        "model": model,
                        "U": u,
                        "threshold": thr,
                        "n_damaged": m["n_damaged"],
                        "damaged_fraction": m["damaged_fraction"],
                        "extension": m["extension"],
                        "tip_x": (m["tip"] or {}).get("x"),
                        "tip_y": (m["tip"] or {}).get("y"),
                        "init_x": (m["initiation"] or {}).get("x"),
                        "init_y": (m["initiation"] or {}).get("y"),
                        "centerline_n": m["centerline_n"],
                    }
                )

    # Repeatability: V3 vs V3_REPEAT
    rep = {"classification": "crack_path_quantitative_metrics_computed", "pairs": []}
    for u in u_vals:
        for thr in thresholds:
            a = all_metrics.get("C2F_V3", {}).get(str(u), {}).get(str(thr))
            b = all_metrics.get("C2F_V3_REPEAT", {}).get(str(u), {}).get(str(thr))
            if not a or not b or a.get("error") or b.get("error"):
                continue
            dist = line_distances(a.get("centerline") or [], b.get("centerline") or [])
            rep["pairs"].append(
                {
                    "U": u,
                    "threshold": thr,
                    "extension_a": a["extension"],
                    "extension_b": b["extension"],
                    "n_damaged_a": a["n_damaged"],
                    "n_damaged_b": b["n_damaged"],
                    "centerline_distance": dist,
                }
            )
    # crude repeatability support if hausdorff small relative to plate (1 mm)
    haus = [p["centerline_distance"].get("hausdorff") for p in rep["pairs"] if p["centerline_distance"].get("hausdorff") is not None]
    if haus and max(haus) < 0.05:
        rep["classification"] = "crack_path_repeatability_supported"
    elif haus:
        rep["classification"] = "crack_path_deviation_detected"

    # H1 vs V3
    h1v3 = {"classification": "crack_path_quantitative_metrics_computed", "pairs": []}
    for u in u_vals:
        for thr in thresholds:
            a = all_metrics.get("H1", {}).get(str(u), {}).get(str(thr))
            b = all_metrics.get("C2F_V3", {}).get(str(u), {}).get(str(thr))
            if not a or not b or a.get("error") or b.get("error"):
                continue
            dist = line_distances(a.get("centerline") or [], b.get("centerline") or [])
            h1v3["pairs"].append(
                {
                    "U": u,
                    "threshold": thr,
                    "extension_H1": a["extension"],
                    "extension_v3": b["extension"],
                    "n_damaged_H1": a["n_damaged"],
                    "n_damaged_v3": b["n_damaged"],
                    "centerline_distance": dist,
                }
            )
    haus2 = [p["centerline_distance"].get("hausdorff") for p in h1v3["pairs"] if p["centerline_distance"].get("hausdorff") is not None]
    if haus2 and max(haus2) < 0.08:
        h1v3["classification"] = "crack_path_qualitatively_reproduced_quantitative_ok"
    elif haus2:
        h1v3["classification"] = "crack_path_deviation_detected"

    # write CSV
    with open(str(out / "CRACK_PATH_METRICS.csv"), "w") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "model",
                "U",
                "threshold",
                "n_damaged",
                "damaged_fraction",
                "extension",
                "tip_x",
                "tip_y",
                "init_x",
                "init_y",
                "centerline_n",
            ],
        )
        w.writeheader()
        for r in rows_csv:
            w.writerow(r)

    (out / "CRACK_PATH_REPEATABILITY.json").write_text(json.dumps(rep, indent=2, sort_keys=True) + "\n")
    (out / "H1_VS_REFINED_V3_CRACK_PATH.json").write_text(json.dumps(h1v3, indent=2, sort_keys=True) + "\n")
    (out / "CRACK_PATH_ALL_METRICS.json").write_text(json.dumps(all_metrics, indent=2, sort_keys=True) + "\n")

    md = [
        "# Quantitative crack-path metrics",
        "",
        "## Repeatability (v3 vs v3-repeat)",
        "",
        "`%s`" % rep["classification"],
        "",
        "## H1 vs refined-v3",
        "",
        "`%s`" % h1v3["classification"],
        "",
        "RF–U peak/pre-peak support remains separate from crack-path conclusions.",
        "",
        "See CRACK_PATH_METRICS.csv for tabulated metrics.",
        "",
    ]
    (out / "CRACK_PATH_QUANTITATIVE_REPORT.md").write_text("\n".join(md) + "\n")
    (out / "CRACK_PATH_METRICS_COMPLETE.ok").write_text("")
    print(json.dumps({"repeat": rep["classification"], "h1_vs_v3": h1v3["classification"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

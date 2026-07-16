#!/usr/bin/env python3
"""Final mesh-quality preflight for Molnar paper-matched candidate v2."""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

import yaml

from validate_molnar_paper_matched_single_notch import parse_deck, signed_area, aspect_ratio


TOL = 1.0e-9


def read_mesh_stats(path: Path) -> dict[str, float]:
    with path.open(newline="", encoding="utf-8") as stream:
        return {row["quantity"]: float(row["value"]) for row in csv.DictReader(stream)}


def distance_point_to_box(px: float, py: float, bounds: tuple[float, float, float, float]) -> float:
    xmin, xmax, ymin, ymax = bounds
    dx = max(xmin - px, 0.0, px - xmax)
    dy = max(ymin - py, 0.0, py - ymax)
    return math.hypot(dx, dy)


def intersects_box(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> bool:
    ax0, ax1, ay0, ay1 = a
    bx0, bx1, by0, by1 = b
    return ax0 <= bx1 + TOL and ax1 + TOL >= bx0 and ay0 <= by1 + TOL and ay1 + TOL >= by0


def summarize_group(elements: list[dict], threshold: float, refined: tuple[float, float, float, float]) -> dict:
    group = [element for element in elements if element["aspect"] > threshold]
    if not group:
        return {
            "threshold": threshold,
            "count": 0,
            "bounds": None,
            "minimum_notch_tip_distance": None,
            "inside_refined_strip_count": 0,
            "intersects_crack_path_count": 0,
            "minimum_signed_area": None,
            "max_aspect": None,
        }
    xmin = min(e["bounds"][0] for e in group)
    xmax = max(e["bounds"][1] for e in group)
    ymin = min(e["bounds"][2] for e in group)
    ymax = max(e["bounds"][3] for e in group)
    return {
        "threshold": threshold,
        "count": len(group),
        "bounds": (xmin, xmax, ymin, ymax),
        "minimum_notch_tip_distance": min(e["notch_tip_distance"] for e in group),
        "inside_refined_strip_count": sum(1 for e in group if e["centroid_inside_refined"]),
        "intersects_crack_path_count": sum(1 for e in group if e["intersects_crack_path"]),
        "minimum_signed_area": min(e["area"] for e in group),
        "max_aspect": max(e["aspect"] for e in group),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/molnar_paper_matched_single_notch.yaml")
    parser.add_argument("--deck", default="models/generated/molnar_gravouil_2017/paper_matched_single_notch_v2/paper_matched_single_notch_v2.inp")
    parser.add_argument("--mesh-stats", default="models/generated/molnar_gravouil_2017/paper_matched_single_notch_v2/mesh_statistics.csv")
    parser.add_argument("--out", default="results/validation/molnar_paper_matched_single_notch_v2/MESH_QUALITY_PREFLIGHT.md")
    args = parser.parse_args()

    config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    parsed = parse_deck(Path(args.deck).read_text(encoding="utf-8"))
    nodes = parsed["nodes"]
    physical = int(config["mesh"]["estimated_physical_element_count"])
    refined_cfg = config["mesh"]["recipe"]["refined_zone"]
    refined = (
        float(refined_cfg["x_min"]),
        float(refined_cfg["x_max"]),
        float(refined_cfg["y_min"]),
        float(refined_cfg["y_max"]),
    )
    crack_path = (0.0, 0.5, 0.0, 0.0)
    lower = set(parsed["nsets"].get("notch_lower_face", []))
    upper = set(parsed["nsets"].get("notch_upper_face", []))
    mesh_stats = read_mesh_stats(Path(args.mesh_stats))

    elements = []
    bridges = 0
    for eid in range(1, physical + 1):
        element = parsed["elements"][eid]
        connectivity = element["connectivity"]
        coords = [nodes[node] for node in connectivity]
        xs = [x for x, _ in coords]
        ys = [y for _, y in coords]
        bounds = (min(xs), max(xs), min(ys), max(ys))
        cx = sum(xs) / 4.0
        cy = sum(ys) / 4.0
        area = signed_area(coords)
        aspect = aspect_ratio(coords)
        node_set = set(connectivity)
        if node_set & lower and node_set & upper:
            bridges += 1
        elements.append(
            {
                "id": eid,
                "connectivity": connectivity,
                "bounds": bounds,
                "centroid": (cx, cy),
                "area": area,
                "aspect": aspect,
                "notch_tip_distance": distance_point_to_box(0.0, 0.0, bounds),
                "centroid_inside_refined": refined[0] - TOL <= cx <= refined[1] + TOL and refined[2] - TOL <= cy <= refined[3] + TOL,
                "intersects_crack_path": bounds[0] <= crack_path[1] + TOL and bounds[1] >= crack_path[0] - TOL and bounds[2] <= 0.0 + TOL and bounds[3] >= 0.0 - TOL,
            }
        )

    groups = [summarize_group(elements, threshold, refined) for threshold in (5.0, 10.0, 20.0)]
    max_element = max(elements, key=lambda item: item["aspect"])
    max_ratio = max(mesh_stats["max_neighbor_size_ratio_x"], mesh_stats["max_neighbor_size_ratio_y"])
    positive_area = min(e["area"] for e in elements) > 0.0
    high_aspect_compromises_refined = any(g["inside_refined_strip_count"] or g["intersects_crack_path_count"] for g in groups)
    high_aspect_at_notch_tip = any(g["minimum_notch_tip_distance"] is not None and g["minimum_notch_tip_distance"] <= 0.001 + TOL for g in groups)
    pass_preflight = (
        not high_aspect_at_notch_tip
        and not high_aspect_compromises_refined
        and positive_area
        and bridges == 0
        and max_ratio <= 1.5 + 1.0e-9
    )

    lines = [
        "# Mesh Quality Preflight - Molnar Paper-Matched Single-Notch v2",
        "",
        "Date: 2026-07-16",
        "",
        f"Classification: `{'mesh_quality_preflight_pass' if pass_preflight else 'mesh_quality_preflight_fail'}`",
        "",
        "## Summary",
        "",
        f"- Physical elements checked: `{physical}`",
        f"- Maximum aspect ratio: `{max_element['aspect']}`",
        f"- Maximum neighboring-size ratio: `{max_ratio}`",
        f"- Minimum signed area/Jacobian indicator: `{min(e['area'] for e in elements)}`",
        f"- Elements bridging the open notch: `{bridges}`",
        "",
        "## High Aspect-Ratio Groups",
        "",
        "| Threshold | Count | Coordinate bounds | Min distance from notch tip | Inside refined strip | Intersects expected crack path | Min signed area | Max aspect | Max neighbor ratio |",
        "|---:|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for group in groups:
        bounds = "none" if group["bounds"] is None else f"x={group['bounds'][0]}..{group['bounds'][1]}, y={group['bounds'][2]}..{group['bounds'][3]}"
        lines.append(
            f"| > {group['threshold']} | {group['count']} | {bounds} | {group['minimum_notch_tip_distance']} | "
            f"{group['inside_refined_strip_count']} | {group['intersects_crack_path_count']} | {group['minimum_signed_area']} | {group['max_aspect']} | {max_ratio} |"
        )
    lines.extend(
        [
            "",
            "## Maximum Aspect-Ratio Element",
            "",
            f"- Element ID: `{max_element['id']}`",
            f"- Aspect ratio: `{max_element['aspect']}`",
            f"- Connectivity: `{max_element['connectivity']}`",
            f"- Coordinate bounds: `x={max_element['bounds'][0]}..{max_element['bounds'][1]}, y={max_element['bounds'][2]}..{max_element['bounds'][3]}`",
            f"- Centroid: `{max_element['centroid']}`",
            f"- Minimum distance from notch tip: `{max_element['notch_tip_distance']}`",
            f"- Inside refined fracture strip: `{max_element['centroid_inside_refined']}`",
            f"- Intersects expected horizontal crack path: `{max_element['intersects_crack_path']}`",
            f"- Signed area/Jacobian indicator: `{max_element['area']}`",
            "",
            "## Decision",
            "",
            "- High-aspect-ratio elements are acceptable only as a documented reconstruction limitation when confined outside the notch-tip/fracture-process corridor.",
            f"- Preflight pass: `{pass_preflight}`",
            "",
        ]
    )
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text("\n".join(lines), encoding="utf-8")
    print(f"classification={'mesh_quality_preflight_pass' if pass_preflight else 'mesh_quality_preflight_fail'}")
    print(f"max_aspect_element={max_element['id']}")
    return 0 if pass_preflight else 2


if __name__ == "__main__":
    raise SystemExit(main())

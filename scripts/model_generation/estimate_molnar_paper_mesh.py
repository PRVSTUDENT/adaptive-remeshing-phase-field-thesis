#!/usr/bin/env python3
"""Shared mesh-spacing and estimate utilities for the Molnar paper candidate."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import yaml


TOL = 1.0e-10


@dataclass(frozen=True)
class AxisSpacing:
    coordinates: list[float]
    spacings: list[float]


def load_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as stream:
        return yaml.safe_load(stream)


def _round_coord(value: float) -> float:
    rounded = round(value, 10)
    return 0.0 if abs(rounded) < 5.0e-9 else rounded


def _graded_sizes_to_refined(length: float, local_h: float, global_h: float, ratio: float) -> list[float]:
    """Return sizes from the coarse boundary toward a refined boundary."""
    transition = []
    size = local_h
    while size < global_h:
        transition.append(size)
        size *= ratio
    if transition[-1] < global_h:
        transition.append(global_h)
    transition_sum = sum(transition)
    if transition_sum >= length:
        n = max(1, round(length / local_h))
        return [length / n] * n
    remaining = length - transition_sum
    coarse_count = max(1, int((remaining + global_h - TOL) // global_h))
    coarse = [remaining / coarse_count] * coarse_count
    return coarse + list(reversed(transition))


def _axis_with_refined_region(start: float, refined_min: float, refined_max: float, end: float, local_h: float, global_h: float, ratio: float) -> AxisSpacing:
    left_sizes = _graded_sizes_to_refined(refined_min - start, local_h, global_h, ratio)
    refined_count = round((refined_max - refined_min) / local_h)
    refined_sizes = [local_h] * refined_count
    right_sizes = list(reversed(_graded_sizes_to_refined(end - refined_max, local_h, global_h, ratio)))
    sizes = left_sizes + refined_sizes + right_sizes
    coords = [start]
    for size in sizes:
        coords.append(_round_coord(coords[-1] + size))
    coords[-1] = _round_coord(end)
    return AxisSpacing(coords, [round(coords[i + 1] - coords[i], 10) for i in range(len(coords) - 1)])


def _axis_refined_to_end(start: float, refined_min: float, end: float, local_h: float, global_h: float, ratio: float) -> AxisSpacing:
    left_sizes = _graded_sizes_to_refined(refined_min - start, local_h, global_h, ratio)
    refined_count = round((end - refined_min) / local_h)
    sizes = left_sizes + [local_h] * refined_count
    coords = [start]
    for size in sizes:
        coords.append(_round_coord(coords[-1] + size))
    coords[-1] = _round_coord(end)
    return AxisSpacing(coords, [round(coords[i + 1] - coords[i], 10) for i in range(len(coords) - 1)])


def make_axis_spacings(config: dict) -> tuple[AxisSpacing, AxisSpacing]:
    mesh = config["mesh"]
    recipe = mesh["recipe"]
    geom = config["geometry"]
    width = float(geom["width"])
    height = float(geom["height"])
    local_h = float(mesh["local_element_size"])
    global_h = float(recipe["global_element_size"])
    ratio = float(recipe["maximum_neighbouring_size_ratio"])
    refined = recipe["refined_zone"]
    x_axis = _axis_refined_to_end(
        -width / 2,
        float(refined["x_min"]),
        width / 2,
        local_h,
        global_h,
        ratio,
    )
    y_axis = _axis_with_refined_region(
        -height / 2,
        float(refined["y_min"]),
        float(refined["y_max"]),
        height / 2,
        local_h,
        global_h,
        ratio,
    )
    return x_axis, y_axis


def max_neighbor_ratio(spacings: list[float]) -> float:
    ratios = []
    for a, b in zip(spacings, spacings[1:]):
        if min(abs(a), abs(b)) > TOL:
            ratios.append(max(abs(a), abs(b)) / min(abs(a), abs(b)))
    return max(ratios) if ratios else 1.0


def estimate(config: dict) -> dict:
    x_axis, y_axis = make_axis_spacings(config)
    mesh = config["mesh"]
    geom = config["geometry"]
    fracture = config["fracture"]
    recipe = mesh["recipe"]
    h = float(mesh["local_element_size"])
    lc = float(fracture["selected_length_scale"])
    physical = (len(x_axis.coordinates) - 1) * (len(y_axis.coordinates) - 1)
    refined = recipe["refined_zone"]
    refined_count = 0
    transition_count = 0
    coarse_count = 0
    notch_adjacent = 0
    crossing_notch = 0
    for j in range(len(y_axis.coordinates) - 1):
        y0, y1 = y_axis.coordinates[j], y_axis.coordinates[j + 1]
        yc = 0.5 * (y0 + y1)
        for i in range(len(x_axis.coordinates) - 1):
            x0, x1 = x_axis.coordinates[i], x_axis.coordinates[i + 1]
            xc = 0.5 * (x0 + x1)
            in_refined = (
                float(refined["x_min"]) <= xc <= float(refined["x_max"])
                and float(refined["y_min"]) <= yc <= float(refined["y_max"])
            )
            near_refined = (
                float(refined["x_min"]) - float(recipe["transition_region_width"]) <= xc <= float(refined["x_max"])
                and float(refined["y_min"]) - float(recipe["transition_region_width"]) <= yc <= float(refined["y_max"]) + float(recipe["transition_region_width"])
            )
            if in_refined:
                refined_count += 1
            elif near_refined:
                transition_count += 1
            else:
                coarse_count += 1
            if -0.5 <= xc < 0.0 and (abs(y0) < TOL or abs(y1) < TOL):
                notch_adjacent += 1
            if x0 < 0.0 and x1 <= 0.0 and y0 < 0.0 < y1:
                crossing_notch += 1
    min_size = min(min(x_axis.spacings), min(y_axis.spacings))
    max_size = max(max(x_axis.spacings), max(y_axis.spacings))
    checks = {
        "h_over_l_target": abs((h / lc) - float(mesh["h_over_l"])) < 1.0e-6,
        "positive_dimensions": float(geom["width"]) > 0 and float(geom["height"]) > 0 and h > 0 and lc > 0,
        "refined_zone_contained": (
            -float(geom["width"]) / 2 <= float(refined["x_min"]) < float(refined["x_max"]) <= float(geom["width"]) / 2
            and -float(geom["height"]) / 2 <= float(refined["y_min"]) < float(refined["y_max"]) <= float(geom["height"]) / 2
        ),
        "valid_transition_ratios": max(max_neighbor_ratio(x_axis.spacings), max_neighbor_ratio(y_axis.spacings)) <= float(recipe["maximum_neighbouring_size_ratio"]) + 1.0e-9,
        "expected_layering": physical * int(mesh["layer_count"]) == physical * 3,
        "notch_grid_alignment": 0.0 in x_axis.coordinates and 0.0 in y_axis.coordinates,
    }
    return {
        "x_node_count": len(x_axis.coordinates),
        "y_node_count": len(y_axis.coordinates),
        "x_element_count": len(x_axis.coordinates) - 1,
        "y_element_count": len(y_axis.coordinates) - 1,
        "refined_region_physical_elements": refined_count,
        "transition_region_physical_elements": transition_count,
        "coarse_region_physical_elements": coarse_count,
        "total_physical_elements": physical,
        "total_layered_elements": physical * int(mesh["layer_count"]),
        "h_over_l": h / lc,
        "minimum_edge_size_mm": min_size,
        "maximum_edge_size_mm": max_size,
        "max_neighbor_size_ratio_x": max_neighbor_ratio(x_axis.spacings),
        "max_neighbor_size_ratio_y": max_neighbor_ratio(y_axis.spacings),
        "notch_adjacent_elements": notch_adjacent,
        "elements_crossing_open_notch_segment": crossing_notch,
        "checks": checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/molnar_paper_matched_single_notch.yaml")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = estimate(load_config(Path(args.config)))
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for key, value in result.items():
            print(f"{key}: {value}")
    return 0 if all(result["checks"].values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())

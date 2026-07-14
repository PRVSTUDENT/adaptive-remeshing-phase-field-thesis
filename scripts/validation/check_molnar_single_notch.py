#!/usr/bin/env python
"""Scientific-review checks for the unchanged Molnar single-notch benchmark.

Run with Abaqus Python because the bounds and irreversibility diagnostics read
the ODB directly:

    abaqus python scripts/validation/check_molnar_single_notch.py

The script does not modify the ODB or the frozen unchanged run. It produces a
scientific-check package and classifies Gate A3 conservatively when reference
data are insufficient.
"""

from __future__ import print_function

import argparse
import csv
import json
import math
import os
import sys
from collections import defaultdict, deque


RUN_DIR = os.path.join(
    "runs",
    "molnar_single_notch_unchanged",
    "20260714_technical_gate_local",
)
EXTRACTED_DIR = os.path.join(RUN_DIR, "extracted")
WORK_DIR = os.path.join(RUN_DIR, "work")
DEFAULT_ODB = os.path.join(WORK_DIR, "SingleNotch.odb")
DEFAULT_INP = os.path.join(WORK_DIR, "SingleNotch.inp")
DEFAULT_OUTPUT_DIR = os.path.join(RUN_DIR, "scientific_check")
DEFAULT_RF_U = os.path.join(EXTRACTED_DIR, "single_notch_rf_u_phase_summary.csv")
DEFAULT_MATCHED = os.path.join(EXTRACTED_DIR, "single_notch_matched_displacement_states.csv")
DEFAULT_RF_REF = os.path.join(
    "references",
    "derived",
    "molnar_gravouil_2017",
    "single_notch",
    "rf_u_reference.csv",
)
DEFAULT_CRACK_REF = os.path.join(
    "references",
    "derived",
    "molnar_gravouil_2017",
    "single_notch",
    "crack_path_reference.csv",
)
DEFAULT_TOLERANCES = os.path.join(
    "configs", "validation", "stage_a_single_notch_tolerances.json"
)

D_CRIT = 0.95
IRREVERSIBILITY_TOL = 1.0e-8
BOUND_TOL = 1.0e-8
ODB_PRECISION_TOL = 1.0e-6


def import_odb_access():
    try:
        from odbAccess import openOdb  # type: ignore
    except ImportError:
        print("ERROR: odbAccess unavailable. Run with Abaqus Python.", file=sys.stderr)
        return None
    return openOdb


def scalar_data(value):
    data = value.data
    try:
        return float(data[0])
    except (TypeError, IndexError):
        return float(data)


def vector_component(value, index):
    data = value.data
    try:
        return float(data[index])
    except (TypeError, IndexError):
        return float(data)


def read_csv_dicts(path):
    with open(path, "r", newline="") as stream:
        return list(csv.DictReader(stream))


def numeric_rows(rows, x_name, y_name):
    result = []
    for row in rows:
        try:
            x = float(row[x_name])
            y = float(row[y_name])
        except (KeyError, TypeError, ValueError):
            continue
        if math.isfinite(x) and math.isfinite(y):
            result.append({"x": x, "y": y, "raw": row})
    result.sort(key=lambda item: item["x"])
    return result


def trapz(x_values, y_values):
    total = 0.0
    for x0, x1, y0, y1 in zip(x_values[:-1], x_values[1:], y_values[:-1], y_values[1:]):
        total += 0.5 * (y0 + y1) * (x1 - x0)
    return total


def interpolate(points, x):
    if not points or x < points[0]["x"] or x > points[-1]["x"]:
        return None
    for left, right in zip(points[:-1], points[1:]):
        if left["x"] <= x <= right["x"]:
            dx = right["x"] - left["x"]
            if abs(dx) < 1.0e-15:
                return left["y"]
            ratio = (x - left["x"]) / dx
            return left["y"] + ratio * (right["y"] - left["y"])
    return points[-1]["y"] if abs(x - points[-1]["x"]) < 1.0e-15 else None


def rf_u_metrics(curve_rows, ref_rows, matched_rows):
    sim_points = numeric_rows(curve_rows, "rp_u2", "rp_rf2")
    ref_points = numeric_rows(ref_rows, "displacement_u2", "reaction_force")
    x = [item["x"] for item in sim_points]
    y = [item["y"] for item in sim_points]
    peak_index = max(range(len(y)), key=lambda index: y[index])
    final_force = y[-1]
    initial_limit = 0.001
    initial = [item for item in sim_points if 0.0 <= item["x"] <= initial_limit]
    if len(initial) >= 2:
        stiffness = (initial[-1]["y"] - initial[0]["y"]) / (initial[-1]["x"] - initial[0]["x"])
    else:
        stiffness = None
    simulation = {
        "initial_tangent_interval_u2": [0.0, initial_limit],
        "initial_tangent_stiffness": stiffness,
        "peak_reaction_force": y[peak_index],
        "displacement_at_peak": x[peak_index],
        "area_under_rf_u": trapz(x, y),
        "post_peak_force_drop": y[peak_index] - final_force,
        "final_residual_force": final_force,
        "final_displacement": x[-1],
    }
    comparison = {
        "reference_available": bool(ref_points),
        "reference_point_count": len(ref_points),
        "common_range": None,
        "relative_peak_force_error": None,
        "relative_peak_displacement_error": None,
        "curve_nrmse": None,
        "matched_force_errors": [],
        "reason": None,
    }
    comparison_rows = []
    for row in matched_rows:
        u = float(row["rp_u2"])
        comparison_rows.append(
            {
                "u2": u,
                "simulation_rf2": float(row["rp_rf2"]),
                "reference_rf2": "",
                "absolute_error": "",
                "relative_error": "",
                "status": "reference_unavailable",
            }
        )
    if not ref_points:
        comparison["reason"] = "No numeric RF-U reference coordinates are available."
        return simulation, comparison, comparison_rows

    common_min = max(sim_points[0]["x"], ref_points[0]["x"])
    common_max = min(sim_points[-1]["x"], ref_points[-1]["x"])
    comparison["common_range"] = [common_min, common_max]
    ref_peak_index = max(range(len(ref_points)), key=lambda index: ref_points[index]["y"])
    ref_peak = ref_points[ref_peak_index]
    comparison["relative_peak_force_error"] = (
        (simulation["peak_reaction_force"] - ref_peak["y"]) / ref_peak["y"]
        if abs(ref_peak["y"]) > 1.0e-15
        else None
    )
    comparison["relative_peak_displacement_error"] = (
        (simulation["displacement_at_peak"] - ref_peak["x"]) / ref_peak["x"]
        if abs(ref_peak["x"]) > 1.0e-15
        else None
    )
    sample_x = [item["x"] for item in sim_points if common_min <= item["x"] <= common_max]
    errors = []
    ref_values = []
    for sx in sample_x:
        sy = interpolate(sim_points, sx)
        ry = interpolate(ref_points, sx)
        if sy is None or ry is None:
            continue
        errors.append((sy - ry) ** 2)
        ref_values.append(ry)
    if errors and ref_values:
        rmse = math.sqrt(sum(errors) / len(errors))
        scale = max(ref_values) - min(ref_values)
        comparison["curve_nrmse"] = rmse / scale if abs(scale) > 1.0e-15 else None
    comparison_rows = []
    for row in matched_rows:
        u = float(row["rp_u2"])
        sim = float(row["rp_rf2"])
        ref = interpolate(ref_points, u)
        if ref is None:
            comparison_rows.append(
                {
                    "u2": u,
                    "simulation_rf2": sim,
                    "reference_rf2": "",
                    "absolute_error": "",
                    "relative_error": "",
                    "status": "outside_reference_range",
                }
            )
        else:
            comparison_rows.append(
                {
                    "u2": u,
                    "simulation_rf2": sim,
                    "reference_rf2": ref,
                    "absolute_error": sim - ref,
                    "relative_error": (sim - ref) / ref if abs(ref) > 1.0e-15 else "",
                    "status": "compared",
                }
            )
    comparison["matched_force_errors"] = comparison_rows
    return simulation, comparison, comparison_rows


def parse_nodes_elements(inp_path):
    nodes = {}
    elements = {}
    section = None
    with open(inp_path, "r", errors="replace") as stream:
        for raw in stream:
            line = raw.strip()
            if not line or line.startswith("**"):
                continue
            lower = line.lower()
            if lower.startswith("*assembly"):
                break
            if lower.startswith("*node"):
                section = "node"
                continue
            if lower.startswith("*element"):
                section = "element"
                continue
            if line.startswith("*"):
                section = None
                continue
            parts = [part.strip() for part in line.split(",") if part.strip()]
            if section == "node" and len(parts) >= 3:
                nodes[int(parts[0])] = (float(parts[1]), float(parts[2]))
            elif section == "element" and len(parts) >= 5:
                elements[int(parts[0])] = [int(item) for item in parts[1:5]]
    return nodes, elements


def centroids_and_adjacency(nodes, elements):
    centroids = {}
    node_to_elements = defaultdict(list)
    for element, conn in elements.items():
        coords = [nodes[node] for node in conn if node in nodes]
        if coords:
            centroids[element] = (
                sum(coord[0] for coord in coords) / len(coords),
                sum(coord[1] for coord in coords) / len(coords),
            )
        for node in conn:
            node_to_elements[node].append(element)
    adjacency = defaultdict(set)
    for labels in node_to_elements.values():
        for label in labels:
            adjacency[label].update(other for other in labels if other != label)
    return centroids, adjacency


def read_contour_elements(path, centroids):
    grouped = defaultdict(list)
    for row in read_csv_dicts(path):
        try:
            element = int(row["element"])
            value = float(row["sdv15"])
        except (KeyError, TypeError, ValueError):
            continue
        if element in centroids:
            grouped[element].append(value)
    result = []
    for element, values in grouped.items():
        x, y = centroids[element]
        result.append({"element": element, "x": x, "y": y, "sdv15": sum(values) / len(values)})
    return result


def connected_component(damaged_elements, adjacency, seed):
    damaged = set(damaged_elements)
    if seed not in damaged:
        return set()
    seen = {seed}
    queue = deque([seed])
    while queue:
        current = queue.popleft()
        for other in adjacency[current]:
            if other in damaged and other not in seen:
                seen.add(other)
                queue.append(other)
    return seen


def crack_metrics(contour_rows, adjacency):
    damaged = [row for row in contour_rows if row["sdv15"] >= D_CRIT]
    if not damaged:
        return {
            "damaged_element_count": 0,
            "connected": False,
            "crack_initiation_x": None,
            "crack_initiation_y": None,
            "crack_extension": 0.0,
            "max_vertical_deviation": None,
            "mean_path_deviation": None,
            "approximately_horizontal": None,
        }
    seed_row = min(damaged, key=lambda row: (row["x"] ** 2 + row["y"] ** 2))
    component = connected_component([row["element"] for row in damaged], adjacency, seed_row["element"])
    component_rows = [row for row in damaged if row["element"] in component]
    ys = [abs(row["y"]) for row in component_rows]
    xs = [row["x"] for row in component_rows]
    extension = max([0.0] + [x for x in xs if x >= 0.0])
    max_dev = max(ys) if ys else None
    mean_dev = sum(ys) / len(ys) if ys else None
    return {
        "damaged_element_count": len(damaged),
        "connected_component_count": len(component_rows),
        "connected": len(component_rows) == len(damaged),
        "crack_initiation_x": seed_row["x"],
        "crack_initiation_y": seed_row["y"],
        "crack_extension": extension,
        "max_vertical_deviation": max_dev,
        "mean_path_deviation": mean_dev,
        "approximately_horizontal": max_dev is not None and max_dev <= 0.05,
    }


def crack_path_diagnostics(contour_dir, inp_path, output_csv):
    nodes, elements = parse_nodes_elements(inp_path)
    centroids, adjacency = centroids_and_adjacency(nodes, elements)
    rows_out = []
    for name in sorted(os.listdir(contour_dir)):
        if not name.startswith("matched_state_") or not name.endswith("_contour_sdv14_sdv15_sdv16.csv"):
            continue
        path = os.path.join(contour_dir, name)
        contour = read_contour_elements(path, centroids)
        metrics = crack_metrics(contour, adjacency)
        first = read_csv_dicts(path)[0]
        metrics.update(
            {
                "source_file": name,
                "step": first["step"],
                "frame": int(first["frame"]),
                "target_abs_u2": float(first["target_abs_u2"]),
                "rp_u2": float(first["rp_u2"]),
                "phase_threshold": D_CRIT,
                "reference_path": "qualitative horizontal ligament y=0",
            }
        )
        rows_out.append(metrics)
    fieldnames = [
        "source_file",
        "step",
        "frame",
        "target_abs_u2",
        "rp_u2",
        "phase_threshold",
        "damaged_element_count",
        "connected_component_count",
        "connected",
        "crack_initiation_x",
        "crack_initiation_y",
        "crack_extension",
        "max_vertical_deviation",
        "mean_path_deviation",
        "approximately_horizontal",
        "reference_path",
    ]
    with open(output_csv, "w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows_out:
            writer.writerow(row)
    return rows_out


def get_rp_u2(frame, rp):
    if "U" not in frame.fieldOutputs:
        return None
    subset = frame.fieldOutputs["U"].getSubset(region=rp)
    if not subset.values:
        return None
    return vector_component(subset.values[0], 1)


def odb_bounds_irreversibility(odb_path):
    open_odb = import_odb_access()
    if open_odb is None:
        return None
    odb = open_odb(path=odb_path, readOnly=True)
    try:
        rp = odb.rootAssembly.nodeSets["RP"]
        stats = {
            "sdv14": {"min": None, "max": None, "below_zero": 0, "above_one": 0, "first_overshoot": None},
            "sdv15": {"min": None, "max": None, "below_zero": 0, "above_one": 0, "first_overshoot": None},
            "sdv16": {"min": None, "max": None},
            "sdv14_minus_sdv15": {"max_abs": 0.0, "location": None},
            "irreversibility": {
                "sdv16_decrease_count": 0,
                "sdv16_worst_drop": 0.0,
                "sdv15_decrease_count": 0,
                "sdv15_worst_drop": 0.0,
                "sdv15_largest_decrease": None,
                "sdv15_decrease_categories": {
                    "same_location_consecutive_frames": 0,
                    "near_step_transition": 0,
                    "smaller_than_odb_precision": 0,
                    "staggered_sync_candidate": 0,
                    "genuine_healing_candidate": 0,
                },
                "tolerance": IRREVERSIBILITY_TOL,
                "odb_precision_tolerance": ODB_PRECISION_TOL,
            },
            "frame_count": 0,
            "value_count_per_sdv": 0,
        }
        previous = {}
        previous_context = {}
        previous_stagger = {}
        overshoot_events = {"SDV14": [], "SDV15": []}
        overshoot_keys = {"SDV14": set(), "SDV15": set()}
        final_above_one_keys = {"SDV14": set(), "SDV15": set()}
        global_frame = 0
        for step_name, step in odb.steps.items():
            for frame_index, frame in enumerate(step.frames):
                stats["frame_count"] += 1
                rp_u2 = get_rp_u2(frame, rp)
                fields = {}
                for sdv in ["SDV14", "SDV15", "SDV16"]:
                    if sdv not in frame.fieldOutputs:
                        continue
                    values = []
                    for index, value in enumerate(frame.fieldOutputs[sdv].values):
                        key = (
                            getattr(value, "elementLabel", None),
                            getattr(value, "integrationPoint", None),
                            index,
                        )
                        values.append((key, scalar_data(value)))
                    fields[sdv] = values
                    stats["value_count_per_sdv"] += len(values)
                    short = sdv.lower()
                    for key, data in values:
                        if stats[short]["min"] is None or data < stats[short]["min"]:
                            stats[short]["min"] = data
                        if stats[short]["max"] is None or data > stats[short]["max"]:
                            stats[short]["max"] = data
                        if sdv in ["SDV14", "SDV15"]:
                            if data < -BOUND_TOL:
                                stats[short]["below_zero"] += 1
                            if data > 1.0 + BOUND_TOL:
                                stats[short]["above_one"] += 1
                                event = {
                                    "step": step_name,
                                    "frame": frame_index,
                                    "global_frame": global_frame,
                                    "step_time": float(frame.frameValue),
                                    "rp_u2": rp_u2,
                                    "element": key[0],
                                    "integration_point": key[1],
                                    "value": data,
                                    "overshoot": data - 1.0,
                                }
                                overshoot_events[sdv].append(event)
                                overshoot_keys[sdv].add(key)
                                if stats[short]["first_overshoot"] is None:
                                    stats[short]["first_overshoot"] = event
                        if sdv in ["SDV15", "SDV16"]:
                            previous_key = (sdv, key)
                            if previous_key in previous:
                                drop = previous[previous_key] - data
                                if drop > IRREVERSIBILITY_TOL:
                                    short_ir = sdv.lower() + "_decrease_count"
                                    short_drop = sdv.lower() + "_worst_drop"
                                    stats["irreversibility"][short_ir] += 1
                                    if drop > stats["irreversibility"][short_drop]:
                                        stats["irreversibility"][short_drop] = drop
                                    if sdv == "SDV15":
                                        stats["irreversibility"]["sdv15_decrease_categories"]["same_location_consecutive_frames"] += 1
                                        prev_ctx = previous_context[previous_key]
                                        near_step = prev_ctx["step"] != step_name
                                        if near_step:
                                            stats["irreversibility"]["sdv15_decrease_categories"]["near_step_transition"] += 1
                                        if drop <= ODB_PRECISION_TOL:
                                            stats["irreversibility"]["sdv15_decrease_categories"]["smaller_than_odb_precision"] += 1
                                        current_stag = None
                                        if "SDV14" in fields:
                                            sdv14_now = dict(fields["SDV14"]).get(key)
                                            if sdv14_now is not None:
                                                current_stag = abs(sdv14_now - data)
                                        previous_stag_value = previous_stagger.get(key)
                                        stagger_candidate = (
                                            (current_stag is not None and current_stag >= drop)
                                            or (previous_stag_value is not None and previous_stag_value >= drop)
                                        )
                                        if stagger_candidate:
                                            stats["irreversibility"]["sdv15_decrease_categories"]["staggered_sync_candidate"] += 1
                                        if (not near_step) and drop > ODB_PRECISION_TOL and not stagger_candidate:
                                            stats["irreversibility"]["sdv15_decrease_categories"]["genuine_healing_candidate"] += 1
                                        event = {
                                            "drop": drop,
                                            "previous_value": previous[previous_key],
                                            "current_value": data,
                                            "previous_step": prev_ctx["step"],
                                            "previous_frame": prev_ctx["frame"],
                                            "previous_global_frame": prev_ctx["global_frame"],
                                            "previous_step_time": prev_ctx["step_time"],
                                            "previous_rp_u2": prev_ctx["rp_u2"],
                                            "step": step_name,
                                            "frame": frame_index,
                                            "global_frame": global_frame,
                                            "step_time": float(frame.frameValue),
                                            "rp_u2": rp_u2,
                                            "element": key[0],
                                            "integration_point": key[1],
                                            "near_step_transition": near_step,
                                            "smaller_than_odb_precision": drop <= ODB_PRECISION_TOL,
                                            "staggered_sync_candidate": stagger_candidate,
                                            "current_abs_sdv14_minus_sdv15": current_stag,
                                            "previous_abs_sdv14_minus_sdv15": previous_stag_value,
                                        }
                                        largest = stats["irreversibility"]["sdv15_largest_decrease"]
                                        if largest is None or drop > largest["drop"]:
                                            stats["irreversibility"]["sdv15_largest_decrease"] = event
                            previous[previous_key] = data
                            previous_context[previous_key] = {
                                "step": step_name,
                                "frame": frame_index,
                                "global_frame": global_frame,
                                "step_time": float(frame.frameValue),
                                "rp_u2": rp_u2,
                            }
                sdv14 = dict(fields.get("SDV14", []))
                sdv15 = dict(fields.get("SDV15", []))
                for key in set(sdv14).intersection(sdv15):
                    diff = sdv14[key] - sdv15[key]
                    previous_stagger[key] = abs(diff)
                    if abs(diff) > stats["sdv14_minus_sdv15"]["max_abs"]:
                        stats["sdv14_minus_sdv15"]["max_abs"] = abs(diff)
                        stats["sdv14_minus_sdv15"]["location"] = {
                            "step": step_name,
                            "frame": frame_index,
                            "step_time": float(frame.frameValue),
                            "rp_u2": rp_u2,
                            "element": key[0],
                            "integration_point": key[1],
                            "signed_difference": diff,
                        }
                final_above_one_keys = {"SDV14": set(), "SDV15": set()}
                for sdv in ["SDV14", "SDV15"]:
                    for key, data in fields.get(sdv, []):
                        if data > 1.0 + BOUND_TOL:
                            final_above_one_keys[sdv].add(key)
                global_frame += 1
        max_u = 0.0
        firsts = []
        for sdv in ["sdv14", "sdv15"]:
            if stats[sdv]["first_overshoot"] is not None:
                firsts.append(stats[sdv]["first_overshoot"]["rp_u2"])
        stats["overshoot_limited_to_final_unstable_stage"] = all(
            value is not None and value >= 0.006 for value in firsts
        ) if firsts else True
        for sdv in ["SDV14", "SDV15"]:
            short = sdv.lower()
            events = overshoot_events[sdv]
            if events:
                max_event = max(events, key=lambda event: event["overshoot"])
                first = min(events, key=lambda event: event["global_frame"])
                last = max(events, key=lambda event: event["global_frame"])
                stats[short]["max_overshoot"] = max_event
                stats[short]["unique_affected_integration_points"] = len(overshoot_keys[sdv])
                stats[short]["overshoot_duration"] = {
                    "first_global_frame": first["global_frame"],
                    "last_global_frame": last["global_frame"],
                    "frame_span": last["global_frame"] - first["global_frame"] + 1,
                    "first_rp_u2": first["rp_u2"],
                    "last_rp_u2": last["rp_u2"],
                }
                stats[short]["affected_points_still_above_one_at_final_frame"] = len(
                    overshoot_keys[sdv].intersection(final_above_one_keys[sdv])
                )
                stats[short]["all_affected_points_remain_above_one_at_final_frame"] = (
                    overshoot_keys[sdv] == final_above_one_keys[sdv]
                )
            else:
                stats[short]["max_overshoot"] = None
                stats[short]["unique_affected_integration_points"] = 0
                stats[short]["overshoot_duration"] = None
                stats[short]["affected_points_still_above_one_at_final_frame"] = 0
                stats[short]["all_affected_points_remain_above_one_at_final_frame"] = True
        return stats
    finally:
        odb.close()


def write_rf_comparison_csv(path, rows):
    fieldnames = ["u2", "simulation_rf2", "reference_rf2", "absolute_error", "relative_error", "status"]
    with open(path, "w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_markdown(path, summary):
    rf = summary["rf_u"]
    b = summary["bounds_irreversibility"]
    lines = [
        "# Molnar Single-Notch Scientific Check",
        "",
        "Date: 2026-07-14",
        "",
        "Gate A3 classification: `%s`" % summary["classification"],
        "",
        "## Reference Status",
        "",
        "- RF-U numeric reference available: `%s`" % rf["comparison"]["reference_available"],
        "- RF-U reference point count: `%s`" % rf["comparison"]["reference_point_count"],
        "- Reason: %s" % rf["comparison"]["reason"],
        "- Crack-path reference: qualitative horizontal ligament `y=0` from Fig. 6 tensile pattern and specimen geometry.",
        "",
        "## Simulation RF-U Metrics",
        "",
        "| Metric | Value |",
        "|---|---:|",
    ]
    for key, value in rf["simulation"].items():
        lines.append("| `%s` | `%s` |" % (key, value))
    lines.extend(
        [
            "",
            "## Bounds and Irreversibility",
            "",
            "| Quantity | Min | Max | Below 0 count | Above 1 count |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for sdv in ["sdv14", "sdv15"]:
        item = b[sdv]
        lines.append(
            "| `%s` | %.6e | %.6e | %s | %s |"
            % (sdv.upper(), item["min"], item["max"], item["below_zero"], item["above_one"])
        )
    lines.append("| `SDV16` | %.6e | %.6e | n/a | n/a |" % (b["sdv16"]["min"], b["sdv16"]["max"]))
    lines.extend(
        [
            "",
            "- Maximum absolute `SDV14 - SDV15`: `%.6e`" % b["sdv14_minus_sdv15"]["max_abs"],
            "- `SDV16` decrease count: `%s`; worst drop `%.6e`"
            % (b["irreversibility"]["sdv16_decrease_count"], b["irreversibility"]["sdv16_worst_drop"]),
            "- `SDV15` decrease count: `%s`; worst drop `%.6e`"
            % (b["irreversibility"]["sdv15_decrease_count"], b["irreversibility"]["sdv15_worst_drop"]),
            "- `SDV15` largest decrease event: `%s`" % b["irreversibility"]["sdv15_largest_decrease"],
            "- `SDV15` decrease categories: `%s`" % b["irreversibility"]["sdv15_decrease_categories"],
            "- `SDV15` unique overshoot integration points: `%s`" % b["sdv15"]["unique_affected_integration_points"],
            "- `SDV15` max overshoot event: `%s`" % b["sdv15"]["max_overshoot"],
            "- `SDV15` overshoot duration: `%s`" % b["sdv15"]["overshoot_duration"],
            "- Overshoot limited to final unstable stage by provisional rule `U2 >= 0.006`: `%s`"
            % b["overshoot_limited_to_final_unstable_stage"],
            "",
            "## Crack Path Diagnostics",
            "",
            "Phase threshold: `d_crit = %.3f`." % summary["crack_path"]["phase_threshold"],
            "",
            "| Target U2 | Damaged elements | Connected | Extension | Max vertical deviation | Mean deviation |",
            "|---:|---:|---|---:|---:|---:|",
        ]
    )
    for row in summary["crack_path"]["rows"]:
        lines.append(
            "| %.6f | %s | `%s` | %s | %s | %s |"
            % (
                row["target_abs_u2"],
                row["damaged_element_count"],
                row["connected"],
                row["crack_extension"],
                row["max_vertical_deviation"],
                row["mean_path_deviation"],
            )
        )
    lines.extend(
        [
            "",
            "## Energy Diagnostics",
            "",
            "- External work from trapezoidal RF-U integration: `%.12e`"
            % summary["energy"]["external_work_trapezoid"],
            "- Global degraded/undamaged elastic energy integration from `SDV12`/`SDV13`: `%s`"
            % summary["energy"]["sdv12_sdv13_global_energy_status"],
            "- Crack-surface functional integration: `%s`"
            % summary["energy"]["crack_surface_functional_status"],
            "",
            "## Tolerance Status",
            "",
            "`configs/validation/stage_a_single_notch_tolerances.json` keeps supervisor-approved tolerances pending. No unconditional scientific pass is allowed from this check.",
        ]
    )
    with open(path, "w") as stream:
        stream.write("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rf-u", default=DEFAULT_RF_U)
    parser.add_argument("--matched", default=DEFAULT_MATCHED)
    parser.add_argument("--rf-reference", default=DEFAULT_RF_REF)
    parser.add_argument("--crack-reference", default=DEFAULT_CRACK_REF)
    parser.add_argument("--tolerances", default=DEFAULT_TOLERANCES)
    parser.add_argument("--odb", default=DEFAULT_ODB)
    parser.add_argument("--inp", default=DEFAULT_INP)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    if not os.path.isdir(args.output_dir):
        os.makedirs(args.output_dir)

    curve_rows = read_csv_dicts(args.rf_u)
    matched_rows = read_csv_dicts(args.matched)
    ref_rows = read_csv_dicts(args.rf_reference)
    simulation_rf, comparison_rf, comparison_rows = rf_u_metrics(curve_rows, ref_rows, matched_rows)
    rf_csv = os.path.join(args.output_dir, "rf_u_curve_comparison.csv")
    write_rf_comparison_csv(rf_csv, comparison_rows)

    crack_csv = os.path.join(args.output_dir, "crack_path_comparison.csv")
    crack_rows = crack_path_diagnostics(EXTRACTED_DIR, args.inp, crack_csv)

    bounds = odb_bounds_irreversibility(args.odb)
    if bounds is None:
        return 2

    energy = {
        "external_work_trapezoid": simulation_rf["area_under_rf_u"],
        "sdv12_sdv13_global_energy_status": "insufficient_in_current_extraction_requires_integration_weights_or_controlled_output_enabled_run",
        "crack_surface_functional_status": "insufficient_current_odb_does_not_provide_a_valid_global_grad_d_integration_contract",
    }
    classification = (
        "reference_data_insufficient"
        if not comparison_rf["reference_available"]
        else "scientific_review_required"
    )
    summary = {
        "classification": classification,
        "rf_u": {"simulation": simulation_rf, "comparison": comparison_rf},
        "bounds_irreversibility": bounds,
        "crack_path": {
            "phase_threshold": D_CRIT,
            "reference_file": args.crack_reference,
            "rows": crack_rows,
        },
        "energy": energy,
        "tolerances_file": args.tolerances,
    }
    json_path = os.path.join(args.output_dir, "single_notch_scientific_check.json")
    md_path = os.path.join(args.output_dir, "SINGLE_NOTCH_SCIENTIFIC_CHECK.md")
    with open(json_path, "w") as stream:
        json.dump(summary, stream, indent=2, sort_keys=True)
        stream.write("\n")
    write_markdown(md_path, summary)
    print("Gate A3 classification: %s" % classification)
    print("Markdown: %s" % md_path)
    print("JSON: %s" % json_path)
    print("RF-U comparison CSV: %s" % rf_csv)
    print("Crack-path comparison CSV: %s" % crack_csv)
    return 0 if classification != "scientific_mismatch" else 1


if __name__ == "__main__":
    raise SystemExit(main())

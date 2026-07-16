#!/usr/bin/env python
"""Detailed no-solution SDV15 event reconstruction for Molnar candidate v2.

Run with Abaqus Python against the retained scratch ODB, read-only:

    abaqus python scripts/postprocessing/extract_molnar_sdv15_detailed_events.py \
      --odb /scratch/.../molnar_paper_matched_single_notch_v2.odb \
      --outdir /scratch/.../sdv15_detailed_review

The script writes lightweight CSV/JSON/Markdown evidence only. It does not
modify the ODB, submit a scheduler job, or run Abaqus/Standard.
"""

from __future__ import print_function

import argparse
import csv
import json
import math
import os
import platform
import subprocess
import sys
import time
from collections import defaultdict, deque


DEFAULT_DECK = os.path.join(
    "models",
    "generated",
    "molnar_gravouil_2017",
    "paper_matched_single_notch_v2",
    "paper_matched_single_notch_v2.inp",
)
DEFAULT_LAYER_MAPPING = os.path.join(
    "models",
    "generated",
    "molnar_gravouil_2017",
    "paper_matched_single_notch_v2",
    "layer_mapping.csv",
)
DEFAULT_OUTDIR = os.path.join(
    "runs",
    "hpc",
    "paper_matched_single_notch_v2",
    "scientific_review",
    "sdv15_detailed_review",
)

N_ELEM_FALLBACK = 33852
WORST_VIS_ELEMENT = 84131
WORST_ODB_IP = 3
WORST_PREV_GLOBAL_FRAME = 189
WORST_CURR_GLOBAL_FRAME = 190
WINDOW_START = 180
WINDOW_END = 200


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


def finite(value):
    try:
        return math.isfinite(value)
    except AttributeError:
        return not (math.isnan(value) or math.isinf(value))


def fmt(value):
    if value is None or value == "":
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return "%.17g" % value
    return str(value)


def write_csv(path, fieldnames, rows):
    with open(path, "w") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(dict((name, fmt(row.get(name, ""))) for name in fieldnames))


def write_json(path, data):
    with open(path, "w") as stream:
        json.dump(data, stream, indent=2, sort_keys=True)
        stream.write("\n")


def read_csv_dicts(path):
    with open(path, "r") as stream:
        return list(csv.DictReader(stream))


def parse_nodes_elements(inp_path, n_elem):
    nodes = {}
    elements = {}
    section = None
    with open(inp_path, "rb") as stream:
        for raw in stream.read().decode("utf-8", "replace").splitlines():
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
                label = int(parts[0])
                if 1 <= label <= n_elem:
                    elements[label] = [int(item) for item in parts[1:5]]
    if not nodes:
        raise RuntimeError("No nodes parsed from %s" % inp_path)
    if len(elements) != n_elem:
        raise RuntimeError(
            "Parsed %d physical elements from %s; expected %d"
            % (len(elements), inp_path, n_elem)
        )
    return nodes, elements


def centroids_and_edges(nodes, elements):
    centroids = {}
    edge_to_elements = defaultdict(list)
    for element, conn in elements.items():
        coords = [nodes[node] for node in conn]
        centroids[element] = (
            sum(coord[0] for coord in coords) / len(coords),
            sum(coord[1] for coord in coords) / len(coords),
        )
        edges = [
            tuple(sorted((conn[0], conn[1]))),
            tuple(sorted((conn[1], conn[2]))),
            tuple(sorted((conn[2], conn[3]))),
            tuple(sorted((conn[3], conn[0]))),
        ]
        for edge in edges:
            edge_to_elements[edge].append(element)
    adjacency = defaultdict(set)
    for labels in edge_to_elements.values():
        if len(labels) < 2:
            continue
        for label in labels:
            for other in labels:
                if other != label:
                    adjacency[label].add(other)
    return centroids, adjacency


def source_ip_from_odb_ip(ip):
    if ip == 3:
        return 4
    if ip == 4:
        return 3
    return ip


def vis_to_physical(label, n_elem):
    return label - 2 * n_elem


def physical_to_vis(label, n_elem):
    return label + 2 * n_elem


def physical_to_u2(label, n_elem):
    return label + n_elem


def distance_to_notch_tip(x, y):
    return math.sqrt(x * x + y * y)


def distance_to_ligament(y):
    return abs(y)


def tolerance_bin(drop, precision_tol):
    if drop <= precision_tol:
        return "le_odb_precision_tol"
    if drop <= 1.0e-5:
        return "gt_precision_to_1e-5"
    if drop <= 1.0e-4:
        return "gt_1e-5_to_1e-4"
    return "gt_1e-4"


def response_region(u2, peak_u2, final_u2):
    if u2 is None:
        return "unknown"
    if u2 < peak_u2 - 1.0e-12:
        return "before_peak"
    if abs(u2 - peak_u2) <= 2.5e-5:
        return "at_peak"
    if u2 < peak_u2 + 0.5 * (final_u2 - peak_u2):
        return "early_post_peak"
    return "late_post_peak"


def preliminary_interpretation(drop, prev_gap, curr_gap, precision_tol):
    if drop <= precision_tol:
        return "retained_precision_effect"
    if max(prev_gap, curr_gap) >= drop:
        return "staggered_sync_effect"
    return "insufficient_mapping_evidence"


def final_category(event, precision_tol):
    if event["decrease_magnitude"] <= precision_tol:
        return "retained_precision_effect"
    if max(event["previous_abs_sdv14_minus_sdv15"], event["current_abs_sdv14_minus_sdv15"]) >= event["decrease_magnitude"]:
        return "staggered_sync_effect"
    return "insufficient_mapping_evidence"


def frame_rp(frame, rp):
    u2 = None
    rf2 = None
    if "U" in frame.fieldOutputs:
        subset = frame.fieldOutputs["U"].getSubset(region=rp)
        if subset.values:
            u2 = vector_component(subset.values[0], 1)
    if "RF" in frame.fieldOutputs:
        subset = frame.fieldOutputs["RF"].getSubset(region=rp)
        if subset.values:
            rf2 = vector_component(subset.values[0], 1)
    return u2, rf2


def field_values(frame, names):
    missing = [name for name in names if name not in frame.fieldOutputs]
    if missing:
        raise RuntimeError("Missing field output(s) %s in frame %s" % (", ".join(missing), frame.description))
    data = {}
    for name in names:
        by_key = {}
        for index, value in enumerate(frame.fieldOutputs[name].values):
            label = getattr(value, "elementLabel", None)
            ip = getattr(value, "integrationPoint", None)
            if label is None or ip is None:
                raise RuntimeError("Field %s contains a value without element/IP" % name)
            by_key[(label, ip, index)] = scalar_data(value)
        data[name] = by_key
    return data


def connected_crack_corridor(final_sdv15, n_elem, centroids, adjacency, threshold):
    means = defaultdict(list)
    for key, value in final_sdv15.items():
        physical = vis_to_physical(key[0], n_elem)
        if physical in centroids:
            means[physical].append(value)
    damaged = set()
    for physical, values in means.items():
        if sum(values) / len(values) >= threshold:
            damaged.add(physical)
    if not damaged:
        return set(), []
    seed = min(damaged, key=lambda label: distance_to_notch_tip(centroids[label][0], centroids[label][1]))
    seen = set([seed])
    queue = deque([seed])
    while queue:
        current = queue.popleft()
        for other in adjacency[current]:
            if other in damaged and other not in seen:
                seen.add(other)
                queue.append(other)
    ordered = sorted(seen, key=lambda label: (centroids[label][0], abs(centroids[label][1]), label))
    return seen, ordered


def percentile(sorted_values, pct):
    if not sorted_values:
        return None
    if len(sorted_values) == 1:
        return sorted_values[0]
    pos = (len(sorted_values) - 1) * pct / 100.0
    low = int(math.floor(pos))
    high = int(math.ceil(pos))
    if low == high:
        return sorted_values[low]
    weight = pos - low
    return sorted_values[low] * (1.0 - weight) + sorted_values[high] * weight


def summarize_distribution(events, corridor):
    drops = sorted(event["decrease_magnitude"] for event in events)
    count = len(drops)
    mean = sum(drops) / count if count else None
    std = None
    if count:
        variance = sum((value - mean) ** 2 for value in drops) / count
        std = math.sqrt(variance)
    bins = [
        ("gt_1e-8_to_1e-7", 1.0e-8, 1.0e-7),
        ("gt_1e-7_to_1e-6", 1.0e-7, 1.0e-6),
        ("gt_1e-6_to_1e-5", 1.0e-6, 1.0e-5),
        ("gt_1e-5_to_1e-4", 1.0e-5, 1.0e-4),
        ("gt_1e-4", 1.0e-4, None),
    ]
    bin_rows = []
    for name, low, high in bins:
        selected = [
            event for event in events
            if event["decrease_magnitude"] > low
            and (high is None or event["decrease_magnitude"] <= high)
        ]
        bin_rows.append({"metric": "magnitude_bin", "name": name, "count": len(selected)})
    by_frame = defaultdict(int)
    by_region = defaultdict(int)
    by_corridor = defaultdict(int)
    by_response = defaultdict(int)
    for event in events:
        by_frame[event["current_global_frame"]] += 1
        by_region[event["spatial_region"]] += 1
        by_response[event["response_region"]] += 1
        by_corridor["inside_connected_crack_corridor" if event["mapped_physical_element"] in corridor else "outside_connected_crack_corridor"] += 1
    rows = [
        {"metric": "count", "name": "events", "count": count},
        {"metric": "count", "name": "affected_locations", "count": len(set((e["odb_element"], e["odb_integration_point"]) for e in events))},
        {"metric": "count", "name": "affected_visual_elements", "count": len(set(e["odb_element"] for e in events))},
        {"metric": "count", "name": "affected_physical_elements", "count": len(set(e["mapped_physical_element"] for e in events))},
    ]
    rows.extend(bin_rows)
    for key in sorted(by_response):
        rows.append({"metric": "response_region", "name": key, "count": by_response[key]})
    for key in sorted(by_region):
        rows.append({"metric": "spatial_region", "name": key, "count": by_region[key]})
    for key in sorted(by_corridor):
        rows.append({"metric": "crack_corridor", "name": key, "count": by_corridor[key]})
    for key in sorted(by_frame):
        rows.append({"metric": "current_global_frame", "name": key, "count": by_frame[key]})
    summary = {
        "event_count": count,
        "affected_locations": len(set((e["odb_element"], e["odb_integration_point"]) for e in events)),
        "affected_visual_elements": len(set(e["odb_element"] for e in events)),
        "affected_physical_elements": len(set(e["mapped_physical_element"] for e in events)),
        "min": drops[0] if drops else None,
        "max": drops[-1] if drops else None,
        "mean": mean,
        "median": percentile(drops, 50.0),
        "std": std,
        "percentiles": dict((str(p), percentile(drops, p)) for p in [1, 5, 10, 25, 50, 75, 90, 95, 99]),
        "non_overlapping_bins": dict((row["name"], row["count"]) for row in bin_rows),
        "response_region_counts": dict(by_response),
        "spatial_region_counts": dict(by_region),
        "crack_corridor_counts": dict(by_corridor),
        "events_per_frame": dict((str(k), by_frame[k]) for k in sorted(by_frame)),
    }
    return summary, rows


def make_mapping_markdown(args, n_elem):
    vis = WORST_VIS_ELEMENT
    physical = vis_to_physical(vis, n_elem)
    u2 = physical_to_u2(physical, n_elem)
    return """# SDV Layer and Update Mapping

Classification: `mapping_for_sdv15_detailed_review`

This file documents the source-defined meaning of the candidate-v2 visualization
fields used by the no-solution SDV15 detailed-event reconstruction. The ODB was
opened read-only; no Abaqus solution job was launched.

| ODB field | Source quantity | Writing layer | Source layer | Update timing | Scientific meaning |
|---|---|---|---|---|---|
| `SDV14` | `PHASE` assigned inside the displacement UEL | U2 displacement UEL writes `USRVAR(physical,14,IP)` | U2 reads U1 phase/history through `USRVAR(physical,15/14,IP)` depending on `STEPITER` | Updated during the displacement layer call; can lag or differ from the U1 phase-field update in the same increment | Phase value used for degraded mechanical response |
| `SDV15` | U1 `SDV(1)` phase variable copied into `USRVAR(physical,15,IP)` | U1 phase-field UEL | U1 phase layer | If `STEPITER=0`, stores `PHASE-DPHASE`; otherwise stores `PHASE` after the phase solve call | Phase-field visualization value, not by itself proof of equivalent converged-state irreversibility |
| `SDV16` | U1 `SDV(2)` history field copied into `USRVAR(physical,16,IP)` | U1 phase-field UEL | U1 phase layer | Updated with the source history maximum logic during phase-field calls | Monotone crack-driving history variable |

Layer offsets for candidate v2:

- Physical/U1 labels: `1..{n_elem}`
- U2 displacement labels: `{u2_start}..{u2_end}`
- CPS4 visualization labels: `{vis_start}..{vis_end}`
- Visualization-to-physical mapping: `physical = visualization - 2*N_ELEM`
- U2 mapping: `u2 = physical + N_ELEM`

Worst recorded SDV15 decrease location:

- ODB visualization element `{vis}`
- mapped physical/U1 element `{physical}`
- mapped U2 displacement element `{u2}`
- ODB integration point `{odb_ip}`
- source storage integration point `{source_ip}` because the UMAT swaps CPS4 points 3 and 4 before reading `USRVAR`

The UMAT visualization layer maps `NOEL - 2*N_ELEM` back to the physical element
and copies `USRVAR(physical,I,NPT)` into `STATEV(I)`. For CPS4 output, source
points 3 and 4 are swapped relative to ODB integration-point numbering; points 1
and 2 remain unchanged. This reconstruction therefore reports both ODB and
source-storage IP identifiers.

Consecutive ODB frames are retained output states, not guaranteed equivalent
phase-update states. Detailed categories therefore remain conservative when the
retained frame data cannot prove whether a decrease is roundoff, staggered sync,
visualization lag, or a true source-level violation.
""".format(
        n_elem=n_elem,
        u2_start=n_elem + 1,
        u2_end=2 * n_elem,
        vis_start=2 * n_elem + 1,
        vis_end=3 * n_elem,
        vis=vis,
        physical=physical,
        u2=u2,
        odb_ip=WORST_ODB_IP,
        source_ip=source_ip_from_odb_ip(WORST_ODB_IP),
    )


def run_extraction(args):
    open_odb = import_odb_access()
    if open_odb is None:
        return 2
    layers = read_csv_dicts(args.layer_mapping)
    n_elem = N_ELEM_FALLBACK
    for row in layers:
        if row.get("layer") == "U1":
            n_elem = int(row["id_end"])
    nodes, elements = parse_nodes_elements(args.deck, n_elem)
    centroids, adjacency = centroids_and_edges(nodes, elements)
    os.makedirs(args.outdir)

    odb_stat = os.stat(args.odb)
    metadata = {
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "python_version": sys.version.replace("\n", " "),
        "platform": platform.platform(),
        "abaqus_python": "odbAccess import succeeded",
        "source_job": args.job_id,
        "repo_revision": args.repo_revision,
        "odb_path": os.path.abspath(args.odb),
        "odb_size_bytes": odb_stat.st_size,
        "odb_mtime_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(odb_stat.st_mtime)),
        "decrease_tolerance": args.decrease_tol,
        "odb_precision_tolerance": args.precision_tol,
        "bound_tolerance": args.bound_tol,
        "physical_element_count": n_elem,
        "note": "No ODB hash was computed to avoid reading the full binary solely for provenance.",
    }

    odb = open_odb(path=args.odb, readOnly=True)
    try:
        if "RP" not in odb.rootAssembly.nodeSets:
            raise RuntimeError("ODB assembly node set RP is missing")
        rp = odb.rootAssembly.nodeSets["RP"]
        previous = {}
        previous_context = {}
        events = []
        overshoots = []
        sdv16_decreases = []
        frames = []
        final_sdv15 = None
        global_frame = 0
        for step_name, step in odb.steps.items():
            if not step.frames:
                raise RuntimeError("Step %s has no frames" % step_name)
            for frame_index, frame in enumerate(step.frames):
                u2, rf2 = frame_rp(frame, rp)
                fields = field_values(frame, ["SDV14", "SDV15", "SDV16"])
                context = {
                    "step": step_name,
                    "frame": frame_index,
                    "global_frame": global_frame,
                    "step_time": float(frame.frameValue),
                    "rp_u2": u2,
                    "rp_rf2": rf2,
                }
                frames.append(context)
                final_sdv15 = fields["SDV15"]
                for key, value in fields["SDV15"].items():
                    label, ip, value_index = key
                    if value > 1.0 + args.bound_tol:
                        physical = vis_to_physical(label, n_elem)
                        x, y = centroids.get(physical, ("", ""))
                        overshoots.append({
                            "step": step_name,
                            "frame": frame_index,
                            "global_frame": global_frame,
                            "step_time": float(frame.frameValue),
                            "rp_u2": u2,
                            "rp_rf2": rf2,
                            "odb_element": label,
                            "odb_integration_point": ip,
                            "source_storage_ip": source_ip_from_odb_ip(ip),
                            "mapped_physical_element": physical,
                            "mapped_u2_element": physical_to_u2(physical, n_elem),
                            "centroid_x": x,
                            "centroid_y": y,
                            "sdv15": value,
                            "overshoot": value - 1.0,
                        })
                    if ("SDV15", key) in previous:
                        prev_value = previous[("SDV15", key)]
                        drop = prev_value - value
                        if drop > args.decrease_tol:
                            prev_ctx = previous_context[("SDV15", key)]
                            prev14 = previous.get(("SDV14", key))
                            curr14 = fields["SDV14"].get(key)
                            prev16 = previous.get(("SDV16", key))
                            curr16 = fields["SDV16"].get(key)
                            if prev14 is None or curr14 is None or prev16 is None or curr16 is None:
                                raise RuntimeError("Missing paired SDV14/SDV16 for SDV15 event key %s" % (key,))
                            physical = vis_to_physical(label, n_elem)
                            if physical not in centroids:
                                raise RuntimeError("Mapped physical element %s missing from deck centroids" % physical)
                            x, y = centroids[physical]
                            prev_gap = abs(prev14 - prev_value)
                            curr_gap = abs(curr14 - value)
                            events.append({
                                "event_index": 0,
                                "previous_step": prev_ctx["step"],
                                "previous_frame": prev_ctx["frame"],
                                "previous_global_frame": prev_ctx["global_frame"],
                                "previous_step_time": prev_ctx["step_time"],
                                "previous_rp_u2": prev_ctx["rp_u2"],
                                "previous_rp_rf2": prev_ctx["rp_rf2"],
                                "current_step": step_name,
                                "current_frame": frame_index,
                                "current_global_frame": global_frame,
                                "current_step_time": float(frame.frameValue),
                                "current_rp_u2": u2,
                                "current_rp_rf2": rf2,
                                "odb_element": label,
                                "odb_integration_point": ip,
                                "odb_value_index": value_index,
                                "source_storage_ip": source_ip_from_odb_ip(ip),
                                "mapped_physical_element": physical,
                                "mapped_u1_element": physical,
                                "mapped_u2_element": physical_to_u2(physical, n_elem),
                                "centroid_x": x,
                                "centroid_y": y,
                                "distance_to_notch_tip": distance_to_notch_tip(x, y),
                                "distance_to_ligament_y0": distance_to_ligament(y),
                                "previous_sdv15": prev_value,
                                "current_sdv15": value,
                                "signed_change": value - prev_value,
                                "decrease_magnitude": drop,
                                "previous_sdv14": prev14,
                                "current_sdv14": curr14,
                                "previous_sdv16": prev16,
                                "current_sdv16": curr16,
                                "previous_abs_sdv14_minus_sdv15": prev_gap,
                                "current_abs_sdv14_minus_sdv15": curr_gap,
                                "sdv16_signed_change": curr16 - prev16,
                                "tolerance_bin": tolerance_bin(drop, args.precision_tol),
                                "spatial_region": "near_ligament" if abs(y) <= args.crack_corridor_half_width else "off_ligament",
                                "response_region": response_region(abs(u2) if u2 is not None else None, args.peak_u2, args.final_u2),
                                "preliminary_interpretation": preliminary_interpretation(drop, prev_gap, curr_gap, args.precision_tol),
                            })
                    previous[("SDV15", key)] = value
                    previous_context[("SDV15", key)] = context
                for key, value in fields["SDV14"].items():
                    previous[("SDV14", key)] = value
                    previous_context[("SDV14", key)] = context
                for key, value in fields["SDV16"].items():
                    if ("SDV16", key) in previous:
                        drop = previous[("SDV16", key)] - value
                        if drop > args.decrease_tol:
                            sdv16_decreases.append((key, drop, previous_context[("SDV16", key)], context))
                    previous[("SDV16", key)] = value
                    previous_context[("SDV16", key)] = context
                global_frame += 1
    finally:
        odb.close()

    if final_sdv15 is None:
        raise RuntimeError("No SDV15 field data were read")
    corridor, crack_order = connected_crack_corridor(final_sdv15, n_elem, centroids, adjacency, args.crack_threshold)
    for event in events:
        event["inside_connected_crack_corridor"] = event["mapped_physical_element"] in corridor
    events.sort(key=lambda row: (-row["decrease_magnitude"], row["odb_element"], row["odb_integration_point"], row["current_global_frame"]))
    for index, event in enumerate(events, start=1):
        event["event_index"] = index

    event_fields = [
        "event_index", "previous_step", "previous_frame", "previous_global_frame", "previous_step_time",
        "previous_rp_u2", "previous_rp_rf2", "current_step", "current_frame", "current_global_frame",
        "current_step_time", "current_rp_u2", "current_rp_rf2", "odb_element", "odb_integration_point",
        "odb_value_index", "source_storage_ip", "mapped_physical_element", "mapped_u1_element", "mapped_u2_element",
        "centroid_x", "centroid_y", "distance_to_notch_tip", "distance_to_ligament_y0", "previous_sdv15",
        "current_sdv15", "signed_change", "decrease_magnitude", "previous_sdv14", "current_sdv14",
        "previous_sdv16", "current_sdv16", "sdv16_signed_change", "previous_abs_sdv14_minus_sdv15",
        "current_abs_sdv14_minus_sdv15", "tolerance_bin", "spatial_region", "response_region",
        "inside_connected_crack_corridor", "preliminary_interpretation",
    ]
    write_csv(os.path.join(args.outdir, "sdv15_decrease_events_full.csv"), event_fields, events)

    distribution, distribution_rows = summarize_distribution(events, corridor)
    distribution["expected_legacy_decrease_count"] = args.expected_decrease_count
    distribution["matches_expected_legacy_count"] = len(events) == args.expected_decrease_count
    distribution["connected_crack_corridor_element_count"] = len(corridor)
    write_json(os.path.join(args.outdir, "sdv15_decrease_distribution.json"), distribution)
    write_csv(os.path.join(args.outdir, "sdv15_decrease_distribution.csv"), ["metric", "name", "count"], distribution_rows)

    over_keys = set((row["odb_element"], row["odb_integration_point"]) for row in overshoots)
    decrease_keys_gt_precision = set(
        (row["odb_element"], row["odb_integration_point"])
        for row in events if row["decrease_magnitude"] > args.precision_tol
    )
    for row in overshoots:
        row["inside_connected_crack_corridor"] = row["mapped_physical_element"] in corridor
        row["overlaps_sdv15_decrease_gt_precision_location"] = (row["odb_element"], row["odb_integration_point"]) in decrease_keys_gt_precision
    overshoots.sort(key=lambda row: (row["global_frame"], row["odb_element"], row["odb_integration_point"]))
    write_csv(
        os.path.join(args.outdir, "sdv15_overshoot_events.csv"),
        [
            "step", "frame", "global_frame", "step_time", "rp_u2", "rp_rf2", "odb_element",
            "odb_integration_point", "source_storage_ip", "mapped_physical_element", "mapped_u2_element",
            "centroid_x", "centroid_y", "sdv15", "overshoot", "inside_connected_crack_corridor",
            "overlaps_sdv15_decrease_gt_precision_location",
        ],
        overshoots,
    )

    eq_rows = []
    category_counts = defaultdict(int)
    for event in events:
        if event["decrease_magnitude"] <= args.precision_tol:
            continue
        category = final_category(event, args.precision_tol)
        category_counts[category] += 1
        eq_rows.append({
            "event_index": event["event_index"],
            "current_global_frame": event["current_global_frame"],
            "odb_element": event["odb_element"],
            "odb_integration_point": event["odb_integration_point"],
            "mapped_physical_element": event["mapped_physical_element"],
            "decrease_magnitude": event["decrease_magnitude"],
            "previous_sdv15": event["previous_sdv15"],
            "current_sdv15": event["current_sdv15"],
            "previous_sdv14": event["previous_sdv14"],
            "current_sdv14": event["current_sdv14"],
            "previous_abs_sdv14_minus_sdv15": event["previous_abs_sdv14_minus_sdv15"],
            "current_abs_sdv14_minus_sdv15": event["current_abs_sdv14_minus_sdv15"],
            "source_defined_equivalent_state_rule": "Consecutive retained ODB frames are not assumed equivalent phase-update states; classify only by precision and SDV14/SDV15 stagger evidence visible in retained fields.",
            "final_category": category,
        })
    write_csv(
        os.path.join(args.outdir, "sdv15_equivalent_state_comparison.csv"),
        [
            "event_index", "current_global_frame", "odb_element", "odb_integration_point",
            "mapped_physical_element", "decrease_magnitude", "previous_sdv15", "current_sdv15",
            "previous_sdv14", "current_sdv14", "previous_abs_sdv14_minus_sdv15",
            "current_abs_sdv14_minus_sdv15", "source_defined_equivalent_state_rule", "final_category",
        ],
        eq_rows,
    )

    sdv16_rows = []
    for event in events:
        if event["decrease_magnitude"] <= args.precision_tol:
            continue
        sdv16_rows.append({
            "event_index": event["event_index"],
            "previous_global_frame": event["previous_global_frame"],
            "current_global_frame": event["current_global_frame"],
            "odb_element": event["odb_element"],
            "odb_integration_point": event["odb_integration_point"],
            "mapped_physical_element": event["mapped_physical_element"],
            "previous_sdv16": event["previous_sdv16"],
            "current_sdv16": event["current_sdv16"],
            "sdv16_signed_change": event["sdv16_signed_change"],
            "sdv16_decrease_gt_tolerance": event["sdv16_signed_change"] < -args.decrease_tol,
        })
    write_csv(
        os.path.join(args.outdir, "sdv16_at_sdv15_event_locations.csv"),
        [
            "event_index", "previous_global_frame", "current_global_frame", "odb_element",
            "odb_integration_point", "mapped_physical_element", "previous_sdv16", "current_sdv16",
            "sdv16_signed_change", "sdv16_decrease_gt_tolerance",
        ],
        sdv16_rows,
    )

    worst_physical = vis_to_physical(WORST_VIS_ELEMENT, n_elem)
    worst_neighbors = sorted(adjacency[worst_physical])
    crack_labels = list(crack_order)
    if worst_physical in crack_labels:
        idx = crack_labels.index(worst_physical)
        crack_context = crack_labels[max(0, idx - 2): idx + 3]
    else:
        crack_context = sorted(crack_labels, key=lambda label: distance_to_notch_tip(centroids[label][0] - centroids[worst_physical][0], centroids[label][1] - centroids[worst_physical][1]))[:5]
    history_physicals = sorted(set([worst_physical] + worst_neighbors + crack_context))
    history_vis = set(physical_to_vis(label, n_elem) for label in history_physicals)

    odb = open_odb(path=args.odb, readOnly=True)
    history_rows = []
    try:
        rp_history = odb.rootAssembly.nodeSets["RP"]
        global_frame = 0
        for step_name, step in odb.steps.items():
            for frame_index, frame in enumerate(step.frames):
                if WINDOW_START <= global_frame <= WINDOW_END:
                    u2, rf2 = frame_rp(frame, rp_history)
                    fields = field_values(frame, ["SDV14", "SDV15", "SDV16"])
                    for key, sdv15 in sorted(fields["SDV15"].items()):
                        label, ip, value_index = key
                        if label not in history_vis:
                            continue
                        physical = vis_to_physical(label, n_elem)
                        x, y = centroids[physical]
                        relation = []
                        if physical == worst_physical:
                            relation.append("worst_element")
                        if physical in worst_neighbors:
                            relation.append("face_neighbor")
                        if physical in crack_context:
                            relation.append("crack_path_context")
                        history_rows.append({
                            "step": step_name,
                            "frame": frame_index,
                            "global_frame": global_frame,
                            "step_time": float(frame.frameValue),
                            "rp_u2": u2,
                            "rp_rf2": rf2,
                            "odb_element": label,
                            "odb_integration_point": ip,
                            "source_storage_ip": source_ip_from_odb_ip(ip),
                            "mapped_physical_element": physical,
                            "centroid_x": x,
                            "centroid_y": y,
                            "relation_to_worst_event": "+".join(relation),
                            "sdv14": fields["SDV14"][key],
                            "sdv15": sdv15,
                            "sdv16": fields["SDV16"][key],
                            "abs_sdv14_minus_sdv15": abs(fields["SDV14"][key] - sdv15),
                        })
                global_frame += 1
    finally:
        odb.close()
    write_csv(
        os.path.join(args.outdir, "sdv15_worst_event_history.csv"),
        [
            "step", "frame", "global_frame", "step_time", "rp_u2", "rp_rf2", "odb_element",
            "odb_integration_point", "source_storage_ip", "mapped_physical_element", "centroid_x",
            "centroid_y", "relation_to_worst_event", "sdv14", "sdv15", "sdv16",
            "abs_sdv14_minus_sdv15",
        ],
        history_rows,
    )

    metadata["frame_count"] = len(frames)
    metadata["sdv15_decrease_event_count"] = len(events)
    metadata["sdv15_gt_precision_event_count"] = len(eq_rows)
    metadata["sdv15_overshoot_event_count"] = len(overshoots)
    metadata["sdv15_overshoot_unique_locations"] = len(over_keys)
    metadata["sdv16_decrease_count_all_locations"] = len(sdv16_decreases)
    metadata["equivalent_state_category_counts_gt_precision"] = dict(category_counts)
    write_json(os.path.join(args.outdir, "extraction_metadata.json"), metadata)

    with open(os.path.join(args.outdir, "SDV_LAYER_AND_UPDATE_MAPPING.md"), "w") as stream:
        stream.write(make_mapping_markdown(args, n_elem))

    worst = events[0] if events else None
    with open(os.path.join(args.outdir, "SDV15_WORST_EVENT_AUDIT.md"), "w") as stream:
        stream.write("# SDV15 Worst Event Audit\n\n")
        stream.write("Classification: `sdv15_worst_event_reconstructed`\n\n")
        if worst:
            stream.write(
                "Worst decrease: `{drop}` at visualization element `{vis}`, IP `{ip}`, "
                "mapped physical element `{phys}`, global frames `{prev}` to `{curr}`.\n\n".format(
                    drop=fmt(worst["decrease_magnitude"]),
                    vis=worst["odb_element"],
                    ip=worst["odb_integration_point"],
                    phys=worst["mapped_physical_element"],
                    prev=worst["previous_global_frame"],
                    curr=worst["current_global_frame"],
                )
            )
            stream.write("- Previous/current SDV15: `{}` -> `{}`\n".format(fmt(worst["previous_sdv15"]), fmt(worst["current_sdv15"])))
            stream.write("- Previous/current SDV14-SDV15 mismatch: `{}` / `{}`\n".format(fmt(worst["previous_abs_sdv14_minus_sdv15"]), fmt(worst["current_abs_sdv14_minus_sdv15"])))
            stream.write("- Previous/current RF2: `{}` / `{}`\n".format(fmt(worst["previous_rp_rf2"]), fmt(worst["current_rp_rf2"])))
            stream.write("- Previous/current U2: `{}` / `{}`\n".format(fmt(worst["previous_rp_u2"]), fmt(worst["current_rp_u2"])))
            stream.write("- Source-storage IP after UMAT swap: `{}`\n".format(worst["source_storage_ip"]))
            stream.write("- Preliminary interpretation: `{}`\n\n".format(worst["preliminary_interpretation"]))
        stream.write("The history CSV covers global frames `{}` through `{}` for the worst physical element, its face-neighbor elements, and local crack-path context elements. Retained ODB frames do not prove equivalent phase-update states, so unresolved non-staggered events remain categorized conservatively.\n".format(WINDOW_START, WINDOW_END))

    with open(os.path.join(args.outdir, "SDV15_OVERSHOOT_AUDIT.md"), "w") as stream:
        stream.write("# SDV15 Overshoot Audit\n\n")
        stream.write("Classification: `sdv15_overshoot_reconstructed`\n\n")
        stream.write("- Overshoot event rows: `{}`\n".format(len(overshoots)))
        stream.write("- Unique overshoot locations: `{}`\n".format(len(over_keys)))
        if overshoots:
            first = overshoots[0]
            max_event = max(overshoots, key=lambda row: row["overshoot"])
            stream.write("- First overshoot: global frame `{}`, U2 `{}`, element `{}`, IP `{}`\n".format(first["global_frame"], fmt(first["rp_u2"]), first["odb_element"], first["odb_integration_point"]))
            stream.write("- Maximum overshoot: `{}` at global frame `{}`, U2 `{}`, element `{}`, IP `{}`\n".format(fmt(max_event["overshoot"]), max_event["global_frame"], fmt(max_event["rp_u2"]), max_event["odb_element"], max_event["odb_integration_point"]))
            stream.write("- Locations overlapping SDV15 decreases greater than ODB precision: `{}`\n".format(len(over_keys.intersection(decrease_keys_gt_precision))))
        stream.write("\nThe preserved source does not clip the phase field before visualization; overshoot is therefore recorded as scientific-review evidence, not as an execution failure.\n")

    incomplete_reasons = []
    if not distribution["matches_expected_legacy_count"]:
        incomplete_reasons.append("event count did not match the prior legacy scan")
    if category_counts.get("insufficient_mapping_evidence", 0):
        incomplete_reasons.append("some decreases greater than ODB precision lack equivalent-update-state proof")
    if len(sdv16_decreases):
        incomplete_reasons.append("SDV16 decreases were detected")
    if incomplete_reasons:
        decision = "sdv15_detailed_review_incomplete"
    else:
        decision = "sdv15_detailed_review_pass"
    with open(os.path.join(args.outdir, "SDV15_DETAILED_EVENT_DECISION.md"), "w") as stream:
        stream.write("# SDV15 Detailed Event Decision\n\n")
        stream.write("Decision: `{}`\n\n".format(decision))
        stream.write("- SDV15 decrease events reconstructed: `{}`\n".format(len(events)))
        stream.write("- Prior legacy count expected: `{}`\n".format(args.expected_decrease_count))
        stream.write("- Count match: `{}`\n".format(distribution["matches_expected_legacy_count"]))
        stream.write("- Events greater than ODB precision: `{}`\n".format(len(eq_rows)))
        stream.write("- Equivalent-state categories: `{}`\n".format(dict(category_counts)))
        stream.write("- SDV16 decrease count at all scanned locations: `{}`\n".format(len(sdv16_decreases)))
        stream.write("- SDV16 decrease flags at SDV15 > precision event locations: `{}`\n".format(sum(1 for row in sdv16_rows if row["sdv16_decrease_gt_tolerance"])))
        if incomplete_reasons:
            stream.write("\nIncomplete basis:\n")
            for reason in incomplete_reasons:
                stream.write("- {}\n".format(reason))
        stream.write("\nThis decision applies only to the detailed SDV15 event reconstruction. It does not promote the overall paper-matched candidate-v2 scientific classification; Gate A3 remains `reference_data_insufficient`.\n")

    print("Wrote SDV15 detailed review to %s" % args.outdir)
    print("SDV15 decrease events: %d" % len(events))
    print("SDV15 > precision events: %d" % len(eq_rows))
    print("SDV16 decreases: %d" % len(sdv16_decreases))
    print("Decision: %s" % decision)
    return 0


def current_revision():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("utf-8", "replace").strip()
    except Exception:
        return "unknown"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--odb", required=True)
    parser.add_argument("--outdir", default=DEFAULT_OUTDIR)
    parser.add_argument("--deck", default=DEFAULT_DECK)
    parser.add_argument("--layer-mapping", default=DEFAULT_LAYER_MAPPING)
    parser.add_argument("--repo-revision", default=current_revision())
    parser.add_argument("--job-id", default="1374864.mmaster02")
    parser.add_argument("--decrease-tol", type=float, default=1.0e-8)
    parser.add_argument("--precision-tol", type=float, default=1.0e-6)
    parser.add_argument("--bound-tol", type=float, default=1.0e-8)
    parser.add_argument("--expected-decrease-count", type=int, default=6113)
    parser.add_argument("--peak-u2", type=float, default=0.00610999995842576)
    parser.add_argument("--final-u2", type=float, default=0.0066999997943639755)
    parser.add_argument("--crack-threshold", type=float, default=0.95)
    parser.add_argument("--crack-corridor-half-width", type=float, default=0.01)
    args = parser.parse_args()

    if os.path.exists(args.outdir):
        raise RuntimeError("Output directory already exists; refusing to overwrite: %s" % args.outdir)
    if not os.path.exists(args.odb):
        raise RuntimeError("ODB not found: %s" % args.odb)
    if not os.path.exists(args.deck):
        raise RuntimeError("Deck not found: %s" % args.deck)
    if not os.path.exists(args.layer_mapping):
        raise RuntimeError("Layer mapping not found: %s" % args.layer_mapping)
    return run_extraction(args)


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python
"""Streaming fixed-key SDV audit for the Stage-F7 H2 ODB (Abaqus Python 2.7)."""
from __future__ import print_function

import csv
import json
import os
import sys


TIERS = (0.0, 1e-8, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3)


def write_json(path, data):
    with open(path, "w") as stream:
        json.dump(data, stream, indent=2, sort_keys=True)
        stream.write("\n")
    with open(path) as stream:
        json.load(stream)


def value_key(value):
    section = getattr(value, "sectionPoint", None)
    section_text = ""
    if section is not None:
        section_text = str(getattr(section, "description", section))
    return "%s|%s|%s|%s|%s" % (
        value.instance.name,
        value.elementLabel,
        getattr(value, "integrationPoint", 0),
        section_text,
        str(value.position),
    )


def scalar(value):
    data = value.data
    if isinstance(data, (tuple, list)):
        return float(data[0])
    return float(data)


def frame_population(frame, field_name):
    field = frame.fieldOutputs[field_name]
    result = {}
    positions = {}
    instances = {}
    for value in field.values:
        key = value_key(value)
        if key in result:
            raise RuntimeError("duplicate material-point key: %s" % key)
        result[key] = scalar(value)
        positions[str(value.position)] = positions.get(str(value.position), 0) + 1
        instances[value.instance.name] = instances.get(value.instance.name, 0) + 1
    return result, positions, instances


def main():
    odb_path = os.environ["F7_SOURCE_ODB"]
    out_dir = os.environ["F7_OUTPUT_DIRECTORY"]
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    from odbAccess import openOdb
    odb = openOdb(path=odb_path, readOnly=True)
    schema = {
        "odb_path": odb_path,
        "odb_precision": str(getattr(odb, "precision", "not_exposed")),
        "steps": [],
        "field_name": "SDV15",
        "history_field_name": "SDV14",
    }
    targeted = []
    frame_rows = []
    threshold_counts = dict((("%.0e" % tier), 0) for tier in TIERS)
    strict_negative_count = 0
    minimum_delta = None
    minimum_record = None
    affected_keys = {}
    affected_elements = {}
    previous = None
    previous_meta = None
    previous_history = None
    history_negative_count = 0
    history_min_delta = None
    total_pairs = 0
    total_frames = 0
    all_positions = {}
    all_instances = {}

    for step_name in odb.steps.keys():
        step = odb.steps[step_name]
        schema["steps"].append({"name": step_name, "frame_count": len(step.frames)})
        for frame_index, frame in enumerate(step.frames):
            if "SDV15" not in frame.fieldOutputs:
                raise RuntimeError("SDV15 missing at %s frame %s" % (step_name, frame_index))
            current, positions, instances = frame_population(frame, "SDV15")
            for key in positions:
                all_positions[key] = all_positions.get(key, 0) + positions[key]
            for key in instances:
                all_instances[key] = all_instances.get(key, 0) + instances[key]
            current_history = None
            if "SDV14" in frame.fieldOutputs:
                current_history, unused_p, unused_i = frame_population(frame, "SDV14")
            current_max_key = max(current, key=current.get)
            current_max = current[current_max_key]
            meta = {
                "step": step_name,
                "frame": frame_index,
                "frame_id": getattr(frame, "frameId", frame_index),
                "time": float(frame.frameValue),
                "maximum": current_max,
                "maximum_key": current_max_key,
            }
            frame_rows.append(meta)
            total_frames += 1
            if previous is not None:
                total_pairs += 1
                shared = set(previous).intersection(current)
                missing = len(set(previous).symmetric_difference(current))
                local_negative = 0
                local_min = None
                local_min_key = None
                local_above_one_only = True
                for key in shared:
                    delta = current[key] - previous[key]
                    if local_min is None or delta < local_min:
                        local_min = delta
                        local_min_key = key
                    if delta < 0.0:
                        strict_negative_count += 1
                        local_negative += 1
                        affected_keys[key] = True
                        parts = key.split("|")
                        if len(parts) > 1:
                            affected_elements[parts[0] + "|" + parts[1]] = True
                        if not (previous[key] > 1.0 and current[key] >= 1.0):
                            local_above_one_only = False
                        for tier in TIERS:
                            if delta < -tier:
                                threshold_counts["%.0e" % tier] += 1
                    if minimum_delta is None or delta < minimum_delta:
                        minimum_delta = delta
                        minimum_record = {
                            "previous": previous_meta,
                            "current": meta,
                            "key": key,
                            "previous_damage": previous[key],
                            "current_damage": current[key],
                            "delta": delta,
                        }
                global_drop = current_max - previous_meta["maximum"]
                if global_drop < 0.0 or local_negative:
                    targeted.append({
                        "previous_step": previous_meta["step"],
                        "previous_frame": previous_meta["frame"],
                        "current_step": meta["step"],
                        "current_frame": meta["frame"],
                        "previous_time": previous_meta["time"],
                        "current_time": meta["time"],
                        "previous_global_max": previous_meta["maximum"],
                        "current_global_max": current_max,
                        "previous_max_key": previous_meta["maximum_key"],
                        "current_max_key": current_max_key,
                        "previous_max_key_current_value": current.get(previous_meta["maximum_key"]),
                        "current_max_key_previous_value": previous.get(current_max_key),
                        "minimum_local_delta": local_min,
                        "minimum_local_delta_key": local_min_key,
                        "negative_local_count": local_negative,
                        "missing_key_count": missing,
                        "all_local_decreases_above_one": local_above_one_only,
                    })
                if previous_history is not None and current_history is not None:
                    for key in set(previous_history).intersection(current_history):
                        delta = current_history[key] - previous_history[key]
                        if delta < 0.0:
                            history_negative_count += 1
                            if history_min_delta is None or delta < history_min_delta:
                                history_min_delta = delta
            previous = current
            previous_meta = meta
            previous_history = current_history

    schema["field_positions"] = all_positions
    schema["instances"] = all_instances
    schema["material_point_key"] = "instance|element_label|integration_point|section_point|position"
    schema["total_frames"] = total_frames
    population = {
        "field": "SDV15",
        "authoritative_selection": "all fixed SDV15 integration-point keys separated by instance, section point, and position",
        "positions": all_positions,
        "instances": all_instances,
        "key_count_last_frame": len(previous or {}),
        "mixed_positions_prohibited": True,
    }
    summary = {
        "frames_audited": total_frames,
        "frame_pairs_audited": total_pairs,
        "strict_negative_count": strict_negative_count,
        "threshold_counts": threshold_counts,
        "global_minimum_delta": minimum_delta,
        "minimum_record": minimum_record,
        "affected_material_point_count": len(affected_keys),
        "affected_element_count": len(affected_elements),
        "targeted_event_pair_count": len(targeted),
        "audit_complete": True,
    }
    history = {
        "field": "SDV14",
        "availability": previous_history is not None,
        "strict_negative_count": history_negative_count,
        "minimum_delta": history_min_delta,
        "source_verification_required": True,
    }

    write_json(os.path.join(out_dir, "H2_ODB_FIELD_SCHEMA.json"), schema)
    write_json(os.path.join(out_dir, "H2_AUTHORITATIVE_POPULATION.json"), population)
    write_json(os.path.join(out_dir, "H2_LOCAL_DELTA_SUMMARY.json"), summary)
    write_json(os.path.join(out_dir, "H2_HISTORY_VARIABLE_AUDIT_RAW.json"), history)
    with open(os.path.join(out_dir, "H2_TARGETED_DECREASE_EVENTS.csv"), "wb") as stream:
        fields = sorted(targeted[0].keys()) if targeted else ["previous_step"]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in targeted:
            writer.writerow(row)
    with open(os.path.join(out_dir, "H2_FRAME_MAX_HISTORY.csv"), "wb") as stream:
        fields = ["step", "frame", "frame_id", "time", "maximum", "maximum_key"]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in frame_rows:
            writer.writerow(row)
    odb.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

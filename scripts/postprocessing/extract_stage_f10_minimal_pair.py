#!/usr/bin/env python
"""Extract Stage F10 fixed-point, response, energy, and convergence evidence."""
from __future__ import print_function
import argparse
import csv
import json
import math
import os
from odbAccess import openOdb


def material_key(value):
    section = getattr(value, "sectionPoint", None)
    return "%s|%s|%s|%s|%s" % (
        value.instance.name, value.elementLabel,
        getattr(value, "integrationPoint", ""),
        getattr(section, "number", "") if section else "",
        getattr(value, "position", ""),
    )


def write_json(path, value):
    with open(path, "w") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--odb", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--role", required=True)
    args = parser.parse_args()
    if not os.path.isdir(args.output_dir):
        os.makedirs(args.output_dir)
    odb = openOdb(args.odb, readOnly=True)
    previous = {}
    fixed_rows = []
    response_rows = []
    energy_rows = []
    deltas = []
    sdv16_deltas = []
    phase_values = []
    frame_count = 0
    for step_name, step in odb.steps.items():
        for frame_index, frame in enumerate(step.frames):
            frame_count += 1
            fields = frame.fieldOutputs
            current = {}
            for name in ("SDV14", "SDV15", "SDV16"):
                if name in fields:
                    for value in fields[name].values:
                        current.setdefault(material_key(value), {})[name] = float(value.data)
            for key, values in current.items():
                old = previous.get(key, {})
                d15 = values.get("SDV15", 0.0) - old.get("SDV15", values.get("SDV15", 0.0))
                d16 = values.get("SDV16", 0.0) - old.get("SDV16", values.get("SDV16", 0.0))
                deltas.append(d15)
                sdv16_deltas.append(d16)
                if "SDV15" in values:
                    phase_values.append(values["SDV15"])
                fixed_rows.append([
                    step_name, frame_index, frame.frameValue, key,
                    values.get("SDV14"), values.get("SDV15"), values.get("SDV16"), d15, d16,
                ])
            previous = current
            top_u = []
            top_rf = []
            if "U" in fields and "RF" in fields:
                for value in fields["U"].values:
                    if value.nodeLabel in (29, 30, 31, 32, 33, 34, 35):
                        top_u.append(float(value.data[0]))
                for value in fields["RF"].values:
                    if value.nodeLabel in (29, 30, 31, 32, 33, 34, 35):
                        top_rf.append(float(value.data[0]))
            response_rows.append([
                step_name, frame_index, frame.frameValue,
                sum(top_u) / len(top_u) if top_u else None,
                sum(top_rf) if top_rf else None,
            ])
            history = {}
            for region in step.historyRegions.values():
                for name in ("ALLIE", "ALLSE", "ALLWK", "ALLVD", "ALLPD"):
                    if name in region.historyOutputs and region.historyOutputs[name].data:
                        history[name] = float(region.historyOutputs[name].data[-1][1])
            energy_rows.append([step_name, frame_index, frame.frameValue] +
                               [history.get(x) for x in ("ALLIE", "ALLSE", "ALLWK", "ALLVD", "ALLPD")])
    odb.close()
    with open(os.path.join(args.output_dir, "fixed_point_history.csv"), "wb") as stream:
        writer = csv.writer(stream)
        writer.writerow(["step", "frame", "time", "key", "sdv14", "sdv15", "sdv16",
                         "delta_sdv15", "delta_sdv16"])
        writer.writerows(fixed_rows)
    with open(os.path.join(args.output_dir, "rf_u_history.csv"), "wb") as stream:
        writer = csv.writer(stream)
        writer.writerow(["step", "frame", "time", "top_u1", "top_rf1"])
        writer.writerows(response_rows)
    with open(os.path.join(args.output_dir, "energy_history.csv"), "wb") as stream:
        writer = csv.writer(stream)
        writer.writerow(["step", "frame", "time", "ALLIE", "ALLSE", "ALLWK", "ALLVD", "ALLPD"])
        writer.writerows(energy_rows)
    thresholds = [0.0, -1e-8, -1e-7, -1e-6, -1e-5, -1e-4, -1e-3]
    summary = {
        "role": args.role,
        "frames": frame_count,
        "phase_delta_counts": {str(x): sum(1 for value in deltas if value < x) for x in thresholds},
        "minimum_delta_sdv15": min(deltas) if deltas else None,
        "minimum_delta_sdv16": min(sdv16_deltas) if sdv16_deltas else None,
        "phase_minimum": min(phase_values) if phase_values else None,
        "phase_maximum": max(phase_values) if phase_values else None,
        "finite": all(not math.isnan(x) and not math.isinf(x)
                      for x in phase_values + deltas + sdv16_deltas),
        "solver_execution_count": 1,
    }
    write_json(os.path.join(args.output_dir, "SUMMARY.json"), summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

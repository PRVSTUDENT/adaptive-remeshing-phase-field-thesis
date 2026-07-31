#!/usr/bin/env python
"""Abaqus-Python-2.7 extraction for the paired Stage-F8 patch jobs."""
from __future__ import print_function
import argparse
import csv
import json
import os
from odbAccess import openOdb


def key(value):
    sp = getattr(value, "sectionPoint", None)
    return "%s|%s|%s|%s" % (
        value.instance.name, value.elementLabel,
        getattr(value, "integrationPoint", ""),
        getattr(sp, "number", "") if sp else "",
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--odb", required=True)
    p.add_argument("--output-dir", required=True)
    args = p.parse_args()
    if not os.path.isdir(args.output_dir):
        os.makedirs(args.output_dir)
    odb = openOdb(args.odb, readOnly=True)
    previous = {}
    rows = []
    strict15 = strict16 = 0
    min15 = min16 = 0.0
    frame_count = 0
    for step_name, step in odb.steps.items():
        for frame_index, frame in enumerate(step.frames):
            frame_count += 1
            fields = frame.fieldOutputs
            current = {}
            for name in ("SDV14", "SDV15", "SDV16"):
                if name not in fields:
                    continue
                for value in fields[name].values:
                    current.setdefault(key(value), {})[name] = float(value.data)
            for material_key, vals in current.items():
                old = previous.get(material_key, {})
                d15 = vals.get("SDV15", 0.0) - old.get("SDV15", vals.get("SDV15", 0.0))
                d16 = vals.get("SDV16", 0.0) - old.get("SDV16", vals.get("SDV16", 0.0))
                if d15 < 0.0:
                    strict15 += 1
                    min15 = min(min15, d15)
                if d16 < 0.0:
                    strict16 += 1
                    min16 = min(min16, d16)
                rows.append([step_name, frame_index, frame.frameValue, material_key,
                             vals.get("SDV14"), vals.get("SDV15"), vals.get("SDV16"),
                             d15, d16])
            previous = current
    odb.close()
    with open(os.path.join(args.output_dir, "fixed_point_history.csv"), "wb") as stream:
        writer = csv.writer(stream)
        writer.writerow(["step", "frame", "time", "key", "sdv14", "sdv15", "sdv16",
                         "delta_sdv15", "delta_sdv16"])
        writer.writerows(rows)
    summary = {
        "frames": frame_count,
        "strict_negative_sdv15": strict15,
        "minimum_delta_sdv15": min15,
        "strict_negative_sdv16": strict16,
        "minimum_delta_sdv16": min16,
        "solver_execution_count": 1,
    }
    with open(os.path.join(args.output_dir, "SUMMARY.json"), "w") as stream:
        json.dump(summary, stream, indent=2, sort_keys=True)
        stream.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


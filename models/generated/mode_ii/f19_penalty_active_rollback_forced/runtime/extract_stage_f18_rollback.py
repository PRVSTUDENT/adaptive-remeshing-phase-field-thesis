#!/usr/bin/env python
"""Python-2.7-compatible F11 ODB extraction and diagnostic-energy integration."""
from __future__ import print_function
import argparse
import csv
import json
import math
import os
from odbAccess import openOdb

IP_VOLUME = 0.005 * 0.005 / 4.0
THRESHOLDS = [0.0, -1e-8, -1e-7, -1e-6, -1e-5, -1e-4, -1e-3]


def finite(value):
    return not math.isnan(value) and not math.isinf(value)


def key(value):
    section = getattr(value, "sectionPoint", None)
    return "%s|%s|%s|%s|%s" % (
        value.instance.name, value.elementLabel,
        getattr(value, "integrationPoint", ""),
        getattr(section, "number", "") if section else "",
        getattr(value, "position", ""))


def write_json(path, data):
    with open(path, "w") as stream:
        json.dump(data, stream, indent=2, sort_keys=True)
        stream.write("\n")
    with open(path) as stream:
        json.load(stream)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--odb", required=True)
    p.add_argument("--output-dir", required=True)
    p.add_argument("--role", required=True)
    a = p.parse_args()
    if not os.path.isdir(a.output_dir):
        os.makedirs(a.output_dir)
    odb = openOdb(a.odb, readOnly=True)
    previous = {}
    fixed_rows = []
    frame_rows = []
    response_rows = []
    deltas = []
    d16s = []
    phases = []
    prior = None
    work = 0.0
    max_imbalance = 0.0
    previous_total = None
    previous_work = 0.0
    for step_name, step in odb.steps.items():
        for frame_index, frame in enumerate(step.frames):
            fields = frame.fieldOutputs
            values = {}
            for number in range(12, 29):
                name = "SDV%d" % number
                if name in fields:
                    for value in fields[name].values:
                        values.setdefault(key(value), {})[number] = float(value.data)
            current = {}
            active_count = 0
            minimum_gap = None
            maximum_penalty_density = 0.0
            sums = dict(elastic=0.0, penalty=0.0, crack_local=0.0,
                        crack_gradient=0.0, history=0.0,
                        penalty_residual=0.0, penalty_tangent=0.0)
            for point, data in values.items():
                phase = data.get(15, data.get(19, 0.0))
                history = data.get(16, 0.0)
                current[point] = (phase, history)
                old = previous.get(point, (phase, history))
                d15 = phase - old[0]
                d16 = history - old[1]
                deltas.append(d15)
                d16s.append(d16)
                phases.append(phase)
                gap = data.get(21, 0.0)
                active = data.get(22, 0.0)
                active_count += 1 if active > 0.5 else 0
                minimum_gap = gap if minimum_gap is None else min(minimum_gap, gap)
                maximum_penalty_density = max(maximum_penalty_density, data.get(23, 0.0))
                sums["elastic"] += data.get(12, 0.0) * IP_VOLUME
                sums["penalty"] += data.get(23, 0.0) * IP_VOLUME
                sums["penalty_residual"] += abs(data.get(24, 0.0)) * IP_VOLUME
                sums["penalty_tangent"] += abs(data.get(25, 0.0)) * IP_VOLUME
                sums["crack_local"] += data.get(26, 0.0) * IP_VOLUME
                sums["crack_gradient"] += data.get(27, 0.0) * IP_VOLUME
                sums["history"] += data.get(28, 0.0) * IP_VOLUME
                fixed_rows.append([step_name, frame_index, frame.frameValue, point,
                                   phase, history, d15, d16, data.get(20),
                                   gap, active, data.get(23)])
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
            u = sum(top_u) / len(top_u) if top_u else 0.0
            rf = sum(top_rf) if top_rf else 0.0
            if prior is not None:
                work += 0.5 * (prior[1] + rf) * (u - prior[0])
            prior = (u, rf)
            total = sums["elastic"] + sums["crack_local"] + sums["crack_gradient"] + sums["penalty"]
            imbalance = 0.0 if previous_total is None else (
                (total - previous_total) - (work - previous_work))
            max_imbalance = max(max_imbalance, imbalance)
            previous_total = total
            previous_work = work
            response_rows.append([step_name, frame_index, frame.frameValue, u, rf, work])
            frame_rows.append([step_name, frame_index, frame.frameValue, active_count,
                               minimum_gap, maximum_penalty_density, sums["penalty"],
                               sums["penalty_residual"], sums["penalty_tangent"],
                               sums["elastic"], sums["crack_local"],
                               sums["crack_gradient"], sums["history"], total, imbalance])
    odb.close()
    with open(os.path.join(a.output_dir, "fixed_point_history.csv"), "wb") as stream:
        w = csv.writer(stream)
        w.writerow(["step", "frame", "time", "key", "sdv15", "sdv16",
                    "delta_sdv15", "delta_sdv16", "prior_phase", "phase_gap",
                    "penalty_active", "penalty_energy_density"])
        w.writerows(fixed_rows)
    with open(os.path.join(a.output_dir, "rf_u_work_history.csv"), "wb") as stream:
        w = csv.writer(stream)
        w.writerow(["step", "frame", "time", "top_u1", "top_rf1", "external_work"])
        w.writerows(response_rows)
    with open(os.path.join(a.output_dir, "diagnostic_energy_history.csv"), "wb") as stream:
        w = csv.writer(stream)
        w.writerow(["step", "frame", "time", "penalty_active_count", "minimum_gap",
                    "maximum_penalty_energy_density", "penalty_energy",
                    "penalty_residual_magnitude", "penalty_tangent_magnitude",
                    "elastic_energy", "local_crack_energy", "gradient_crack_energy",
                    "history_driven_term", "total_diagnostic_energy",
                    "incremental_diagnostic_imbalance"])
        w.writerows(frame_rows)
    summary = {
        "role": a.role,
        "frames": len(frame_rows),
        "minimum_delta_sdv15": min(deltas) if deltas else None,
        "minimum_delta_sdv16": min(d16s) if d16s else None,
        "phase_minimum": min(phases) if phases else None,
        "phase_maximum": max(phases) if phases else None,
        "phase_delta_counts": dict((str(t), sum(1 for x in deltas if x < t))
                                   for t in THRESHOLDS),
        "maximum_penalty_active_count": max(row[3] for row in frame_rows),
        "maximum_positive_incremental_diagnostic_imbalance": max_imbalance,
        "finite": all(finite(x) for x in deltas + d16s + phases),
        "solver_execution_count": 1,
    }
    write_json(os.path.join(a.output_dir, "SUMMARY.json"), summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

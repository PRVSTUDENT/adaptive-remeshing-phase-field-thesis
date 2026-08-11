#!/usr/bin/env python
"""Extract detailed H2 endpoint SDV and matched crack-state evidence (Abaqus Python 2/3)."""
from __future__ import print_function

import argparse
import csv
import json
import os


def scalar(data):
    try:
        return float(data)
    except Exception:
        return float(data[0])


def rp_u1(frame, rp):
    vals = frame.fieldOutputs["U"].getSubset(region=rp).values
    return float(vals[0].data[0])


def keyed(frame, name):
    out = {}
    if name not in frame.fieldOutputs:
        return out
    for value in frame.fieldOutputs[name].values:
        key = (str(value.instance.name), int(value.elementLabel), int(getattr(value, "integrationPoint", 0)))
        out[key] = scalar(value.data)
    return out


def centroid(instance, element_label):
    element = instance.getElementFromLabel(element_label)
    coords = [instance.getNodeFromLabel(label).coordinates for label in element.connectivity]
    return (sum(p[0] for p in coords) / len(coords), sum(p[1] for p in coords) / len(coords))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--odb", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--targets", default="0.00925,0.009632,0.0097625")
    args = parser.parse_args()
    if not os.path.isdir(args.out_dir):
        os.makedirs(args.out_dir)

    from odbAccess import openOdb
    odb = openOdb(path=args.odb, readOnly=True)
    rp = odb.rootAssembly.nodeSets.get("RP")
    if rp is None:
        for instance in odb.rootAssembly.instances.values():
            if "RP" in instance.nodeSets:
                rp = instance.nodeSets["RP"]
                break
    if rp is None:
        raise KeyError("RP node set not found")
    frames = []
    for step_name in sorted(odb.steps.keys()):
        for frame in odb.steps[step_name].frames:
            frames.append((step_name, frame, rp_u1(frame, rp)))

    targets = [float(item) for item in args.targets.split(",")]
    selected = []
    for target in targets:
        selected.append((target, min(frames, key=lambda item: abs(item[2] - target))))

    sdv15_negative = 0
    sdv16_negative = 0
    worst_sdv15 = 0.0
    worst_sdv16 = 0.0
    global_phase_min = None
    global_phase_max = None
    global_sdv16_max = None
    global_max_abs_14_15 = 0.0
    sum_abs_14_15 = 0.0
    count_abs_14_15 = 0
    previous15 = {}
    previous16 = {}
    frame_rows = []

    for step_name, frame, u1 in frames:
        values14 = keyed(frame, "SDV14")
        values15 = keyed(frame, "SDV15")
        values16 = keyed(frame, "SDV16")
        vals15 = list(values15.values())
        vals16 = list(values16.values())
        phase_min = min(vals15) if vals15 else None
        phase_max = max(vals15) if vals15 else None
        hist_max = max(vals16) if vals16 else None
        if phase_min is not None:
            global_phase_min = phase_min if global_phase_min is None else min(global_phase_min, phase_min)
            global_phase_max = phase_max if global_phase_max is None else max(global_phase_max, phase_max)
        if hist_max is not None:
            global_sdv16_max = hist_max if global_sdv16_max is None else max(global_sdv16_max, hist_max)
        for key, value in values15.items():
            if key in previous15:
                delta = value - previous15[key]
                if delta < 0.0:
                    sdv15_negative += 1
                    worst_sdv15 = min(worst_sdv15, delta)
        for key, value in values16.items():
            if key in previous16:
                delta = value - previous16[key]
                if delta < 0.0:
                    sdv16_negative += 1
                    worst_sdv16 = min(worst_sdv16, delta)
        for key in set(values14).intersection(values15):
            diff = abs(values14[key] - values15[key])
            global_max_abs_14_15 = max(global_max_abs_14_15, diff)
            sum_abs_14_15 += diff
            count_abs_14_15 += 1
        previous15 = values15
        previous16 = values16
        frame_rows.append({"step": step_name, "frame": frame.frameId, "u1": u1,
                           "phase_min": phase_min, "phase_max": phase_max, "sdv16_max": hist_max})

    with open(os.path.join(args.out_dir, "endpoint_frame_metrics.csv"), "w") as handle:
        writer = csv.DictWriter(handle, fieldnames=["step", "frame", "u1", "phase_min", "phase_max", "sdv16_max"])
        writer.writeheader(); writer.writerows(frame_rows)

    matched = []
    for target, (step_name, frame, u1) in selected:
        values14 = keyed(frame, "SDV14")
        values15 = keyed(frame, "SDV15")
        values16 = keyed(frame, "SDV16")
        csv_name = "matched_state_%s.csv" % str(target).replace(".", "p")
        rows = []
        centroid_cache = {}
        for key in sorted(values15):
            instance_name, element_label, ip = key
            cache_key = (instance_name, element_label)
            if cache_key not in centroid_cache:
                centroid_cache[cache_key] = centroid(odb.rootAssembly.instances[instance_name], element_label)
            x, y = centroid_cache[cache_key]
            rows.append({"instance": instance_name, "element_label": element_label, "integration_point": ip,
                         "x": x, "y": y, "SDV14": values14.get(key), "SDV15": values15[key],
                         "SDV16": values16.get(key), "crack_flag": 1 if values15[key] >= 0.5 else 0})
        with open(os.path.join(args.out_dir, csv_name), "w") as handle:
            writer = csv.DictWriter(handle, fieldnames=["instance", "element_label", "integration_point", "x", "y", "SDV14", "SDV15", "SDV16", "crack_flag"])
            writer.writeheader(); writer.writerows(rows)
        matched.append({"target_u1": target, "actual_u1": u1, "step": step_name,
                        "frame": frame.frameId, "csv": csv_name,
                        "crack_point_count": sum(row["crack_flag"] for row in rows)})

    summary = {
        "odb": args.odb,
        "frame_count": len(frames),
        "final_u1": frames[-1][2],
        "phase_min_global": global_phase_min,
        "phase_max_global": global_phase_max,
        "phase_overshoot": max(0.0, (global_phase_max or 0.0) - 1.0),
        "sdv16_max_global": global_sdv16_max,
        "sdv16_negative_transitions": sdv16_negative,
        "worst_sdv16_decrease": worst_sdv16,
        "sdv15_negative_transitions": sdv15_negative,
        "worst_sdv15_decrease": worst_sdv15,
        "max_abs_sdv14_minus_sdv15": global_max_abs_14_15,
        "mean_abs_sdv14_minus_sdv15": sum_abs_14_15 / count_abs_14_15 if count_abs_14_15 else None,
        "matched_states": matched,
        "fracture_energy_status": "unavailable_no_direct_phase_field_fracture_energy_history",
    }
    with open(os.path.join(args.out_dir, "H2_ENDPOINT_DETAILED_SUMMARY.json"), "w") as handle:
        handle.write(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True))
    odb.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

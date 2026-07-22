#!/usr/bin/env python
"""Extract the D3 early pre-peak checkpoint from an existing H0 ODB.

Run with Abaqus Python. This is ODB post-processing only; it must not launch an
Abaqus/Standard solve or compile a UEL.
"""

from __future__ import print_function

import argparse
import csv
import json
import math
import os


TARGET_U2 = 0.003
PHYSICAL_ELEMENTS = 3930
UMAT_OFFSET = 2 * PHYSICAL_ELEMENTS


def odb_data(value):
    try:
        return value.dataDouble
    except Exception:
        return value.data


def scalar(value):
    data = odb_data(value)
    try:
        return float(data)
    except TypeError:
        return float(data[0])


def ensure_dir(path):
    if not os.path.isdir(path):
        os.makedirs(path)


def write_csv(path, fields, rows):
    handle = open(path, "w")
    try:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    finally:
        handle.close()


def finite(value):
    try:
        return math.isfinite(float(value))
    except Exception:
        return False


def node_set(odb, name):
    try:
        if name in odb.rootAssembly.nodeSets:
            return odb.rootAssembly.nodeSets[name]
    except Exception:
        pass
    return None


def element_set(odb, name):
    try:
        if name in odb.rootAssembly.elementSets:
            return odb.rootAssembly.elementSets[name]
    except Exception:
        pass
    return None


def rp_u_rf(odb, frame):
    rp = node_set(odb, "RP")
    u2 = None
    rf2 = None
    if rp is not None and "U" in frame.fieldOutputs:
        try:
            values = frame.fieldOutputs["U"].getSubset(region=rp).values
            if values:
                u2 = float(odb_data(values[0])[1])
        except Exception:
            pass
    if rp is not None and "RF" in frame.fieldOutputs:
        try:
            values = frame.fieldOutputs["RF"].getSubset(region=rp).values
            if values:
                rf2 = float(odb_data(values[0])[1])
        except Exception:
            pass
    if rf2 is None:
        rf2 = 0.0
    return u2, rf2


def history_value(step, name, frame):
    best = None
    best_dist = None
    target_time = float(frame.frameValue)
    for region in step.historyRegions.values():
        outputs = region.historyOutputs
        if name not in outputs:
            continue
        for time_value in outputs[name].data:
            dist = abs(float(time_value[0]) - target_time)
            if best is None or dist < best_dist:
                best = float(time_value[1])
                best_dist = dist
    return None if best is None else best


def instance_nodes_by_label(odb):
    nodes = {}
    for instance in odb.rootAssembly.instances.values():
        for node in instance.nodes:
            nodes[int(node.label)] = tuple(float(x) for x in node.coordinates[:2])
    return nodes


def centroid_by_element_label(odb):
    nodes = instance_nodes_by_label(odb)
    out = {}
    for instance in odb.rootAssembly.instances.values():
        for elem in instance.elements:
            coords = [nodes[int(n)] for n in elem.connectivity if int(n) in nodes]
            if not coords:
                continue
            x = sum(c[0] for c in coords) / float(len(coords))
            y = sum(c[1] for c in coords) / float(len(coords))
            out[int(elem.label)] = (x, y)
    return out


def value_component(frame, name, label, ip):
    if name not in frame.fieldOutputs:
        return ""
    for value in frame.fieldOutputs[name].values:
        if int(value.elementLabel) == label and int(value.integrationPoint) == ip:
            data = odb_data(value)
            try:
                return float(data)
            except TypeError:
                return ";".join(str(float(x)) for x in data)
    return ""


def extract_state(odb, frame, out_dir):
    centroids = centroid_by_element_label(odb)
    coord_values = {}
    if "COORD" in frame.fieldOutputs:
        for value in frame.fieldOutputs["COORD"].values:
            label = int(value.elementLabel)
            ip = int(value.integrationPoint)
            data = odb_data(value)
            if len(data) >= 2:
                coord_values[(label, ip)] = (float(data[0]), float(data[1]))

    rows = []
    ip_h_rows = []
    for value in frame.fieldOutputs["SDV15"].values:
        umat_label = int(value.elementLabel)
        physical = umat_label - UMAT_OFFSET
        ip = int(value.integrationPoint)
        if physical < 1 or physical > PHYSICAL_ELEMENTS:
            continue
        d_value = scalar(value)
        h_value = value_component(frame, "SDV16", umat_label, ip)
        x, y = coord_values.get((umat_label, ip), centroids.get(umat_label, ("", "")))
        row = {
            "element": physical,
            "umat_element": umat_label,
            "integration_point": ip,
            "x": x,
            "y": y,
            "SDV15_d": d_value,
            "SDV16_H": h_value,
            "S": value_component(frame, "S", umat_label, ip),
            "E": value_component(frame, "E", umat_label, ip),
            "LE": value_component(frame, "LE", umat_label, ip),
        }
        rows.append(row)
        ip_h_rows.append(
            {
                "element": physical,
                "integration_point": ip,
                "x": x,
                "y": y,
                "H": h_value,
            }
        )
    rows.sort(key=lambda r: (int(r["element"]), int(r["integration_point"])))
    ip_h_rows.sort(key=lambda r: (int(r["element"]), int(r["integration_point"])))
    write_csv(
        os.path.join(out_dir, "D3_CHECKPOINT_STATE.csv"),
        ["element", "umat_element", "integration_point", "x", "y", "SDV15_d", "SDV16_H", "S", "E", "LE"],
        rows,
    )
    write_csv(os.path.join(out_dir, "D3_CHECKPOINT_IP_H.csv"), ["element", "integration_point", "x", "y", "H"], ip_h_rows)
    return rows


def extract_nodal_d(odb, frame, out_dir):
    rows = []
    if "U" not in frame.fieldOutputs:
        write_csv(os.path.join(out_dir, "D3_CHECKPOINT_NODAL_D.csv"), ["node", "x", "y", "phase_d", "source"], rows)
        return rows
    nodes = instance_nodes_by_label(odb)
    for value in frame.fieldOutputs["U"].values:
        label = int(value.nodeLabel)
        data = odb_data(value)
        phase = ""
        if len(data) == 1:
            phase = float(data[0])
        elif len(data) >= 3:
            phase = float(data[2])
        elif len(data) >= 1 and label <= 3999:
            phase = float(data[0])
        if phase == "":
            continue
        x, y = nodes.get(label, ("", ""))
        rows.append({"node": label, "x": x, "y": y, "phase_d": phase, "source": "U"})
    rows.sort(key=lambda r: int(r["node"]))
    write_csv(os.path.join(out_dir, "D3_CHECKPOINT_NODAL_D.csv"), ["node", "x", "y", "phase_d", "source"], rows)
    return rows


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--odb", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--target-u2", type=float, default=TARGET_U2)
    parser.add_argument("--source-job-id", default="1376154.mmaster02")
    parser.add_argument("--source-peak-rf2", type=float, default=0.7276078462600708)
    parser.add_argument("--source-peak-u2", type=float, default=0.006099999882280827)
    args = parser.parse_args(argv)

    from odbAccess import openOdb

    ensure_dir(args.out_dir)
    odb = openOdb(path=args.odb, readOnly=True)
    candidates = []
    total_time_offset = 0.0
    closest = None
    peak_rf2 = None
    peak_u2 = None
    available_sdvs = set()
    step_periods = []

    for step_name, step in odb.steps.items():
        step_max_time = 0.0
        for frame_index, frame in enumerate(step.frames):
            step_max_time = max(step_max_time, float(frame.frameValue))
            for key in frame.fieldOutputs.keys():
                if str(key).startswith("SDV"):
                    available_sdvs.add(str(key))
            u2, rf2 = rp_u_rf(odb, frame)
            if u2 is None:
                continue
            rec = {
                "step": str(step_name),
                "frame_index": int(frame_index),
                "frame_id": int(frame.frameId),
                "increment_number": int(frame.incrementNumber),
                "step_time": float(frame.frameValue),
                "total_time": total_time_offset + float(frame.frameValue),
                "U2": u2,
                "RF2": rf2,
                "distance_to_target": abs(float(u2) - args.target_u2),
                "pre_peak": float(u2) < args.source_peak_u2,
            }
            candidates.append(rec)
            if peak_rf2 is None or rf2 > peak_rf2:
                peak_rf2 = rf2
                peak_u2 = u2
            if closest is None or rec["distance_to_target"] < closest["distance_to_target"]:
                closest = rec
        step_periods.append({"step": str(step_name), "period": step_max_time})
        total_time_offset += step_max_time

    if closest is None:
        odb.close()
        raise RuntimeError("no RF/U frame candidates found")
    if "SDV15" not in available_sdvs or "SDV16" not in available_sdvs:
        odb.close()
        raise RuntimeError("required SDV15/SDV16 outputs are not available")

    selected_frame = odb.steps[closest["step"]].frames[closest["frame_index"]]
    state_rows = extract_state(odb, selected_frame, args.out_dir)
    nodal_rows = extract_nodal_d(odb, selected_frame, args.out_dir)
    allie = history_value(odb.steps[closest["step"]], "ALLIE", selected_frame)
    allse = history_value(odb.steps[closest["step"]], "ALLSE", selected_frame)
    allwk = history_value(odb.steps[closest["step"]], "ALLWK", selected_frame)
    odb.close()

    write_csv(
        os.path.join(args.out_dir, "D3_CHECKPOINT_FRAME_CANDIDATES.csv"),
        ["step", "frame_index", "frame_id", "increment_number", "step_time", "total_time", "U2", "RF2", "distance_to_target", "pre_peak"],
        candidates,
    )
    write_csv(os.path.join(args.out_dir, "D3_CHECKPOINT_RF_U.csv"), ["step", "frame_index", "frame_id", "increment_number", "step_time", "total_time", "U2", "RF2"], candidates)

    d_values = [float(r["SDV15_d"]) for r in state_rows if finite(r["SDV15_d"])]
    h_values = [float(r["SDV16_H"]) for r in state_rows if finite(r["SDV16_H"])]
    selection = {
        "classification": "stage_d3a_checkpoint_extracted",
        "source_job_id": args.source_job_id,
        "odb": args.odb,
        "target_U2": args.target_u2,
        "actual_U2": closest["U2"],
        "distance_to_target": closest["distance_to_target"],
        "step": closest["step"],
        "frame_index": closest["frame_index"],
        "frame_id": closest["frame_id"],
        "increment_number": closest["increment_number"],
        "step_time": closest["step_time"],
        "total_time": closest["total_time"],
        "checkpoint_RF2": closest["RF2"],
        "source_peak_RF2": args.source_peak_rf2,
        "source_peak_U2": args.source_peak_u2,
        "checkpoint_RF2_over_H0_peak_RF2": None if args.source_peak_rf2 == 0 else closest["RF2"] / args.source_peak_rf2,
        "pre_peak": closest["U2"] < args.source_peak_u2 and closest["RF2"] < args.source_peak_rf2,
        "available_sdvs": sorted(available_sdvs),
        "physical_element_count": PHYSICAL_ELEMENTS,
        "state_rows": len(state_rows),
        "nodal_d_rows": len(nodal_rows),
        "max_d": max(d_values) if d_values else None,
        "ip_count_d_ge_0p1": sum(1 for v in d_values if v >= 0.1),
        "ip_count_d_ge_0p5": sum(1 for v in d_values if v >= 0.5),
        "max_H": max(h_values) if h_values else None,
    }
    energy = {
        "step": closest["step"],
        "frame_id": closest["frame_id"],
        "ALLIE": allie,
        "ALLSE": allse,
        "ALLWK": allwk,
    }
    with open(os.path.join(args.out_dir, "D3_CHECKPOINT_SELECTION.json"), "w") as handle:
        handle.write(json.dumps(selection, indent=2, sort_keys=True) + "\n")
    with open(os.path.join(args.out_dir, "D3_CHECKPOINT_ENERGY.json"), "w") as handle:
        handle.write(json.dumps(energy, indent=2, sort_keys=True) + "\n")
    report = [
        "# D3A Checkpoint Extraction Report",
        "",
        "Classification: `stage_d3a_checkpoint_extracted`",
        "",
        "- Source job: `{0}`".format(args.source_job_id),
        "- Target U2: `{0}` mm".format(args.target_u2),
        "- Actual U2: `{0}` mm".format(closest["U2"]),
        "- Step/frame: `{0}` / `{1}`".format(closest["step"], closest["frame_id"]),
        "- RF2 at checkpoint: `{0}`".format(closest["RF2"]),
        "- RF2 / H0 peak RF2: `{0}`".format(selection["checkpoint_RF2_over_H0_peak_RF2"]),
        "- Maximum d: `{0}`".format(selection["max_d"]),
        "- IPs with d >= 0.1: `{0}`".format(selection["ip_count_d_ge_0p1"]),
        "- IPs with d >= 0.5: `{0}`".format(selection["ip_count_d_ge_0p5"]),
        "- Maximum H: `{0}`".format(selection["max_H"]),
        "",
        "No state interpolation between frames was performed.",
        "",
    ]
    with open(os.path.join(args.out_dir, "D3_CHECKPOINT_REPORT.md"), "w") as handle:
        handle.write("\n".join(report))
    print(json.dumps(selection, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

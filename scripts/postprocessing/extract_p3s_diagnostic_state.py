from __future__ import print_function

import argparse
import csv
import json
import math
import os


N_ELEM = 8
TOP_NODES = set([1011, 1012, 1013, 1014, 1015])


def odb_data(value):
    try:
        return value.dataDouble
    except Exception:
        return value.data


def odb_scalar(value):
    data = odb_data(value)
    try:
        return float(data)
    except TypeError:
        return float(data[0])


def read_csv(path):
    with open(path, "r") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, fields, rows):
    handle = open(path, "w")
    try:
        handle.write(",".join(fields) + "\n")
        for row in rows:
            handle.write(",".join(str(row.get(f, "")) for f in fields) + "\n")
    finally:
        handle.close()


def target_geometry(package_dir):
    nodes = {}
    for row in read_csv(os.path.join(package_dir, "target_nodes.csv")):
        nodes[int(row["node"])] = (float(row["x"]), float(row["y"]))
    elems = {}
    for row in read_csv(os.path.join(package_dir, "target_elements.csv")):
        label = int(row["element"])
        conn = [int(row["n1"]), int(row["n2"]), int(row["n3"]), int(row["n4"])]
        x = sum(nodes[n][0] for n in conn) / float(len(conn))
        y = sum(nodes[n][1] for n in conn) / float(len(conn))
        elems[label] = {"nodes": conn, "x": x, "y": y}
    return elems


def target_keys(package_dir):
    rows = read_csv(os.path.join(package_dir, "target_transferred_ip_H.csv"))
    return sorted((int(row["target_element"]), int(row["target_ip"])) for row in rows)


def converged_frames(step):
    frames = [frame for frame in step.frames if int(frame.incrementNumber) > 0]
    if frames:
        return frames
    return list(step.frames)


def frame_bundle(odb):
    steps = odb.steps
    init = steps["D2A_INIT"]
    release = steps["D2B_RELEASE_HOLD"]
    continuation = steps["D2B_TINY_CONTINUATION"]
    release_frames = converged_frames(release)
    continuation_frames = converged_frames(continuation)
    return [
        ("F0", init, converged_frames(init)[-1]),
        ("F1", release, release_frames[0]),
        ("F2", release, release_frames[-1]),
        ("F3", continuation, continuation_frames[-1]),
    ]


def sdv_by_key(frame, name):
    values = {}
    if name not in frame.fieldOutputs:
        return values
    for value in frame.fieldOutputs[name].values:
        physical = int(value.elementLabel) - 2 * N_ELEM
        ip = int(value.integrationPoint)
        if physical >= 1 and physical <= N_ELEM and ip == 1:
            values[(physical, ip)] = odb_scalar(value)
    return values


def u_rf_probe(frame):
    u2_values = []
    rf2_values = []
    if "U" in frame.fieldOutputs:
        for value in frame.fieldOutputs["U"].values:
            if int(value.nodeLabel) in TOP_NODES:
                data = odb_data(value)
                if len(data) >= 2:
                    u2_values.append(float(data[1]))
    if "RF" in frame.fieldOutputs:
        for value in frame.fieldOutputs["RF"].values:
            if int(value.nodeLabel) in TOP_NODES:
                data = odb_data(value)
                if len(data) >= 2:
                    rf2_values.append(float(data[1]))
    u2 = "" if not u2_values else sum(u2_values) / float(len(u2_values))
    rf2 = "" if not rf2_values else sum(rf2_values)
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
    return "" if best is None else best


def energy_frames(rf_rows):
    energies = {}
    for row in rf_rows:
        label = row["frame"]
        energies[label] = {}
        for name in ["ALLIE", "ALLSE", "ALLWK"]:
            value = row[name]
            energies[label][name] = None if value == "" else float(value)
    return energies


def extract(odb_path, package_dir, out_dir):
    from odbAccess import openOdb

    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    elems = target_geometry(package_dir)
    keys = target_keys(package_dir)
    odb = openOdb(path=str(odb_path), readOnly=True)
    bundles = frame_bundle(odb)

    state = {}
    rf_rows = []
    for label, step, frame in bundles:
        sdv15 = sdv_by_key(frame, "SDV15")
        sdv16 = sdv_by_key(frame, "SDV16")
        state[label] = {"SDV15": sdv15, "SDV16": sdv16}
        u2, rf2 = u_rf_probe(frame)
        rf_rows.append(
            {
                "frame": label,
                "step": step.name,
                "increment_number": int(frame.incrementNumber),
                "step_time": float(frame.frameValue),
                "U2": u2,
                "RF2": rf2,
                "ALLIE": history_value(step, "ALLIE", frame),
                "ALLSE": history_value(step, "ALLSE", frame),
                "ALLWK": history_value(step, "ALLWK", frame),
            }
        )

    rows = []
    for element, ip in keys:
        row = {
            "element": element,
            "integration_point": ip,
            "x": elems[element]["x"],
            "y": elems[element]["y"],
        }
        for frame_label in ["F0", "F1", "F2", "F3"]:
            row["SDV15_" + frame_label] = state[frame_label]["SDV15"].get((element, ip), "")
        for frame_label in ["F0", "F1", "F2", "F3"]:
            row["SDV16_" + frame_label] = state[frame_label]["SDV16"].get((element, ip), "")
        rows.append(row)

    state_fields = [
        "element",
        "integration_point",
        "x",
        "y",
        "SDV15_F0",
        "SDV15_F1",
        "SDV15_F2",
        "SDV15_F3",
        "SDV16_F0",
        "SDV16_F1",
        "SDV16_F2",
        "SDV16_F3",
    ]
    write_csv(os.path.join(out_dir, "P3S_STATE_OUTPUT.csv"), state_fields, rows)
    write_csv(
        os.path.join(out_dir, "P3S_RF_U.csv"),
        ["frame", "step", "increment_number", "step_time", "U2", "RF2", "ALLIE", "ALLSE", "ALLWK"],
        rf_rows,
    )
    energy_rows = []
    for row in rf_rows:
        energy_rows.append(
            {
                "frame": row["frame"],
                "step": row["step"],
                "increment_number": row["increment_number"],
                "ALLIE": row["ALLIE"],
                "ALLSE": row["ALLSE"],
                "ALLWK": row["ALLWK"],
            }
        )
    write_csv(
        os.path.join(out_dir, "P3S_ENERGY.csv"),
        ["frame", "step", "increment_number", "ALLIE", "ALLSE", "ALLWK"],
        energy_rows,
    )
    odb.close()
    print("p3s_extract_ok records=%d frames=%d" % (len(rows), len(rf_rows)))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Extract P3-S serial diagnostic state from ODB")
    parser.add_argument("--odb", required=True)
    parser.add_argument("--package", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args(argv)
    extract(args.odb, args.package, args.out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import print_function

import argparse
import csv
import os
import re


IP_COUNT_BY_TYPE = {"CPS4": 4}


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


def write_csv(path, fields, rows):
    handle = open(path, "w")
    try:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    finally:
        handle.close()


def parse_deck(path):
    nodes = {}
    elements = []
    mode = None
    element_type = None
    element_set = None
    for raw in open(path, "r"):
        line = raw.strip()
        upper = line.upper()
        if not line or line.startswith("**"):
            continue
        if line.startswith("*"):
            mode = None
            if upper == "*NODE":
                mode = "node"
            elif upper.replace(" ", "").startswith("*ELEMENT,"):
                mode = "element"
                match_type = re.search(r"TYPE=([^,]+)", upper)
                match_set = re.search(r"ELSET=([^,]+)", upper)
                element_type = match_type.group(1).strip() if match_type else ""
                element_set = match_set.group(1).strip() if match_set else ""
            continue
        fields = [item.strip() for item in line.split(",") if item.strip()]
        if mode == "node":
            nodes[int(fields[0])] = (float(fields[1]), float(fields[2]))
        elif mode == "element" and element_set == "UMATELEM":
            elements.append((int(fields[0]), element_type))
    if not elements:
        raise ValueError("no umatelem visualization elements found")
    types = set(item[1] for item in elements)
    if len(types) != 1 or list(types)[0] not in IP_COUNT_BY_TYPE:
        raise ValueError("unsupported or mixed visualization formulation")
    vis_nodes = dict((label, xy) for label, xy in nodes.items() if label >= 1000)
    top_y = max(xy[1] for xy in vis_nodes.values())
    top_nodes = set(label for label, xy in vis_nodes.items() if xy[1] == top_y)
    return {
        "element_labels": [item[0] for item in elements],
        "element_type": list(types)[0],
        "integration_points": IP_COUNT_BY_TYPE[list(types)[0]],
        "top_nodes": top_nodes,
    }


def frame_bundles(odb):
    bundles = []
    for step_name, step in odb.steps.items():
        frames = [frame for frame in step.frames if int(frame.incrementNumber) > 0]
        if not frames:
            frames = list(step.frames)
        for frame in frames:
            bundles.append((step_name, frame))
    if not bundles:
        raise ValueError("ODB has no frames")
    return bundles


def field_map(frame, name, expected_labels):
    values = {}
    if name not in frame.fieldOutputs:
        return values
    for value in frame.fieldOutputs[name].values:
        label = int(value.elementLabel)
        if label in expected_labels:
            values[(label, int(value.integrationPoint))] = scalar(value)
    return values


def probe(frame, top_nodes):
    u2 = []
    rf2 = []
    for name, target in (("U", u2), ("RF", rf2)):
        if name not in frame.fieldOutputs:
            continue
        for value in frame.fieldOutputs[name].values:
            if int(value.nodeLabel) in top_nodes:
                data = odb_data(value)
                if len(data) >= 2:
                    target.append(float(data[1]))
    return (
        "" if not u2 else sum(u2) / float(len(u2)),
        "" if not rf2 else sum(rf2),
    )


def history_value(step, name, frame_time):
    best = None
    distance = None
    for region in step.historyRegions.values():
        if name not in region.historyOutputs:
            continue
        for time_value in region.historyOutputs[name].data:
            candidate = abs(float(time_value[0]) - frame_time)
            if best is None or candidate < distance:
                best = float(time_value[1])
                distance = candidate
    return "" if best is None else best


def extract(odb_path, deck_path, out_dir):
    from odbAccess import openOdb

    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    deck = parse_deck(deck_path)
    expected_labels = set(deck["element_labels"])
    odb = openOdb(path=str(odb_path), readOnly=True)
    bundles = frame_bundles(odb)
    frame_names = []
    state_by_frame = {}
    rf_rows = []
    energy_rows = []
    for index, (step_name, frame) in enumerate(bundles):
        frame_name = "F%d" % index
        frame_names.append(frame_name)
        state_by_frame[frame_name] = {
            "SDV15": field_map(frame, "SDV15", expected_labels),
            "SDV16": field_map(frame, "SDV16", expected_labels),
        }
        u2, rf2 = probe(frame, deck["top_nodes"])
        step = odb.steps[step_name]
        common = {
            "frame": frame_name,
            "step": step_name,
            "increment_number": int(frame.incrementNumber),
            "step_time": float(frame.frameValue),
        }
        rf_rows.append(dict(common, U2=u2, RF2=rf2))
        energy_rows.append(dict(
            common,
            ALLIE=history_value(step, "ALLIE", float(frame.frameValue)),
            ALLSE=history_value(step, "ALLSE", float(frame.frameValue)),
            ALLWK=history_value(step, "ALLWK", float(frame.frameValue)),
        ))

    keys = [
        (label, ip)
        for label in deck["element_labels"]
        for ip in range(1, deck["integration_points"] + 1)
    ]
    rows = []
    for label, ip in keys:
        row = {
            "visualization_element": label,
            "physical_element": label - 16,
            "integration_point": ip,
            "element_type": deck["element_type"],
        }
        for frame_name in frame_names:
            row["SDV15_" + frame_name] = state_by_frame[frame_name]["SDV15"].get((label, ip), "")
            row["SDV16_" + frame_name] = state_by_frame[frame_name]["SDV16"].get((label, ip), "")
        rows.append(row)

    state_fields = [
        "visualization_element", "physical_element", "integration_point", "element_type"
    ]
    for frame_name in frame_names:
        state_fields.extend(["SDV15_" + frame_name, "SDV16_" + frame_name])
    write_csv(os.path.join(out_dir, "P3SM0_STATE_OUTPUT.csv"), state_fields, rows)
    write_csv(
        os.path.join(out_dir, "P3SM0_RF_U.csv"),
        ["frame", "step", "increment_number", "step_time", "U2", "RF2"],
        rf_rows,
    )
    write_csv(
        os.path.join(out_dir, "P3SM0_ENERGY.csv"),
        ["frame", "step", "increment_number", "step_time", "ALLIE", "ALLSE", "ALLWK"],
        energy_rows,
    )
    odb.close()
    print(
        "p3sm0_extract_ok elements=%d ips_per_element=%d frames=%d"
        % (len(deck["element_labels"]), deck["integration_points"], len(frame_names))
    )


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--odb", required=True)
    parser.add_argument("--deck", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args(argv)
    extract(args.odb, args.deck, args.out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

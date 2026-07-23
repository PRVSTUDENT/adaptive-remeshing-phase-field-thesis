#!/usr/bin/env python3
"""Extract D3A3 ingested/equilibrated/released state from an Abaqus ODB.

Run this with Abaqus Python on the cluster after the full D3A3-R2 job, not
with ordinary CPython.
"""

from __future__ import print_function

import argparse
import csv
import json
import math
import os


N_ELEM = 6400
N_IP = 4
NODE_OFFSET = 100000
GAUSS = [
    (-1.0 / math.sqrt(3.0), -1.0 / math.sqrt(3.0)),
    (1.0 / math.sqrt(3.0), -1.0 / math.sqrt(3.0)),
    (1.0 / math.sqrt(3.0), 1.0 / math.sqrt(3.0)),
    (-1.0 / math.sqrt(3.0), 1.0 / math.sqrt(3.0)),
]


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
    with open(path, "w") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def shape_values(ip):
    xi, eta = GAUSS[ip - 1]
    return [
        0.25 * (1.0 - xi) * (1.0 - eta),
        0.25 * (1.0 + xi) * (1.0 - eta),
        0.25 * (1.0 + xi) * (1.0 + eta),
        0.25 * (1.0 - xi) * (1.0 + eta),
    ]


def load_package(package_dir, model_dir):
    nodal = {}
    for row in read_csv(os.path.join(package_dir, "D3_TRANSFERRED_NODAL_D.csv")):
        nodal[int(row["node"])] = float(row["d"])
    history = {}
    energy = {}
    for row in read_csv(os.path.join(package_dir, "D3_TRANSFERRED_IP_H.csv")):
        key = (int(row["element"]), int(row["integration_point"]))
        history[key] = float(row["H"])
        energy[key] = float(row.get("stress_strain_energy_density", row["H"]))
    elements = {}
    for row in read_csv(os.path.join(model_dir, "target", "target_elements.csv")):
        elements[int(row["element"])] = [int(row["n1"]), int(row["n2"]), int(row["n3"]), int(row["n4"])]
    return nodal, history, energy, elements


def expected_phase(element, ip, nodal_d, elements):
    weights = shape_values(ip)
    return sum(weights[i] * nodal_d[elements[element][i]] for i in range(4))


def frame_tag(step_name, frame_index, total):
    if step_name == "INGEST_TRANSFERRED_STATE":
        return "F0_ingested"
    if step_name == "CHECKPOINT_EQUILIBRATION_PHASE_FIXED":
        return "F1_equilibrated"
    if step_name == "PHASE_RELEASE_HOLD" and frame_index == total - 1:
        return "F3_release_last"
    if step_name == "PHASE_RELEASE_HOLD":
        return "F2_release_first"
    return step_name


def selected_frames(odb):
    selected = []
    for name in ["INGEST_TRANSFERRED_STATE", "CHECKPOINT_EQUILIBRATION_PHASE_FIXED"]:
        step = odb.steps[name]
        selected.append((frame_tag(name, len(step.frames) - 1, len(step.frames)), name, len(step.frames) - 1, step.frames[-1]))
    step = odb.steps["PHASE_RELEASE_HOLD"]
    first = 1 if len(step.frames) > 1 else 0
    selected.append((frame_tag("PHASE_RELEASE_HOLD", first, len(step.frames)), "PHASE_RELEASE_HOLD", first, step.frames[first]))
    if len(step.frames) > 1:
        selected.append((frame_tag("PHASE_RELEASE_HOLD", len(step.frames) - 1, len(step.frames)), "PHASE_RELEASE_HOLD", len(step.frames) - 1, step.frames[-1]))
    return selected


def physical_label(label):
    label = int(label)
    if 2 * N_ELEM < label <= 3 * N_ELEM:
        return label - 2 * N_ELEM
    if 1 <= label <= N_ELEM:
        return label
    return None


def field_by_key(frame, field_name):
    out = {}
    if field_name not in frame.fieldOutputs:
        return out
    for value in frame.fieldOutputs[field_name].values:
        elem = physical_label(value.elementLabel)
        if elem is not None:
            out[(elem, int(value.integrationPoint))] = odb_scalar(value)
    return out


def rf_u(frame):
    u2_vals = []
    rf2_sum = 0.0
    if "U" in frame.fieldOutputs:
        for value in frame.fieldOutputs["U"].values:
            if int(value.nodeLabel) > NODE_OFFSET:
                data = odb_data(value)
                if len(data) >= 2:
                    u2_vals.append(float(data[1]))
    if "RF" in frame.fieldOutputs:
        for value in frame.fieldOutputs["RF"].values:
            if int(value.nodeLabel) > NODE_OFFSET:
                data = odb_data(value)
                if len(data) >= 2:
                    rf2_sum += float(data[1])
    return {
        "top_u2_mean": sum(u2_vals) / float(len(u2_vals)) if u2_vals else "",
        "top_u2_min": min(u2_vals) if u2_vals else "",
        "top_u2_max": max(u2_vals) if u2_vals else "",
        "top_rf2_sum": rf2_sum,
    }


def metric(values):
    if not values:
        return {"count": 0, "l2": None, "max_abs": None}
    return {
        "count": len(values),
        "l2": math.sqrt(sum(v * v for v in values) / float(len(values))),
        "max_abs": max(abs(v) for v in values),
    }


def extract(odb_path, package_dir, model_dir, out_dir):
    from odbAccess import openOdb

    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    nodal_d, h_transfer, energy_transfer, elements = load_package(package_dir, model_dir)
    odb = openOdb(path=str(odb_path), readOnly=True)
    try:
        state_rows = []
        transfer_rows = []
        rf_rows = []
        energy_rows = []
        snapshots = {}
        for tag, step_name, frame_index, frame in selected_frames(odb):
            sdv15 = field_by_key(frame, "SDV15")
            sdv16 = field_by_key(frame, "SDV16")
            snapshots[tag] = {"sdv15": sdv15, "sdv16": sdv16}
            ru = rf_u(frame)
            rf_rows.append(dict({"frame_tag": tag, "step": step_name, "frame_index": frame_index}, **ru))
            sdv15_errors = []
            sdv16_errors = []
            for element in range(1, N_ELEM + 1):
                for ip in range(1, N_IP + 1):
                    key = (element, ip)
                    d_expected = expected_phase(element, ip, nodal_d, elements)
                    h_expected = h_transfer[key]
                    d_odb = sdv15.get(key, "")
                    h_odb = sdv16.get(key, "")
                    d_error = "" if d_odb == "" else float(d_odb) - d_expected
                    h_error = "" if h_odb == "" else float(h_odb) - h_expected
                    if d_error != "":
                        sdv15_errors.append(d_error)
                    if h_error != "":
                        sdv16_errors.append(h_error)
                    row = {
                        "frame_tag": tag,
                        "step": step_name,
                        "frame_index": frame_index,
                        "element": element,
                        "integration_point": ip,
                        "expected_sdv15": d_expected,
                        "odb_sdv15": d_odb,
                        "sdv15_error": d_error,
                        "expected_sdv16": h_expected,
                        "odb_sdv16": h_odb,
                        "sdv16_error": h_error,
                    }
                    state_rows.append(row)
                    if tag == "F0_ingested":
                        transfer_rows.append(row)
            energy_rows.append({
                "frame_tag": tag,
                "step": step_name,
                "frame_index": frame_index,
                "sdv15_error_metric": metric(sdv15_errors),
                "sdv16_error_metric": metric(sdv16_errors),
                "transfer_H_sum": sum(energy_transfer.values()),
                "odb_H_sum": sum(v for v in sdv16.values()),
            })

        def compare_frames(name, left, right):
            rows = []
            diffs15 = []
            diffs16 = []
            a = snapshots[left]
            b = snapshots[right]
            for element in range(1, N_ELEM + 1):
                for ip in range(1, N_IP + 1):
                    key = (element, ip)
                    d0 = a["sdv15"].get(key, "")
                    d1 = b["sdv15"].get(key, "")
                    h0 = a["sdv16"].get(key, "")
                    h1 = b["sdv16"].get(key, "")
                    dd = "" if d0 == "" or d1 == "" else float(d1) - float(d0)
                    dh = "" if h0 == "" or h1 == "" else float(h1) - float(h0)
                    if dd != "":
                        diffs15.append(dd)
                    if dh != "":
                        diffs16.append(dh)
                    rows.append({"element": element, "integration_point": ip, "left": left, "right": right, "sdv15_delta": dd, "sdv16_delta": dh})
            write_csv(os.path.join(out_dir, name), ["element", "integration_point", "left", "right", "sdv15_delta", "sdv16_delta"], rows)
            return {"sdv15_delta": metric(diffs15), "sdv16_delta": metric(diffs16)}

        initial_eq = compare_frames("D3A3_INITIAL_VS_EQUILIBRATED.csv", "F0_ingested", "F1_equilibrated")
        eq_rel = compare_frames("D3A3_EQUILIBRATED_VS_RELEASED.csv", "F1_equilibrated", "F3_release_last" if "F3_release_last" in snapshots else "F2_release_first")
        write_csv(os.path.join(out_dir, "D3A3_STATE_BY_FRAME.csv"), list(state_rows[0].keys()), state_rows)
        write_csv(os.path.join(out_dir, "D3A3_TRANSFER_VS_ODB.csv"), list(transfer_rows[0].keys()), transfer_rows)
        write_csv(os.path.join(out_dir, "D3A3_RF_U.csv"), ["frame_tag", "step", "frame_index", "top_u2_mean", "top_u2_min", "top_u2_max", "top_rf2_sum"], rf_rows)
        with open(os.path.join(out_dir, "D3A3_ENERGY_BY_FRAME.json"), "w") as handle:
            json.dump({"classification": "stage_d3a3_energy_by_frame_extracted", "frames": energy_rows}, handle, indent=2, sort_keys=True)
            handle.write("\n")
        jump = {
            "classification": "stage_d3a3_release_jump_extracted",
            "initial_vs_equilibrated": initial_eq,
            "equilibrated_vs_released": eq_rel,
        }
        with open(os.path.join(out_dir, "D3A3_RELEASE_JUMP.json"), "w") as handle:
            json.dump(jump, handle, indent=2, sort_keys=True)
            handle.write("\n")
        with open(os.path.join(out_dir, "D3A3_EXTRACTION_STATUS.json"), "w") as handle:
            json.dump({"classification": "stage_d3a3_extraction_complete", "odb": str(odb_path), "state_rows": len(state_rows)}, handle, indent=2, sort_keys=True)
            handle.write("\n")
    finally:
        odb.close()
    print("d3a3_extract_ok out_dir=%s" % out_dir)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--odb", required=True)
    parser.add_argument("--package-dir", default="runs/hpc/stage_d3/interrupted_transfer/package")
    parser.add_argument("--model-dir", default="models/state_transfer/d3_interrupted_transfer")
    parser.add_argument("--out-dir", default="runs/hpc/stage_d3/interrupted_transfer/target_ingestion_r2")
    args = parser.parse_args(argv)
    extract(args.odb, args.package_dir, args.model_dir, args.out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

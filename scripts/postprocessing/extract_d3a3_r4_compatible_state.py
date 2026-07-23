#!/usr/bin/env python3
"""Extract D3A3-R4 compatible-state frames from an Abaqus ODB.

Abaqus Python: ODB extraction only when not --skip-odb-extract.
Ordinary Python 3.11: active/free builder when not --skip-active-free-build.
"""

from __future__ import print_function

import argparse
import csv
import json
import os
import shutil

import extract_d3a3_ingested_state as base


def r4_frame_tag(step_name, frame_index, total):
    if step_name == "INGEST_COMPATIBLE_R2":
        return "F0_ingested"
    if step_name == "CHECKPOINT_EQUILIBRATION_COMPATIBLE_R2_FIXED":
        return "F1_equilibrated"
    if step_name == "ACTIVE_SET_R2_RELEASE_HOLD" and frame_index == total - 1:
        return "F3_release_last"
    if step_name == "ACTIVE_SET_R2_RELEASE_HOLD":
        return "F2_release_first"
    return step_name


def r4_selected_frames(odb):
    selected = []
    for name in ["INGEST_COMPATIBLE_R2", "CHECKPOINT_EQUILIBRATION_COMPATIBLE_R2_FIXED"]:
        step = odb.steps[name]
        selected.append(
            (r4_frame_tag(name, len(step.frames) - 1, len(step.frames)), name, len(step.frames) - 1, step.frames[-1])
        )
    step = odb.steps["ACTIVE_SET_R2_RELEASE_HOLD"]
    first = 1 if len(step.frames) > 1 else 0
    selected.append(
        (
            r4_frame_tag("ACTIVE_SET_R2_RELEASE_HOLD", first, len(step.frames)),
            "ACTIVE_SET_R2_RELEASE_HOLD",
            first,
            step.frames[first],
        )
    )
    if len(step.frames) > 1:
        selected.append(
            (
                r4_frame_tag("ACTIVE_SET_R2_RELEASE_HOLD", len(step.frames) - 1, len(step.frames)),
                "ACTIVE_SET_R2_RELEASE_HOLD",
                len(step.frames) - 1,
                step.frames[-1],
            )
        )
    return selected


def copy_r4_names(out_dir):
    pairs = [
        ("D3A3_STATE_BY_FRAME.csv", "D3A3_R4_STATE_BY_FRAME.csv"),
        ("D3A3_TRANSFER_VS_ODB.csv", "D3A3_R4_TRANSFER_VS_ODB.csv"),
        ("D3A3_RF_U_CORRECTED.csv", "D3A3_R4_TOP_RF_U.csv"),
        ("D3A3_RELEASE_JUMP.json", "D3A3_R4_RELEASE_JUMP.json"),
        ("D3A3_RECONSTRUCTED_ENERGY_BY_FRAME_CORRECTED.json", "D3A3_R4_RECONSTRUCTED_ENERGY.json"),
        ("D3A3_PHASE_NODE_RECOVERY_BY_FRAME.csv", "D3A3_R4_PHASE_NODE_RECOVERY_BY_FRAME.csv"),
    ]
    for src, dst in pairs:
        src_path = os.path.join(out_dir, src)
        if os.path.exists(src_path):
            shutil.copyfile(src_path, os.path.join(out_dir, dst))


def _read_csv(path):
    with open(path, "r") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path, fields, rows):
    with open(path, "w") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path, data):
    with open(path, "w") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _bool_value(value):
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in ("true", "1", "yes"):
        return True
    if text in ("false", "0", "no"):
        return False
    raise ValueError("cannot parse boolean: %r" % value)


def build_active_free_state(out_dir, active_set_csv, lower_bound_csv, expected_nodes, expected_active, expected_free):
    recovery_path = os.path.join(out_dir, "D3A3_PHASE_NODE_RECOVERY_BY_FRAME.csv")
    if not os.path.exists(recovery_path):
        raise FileNotFoundError("missing phase recovery: %s" % recovery_path)

    recovery_rows = _read_csv(recovery_path)
    active_rows = _read_csv(active_set_csv)
    lower_rows = _read_csv(lower_bound_csv)

    active_by_node = {}
    xy_by_node = {}
    for row in active_rows:
        node = int(row["node"])
        active_by_node[node] = _bool_value(row["active_lower_bound"])
        xy_by_node[node] = (float(row["x"]), float(row["y"]))

    lower_by_node = {}
    for row in lower_rows:
        node = int(row["node"])
        lower_by_node[node] = float(row["d_lower_bound"])
        if node not in xy_by_node:
            xy_by_node[node] = (float(row["x"]), float(row["y"]))

    by_frame = {}
    for row in recovery_rows:
        tag = row["frame_tag"]
        node = int(row["node"])
        by_frame.setdefault(tag, {})[node] = float(row["recovered_d_mean"])

    required_frames = ["F0_ingested", "F1_equilibrated", "F2_release_first", "F3_release_last"]
    missing_frames = [tag for tag in required_frames if tag not in by_frame]
    if missing_frames:
        raise ValueError("missing recovered frames: %s" % ",".join(missing_frames))

    all_nodes = sorted(set(active_by_node) | set(lower_by_node))
    fields = [
        "node",
        "x",
        "y",
        "active_lower_bound",
        "d_lower_bound",
        "d_F0",
        "d_F1",
        "d_F2",
        "d_F3",
        "F3_minus_F1",
        "F3_minus_lower_bound",
    ]
    node_rows = []
    missing_recovered = 0
    for node in all_nodes:
        values = {}
        complete = True
        for tag, key in [
            ("F0_ingested", "d_F0"),
            ("F1_equilibrated", "d_F1"),
            ("F2_release_first", "d_F2"),
            ("F3_release_last", "d_F3"),
        ]:
            if node not in by_frame[tag]:
                complete = False
                values[key] = ""
            else:
                values[key] = by_frame[tag][node]
        if not complete:
            missing_recovered += 1
            f3_minus_f1 = ""
            f3_minus_lb = ""
        else:
            f3_minus_f1 = values["d_F3"] - values["d_F1"]
            f3_minus_lb = values["d_F3"] - lower_by_node[node]
        x, y = xy_by_node.get(node, ("", ""))
        node_rows.append(
            {
                "node": node,
                "x": x,
                "y": y,
                "active_lower_bound": bool(active_by_node.get(node, False)),
                "d_lower_bound": lower_by_node.get(node, ""),
                "d_F0": values["d_F0"],
                "d_F1": values["d_F1"],
                "d_F2": values["d_F2"],
                "d_F3": values["d_F3"],
                "F3_minus_F1": f3_minus_f1,
                "F3_minus_lower_bound": f3_minus_lb,
            }
        )

    active_out = [row for row in node_rows if row["active_lower_bound"]]
    free_out = [row for row in node_rows if not row["active_lower_bound"]]
    _write_csv(os.path.join(out_dir, "D3A3_R4_PHASE_NODE_STATE_BY_FRAME.csv"), fields, node_rows)
    _write_csv(os.path.join(out_dir, "D3A3_R4_ACTIVE_NODE_STATE.csv"), fields, active_out)
    _write_csv(os.path.join(out_dir, "D3A3_R4_FREE_NODE_STATE.csv"), fields, free_out)

    audit = {
        "classification": (
            "stage_d3a3_r4_lower_bound_audit_pass"
            if (
                len(node_rows) == expected_nodes
                and len(active_out) == expected_active
                and len(free_out) == expected_free
                and missing_recovered == 0
            )
            else "stage_d3a3_r4_lower_bound_audit_fail"
        ),
        "all_nodes": len(node_rows),
        "active_nodes": len(active_out),
        "free_nodes": len(free_out),
        "missing_recovered_values": missing_recovered,
        "expected_all_nodes": expected_nodes,
        "expected_active_nodes": expected_active,
        "expected_free_nodes": expected_free,
        "required_frames": required_frames,
        "active_set_csv": active_set_csv,
        "lower_bound_csv": lower_bound_csv,
    }
    _write_json(os.path.join(out_dir, "D3A3_R4_LOWER_BOUND_AUDIT.json"), audit)
    return audit


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--odb", default=None)
    parser.add_argument("--package-dir", default="runs/hpc/stage_d3/interrupted_transfer/package_compatible_r2")
    parser.add_argument(
        "--active-set-csv",
        default="runs/hpc/stage_d3/interrupted_transfer/package_compatible_r2/D3_ACTIVE_SET_BY_NODE.csv",
    )
    parser.add_argument(
        "--lower-bound-csv",
        default="runs/hpc/stage_d3/interrupted_transfer/package_compatible_r2/D3_LOWER_BOUND_NODAL_D.csv",
    )
    parser.add_argument("--expected-active", type=int, default=6446)
    parser.add_argument("--expected-free", type=int, default=155)
    parser.add_argument("--expected-nodes", type=int, default=6601)
    parser.add_argument("--model-dir", default="models/state_transfer/d3_interrupted_transfer")
    parser.add_argument("--out-dir", default="runs/hpc/stage_d3/interrupted_transfer/target_ingestion_r4_compatible")
    parser.add_argument("--skip-odb-extract", action="store_true")
    parser.add_argument("--skip-active-free-build", action="store_true")
    args = parser.parse_args(argv)

    if args.skip_odb_extract and args.skip_active_free_build:
        raise SystemExit("refusing both --skip-odb-extract and --skip-active-free-build")
    if not args.skip_odb_extract and not args.odb:
        raise SystemExit("--odb is required unless --skip-odb-extract is set")

    if not args.skip_odb_extract:
        base.selected_frames = r4_selected_frames
        base.extract(args.odb, args.package_dir, args.model_dir, args.out_dir)
        copy_r4_names(args.out_dir)

    if not args.skip_active_free_build:
        audit = build_active_free_state(
            args.out_dir,
            args.active_set_csv,
            args.lower_bound_csv,
            args.expected_nodes,
            args.expected_active,
            args.expected_free,
        )
        print(json.dumps(audit, indent=2, sort_keys=True))
        if audit["classification"] != "stage_d3a3_r4_lower_bound_audit_pass":
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

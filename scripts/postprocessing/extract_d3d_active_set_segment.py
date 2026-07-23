#!/usr/bin/env python3
"""Extract D3D active-set segment frames from an Abaqus ODB (Abaqus Python)."""

from __future__ import print_function

import argparse
import csv
import json
import os
import shutil

import extract_d3a3_ingested_state as base


CHECKPOINT_U2 = 0.003000000026077032
SEGMENT_U2 = 0.0031
STEP4_PERIOD = 1.0
EXPECTED_TOP_NODES = 81


def d3d_frame_tag(step_name, frame_index, total):
    if step_name == "INGEST_COMPATIBLE_R2":
        return "F0_ingested"
    if step_name == "CHECKPOINT_EQUILIBRATION_COMPATIBLE_R2_FIXED":
        return "F1_equilibrated"
    if step_name == "ACTIVE_SET_R2_RELEASE_HOLD" and frame_index == total - 1:
        return "F3_release_last"
    if step_name == "ACTIVE_SET_R2_RELEASE_HOLD":
        return "F2_release_first"
    if step_name == "ACTIVE_SET_VALIDITY_SEGMENT":
        if frame_index == 0:
            return "F4_segment_initial"
        if frame_index == total - 1:
            return "F4_segment_end"
        return "F4_segment_inc_%03d" % frame_index
    return "%s_f%d" % (step_name, frame_index)


def d3d_selected_frames(odb):
    selected = []
    for name in ["INGEST_COMPATIBLE_R2", "CHECKPOINT_EQUILIBRATION_COMPATIBLE_R2_FIXED"]:
        step = odb.steps[name]
        selected.append(
            (
                d3d_frame_tag(name, len(step.frames) - 1, len(step.frames)),
                name,
                len(step.frames) - 1,
                step.frames[-1],
            )
        )
    step = odb.steps["ACTIVE_SET_R2_RELEASE_HOLD"]
    first = 1 if len(step.frames) > 1 else 0
    selected.append(
        (
            d3d_frame_tag("ACTIVE_SET_R2_RELEASE_HOLD", first, len(step.frames)),
            "ACTIVE_SET_R2_RELEASE_HOLD",
            first,
            step.frames[first],
        )
    )
    if len(step.frames) > 1:
        selected.append(
            (
                d3d_frame_tag("ACTIVE_SET_R2_RELEASE_HOLD", len(step.frames) - 1, len(step.frames)),
                "ACTIVE_SET_R2_RELEASE_HOLD",
                len(step.frames) - 1,
                step.frames[-1],
            )
        )
    seg = odb.steps["ACTIVE_SET_VALIDITY_SEGMENT"]
    total = len(seg.frames)
    for i, frame in enumerate(seg.frames):
        selected.append(
            (d3d_frame_tag("ACTIVE_SET_VALIDITY_SEGMENT", i, total), "ACTIVE_SET_VALIDITY_SEGMENT", i, frame)
        )
    return selected


def expected_top_u2(step_name, step_time):
    if step_name == "INGEST_COMPATIBLE_R2":
        return 0.0
    if step_name in (
        "CHECKPOINT_EQUILIBRATION_COMPATIBLE_R2_FIXED",
        "ACTIVE_SET_R2_RELEASE_HOLD",
    ):
        return CHECKPOINT_U2
    if step_name == "ACTIVE_SET_VALIDITY_SEGMENT":
        t = float(step_time) / STEP4_PERIOD if STEP4_PERIOD else 0.0
        return CHECKPOINT_U2 + (SEGMENT_U2 - CHECKPOINT_U2) * t
    return ""


def copy_names(out_dir):
    # Do not promote the R4 release-jump file as the D3D irreversibility audit.
    pairs = [
        ("D3A3_STATE_BY_FRAME.csv", "D3D_STATE_BY_FRAME.csv"),
        ("D3A3_RF_U_CORRECTED.csv", "D3D_TOP_RF_U.csv"),
        ("D3A3_PHASE_NODE_RECOVERY_BY_FRAME.csv", "D3D_PHASE_NODE_STATE_BY_FRAME.csv"),
        ("D3A3_RECONSTRUCTED_ENERGY_BY_FRAME_CORRECTED.json", "D3D_RECONSTRUCTED_ENERGY_BY_FRAME.json"),
    ]
    for src, dst in pairs:
        sp = os.path.join(out_dir, src)
        if os.path.exists(sp):
            shutil.copyfile(sp, os.path.join(out_dir, dst))


def _read_rf_by_tag(out_dir):
    path = os.path.join(out_dir, "D3D_TOP_RF_U.csv")
    if not os.path.exists(path):
        path = os.path.join(out_dir, "D3A3_RF_U_CORRECTED.csv")
    out = {}
    if not os.path.exists(path):
        return out
    with open(path, "r") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            out[row["frame_tag"]] = row
    return out


def write_frame_manifest(odb_path, out_dir):
    from odbAccess import openOdb  # Abaqus only

    rf = _read_rf_by_tag(out_dir)
    odb = openOdb(path=str(odb_path), readOnly=True)
    rows = []
    try:
        for tag, step_name, frame_index, frame in d3d_selected_frames(odb):
            step_time = float(frame.frameValue)
            if step_name == "ACTIVE_SET_VALIDITY_SEGMENT":
                normalized = step_time / STEP4_PERIOD if STEP4_PERIOD else 0.0
            else:
                # Prefix steps use their own period; report absolute step time.
                period = float(odb.steps[step_name].timePeriod) if hasattr(odb.steps[step_name], "timePeriod") else 1.0
                normalized = step_time / period if period else 0.0
            expected = expected_top_u2(step_name, step_time)
            ru = rf.get(tag, {})
            rows.append(
                {
                    "frame_tag": tag,
                    "step_name": step_name,
                    "frame_index": frame_index,
                    "step_time": step_time,
                    "normalized_step_time": normalized,
                    "expected_top_u2": expected,
                    "actual_top_u2_mean": ru.get("top_u2_mean", ""),
                    "actual_top_u2_min": ru.get("top_u2_min", ""),
                    "actual_top_u2_max": ru.get("top_u2_max", ""),
                    "top_node_count": ru.get("top_node_count", ""),
                    "top_rf2_sum": ru.get("top_rf2_sum", ""),
                }
            )
    finally:
        odb.close()

    fields = [
        "frame_tag",
        "step_name",
        "frame_index",
        "step_time",
        "normalized_step_time",
        "expected_top_u2",
        "actual_top_u2_mean",
        "actual_top_u2_min",
        "actual_top_u2_max",
        "top_node_count",
        "top_rf2_sum",
    ]
    csv_path = os.path.join(out_dir, "D3D_FRAME_MANIFEST.csv")
    with open(csv_path, "w") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    step4 = [r for r in rows if r["step_name"] == "ACTIVE_SET_VALIDITY_SEGMENT"]
    step4_sorted = sorted(step4, key=lambda r: (int(r["frame_index"]), float(r["step_time"])))
    accepted_increments = max(0, len(step4_sorted) - 1)
    first_t = float(step4_sorted[0]["step_time"]) if step4_sorted else None
    last_t = float(step4_sorted[-1]["step_time"]) if step4_sorted else None
    last_expected = float(step4_sorted[-1]["expected_top_u2"]) if step4_sorted else None
    top_counts = []
    for r in step4_sorted:
        try:
            top_counts.append(int(r["top_node_count"]))
        except (TypeError, ValueError):
            top_counts.append(-1)

    payload = {
        "classification": "stage_d3d_frame_manifest_written",
        "frames": rows,
        "step4_frame_count": len(step4_sorted),
        "accepted_continuation_increments": accepted_increments,
        "step4_first_time": first_t,
        "step4_last_time": last_t,
        "step4_endpoint_expected_u2": last_expected,
        "step4_top_node_count_ok": all(c == EXPECTED_TOP_NODES for c in top_counts) if top_counts else False,
        "expected_top_nodes": EXPECTED_TOP_NODES,
        "checkpoint_u2": CHECKPOINT_U2,
        "segment_u2": SEGMENT_U2,
    }
    with open(os.path.join(out_dir, "D3D_FRAME_MANIFEST.json"), "w") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return payload


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--odb", required=True)
    parser.add_argument(
        "--package-dir",
        default="runs/hpc/stage_d3/interrupted_transfer/package_compatible_r2",
    )
    parser.add_argument("--model-dir", default="models/state_transfer/d3_interrupted_transfer")
    parser.add_argument(
        "--out-dir",
        default="runs/hpc/stage_d3/fracture_continuation/d3d_active_set_segment",
    )
    args = parser.parse_args(argv)
    base.selected_frames = d3d_selected_frames
    base.extract(args.odb, args.package_dir, args.model_dir, args.out_dir)
    copy_names(args.out_dir)
    manifest = write_frame_manifest(args.odb, args.out_dir)
    status = {
        "classification": "stage_d3d_extraction_complete",
        "odb": args.odb,
        "out_dir": args.out_dir,
        "step4_frame_count": manifest.get("step4_frame_count"),
        "accepted_continuation_increments": manifest.get("accepted_continuation_increments"),
    }
    with open(os.path.join(args.out_dir, "D3D_EXTRACTION_STATUS.json"), "w") as handle:
        json.dump(status, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(status, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

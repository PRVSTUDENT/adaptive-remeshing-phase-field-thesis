#!/usr/bin/env python3
"""Extract D3D active-set segment frames from an Abaqus ODB (Abaqus Python)."""

from __future__ import print_function

import argparse
import json
import os
import shutil

import extract_d3a3_ingested_state as base


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
    # All frames of continuation segment.
    seg = odb.steps["ACTIVE_SET_VALIDITY_SEGMENT"]
    total = len(seg.frames)
    for i, frame in enumerate(seg.frames):
        selected.append(
            (d3d_frame_tag("ACTIVE_SET_VALIDITY_SEGMENT", i, total), "ACTIVE_SET_VALIDITY_SEGMENT", i, frame)
        )
    return selected


def copy_names(out_dir):
    pairs = [
        ("D3A3_STATE_BY_FRAME.csv", "D3D_STATE_BY_FRAME.csv"),
        ("D3A3_RF_U_CORRECTED.csv", "D3D_TOP_RF_U.csv"),
        ("D3A3_PHASE_NODE_RECOVERY_BY_FRAME.csv", "D3D_PHASE_NODE_STATE_BY_FRAME.csv"),
        ("D3A3_RECONSTRUCTED_ENERGY_BY_FRAME_CORRECTED.json", "D3D_RECONSTRUCTED_ENERGY_BY_FRAME.json"),
        ("D3A3_RELEASE_JUMP.json", "D3D_IRREVERSIBILITY_AUDIT.json"),
    ]
    for src, dst in pairs:
        sp = os.path.join(out_dir, src)
        if os.path.exists(sp):
            shutil.copyfile(sp, os.path.join(out_dir, dst))


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
    status = {
        "classification": "stage_d3d_extraction_complete",
        "odb": args.odb,
        "out_dir": args.out_dir,
    }
    with open(os.path.join(args.out_dir, "D3D_EXTRACTION_STATUS.json"), "w") as handle:
        json.dump(status, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(status, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

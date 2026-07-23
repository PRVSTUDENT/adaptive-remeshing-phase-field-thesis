#!/usr/bin/env python3
"""Extract D3A3-R3 compatible-state frames from an Abaqus ODB.

This reuses the corrected D3A3 extractor machinery with the R3 step names and
the compatible package. Run with Abaqus Python.
"""

from __future__ import print_function

import argparse
import os
import shutil

import extract_d3a3_ingested_state as base


def r3_frame_tag(step_name, frame_index, total):
    if step_name == "INGEST_COMPATIBLE_STATE":
        return "F0_ingested"
    if step_name == "CHECKPOINT_EQUILIBRATION_COMPATIBLE_FIXED":
        return "F1_equilibrated"
    if step_name == "ACTIVE_SET_RELEASE_HOLD" and frame_index == total - 1:
        return "F3_release_last"
    if step_name == "ACTIVE_SET_RELEASE_HOLD":
        return "F2_release_first"
    return step_name


def r3_selected_frames(odb):
    selected = []
    for name in ["INGEST_COMPATIBLE_STATE", "CHECKPOINT_EQUILIBRATION_COMPATIBLE_FIXED"]:
        step = odb.steps[name]
        selected.append((r3_frame_tag(name, len(step.frames) - 1, len(step.frames)), name, len(step.frames) - 1, step.frames[-1]))
    step = odb.steps["ACTIVE_SET_RELEASE_HOLD"]
    first = 1 if len(step.frames) > 1 else 0
    selected.append((r3_frame_tag("ACTIVE_SET_RELEASE_HOLD", first, len(step.frames)), "ACTIVE_SET_RELEASE_HOLD", first, step.frames[first]))
    if len(step.frames) > 1:
        selected.append((r3_frame_tag("ACTIVE_SET_RELEASE_HOLD", len(step.frames) - 1, len(step.frames)), "ACTIVE_SET_RELEASE_HOLD", len(step.frames) - 1, step.frames[-1]))
    return selected


def copy_r3_names(out_dir):
    pairs = [
        ("D3A3_STATE_BY_FRAME.csv", "D3A3_R3_STATE_BY_FRAME.csv"),
        ("D3A3_TRANSFER_VS_ODB.csv", "D3A3_R3_TRANSFER_VS_ODB.csv"),
        ("D3A3_RF_U_CORRECTED.csv", "D3A3_R3_TOP_RF_U.csv"),
        ("D3A3_RELEASE_JUMP.json", "D3A3_R3_RELEASE_JUMP.json"),
        ("D3A3_RECONSTRUCTED_ENERGY_BY_FRAME_CORRECTED.json", "D3A3_R3_RECONSTRUCTED_ENERGY.json"),
    ]
    for src, dst in pairs:
        src_path = os.path.join(out_dir, src)
        if os.path.exists(src_path):
            shutil.copyfile(src_path, os.path.join(out_dir, dst))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--odb", required=True)
    parser.add_argument("--package-dir", default="runs/hpc/stage_d3/interrupted_transfer/package_compatible_r1")
    parser.add_argument("--model-dir", default="models/state_transfer/d3_interrupted_transfer")
    parser.add_argument("--out-dir", default="runs/hpc/stage_d3/interrupted_transfer/target_ingestion_r3_compatible")
    args = parser.parse_args(argv)
    base.selected_frames = r3_selected_frames
    base.extract(args.odb, args.package_dir, args.model_dir, args.out_dir)
    copy_r3_names(args.out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

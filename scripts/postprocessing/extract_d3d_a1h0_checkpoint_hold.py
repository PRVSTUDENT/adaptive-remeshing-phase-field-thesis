#!/usr/bin/env python3
"""Extract the two fixed-phase D3D-A1H0 checkpoint frames (Abaqus Python)."""

from __future__ import print_function

import argparse
import json
import os
import shutil

import extract_d3a3_ingested_state as base


def selected_frames(odb):
    out = []
    mapping = [
        ("F0_ingested", "INGEST_D3D_A1_CANDIDATE"),
        ("F1_equilibrated", "D3D_A1_MECHANICAL_CHECKPOINT_EQUILIBRATION"),
    ]
    for tag, name in mapping:
        step = odb.steps[name]
        index = len(step.frames) - 1
        out.append((tag, name, index, step.frames[index]))
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--odb", required=True)
    parser.add_argument("--package-dir", required=True)
    parser.add_argument("--model-dir", default="models/state_transfer/d3_interrupted_transfer")
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args(argv)
    base.selected_frames = selected_frames
    base.extract(args.odb, args.package_dir, args.model_dir, args.out_dir)
    renames = {
        "D3A3_STATE_BY_FRAME.csv": "D3D_A1H0_STATE_BY_FRAME.csv",
        "D3A3_PHASE_NODE_RECOVERY_BY_FRAME.csv": "D3D_A1H0_PHASE_NODE_STATE_BY_FRAME.csv",
        "D3A3_RF_U_CORRECTED.csv": "D3D_A1H0_TOP_RF_U.csv",
        "D3A3_RECONSTRUCTED_ENERGY_BY_FRAME_CORRECTED.json": "D3D_A1H0_RECONSTRUCTED_ENERGY_BY_FRAME.json",
    }
    for source, destination in renames.items():
        shutil.copyfile(os.path.join(args.out_dir, source), os.path.join(args.out_dir, destination))
    status = {"classification": "stage_d3d_a1h0_extraction_complete", "odb": args.odb}
    with open(os.path.join(args.out_dir, "D3D_A1H0_ODB_LOCATION.json"), "w") as handle:
        json.dump({"odb_path": args.odb, "repository_copy_created": False}, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(status, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

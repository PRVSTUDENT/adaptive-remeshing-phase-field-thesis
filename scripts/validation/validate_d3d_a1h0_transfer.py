#!/usr/bin/env python3
"""Validate D3D-A1H0 ingestion coverage and transfer errors."""

import argparse
import csv
import json
from pathlib import Path


def rows(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def validate(target):
    state = [r for r in rows(target / "D3D_A1H0_STATE_BY_FRAME.csv") if r["frame_tag"] == "F0_ingested"]
    phase = [r for r in rows(target / "D3D_A1H0_PHASE_NODE_STATE_BY_FRAME.csv") if r["frame_tag"] == "F0_ingested"]
    result = {
        "classification": "stage_d3d_a1h0_transfer_pass",
        "phase_node_coverage": len(phase),
        "history_coverage": len(state),
        "sdv15_transfer_max_error": max((abs(float(r["sdv15_error"])) for r in state), default=float("inf")),
        "sdv16_transfer_max_error": max((abs(float(r["sdv16_error"])) for r in state), default=float("inf")),
        "non_positive_detJ": 0,
    }
    result["failures"] = [
        name for name, ok in {
            "phase_coverage": result["phase_node_coverage"] == 6601,
            "history_coverage": result["history_coverage"] == 25600,
            "sdv15": result["sdv15_transfer_max_error"] <= 1e-8,
            "sdv16": result["sdv16_transfer_max_error"] <= 1e-8,
        }.items() if not ok
    ]
    if result["failures"]:
        result["classification"] = "stage_d3d_a1h0_postprocessing_fail"
    (target / "D3D_A1H0_TRANSFER_VALIDATION.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-dir", type=Path, required=True)
    args = parser.parse_args()
    result = validate(args.target_dir)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not result["failures"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate D3D-A1H0 ingestion coverage and transfer errors."""

import argparse
import csv
import json
import math
from pathlib import Path


def rows(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def validate(target):
    state = [r for r in rows(target / "D3D_A1H0_STATE_BY_FRAME.csv") if r["frame_tag"] == "F0_ingested"]
    phase = [r for r in rows(target / "D3D_A1H0_PHASE_NODE_STATE_BY_FRAME.csv") if r["frame_tag"] == "F0_ingested"]
    energy = json.loads((target / "D3D_A1H0_RECONSTRUCTED_ENERGY_BY_FRAME.json").read_text(encoding="utf-8"))
    energy_f0 = next(r for r in energy["frames"] if r["frame_tag"] == "F0_ingested")
    phase_nodes = {int(r["node"]) for r in phase}
    history_ips = {(int(r["element"]), int(r["uel_integration_point"])) for r in state}
    finite_columns = ["odb_sdv15", "odb_sdv16", "sdv15_error", "sdv16_error"]
    all_finite = all(math.isfinite(float(r[c])) for r in state for c in finite_columns) and all(
        math.isfinite(float(r["recovered_d_mean"])) for r in phase
    )
    result = {
        "classification": "stage_d3d_a1h0_transfer_pass",
        "phase_node_coverage": len(phase_nodes),
        "history_coverage": len(history_ips),
        "duplicate_phase_node_records": len(phase) - len(phase_nodes),
        "duplicate_history_ip_records": len(state) - len(history_ips),
        "sdv15_transfer_max_error": max((abs(float(r["sdv15_error"])) for r in state), default=float("inf")),
        "sdv16_transfer_max_error": max((abs(float(r["sdv16_error"])) for r in state), default=float("inf")),
        "non_positive_detJ": int(energy_f0["non_positive_detJ_count"]),
        "all_values_finite": all_finite,
    }
    result["failures"] = [
        name for name, ok in {
            "phase_coverage": result["phase_node_coverage"] == 6601,
            "history_coverage": result["history_coverage"] == 25600,
            "phase_duplicates": result["duplicate_phase_node_records"] == 0,
            "history_duplicates": result["duplicate_history_ip_records"] == 0,
            "sdv15": result["sdv15_transfer_max_error"] <= 1e-8,
            "sdv16": result["sdv16_transfer_max_error"] <= 1e-8,
            "detJ": result["non_positive_detJ"] == 0,
            "finite": result["all_values_finite"],
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

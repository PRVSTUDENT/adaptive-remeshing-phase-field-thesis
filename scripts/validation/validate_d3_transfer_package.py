#!/usr/bin/env python3
"""Validate a prepared D3 transfer-package design before any solver submission."""

import argparse
from pathlib import Path


REQUIRED_METRICS = {
    "RF_jump_at_transfer",
    "RF_U_continuity",
    "SDV15_L2_error",
    "SDV15_max_error",
    "SDV16_L2_error",
    "SDV16_max_error",
    "no_healing_violations",
    "history_monotonicity_violations",
    "energy_jump",
    "peak_force_difference",
    "peak_displacement_difference",
    "crack_path_distance",
    "unmapped_state_count",
}


def parse_design(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    metrics = []
    in_metrics = False
    submission_authorized = None
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("submission_authorized:"):
            submission_authorized = line.split(":", 1)[1].strip().lower() == "true"
        if line == "metrics:":
            in_metrics = True
            continue
        if in_metrics:
            if line.startswith("- "):
                metrics.append(line[2:].strip())
            elif line and not raw.startswith(" "):
                in_metrics = False
    return {
        "solver_job_submitted": False,
        "submission_authorized": submission_authorized,
        "metrics": metrics,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--design", type=Path, default=Path("configs/state_transfer/d3_interrupted_transfer.yaml"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    manifest = parse_design(args.design)
    failures = []
    if manifest.get("solver_job_submitted") is not False:
        failures.append("D3 validation package must not represent a submitted solver job")
    if manifest.get("submission_authorized") is not False:
        failures.append("D3 design must keep submission_authorized: false")
    metrics = set(manifest.get("metrics", []))
    missing = sorted(REQUIRED_METRICS - metrics)
    if missing:
        failures.append("missing predeclared metrics: " + ", ".join(missing))

    status = {
        "classification": "stage_d3_transfer_package_design_pass" if not failures else "stage_d3_transfer_package_design_fail",
        "D3_design_ok": not failures,
        "solver_job_submitted": False,
        "design": str(args.design),
        "failures": failures,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    import json

    args.out.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(status, indent=2, sort_keys=True))
    return 0 if status["D3_design_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Apply the strict Stage P3-S serial diagnostic acceptance gates."""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def finite(value: str) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--job-id", default="unknown")
    parser.add_argument("--solver-exit", type=int, required=True)
    args = parser.parse_args()
    out = args.out_dir
    failures: list[str] = []
    required = [
        "P3S_ENVIRONMENT.txt",
        "P3S_JOB_RECORD.txt",
        "P3S_CALLBACK_EVENTS.csv",
        "P3S_SHARED_ACCESS_SUMMARY.json",
        "P3S_STATE_OUTPUT.csv",
        "P3S_RF_U.csv",
        "P3S_ENERGY.csv",
        "p3s_serial.sta",
    ]
    for name in required:
        if not (out / name).is_file():
            failures.append("missing " + name)

    summary: dict[str, object] = {}
    state: list[dict[str, str]] = []
    if (out / "P3S_SHARED_ACCESS_SUMMARY.json").is_file():
        summary = json.loads((out / "P3S_SHARED_ACCESS_SUMMARY.json").read_text(encoding="utf-8"))
    if (out / "P3S_STATE_OUTPUT.csv").is_file():
        state = rows(out / "P3S_STATE_OUTPUT.csv")

    callbacks = summary.get("callbacks", {}) if isinstance(summary, dict) else {}
    for callback in ("UEXTERNALDB", "UEL", "UMAT"):
        if not isinstance(callbacks, dict) or not callbacks.get(callback):
            failures.append(callback + " callback not observed")
    if summary.get("ranks") != [0]:
        failures.append("serial rank set is not [0]")
    if summary.get("threads") != [0]:
        failures.append("serial thread set is not [0]")
    if summary.get("initialization_write_records") != 8:
        failures.append("initialization event count is not 8")
    if summary.get("conflicting_shared_writes") != 0:
        failures.append("shared-state conflict detected")
    if len(state) != 8:
        failures.append("expected eight element/IP state records")

    expected_keys = {(element, 1) for element in range(1, 9)}
    observed_keys = {
        (int(row["element"]), int(row["integration_point"]))
        for row in state
        if row.get("element") and row.get("integration_point")
    }
    if observed_keys != expected_keys:
        failures.append("element/IP coverage is incomplete")

    phase_columns = ["SDV15_F0", "SDV15_F1", "SDV15_F2", "SDV15_F3"]
    history_columns = ["SDV16_F0", "SDV16_F1", "SDV16_F2", "SDV16_F3"]
    nonfinite = phase_bounds = phase_decreases = history_decreases = 0
    for row in state:
        phase = [float(row[name]) for name in phase_columns if finite(row.get(name, ""))]
        history = [float(row[name]) for name in history_columns if finite(row.get(name, ""))]
        if len(phase) != 4 or len(history) != 4:
            nonfinite += 1
            continue
        phase_bounds += sum(value < 0.0 or value > 1.0 for value in phase)
        phase_decreases += sum(b < a for a, b in zip(phase, phase[1:]))
        history_decreases += sum(b < a for a, b in zip(history, history[1:]))
    if nonfinite:
        failures.append("nonfinite or missing state values")
    if phase_bounds:
        failures.append("phase-bound violations")
    if phase_decreases:
        failures.append("phase irreversibility violations")
    if history_decreases:
        failures.append("history decreases")

    sta = (out / "p3s_serial.sta")
    completion = sta.is_file() and "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" in sta.read_text(
        encoding="utf-8", errors="replace"
    )
    if args.solver_exit != 0:
        failures.append("nonzero solver exit")
    if not completion:
        failures.append("job completion token absent")

    status = {
        "classification": "stage_p3_serial_diagnostic_pass" if not failures else "stage_p3_serial_diagnostic_fail",
        "P3S_ok": not failures,
        "job_id": args.job_id,
        "solver_exit": args.solver_exit,
        "solver_executed": True,
        "expected_element_ip_coverage": 1.0 if observed_keys == expected_keys else len(observed_keys) / 8.0,
        "initialization_events": summary.get("initialization_write_records"),
        "duplicate_ownership_conflicts": summary.get("conflicting_shared_writes"),
        "nonfinite_state_records": nonfinite,
        "phase_bound_violations": phase_bounds,
        "phase_irreversibility_violations": phase_decreases,
        "history_decreases": history_decreases,
        "failures": failures,
    }
    (out / "P3S_STATUS.json").write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    marker = out / "P3S_COMPLETION.ok"
    if marker.exists():
        marker.unlink()
    if not failures:
        marker.write_text(
            "classification=stage_p3_serial_diagnostic_pass\njob_id=" + args.job_id + "\n",
            encoding="utf-8",
        )
    print(json.dumps(status, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())

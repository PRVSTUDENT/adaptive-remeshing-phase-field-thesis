#!/usr/bin/env python3
"""Apply strict technical, callback, state and completion gates to P3-S."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from pathlib import Path


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def finite(value: object) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""


def technical_gates(out: Path, solver_exit: int) -> dict[str, bool]:
    stdout = text(out / "p3s_serial.abaqus_stdout.log")
    sta = text(out / "p3s_serial.sta")
    return {
        "abaqus_launched": "Begin Compiling Abaqus/Standard User Subroutines" in stdout,
        "compile_complete": "End Compiling Abaqus/Standard User Subroutines" in stdout,
        "link_complete": "End Linking Abaqus/Standard User Subroutines" in stdout,
        "input_processing_complete": (
            "Begin Analysis Input File Processor" in stdout
            and "End Analysis Input File Processor" in stdout
        ),
        "job_completion_token_present": (
            solver_exit == 0
            and (
                "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" in sta
                or "THE ANALYSIS HAS BEEN COMPLETED" in sta
            )
        ),
    }


def increment_sequence(sta_path: Path) -> dict[str, object]:
    raw = text(sta_path)
    lines = [
        " ".join(line.split())
        for line in raw.splitlines()
        if re.match(r"^\s*\d+\s+\d+\s+", line)
    ]
    digest = hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()
    return {"records": lines, "record_count": len(lines), "sha256": digest}


def event_metrics(events: list[dict[str, str]]) -> dict[str, int]:
    accesses = [row for row in events if row.get("event") == "shared_access"]
    keys = [
        (
            row.get("variable_id"),
            row.get("operation_id"),
            row.get("routine_id"),
            row.get("shared_index"),
            row.get("rank"),
            row.get("thread"),
            row.get("step"),
            row.get("increment"),
            row.get("initialization"),
        )
        for row in accesses
    ]
    initialization = [
        row
        for row in accesses
        if row.get("variable_id") == "4"
        and row.get("operation_id") == "2"
        and row.get("initialization") == "1"
    ]
    required = {
        (str(var_id), str(op_id), str(index))
        for index in range(1, 9)
        for var_id, op_id in ((1, 1), (1, 2), (2, 1), (2, 2), (4, 2))
    }
    observed = {
        (row.get("variable_id", ""), row.get("operation_id", ""), row.get("shared_index", ""))
        for row in accesses
    }
    return {
        "duplicate_callback_events": len(keys) - len(set(keys)),
        "initialization_events": len(initialization),
        "duplicate_initialization_events": max(0, len(initialization) - 8),
        "missing_shared_state_records": len(required - observed),
        "event_conflicts": sum(row.get("event") == "conflict" for row in events),
    }


def validate(out: Path, job_id: str, solver_exit: int) -> dict[str, object]:
    failures: list[str] = []
    required = [
        "P3S_ENVIRONMENT.txt",
        "P3S_JOB_RECORD.txt",
        "P3S_CALLBACK_EVENTS.csv",
        "P3S_SHARED_ACCESS_SUMMARY.json",
        "P3S_STATE_OUTPUT.csv",
        "P3S_RF_U.csv",
        "P3S_ENERGY.csv",
        "p3s_serial.abaqus_stdout.log",
        "p3s_serial.sta",
    ]
    for name in required:
        if not (out / name).is_file():
            failures.append("missing " + name)

    summary: dict[str, object] = {}
    state: list[dict[str, str]] = []
    events: list[dict[str, str]] = []
    if (out / "P3S_SHARED_ACCESS_SUMMARY.json").is_file():
        summary = json.loads((out / "P3S_SHARED_ACCESS_SUMMARY.json").read_text(encoding="utf-8"))
    if (out / "P3S_STATE_OUTPUT.csv").is_file():
        state = csv_rows(out / "P3S_STATE_OUTPUT.csv")
    if (out / "P3S_CALLBACK_EVENTS.csv").is_file():
        events = csv_rows(out / "P3S_CALLBACK_EVENTS.csv")

    tech = technical_gates(out, solver_exit)
    for name, passed in tech.items():
        if not passed:
            failures.append(name + " is false")

    callbacks = summary.get("callbacks", {}) if isinstance(summary, dict) else {}
    callback_gates = {
        name: isinstance(callbacks, dict) and callbacks.get(name) is True
        for name in ("UEXTERNALDB", "UEL", "UMAT")
    }
    for name, passed in callback_gates.items():
        if not passed:
            failures.append(name + " callback not observed")

    ranks = summary.get("ranks", [])
    threads = summary.get("threads", [])
    unexpected_ranks = sum(rank != 0 for rank in ranks) if isinstance(ranks, list) else 1
    unexpected_threads = sum(thread != 0 for thread in threads) if isinstance(threads, list) else 1
    if ranks != [0]:
        failures.append("unexpected MPI rank set")
    if threads != [0]:
        failures.append("unexpected thread ID set")

    metrics = event_metrics(events)
    if metrics["initialization_events"] != 8:
        failures.append("initialization event count is not 8")
    for key in (
        "duplicate_callback_events",
        "duplicate_initialization_events",
        "missing_shared_state_records",
        "event_conflicts",
    ):
        if metrics[key]:
            failures.append(key + " is nonzero")
    summary_conflicts = int(summary.get("conflicting_shared_writes", 0) or 0)
    if summary_conflicts:
        failures.append("conflicting shared writes detected")

    expected_keys = {(element, 1) for element in range(1, 9)}
    observed_keys = {
        (int(row["element"]), int(row["integration_point"]))
        for row in state
        if row.get("element") and row.get("integration_point")
    }
    if observed_keys != expected_keys:
        failures.append("element/integration-point coverage is incomplete")

    phase_columns = ["SDV15_F0", "SDV15_F1", "SDV15_F2", "SDV15_F3"]
    history_columns = ["SDV16_F0", "SDV16_F1", "SDV16_F2", "SDV16_F3"]
    nonfinite = phase_bounds = phase_decreases = history_decreases = 0
    for row in state:
        phase = [float(row[name]) for name in phase_columns if finite(row.get(name))]
        history = [float(row[name]) for name in history_columns if finite(row.get(name))]
        if len(phase) != 4 or len(history) != 4:
            nonfinite += 1
            continue
        phase_bounds += sum(value < 0.0 or value > 1.0 for value in phase)
        phase_decreases += sum(b < a for a, b in zip(phase, phase[1:]))
        history_decreases += sum(b < a for a, b in zip(history, history[1:]))

    for file_name, numeric_fields in (
        ("P3S_RF_U.csv", ("U2", "RF2")),
        ("P3S_ENERGY.csv", ("ALLIE", "ALLSE", "ALLWK")),
    ):
        if (out / file_name).is_file():
            for row in csv_rows(out / file_name):
                for field in numeric_fields:
                    if not finite(row.get(field)):
                        nonfinite += 1
    if nonfinite:
        failures.append("nonfinite or missing state/RF/energy values")
    if phase_bounds:
        failures.append("phase-bound violations")
    if phase_decreases:
        failures.append("phase irreversibility violations")
    if history_decreases:
        failures.append("history decreases")

    sequence = increment_sequence(out / "p3s_serial.sta")
    (out / "P3S_INCREMENT_SEQUENCE.json").write_text(
        json.dumps(sequence, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    if sequence["record_count"] == 0:
        failures.append("increment sequence is empty")

    conflict_detected = summary_conflicts > 0 or metrics["event_conflicts"] > 0
    classification = (
        "stage_p3_serial_diagnostic_conflict_detected"
        if conflict_detected
        else ("stage_p3_serial_diagnostic_pass" if not failures else "stage_p3_serial_diagnostic_fail")
    )
    status = {
        "classification": classification,
        "P3S_ok": not failures,
        "job_id": job_id,
        "solver_exit": solver_exit,
        **tech,
        "callbacks": callback_gates,
        "expected_physical_element_coverage": len({key[0] for key in observed_keys}) / 8.0,
        "expected_integration_point_coverage": len(observed_keys) / 8.0,
        "unexpected_mpi_ranks": unexpected_ranks,
        "unexpected_thread_ids": unexpected_threads,
        "conflicting_shared_writes": summary_conflicts,
        "nonfinite_state_records": nonfinite,
        "phase_bound_violations": phase_bounds,
        "phase_irreversibility_violations": phase_decreases,
        "history_decreases": history_decreases,
        **metrics,
        "failures": failures,
    }
    (out / "P3S_STATUS.json").write_text(
        json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    marker = out / "P3S_COMPLETION.ok"
    if marker.exists():
        marker.unlink()
    if not failures:
        marker.write_text(
            "classification=stage_p3_serial_diagnostic_pass\njob_id=" + job_id + "\n",
            encoding="utf-8",
        )
    return status


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--job-id", default="unknown")
    parser.add_argument("--solver-exit", type=int, required=True)
    args = parser.parse_args()
    status = validate(args.out_dir, args.job_id, args.solver_exit)
    print(json.dumps(status, sort_keys=True))
    return 0 if status["P3S_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

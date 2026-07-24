#!/usr/bin/env python3
"""Scientific and technical gates for the uninstrumented P3-SB baseline."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from pathlib import Path


IP_COUNT_BY_TYPE = {"CPS4": 4}
TRANSFER_TOLERANCE = 1.0e-8


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def finite(value: object) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""


def parse_deck(path: Path) -> tuple[list[int], str, int]:
    labels: list[int] = []
    active = False
    element_type = ""
    for raw in text(path).splitlines():
        line = raw.strip()
        upper = line.upper()
        if line.startswith("*"):
            active = False
            compact = upper.replace(" ", "")
            if compact.startswith("*ELEMENT,") and "ELSET=UMATELEM" in compact:
                match = re.search(r"TYPE=([^,]+)", upper)
                element_type = match.group(1).strip() if match else ""
                active = True
            continue
        if active and line and not line.startswith("**"):
            labels.append(int(line.split(",", 1)[0]))
    if not labels or element_type not in IP_COUNT_BY_TYPE:
        raise ValueError("unsupported or missing visualization element block")
    return labels, element_type, IP_COUNT_BY_TYPE[element_type]


def parse_transfer(path: Path) -> dict[int, float]:
    raw = text(path)
    elem_match = re.search(r"DATA\s+D2_TRANSFER_ELEM\s*/(.*?)/", raw, re.I | re.S)
    value_match = re.search(r"DATA\s+D2_TRANSFER_H\s*/(.*?)/", raw, re.I | re.S)
    if not elem_match or not value_match:
        raise ValueError("transfer table DATA blocks missing")
    clean = lambda value: re.sub(r"(?m)^\s*\d\s*", "", value)
    elems = [int(item) for item in clean(elem_match.group(1)).split(",") if item.strip()]
    values = [
        float(item.replace("D", "E").replace("d", "e"))
        for item in clean(value_match.group(1)).split(",") if item.strip()
    ]
    if len(elems) != len(values):
        raise ValueError("transfer table lengths differ")
    return dict(zip(elems, values))


def technical_gates(out: Path, solver_exit: int) -> dict[str, bool]:
    stdout = text(out / "p3sb_baseline.abaqus_stdout.log")
    sta = text(out / "p3sb_baseline.sta")
    job_record = text(out / "P3SB_JOB_RECORD.txt")
    return {
        "abaqus_launched": "Begin Compiling Abaqus/Standard User Subroutines" in stdout,
        "fortran_compile_pass": "End Compiling Abaqus/Standard User Subroutines" in stdout,
        "fortran_link_pass": "End Linking Abaqus/Standard User Subroutines" in stdout,
        "input_processing_pass": (
            "Begin Analysis Input File Processor" in stdout
            and "End Analysis Input File Processor" in stdout
        ),
        "analysis_completed_successfully": (
            solver_exit == 0
            and (
                "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" in sta
                or "THE ANALYSIS HAS BEEN COMPLETED" in sta
                or "COMPLETED SUCCESSFULLY" in stdout
            )
        ),
        "odb_readable": "odb_readable=true" in job_record,
    }


def increment_sequence(path: Path) -> dict[str, object]:
    records = [
        " ".join(line.split())
        for line in text(path).splitlines()
        if re.match(r"^\s*\d+\s+\d+\s+", line)
    ]
    return {
        "records": records,
        "record_count": len(records),
        "sha256": hashlib.sha256("\n".join(records).encode("utf-8")).hexdigest(),
    }


def validate(
    out: Path, deck: Path, transfer_path: Path, job_id: str, solver_exit: int
) -> dict[str, object]:
    failures: list[str] = []
    required = (
        "P3SB_ENVIRONMENT.txt", "P3SB_JOB_RECORD.txt", "P3SB_STATE_OUTPUT.csv",
        "P3SB_RF_U.csv", "P3SB_ENERGY.csv", "p3sb_baseline.abaqus_stdout.log",
        "p3sb_baseline.sta",
    )
    for name in required:
        if not (out / name).is_file():
            failures.append(f"missing {name}")

    technical = technical_gates(out, solver_exit)
    for name, passed in technical.items():
        if not passed:
            failures.append(f"{name} is false")

    try:
        labels, element_type, ip_count = parse_deck(deck)
        transferred = parse_transfer(transfer_path)
    except ValueError as exc:
        failures.append(str(exc))
        labels, element_type, ip_count, transferred = [], "", 0, {}

    state = read_csv(out / "P3SB_STATE_OUTPUT.csv") if (out / "P3SB_STATE_OUTPUT.csv").is_file() else []
    expected = {(label, ip) for label in labels for ip in range(1, ip_count + 1)}
    observed = {
        (int(row["visualization_element"]), int(row["integration_point"]))
        for row in state
        if row.get("visualization_element") and row.get("integration_point")
    }
    missing_elements = set(labels) - {label for label, _ in observed}
    missing_ips = expected - observed
    if missing_elements:
        failures.append("visualization element coverage incomplete")
    if missing_ips:
        failures.append("integration-point coverage incomplete")

    phase_columns = sorted(
        (name for name in (state[0].keys() if state else []) if name.startswith("SDV15_F")),
        key=lambda name: int(name.split("_F")[1]),
    )
    history_columns = [name.replace("SDV15_", "SDV16_") for name in phase_columns]
    if not phase_columns:
        failures.append("no state frames extracted")
    nonfinite = phase_bounds = phase_decreases = history_decreases = 0
    transfer_mismatches = 0
    for row in state:
        phase = [float(row[name]) for name in phase_columns if finite(row.get(name))]
        history = [float(row[name]) for name in history_columns if finite(row.get(name))]
        if len(phase) != len(phase_columns) or len(history) != len(history_columns):
            nonfinite += 1
            continue
        phase_bounds += sum(value < 0.0 or value > 1.0 for value in phase)
        phase_decreases += sum(b + 1.0e-12 < a for a, b in zip(phase, phase[1:]))
        history_decreases += sum(b + 1.0e-12 < a for a, b in zip(history, history[1:]))
        physical = int(row["physical_element"])
        if physical not in transferred or abs(history[0] - transferred[physical]) > TRANSFER_TOLERANCE:
            transfer_mismatches += 1

    for file_name, fields in (
        ("P3SB_RF_U.csv", ("U2", "RF2")),
        ("P3SB_ENERGY.csv", ("ALLIE", "ALLSE", "ALLWK")),
    ):
        rows = read_csv(out / file_name) if (out / file_name).is_file() else []
        if not rows:
            failures.append(f"{file_name} is empty")
        for row in rows:
            nonfinite += sum(not finite(row.get(field)) for field in fields)
    for count, message in (
        (nonfinite, "nonfinite phase/history/RF/energy values"),
        (phase_bounds, "phase-bound violations"),
        (phase_decreases, "phase irreversibility violations"),
        (history_decreases, "history monotonicity violations"),
        (transfer_mismatches, "initial transfer-table mismatches"),
    ):
        if count:
            failures.append(message)

    sequence = increment_sequence(out / "p3sb_baseline.sta")
    (out / "P3SB_INCREMENT_SEQUENCE.json").write_text(
        json.dumps(sequence, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    if sequence["record_count"] == 0:
        failures.append("increment sequence is empty")

    status = {
        "classification": (
            "stage_p3sb_baseline_serial_pass"
            if not failures else "stage_p3sb_baseline_serial_fail_validation"
        ),
        "P3SB_ok": not failures,
        "job_id": job_id,
        "solver_exit": solver_exit,
        **technical,
        "expected_visualization_elements": len(labels),
        "expected_integration_points_per_element": ip_count,
        "expected_state_records": len(expected),
        "observed_state_records": len(observed),
        "missing_visualization_elements": len(missing_elements),
        "missing_integration_points": len(missing_ips),
        "nonfinite_values": nonfinite,
        "phase_bound_violations": phase_bounds,
        "phase_irreversibility_violations": phase_decreases,
        "history_monotonicity_violations": history_decreases,
        "transfer_table_mismatches": transfer_mismatches,
        "increment_records": sequence["record_count"],
        "failures": failures,
    }
    (out / "P3SB_STATUS.json").write_text(
        json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    marker = out / "P3SB_COMPLETION.ok"
    if marker.exists():
        marker.unlink()
    if not failures:
        marker.write_text(
            f"classification=stage_p3sb_baseline_serial_pass\njob_id={job_id}\n",
            encoding="utf-8",
        )
    return status


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--deck", type=Path, required=True)
    parser.add_argument("--transfer", type=Path, required=True)
    parser.add_argument("--job-id", default="unknown")
    parser.add_argument("--solver-exit", type=int, required=True)
    args = parser.parse_args()
    result = validate(args.out_dir, args.deck, args.transfer, args.job_id, args.solver_exit)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["P3SB_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

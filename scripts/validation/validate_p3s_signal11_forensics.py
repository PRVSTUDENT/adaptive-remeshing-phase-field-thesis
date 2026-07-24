#!/usr/bin/env python3
"""Offline validation for P3-S signal-11 evidence and P3-SB preparation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FORENSICS = ROOT / "results/validation/stage_p/p3s_signal11_forensics"
RAW = ROOT / "runs/hpc/stage_p/p3s_serial_diagnostic/raw_failure_evidence"
P3SB = ROOT / "models/parallelization/p3sb_baseline_eight_element_serial"
D2 = ROOT / "models/state_transfer/d2_tiny_transfer/executable"
P3S = ROOT / "models/parallelization/minimal_externaldb_commonblock_test"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    failures: list[str] = []

    required = [
        "P3S_FAILURE_FILE_MANIFEST.json",
        "P3S_FAILURE_TIMELINE.md",
        "P3S_LAST_CALLBACK.json",
        "P3S_SOURCE_CHANGE_MAP.csv",
        "P3S_HYPOTHESIS_MATRIX.csv",
        "P3S_FORENSIC_STATUS.json",
    ]
    for name in required:
        if not (FORENSICS / name).is_file():
            failures.append(f"missing forensic artifact: {name}")

    manifest = load_json(FORENSICS / "P3S_FAILURE_FILE_MANIFEST.json")
    for item in manifest["files"]:
        if item["copied"]:
            path = RAW / item.get("local_name", item["name"])
            if not path.is_file():
                failures.append(f"missing copied evidence: {item['name']}")
            elif sha256(path) != item["sha256"]:
                failures.append(f"evidence hash mismatch: {item['name']}")

    status = load_json(FORENSICS / "P3S_FORENSIC_STATUS.json")
    if status["classification"] != "stage_p3s_signal11_cause_localized":
        failures.append("unexpected forensic classification")
    if status["retry_authorized"] or status["future_test_authorized"]:
        failures.append("execution must remain unauthorized")
    if any(status[key] for key in (
        "p3t4_authorized",
        "mpi_authorized",
        "hybrid_authorized",
        "production_h1_authorized",
        "d3d_a1_reopening_authorized",
        "d3e_authorized",
    )):
        failures.append("downstream authorization found")

    pairs = [
        (P3SB / "p3sb_baseline_uel.for", D2 / "d2_tiny_transfer_uel.for"),
        (P3SB / "P3SB_baseline_serial.inp", P3S / "P3S_serial_diagnostic.inp"),
        (P3SB / "d2_transfer_table.inc", D2 / "d2_transfer_table.inc"),
    ]
    for prepared, reference in pairs:
        if not prepared.is_file() or prepared.read_bytes() != reference.read_bytes():
            failures.append(f"P3-SB is not byte-identical: {prepared.name}")

    source_lines = (P3SB / "p3sb_baseline_uel.for").read_text(
        encoding="utf-8"
    ).splitlines()
    invalid_fixed_form = [
        number
        for number, line in enumerate(source_lines, 1)
        if line and line[0] not in ("C", "c", "*", "!") and len(line) > 72
    ]
    if invalid_fixed_form:
        failures.append(f"fixed-form code exceeds column 72: {invalid_fixed_form}")

    forbidden = ("GETRANK", "GETTHREADID", "MUTEX", "KP2TRACE", "KP3ACCESS")
    baseline_text = "\n".join(source_lines).upper()
    for token in forbidden:
        if token in baseline_text:
            failures.append(f"P3-SB contains diagnostic token: {token}")

    if failures:
        print(json.dumps({"classification": "stage_p3f_static_fail", "failures": failures}, indent=2))
        return 1
    print("stage_p3f_offline_forensics_static_pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate the D3A3-R2 runtime H-state file."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


EXPECTED_ELEMENTS = 6400
EXPECTED_IPS = 4
EXPECTED_RECORDS = EXPECTED_ELEMENTS * EXPECTED_IPS


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate(path: Path, out: Path | None = None) -> dict[str, object]:
    failures: list[str] = []
    seen: set[tuple[int, int]] = set()
    duplicates = 0
    h_min = None
    h_max = None
    previous = None
    records = 0
    with path.open(encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) != 3:
                failures.append(f"invalid record: {line}")
                continue
            element = int(parts[0])
            ip = int(parts[1])
            h_value = float(parts[2])
            key = (element, ip)
            if key in seen:
                duplicates += 1
            seen.add(key)
            if element < 1 or element > EXPECTED_ELEMENTS:
                failures.append(f"element out of range: {element}")
            if ip < 1 or ip > EXPECTED_IPS:
                failures.append(f"integration point out of range: {ip}")
            if not math.isfinite(h_value):
                failures.append(f"H is not finite for {element}/{ip}")
            if h_value < -1.0e-14:
                failures.append(f"H is negative for {element}/{ip}: {h_value}")
            h_min = h_value if h_min is None else min(h_min, h_value)
            h_max = h_value if h_max is None else max(h_max, h_value)
            if previous is not None and key <= previous:
                failures.append(f"records are not strictly sorted at {element}/{ip}")
            previous = key
            records += 1

    expected = {
        (element, ip)
        for element in range(1, EXPECTED_ELEMENTS + 1)
        for ip in range(1, EXPECTED_IPS + 1)
    }
    missing = sorted(expected - seen)
    if records != EXPECTED_RECORDS:
        failures.append(f"records={records}, expected {EXPECTED_RECORDS}")
    if duplicates:
        failures.append(f"duplicates={duplicates}")
    if missing:
        failures.append(f"missing_records={len(missing)}")

    status = {
        "classification": "stage_d3a3_r2_runtime_state_validation_pass" if not failures else "stage_d3a3_r2_runtime_state_validation_fail",
        "runtime_state_ok": not failures,
        "path": str(path),
        "records": records,
        "expected_records": EXPECTED_RECORDS,
        "elements": EXPECTED_ELEMENTS,
        "integration_points_per_element": EXPECTED_IPS,
        "duplicates": duplicates,
        "missing_records": len(missing),
        "all_H_finite": not any("not finite" in failure for failure in failures),
        "all_H_nonnegative": not any("negative" in failure for failure in failures),
        "minimum_H": h_min,
        "maximum_H": h_max,
        "sha256": sha256(path),
        "failures": failures,
    }
    if out is not None:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(status, indent=2, sort_keys=True))
    return status


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("models/state_transfer/d3_interrupted_transfer/executable/d3_transfer_h.dat"))
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    status = validate(args.input, args.out)
    return 0 if status["runtime_state_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

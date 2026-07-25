#!/usr/bin/env python3
"""Compare P3-T4 state, RF-U, energy and increments to frozen P3-SM0."""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

ABS_TOL = 1.0e-12
REL_TOL = 1.0e-10


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def compare_csv(candidate: Path, reference: Path) -> dict[str, object]:
    if not candidate.is_file() or not reference.is_file():
        return {"ok": False, "reason": "missing file", "mismatches": 1}
    left, right = rows(candidate), rows(reference)
    mismatches = abs(len(left) - len(right))
    max_abs = 0.0
    for a, b in zip(left, right):
        if a.keys() != b.keys():
            mismatches += 1
            continue
        for key in a:
            try:
                av, bv = float(a[key]), float(b[key])
            except ValueError:
                mismatches += a[key] != b[key]
                continue
            delta = abs(av - bv)
            max_abs = max(max_abs, delta)
            if not math.isclose(av, bv, rel_tol=REL_TOL, abs_tol=ABS_TOL):
                mismatches += 1
    return {"ok": mismatches == 0, "mismatches": mismatches,
            "candidate_rows": len(left), "reference_rows": len(right),
            "max_abs_difference": max_abs}


def compare(candidate: Path, reference: Path) -> dict[str, object]:
    mapping = {
        "state": ("P3T4_STATE_OUTPUT.csv", "P3SM0_STATE_OUTPUT.csv"),
        "rf_u": ("P3T4_RF_U.csv", "P3SM0_RF_U.csv"),
        "energy": ("P3T4_ENERGY.csv", "P3SM0_ENERGY.csv"),
    }
    results = {
        name: compare_csv(candidate / left, reference / right)
        for name, (left, right) in mapping.items()
    }
    candidate_inc = candidate / "P3T4_INCREMENT_SEQUENCE.json"
    reference_inc = reference / "P3SM0_INCREMENT_SEQUENCE.json"
    if candidate_inc.is_file() and reference_inc.is_file():
        left = json.loads(candidate_inc.read_text(encoding="utf-8"))
        right = json.loads(reference_inc.read_text(encoding="utf-8"))
        results["increments"] = {
            "ok": left.get("records") == right.get("records"),
            "candidate_records": left.get("record_count"),
            "reference_records": right.get("record_count"),
        }
    else:
        results["increments"] = {"ok": False, "reason": "missing file"}
    result = {
        "classification": "stage_p3t4_serial_reference_comparison",
        "absolute_tolerance": ABS_TOL,
        "relative_tolerance": REL_TOL,
        "comparisons": results,
        "serial_equivalent": all(item["ok"] for item in results.values()),
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = compare(args.candidate, args.reference)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["serial_equivalent"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

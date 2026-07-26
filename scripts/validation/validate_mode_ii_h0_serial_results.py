#!/usr/bin/env python3
"""Fail-closed validation of lightweight extraction outputs for Mode-II H0 serial run."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from pathlib import Path

PHASE_LOWER_TOL = -1e-8
PHASE_UPPER_TOL = 1.0 + 1e-6
HEALING_TOL = 1e-8
HISTORY_DECREASE_TOL = 1e-10

DECK_SHA256 = "32a25380767bbb0e9e76eb55b3bb7a97d78bb75c4f86c7e8585aa2032ce2d33b"
SOURCE_SHA256 = "5decf4b1f587019d6bdd904e8ceed22175c113e070e714777cb998da428e4d8c"


def read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def parse_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise ValueError(f"missing CSV file: {path}")
    with path.open("r", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        return list(reader)


def validate_results(
    extraction_dir: Path,
    sta_path: Path | None = None,
    dat_path: Path | None = None,
    msg_path: Path | None = None,
) -> dict:
    failures: list[str] = []

    manifest_path = extraction_dir / "extraction_manifest.json"
    if not manifest_path.is_file():
        failures.append("missing extraction_manifest.json")

    summary_path = extraction_dir / "single_notch_extraction_summary.json"
    summary_data = {}
    if summary_path.is_file():
        try:
            summary_data = json.loads(summary_path.read_text(encoding="utf-8"))
        except Exception as exc:
            failures.append(f"invalid summary JSON: {exc}")
    else:
        failures.append("missing single_notch_extraction_summary.json")

    # Curve CSV
    curve_csv = extraction_dir / "rf1_u1_curve.csv"
    if not curve_csv.is_file():
        curve_csv = extraction_dir / "single_notch_rf_u_phase_summary.csv"
    curve_rows = []
    if curve_csv.is_file():
        try:
            curve_rows = parse_csv(curve_csv)
        except Exception as exc:
            failures.append(f"invalid curve CSV: {exc}")
    else:
        failures.append("missing curve CSV file")

    # Crack path CSV
    crack_csv = extraction_dir / "crack_path_sdv15_ge_0p5.csv"
    if not crack_csv.is_file():
        # search for any crack_path CSV
        candidates = list(extraction_dir.glob("crack_path_*.csv"))
        if candidates:
            crack_csv = candidates[0]
    crack_rows = []
    if crack_csv.is_file():
        try:
            crack_rows = parse_csv(crack_csv)
        except Exception as exc:
            failures.append(f"invalid crack path CSV: {exc}")
    else:
        failures.append("missing crack path CSV file")

    # Gate checks on curve rows
    max_phase = 0.0
    if curve_rows:
        for idx, row in enumerate(curve_rows):
            u_val = float(row.get("rp_u1", row.get("rp_u2", 0.0)) or 0.0)
            rf_val = float(row.get("rp_rf1", row.get("rp_rf2", 0.0)) or 0.0)
            phase_val = float(row.get("max_sdv15", 0.0) or 0.0)
            hist_val = float(row.get("max_sdv16", 0.0) or 0.0)

            if phase_val > max_phase:
                max_phase = phase_val

            if phase_val < PHASE_LOWER_TOL:
                failures.append(f"row {idx}: phase {phase_val} < lower tol {PHASE_LOWER_TOL}")
            if phase_val > PHASE_UPPER_TOL:
                failures.append(f"row {idx}: phase {phase_val} > upper tol {PHASE_UPPER_TOL}")

            # Check history non-decrease
            if idx > 0:
                prev_hist = float(curve_rows[idx - 1].get("max_sdv16", 0.0) or 0.0)
                if hist_val < prev_hist - HISTORY_DECREASE_TOL:
                    failures.append(
                        f"row {idx}: history decrease {hist_val} < prev {prev_hist}"
                    )

    if max_phase <= 0.01:
        failures.append("trivial phase evolution: max_sdv15 <= 0.01")

    # Check status from .sta if provided
    if sta_path and sta_path.is_file():
        sta_text = read_text(sta_path)
        if "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" not in sta_text:
            failures.append("analysis did not report completion in .sta")

    classification = (
        "stage_f_mode_ii_h0_serial_baseline_characterized"
        if not failures
        else "stage_f_mode_ii_h0_serial_validation_fail"
    )

    return {
        "classification": classification,
        "failures": failures,
        "max_phase_sdv15": max_phase,
        "curve_points": len(curve_rows),
        "crack_path_elements": len(crack_rows),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--extraction-dir", type=Path, required=True)
    parser.add_argument("--sta", type=Path, default=None)
    parser.add_argument("--dat", type=Path, default=None)
    parser.add_argument("--msg", type=Path, default=None)
    args = parser.parse_args()

    result = validate_results(
        args.extraction_dir,
        sta_path=args.sta,
        dat_path=args.dat,
        msg_path=args.msg,
    )

    print(json.dumps(result, indent=2, sort_keys=True))
    if result["failures"]:
        print("Mode-II H0 serial result validation failed")
        return 20
    print("Mode-II H0 serial result validation pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

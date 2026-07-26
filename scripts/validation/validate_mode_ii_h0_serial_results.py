#!/usr/bin/env python3
"""Fail-closed validation of lightweight extraction outputs for Mode-II H0 serial run."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import sys
from pathlib import Path

PHASE_LOWER_TOL = -1e-8
PHASE_UPPER_TOL = 1.0 + 1e-6

DECK_SHA256 = "32a25380767bbb0e9e76eb55b3bb7a97d78bb75c4f86c7e8585aa2032ce2d33b"
SOURCE_SHA256 = "5decf4b1f587019d6bdd904e8ceed22175c113e070e714777cb998da428e4d8c"


def read_text(path: Path | None) -> str:
    if path is None or not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def parse_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise ValueError(f"missing CSV file: {path}")
    with path.open("r", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        return list(reader)


def check_finite(val_str: str) -> bool:
    try:
        f = float(val_str)
        return math.isfinite(f)
    except (ValueError, TypeError):
        return False


def validate_results(
    extraction_dir: Path,
    sta_path: Path | None = None,
    dat_path: Path | None = None,
    msg_path: Path | None = None,
    runtime_manifest_path: Path | None = None,
    input_hash_check_path: Path | None = None,
    expected_final_disp: float = 0.010,
    final_disp_tol: float = 1e-6,
) -> dict:
    failures: list[str] = []

    # 1. Extraction manifest
    manifest_path = extraction_dir / "extraction_manifest.json"
    if not manifest_path.is_file():
        failures.append("missing extraction_manifest.json")

    # 2. Runtime manifest
    runtime_manifest_data = {}
    if runtime_manifest_path and runtime_manifest_path.is_file():
        try:
            runtime_manifest_data = json.loads(runtime_manifest_path.read_text(encoding="utf-8"))
        except Exception as exc:
            failures.append(f"invalid runtime manifest JSON: {exc}")
    elif runtime_manifest_path:
        failures.append("missing runtime manifest file")

    if runtime_manifest_data:
        cpus = runtime_manifest_data.get("cpus")
        ranks = runtime_manifest_data.get("mpi_ranks")
        threads = runtime_manifest_data.get("omp_threads")
        mp_mode = runtime_manifest_data.get("mp_mode")
        deck_hash = runtime_manifest_data.get("deck_sha256")
        source_hash = runtime_manifest_data.get("source_sha256")

        if (cpus, ranks, threads) != (1, 1, 1):
            failures.append(f"runtime cpus/ranks/threads expected 1/1/1, got {cpus}/{ranks}/{threads}")
        if mp_mode != "threads":
            failures.append(f"mp_mode expected threads, got {mp_mode}")

        if deck_hash and deck_hash.lower() != DECK_SHA256:
            failures.append(f"deck hash mismatch: expected {DECK_SHA256}, got {deck_hash}")
        if source_hash and source_hash.lower() != SOURCE_SHA256:
            failures.append(f"source hash mismatch: expected {SOURCE_SHA256}, got {source_hash}")

    # 3. Input hash check file
    if input_hash_check_path and input_hash_check_path.is_file():
        hash_check_text = read_text(input_hash_check_path)
        if "FAILED" in hash_check_text or "FAILED open or read" in hash_check_text:
            failures.append("input hash check failed")

    # 4. Curve CSV checks
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

    if curve_rows:
        if len(curve_rows) < 2:
            failures.append(f"curve contains fewer than 2 points: {len(curve_rows)}")

        u_vals = []
        rf_vals = []
        for idx, row in enumerate(curve_rows):
            u_str = row.get("rp_u1", row.get("rp_u2", ""))
            rf_str = row.get("rp_rf1", row.get("rp_rf2", ""))

            if not check_finite(u_str):
                failures.append(f"non-finite U1 at row {idx}: {u_str}")
            else:
                u_vals.append(float(u_str))

            if not check_finite(rf_str):
                failures.append(f"non-finite RF1 at row {idx}: {rf_str}")
            else:
                rf_vals.append(float(rf_str))

        if u_vals:
            final_u = abs(u_vals[-1])
            if abs(final_u - expected_final_disp) > final_disp_tol:
                failures.append(
                    f"final |U1| {final_u:.6f} not within tolerance {final_disp_tol} of expected {expected_final_disp:.6f}"
                )

    # 5. Energy history CSV
    energy_csv = extraction_dir / "energy_history.csv"
    if energy_csv.is_file():
        try:
            e_rows = parse_csv(energy_csv)
            if not e_rows:
                failures.append("energy_history.csv is empty")
            for idx, r in enumerate(e_rows):
                val_str = r.get("value", "")
                if not check_finite(val_str):
                    failures.append(f"non-finite energy at row {idx}: {r.get('variable')} = {val_str}")
        except Exception as exc:
            failures.append(f"invalid energy_history.csv: {exc}")
    else:
        failures.append("missing energy_history.csv")

    # 6. Irreversibility summary
    irrev_json = extraction_dir / "irreversibility_summary.json"
    if irrev_json.is_file():
        try:
            irrev_data = json.loads(irrev_json.read_text(encoding="utf-8"))
            phase_violations = irrev_data.get("phase_healing_violation_count", 0)
            hist_violations = irrev_data.get("history_decrease_violation_count", 0)

            if phase_violations > 0:
                failures.append(
                    f"phase healing violations detected: {phase_violations} (worst decrease: {irrev_data.get('worst_phase_decrease')})"
                )
            if hist_violations > 0:
                failures.append(
                    f"history decrease violations detected: {hist_violations} (worst decrease: {irrev_data.get('worst_history_decrease')})"
                )
        except Exception as exc:
            failures.append(f"invalid irreversibility_summary.json: {exc}")
    else:
        failures.append("missing irreversibility_summary.json")

    # 7. Phase bounds summary
    pb_json = extraction_dir / "phase_bounds_summary.json"
    if pb_json.is_file():
        try:
            pb_data = json.loads(pb_json.read_text(encoding="utf-8"))
            min_p = pb_data.get("minimum_phase", 0.0)
            max_p = pb_data.get("maximum_phase", 0.0)

            if min_p < PHASE_LOWER_TOL:
                failures.append(f"minimum phase {min_p} < lower tol {PHASE_LOWER_TOL}")
            if max_p > PHASE_UPPER_TOL:
                failures.append(f"maximum phase {max_p} > upper tol {PHASE_UPPER_TOL}")
            if max_p <= 0.01:
                failures.append(f"trivial phase evolution: maximum phase {max_p} <= 0.01")
        except Exception as exc:
            failures.append(f"invalid phase_bounds_summary.json: {exc}")
    else:
        failures.append("missing phase_bounds_summary.json")

    # 8. Crack path CSV
    candidates = list(extraction_dir.glob("crack_path_*.csv"))
    if candidates:
        crack_csv = candidates[0]
        try:
            crack_rows = parse_csv(crack_csv)
            if not crack_rows:
                failures.append("crack-path CSV is empty")
        except Exception as exc:
            failures.append(f"invalid crack-path CSV: {exc}")
    else:
        failures.append("missing crack-path CSV file")

    # 9. `.sta` check
    if sta_path and sta_path.is_file():
        sta_text = read_text(sta_path)
        if "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" not in sta_text:
            failures.append("analysis did not report completion in .sta")

    # 10. `.dat` and `.msg` log error token checks
    fatal_tokens = [
        "unresolved external",
        "undefined reference",
        "signal 11",
        "SIGSEGV",
        "negative eigenvalue",
        "zero or negative",
    ]
    for log_path, log_name in [(dat_path, ".dat"), (msg_path, ".msg")]:
        if log_path and log_path.is_file():
            txt = read_text(log_path)
            for token in fatal_tokens:
                if re.search(r"\b" + re.escape(token) + r"\b", txt, re.IGNORECASE):
                    failures.append(f"fatal token '{token}' found in {log_name}")

    classification = (
        "stage_f_mode_ii_h0_serial_baseline_characterized"
        if not failures
        else "stage_f_mode_ii_h0_serial_validation_fail"
    )

    return {
        "classification": classification,
        "failures": failures,
        "curve_points": len(curve_rows),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--extraction-dir", type=Path, required=True)
    parser.add_argument("--sta", type=Path, default=None)
    parser.add_argument("--dat", type=Path, default=None)
    parser.add_argument("--msg", type=Path, default=None)
    parser.add_argument("--runtime-manifest", type=Path, default=None)
    parser.add_argument("--input-hash-check", type=Path, default=None)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--expected-final-displacement", type=float, default=0.010)
    parser.add_argument("--final-displacement-tolerance", type=float, default=1e-6)
    args = parser.parse_args()

    result = validate_results(
        args.extraction_dir,
        sta_path=args.sta,
        dat_path=args.dat,
        msg_path=args.msg,
        runtime_manifest_path=args.runtime_manifest,
        input_hash_check_path=args.input_hash_check,
        expected_final_disp=args.expected_final_displacement,
        final_disp_tol=args.final_displacement_tolerance,
    )

    if args.output_json:
        out_path = args.output_json.resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8") as stream:
            json.dump(result, stream, indent=2, sort_keys=True)
            stream.write("\n")

    print(json.dumps(result, indent=2, sort_keys=True))
    if result["failures"]:
        print("Mode-II H0 serial result validation failed")
        return 20
    print("Mode-II H0 serial result validation pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate D3A3 static preflight or completed ingestion/hold outputs."""

import argparse
import csv
import json
import math
from pathlib import Path


DEFAULT_TOL = 1.0e-8


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def floats(rows: list[dict[str, str]], column: str) -> list[float]:
    out = []
    for row in rows:
        value = row.get(column, "")
        if value not in ("", None):
            out.append(float(value))
    return out


def metric(values: list[float]) -> dict[str, object]:
    if not values:
        return {"count": 0, "l2": None, "max_abs": None}
    return {
        "count": len(values),
        "l2": math.sqrt(sum(v * v for v in values) / len(values)),
        "max_abs": max(abs(v) for v in values),
    }


def require_file(target_dir: Path, name: str, failures: list[str]) -> Path:
    path = target_dir / name
    if not path.exists():
        failures.append(f"{name} missing")
    return path


def validate_completed(target_dir: Path, failures: list[str], tol: float) -> dict[str, object]:
    required = [
        "D3A3_STATE_BY_FRAME.csv",
        "D3A3_TRANSFER_VS_ODB.csv",
        "D3A3_INITIAL_VS_EQUILIBRATED.csv",
        "D3A3_EQUILIBRATED_VS_RELEASED.csv",
        "D3A3_RF_U.csv",
        "D3A3_ENERGY_BY_FRAME.json",
        "D3A3_RELEASE_JUMP.json",
    ]
    paths = {name: require_file(target_dir, name, failures) for name in required}
    if failures:
        return {}

    transfer = read_csv(paths["D3A3_TRANSFER_VS_ODB.csv"])
    initial_eq = read_csv(paths["D3A3_INITIAL_VS_EQUILIBRATED.csv"])
    eq_release = read_csv(paths["D3A3_EQUILIBRATED_VS_RELEASED.csv"])
    rf_u = read_csv(paths["D3A3_RF_U.csv"])
    energy = read_json(paths["D3A3_ENERGY_BY_FRAME.json"])
    release = read_json(paths["D3A3_RELEASE_JUMP.json"])

    sdv15_transfer = metric(floats(transfer, "sdv15_error"))
    sdv16_transfer = metric(floats(transfer, "sdv16_error"))
    sdv15_eq = metric(floats(initial_eq, "sdv15_delta"))
    sdv16_eq = metric(floats(initial_eq, "sdv16_delta"))
    sdv15_release = metric(floats(eq_release, "sdv15_delta"))
    sdv16_release = metric(floats(eq_release, "sdv16_delta"))

    expected_records = 6400 * 4
    if len(transfer) != expected_records:
        failures.append(f"D3A3_TRANSFER_VS_ODB.csv rows={len(transfer)}, expected {expected_records}")
    for name, data in [
        ("sdv15_transfer", sdv15_transfer),
        ("sdv16_transfer", sdv16_transfer),
    ]:
        if data["count"] != expected_records:
            failures.append(f"{name} has {data['count']} numeric rows, expected {expected_records}")
        if data["max_abs"] is None or data["max_abs"] > tol:
            failures.append(f"{name} max_abs {data['max_abs']} exceeds {tol}")
    if len(rf_u) < 3:
        failures.append("RF-U extraction has fewer than three frame rows")

    return {
        "transfer_sdv15_error": sdv15_transfer,
        "transfer_sdv16_error": sdv16_transfer,
        "initial_vs_equilibrated_sdv15_delta": sdv15_eq,
        "initial_vs_equilibrated_sdv16_delta": sdv16_eq,
        "equilibrated_vs_released_sdv15_delta": sdv15_release,
        "equilibrated_vs_released_sdv16_delta": sdv16_release,
        "rf_u_rows": len(rf_u),
        "energy": energy,
        "release_jump": release,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-dir", type=Path, default=Path("runs/hpc/stage_d3/interrupted_transfer/target_ingestion_r2"))
    parser.add_argument("--static-only", action="store_true")
    parser.add_argument("--tol", type=float, default=DEFAULT_TOL)
    args = parser.parse_args()

    failures: list[str] = []
    static_path = args.target_dir / "D3A3_STATIC_VALIDATION.json"
    if not static_path.exists():
        failures.append("D3A3_STATIC_VALIDATION.json missing")
        static = {}
    else:
        static = read_json(static_path)
        if static.get("classification") != "stage_d3a3_static_validation_pass":
            failures.append("static validation did not pass")

    completed = {} if args.static_only else validate_completed(args.target_dir, failures, args.tol)
    classification = (
        "stage_d3a3_static_validation_pass"
        if not failures and args.static_only
        else ("stage_d3a3_full_target_ingestion_pass" if not failures else "stage_d3a3_state_ingestion_fail")
    )
    status = {
        "classification": classification,
        "D3A3_ok": not failures and not args.static_only,
        "static_only": args.static_only,
        "tolerance": args.tol,
        "static": static,
        "completed": completed,
        "failures": failures,
    }
    args.target_dir.mkdir(parents=True, exist_ok=True)
    (args.target_dir / "D3A3_STATUS.json").write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if status["D3A3_ok"]:
        (args.target_dir / "D3A3.ok").write_text("stage_d3a3_full_target_ingestion_pass\n", encoding="utf-8")
    print(json.dumps(status, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())

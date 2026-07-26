#!/usr/bin/env python3
"""Fail-closed authorization/preflight checks for Stage-F Mode-II H0."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

REQUIRED_FALSE = (
    "automatic_retry_authorized",
    "threaded_execution_authorized",
    "mpi_authorized",
    "hybrid_authorized",
    "miseseri_authorized",
    "h1_authorized",
    "stage_p_reopening_authorized",
    "d3d_reopening_authorized",
    "thesis_submission_task_authorized",
)


def load_object(path: Path) -> dict:
    if not path.is_file():
        raise ValueError(f"missing file: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("JSON root must be an object")
    return data


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_authorization(path: Path, require_datacheck: bool, require_solver: bool) -> dict:
    data = load_object(path)
    if data.get("preparation_complete") is not True:
        raise ValueError("preparation_complete must be true")
    if data.get("maximum_datacheck_submissions") != 1:
        raise ValueError("maximum_datacheck_submissions must equal 1")
    if data.get("maximum_solver_submissions") != 1:
        raise ValueError("maximum_solver_submissions must equal 1")
    if not isinstance(data.get("datacheck_submissions_used"), int) or isinstance(
        data.get("datacheck_submissions_used"), bool
    ):
        raise ValueError("datacheck_submissions_used invalid")
    if not isinstance(data.get("solver_submissions_used"), int) or isinstance(
        data.get("solver_submissions_used"), bool
    ):
        raise ValueError("solver_submissions_used invalid")
    for key in REQUIRED_FALSE:
        if data.get(key) is not False:
            raise ValueError(f"{key} must remain false")

    if require_datacheck:
        if data.get("classification") not in {
            "stage_f_mode_ii_h0_datacheck_authorized",
            "stage_f_mode_ii_h0_prepared",  # rejected below unless authorized true
        }:
            # Allow only the explicit authorized classification for submission.
            pass
        if data.get("classification") != "stage_f_mode_ii_h0_datacheck_authorized":
            raise ValueError("datacheck classification must be stage_f_mode_ii_h0_datacheck_authorized")
        if data.get("datacheck_authorized") is not True:
            raise ValueError("datacheck_authorized must be true for submission")
        if data.get("datacheck_submissions_used") != 0:
            raise ValueError("datacheck already consumed")
        if data.get("solver_authorized") is not False:
            raise ValueError("solver must remain unauthorized during datacheck")
    elif require_solver:
        if data.get("classification") != "stage_f_mode_ii_h0_solver_authorized":
            raise ValueError("solver classification must be stage_f_mode_ii_h0_solver_authorized")
        if data.get("solver_authorized") is not True:
            raise ValueError("solver_authorized must be true for submission")
        if data.get("solver_submissions_used") != 0:
            raise ValueError("solver already consumed")
    else:
        if data.get("classification") not in {
            "stage_f_mode_ii_h0_prepared",
            "stage_f_mode_ii_h0_datacheck_authorized",
            "stage_f_mode_ii_h0_solver_authorized",
        }:
            raise ValueError("unexpected prepared classification")
        if data.get("classification") == "stage_f_mode_ii_h0_prepared":
            if data.get("datacheck_authorized") is not False:
                raise ValueError("datacheck must remain unauthorized in prepared state")
            if data.get("solver_authorized") is not False:
                raise ValueError("solver must remain unauthorized in prepared state")
    return data


def validate_package_hashes(package: Path) -> dict:
    deck = package / "ModeII_H0_serial.inp"
    source = package / "ModeII_H0_serial.for"
    manifest = package / "PACKAGE_MANIFEST.json"
    static = package / "STATIC_VALIDATION.json"
    for path in (deck, source, manifest, static):
        if not path.is_file():
            raise ValueError(f"missing package file: {path.name}")
    data = load_object(manifest)
    if data.get("deck", {}).get("sha256") != sha256(deck):
        raise ValueError("deck hash mismatch")
    if data.get("source", {}).get("sha256") != sha256(source):
        raise ValueError("source hash mismatch")
    static_data = load_object(static)
    if static_data.get("classification") != "stage_f_mode_ii_h0_static_pass":
        raise ValueError("static validation not passed")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authorization", type=Path, required=True)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--require-datacheck", action="store_true")
    parser.add_argument("--require-solver", action="store_true")
    args = parser.parse_args()
    try:
        if args.require_datacheck and args.require_solver:
            raise ValueError("choose only one of --require-datacheck/--require-solver")
        validate_authorization(
            args.authorization,
            require_datacheck=args.require_datacheck,
            require_solver=args.require_solver,
        )
        validate_package_hashes(args.package)
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"Mode-II H0 preflight blocked: {exc}")
        return 20
    print("Mode-II H0 preflight pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

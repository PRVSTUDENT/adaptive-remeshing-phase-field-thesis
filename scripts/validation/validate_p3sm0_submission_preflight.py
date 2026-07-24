#!/usr/bin/env python3
"""Fail-closed authorization and staging checks for P3-SM0."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


REQUIRED_FALSE = (
    "automatic_retry_authorized", "p3sm1_authorized", "p3t4_authorized",
    "mpi_authorized", "hybrid_authorized", "p4_authorized",
    "production_h1_authorized", "d3d_a1_reopening_authorized", "d3e_authorized",
)


def load_object(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise ValueError(f"missing file: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"malformed JSON: {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("JSON root must be an object")
    return data


def validate_authorization(path: Path, require_submit: bool) -> dict[str, object]:
    data = load_object(path)
    expected = (
        "stage_p3sm0_minimal_callback_serial_authorized"
        if require_submit else "stage_p3sm0_minimal_callback_serial_prepared"
    )
    if data.get("classification") != expected:
        raise ValueError("unexpected authorization classification")
    if data.get("p3sm0_preparation_complete") is not True:
        raise ValueError("P3-SM0 preparation incomplete")
    if data.get("maximum_p3sm0_submissions") != 1:
        raise ValueError("maximum_p3sm0_submissions must equal 1")
    used = data.get("p3sm0_submissions_used")
    if not isinstance(used, int) or isinstance(used, bool) or used != 0:
        raise ValueError("P3-SM0 submission count consumed or invalid")
    if require_submit and data.get("p3sm0_submission_authorized") is not True:
        raise ValueError("P3-SM0 submission not authorized")
    for key in REQUIRED_FALSE:
        if data.get(key) is not False:
            raise ValueError(f"{key} must remain false")
    return data


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_manifest(path: Path, stage_root: Path) -> dict[str, object]:
    data = load_object(path)
    mapping = {
        "deck_sha256": stage_root / "P3SM0_serial.inp",
        "source_sha256": stage_root / "p3sm0_minimal_callback.for",
        "transfer_sha256": stage_root / "d2_transfer_table.inc",
    }
    for key, candidate in mapping.items():
        expected = data.get(key)
        if not isinstance(expected, str) or len(expected) != 64:
            raise ValueError(f"invalid staged hash: {key}")
        if not candidate.is_file() or sha256(candidate) != expected:
            raise ValueError(f"staged hash mismatch: {candidate.name}")
    if data.get("compute_git_required") is not False:
        raise ValueError("compute_git_required must be false")
    return data


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--authorization", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--stage-root", type=Path)
    parser.add_argument("--require-submit", action="store_true")
    args = parser.parse_args()
    try:
        validate_authorization(args.authorization, args.require_submit)
        if bool(args.manifest) != bool(args.stage_root):
            raise ValueError("--manifest and --stage-root must be supplied together")
        if args.manifest and args.stage_root:
            validate_manifest(args.manifest, args.stage_root)
    except ValueError as exc:
        print(f"P3-SM0 preflight blocked: {exc}")
        return 20
    print("P3-SM0 preflight pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

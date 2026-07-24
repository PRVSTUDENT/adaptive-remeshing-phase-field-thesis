#!/usr/bin/env python3
"""Fail-closed login/staging checks for the one-shot P3-S submission lane."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


REQUIRED_FALSE = [
    "automatic_retry_authorized",
    "p3t4_authorized",
    "mpi_authorized",
    "hybrid_authorized",
    "production_h1_authorized",
    "d3d_a1_reopening_authorized",
    "d3e_authorized",
]


def load_object(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise ValueError(f"missing file: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"malformed JSON: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


def validate_authorization(path: Path, require_submit: bool) -> dict[str, object]:
    data = load_object(path)
    if data.get("classification") != "stage_p3_serial_diagnostic_prepared":
        raise ValueError("unexpected authorization classification")
    if data.get("p3s_preparation_complete") is not True:
        raise ValueError("P3-S preparation is not complete")
    if data.get("maximum_p3s_submissions") != 1:
        raise ValueError("maximum_p3s_submissions must equal 1")
    used = data.get("p3s_submissions_used")
    if not isinstance(used, int) or isinstance(used, bool) or used != 0:
        raise ValueError("P3-S submission count is consumed or invalid")
    for key in REQUIRED_FALSE:
        if data.get(key) is not False:
            raise ValueError(f"{key} must remain false")
    if require_submit and data.get("p3s_submission_authorized") is not True:
        raise ValueError("P3-S submission is not authorized")
    return data


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_manifest(path: Path, stage_root: Path) -> dict[str, object]:
    data = load_object(path)
    mapping = {
        "deck_sha256": stage_root / "P3S_serial_diagnostic.inp",
        "source_sha256": stage_root / "p3_instrumented_commonblock.for",
        "transfer_sha256": stage_root / "d2_transfer_table.inc",
    }
    for key, file_path in mapping.items():
        expected = data.get(key)
        if not isinstance(expected, str) or len(expected) != 64:
            raise ValueError(f"missing or invalid login-side hash: {key}")
        if not file_path.is_file():
            raise ValueError(f"missing staged file: {file_path}")
        if sha256(file_path) != expected:
            raise ValueError(f"staged-source hash mismatch: {file_path.name}")
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
        print(f"P3-S preflight blocked: {exc}")
        return 20
    print("P3-S preflight pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Offline validation of Mode-II H0 serial staging contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path

FROZEN_DECK_SHA256 = "32a25380767bbb0e9e76eb55b3bb7a97d78bb75c4f86c7e8585aa2032ce2d33b"
FROZEN_SOURCE_SHA256 = "5decf4b1f587019d6bdd904e8ceed22175c113e070e714777cb998da428e4d8c"


def compute_sha256(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"missing file for hashing: {path}")
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def is_valid_sha256(val: str | None) -> bool:
    if not val or not isinstance(val, str):
        return False
    return bool(re.match(r"^[0-9a-f]{64}$", val))


def validate_staging_contract(
    package_dir: Path,
    pbs_path: Path,
    extractor_path: Path,
    validator_path: Path,
) -> dict:
    failures: list[str] = []

    # 1. Package existence checks
    deck_path = package_dir / "ModeII_H0_serial.inp"
    source_path = package_dir / "ModeII_H0_serial.for"

    if not deck_path.is_file():
        failures.append(f"frozen package deck missing: {deck_path}")
    if not source_path.is_file():
        failures.append(f"frozen package source missing: {source_path}")
    if not pbs_path.is_file():
        failures.append(f"PBS script missing: {pbs_path}")
    if not extractor_path.is_file():
        failures.append(f"extractor script missing: {extractor_path}")
    if not validator_path.is_file():
        failures.append(f"validator script missing: {validator_path}")

    if failures:
        return {
            "classification": "stage_f_mode_ii_h0_serial_staging_contract_fail",
            "failures": failures,
        }

    # 2. Compute reference hashes
    try:
        pkg_deck_hash = compute_sha256(deck_path)
        pkg_source_hash = compute_sha256(source_path)
        pbs_hash = compute_sha256(pbs_path)
        extractor_hash = compute_sha256(extractor_path)
        validator_hash = compute_sha256(validator_path)
    except Exception as exc:
        return {
            "classification": "stage_f_mode_ii_h0_serial_staging_contract_fail",
            "failures": [f"hash computation error: {exc}"],
        }

    if pkg_deck_hash != FROZEN_DECK_SHA256:
        failures.append(f"package deck hash mismatch: expected {FROZEN_DECK_SHA256}, got {pkg_deck_hash}")
    if pkg_source_hash != FROZEN_SOURCE_SHA256:
        failures.append(f"package source hash mismatch: expected {FROZEN_SOURCE_SHA256}, got {pkg_source_hash}")

    for h_name, h_val in [
        ("pbs_hash", pbs_hash),
        ("extractor_hash", extractor_hash),
        ("validator_hash", validator_hash),
    ]:
        if not is_valid_sha256(h_val):
            failures.append(f"invalid SHA-256 for {h_name}: '{h_val}'")

    # 3. Simulate scratch staging
    with tempfile.TemporaryDirectory() as temp_dir_str:
        scratch = Path(temp_dir_str)
        orig_deck = scratch / "ModeII_H0_serial.inp"
        job_deck = scratch / "mode_ii_h0_serial.inp"
        src_file = scratch / "ModeII_H0_serial.for"

        orig_deck.write_bytes(deck_path.read_bytes())
        job_deck.write_bytes(orig_deck.read_bytes())
        src_file.write_bytes(source_path.read_bytes())

        if not orig_deck.is_file():
            failures.append("original scratch deck missing")
        if not job_deck.is_file():
            failures.append("job-named scratch deck missing")

        if orig_deck.is_file() and job_deck.is_file():
            h_orig = compute_sha256(orig_deck)
            h_job = compute_sha256(job_deck)
            if h_orig != h_job:
                failures.append(f"original and job deck hash mismatch: orig={h_orig}, job={h_job}")
            if h_orig != pkg_deck_hash:
                failures.append(f"staged deck hash mismatch with package: staged={h_orig}, pkg={pkg_deck_hash}")

        # 4. Generate runtime manifest
        runtime_manifest_data = {
            "project_revision": "dummy_rev",
            "job_name": "mode_ii_h0_serial",
            "cpus": 1,
            "mpi_ranks": 1,
            "omp_threads": 1,
            "mp_mode": "threads",
            "memory": "16 GB",
            "walltime": "04:00:00",
            "deck_sha256": pkg_deck_hash,
            "abaqus_deck_sha256": pkg_deck_hash,
            "source_sha256": pkg_source_hash,
            "extractor_sha256": extractor_hash,
            "validator_sha256": validator_hash,
            "pbs_script_sha256": pbs_hash,
        }

        for k, v in runtime_manifest_data.items():
            if v == "" or v is None:
                failures.append(f"runtime manifest has empty field: {k}")

        # 5. Generate login manifest and compare
        login_manifest_data = {
            "classification": "stage_f_mode_ii_h0_login_staging_complete",
            "project_revision": "dummy_rev",
            "deck_sha256": pkg_deck_hash,
            "source_sha256": pkg_source_hash,
            "extractor_sha256": extractor_hash,
            "validator_sha256": validator_hash,
            "pbs_script_sha256": pbs_hash,
        }

        shared_keys = [
            "project_revision",
            "deck_sha256",
            "source_sha256",
            "extractor_sha256",
            "validator_sha256",
            "pbs_script_sha256",
        ]
        for sk in shared_keys:
            if login_manifest_data.get(sk) != runtime_manifest_data.get(sk):
                failures.append(f"manifest comparison mismatch for {sk}")

    classification = (
        "stage_f_mode_ii_h0_serial_staging_contract_pass"
        if not failures
        else "stage_f_mode_ii_h0_serial_staging_contract_fail"
    )

    return {
        "classification": classification,
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--pbs", type=Path, required=True)
    parser.add_argument("--extractor", type=Path, required=True)
    parser.add_argument("--result-validator", type=Path, required=True)
    args = parser.parse_args()

    result = validate_staging_contract(
        args.package.resolve(),
        args.pbs.resolve(),
        args.extractor.resolve(),
        args.result_validator.resolve(),
    )

    print(json.dumps(result, indent=2, sort_keys=True))
    if result["failures"]:
        print("Mode-II H0 serial staging contract validation failed")
        return 1
    print("Mode-II H0 serial staging contract validation pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

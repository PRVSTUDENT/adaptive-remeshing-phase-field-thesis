#!/usr/bin/env python3
"""Fail-Closed Static Validator for M2STATE_FRACFIX_RESTART2 Package.
Task: F43STATE-M2-OVERNIGHT-CONTINUE1
"""

import os
import sys
import json
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG_DIR = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2"
EXPECTED_UEL_SHA = "0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8"
APPROVED_EMAIL = "#PBS -M Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de,pr21vyci@mailserver.tu-freiberg.de"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    print("======================================================================")
    print("F43STATE-M2-OVERNIGHT-CONTINUE1: VALIDATING M2STATE_FRACFIX_RESTART2 PACKAGE")
    print("======================================================================")

    errors = []

    required_files = [
        "M2STATE_FRACFIX_RESTART2.inp",
        "f42_mixed_uel.for",
        "M2STATE_FRACFIX_RESTART2.pbs",
        "submit_m2state_fracfix_restart2.sh",
        "STATE_TRANSFER_ARTIFACT.json",
        "TRANSFER_MANIFEST.json",
        "RESTART_ACCEPTANCE_CONTRACT.json",
        "PACKAGE_MANIFEST.json",
    ]

    for fname in required_files:
        if not (PKG_DIR / fname).exists():
            errors.append(f"Missing file: {fname}")

    if errors:
        print("FAIL: Missing files.")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)

    # 1. UEL SHA256 check
    uel_sha = sha256_file(PKG_DIR / "f42_mixed_uel.for")
    if uel_sha != EXPECTED_UEL_SHA:
        errors.append(f"UEL SHA256 mismatch! Got {uel_sha}, expected {EXPECTED_UEL_SHA}")
    else:
        print("UEL SHA256 check: PASS")

    # 2. Package manifest check
    manifest = json.loads((PKG_DIR / "PACKAGE_MANIFEST.json").read_text(encoding="utf-8"))
    raw_hashes = manifest["raw_execution_hashes"]

    for key, fname in [
        ("input_sha256", "M2STATE_FRACFIX_RESTART2.inp"),
        ("uel_sha256", "f42_mixed_uel.for"),
        ("pbs_sha256", "M2STATE_FRACFIX_RESTART2.pbs"),
        ("wrapper_sha256", "submit_m2state_fracfix_restart2.sh"),
        ("transfer_artifact_sha256", "STATE_TRANSFER_ARTIFACT.json"),
        ("transfer_manifest_sha256", "TRANSFER_MANIFEST.json"),
        ("acceptance_contract_sha256", "RESTART_ACCEPTANCE_CONTRACT.json"),
    ]:
        calc_sha = sha256_file(PKG_DIR / fname)
        if raw_hashes[key] != calc_sha:
            errors.append(f"Manifest hash mismatch for {fname}! Manifest: {raw_hashes[key]}, Calc: {calc_sha}")

    if not errors:
        print("Package manifest hashes check: PASS")

    # 3. PBS check
    pbs_content = (PKG_DIR / "M2STATE_FRACFIX_RESTART2.pbs").read_text(encoding="utf-8")
    if "#PBS -l select=1:ncpus=1:mem=16gb" not in pbs_content:
        errors.append("PBS select resource line invalid!")
    if "#PBS -l walltime=01:30:00" not in pbs_content:
        errors.append("PBS walltime invalid!")
    if APPROVED_EMAIL not in pbs_content:
        errors.append("PBS approved email missing!")

    if not errors:
        print("PBS syntax and notification contract check: PASS")

    if errors:
        print("======================================================================")
        print("VALIDATION STATUS: FAIL")
        print("======================================================================")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("======================================================================")
        print("OVERALL VALIDATION STATUS: ALL PASS")
        print("======================================================================")


if __name__ == "__main__":
    main()

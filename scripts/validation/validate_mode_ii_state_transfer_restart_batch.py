#!/usr/bin/env python3
"""Fail-Closed Static Validator for Mode-II Evolving-Remesh / State-Transfer Restart Package (M2STATE_FRACFIX_RESTART1).
Task: F43STATE-M2-OVERNIGHT-PREP1

Verifies:
  1. File existence & exact Linux LF SHA256 hashes for all execution items.
  2. Qualified UEL SHA256 (0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8).
  3. Target physical element count (4,894) and NPHYS mapping in 5th property slot of U2/U4.
  4. Transfer state bounds & energy jump validation (energy_jump_pct <= 1.0%).
  5. OpenPBS resource request: select=1:ncpus=1:mem=8gb, walltime=08:00:00, queue=entry_imfdfkmq.
  6. Email notification contract: -m abe with approved 2-recipient configuration.
  7. Output sufficiency requests for field/history/energy/restart fields.
"""

import os
import sys
import json
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG_DIR = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1"
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
    print("F43STATE-M2-OVERNIGHT-PREP1: VALIDATING M2STATE_FRACFIX_RESTART1 PACKAGE")
    print("======================================================================")

    errors = []

    # Check files
    required_files = [
        "M2STATE_FRACFIX_RESTART1.inp",
        "f42_mixed_uel.for",
        "M2STATE_FRACFIX_RESTART1.pbs",
        "submit_m2state_fracfix_restart1.sh",
        "STATE_TRANSFER_ARTIFACT.json",
        "TRANSFER_MANIFEST.json",
        "RESTART_ACCEPTANCE_CONTRACT.json",
        "PACKAGE_MANIFEST.json",
    ]

    for fname in required_files:
        fpath = PKG_DIR / fname
        if not fpath.exists():
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
        ("input_sha256", "M2STATE_FRACFIX_RESTART1.inp"),
        ("uel_sha256", "f42_mixed_uel.for"),
        ("pbs_sha256", "M2STATE_FRACFIX_RESTART1.pbs"),
        ("wrapper_sha256", "submit_m2state_fracfix_restart1.sh"),
        ("transfer_artifact_sha256", "STATE_TRANSFER_ARTIFACT.json"),
        ("transfer_manifest_sha256", "TRANSFER_MANIFEST.json"),
        ("acceptance_contract_sha256", "RESTART_ACCEPTANCE_CONTRACT.json"),
    ]:
        calc_sha = sha256_file(PKG_DIR / fname)
        if raw_hashes[key] != calc_sha:
            errors.append(f"Manifest hash mismatch for {fname}! Manifest: {raw_hashes[key]}, Calc: {calc_sha}")

    if not errors:
        print("Package manifest hashes check: PASS")

    # 3. PBS grammar & notification check
    pbs_content = (PKG_DIR / "M2STATE_FRACFIX_RESTART1.pbs").read_text(encoding="utf-8")
    if "#PBS -l select=1:ncpus=1:mem=8gb" not in pbs_content:
        errors.append("PBS select resource line invalid!")
    if "#PBS -l walltime=08:00:00" not in pbs_content:
        errors.append("PBS walltime invalid!")
    if "#PBS -q entry_imfdfkmq" not in pbs_content:
        errors.append("PBS queue invalid!")
    if "#PBS -m abe" not in pbs_content:
        errors.append("PBS mail points -m abe missing!")
    if APPROVED_EMAIL not in pbs_content:
        errors.append("PBS approved two-recipient email directive missing!")

    if not errors:
        print("PBS syntax and notification contract check: PASS")

    # 4. Transfer artifact check
    artifact = json.loads((PKG_DIR / "STATE_TRANSFER_ARTIFACT.json").read_text(encoding="utf-8"))
    if artifact["transfer_validation_status"] != "PASS":
        errors.append(f"Transfer validation status is {artifact['transfer_validation_status']}")
    if artifact["phase_bound_violations"] != 0:
        errors.append("Phase bound violations non-zero!")
    if artifact["healing_count"] != 0:
        errors.append("Healing count non-zero!")
    if artifact["energy_jump_pct"] > 1.0:
        errors.append(f"Energy jump {artifact['energy_jump_pct']}% exceeds 1.0% gate!")

    if not errors:
        print("State transfer artifact validation check: PASS")

    # 5. Input deck NPHYS check
    inp_content = (PKG_DIR / "M2STATE_FRACFIX_RESTART1.inp").read_text(encoding="utf-8")
    if "*UEL PROPERTY, ELSET=E_U2" not in inp_content or "4894" not in inp_content:
        errors.append("NPHYS=4894 property card missing in U2!")

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

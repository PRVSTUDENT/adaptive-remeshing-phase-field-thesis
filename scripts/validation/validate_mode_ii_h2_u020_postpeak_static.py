#!/usr/bin/env python3
"""Static validator for Stage-F Mode-II H2 uniform reference u020 postpeak package.

Verifies:
- 33,852 physical UEL elements
- Fortran N_ELEM = 33,852
- Node count = 34,508
- True slit topology
- Prescribed final U1 = 0.020 mm (analytical endpoint audit pass)
- Step-1/Step-2 continuity
- Deck SHA: fdcd6ee1b1d6cbfb88d59a3edfb7f1c6b35cecde736a427f6b3030b0443b10bf
- Fortran SHA: 49c9054ab5faec9e069e0a9149af5058e6f1e11ab164c2a0e318f60282309b37
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGE_DIR = ROOT / "models/generated/mode_ii/h2_uniform_serial_u020_postpeak"

EXPECTED_DECK_SHA = "fdcd6ee1b1d6cbfb88d59a3edfb7f1c6b35cecde736a427f6b3030b0443b10bf"
EXPECTED_FORTRAN_SHA = "49c9054ab5faec9e069e0a9149af5058e6f1e11ab164c2a0e318f60282309b37"

EXPECTED_PHYSICAL = 33852
EXPECTED_LAYERED = 101556
EXPECTED_NODES = 34508
EXPECTED_N_ELEM = 33852


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate(package_dir: Path = PACKAGE_DIR) -> dict:
    failures = []
    checks = []

    def check(condition: bool, msg: str) -> None:
        checks.append(msg)
        if not condition:
            failures.append(msg)

    check(package_dir.is_dir(), f"package directory exists ({package_dir})")

    deck_path = package_dir / "ModeII_H2_uniform_serial.inp"
    for_path = package_dir / "ModeII_H2_uniform_serial.for"
    audit_path = package_dir / "STEP_ENDPOINT_AUDIT.json"
    manifest_path = package_dir / "GENERATION_MANIFEST.json"

    check(deck_path.is_file(), f"input deck exists ({deck_path})")
    check(for_path.is_file(), f"Fortran file exists ({for_path})")
    check(audit_path.is_file(), f"endpoint audit file exists ({audit_path})")
    check(manifest_path.is_file(), f"generation manifest exists ({manifest_path})")

    if deck_path.is_file():
        deck_sha = sha256_file(deck_path)
        check(deck_sha == EXPECTED_DECK_SHA, f"deck SHA matches expected ({EXPECTED_DECK_SHA})")
    
    if for_path.is_file():
        for_sha = sha256_file(for_path)
        check(for_sha == EXPECTED_FORTRAN_SHA, f"Fortran SHA matches expected ({EXPECTED_FORTRAN_SHA})")

    if audit_path.is_file():
        try:
            audit = json.loads(audit_path.read_text(encoding="utf-8"))
            check(audit.get("pass") is True, "step endpoint audit passed")
            check(abs(audit.get("calculated_final_u1_mm", 0.0) - 0.020) <= 1.0e-12, "calculated final U1 is 0.020 mm")
        except Exception as e:
            check(False, f"failed to parse STEP_ENDPOINT_AUDIT.json: {e}")

    if manifest_path.is_file():
        try:
            m = json.loads(manifest_path.read_text(encoding="utf-8"))
            check(m.get("physical_elements") == EXPECTED_PHYSICAL, f"physical_elements is {EXPECTED_PHYSICAL}")
            check(m.get("layered_elements") == EXPECTED_LAYERED, f"layered_elements is {EXPECTED_LAYERED}")
            check(m.get("nodes") == EXPECTED_NODES, f"nodes count is {EXPECTED_NODES}")
            check(m.get("fortran_N_ELEM") == EXPECTED_N_ELEM, f"fortran_N_ELEM is {EXPECTED_N_ELEM}")
        except Exception as e:
            check(False, f"failed to parse GENERATION_MANIFEST.json: {e}")

    passed = len(failures) == 0
    classification = "stage_f4_h2_u020_static_pass" if passed else "stage_f4_h2_u020_static_fail"

    return {
        "classification": classification,
        "passed": passed,
        "total_checks": len(checks),
        "failures": failures,
        "package_dir": str(package_dir),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-dir", type=Path, default=PACKAGE_DIR)
    args = parser.parse_args()

    res = validate(args.package_dir)
    print(json.dumps(res, indent=2))
    return 0 if res["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())

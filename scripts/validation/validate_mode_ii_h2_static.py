#!/usr/bin/env python3
"""Static validator for Stage F Candidate Job A: Mode-II H2 uniform reference package."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGE_DIR = ROOT / "models/generated/mode_ii/h2_uniform_serial"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_h2_static(package_dir: Path = PACKAGE_DIR) -> dict:
    failures = []
    checks = []

    def check(condition: bool, msg: str) -> None:
        checks.append(msg)
        if not condition:
            failures.append(msg)

    check(package_dir.is_dir(), f"package directory exists ({package_dir.relative_to(ROOT)})")

    out_inp = package_dir / "ModeII_H2_uniform_serial.inp"
    out_for = package_dir / "ModeII_H2_uniform_serial.for"
    manifest_json = package_dir / "GENERATION_MANIFEST.json"

    check(out_inp.is_file(), f"H2 deck exists ({out_inp.name})")
    check(out_for.is_file(), f"H2 Fortran code exists ({out_for.name})")
    check(manifest_json.is_file(), f"Manifest JSON exists ({manifest_json.name})")

    deck_text = out_inp.read_text(encoding="utf-8") if out_inp.is_file() else ""
    for_text = out_for.read_text(encoding="utf-8") if out_for.is_file() else ""

    # Header check
    check("Mode-II pure shear H2 uniform serial" in deck_text, "Deck header contains Stage-F Mode-II H2 description")
    # Amplitude check: 0.020 mm target
    check("0.02" in deck_text, "Deck contains 0.020 mm target displacement in Amp-2")
    # Equation check: top, 1, 1 / RP, 1, -1
    check("top, 1, 1." in deck_text and "RP, 1, -1." in deck_text, "Deck contains pure-shear U1 equation coupling")
    # Fortran N_ELEM check
    check("N_ELEM=33852" in for_text, "Fortran UEL code declares N_ELEM=33852")

    passed = len(failures) == 0

    return {
        "job_name": "mode_ii_h2_uniform_serial",
        "passed": passed,
        "total_checks": len(checks),
        "failures": failures,
        "deck_sha256": sha256_file(out_inp) if out_inp.is_file() else "",
        "fortran_sha256": sha256_file(out_for) if out_for.is_file() else "",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-dir", type=Path, default=PACKAGE_DIR)
    args = parser.parse_args()

    res = validate_h2_static(args.package_dir)
    print(json.dumps(res, indent=2))
    return 0 if res["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())

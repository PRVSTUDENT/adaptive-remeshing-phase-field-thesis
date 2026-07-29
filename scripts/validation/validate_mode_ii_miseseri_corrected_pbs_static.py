#!/usr/bin/env python3
"""Static validator for Stage-F Mode-II corrected MISESERI PBS package.

Verifies:
- 3,930 CPE4 plane-strain elements
- 3,999 nodes
- 15 coincident slit-face node pairs along true slit
- Assembly-level All_elem set
- Target displacement U1 = 0.001 mm
- MISESERI, MISESAVG, S, E, EVOL, U, RF field output requests
- Deck SHA: a927b8317ff9e20bfa84dd669a2577b095e69d1bf1c343b81b158a83fd075ea2
- Unique Abaqus job name: ModeII_MISESERI_corrected_pbs
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGE_DIR = ROOT / "models/generated/mode_ii/miseseri_preanalysis_corrected_pbs"

EXPECTED_DECK_SHA = "a927b8317ff9e20bfa84dd669a2577b095e69d1bf1c343b81b158a83fd075ea2"
EXPECTED_PHYSICAL = 3930
EXPECTED_NODES = 3999
EXPECTED_SLIT_PAIRS = 15


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

    deck_path = package_dir / "ModeII_MISESERI_preanalysis.inp"
    manifest_path = package_dir / "GENERATION_MANIFEST.json"

    check(deck_path.is_file(), f"input deck exists ({deck_path})")
    check(manifest_path.is_file(), f"generation manifest exists ({manifest_path})")

    if deck_path.is_file():
        deck_sha = sha256_file(deck_path)
        check(deck_sha == EXPECTED_DECK_SHA, f"deck SHA matches expected ({EXPECTED_DECK_SHA})")

        text = deck_path.read_text(encoding="utf-8")
        check(re.search(r"\*Element,\s*type=CPE4", text, re.IGNORECASE) is not None, "CPE4 plane-strain element type specified")
        check(re.search(r"\*Elset,\s*elset=All_elem", text, re.IGNORECASE) is not None, "assembly-level All_elem set present")
        check("MISESERI" in text and "MISESAVG" in text, "MISESERI and MISESAVG output requests present")

    pbs_path = ROOT / "scripts/hpc/stage_f/06_mode_ii_miseseri_corrected_pbs.pbs"
    check(pbs_path.is_file(), f"PBS script exists ({pbs_path})")
    if pbs_path.is_file():
        pbs_text = pbs_path.read_text(encoding="utf-8")
        check('JOBNAME="ModeII_MISESERI_corrected_pbs"' in pbs_text, "PBS script specifies unique job name ModeII_MISESERI_corrected_pbs")

    if manifest_path.is_file():
        try:
            m = json.loads(manifest_path.read_text(encoding="utf-8"))
            check(m.get("physical_elements") == EXPECTED_PHYSICAL, f"physical_elements is {EXPECTED_PHYSICAL}")
            check(m.get("nodes") == EXPECTED_NODES, f"nodes count is {EXPECTED_NODES}")
            check(m.get("slit_coincident_pairs") == EXPECTED_SLIT_PAIRS, f"slit_coincident_pairs is {EXPECTED_SLIT_PAIRS}")
            check(m.get("target_u1_mm") == 0.001, "target_u1_mm is 0.001")
        except Exception as e:
            check(False, f"failed to parse GENERATION_MANIFEST.json: {e}")

    passed = len(failures) == 0
    classification = "stage_f4_miseseri_pbs_static_pass" if passed else "stage_f4_miseseri_pbs_static_fail"

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

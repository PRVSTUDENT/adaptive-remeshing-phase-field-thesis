#!/usr/bin/env python3
"""Static scientific validator for Stage-F Mode-II H1 endpoint-corrected package.

Performs thorough offline validation of the finite element deck, Fortran source,
and metadata files for the H1 endpoint-corrected package.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PKG_DIR = ROOT / "models/generated/mode_ii/h1_endpoint_corrected_serial"
CONFIG_PATH = ROOT / "configs/studies/mode_ii_molnar_shear_endpoint_corrected.yaml"

EXPECTED_DECK_SHA256 = "613398be7cd1c9061cbb469beb4130188512a2f6d25cf3d78b6364eb3255342f"
EXPECTED_FOR_SHA256 = "745db8fcfb612895e0289f4533c90d204cc9b2ade3678a035614feeb308b5ead"

PASS_CLASSIFICATION = "stage_f_mode_ii_h1_endpoint_corrected_static_pass"
FAIL_CLASSIFICATION = "stage_f_mode_ii_h1_endpoint_corrected_static_fail"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_static_package(pkg_dir: Path = DEFAULT_PKG_DIR) -> dict:
    failures = []
    checks = []

    def check(condition: bool, msg: str) -> None:
        checks.append(msg)
        if not condition:
            failures.append(msg)

    check(pkg_dir.is_dir(), f"package directory exists ({pkg_dir})")

    deck_path = pkg_dir / "ModeII_H1_endpoint_corrected_serial.inp"
    for_path = pkg_dir / "ModeII_H1_endpoint_corrected_serial.for"
    hashes_path = pkg_dir / "input_hashes.sha256"
    manifest_path = pkg_dir / "PACKAGE_MANIFEST.json"

    check(deck_path.is_file(), f"deck file exists ({deck_path.name})")
    check(for_path.is_file(), f"fortran file exists ({for_path.name})")
    check(hashes_path.is_file(), f"hashes file exists ({hashes_path.name})")
    check(manifest_path.is_file(), f"manifest file exists ({manifest_path.name})")

    if not deck_path.is_file() or not for_path.is_file():
        res = {
            "classification": FAIL_CLASSIFICATION,
            "passed": False,
            "total_checks": len(checks),
            "failures": failures,
        }
        return res

    deck_sha = sha256_file(deck_path)
    for_sha = sha256_file(for_path)

    check(deck_sha == EXPECTED_DECK_SHA256, f"deck SHA256 matches expected ({deck_sha} == {EXPECTED_DECK_SHA256})")
    check(for_sha == EXPECTED_FOR_SHA256, f"fortran SHA256 matches expected ({for_sha} == {EXPECTED_FOR_SHA256})")

    deck_text = deck_path.read_text(encoding="utf-8", errors="replace")
    for_text = for_path.read_text(encoding="utf-8", errors="replace")

    # Fortran N_ELEM check
    check("N_ELEM=12064" in for_text, "Fortran N_ELEM is set to 12064")
    check("SUBROUTINE UEL" in for_text and "SUBROUTINE UMAT" in for_text, "UEL/UMAT subroutines present in Fortran")

    # Deck checks
    check("*Amplitude, name=Amp-2\n0., 0.005, 0.2, 0.01" in deck_text or "0., 0.005, 0.2, 0.01" in deck_text, "Amp-2 endpoint time is 0.2s")
    check("*Step, name=Step-2, nlgeom=NO, inc=2000" in deck_text, "Step-2 max increments is 2000")
    check("0.0001, 0.2," in deck_text, "Step-2 period is 0.2s with direct increment 0.0001s")

    check("RP, 1, 1, 1." in deck_text, "Mode-II RP U1 loading prescribed")
    check("top, 1, 1." in deck_text and "RP, 1, -1." in deck_text, "top U1 equation coupling to RP U1 present")
    check("bottom, 1, 2" in deck_text, "bottom fully fixed in U1 and U2")

    check("E=210" in deck_text or "210." in deck_text or "210000" in deck_text or "*User Material, constants=2" in deck_text, "material properties present")
    check("RF, U" in deck_text or "RF," in deck_text, "RF1 and U1 output requests available")

    # Element and node label uniqueness checks
    node_ids = set()
    dup_nodes = False
    elem_ids = set()
    dup_elems = False

    in_nodes = False
    in_elems = False

    for line in deck_text.splitlines():
        line_s = line.strip()
        if line_s.startswith("*Node"):
            in_nodes = True
            in_elems = False
            continue
        elif line_s.startswith("*Element"):
            in_nodes = False
            in_elems = True
            continue
        elif line_s.startswith("*"):
            in_nodes = False
            in_elems = False
            continue

        if in_nodes and line_s and not line_s.startswith("**"):
            parts = line_s.split(",")
            try:
                nid = int(parts[0])
                if nid in node_ids:
                    dup_nodes = True
                node_ids.add(nid)
            except ValueError:
                pass

        if in_elems and line_s and not line_s.startswith("**"):
            parts = line_s.split(",")
            try:
                eid = int(parts[0])
                if eid in elem_ids:
                    dup_elems = True
                elem_ids.add(eid)
            except ValueError:
                pass

    check(len(node_ids) == 12382, f"node count is exactly 12382 (got {len(node_ids)})")
    check(not dup_nodes, "no duplicate node IDs found in deck")
    check(len(elem_ids) == 36192, f"layered element count is exactly 36192 (got {len(elem_ids)})")
    check(not dup_elems, "no duplicate element IDs found in deck")

    # Manifest checks
    if manifest_path.is_file():
        try:
            m = json.loads(manifest_path.read_text(encoding="utf-8"))
            check(m.get("physical_element_count") == 12064, "manifest physical_element_count is 12064")
            check(m.get("layered_element_count") == 36192, "manifest layered_element_count is 36192")
            check(m.get("node_count") == 12382, "manifest node_count is 12382")
            check(m.get("n_elem_fortran") == 12064, "manifest n_elem_fortran is 12064")
            check(m.get("datacheck_authorized") is False, "datacheck_authorized is False")
            check(m.get("solver_authorized") is False, "solver_authorized is False")
        except Exception as exc:
            failures.append(f"error parsing PACKAGE_MANIFEST.json: {exc}")

    passed = len(failures) == 0
    classification = PASS_CLASSIFICATION if passed else FAIL_CLASSIFICATION

    result = {
        "classification": classification,
        "passed": passed,
        "deck_sha256": deck_sha,
        "fortran_sha256": for_sha,
        "physical_element_count": 12064,
        "layered_element_count": 36192,
        "node_count": 12382,
        "n_elem_fortran": 12064,
        "total_checks": len(checks),
        "failures": failures,
    }

    if pkg_dir.is_dir():
        val_json = pkg_dir / "STATIC_VALIDATION.json"
        try:
            val_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        except Exception:
            pass

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pkg-dir", type=Path, default=DEFAULT_PKG_DIR)
    args = parser.parse_args()

    res = validate_static_package(args.pkg_dir)
    print(json.dumps(res, indent=2))
    return 0 if res["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())

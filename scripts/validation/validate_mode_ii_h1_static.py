#!/usr/bin/env python3
"""Static scientific validator for Stage-F Mode-II H1 uniform reference package."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PKG_DIR = ROOT / "models/generated/mode_ii/h1_uniform_serial"
CONFIG_PATH = ROOT / "configs/studies/mode_ii_molnar_shear_h1.yaml"

PASS_CLASSIFICATION = "stage_f_mode_ii_h1_uniform_static_pass"
FAIL_CLASSIFICATION = "stage_f_mode_ii_h1_uniform_static_fail"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_static_package(pkg_dir: Path = DEFAULT_PKG_DIR, config_path: Path = CONFIG_PATH) -> dict:
    failures = []
    checks = []

    def check(condition: bool, msg: str) -> None:
        checks.append(msg)
        if not condition:
            failures.append(msg)

    check(pkg_dir.is_dir(), f"package directory exists: {pkg_dir}")
    check(config_path.is_file(), f"study configuration exists: {config_path}")

    deck_path = pkg_dir / "ModeII_H1_uniform_serial.inp"
    for_path = pkg_dir / "ModeII_H1_uniform_serial.for"
    hashes_path = pkg_dir / "input_hashes.sha256"
    manifest_path = pkg_dir / "GENERATION_MANIFEST.json"
    mesh_quality_path = pkg_dir / "MESH_QUALITY.json"
    benchmark_def_path = pkg_dir / "BENCHMARK_DEFINITION.md"

    for p, name in [
        (deck_path, "deck"),
        (for_path, "fortran"),
        (hashes_path, "input_hashes"),
        (manifest_path, "manifest"),
        (mesh_quality_path, "mesh_quality"),
        (benchmark_def_path, "benchmark_definition"),
    ]:
        check(p.is_file(), f"required file exists: {name} ({p.name})")

    if not deck_path.is_file() or not for_path.is_file():
        result = {
            "classification": FAIL_CLASSIFICATION,
            "passed": False,
            "total_checks": len(checks),
            "failures": failures,
        }
        return result

    deck_text = deck_path.read_text(encoding="utf-8", errors="replace")
    for_text = for_path.read_text(encoding="utf-8", errors="replace")

    # 1. Deck checks
    check("*Amplitude, name=Amp-2\n0., 0.005, 0.2, 0.01" in deck_text or "0., 0.005, 0.2, 0.01" in deck_text, "Amp-2 endpoint time is 0.2s")
    check("*Step, name=Step-2, nlgeom=NO, inc=2000" in deck_text, "Step-2 max increments is 2000")
    check("0.0001, 0.2," in deck_text, "Step-2 period is 0.2s with direct increment 0.0001s")

    check("RP, 1, 1, 1." in deck_text, "Mode-II pure shear RP U1 prescribed")
    check("top, 1, 1." in deck_text and "RP, 1, -1." in deck_text, "Mode-II top U1 equation coupling to RP U1 present")
    check("bottom, 1, 2" in deck_text, "bottom fully fixed in U1 and U2")

    # 2. Fortran checks
    check("N_ELEM=12064" in for_text, "Fortran N_ELEM is set to 12064")
    check("SUBROUTINE UEL" in for_text and "SUBROUTINE UMAT" in for_text, "UEL/UMAT subroutine signatures present")

    # 3. Hash integrity
    deck_sha = sha256_file(deck_path)
    for_sha = sha256_file(for_path)

    if hashes_path.is_file():
        h_text = hashes_path.read_text(encoding="utf-8")
        check(deck_sha in h_text, "input_hashes.sha256 matches deck SHA-256")
        check(for_sha in h_text, "input_hashes.sha256 matches Fortran SHA-256")

    # 4. Manifest checks
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
            failures.append(f"error parsing GENERATION_MANIFEST.json: {exc}")

    # 5. Mesh quality checks
    if mesh_quality_path.is_file():
        try:
            mq = json.loads(mesh_quality_path.read_text(encoding="utf-8"))
            check(mq.get("negative_jacobian_count") == 0, "negative_jacobian_count is 0")
            check(mq.get("positive_orientation_fraction") == 1.0, "positive_orientation_fraction is 1.0")
            check(abs(mq.get("local_target_h_mm", 0) - 0.0025) < 1e-6, "local_target_h_mm is 0.0025 mm")
        except Exception as exc:
            failures.append(f"error parsing MESH_QUALITY.json: {exc}")

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

#!/usr/bin/env python3
"""Static scientific validator for Stage-F Mode-II H1 endpoint sweep packages."""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SWEEP_DIR = ROOT / "models/generated/mode_ii/h1_endpoint_sweep"

PASS_CLASSIFICATION = "stage_f_mode_ii_h1_endpoint_sweep_static_pass"
FAIL_CLASSIFICATION = "stage_f_mode_ii_h1_endpoint_sweep_static_fail"

VARIANTS = {
    "u015": {
        "job_name": "m2h1_u015",
        "target_u1_mm": 0.015,
        "step2_period_s": 0.4,
        "step2_max_inc": 4000,
    },
    "u020": {
        "job_name": "m2h1_u020",
        "target_u1_mm": 0.020,
        "step2_period_s": 0.6,
        "step2_max_inc": 6000,
    },
    "u030": {
        "job_name": "m2h1_u030",
        "target_u1_mm": 0.030,
        "step2_period_s": 1.0,
        "step2_max_inc": 10000,
    },
    "u040": {
        "job_name": "m2h1_u040",
        "target_u1_mm": 0.040,
        "step2_period_s": 1.4,
        "step2_max_inc": 14000,
    },
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_variant_package(variant_key: str, sweep_dir: Path = DEFAULT_SWEEP_DIR) -> dict:
    vinfo = VARIANTS[variant_key]
    job_name = vinfo["job_name"]
    target_u1 = vinfo["target_u1_mm"]
    period_s = vinfo["step2_period_s"]
    max_inc = vinfo["step2_max_inc"]

    v_dir = sweep_dir / variant_key
    failures = []
    checks = []

    def check(condition: bool, msg: str) -> None:
        checks.append(msg)
        if not condition:
            failures.append(msg)

    check(v_dir.is_dir(), f"variant directory exists: {v_dir}")

    deck_path = v_dir / f"{job_name}.inp"
    for_path = v_dir / f"{job_name}.for"
    hashes_path = v_dir / "input_hashes.sha256"
    manifest_path = v_dir / "GENERATION_MANIFEST.json"
    pkg_report_path = v_dir / "PACKAGE_REPORT.md"

    for p, name in [
        (deck_path, "deck"),
        (for_path, "fortran"),
        (hashes_path, "input_hashes"),
        (manifest_path, "manifest"),
        (pkg_report_path, "package_report"),
    ]:
        check(p.is_file(), f"required file exists: {name} ({p.name})")

    if not deck_path.is_file() or not for_path.is_file():
        return {
            "variant": variant_key,
            "passed": False,
            "total_checks": len(checks),
            "failures": failures,
        }

    deck_text = deck_path.read_text(encoding="utf-8", errors="replace")
    for_text = for_path.read_text(encoding="utf-8", errors="replace")

    # 1. Deck checks
    check(
        f"0., 0.005, {period_s:.1f}, {target_u1:.3f}" in deck_text
        or f"0., 0.005, {period_s:.1f}, {target_u1:.4f}" in deck_text,
        f"Amp-2 table contains period {period_s:.1f}s and target U1 {target_u1:.3f}mm",
    )
    check(f"INC={max_inc}" in deck_text, f"Step-2 max increments is {max_inc}")
    check(
        f"0.0001, {period_s:.1f}" in deck_text or f"0.0001,{period_s:.1f}" in deck_text,
        f"Step-2 period is {period_s:.1f}s with direct increment 0.0001s",
    )

    check("RP, 1, 1, 1." in deck_text, "Mode-II pure shear RP U1 prescribed")
    check(
        "top, 1, 1." in deck_text and "RP, 1, -1." in deck_text,
        "Mode-II top U1 equation coupling to RP U1 present",
    )
    check("bottom, 1, 2" in deck_text, "bottom fully fixed in U1 and U2")
    check("bottoml, 1, 1" not in deck_text, "redundant bottoml BC removed")
    check("topl, 1, 1" not in deck_text, "redundant topl BC removed")

    # 2. Fortran checks
    check("N_ELEM=12064" in for_text, "Fortran N_ELEM is set to 12064")
    check(
        "SUBROUTINE UEL" in for_text and "SUBROUTINE UMAT" in for_text,
        "UEL/UMAT subroutine signatures present",
    )

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
            check(abs(m.get("target_u1_mm", 0) - target_u1) < 1e-6, f"manifest target_u1_mm is {target_u1}")
        except Exception as exc:
            failures.append(f"error parsing GENERATION_MANIFEST.json: {exc}")

    passed = len(failures) == 0

    result = {
        "variant": variant_key,
        "job_name": job_name,
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

    if v_dir.is_dir():
        val_json = v_dir / "STATIC_VALIDATION.json"
        try:
            val_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        except Exception:
            pass

    return result


def validate_all_sweep_packages(sweep_dir: Path = DEFAULT_SWEEP_DIR) -> dict:
    variant_results = {}
    all_passed = True
    total_checks = 0

    for vkey in VARIANTS:
        res = validate_variant_package(vkey, sweep_dir)
        variant_results[vkey] = res
        if not res["passed"]:
            all_passed = False
        total_checks += res.get("total_checks", 0)

    classification = PASS_CLASSIFICATION if all_passed else FAIL_CLASSIFICATION
    summary = {
        "classification": classification,
        "all_passed": all_passed,
        "total_checks": total_checks,
        "variant_results": variant_results,
    }

    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sweep-dir", type=Path, default=DEFAULT_SWEEP_DIR)
    args = parser.parse_args()

    summary = validate_all_sweep_packages(args.sweep_dir)
    print(json.dumps(summary, indent=2))
    return 0 if summary["all_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Result validator for Stage-F Mode-II MISESERI pre-analysis PBS runs.

Evaluates extracted MISESERI CSV and summary JSON files against criteria:
- total_elements = 3930
- positive recovery error (miseseri_max > 0)
- final displacement U1 within tolerance of 0.001 mm
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

PASS_CLASSIFICATION = "official_corrected_pbs_validation_pass"
FAIL_CLASSIFICATION = "stage_f4_miseseri_preanalysis_validation_fail"


def validate_results(
    evidence_dir: Path,
    abaqus_return_code: int = 0,
    exporter_return_code: int = 0,
    expected_u1_target: float = 0.001,
    u1_tolerance: float = 1e-4,
) -> dict:
    failures = []
    checks = []

    def check(condition: bool, msg: str) -> None:
        checks.append(msg)
        if not condition:
            failures.append(msg)

    # Return codes
    check(abaqus_return_code == 0, f"Abaqus return code is 0 (got {abaqus_return_code})")
    check(exporter_return_code == 0, f"Exporter return code is 0 (got {exporter_return_code})")

    check(evidence_dir.is_dir(), f"evidence directory exists ({evidence_dir})")
    extracted_dir = evidence_dir / "extracted" if (evidence_dir / "extracted").is_dir() else evidence_dir

    elem_csv = extracted_dir / "miseseri_preanalysis_elements.csv"
    tech_json = extracted_dir / "MISESERI_TECHNICAL_SUMMARY.json"

    check(elem_csv.is_file(), f"element CSV file exists ({elem_csv})")
    check(tech_json.is_file(), f"technical summary JSON exists ({tech_json})")

    if tech_json.is_file():
        try:
            with tech_json.open("r", encoding="utf-8") as f:
                summary = json.load(f)

            n_elems = summary.get("instance_elements", summary.get("total_elements", 0))
            n_rows = summary.get("n_csv_rows", 0)
            check(n_elems == 3930, f"instance_elements is 3930 (got {n_elems})")
            check(n_rows == 3930, f"n_csv_rows is 3930 (got {n_rows})")

            miseseri_max = summary.get("miseseri_max", 0.0)
            check(math.isfinite(miseseri_max) and miseseri_max > 0.0, f"miseseri_max is finite and positive (got {miseseri_max})")
            check(summary.get("all_finite") is True, "all extracted values are finite")
            check(summary.get("has_positive_nonzero") is True, "at least one MISESERI value is strictly positive")

            present = summary.get("field_present", {})
            for field in ("MISESERI", "MISESAVG", "S", "E", "EVOL", "U", "RF"):
                check(present.get(field) is True, f"required field {field} is present")

            final_u1 = summary.get("U1_final", summary.get("u1_mm", 0.0))
            u1_err = abs(final_u1 - expected_u1_target)
            check(u1_err <= u1_tolerance, f"final U1 is within {u1_tolerance} mm of target {expected_u1_target} mm (got {final_u1})")

        except Exception as e:
            check(False, f"failed to parse MISESERI_TECHNICAL_SUMMARY.json: {e}")

    passed = len(failures) == 0
    classification = PASS_CLASSIFICATION if passed else FAIL_CLASSIFICATION

    return {
        "classification": classification,
        "passed": passed,
        "total_checks": len(checks),
        "failures": failures,
        "evidence_dir": str(evidence_dir),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Stage-F Mode-II MISESERI pre-analysis results")
    parser.add_argument("--evidence-dir", type=Path, required=True, help="Path to evidence directory")
    parser.add_argument("--abaqus-return-code", type=int, default=0, help="Abaqus process return code")
    parser.add_argument("--exporter-return-code", type=int, default=0, help="Exporter script return code")
    parser.add_argument("--expected-u1-target", type=float, default=0.001, help="Expected U1 target in mm")
    parser.add_argument("--out-json", type=Path, default=None, help="Output path for validation JSON")
    args = parser.parse_args()

    result = validate_results(
        evidence_dir=args.evidence_dir,
        abaqus_return_code=args.abaqus_return_code,
        exporter_return_code=args.exporter_return_code,
        expected_u1_target=args.expected_u1_target,
    )

    out_json = args.out_json or (args.evidence_dir / "VALIDATION_RESULTS.json")
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with out_json.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, sort_keys=True)
        f.write("\n")

    print(f"Validation status: {'PASS' if result['passed'] else 'FAIL'}")
    print(f"Classification: {result['classification']}")

    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())

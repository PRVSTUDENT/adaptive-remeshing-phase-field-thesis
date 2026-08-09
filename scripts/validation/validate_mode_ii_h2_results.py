#!/usr/bin/env python3
"""Result validator for Stage-F Mode-II H2 uniform reference serial runs.

Evaluates extracted result files against scientific acceptance criteria.
Target displacement: U1 = 0.020 mm.
"""


import argparse
import csv
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "configs/studies/mode_ii_molnar_shear_endpoint_corrected.yaml"

PASS_CLASSIFICATION = "stage_f_mode_ii_h2_uniform_serial_pass"
FAIL_CLASSIFICATION = "stage_f_mode_ii_h2_uniform_serial_validation_fail"


def validate_results(
    evidence_dir: Path,
    abaqus_return_code: int = 0,
    extractor_return_code: int = 0,
    config_path: Path = CONFIG_PATH,
    expected_u1_target: float = 0.007,
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
    check(extractor_return_code == 0, f"Extractor return code is 0 (got {extractor_return_code})")

    check(evidence_dir.is_dir(), f"evidence directory exists ({evidence_dir})")

    extracted_dir = evidence_dir / "extracted" if (evidence_dir / "extracted").is_dir() else evidence_dir

    rf1_u1_csv = extracted_dir / "rf1_u1_curve.csv"
    h2_summary_json = extracted_dir / "H2_EXTRACTION_SUMMARY.json"

    final_u1 = None
    max_rf1 = None

    # Parse H2_EXTRACTION_SUMMARY.json if present
    summary_data = {}
    if h2_summary_json.is_file():
        try:
            with h2_summary_json.open("r", encoding="utf-8") as f:
                summary_data = json.load(f)
                check(summary_data.get("completed_cleanly", False), "Analysis completed cleanly in .sta")
                final_u1 = summary_data.get("final_u1")
                max_rf1 = summary_data.get("peak_rf1")
                d_max = summary_data.get("damage_max")
                check(d_max is not None and d_max >= 0.0, f"Phase damage d_max is finite non-negative (got {d_max})")
                check(d_max is not None and d_max <= 1.01, f"Phase damage d_max <= 1.01 (got {d_max})")
                check(
                    summary_data.get("irreversibility_satisfied") is True,
                    "Framewise maximum-damage irreversibility check passed",
                )
        except Exception as exc:
            check(False, f"Failed to parse H2_EXTRACTION_SUMMARY.json: {exc}")
    else:
        check(False, f"H2_EXTRACTION_SUMMARY.json exists in {extracted_dir}")

    # Parse rf1_u1_curve.csv if present
    if rf1_u1_csv.is_file():
        try:
            with rf1_u1_csv.open("r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                check(len(rows) > 0, "RF1-U1 curve CSV contains data rows")
                if rows and final_u1 is None:
                    last_row = rows[-1]
                    for k in ["u1", "U1", "rp_u1", "RP_U1"]:
                        if k in last_row and last_row[k] != "":
                            final_u1 = abs(float(last_row[k]))
                            break
        except Exception as exc:
            check(False, f"Failed to parse rf1_u1_curve.csv: {exc}")

    # Validate final target displacement
    if final_u1 is not None:
        check(
            abs(final_u1 - expected_u1_target) <= u1_tolerance,
            f"Final U1 displacement {final_u1:.6f} mm is within {u1_tolerance} mm of target {expected_u1_target:.6f} mm",
        )
    else:
        check(False, "Could not determine final U1 displacement")

    passed = len(failures) == 0
    classification = PASS_CLASSIFICATION if passed else FAIL_CLASSIFICATION

    return {
        "classification": classification,
        "passed": passed,
        "checks_passed": len(checks) - len(failures),
        "total_checks": len(checks),
        "failures": failures,
        "summary": {
            "final_u1_mm": final_u1,
            "peak_rf1_kN": max_rf1,
            "expected_u1_mm": expected_u1_target,
            "u1_tolerance_mm": u1_tolerance,
            "extracted_data": summary_data,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Stage-F Mode-II H2 uniform reference results")
    parser.add_argument("--evidence-dir", type=Path, required=True, help="Path to evidence directory")
    parser.add_argument("--abaqus-return-code", type=int, default=0, help="Abaqus process return code")
    parser.add_argument("--extractor-return-code", type=int, default=0, help="Extractor script return code")
    parser.add_argument("--expected-u1-target", type=float, default=0.020, help="Expected U1 target displacement in mm")
    parser.add_argument("--out-json", type=Path, default=None, help="Output path for validation JSON")
    args = parser.parse_args()

    result = validate_results(
        evidence_dir=args.evidence_dir,
        abaqus_return_code=args.abaqus_return_code,
        extractor_return_code=args.extractor_return_code,
        expected_u1_target=args.expected_u1_target,
    )

    out_json = args.out_json or (args.evidence_dir / "VALIDATION_RESULTS.json")
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with out_json.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, sort_keys=True)
        f.write("\n")

    print(f"Validation status: {'PASS' if result['passed'] else 'FAIL'}")
    print(f"Classification: {result['classification']}")
    if result["failures"]:
        print("Failures:")
        for fail_msg in result["failures"]:
            print(f"  - {fail_msg}")

    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())

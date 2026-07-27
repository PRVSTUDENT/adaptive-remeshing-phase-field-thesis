#!/usr/bin/env python3
"""Result validator for Stage-F Mode-II H0 endpoint-corrected serial runs.

Evaluates extracted result files against scientific acceptance criteria.
Target displacement: U1 = 0.010 mm. Crack path must be non-empty.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "configs/studies/mode_ii_molnar_shear_endpoint_corrected.yaml"

PASS_CLASSIFICATION = "stage_f_mode_ii_h0_endpoint_corrected_serial_baseline_characterized"
FAIL_CLASSIFICATION = "stage_f_mode_ii_h0_endpoint_corrected_serial_validation_fail"


def validate_results(
    evidence_dir: Path,
    abaqus_return_code: int = 0,
    extractor_return_code: int = 0,
    config_path: Path = CONFIG_PATH,
    expected_u1_target: float = 0.010,
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

    # Check extracted files
    energy_csv = extracted_dir / "energy_history.csv"
    crack_csv = extracted_dir / "sdv14_sdv15_sdv16_contours.csv"

    check(energy_csv.is_file(), f"energy history CSV exists ({energy_csv.name})")

    # Read energy history / RF-U data
    final_u1 = None
    max_rf1 = None
    if energy_csv.is_file():
        try:
            with energy_csv.open("r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                check(len(rows) > 0, "energy history CSV contains data rows")
                if rows:
                    last_row = rows[-1]

                    # Parse U1
                    u1_val = None
                    for k in ["rp_u1", "U1", "u1", "RP_U1"]:
                        if k in last_row and last_row[k] != "":
                            u1_val = float(last_row[k])
                            break
                    if u1_val is not None:
                        final_u1 = abs(u1_val)
                        check(
                            abs(final_u1 - expected_u1_target) <= u1_tolerance,
                            f"final |U1| equals target {expected_u1_target} mm within tol {u1_tolerance} (got {final_u1:.6f} mm)",
                        )
                    else:
                        failures.append("could not parse rp_u1 from energy history CSV")

                    # Check finite energies & RF1
                    for r in rows:
                        for key, val_str in r.items():
                            if val_str != "":
                                try:
                                    v = float(val_str)
                                    if math.isnan(v) or math.isinf(v):
                                        failures.append(f"non-finite value {v} found for {key}")
                                        break
                                except ValueError:
                                    pass
        except Exception as exc:
            failures.append(f"error reading energy history CSV: {exc}")

    # Check crack path CSV
    crack_rows_count = 0
    max_sdv15 = 0.0
    if crack_csv.is_file():
        try:
            with crack_csv.open("r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                c_rows = list(reader)
                crack_rows_count = len(c_rows)
                for cr in c_rows:
                    if "sdv15" in cr and cr["sdv15"] != "":
                        try:
                            max_sdv15 = max(max_sdv15, float(cr["sdv15"]))
                        except ValueError:
                            pass
        except Exception as exc:
            failures.append(f"error reading crack path CSV: {exc}")

    check(crack_rows_count > 0, f"crack-path CSV is non-empty (got {crack_rows_count} rows)")
    check(max_sdv15 >= 0.5, f"maximum damage sdv15 reaches threshold >= 0.5 (got {max_sdv15:.4f})")

    passed = len(failures) == 0
    classification = PASS_CLASSIFICATION if passed else FAIL_CLASSIFICATION

    result = {
        "classification": classification,
        "passed": passed,
        "abaqus_return_code": abaqus_return_code,
        "extractor_return_code": extractor_return_code,
        "final_u1_mm": final_u1,
        "expected_u1_target_mm": expected_u1_target,
        "max_sdv15": max_sdv15,
        "crack_path_rows": crack_rows_count,
        "total_checks": len(checks),
        "failures": failures,
    }

    # Write VALIDATION_RESULTS.json only if directory is writable evidence directory
    if evidence_dir.is_dir():
        val_json = evidence_dir / "VALIDATION_RESULTS.json"
        try:
            val_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        except Exception:
            pass

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence_dir", type=Path)
    parser.add_argument("--abaqus-rc", type=int, default=0)
    parser.add_argument("--extractor-rc", type=int, default=0)
    args = parser.parse_args()

    res = validate_results(args.evidence_dir, args.abaqus_rc, args.extractor_rc)
    print(json.dumps(res, indent=2))
    return 0 if res["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())

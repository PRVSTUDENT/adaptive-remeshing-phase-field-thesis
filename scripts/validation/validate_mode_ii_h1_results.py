#!/usr/bin/env python3
"""Result validator for Stage-F Mode-II H1 uniform reference and endpoint sweep serial runs.

Evaluates extracted result files against technical and scientific acceptance criteria.
"""

import argparse
import csv
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "configs/studies/mode_ii_molnar_shear_h1.yaml"


def validate_results(
    evidence_dir: Path,
    abaqus_return_code: int = 0,
    extractor_return_code: int = 0,
    config_path: Path = CONFIG_PATH,
    expected_u1_target: float | None = None,
    u1_tolerance: float = 1e-4,
    damage_upper_warn_tol: float = 1.0001,
    damage_upper_fail_tol: float = 1.01,
    damage_lower_fail_tol: float = -1e-4,
    output_json_path: Path | None = None,
) -> dict:
    failures = []
    warnings = []
    checks = []

    def check(condition: bool, msg: str) -> None:
        checks.append(msg)
        if not condition:
            failures.append(msg)

    # Technical execution checks
    check(abaqus_return_code == 0, f"Abaqus return code is 0 (got {abaqus_return_code})")
    check(extractor_return_code == 0, f"Extractor return code is 0 (got {extractor_return_code})")
    check(evidence_dir.is_dir(), f"evidence directory exists ({evidence_dir})")

    extracted_dir = evidence_dir / "extracted" if (evidence_dir / "extracted").is_dir() else evidence_dir

    rf1_u1_csv = extracted_dir / "rf1_u1_curve.csv"
    energy_csv = extracted_dir / "energy_history.csv"
    phase_summary_json = extracted_dir / "phase_bounds_summary.json"
    irrev_json = extracted_dir / "irreversibility_summary.json"
    resource_json = extracted_dir / "resource_summary.json"

    crack_csv = None
    for candidate in [
        extracted_dir / "crack_path_sdv15_ge_0p5.csv",
        extracted_dir / "sdv14_sdv15_sdv16_contours.csv",
    ]:
        if candidate.is_file():
            crack_csv = candidate
            break

    u1_vals = []
    rf1_vals = []
    sdv15_curve_vals = []

    final_u1 = None
    max_rf1 = None
    u1_at_max_rf1 = None
    final_rf1 = None
    pct_force_drop = 0.0
    initial_stiffness = None
    u1_at_first_d05 = None
    max_sdv15_curve = None

    # Parse rf1_u1_curve.csv if present
    if rf1_u1_csv.is_file():
        try:
            with rf1_u1_csv.open("r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                check(len(rows) > 0, "RF1-U1 curve CSV contains data rows")
                for r in rows:
                    u_val = None
                    rf_val = None
                    sdv_val = None

                    for k in ["rp_u1", "U1", "u1", "RP_U1"]:
                        if k in r and r[k] != "":
                            try:
                                u_val = abs(float(r[k]))
                            except ValueError:
                                pass
                            break

                    for k in ["rp_rf1", "RF1", "rf1", "RP_RF1"]:
                        if k in r and r[k] != "":
                            try:
                                rf_val = abs(float(r[k]))
                            except ValueError:
                                pass
                            break

                    for k in ["max_sdv15", "sdv15", "SDV15"]:
                        if k in r and r[k] != "":
                            try:
                                sdv_val = float(r[k])
                            except ValueError:
                                pass
                            break

                    if u_val is not None and rf_val is not None:
                        u1_vals.append(u_val)
                        rf1_vals.append(rf_val)
                    if sdv_val is not None:
                        sdv15_curve_vals.append(sdv_val)
                        if sdv_val >= 0.5 and u1_at_first_d05 is None and u_val is not None:
                            u1_at_first_d05 = u_val

                if u1_vals and rf1_vals:
                    final_u1 = u1_vals[-1]
                    final_rf1 = rf1_vals[-1]
                    max_rf1 = max(rf1_vals)
                    max_idx = rf1_vals.index(max_rf1)
                    u1_at_max_rf1 = u1_vals[max_idx]

                    if max_rf1 > 0:
                        pct_force_drop = max(0.0, (max_rf1 - final_rf1) / max_rf1 * 100.0)

                    # Initial stiffness calculation (U1 <= 0.002 mm)
                    early_k = [rf / u for u, rf in zip(u1_vals, rf1_vals) if 0 < u <= 0.002]
                    if early_k:
                        initial_stiffness = sum(early_k) / len(early_k)

                if sdv15_curve_vals:
                    max_sdv15_curve = max(sdv15_curve_vals)

        except Exception as exc:
            failures.append(f"error reading RF1-U1 curve CSV: {exc}")

    # Check target displacement match if expected_u1_target provided
    if expected_u1_target is not None:
        if final_u1 is not None:
            check(
                abs(final_u1 - expected_u1_target) <= u1_tolerance,
                f"final |U1| equals target {expected_u1_target} mm within tol {u1_tolerance} (got {final_u1:.6f} mm)",
            )
        else:
            failures.append("could not parse U1 from rf1_u1_curve.csv")

    # Check energy history CSV for finite values if present and non-empty
    if energy_csv.is_file():
        try:
            with energy_csv.open("r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                if rows:
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

    # Read phase bounds summary JSON
    max_sdv15 = None
    min_sdv15 = None
    if phase_summary_json.is_file():
        try:
            summary_data = json.loads(phase_summary_json.read_text(encoding="utf-8"))
            if "maximum_phase" in summary_data:
                max_sdv15 = float(summary_data["maximum_phase"])
            if "minimum_phase" in summary_data:
                min_sdv15 = float(summary_data["minimum_phase"])
        except Exception as exc:
            failures.append(f"error reading phase_bounds_summary.json: {exc}")

    if max_sdv15 is None and max_sdv15_curve is not None:
        max_sdv15 = max_sdv15_curve

    if max_sdv15 is not None:
        if math.isnan(max_sdv15) or math.isinf(max_sdv15):
            failures.append(f"maximum damage sdv15 is non-finite ({max_sdv15})")
        elif max_sdv15 > damage_upper_fail_tol:
            failures.append(f"maximum damage sdv15 exceeds upper bound tolerance {damage_upper_fail_tol} (got {max_sdv15:.6f})")
        elif max_sdv15 > damage_upper_warn_tol:
            warnings.append("damage_upper_bound_small_overshoot")
    else:
        failures.append("could not parse maximum phase damage (sdv15)")

    if min_sdv15 is not None:
        if math.isnan(min_sdv15) or math.isinf(min_sdv15):
            failures.append(f"minimum damage sdv15 is non-finite ({min_sdv15})")
        elif min_sdv15 < damage_lower_fail_tol:
            failures.append(f"minimum damage sdv15 below lower bound tolerance {damage_lower_fail_tol} (got {min_sdv15:.6f})")

    # Check irreversibility summary if present
    history_decrease_violations = 0
    if irrev_json.is_file():
        try:
            irrev_data = json.loads(irrev_json.read_text(encoding="utf-8"))
            if "history_decrease_violation_count" in irrev_data:
                history_decrease_violations = int(irrev_data["history_decrease_violation_count"])
                check(
                    history_decrease_violations == 0,
                    f"history decrease violation count is 0 (got {history_decrease_violations})",
                )
        except Exception as exc:
            failures.append(f"error reading irreversibility_summary.json: {exc}")

    # Check spatial crack path CSV
    crack_rows_count = 0
    if crack_csv is not None and crack_csv.is_file():
        try:
            with crack_csv.open("r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                c_rows = list(reader)
                crack_rows_count = len(c_rows)
        except Exception as exc:
            failures.append(f"error reading crack path CSV: {exc}")

    # Resource usage metrics
    walltime_s = None
    cputime_s = None
    peak_mem_kb = None
    total_increments = None
    if resource_json.is_file():
        try:
            rdata = json.loads(resource_json.read_text(encoding="utf-8"))
            walltime_s = rdata.get("walltime_seconds")
            cputime_s = rdata.get("cpu_time_seconds")
            peak_mem_kb = rdata.get("peak_memory_kb")
            total_increments = rdata.get("total_increments")
        except Exception:
            pass

    # Technical validity passed if zero technical failures
    technical_pass = (len(failures) == 0)

    # Classify physical state separately
    if not technical_pass:
        physical_classification = "stage_f_mode_ii_h1_technical_fail"
    elif max_sdv15 is not None and max_sdv15 < 0.50:
        physical_classification = "stage_f_mode_ii_h1_prepeak"
    elif crack_rows_count == 0:
        physical_classification = "stage_f_mode_ii_h1_crack_initiated"
    elif pct_force_drop >= 5.0:
        physical_classification = "stage_f_mode_ii_h1_postpeak"
    else:
        physical_classification = "stage_f_mode_ii_h1_crack_propagating"

    result = {
        "classification": physical_classification,
        "technical_pass": technical_pass,
        "passed": technical_pass,
        "validator_return_code": 0 if technical_pass else 1,
        "warnings": warnings,
        "abaqus_return_code": abaqus_return_code,
        "extractor_return_code": extractor_return_code,
        "final_u1_mm": final_u1,
        "expected_u1_target_mm": expected_u1_target,
        "max_rf1_kn": max_rf1,
        "u1_at_max_rf1_mm": u1_at_max_rf1,
        "final_rf1_kn": final_rf1,
        "percentage_force_drop": pct_force_drop,
        "initial_stiffness_kn_per_mm": initial_stiffness,
        "u1_at_first_d05_mm": u1_at_first_d05,
        "max_sdv15": max_sdv15,
        "min_sdv15": min_sdv15,
        "crack_path_rows": crack_rows_count,
        "history_decrease_violations": history_decrease_violations,
        "total_increments": total_increments,
        "walltime_seconds": walltime_s,
        "cpu_time_seconds": cputime_s,
        "peak_memory_kb": peak_mem_kb,
        "total_checks": len(checks),
        "failures": failures,
    }

    target_json = output_json_path if output_json_path is not None else (evidence_dir / "VALIDATION_RESULTS.json")
    if target_json.parent.is_dir():
        try:
            target_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        except Exception:
            pass

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence_dir", type=Path)
    parser.add_argument("--abaqus-rc", type=int, default=0)
    parser.add_argument("--extractor-rc", type=int, default=0)
    parser.add_argument("--target-u1", type=float, default=None)
    args = parser.parse_args()

    res = validate_results(args.evidence_dir, args.abaqus_rc, args.extractor_rc, expected_u1_target=args.target_u1)
    print(json.dumps(res, indent=2))
    return 0 if res["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())

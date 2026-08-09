#!/usr/bin/env python3
"""Fail-closed validation of lightweight extraction outputs for Mode-II H0 serial run."""


import argparse
import csv
import json
import math
import os
import re
import sys
from pathlib import Path

PHASE_LOWER_TOL = -1e-8
PHASE_UPPER_TOL = 1.0 + 1e-6

DECK_SHA256 = "32a25380767bbb0e9e76eb55b3bb7a97d78bb75c4f86c7e8585aa2032ce2d33b"
SOURCE_SHA256 = "5decf4b1f587019d6bdd904e8ceed22175c113e070e714777cb998da428e4d8c"

LOGIN_REQUIRED_FIELDS = [
    "project_revision",
    "deck_sha256",
    "source_sha256",
    "extractor_sha256",
    "validator_sha256",
    "pbs_script_sha256",
]

RUNTIME_REQUIRED_FIELDS = [
    "project_revision",
    "job_name",
    "cpus",
    "mpi_ranks",
    "omp_threads",
    "mp_mode",
    "memory",
    "walltime",
    "deck_sha256",
    "source_sha256",
    "extractor_sha256",
    "validator_sha256",
    "pbs_script_sha256",
]


def read_text(path: Path | None) -> str:
    if path is None or not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def parse_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise ValueError(f"missing CSV file: {path}")
    with path.open("r", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        return list(reader)


def check_finite(val: float | str | None) -> bool:
    if val is None:
        return False
    try:
        f = float(val)
        return math.isfinite(f)
    except (ValueError, TypeError):
        return False


def validate_results(
    extraction_dir: Path,
    sta_path: Path | None = None,
    dat_path: Path | None = None,
    msg_path: Path | None = None,
    runtime_manifest_path: Path | None = None,
    login_manifest_path: Path | None = None,
    runtime_staging_check_path: Path | None = None,
    input_hash_check_path: Path | None = None,
    expected_final_disp: float = 0.010,
    final_disp_tol: float = 1e-6,
) -> dict:
    failures: list[str] = []
    neg_eigenvalue_count = 0

    # 1. `.sta` file verification
    if sta_path:
        if not sta_path.is_file() or sta_path.stat().st_size == 0:
            failures.append(f".sta file is missing or empty: {sta_path}")
        else:
            sta_text = read_text(sta_path)
            if "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" not in sta_text:
                failures.append("analysis did not report completion in .sta")

    # 2. `.dat` and `.msg` file verification
    if dat_path:
        if not dat_path.is_file() or dat_path.stat().st_size == 0:
            failures.append(f".dat file is missing or empty: {dat_path}")
    if msg_path:
        if not msg_path.is_file() or msg_path.stat().st_size == 0:
            failures.append(f".msg file is missing or empty: {msg_path}")

    # 3. Fatal log tokens check
    fatal_tokens = [
        "unresolved external",
        "undefined reference",
        "signal 11",
        "SIGSEGV",
        "Abaqus Error",
        "THE ANALYSIS HAS NOT BEEN COMPLETED",
        "too many attempts",
        "time increment required is less than",
    ]
    for log_path, log_name in [(dat_path, ".dat"), (msg_path, ".msg")]:
        if log_path and log_path.is_file():
            txt = read_text(log_path)
            for token in fatal_tokens:
                if re.search(r"\b" + re.escape(token) + r"\b", txt, re.IGNORECASE):
                    failures.append(f"fatal token '{token}' found in {log_name}")
            # count negative eigenvalue warnings separately
            neg_eigenvalue_count += len(re.findall(r"negative eigenvalue", txt, re.IGNORECASE))

    # 4. Input hash check file
    if input_hash_check_path:
        if not input_hash_check_path.is_file() or input_hash_check_path.stat().st_size == 0:
            failures.append(f"input hash check file is missing or empty: {input_hash_check_path}")
        else:
            hash_text = read_text(input_hash_check_path)
            if "ModeII_H0_serial.inp: OK" not in hash_text:
                failures.append("input hash check missing 'ModeII_H0_serial.inp: OK'")
            if "ModeII_H0_serial.for: OK" not in hash_text:
                failures.append("input hash check missing 'ModeII_H0_serial.for: OK'")

    # 5. Login manifest
    login_manifest_data = {}
    if login_manifest_path:
        if not login_manifest_path.is_file() or login_manifest_path.stat().st_size == 0:
            failures.append(f"login manifest file is missing or empty: {login_manifest_path}")
        else:
            try:
                login_manifest_data = json.loads(login_manifest_path.read_text(encoding="utf-8"))
                for field in LOGIN_REQUIRED_FIELDS:
                    if field not in login_manifest_data or login_manifest_data[field] is None:
                        failures.append(f"login manifest missing required field: {field}")
            except Exception as exc:
                failures.append(f"invalid login manifest JSON: {exc}")

    # 6. Runtime manifest
    runtime_manifest_data = {}
    if runtime_manifest_path:
        if not runtime_manifest_path.is_file() or runtime_manifest_path.stat().st_size == 0:
            failures.append(f"runtime manifest file is missing or empty: {runtime_manifest_path}")
        else:
            try:
                runtime_manifest_data = json.loads(runtime_manifest_path.read_text(encoding="utf-8"))
                for field in RUNTIME_REQUIRED_FIELDS:
                    if field not in runtime_manifest_data or runtime_manifest_data[field] is None:
                        failures.append(f"runtime manifest missing required field: {field}")
            except Exception as exc:
                failures.append(f"invalid runtime manifest JSON: {exc}")

    # 7. Compare shared manifest fields & enforce fixed resource parameters
    if runtime_manifest_data:
        cpus = runtime_manifest_data.get("cpus")
        ranks = runtime_manifest_data.get("mpi_ranks")
        threads = runtime_manifest_data.get("omp_threads")
        mp_mode = runtime_manifest_data.get("mp_mode")
        job_name = runtime_manifest_data.get("job_name")
        memory = runtime_manifest_data.get("memory")
        walltime = runtime_manifest_data.get("walltime")
        deck_hash = runtime_manifest_data.get("deck_sha256")
        source_hash = runtime_manifest_data.get("source_sha256")

        if (cpus, ranks, threads) != (1, 1, 1):
            failures.append(f"runtime cpus/ranks/threads expected 1/1/1, got {cpus}/{ranks}/{threads}")
        if mp_mode != "threads":
            failures.append(f"mp_mode expected threads, got {mp_mode}")
        if job_name != "mode_ii_h0_serial":
            failures.append(f"job_name expected mode_ii_h0_serial, got {job_name}")
        if memory != "16 GB":
            failures.append(f"memory expected 16 GB, got {memory}")
        if walltime != "04:00:00":
            failures.append(f"walltime expected 04:00:00, got {walltime}")

        if deck_hash and deck_hash.lower() != DECK_SHA256:
            failures.append(f"deck hash mismatch: expected {DECK_SHA256}, got {deck_hash}")
        if source_hash and source_hash.lower() != SOURCE_SHA256:
            failures.append(f"source hash mismatch: expected {SOURCE_SHA256}, got {source_hash}")

        if login_manifest_data:
            shared_fields = [
                "project_revision",
                "deck_sha256",
                "source_sha256",
                "extractor_sha256",
                "validator_sha256",
                "pbs_script_sha256",
            ]
            for f_key in shared_fields:
                l_v = login_manifest_data.get(f_key)
                r_v = runtime_manifest_data.get(f_key)
                if l_v != r_v:
                    failures.append(f"manifest {f_key} mismatch: login={l_v}, runtime={r_v}")

    # 8. Runtime staging check file
    if runtime_staging_check_path:
        if not runtime_staging_check_path.is_file() or runtime_staging_check_path.stat().st_size == 0:
            failures.append(f"runtime staging check file is missing or empty: {runtime_staging_check_path}")
        else:
            try:
                staging_data = json.loads(runtime_staging_check_path.read_text(encoding="utf-8"))
                if staging_data.get("classification") != "stage_f_mode_ii_h0_runtime_staging_pass":
                    failures.append(f"runtime staging check classification failure: {staging_data.get('classification')}")
                if staging_data.get("failures"):
                    failures.append(f"runtime staging check contained failures: {staging_data.get('failures')}")
            except Exception as exc:
                failures.append(f"invalid runtime staging check JSON: {exc}")

    # 9. Extraction manifest
    manifest_path = extraction_dir / "extraction_manifest.json"
    if not manifest_path.is_file():
        failures.append("missing extraction_manifest.json")

    # 10. Curve CSV checks
    curve_csv = extraction_dir / "rf1_u1_curve.csv"
    if not curve_csv.is_file():
        curve_csv = extraction_dir / "single_notch_rf_u_phase_summary.csv"
    curve_rows = []
    if curve_csv.is_file():
        try:
            curve_rows = parse_csv(curve_csv)
        except Exception as exc:
            failures.append(f"invalid curve CSV: {exc}")
    else:
        failures.append("missing curve CSV file")

    if curve_rows:
        if len(curve_rows) < 2:
            failures.append(f"curve contains fewer than 2 points: {len(curve_rows)}")

        u_vals = []
        rf_vals = []
        for idx, row in enumerate(curve_rows):
            u_str = row.get("rp_u1", row.get("rp_u2", ""))
            rf_str = row.get("rp_rf1", row.get("rp_rf2", ""))

            if not check_finite(u_str):
                failures.append(f"non-finite U1 at row {idx}: {u_str}")
            else:
                u_vals.append(float(u_str))

            if not check_finite(rf_str):
                failures.append(f"non-finite RF1 at row {idx}: {rf_str}")
            else:
                rf_vals.append(float(rf_str))

        if u_vals:
            final_u = abs(u_vals[-1])
            if abs(final_u - expected_final_disp) > final_disp_tol:
                failures.append(
                    f"final |U1| {final_u:.6f} not within tolerance {final_disp_tol} of expected {expected_final_disp:.6f}"
                )

    # 11. Energy history CSV
    energy_csv = extraction_dir / "energy_history.csv"
    if energy_csv.is_file():
        try:
            e_rows = parse_csv(energy_csv)
            if not e_rows:
                failures.append("energy_history.csv is empty")
            for idx, r in enumerate(e_rows):
                val_str = r.get("value", "")
                if not check_finite(val_str):
                    failures.append(f"non-finite energy at row {idx}: {r.get('variable')} = {val_str}")
        except Exception as exc:
            failures.append(f"invalid energy_history.csv: {exc}")
    else:
        failures.append("missing energy_history.csv")

    # 12. Irreversibility summary
    irrev_json = extraction_dir / "irreversibility_summary.json"
    if irrev_json.is_file():
        try:
            irrev_data = json.loads(irrev_json.read_text(encoding="utf-8"))
            required_irrev_fields = [
                "phase_healing_violation_count",
                "worst_phase_decrease",
                "history_decrease_violation_count",
                "worst_history_decrease",
                "healing_tolerance",
                "history_decrease_tolerance",
            ]
            for f in required_irrev_fields:
                if f not in irrev_data:
                    failures.append(f"irreversibility_summary.json missing required field: {f}")

            phase_violations = irrev_data.get("phase_healing_violation_count")
            hist_violations = irrev_data.get("history_decrease_violation_count")
            worst_phase_dec = irrev_data.get("worst_phase_decrease")
            worst_hist_dec = irrev_data.get("worst_history_decrease")

            if not check_finite(worst_phase_dec):
                failures.append("non-finite worst_phase_decrease in irreversibility_summary.json")
            if not check_finite(worst_hist_dec):
                failures.append("non-finite worst_history_decrease in irreversibility_summary.json")

            if not isinstance(phase_violations, int) or phase_violations < 0 or phase_violations != 0:
                failures.append(f"invalid phase_healing_violation_count: {phase_violations}")
            if not isinstance(hist_violations, int) or hist_violations < 0 or hist_violations != 0:
                failures.append(f"invalid history_decrease_violation_count: {hist_violations}")
        except Exception as exc:
            failures.append(f"invalid irreversibility_summary.json: {exc}")
    else:
        failures.append("missing irreversibility_summary.json")

    # 13. Phase bounds summary
    pb_json = extraction_dir / "phase_bounds_summary.json"
    if pb_json.is_file():
        try:
            pb_data = json.loads(pb_json.read_text(encoding="utf-8"))
            for f in ["minimum_phase", "maximum_phase", "values_checked"]:
                if f not in pb_data:
                    failures.append(f"phase_bounds_summary.json missing required field: {f}")

            min_p = pb_data.get("minimum_phase")
            max_p = pb_data.get("maximum_phase")
            checked = pb_data.get("values_checked")

            if not check_finite(min_p):
                failures.append("non-finite minimum_phase in phase_bounds_summary.json")
            if not check_finite(max_p):
                failures.append("non-finite maximum_phase in phase_bounds_summary.json")
            if not isinstance(checked, int) or checked <= 0:
                failures.append(f"values_checked must be positive integer, got: {checked}")

            if check_finite(min_p) and float(min_p) < PHASE_LOWER_TOL:
                failures.append(f"minimum phase {min_p} < lower tol {PHASE_LOWER_TOL}")
            if check_finite(max_p) and float(max_p) > PHASE_UPPER_TOL:
                failures.append(f"maximum phase {max_p} > upper tol {PHASE_UPPER_TOL}")
            if check_finite(max_p) and float(max_p) <= 0.01:
                failures.append(f"trivial phase evolution: maximum phase {max_p} <= 0.01")
        except Exception as exc:
            failures.append(f"invalid phase_bounds_summary.json: {exc}")
    else:
        failures.append("missing phase_bounds_summary.json")

    # 14. Crack path CSV
    candidates = list(extraction_dir.glob("crack_path_*.csv"))
    if candidates:
        crack_csv = candidates[0]
        try:
            crack_rows = parse_csv(crack_csv)
            if not crack_rows:
                failures.append("crack-path CSV is empty")
        except Exception as exc:
            failures.append(f"invalid crack-path CSV: {exc}")
    else:
        failures.append("missing crack-path CSV file")

    classification = (
        "stage_f_mode_ii_h0_serial_baseline_characterized"
        if not failures
        else "stage_f_mode_ii_h0_serial_validation_fail"
    )

    return {
        "classification": classification,
        "failures": failures,
        "curve_points": len(curve_rows),
        "negative_eigenvalue_warning_count": neg_eigenvalue_count,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--extraction-dir", type=Path, required=True)
    parser.add_argument("--sta", type=Path, default=None)
    parser.add_argument("--dat", type=Path, default=None)
    parser.add_argument("--msg", type=Path, default=None)
    parser.add_argument("--runtime-manifest", type=Path, default=None)
    parser.add_argument("--login-manifest", type=Path, default=None)
    parser.add_argument("--runtime-staging-check", type=Path, default=None)
    parser.add_argument("--input-hash-check", type=Path, default=None)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--expected-final-displacement", type=float, default=0.010)
    parser.add_argument("--final-displacement-tolerance", type=float, default=1e-6)
    args = parser.parse_args()

    result = validate_results(
        args.extraction_dir,
        sta_path=args.sta,
        dat_path=args.dat,
        msg_path=args.msg,
        runtime_manifest_path=args.runtime_manifest,
        login_manifest_path=args.login_manifest,
        runtime_staging_check_path=args.runtime_staging_check,
        input_hash_check_path=args.input_hash_check,
        expected_final_disp=args.expected_final_displacement,
        final_disp_tol=args.final_displacement_tolerance,
    )

    if args.output_json:
        out_path = args.output_json.resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8") as stream:
            json.dump(result, stream, indent=2, sort_keys=True)
            stream.write("\n")

    print(json.dumps(result, indent=2, sort_keys=True))
    if result["failures"]:
        print("Mode-II H0 serial result validation failed")
        return 20
    print("Mode-II H0 serial result validation pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

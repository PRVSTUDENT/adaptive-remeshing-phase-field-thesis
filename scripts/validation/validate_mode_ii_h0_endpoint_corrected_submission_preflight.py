#!/usr/bin/env python3
"""Submission preflight validator for Stage-F Mode-II H0 endpoint-corrected serial lane."""


import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUTH_FILE = ROOT / "runs/hpc/stage_f/mode_ii_h0_endpoint_corrected/MODE_II_H0_ENDPOINT_CORRECTED_AUTHORIZATION.json"
PACKAGE_DIR = ROOT / "models/generated/mode_ii/h0_endpoint_corrected_serial"


def validate_preflight(
    auth_file: Path = AUTH_FILE,
    package_dir: Path = PACKAGE_DIR,
    mode: str = "preparation",  # preparation | datacheck | solver
) -> dict:
    failures = []
    checks = []

    def check(condition: bool, msg: str) -> None:
        checks.append(msg)
        if not condition:
            failures.append(msg)

    check(auth_file.is_file(), f"authorization file exists ({auth_file})")
    check(package_dir.is_dir(), f"package directory exists ({package_dir})")

    auth = {}
    if auth_file.is_file():
        try:
            auth = json.loads(auth_file.read_text(encoding="utf-8"))
        except Exception as exc:
            failures.append(f"could not parse authorization JSON: {exc}")

    # Check authorization path isn't historical
    check("mode_ii_h0/MODE_II_H0_AUTHORIZATION.json" not in str(auth_file).replace("\\", "/"), "authorization path is not historical")

    # Safety flags
    check(auth.get("automatic_retry_authorized") is False, "automatic_retry_authorized is false")
    check(auth.get("mpi_authorized") is False, "mpi_authorized is false")
    check(auth.get("threaded_execution_authorized") is False, "threaded_execution_authorized is false")
    check(auth.get("hybrid_authorized") is False, "hybrid_authorized is false")
    check(auth.get("h1_authorized") is False, "h1_authorized is false")

    if mode == "preparation":
        check(auth.get("datacheck_authorized") is False, "datacheck_authorized is false for preparation mode")
        check(auth.get("solver_authorized") is False, "solver_authorized is false for preparation mode")
        check(auth.get("execution_authorized") is False, "execution_authorized is false for preparation mode")
        check(auth.get("preparation_complete") is True, "preparation_complete is true")
        check(auth.get("static_validation_passed") is True, "static_validation_passed is true")
    elif mode == "datacheck":
        check(auth.get("datacheck_authorized") is True, "datacheck_authorized is true for datacheck mode")
        check(auth.get("datacheck_submissions_used", 1) < auth.get("maximum_datacheck_submissions", 1), "datacheck submission count within limits")
    elif mode == "solver":
        check(auth.get("solver_authorized") is True, "solver_authorized is true for solver mode")
        check(auth.get("solver_submissions_used", 1) < auth.get("maximum_solver_submissions", 1), "solver submission count within limits")
    else:
        failures.append(f"unknown mode: {mode}")

    # Package hash check
    hashes_file = package_dir / "input_hashes.sha256"
    check(hashes_file.is_file(), "package input_hashes.sha256 exists")

    # Deck content check
    deck_path = package_dir / "ModeII_H0_endpoint_corrected_serial.inp"
    if deck_path.is_file():
        deck_text = deck_path.read_text(encoding="utf-8")
        check("*Amplitude, name=Amp-2\n             0.,           0.005,             0.2,            0.01" in deck_text, "deck contains corrected Amp-2 table")

    passed = len(failures) == 0
    classification = (
        f"stage_f_mode_ii_h0_endpoint_corrected_preflight_{mode}_pass"
        if passed
        else f"stage_f_mode_ii_h0_endpoint_corrected_preflight_{mode}_fail"
    )

    return {
        "classification": classification,
        "mode": mode,
        "passed": passed,
        "total_checks": len(checks),
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["preparation", "datacheck", "solver"], default="preparation")
    parser.add_argument("--auth-file", type=Path, default=AUTH_FILE)
    parser.add_argument("--package-dir", type=Path, default=PACKAGE_DIR)
    args = parser.parse_args()

    res = validate_preflight(args.auth_file, args.package_dir, args.mode)
    print(json.dumps(res, indent=2))
    return 0 if res["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())

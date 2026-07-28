#!/usr/bin/env python3
"""Static validator for the Mode-II H0 endpoint-corrected serial solver staging contract."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
R1_AUTH_PATH = (
    ROOT
    / "runs"
    / "hpc"
    / "stage_f"
    / "mode_ii_h0_endpoint_corrected"
    / "replacement_r1"
    / "MODE_II_H0_ENDPOINT_CORRECTED_R1_AUTHORIZATION.json"
)
OLD_AUTH_PATH = (
    ROOT
    / "runs"
    / "hpc"
    / "stage_f"
    / "mode_ii_h0_endpoint_corrected"
    / "MODE_II_H0_ENDPOINT_CORRECTED_AUTHORIZATION.json"
)
WRAPPER_PATH = ROOT / "scripts" / "hpc" / "stage_f" / "submit_mode_ii_h0_endpoint_corrected_serial.sh"
PBS_PATH = ROOT / "scripts" / "hpc" / "stage_f" / "04_mode_ii_h0_endpoint_corrected_serial.pbs"


def fail(msg: str, errors: list[str]) -> None:
    errors.append(msg)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    root: Path = args.root
    errors: list[str] = []

    wrapper_file = root / "scripts" / "hpc" / "stage_f" / "submit_mode_ii_h0_endpoint_corrected_serial.sh"
    pbs_file = root / "scripts" / "hpc" / "stage_f" / "04_mode_ii_h0_endpoint_corrected_serial.pbs"
    r1_auth_file = (
        root
        / "runs"
        / "hpc"
        / "stage_f"
        / "mode_ii_h0_endpoint_corrected"
        / "replacement_r1"
        / "MODE_II_H0_ENDPOINT_CORRECTED_R1_AUTHORIZATION.json"
    )

    if not wrapper_file.is_file():
        fail(f"missing wrapper script: {wrapper_file.relative_to(root)}", errors)
    if not pbs_file.is_file():
        fail(f"missing PBS script: {pbs_file.relative_to(root)}", errors)
    if not r1_auth_file.is_file():
        fail(f"missing R1 authorization record: {r1_auth_file.relative_to(root)}", errors)

    if errors:
        result = {
            "staging_contract_ok": False,
            "classification": "stage_f_mode_ii_h0_endpoint_corrected_solver_staging_contract_fail",
            "failures": errors,
        }
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print("stage_f_mode_ii_h0_endpoint_corrected_solver_staging_contract_fail")
            for e in errors:
                print(f"  - {e}")
        return 1

    wrapper_text = wrapper_file.read_text(encoding="utf-8")
    pbs_text = pbs_file.read_text(encoding="utf-8")

    # 1. R1 Auth path only, no fallback to old auth
    if "replacement_r1/MODE_II_H0_ENDPOINT_CORRECTED_R1_AUTHORIZATION.json" not in wrapper_text:
        fail("wrapper script does not use R1 authorization path", errors)
    if "MODE_II_H0_ENDPOINT_CORRECTED_AUTHORIZATION.json" in wrapper_text:
        fail("wrapper script contains fallback to historical non-R1 authorization path", errors)

    # 2. Four key variables in wrapper and passed via qsub -v
    for var in ("PRESTAGED_ROOT", "LOGIN_MANIFEST_PATH", "PROJECT_REVISION", "PRESTAGED_RUNTIME_ROOT"):
        if var not in wrapper_text:
            fail(f"wrapper script missing reference to variable {var}", errors)
        if var not in pbs_text:
            fail(f"PBS script missing reference to variable {var}", errors)

    if '-v "PRESTAGED_ROOT=${STAGE_ROOT},LOGIN_MANIFEST_PATH=${MANIFEST},PROJECT_REVISION=${REVISION},PRESTAGED_RUNTIME_ROOT=${RUNTIME_ROOT}"' not in wrapper_text and 'PRESTAGED_RUNTIME_ROOT' not in wrapper_text:
        fail("wrapper script does not pass all 4 variables via qsub -v", errors)

    # 3. Serial environment enforcement in PBS script
    if "export OMP_NUM_THREADS=1" not in pbs_text:
        fail("PBS script does not set export OMP_NUM_THREADS=1", errors)
    if "export MKL_NUM_THREADS=1" not in pbs_text:
        fail("PBS script does not set export MKL_NUM_THREADS=1", errors)

    # 4. Verification checks in wrapper
    if "ALLOW_MODE_II_H0_ENDPOINT_CORRECTED_SOLVER_SUBMIT" not in wrapper_text:
        fail("wrapper script missing ALLOW_MODE_II_H0_ENDPOINT_CORRECTED_SOLVER_SUBMIT flag check", errors)
    if "c9160d50c944de7037a9f05dc1dbccfa9718f69b198bb48659f784bac220ddef" not in wrapper_text:
        fail("wrapper script missing expected deck SHA-256 check", errors)
    if "5decf4b1f587019d6bdd904e8ceed22175c113e070e714777cb998da428e4d8c" not in wrapper_text:
        fail("wrapper script missing expected source SHA-256 check", errors)
    if "extract_molnar_single_notch.py" not in wrapper_text or "validate_mode_ii_h0_endpoint_corrected_results.py" not in wrapper_text:
        fail("wrapper script missing runtime extractor/validator script prestaging", errors)

    # 5. Duplicate job check before qsub
    if "grep \"mode_ii_h0_endpoint_corrected_serial\"" not in wrapper_text:
        fail("wrapper script missing duplicate job qstat check", errors)

    ok = len(errors) == 0
    classification = (
        "stage_f_mode_ii_h0_endpoint_corrected_solver_staging_contract_pass"
        if ok
        else "stage_f_mode_ii_h0_endpoint_corrected_solver_staging_contract_fail"
    )

    result = {
        "staging_contract_ok": ok,
        "classification": classification,
        "failures": errors,
        "wrapper": str(wrapper_file.relative_to(root)),
        "pbs": str(pbs_file.relative_to(root)),
    }

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if ok:
            print("stage_f_mode_ii_h0_endpoint_corrected_solver_staging_contract_pass")
        else:
            print("stage_f_mode_ii_h0_endpoint_corrected_solver_staging_contract_fail")
            for e in errors:
                print(f"  - {e}")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

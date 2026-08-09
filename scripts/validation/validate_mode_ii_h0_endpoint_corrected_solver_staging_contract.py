#!/usr/bin/env python3
"""Static validator for the Mode-II H0 endpoint-corrected serial solver staging contract."""


import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


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

    # 3. Exact authorization classification check
    if "stage_f_mode_ii_h0_endpoint_corrected_serial_solver_submission_approved" not in wrapper_text:
        fail("wrapper script missing exact operational classification check", errors)

    # 4. Approved revision binding
    if "approved_project_revision" not in wrapper_text:
        fail("wrapper script missing approved_project_revision check", errors)

    # 5. Tracked-clean repository check
    if "git -C \"${ROOT_DIR}\" status --porcelain --untracked-files=no" not in wrapper_text and "status --porcelain" not in wrapper_text:
        fail("wrapper script missing tracked-clean repository check", errors)

    # 6. Datacheck job and closeout revision checks
    if "1379387.mmaster02" not in wrapper_text:
        fail("wrapper script missing expected datacheck job ID check", errors)
    if "91d6fad0b972687380759c30a3a268515a733339" not in wrapper_text:
        fail("wrapper script missing expected datacheck closeout revision check", errors)

    # 7. Committed datacheck evidence check
    if "MODE_II_H0_ENDPOINT_CORRECTED_DATACHECK_STATUS.json" not in wrapper_text:
        fail("wrapper script missing committed datacheck evidence check", errors)

    # 8. Execution authorization check
    if "execution_authorized" not in wrapper_text:
        fail("wrapper script missing execution_authorized check", errors)

    # 9. Explicit submission flag check
    if "ALLOW_MODE_II_H0_ENDPOINT_CORRECTED_SOLVER_SUBMIT" not in wrapper_text:
        fail("wrapper script missing ALLOW_MODE_II_H0_ENDPOINT_CORRECTED_SOLVER_SUBMIT flag check", errors)

    # 10. Package hash checks in wrapper
    if "c9160d50c944de7037a9f05dc1dbccfa9718f69b198bb48659f784bac220ddef" not in wrapper_text:
        fail("wrapper script missing expected deck SHA-256 check", errors)
    if "5decf4b1f587019d6bdd904e8ceed22175c113e070e714777cb998da428e4d8c" not in wrapper_text:
        fail("wrapper script missing expected source SHA-256 check", errors)

    # 11. Duplicate job check before qsub
    if "grep \"mode_ii_h0_endpoint_corrected_serial\"" not in wrapper_text:
        fail("wrapper script missing duplicate job qstat check", errors)

    # 12. PBS Manifest parsing and hash checks
    if "deck_sha256" not in pbs_text or "source_sha256" not in pbs_text:
        fail("PBS script missing manifest deck/source hash verification", errors)
    if "extractor_sha256" not in pbs_text or "validator_sha256" not in pbs_text or "configuration_sha256" not in pbs_text:
        fail("PBS script missing manifest extractor/validator/configuration hash verification", errors)

    # 13. Absolute-path checks in PBS script
    if "missing or non-absolute PRESTAGED_ROOT" not in pbs_text and "!= /*" not in pbs_text:
        fail("PBS script missing absolute-path verification for environment variables", errors)

    # 14. Serial environment enforcement in PBS script
    if "export OMP_NUM_THREADS=1" not in pbs_text:
        fail("PBS script does not set export OMP_NUM_THREADS=1", errors)
    if "export MKL_NUM_THREADS=1" not in pbs_text:
        fail("PBS script does not set export MKL_NUM_THREADS=1", errors)

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

#!/usr/bin/env python3
"""Staging contract static validator for Mode-II H0 endpoint-corrected datacheck.

Verifies wrapper-to-PBS variable mapping, hash verification, authorization checks,
and login-manifest schema static properties.
"""


import argparse
import json
import pathlib
import sys

CLASSIFICATION_PASS = "stage_f_mode_ii_h0_endpoint_corrected_staging_contract_pass"
CLASSIFICATION_FAIL = "stage_f_mode_ii_h0_endpoint_corrected_staging_contract_fail"


def validate_staging_contract(
    wrapper_path: pathlib.Path,
    pbs_path: pathlib.Path,
) -> tuple[bool, str, list[str]]:
    failures: list[str] = []

    if not wrapper_path.is_file():
        failures.append(f"Submit wrapper not found: {wrapper_path}")
    if not pbs_path.is_file():
        failures.append(f"PBS script not found: {pbs_path}")

    if failures:
        return False, CLASSIFICATION_FAIL, failures

    wrapper_text = wrapper_path.read_text(encoding="utf-8")
    pbs_text = pbs_path.read_text(encoding="utf-8")

    # 1. Verify wrapper sets and passes PRESTAGED_ROOT, LOGIN_MANIFEST_PATH, PROJECT_REVISION
    for var in ["PRESTAGED_ROOT", "LOGIN_MANIFEST_PATH", "PROJECT_REVISION"]:
        if f"{var}=" not in wrapper_text:
            failures.append(f"Wrapper does not define {var}")
        if var not in pbs_text:
            failures.append(f"PBS script does not consume {var}")

    # 2. Verify qsub receives environment variables via -v
    if "-v " not in wrapper_text or "PRESTAGED_ROOT=" not in wrapper_text:
        failures.append("Wrapper qsub invocation missing -v environment parameters")

    # 3. Verify hash checks before submission
    if "sha256sum" not in wrapper_text or "EXPECTED_DECK_SHA" not in wrapper_text:
        failures.append("Wrapper missing pre-submission package hash checks")

    # 4. Verify duplicate job check
    if "qstat" not in wrapper_text or "grep" not in wrapper_text:
        failures.append("Wrapper missing scheduler duplicate job detection")

    # 5. Verify explicit submission flag
    if "ALLOW_MODE_II_H0_ENDPOINT_CORRECTED_DATACHECK_SUBMIT" not in wrapper_text:
        failures.append("Wrapper missing explicit ALLOW_MODE_II_H0_ENDPOINT_CORRECTED_DATACHECK_SUBMIT environment flag requirement")

    # 6. Verify login manifest schema properties in wrapper and PBS script expectations
    manifest_fields = ["project_revision", "deck_sha256", "source_sha256"]
    for field in manifest_fields:
        if field not in wrapper_text:
            failures.append(f"Wrapper manifest generation missing field: {field}")

    if failures:
        return False, CLASSIFICATION_FAIL, failures

    return True, CLASSIFICATION_PASS, []


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate staging contract statically")
    parser.add_argument("--wrapper", type=pathlib.Path, default=pathlib.Path("scripts/hpc/stage_f/submit_mode_ii_h0_endpoint_corrected_datacheck.sh"))
    parser.add_argument("--pbs", type=pathlib.Path, default=pathlib.Path("scripts/hpc/stage_f/03_mode_ii_h0_endpoint_corrected_datacheck.pbs"))
    args = parser.parse_args()

    ok, classification, failures = validate_staging_contract(args.wrapper, args.pbs)

    result = {
        "staging_contract_ok": ok,
        "classification": classification,
        "failures": failures,
        "wrapper": str(args.wrapper),
        "pbs": str(args.pbs),
    }

    print(json.dumps(result, indent=2))
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()

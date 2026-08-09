#!/usr/bin/env python3
"""Standalone, fail-closed runtime staging verifier for Stage F Mode-II H0 serial runs."""


import argparse
import json
import re
import sys
from pathlib import Path

SHA256_REGEX = re.compile(r"^[0-9a-f]{64}$")

MATCH_FIELDS = {
    "project_revision_match": "project_revision",
    "deck_hash_match": "deck_sha256",
    "source_hash_match": "source_sha256",
    "extractor_hash_match": "extractor_sha256",
    "validator_hash_match": "validator_sha256",
    "pbs_hash_match": "pbs_script_sha256",
    "staging_checker_hash_match": "staging_checker_sha256",
}


def write_result(output_path: Path | None, data: dict) -> None:
    if output_path is not None:
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, sort_keys=True)
                f.write("\n")
        except Exception as err:
            print(f"Error writing staging result file: {err}", file=sys.stderr)


def verify_staging(
    login_path: Path, runtime_path: Path, output_path: Path | None = None
) -> tuple[int, dict]:
    failures: list[str] = []
    result: dict = {
        "classification": "stage_f_mode_ii_h0_runtime_staging_fail",
        "project_revision_match": False,
        "deck_hash_match": False,
        "source_hash_match": False,
        "extractor_hash_match": False,
        "validator_hash_match": False,
        "pbs_hash_match": False,
        "staging_checker_hash_match": False,
        "abaqus_deck_hash_match": False,
        "failures": failures,
    }

    if not login_path.exists():
        failures.append(f"Login manifest does not exist: {login_path}")
        write_result(output_path, result)
        return 1, result

    if not runtime_path.exists():
        failures.append(f"Runtime manifest does not exist: {runtime_path}")
        write_result(output_path, result)
        return 1, result

    try:
        login_text = login_path.read_text(encoding="utf-8").strip()
        if not login_text:
            failures.append("Login manifest file is empty")
            write_result(output_path, result)
            return 1, result
        login_data = json.loads(login_text)
    except Exception as err:
        failures.append(f"Failed to parse login manifest JSON: {err}")
        write_result(output_path, result)
        return 1, result

    try:
        runtime_text = runtime_path.read_text(encoding="utf-8").strip()
        if not runtime_text:
            failures.append("Runtime manifest file is empty")
            write_result(output_path, result)
            return 1, result
        runtime_data = json.loads(runtime_text)
    except Exception as err:
        failures.append(f"Failed to parse runtime manifest JSON: {err}")
        write_result(output_path, result)
        return 1, result

    if not isinstance(login_data, dict):
        failures.append("Login manifest JSON root is not an object")
        write_result(output_path, result)
        return 1, result

    if not isinstance(runtime_data, dict):
        failures.append("Runtime manifest JSON root is not an object")
        write_result(output_path, result)
        return 1, result

    # Check matching fields
    for out_key, field_name in MATCH_FIELDS.items():
        if field_name not in login_data:
            failures.append(f"Required field '{field_name}' missing from login manifest")
            continue
        if field_name not in runtime_data:
            failures.append(f"Required field '{field_name}' missing from runtime manifest")
            continue

        l_val = login_data[field_name]
        r_val = runtime_data[field_name]

        # Check format for SHA fields
        if field_name.endswith("_sha256"):
            if not isinstance(l_val, str) or not SHA256_REGEX.match(l_val):
                failures.append(
                    f"Field '{field_name}' in login manifest is not a 64-char hex SHA256 string: {l_val!r}"
                )
            if not isinstance(r_val, str) or not SHA256_REGEX.match(r_val):
                failures.append(
                    f"Field '{field_name}' in runtime manifest is not a 64-char hex SHA256 string: {r_val!r}"
                )

        if l_val == r_val and l_val is not None:
            result[out_key] = True
        else:
            failures.append(f"{field_name} mismatch: login={l_val!r}, runtime={r_val!r}")

    # Check abaqus_deck_sha256 equals deck_sha256 in runtime manifest
    if "abaqus_deck_sha256" not in runtime_data:
        failures.append("Required field 'abaqus_deck_sha256' missing from runtime manifest")
    else:
        abq_deck = runtime_data["abaqus_deck_sha256"]
        deck = runtime_data.get("deck_sha256")
        if not isinstance(abq_deck, str) or not SHA256_REGEX.match(abq_deck):
            failures.append(
                f"Field 'abaqus_deck_sha256' in runtime manifest is not a 64-char hex SHA256 string: {abq_deck!r}"
            )
        if abq_deck == deck and abq_deck is not None:
            result["abaqus_deck_hash_match"] = True
        else:
            failures.append(
                f"abaqus_deck_sha256 mismatch in runtime manifest: abaqus_deck={abq_deck!r}, deck={deck!r}"
            )

    if not failures:
        result["classification"] = "stage_f_mode_ii_h0_runtime_staging_pass"
        write_result(output_path, result)
        return 0, result
    else:
        write_result(output_path, result)
        return 1, result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify Stage F Mode-II runtime staging manifest consistency."
    )
    parser.add_argument("--login-manifest", type=Path, required=True)
    parser.add_argument("--runtime-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=False)

    args = parser.parse_args()

    rc, result = verify_staging(
        login_path=args.login_manifest,
        runtime_path=args.runtime_manifest,
        output_path=args.output,
    )
    return rc


if __name__ == "__main__":
    sys.exit(main())

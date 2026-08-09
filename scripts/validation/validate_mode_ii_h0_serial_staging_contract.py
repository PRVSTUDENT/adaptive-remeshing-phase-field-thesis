#!/usr/bin/env python3
"""Offline validation of Mode-II H0 serial staging contract."""


import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

FROZEN_DECK_SHA256 = "32a25380767bbb0e9e76eb55b3bb7a97d78bb75c4f86c7e8585aa2032ce2d33b"
FROZEN_SOURCE_SHA256 = "5decf4b1f587019d6bdd904e8ceed22175c113e070e714777cb998da428e4d8c"


def compute_sha256(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"missing file for hashing: {path}")
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def is_valid_sha256(val: str | None) -> bool:
    if not val or not isinstance(val, str):
        return False
    return bool(re.match(r"^[0-9a-f]{64}$", val))


def validate_staging_contract(
    package_dir: Path,
    pbs_path: Path,
    extractor_path: Path,
    validator_path: Path,
    verifier_path: Path,
) -> dict:
    failures: list[str] = []

    # 1. Component existence checks
    deck_path = package_dir / "ModeII_H0_serial.inp"
    source_path = package_dir / "ModeII_H0_serial.for"

    if not deck_path.is_file():
        failures.append(f"frozen package deck missing: {deck_path}")
    if not source_path.is_file():
        failures.append(f"frozen package source missing: {source_path}")
    if not pbs_path.is_file():
        failures.append(f"PBS script missing: {pbs_path}")
    if not extractor_path.is_file():
        failures.append(f"extractor script missing: {extractor_path}")
    if not validator_path.is_file():
        failures.append(f"validator script missing: {validator_path}")
    if not verifier_path.is_file():
        failures.append(f"staging verifier script missing: {verifier_path}")

    if failures:
        return {
            "classification": "stage_f_mode_ii_h0_serial_staging_contract_fail",
            "failures": failures,
        }

    # 2. Check PBS script does NOT contain inline manifest comparison code
    pbs_text = pbs_path.read_text(encoding="utf-8")
    forbidden_pbs_patterns = (
        'matches[field + "_match"]',
        'matches["deck_hash_match"]',
        "login_data.get(field)",
        "matches[field",
    )
    for pat in forbidden_pbs_patterns:
        if pat in pbs_text:
            failures.append(f"PBS script contains obsolete/untested inline staging comparison: {pat!r}")

    # Check PBS script calls the staged verifier
    if "verify_mode_ii_h0_runtime_staging.py" not in pbs_text:
        failures.append("PBS script does not invoke verify_mode_ii_h0_runtime_staging.py")

    # 3. Compute reference hashes
    try:
        pkg_deck_hash = compute_sha256(deck_path)
        pkg_source_hash = compute_sha256(source_path)
        pbs_hash = compute_sha256(pbs_path)
        extractor_hash = compute_sha256(extractor_path)
        validator_hash = compute_sha256(validator_path)
        verifier_hash = compute_sha256(verifier_path)
    except Exception as exc:
        return {
            "classification": "stage_f_mode_ii_h0_serial_staging_contract_fail",
            "failures": [f"hash computation error: {exc}"],
        }

    if pkg_deck_hash != FROZEN_DECK_SHA256:
        failures.append(f"package deck hash mismatch: expected {FROZEN_DECK_SHA256}, got {pkg_deck_hash}")
    if pkg_source_hash != FROZEN_SOURCE_SHA256:
        failures.append(f"package source hash mismatch: expected {FROZEN_SOURCE_SHA256}, got {pkg_source_hash}")

    for h_name, h_val in [
        ("pbs_hash", pbs_hash),
        ("extractor_hash", extractor_hash),
        ("validator_hash", validator_hash),
        ("verifier_hash", verifier_hash),
    ]:
        if not is_valid_sha256(h_val):
            failures.append(f"invalid SHA-256 for {h_name}: '{h_val}'")

    # 4. Invoke staging verifier as subprocess with temporary manifests (passing case)
    with tempfile.TemporaryDirectory() as temp_dir_str:
        td = Path(temp_dir_str)
        login_manifest = td / "LOGIN_MANIFEST.json"
        runtime_manifest = td / "RUNTIME_MANIFEST.json"
        output_file = td / "STAGING_CHECK.json"

        login_data = {
            "classification": "stage_f_mode_ii_h0_login_staging_complete",
            "project_revision": "dummy_rev",
            "deck_sha256": pkg_deck_hash,
            "source_sha256": pkg_source_hash,
            "extractor_sha256": extractor_hash,
            "validator_sha256": validator_hash,
            "pbs_script_sha256": pbs_hash,
            "staging_checker_sha256": verifier_hash,
            "compute_git_required": False,
        }
        runtime_data = {
            "project_revision": "dummy_rev",
            "job_name": "mode_ii_h0_serial",
            "cpus": 1,
            "mpi_ranks": 1,
            "omp_threads": 1,
            "mp_mode": "threads",
            "memory": "16 GB",
            "walltime": "04:00:00",
            "deck_sha256": pkg_deck_hash,
            "abaqus_deck_sha256": pkg_deck_hash,
            "source_sha256": pkg_source_hash,
            "extractor_sha256": extractor_hash,
            "validator_sha256": validator_hash,
            "pbs_script_sha256": pbs_hash,
            "staging_checker_sha256": verifier_hash,
        }

        login_manifest.write_text(json.dumps(login_data, indent=2), encoding="utf-8")
        runtime_manifest.write_text(json.dumps(runtime_data, indent=2), encoding="utf-8")

        proc = subprocess.run(
            [
                sys.executable,
                str(verifier_path),
                "--login-manifest",
                str(login_manifest),
                "--runtime-manifest",
                str(runtime_manifest),
                "--output",
                str(output_file),
            ],
            capture_output=True,
            text=True,
        )

        if proc.returncode != 0:
            failures.append(f"Subprocess verifier returned non-zero code {proc.returncode}: {proc.stderr}")

        if not output_file.is_file():
            failures.append("Subprocess verifier failed to produce output JSON")
        else:
            try:
                res_data = json.loads(output_file.read_text(encoding="utf-8"))
                if res_data.get("classification") != "stage_f_mode_ii_h0_runtime_staging_pass":
                    failures.append(
                        f"Subprocess verifier classification mismatch: {res_data.get('classification')}"
                    )
                bool_fields = (
                    "project_revision_match",
                    "deck_hash_match",
                    "source_hash_match",
                    "extractor_hash_match",
                    "validator_hash_match",
                    "pbs_hash_match",
                    "staging_checker_hash_match",
                    "abaqus_deck_hash_match",
                )
                for bf in bool_fields:
                    if res_data.get(bf) is not True:
                        failures.append(f"Subprocess verifier field {bf} is not True")
            except Exception as exc:
                failures.append(f"Failed to parse verifier output JSON: {exc}")

        # 5. Malformed fixture test: verify clean failure JSON without crash
        bad_runtime_data = dict(runtime_data)
        bad_runtime_data["deck_sha256"] = "0" * 64
        bad_runtime_manifest = td / "BAD_RUNTIME_MANIFEST.json"
        bad_output_file = td / "BAD_STAGING_CHECK.json"
        bad_runtime_manifest.write_text(json.dumps(bad_runtime_data, indent=2), encoding="utf-8")

        bad_proc = subprocess.run(
            [
                sys.executable,
                str(verifier_path),
                "--login-manifest",
                str(login_manifest),
                "--runtime-manifest",
                str(bad_runtime_manifest),
                "--output",
                str(bad_output_file),
            ],
            capture_output=True,
            text=True,
        )

        if bad_proc.returncode == 0:
            failures.append("Subprocess verifier expected non-zero returncode on hash mismatch but got 0")

        if not bad_output_file.is_file():
            failures.append("Subprocess verifier failed to produce output JSON on bad fixture")
        else:
            try:
                bad_res = json.loads(bad_output_file.read_text(encoding="utf-8"))
                if bad_res.get("classification") != "stage_f_mode_ii_h0_runtime_staging_fail":
                    failures.append("Subprocess verifier did not return staging fail classification")
            except Exception as exc:
                failures.append(f"Failed to parse bad verifier output JSON: {exc}")

    classification = (
        "stage_f_mode_ii_h0_serial_staging_contract_pass"
        if not failures
        else "stage_f_mode_ii_h0_serial_staging_contract_fail"
    )

    return {
        "classification": classification,
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--pbs", type=Path, required=True)
    parser.add_argument("--extractor", type=Path, required=True)
    parser.add_argument("--result-validator", type=Path, required=True)
    parser.add_argument(
        "--staging-verifier",
        type=Path,
        default=Path("scripts/validation/verify_mode_ii_h0_runtime_staging.py"),
    )
    args = parser.parse_args()

    result = validate_staging_contract(
        args.package.resolve(),
        args.pbs.resolve(),
        args.extractor.resolve(),
        args.result_validator.resolve(),
        args.staging_verifier.resolve(),
    )

    print(json.dumps(result, indent=2, sort_keys=True))
    if result["failures"]:
        print("Mode-II H0 serial staging contract validation failed")
        return 1
    print("Mode-II H0 serial staging contract validation pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

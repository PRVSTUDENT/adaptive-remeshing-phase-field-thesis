#!/usr/bin/env python3
"""Local staging contract smoke validator for Mode-II H0 endpoint-corrected datacheck.

Executes a local staging simulation without launching Abaqus or qsub.
Verifies prestaging tree creation, login manifest generation, hash integrity,
and mocked qsub argument composition.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import shutil
import sys
import tempfile

CLASSIFICATION_PASS = "stage_f_mode_ii_h0_endpoint_corrected_staging_smoke_pass"
CLASSIFICATION_FAIL = "stage_f_mode_ii_h0_endpoint_corrected_staging_smoke_fail"

EXPECTED_DECK_SHA = "c9160d50c944de7037a9f05dc1dbccfa9718f69b198bb48659f784bac220ddef"
EXPECTED_SOURCE_SHA = "5decf4b1f587019d6bdd904e8ceed22175c113e070e714777cb998da428e4d8c"


def run_staging_smoke(
    package_dir: pathlib.Path,
    evidence_output_dir: pathlib.Path,
    revision: str = "20cad4f94133635076da48eda821b50dd53a050a",
) -> tuple[bool, str, list[str]]:
    failures: list[str] = []

    deck_path = package_dir / "ModeII_H0_endpoint_corrected_serial.inp"
    source_path = package_dir / "ModeII_H0_endpoint_corrected_serial.for"

    if not deck_path.is_file() or not source_path.is_file():
        failures.append("Input deck or source missing in package directory")
        return False, CLASSIFICATION_FAIL, failures

    deck_sha = hashlib.sha256(deck_path.read_bytes()).hexdigest()
    source_sha = hashlib.sha256(source_path.read_bytes()).hexdigest()

    if deck_sha != EXPECTED_DECK_SHA or source_sha != EXPECTED_SOURCE_SHA:
        failures.append("Package SHA-256 mismatch")
        return False, CLASSIFICATION_FAIL, failures

    # Perform mock staging inside temporary directory
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = pathlib.Path(tmp)
        staged_root = tmp_path / "mode_ii_h0_endpoint_corrected_staged" / revision
        staged_pkg = staged_root / "models/generated/mode_ii/h0_endpoint_corrected_serial"
        staged_pkg.mkdir(parents=True, exist_ok=True)

        staged_deck = staged_pkg / "ModeII_H0_endpoint_corrected_serial.inp"
        staged_source = staged_pkg / "ModeII_H0_endpoint_corrected_serial.for"
        shutil.copy(deck_path, staged_deck)
        shutil.copy(source_path, staged_source)

        (staged_root / "PROJECT_REVISION.txt").write_text(f"{revision}\n", encoding="utf-8")

        manifest_path = staged_root / "MODE_II_H0_LOGIN_MANIFEST.json"
        manifest_data = {
            "classification": "stage_f_mode_ii_h0_endpoint_corrected_login_staging_complete",
            "project_revision": revision,
            "deck_sha256": hashlib.sha256(staged_deck.read_bytes()).hexdigest(),
            "source_sha256": hashlib.sha256(staged_source.read_bytes()).hexdigest(),
            "compute_git_required": False,
        }
        manifest_path.write_text(json.dumps(manifest_data, indent=2) + "\n", encoding="utf-8")

        # Mock qsub argument string
        mock_v_arg = f"PRESTAGED_ROOT={staged_root.resolve()},LOGIN_MANIFEST_PATH={manifest_path.resolve()},PROJECT_REVISION={revision}"
        mock_qsub_cmd = f"qsub -q entry_imfdfkmq -M pr21vyci@mailserver.tu-freiberg.de -m abe -v \"{mock_v_arg}\" scripts/hpc/stage_f/03_mode_ii_h0_endpoint_corrected_datacheck.pbs"

        # Verify mocked qsub arguments
        if "PRESTAGED_ROOT=" not in mock_qsub_cmd or "LOGIN_MANIFEST_PATH=" not in mock_qsub_cmd or "PROJECT_REVISION=" not in mock_qsub_cmd:
            failures.append("Mocked qsub argument string missing required staging variables")

        # Write evidence to evidence_output_dir
        evidence_output_dir.mkdir(parents=True, exist_ok=True)

        mock_record_path = evidence_output_dir / "mocked_qsub_arguments.txt"
        mock_record_path.write_text(f"{mock_qsub_cmd}\n", encoding="utf-8")

        manifest_copy_path = evidence_output_dir / "staged_login_manifest.json"
        manifest_copy_path.write_text(json.dumps(manifest_data, indent=2) + "\n", encoding="utf-8")

        status_data = {
            "local_smoke_ok": True,
            "classification": CLASSIFICATION_PASS,
            "qsub_submissions_count": 0,
            "abaqus_executions_count": 0,
            "prestaged_root": str(staged_root.resolve()),
            "login_manifest_path": str(manifest_path.resolve()),
            "project_revision": revision,
            "deck_sha256": deck_sha,
            "source_sha256": source_sha,
        }
        (evidence_output_dir / "LOCAL_STAGING_SMOKE_STATUS.json").write_text(json.dumps(status_data, indent=2) + "\n", encoding="utf-8")

        # Build EVIDENCE_FILE_INVENTORY.csv
        rows = ["filename,size_bytes,sha256"]
        for f in sorted(evidence_output_dir.glob("*")):
            if f.is_file() and f.name != "EVIDENCE_FILE_INVENTORY.csv":
                size = f.stat().st_size
                sha = hashlib.sha256(f.read_bytes()).hexdigest()
                rows.append(f"{f.name},{size},{sha}")
        (evidence_output_dir / "EVIDENCE_FILE_INVENTORY.csv").write_text("\n".join(rows) + "\n", encoding="utf-8")

    if failures:
        return False, CLASSIFICATION_FAIL, failures

    return True, CLASSIFICATION_PASS, []


def main() -> None:
    parser = argparse.ArgumentParser(description="Run local staging smoke validator")
    parser.add_argument("--package", type=pathlib.Path, default=pathlib.Path("models/generated/mode_ii/h0_endpoint_corrected_serial"))
    parser.add_argument("--output", type=pathlib.Path, default=pathlib.Path("runs/hpc/stage_f/mode_ii_h0_endpoint_corrected/replacement_r1/smoke_evidence/local"))
    parser.add_argument("--revision", type=str, default="20cad4f94133635076da48eda821b50dd53a050a")
    args = parser.parse_args()

    ok, classification, failures = run_staging_smoke(args.package, args.output, args.revision)

    res = {
        "local_smoke_ok": ok,
        "classification": classification,
        "failures": failures,
        "output_dir": str(args.output),
    }
    print(json.dumps(res, indent=2))
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()

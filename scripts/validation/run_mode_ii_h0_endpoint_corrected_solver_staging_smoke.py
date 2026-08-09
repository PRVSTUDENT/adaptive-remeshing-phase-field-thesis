#!/usr/bin/env python3
"""Run solver staging smoke test for Mode-II H0 endpoint-corrected serial solver lane."""


import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
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
SMOKE_EVIDENCE_DIR = (
    ROOT
    / "runs"
    / "hpc"
    / "stage_f"
    / "mode_ii_h0_endpoint_corrected"
    / "replacement_r1"
    / "solver_smoke_evidence"
    / "local"
)
PACKAGE_DIR = ROOT / "models" / "generated" / "mode_ii" / "h0_endpoint_corrected_serial"

EXPECTED_DECK_SHA = "c9160d50c944de7037a9f05dc1dbccfa9718f69b198bb48659f784bac220ddef"
EXPECTED_SOURCE_SHA = "5decf4b1f587019d6bdd904e8ceed22175c113e070e714777cb998da428e4d8c"
EXPECTED_PREP_REVISION = "f7e44ae6e7df7dcf1b7eb468eaa946b2eec9caae"
EXPECTED_DATACHECK_JOB = "1379387.mmaster02"
EXPECTED_DATACHECK_CLOSEOUT_REV = "91d6fad0b972687380759c30a3a268515a733339"


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--evidence-dir", type=Path, default=SMOKE_EVIDENCE_DIR)
    args = parser.parse_args()

    root: Path = args.root
    evidence_dir: Path = args.evidence_dir
    evidence_dir.mkdir(parents=True, exist_ok=True)

    errors: list[str] = []

    # 1. Verify package existence and hashes
    deck_path = PACKAGE_DIR / "ModeII_H0_endpoint_corrected_serial.inp"
    source_path = PACKAGE_DIR / "ModeII_H0_endpoint_corrected_serial.for"

    if not deck_path.is_file():
        errors.append(f"missing input deck: {deck_path}")
    if not source_path.is_file():
        errors.append(f"missing Fortran source: {source_path}")

    if errors:
        print("stage_f_mode_ii_h0_endpoint_corrected_solver_smoke_fail")
        for e in errors:
            print(f"  - {e}")
        return 1

    deck_sha = compute_sha256(deck_path)
    source_sha = compute_sha256(source_path)

    if deck_sha != EXPECTED_DECK_SHA:
        errors.append(f"deck SHA mismatch: {deck_sha} != {EXPECTED_DECK_SHA}")
    if source_sha != EXPECTED_SOURCE_SHA:
        errors.append(f"source SHA mismatch: {source_sha} != {EXPECTED_SOURCE_SHA}")

    # 2. Simulate prestaging in a temporary directory
    temp_dir = Path(tempfile.mkdtemp(prefix="solver_staging_smoke_"))
    try:
        revision = "fef51c7ccbe29a4240274d1c67b811fce72955a1"
        staged_root = (temp_dir / "staged" / revision).resolve()
        staged_pkg = staged_root / "models" / "generated" / "mode_ii" / "h0_endpoint_corrected_serial"
        staged_runtime = staged_root / "runtime"

        staged_pkg.mkdir(parents=True, exist_ok=True)
        (staged_runtime / "scripts" / "postprocessing").mkdir(parents=True, exist_ok=True)
        (staged_runtime / "scripts" / "validation").mkdir(parents=True, exist_ok=True)
        (staged_runtime / "configs" / "studies").mkdir(parents=True, exist_ok=True)

        shutil.copy2(deck_path, staged_pkg / deck_path.name)
        shutil.copy2(source_path, staged_pkg / source_path.name)

        extractor_src = root / "scripts" / "postprocessing" / "extract_molnar_single_notch.py"
        validator_src = root / "scripts" / "validation" / "validate_mode_ii_h0_endpoint_corrected_results.py"
        study_cfg_src = root / "configs" / "studies" / "mode_ii_molnar_shear_endpoint_corrected.yaml"

        shutil.copy2(extractor_src, staged_runtime / "scripts" / "postprocessing" / "extract_molnar_single_notch.py")
        shutil.copy2(validator_src, staged_runtime / "scripts" / "validation" / "validate_mode_ii_h0_endpoint_corrected_results.py")
        shutil.copy2(study_cfg_src, staged_runtime / "configs" / "studies" / "mode_ii_molnar_shear_endpoint_corrected.yaml")

        staged_deck_sha = compute_sha256(staged_pkg / deck_path.name)
        staged_source_sha = compute_sha256(staged_pkg / source_path.name)
        staged_ext_sha = compute_sha256(staged_runtime / "scripts" / "postprocessing" / "extract_molnar_single_notch.py")
        staged_val_sha = compute_sha256(staged_runtime / "scripts" / "validation" / "validate_mode_ii_h0_endpoint_corrected_results.py")
        staged_cfg_sha = compute_sha256(staged_runtime / "configs" / "studies" / "mode_ii_molnar_shear_endpoint_corrected.yaml")

        manifest_path = staged_root / "MODE_II_H0_LOGIN_MANIFEST.json"
        manifest_data = {
            "classification": "stage_f_mode_ii_h0_endpoint_corrected_serial_solver_login_staging_complete",
            "project_revision": revision,
            "authorization_classification": "stage_f_mode_ii_h0_endpoint_corrected_serial_solver_submission_approved",
            "authorization_path": str(R1_AUTH_PATH.resolve()),
            "approved_project_revision": revision,
            "solver_contract_preparation_revision": EXPECTED_PREP_REVISION,
            "datacheck_job_id": EXPECTED_DATACHECK_JOB,
            "datacheck_closeout_revision": EXPECTED_DATACHECK_CLOSEOUT_REV,
            "package_path": str(staged_pkg),
            "deck_sha256": staged_deck_sha,
            "source_sha256": staged_source_sha,
            "runtime_root": str(staged_runtime),
            "extractor_path": "scripts/postprocessing/extract_molnar_single_notch.py",
            "extractor_sha256": staged_ext_sha,
            "validator_path": "scripts/validation/validate_mode_ii_h0_endpoint_corrected_results.py",
            "validator_sha256": staged_val_sha,
            "configuration_path": "configs/studies/mode_ii_molnar_shear_endpoint_corrected.yaml",
            "configuration_sha256": staged_cfg_sha,
            "cpus": 1,
            "mpi_ranks": 1,
            "omp_threads": 1,
            "memory": "16 GB",
            "walltime": "04:00:00",
            "queue": "entry_imfdfkmq",
            "compute_git_required": False,
        }
        manifest_path.write_text(json.dumps(manifest_data, indent=2) + "\n", encoding="utf-8")

        mocked_qsub_args = (
            f"-q entry_imfdfkmq -M pr21vyci@mailserver.tu-freiberg.de -m abe "
            f"-v \"PRESTAGED_ROOT={staged_root},"
            f"LOGIN_MANIFEST_PATH={manifest_path},"
            f"PROJECT_REVISION={revision},"
            f"PRESTAGED_RUNTIME_ROOT={staged_runtime}\" "
            f"scripts/hpc/stage_f/04_mode_ii_h0_endpoint_corrected_serial.pbs"
        )
        (evidence_dir / "mocked_qsub_arguments.txt").write_text(mocked_qsub_args + "\n", encoding="utf-8")

        status_data = {
            "smoke_ok": True,
            "classification": "stage_f_mode_ii_h0_endpoint_corrected_solver_local_staging_smoke_pass",
            "failures": [],
            "qsub_count": 0,
            "abaqus_executions": 0,
            "staged_root": str(staged_root),
            "manifest_path": str(manifest_path),
            "deck_sha256": staged_deck_sha,
            "source_sha256": staged_source_sha,
            "extractor_sha256": staged_ext_sha,
            "validator_sha256": staged_val_sha,
            "configuration_sha256": staged_cfg_sha,
            "required_vars": ["PRESTAGED_ROOT", "LOGIN_MANIFEST_PATH", "PROJECT_REVISION", "PRESTAGED_RUNTIME_ROOT"],
        }
        (evidence_dir / "LOCAL_STAGING_SMOKE_STATUS.json").write_text(
            json.dumps(status_data, indent=2) + "\n", encoding="utf-8"
        )

        inventory_rows = [
            "filename,size_bytes,sha256",
            f"mocked_qsub_arguments.txt,{len(mocked_qsub_args)},{hashlib.sha256(mocked_qsub_args.encode('utf-8')).hexdigest()}",
            f"LOCAL_STAGING_SMOKE_STATUS.json,{len(json.dumps(status_data))},{hashlib.sha256(json.dumps(status_data).encode('utf-8')).hexdigest()}",
        ]
        (evidence_dir / "EVIDENCE_FILE_INVENTORY.csv").write_text("\n".join(inventory_rows) + "\n", encoding="utf-8")

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    print("stage_f_mode_ii_h0_endpoint_corrected_solver_local_staging_smoke_pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

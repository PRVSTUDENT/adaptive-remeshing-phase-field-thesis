#!/usr/bin/env python3
"""Deterministic no-solver R3 postprocessing replay for job 1377417.

Reuses committed base-extraction products only. Does not read ODB, run Abaqus,
compile Fortran, or modify the preserved failure evidence directory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Import active/free builder from the postprocessing package.
POST_DIR = REPO_ROOT / "scripts" / "postprocessing"
if str(POST_DIR) not in sys.path:
    sys.path.insert(0, str(POST_DIR))

import extract_d3a3_r3_compatible_state as r3_extract  # noqa: E402
from scripts.validation.analyze_d3a3_r3_fixed_state_kkt import analyze as analyze_kkt  # noqa: E402
from scripts.validation import validate_d3a3_r3_compatible_hold as validate_hold  # noqa: E402

SOURCE_JOB = "1377417.mmaster02"
SOURCE_COMMIT = "4bee79e6224ad4acfbeb49d13c51bf7a983e181a"
SOURCE_FAILURE_COMMIT = "213dd1c1d8cb9496674d311fb03b369ea27f13d0"
SOURCE_CLASSIFICATION = "stage_d3a3_r3_ingestion_fail"
PASS_CLASSIFICATION = "stage_d3a3_r3_compatible_release_pass"
REPLAY_PASS = "stage_d3a3_r3_postprocess_replay_pass"
EXPECTED_STATE_ROWS = 102400
EXPECTED_EXTRACTION = "stage_d3a3_extraction_complete_corrected"

SOURCE_FILES = [
    "D3A3_TRANSFER_VS_ODB.csv",
    "D3A3_STATE_BY_FRAME.csv",
    "D3A3_RF_U_CORRECTED.csv",
    "D3A3_RELEASE_JUMP.json",
    "D3A3_RECONSTRUCTED_ENERGY_BY_FRAME_CORRECTED.json",
    "D3A3_PHASE_NODE_RECOVERY_BY_FRAME.csv",
    "D3A3_EXTRACTION_STATUS.json",
    "D3A3_R3_ODB_LOCATION.json",
]

DERIVED_COPY = [
    "D3A3_R3_PHASE_NODE_STATE_BY_FRAME.csv",
    "D3A3_R3_ACTIVE_NODE_STATE.csv",
    "D3A3_R3_FREE_NODE_STATE.csv",
    "D3A3_R3_LOWER_BOUND_AUDIT.json",
    "D3A3_R3_F1_RESIDUAL_BY_NODE.csv",
    "D3A3_R3_F1_KKT_METRICS.json",
    "D3A3_R3_STATUS.json",
    "D3A3_R3_REPORT.md",
    "D3A3_R3.ok",
    "D3A3.ok",
    # Validator also writes these under D3A3_* names that it requires as inputs
    # when reading from target_dir; keep status mirrors if present.
    "D3A3_R3_RUNTIME_STATE_VALIDATION.json",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def require_python_311() -> dict:
    import numpy
    import scipy

    major, minor = sys.version_info[:2]
    if major != 3 or minor != 11:
        raise SystemExit("qualified Python 3.11.x required, got %s.%s" % (major, minor))
    return {
        "python": sys.version,
        "python_major_minor": "%s.%s" % (major, minor),
        "numpy": numpy.__version__,
        "scipy": scipy.__version__,
        "numpy_import": True,
        "scipy_import": True,
    }


def copy_sources(source_dir: Path, work_dir: Path) -> dict:
    hashes = {}
    for name in SOURCE_FILES:
        src = source_dir / name
        if not src.exists():
            raise FileNotFoundError("missing required source file: %s" % src)
        digest = sha256_file(src)
        hashes[name] = {
            "path": str(src.as_posix()),
            "sha256": digest,
            "bytes": src.stat().st_size,
        }
        shutil.copy2(src, work_dir / name)
    return hashes


def verify_source_hashes(source_dir: Path, hashes: dict) -> None:
    for name, meta in hashes.items():
        actual = sha256_file(source_dir / name)
        if actual != meta["sha256"]:
            raise SystemExit("source hash changed for %s: %s != %s" % (name, actual, meta["sha256"]))


def run_replay(source_dir: Path, replay_dir: Path, package_dir: Path, d3a4_dir: Path, model_dir: Path) -> dict:
    env = require_python_311()
    extraction = read_json(source_dir / "D3A3_EXTRACTION_STATUS.json")
    if extraction.get("classification") != EXPECTED_EXTRACTION:
        raise SystemExit("unexpected extraction classification: %s" % extraction.get("classification"))
    if int(extraction.get("state_rows", -1)) != EXPECTED_STATE_ROWS:
        raise SystemExit("unexpected state_rows: %s" % extraction.get("state_rows"))

    replay_dir.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="d3a3_r3_postprocess_replay_"))
    try:
        hashes = copy_sources(source_dir, work)
        verify_source_hashes(source_dir, hashes)

        # Active/free builder under ordinary Python 3.11.
        audit = r3_extract.build_active_free_state(str(work), str(d3a4_dir), str(package_dir))
        if audit.get("classification") != "stage_d3a3_r3_lower_bound_audit_pass":
            write_json(replay_dir / "D3A3_R3_LOWER_BOUND_AUDIT.json", audit)
            raise SystemExit("active/free lower-bound audit failed: %s" % audit)

        kkt = analyze_kkt(work, d3a4_dir, model_dir, package_dir)
        status = validate_hold.validate(work, d3a4_dir)
        validate_hold.apply_status(work, status)

        # Provenance and hashes into replay lane first.
        provenance = {
            "source_job": SOURCE_JOB,
            "source_commit": SOURCE_COMMIT,
            "source_failure_commit": SOURCE_FAILURE_COMMIT,
            "source_classification": SOURCE_CLASSIFICATION,
            "abaqus_analysis_reused": True,
            "odb_reread": False,
            "solver_executed": False,
            "fortran_compiled": False,
            "new_transfer_package": False,
            "new_mesh": False,
            "base_extraction_reused": True,
            "postprocessing_interpreter": "python/gcc/11.4.0/3.11.7",
            "correction": "run active/free builder under qualified Python after Abaqus-only extraction",
            "environment": env,
            "source_extraction_classification": extraction.get("classification"),
            "source_state_rows": extraction.get("state_rows"),
            "source_dir": str(source_dir.as_posix()),
            "replay_dir": str(replay_dir.as_posix()),
            "work_dir_removed": True,
        }
        write_json(replay_dir / "D3A3_R3_POSTPROCESS_REPLAY_PROVENANCE.json", provenance)
        write_json(replay_dir / "D3A3_R3_POSTPROCESS_SOURCE_HASHES.json", {
            "classification": "stage_d3a3_r3_postprocess_source_hashes",
            "source_job": SOURCE_JOB,
            "files": hashes,
            "hashes_unchanged": True,
        })

        # Copy lightweight derived outputs into the isolated replay lane.
        for name in DERIVED_COPY:
            src = work / name
            if src.exists():
                shutil.copy2(src, replay_dir / name)

        # Also keep a copy of the lower-bound audit and KKT already written under work.
        for name in [
            "D3A3_R3_LOWER_BOUND_AUDIT.json",
            "D3A3_R3_F1_KKT_METRICS.json",
            "D3A3_R3_F1_RESIDUAL_BY_NODE.csv",
        ]:
            src = work / name
            if src.exists():
                shutil.copy2(src, replay_dir / name)

        scientific_pass = bool(status.get("D3A3_ok"))
        if scientific_pass:
            (replay_dir / "D3A3_R3_POSTPROCESS_REPLAY.ok").write_text(
                REPLAY_PASS + "\n", encoding="utf-8"
            )
            # Canonical markers only when scientific gates pass.
            (replay_dir / "D3A3_R3.ok").write_text(PASS_CLASSIFICATION + "\n", encoding="utf-8")
            (replay_dir / "D3A3.ok").write_text(PASS_CLASSIFICATION + "\n", encoding="utf-8")
        else:
            for marker in [
                replay_dir / "D3A3_R3_POSTPROCESS_REPLAY.ok",
                replay_dir / "D3A3_R3.ok",
                replay_dir / "D3A3.ok",
            ]:
                if marker.exists():
                    marker.unlink()

        result = {
            "classification": REPLAY_PASS if scientific_pass else status.get("classification"),
            "scientific_pass": scientific_pass,
            "D3A3_ok": scientific_pass,
            "status": status,
            "kkt_classification": kkt.get("classification"),
            "lower_bound_audit": audit.get("classification"),
            "environment": env,
        }
        write_json(replay_dir / "D3A3_R3_POSTPROCESS_REPLAY_STATUS.json", result)
        return result
    finally:
        shutil.rmtree(work, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=Path("runs/hpc/stage_d3/interrupted_transfer/target_ingestion_r3_compatible"),
    )
    parser.add_argument(
        "--replay-dir",
        type=Path,
        default=Path(
            "runs/hpc/stage_d3/interrupted_transfer/target_ingestion_r3_compatible_postprocess_replay"
        ),
    )
    parser.add_argument(
        "--package-dir",
        type=Path,
        default=Path("runs/hpc/stage_d3/interrupted_transfer/package_compatible_r1"),
    )
    parser.add_argument(
        "--d3a4-dir",
        type=Path,
        default=Path("runs/hpc/stage_d3/interrupted_transfer/compatibility_projection_d3a4"),
    )
    parser.add_argument(
        "--model-dir",
        type=Path,
        default=Path("models/state_transfer/d3_interrupted_transfer"),
    )
    args = parser.parse_args()

    # Refuse to write into the preserved failure directory.
    source_resolved = args.source_dir.resolve()
    replay_resolved = args.replay_dir.resolve()
    if source_resolved == replay_resolved:
        raise SystemExit("replay-dir must differ from the preserved failure source-dir")

    result = run_replay(
        args.source_dir,
        args.replay_dir,
        args.package_dir,
        args.d3a4_dir,
        args.model_dir,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("scientific_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())

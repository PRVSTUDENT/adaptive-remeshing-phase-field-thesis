#!/usr/bin/env python3
"""Validate P3-SM0 scientific baseline gates plus minimal callback markers."""
from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path

import validate_p3sb_baseline_serial as baseline


MARKERS = (
    "P3SM0_UEXTERNALDB_LOP0",
    "P3SM0_UEL_OBSERVED",
    "P3SM0_UMAT_OBSERVED",
    "P3SM0_UEXTERNALDB_END",
)
FORBIDDEN = (
    "GETRANK", "GETTHREADID", "MUTEXINIT", "MUTEXLOCK", "MUTEXUNLOCK",
    "KP2TRACE", "KP3READ", "KP3BEGINWRITE", "KP3ENDWRITE", "KP2DIAG", "KP3ACCESS",
)


def validate(
    out: Path, deck: Path, transfer: Path, source: Path, job_id: str, solver_exit: int
) -> dict[str, object]:
    mapping = {
        "P3SM0_ENVIRONMENT.txt": "P3SB_ENVIRONMENT.txt",
        "P3SM0_JOB_RECORD.txt": "P3SB_JOB_RECORD.txt",
        "P3SM0_STATE_OUTPUT.csv": "P3SB_STATE_OUTPUT.csv",
        "P3SM0_RF_U.csv": "P3SB_RF_U.csv",
        "P3SM0_ENERGY.csv": "P3SB_ENERGY.csv",
        "p3sm0_serial.abaqus_stdout.log": "p3sb_baseline.abaqus_stdout.log",
        "p3sm0_serial.sta": "p3sb_baseline.sta",
    }
    with tempfile.TemporaryDirectory(prefix="p3sm0_baseline_gate_") as temporary:
        replay = Path(temporary)
        for source_name, target_name in mapping.items():
            candidate = out / source_name
            if candidate.is_file():
                shutil.copyfile(candidate, replay / target_name)
        base = baseline.validate(replay, deck, transfer, job_id, solver_exit)
        sequence_path = replay / "P3SB_INCREMENT_SEQUENCE.json"
        sequence = (
            json.loads(sequence_path.read_text(encoding="utf-8"))
            if sequence_path.is_file() else {"record_count": 0, "records": [], "sha256": ""}
        )

    failures = list(base["failures"])
    callback_path = out / "P3SM0_CALLBACK_SUMMARY.json"
    if callback_path.is_file():
        callback = json.loads(callback_path.read_text(encoding="utf-8"))
    else:
        callback = {"observed": {}, "counts": {}, "signal_11_present": False}
        failures.append("missing P3SM0_CALLBACK_SUMMARY.json")
    observed = callback.get("observed", {})
    callback_failures = []
    for marker in MARKERS:
        if not isinstance(observed, dict) or observed.get(marker) is not True:
            callback_failures.append(f"{marker} not observed")
    if callback.get("signal_11_present") is True:
        callback_failures.append("signal 11 present")

    source_text = source.read_text(encoding="utf-8", errors="replace").upper()
    if "SUBROUTINE UEXTERNALDB" not in source_text:
        callback_failures.append("UEXTERNALDB source missing")
    for token in FORBIDDEN:
        if token in source_text:
            callback_failures.append(f"forbidden source token present: {token}")
    failures.extend(callback_failures)

    if base["failures"]:
        classification = "stage_p3sm0_minimal_callback_serial_fail_validation"
    elif callback_failures:
        classification = "stage_p3sm0_minimal_callback_serial_fail_callback"
    else:
        classification = "stage_p3sm0_minimal_callback_serial_pass"
    status = {
        **{key: value for key, value in base.items() if key not in ("classification", "P3SB_ok", "failures")},
        "classification": classification,
        "P3SM0_ok": not failures,
        "callbacks": {marker: bool(isinstance(observed, dict) and observed.get(marker)) for marker in MARKERS},
        "callback_counts": callback.get("counts", {}),
        "signal_11_present": callback.get("signal_11_present", False),
        "rank_thread_utilities_present": any(token in source_text for token in ("GETRANK", "GETTHREADID")),
        "mutex_utilities_present": any(token in source_text for token in ("MUTEXINIT", "MUTEXLOCK", "MUTEXUNLOCK")),
        "diagnostic_shared_state_present": any(token in source_text for token in ("KP2DIAG", "KP3ACCESS")),
        "failures": failures,
    }
    (out / "P3SM0_INCREMENT_SEQUENCE.json").write_text(
        json.dumps(sequence, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out / "P3SM0_STATUS.json").write_text(
        json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    marker = out / "P3SM0_COMPLETION.ok"
    if marker.exists():
        marker.unlink()
    if not failures:
        marker.write_text(
            f"classification=stage_p3sm0_minimal_callback_serial_pass\njob_id={job_id}\n",
            encoding="utf-8",
        )
    return status


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--deck", type=Path, required=True)
    parser.add_argument("--transfer", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--job-id", default="unknown")
    parser.add_argument("--solver-exit", type=int, required=True)
    args = parser.parse_args()
    result = validate(
        args.out_dir, args.deck, args.transfer, args.source, args.job_id, args.solver_exit
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["P3SM0_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

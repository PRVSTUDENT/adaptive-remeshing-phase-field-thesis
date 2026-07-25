#!/usr/bin/env python3
"""Validate P3-SM0 gates plus the documented GETRANK call interface."""
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
    "MUTEXINIT", "MUTEXLOCK", "MUTEXUNLOCK", "GET_THREAD_ID", "GETTHREADID",
    "KP2TRACE", "KP3READ", "KP3BEGINWRITE", "KP3ENDWRITE", "KP2DIAG", "KP3ACCESS",
)


def routine_body(source: str, name: str) -> str:
    start = source.find(f"SUBROUTINE {name}")
    if start < 0:
        return ""
    following = source.find("\n      SUBROUTINE ", start + 1)
    block_data = source.find("\n      BLOCK DATA ", start + 1)
    stops = [position for position in (following, block_data) if position >= 0]
    return source[start:min(stops) if stops else len(source)]


def validate(
    out: Path, deck: Path, transfer: Path, source: Path, job_id: str, solver_exit: int
) -> dict[str, object]:
    mapping = {
        "P3SM1R_ENVIRONMENT.txt": "P3SB_ENVIRONMENT.txt",
        "P3SM1R_JOB_RECORD.txt": "P3SB_JOB_RECORD.txt",
        "P3SM1R_STATE_OUTPUT.csv": "P3SB_STATE_OUTPUT.csv",
        "P3SM1R_RF_U.csv": "P3SB_RF_U.csv",
        "P3SM1R_ENERGY.csv": "P3SB_ENERGY.csv",
        "p3sm1r_serial.abaqus_stdout.log": "p3sb_baseline.abaqus_stdout.log",
        "p3sm1r_serial.sta": "p3sb_baseline.sta",
    }
    with tempfile.TemporaryDirectory(prefix="p3sm1r_baseline_gate_") as temporary:
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
    callback_path = out / "P3SM1R_CALLBACK_SUMMARY.json"
    if callback_path.is_file():
        callback = json.loads(callback_path.read_text(encoding="utf-8"))
    else:
        callback = {"observed": {}, "counts": {}, "signal_11_present": False}
        failures.append("missing P3SM1R_CALLBACK_SUMMARY.json")
    observed = callback.get("observed", {})
    callback_failures = []
    for marker in MARKERS:
        if not isinstance(observed, dict) or observed.get(marker) is not True:
            callback_failures.append(f"{marker} not observed")
    if callback.get("signal_11_present") is True:
        callback_failures.append("signal 11 present")
    before = callback.get("before_count", 0)
    after = callback.get("after_count", 0)
    returned = callback.get("returned_process_ids", [])
    unique = callback.get("unique_process_ids", [])
    if not isinstance(before, int) or before < 1:
        callback_failures.append("before marker not observed")
    if not isinstance(after, int) or after < 1:
        callback_failures.append("after marker not observed")
    if before != after or callback.get("unmatched_before_calls", 0) != 0:
        callback_failures.append("GETRANK before/after mismatch")
    if not isinstance(returned, list) or not returned:
        callback_failures.append("returned process-ID list empty")
    elif any(not isinstance(value, int) or isinstance(value, bool) or value < 0 or value >= 1
             for value in returned):
        callback_failures.append("returned process ID outside MPI rank count 1")
    if unique != [0]:
        callback_failures.append("unique returned process IDs must equal [0]")

    source_text_raw = source.read_text(encoding="utf-8", errors="replace")
    source_text = source_text_raw.upper()
    if "SUBROUTINE UEXTERNALDB" not in source_text:
        callback_failures.append("UEXTERNALDB source missing")
    uel = routine_body(source_text, "UEL")
    if "CALL GETRANK(KPROCESSNUM)" not in uel:
        callback_failures.append("CALL GETRANK(KPROCESSNUM) not inside UEL")
    if not all(token in uel for token in ("JELEM.EQ.1", "KSTEP.EQ.1", "KINC.EQ.1")):
        callback_failures.append("GETRANK UEL control condition missing")
    if "GETRANK" in source_text.replace(uel, "", 1):
        callback_failures.append("GETRANK present outside UEL")
    if "GETRANK(" in source_text.replace("CALL GETRANK(", ""):
        callback_failures.append("GETRANK function expression present")
    runtime_text = ""
    for candidate in (
        out / "p3sm1r_serial.abaqus_stdout.log",
        out / "p3sm1r_serial.msg",
    ):
        if candidate.is_file():
            runtime_text += candidate.read_text(
                encoding="utf-8", errors="replace"
            ).lower()
    if "undefined symbol: getrank_" in runtime_text:
        callback_failures.append("unresolved documented getrank_ symbol")
    for token in FORBIDDEN:
        if token in source_text:
            callback_failures.append(f"forbidden source token present: {token}")
    failures.extend(callback_failures)

    if base["failures"]:
        classification = "stage_p3sm1r_getrank_serial_fail_validation"
    elif callback_failures:
        if (before and not after) or callback.get("signal_11_present") is True:
            classification = "stage_p3sm1r_getrank_serial_fail_identifier"
        else:
            classification = "stage_p3sm1r_getrank_serial_fail_callback"
    else:
        classification = "stage_p3sm1r_getrank_serial_pass"
    status = {
        **{key: value for key, value in base.items() if key not in ("classification", "P3SB_ok", "failures")},
        "classification": classification,
        "P3SM1R_ok": not failures,
        "callbacks": {marker: bool(isinstance(observed, dict) and observed.get(marker)) for marker in MARKERS},
        "callback_counts": callback.get("counts", {}),
        "signal_11_present": callback.get("signal_11_present", False),
        "before_count": before,
        "after_count": after,
        "returned_process_ids": returned,
        "unique_process_ids": unique,
        "unmatched_before_calls": callback.get("unmatched_before_calls", 0),
        "rank_utility_present": "CALL GETRANK(KPROCESSNUM)" in source_text,
        "mutex_utilities_present": any(token in source_text for token in ("MUTEXINIT", "MUTEXLOCK", "MUTEXUNLOCK")),
        "diagnostic_shared_state_present": any(token in source_text for token in ("KP2DIAG", "KP3ACCESS")),
        "failures": failures,
    }
    (out / "P3SM1R_INCREMENT_SEQUENCE.json").write_text(
        json.dumps(sequence, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out / "P3SM1R_STATUS.json").write_text(
        json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    marker = out / "P3SM1R_COMPLETION.ok"
    if marker.exists():
        marker.unlink()
    if not failures:
        marker.write_text(
            f"classification=stage_p3sm1r_getrank_serial_pass\njob_id={job_id}\n",
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
    return 0 if result["P3SM1R_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

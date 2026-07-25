#!/usr/bin/env python3
"""Validate bounded one-rank/four-thread P3-T4 characterization."""
from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path

import compare_p3t4_serial_reference as comparator
import validate_p3sb_baseline_serial as baseline


BASE_MARKERS = (
    "P3SM0_UEXTERNALDB_LOP0", "P3SM0_UEL_OBSERVED",
    "P3SM0_UMAT_OBSERVED", "P3SM0_UEXTERNALDB_END",
)


def routine(source: str, name: str) -> str:
    start = source.find(f"SUBROUTINE {name}")
    if start < 0:
        return ""
    following = source.find("\n      SUBROUTINE ", start + 1)
    block = source.find("\n      BLOCK DATA ", start + 1)
    stops = [value for value in (following, block) if value >= 0]
    return source[start:min(stops) if stops else len(source)]


def validate(out: Path, deck: Path, transfer: Path, source: Path,
             reference: Path, job_id: str, solver_exit: int) -> dict[str, object]:
    mapping = {
        "P3T4_ENVIRONMENT.txt": "P3SB_ENVIRONMENT.txt",
        "P3T4_JOB_RECORD.txt": "P3SB_JOB_RECORD.txt",
        "P3T4_STATE_OUTPUT.csv": "P3SB_STATE_OUTPUT.csv",
        "P3T4_RF_U.csv": "P3SB_RF_U.csv",
        "P3T4_ENERGY.csv": "P3SB_ENERGY.csv",
        "p3t4_threaded.abaqus_stdout.log": "p3sb_baseline.abaqus_stdout.log",
        "p3t4_threaded.sta": "p3sb_baseline.sta",
    }
    with tempfile.TemporaryDirectory(prefix="p3t4_baseline_") as temporary:
        replay = Path(temporary)
        for source_name, target_name in mapping.items():
            candidate = out / source_name
            if candidate.is_file():
                shutil.copyfile(candidate, replay / target_name)
        base = baseline.validate(replay, deck, transfer, job_id, solver_exit)
        sequence = json.loads(
            (replay / "P3SB_INCREMENT_SEQUENCE.json").read_text(encoding="utf-8")
        )
    (out / "P3T4_INCREMENT_SEQUENCE.json").write_text(
        json.dumps(sequence, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    failures = list(base["failures"])
    diag_path = out / "P3T4_DIAGNOSTIC_SUMMARY.json"
    diag = (json.loads(diag_path.read_text(encoding="utf-8"))
            if diag_path.is_file() else {})
    if not diag:
        failures.append("missing P3T4_DIAGNOSTIC_SUMMARY.json")
    markers = diag.get("base_markers", {})
    for marker in BASE_MARKERS:
        if not isinstance(markers, dict) or int(markers.get(marker, 0)) < 1:
            failures.append(f"{marker} not observed")

    ranks = diag.get("ranks", [])
    threads = diag.get("threads", [])
    callback_threads = diag.get("callback_threads", {})
    exercised = len(set(callback_threads.get("UEL", []))
                    | set(callback_threads.get("UMAT", []))) >= 2
    if ranks != [0]:
        failures.append("rank IDs must equal [0]")
    if (not isinstance(threads, list) or not threads
            or any(not isinstance(value, int) or value < 0 or value > 3
                   for value in threads)):
        failures.append("thread IDs must be nonempty and within [0,3]")
    if int(diag.get("unmatched_begin_end_records", 0)) != 0:
        failures.append("unmatched diagnostic begin/end records")
    duplicate = int(diag.get("duplicate_initialization_count", 0))
    initialization_writes = int(diag.get("initialization_write_count", 0))
    conflicts = int(diag.get("concurrent_conflict_count", 0))
    if initialization_writes != 8:
        failures.append("transfer initialization was not exactly once per state location")
    if duplicate:
        failures.append("duplicate initialization observed")
    if diag.get("signal_11_present") is True:
        failures.append("signal 11 present")

    source_text = source.read_text(encoding="utf-8", errors="replace").upper()
    external = routine(source_text, "UEXTERNALDB")
    if "GETRANK" in external or "GET_THREAD_ID" in external or "GETTHREADID" in external:
        failures.append("identifier utility present in UEXTERNALDB")
    for required in (
        "#INCLUDE <SMAASPUSERSUBROUTINES.HDR>",
        "CALL GETRANK(RANK)", "THREAD=GET_THREAD_ID()",
        "CALL MUTEXINIT(91)", "CALL MUTEXLOCK(91)", "CALL MUTEXUNLOCK(91)",
    ):
        if required not in source_text:
            failures.append(f"source requirement absent: {required}")
    compact = source_text.replace(" ", "")
    if "RANK=GETRANK()" in compact or "GETTHREADID()" in compact:
        failures.append("rejected identifier spelling present")

    runtime = ""
    for name in ("p3t4_threaded.abaqus_stdout.log", "p3t4_threaded.msg"):
        candidate = out / name
        if candidate.is_file():
            runtime += candidate.read_text(encoding="utf-8", errors="replace").lower()
    unresolved_identifier = any(token in runtime for token in (
        "undefined symbol: getrank_", "undefined symbol: get_thread_id_",
    ))
    unresolved_mutex = any(token in runtime for token in (
        "undefined symbol: mutexinit_", "undefined symbol: mutexlock_",
        "undefined symbol: mutexunlock_",
    ))
    unresolved = unresolved_identifier or unresolved_mutex
    deadlock = "walltime" in runtime and "exceeded" in runtime
    if unresolved:
        failures.append("unresolved identifier or mutex symbol")
    if deadlock:
        failures.append("deadlock or walltime termination")

    comparison = comparator.compare(out, reference)
    (out / "P3T4_SERIAL_COMPARISON.json").write_text(
        json.dumps(comparison, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    scientific_match = comparison["serial_equivalent"]
    if not scientific_match:
        failures.append("serial scientific reference mismatch")
    if conflicts:
        failures.append("shared-state conflict observed")
    if not exercised:
        failures.append("multiple callback threads not observed")

    if conflicts:
        classification = "stage_p3t4_shared_state_conflict_observed"
    elif not scientific_match:
        classification = "stage_p3t4_scientific_mismatch"
    elif not exercised and not base["failures"]:
        classification = "stage_p3t4_threading_not_exercised"
    elif unresolved_mutex:
        classification = "stage_p3t4_threaded_fail_mutex"
    elif unresolved_identifier:
        classification = "stage_p3t4_threaded_fail_identifier"
    elif deadlock:
        classification = "stage_p3t4_threaded_fail_deadlock"
    elif failures:
        classification = "stage_p3t4_threaded_fail_validation"
    else:
        classification = "stage_p3t4_threaded_characterization_pass"
    status = {
        **{key: value for key, value in base.items()
           if key not in ("classification", "P3SB_ok", "failures")},
        "classification": classification,
        "P3T4_ok": not failures,
        "ranks": ranks,
        "threads": threads,
        "callback_threads": callback_threads,
        "threading_exercised": exercised,
        "unmatched_begin_end_records": diag.get("unmatched_begin_end_records", 0),
        "duplicate_initialization_count": duplicate,
        "initialization_write_count": initialization_writes,
        "concurrent_conflict_count": conflicts,
        "serial_reference_equivalent": scientific_match,
        "unresolved_utility_symbol": unresolved,
        "deadlock_or_walltime_termination": deadlock,
        "failures": failures,
    }
    (out / "P3T4_STATUS.json").write_text(
        json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    marker = out / "P3T4_COMPLETION.ok"
    if marker.exists():
        marker.unlink()
    if not failures:
        marker.write_text(
            f"classification={classification}\njob_id={job_id}\n",
            encoding="utf-8",
        )
    return status


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--deck", type=Path, required=True)
    parser.add_argument("--transfer", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--job-id", default="unknown")
    parser.add_argument("--solver-exit", type=int, required=True)
    args = parser.parse_args()
    status = validate(args.out_dir, args.deck, args.transfer, args.source,
                      args.reference, args.job_id, args.solver_exit)
    print(json.dumps(status, sort_keys=True))
    return 0 if status["P3T4_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

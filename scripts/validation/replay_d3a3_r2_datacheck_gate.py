#!/usr/bin/env python3
"""Replay the D3A3-R2 datacheck postcheck from preserved Abaqus evidence."""

import argparse
import json
import re
from pathlib import Path


CLASSIFICATION = "stage_d3a3_r2_compile_datacheck_pass_postcheck_replay"
EXPECTED_JOB = "1377393.mmaster02"
EXPECTED_PATH = (
    "/scratch9/pr21vyci/adaptive-remeshing/runs/"
    "d3a3_r2_datacheck_r2_1377393.mmaster02/d3_transfer_h.dat"
)
EXPECTED_SHA = "4689ea5c10c0972e69ba46f8676a326c8b011b98faa8031c7c26cfb218607cd9"


def read_text(path):
    return path.read_text(encoding="utf-8", errors="replace")


def reconstruct_runtime_h_path(msg_path):
    lines = read_text(msg_path).splitlines()
    for idx, line in enumerate(lines):
        if "D3A3-R2 H FILE PATH" not in line:
            continue
        parts = []
        for next_idx in range(idx + 1, len(lines)):
            parts.append(lines[next_idx])
            if "d3_transfer_h.dat" in lines[next_idx]:
                raw = "".join(parts)
                reconstructed = re.sub(r"[ \t\r\f\n]+", "", raw)
                return {
                    "path_token_line": idx + 1,
                    "path_end_line": next_idx + 1,
                    "raw_lines": parts,
                    "reconstructed_path": reconstructed,
                }
    raise ValueError("D3A3-R2 H FILE PATH block ending in d3_transfer_h.dat not found")


def require(condition, failures, message):
    if not condition:
        failures.append(message)


def replay(evidence_dir, out_dir, expected_path):
    msg_path = evidence_dir / "D3A3_R2_DATACHECK.msg"
    stdout_path = evidence_dir / "D3A3_R2_DATACHECK_STDOUT.log"
    runtime_path = evidence_dir / "D3A3_R2_RUNTIME_STATE_VALIDATION.json"
    failure_path = evidence_dir / "D3A3_R2_R2_FAILURE_ANALYSIS.json"
    record_path = evidence_dir / "D3A3_R2_DATACHECK_JOB_RECORD.txt"
    required_inputs = [msg_path, stdout_path, runtime_path, failure_path, record_path]
    missing = [str(path) for path in required_inputs if not path.exists()]
    if missing:
        raise FileNotFoundError("missing replay inputs: " + ", ".join(missing))

    msg = read_text(msg_path)
    stdout = read_text(stdout_path)
    record = read_text(record_path)
    runtime = json.loads(read_text(runtime_path))
    failure = json.loads(read_text(failure_path))
    path_reconstruction = reconstruct_runtime_h_path(msg_path)

    combined = "\n".join([msg, stdout])
    failures = []
    require("End Compiling Abaqus/Standard User Subroutines" in stdout, failures, "compile completion token missing")
    require("End Linking Abaqus/Standard User Subroutines" in stdout, failures, "link completion token missing")
    require("End Analysis Input File Processor" in stdout, failures, "input processing completion token missing")
    require("End Abaqus/Standard Analysis" in stdout, failures, "Standard datacheck completion token missing")
    require(
        "Abaqus JOB D3A3_R2_DATACHECK COMPLETED" in stdout,
        failures,
        "Abaqus job completion token missing",
    )
    require(
        re.search(r"D3A3-R2 H LOAD COMPLETE\s+25600", combined) is not None,
        failures,
        "runtime H load-complete 25600 token missing",
    )
    require("D3A3-R2 premature runtime H EOF" not in combined, failures, "premature runtime H EOF token present")
    require("D3A3-R2 runtime H read error" not in combined, failures, "runtime H read-error token present")
    require(path_reconstruction["reconstructed_path"] == expected_path, failures, "reconstructed runtime H path mismatch")
    require(int(runtime.get("records", -1)) == 25600, failures, "runtime records != 25600")
    require(int(runtime.get("duplicates", -1)) == 0, failures, "runtime duplicates != 0")
    require(int(runtime.get("missing_records", -1)) == 0, failures, "runtime missing_records != 0")
    require(runtime.get("sha256") == EXPECTED_SHA, failures, "runtime H SHA256 changed")
    require(failure.get("pbs_exit_status") == 10, failures, "preserved PBS exit status is not 10")
    require(failure.get("runtime_H_load_complete_25600") is True, failures, "failure analysis lacks load-complete evidence")
    require("job_id=1377393.mmaster02" in record, failures, "job record does not name 1377393.mmaster02")

    out_dir.mkdir(parents=True, exist_ok=True)
    path_status = {
        "classification": CLASSIFICATION if not failures else "stage_d3a3_r2_postcheck_replay_fail_path",
        "evidence_job": EXPECTED_JOB,
        "expected_path": expected_path,
        "path_reconstructable": not failures or path_reconstruction["reconstructed_path"] == expected_path,
        **path_reconstruction,
        "failures": [f for f in failures if "path" in f.lower()],
    }
    status = {
        "classification": CLASSIFICATION if not failures else "stage_d3a3_r2_postcheck_replay_fail",
        "evidence_job": EXPECTED_JOB,
        "pbs_exit_status": 10,
        "abaqus_datacheck_pass": not failures,
        "runtime_H_load_complete_25600": re.search(r"D3A3-R2 H LOAD COMPLETE\s+25600", combined) is not None,
        "wrapper_path_gate_false_negative": True,
        "postcheck_replay_pass": not failures,
        "new_pbs_job_submitted": False,
        "records": runtime.get("records"),
        "duplicates": runtime.get("duplicates"),
        "missing_records": runtime.get("missing_records"),
        "runtime_H_sha256": runtime.get("sha256"),
        "reconstructed_runtime_H_path": path_reconstruction["reconstructed_path"],
        "failures": failures,
    }
    report = [
        "# D3A3-R2 Postcheck Replay",
        "",
        f"- Classification: `{status['classification']}`",
        f"- Evidence job: `{EXPECTED_JOB}`",
        "- New PBS job submitted: `false`",
        "- Preserved PBS exit status: `10`",
        f"- Reconstructed runtime-H path: `{path_reconstruction['reconstructed_path']}`",
        "- Abaqus compile/link/input/datacheck completion tokens: `pass`" if not failures else "- Replay gates: `fail`",
        f"- Runtime-H records: `{runtime.get('records')}`",
        f"- Runtime-H duplicates: `{runtime.get('duplicates')}`",
        f"- Runtime-H missing records: `{runtime.get('missing_records')}`",
        f"- Runtime-H SHA256: `{runtime.get('sha256')}`",
        "- Marker meaning: compile/datacheck scientific gate accepted by deterministic replay of the failed wrapper path check.",
        "",
    ]
    if failures:
        report.extend(["## Failures", ""])
        report.extend(f"- {failure}" for failure in failures)
        report.append("")

    (out_dir / "D3A3_R2_PATH_RECONSTRUCTION.json").write_text(
        json.dumps(path_status, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out_dir / "D3A3_R2_POSTCHECK_REPLAY_STATUS.json").write_text(
        json.dumps(status, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out_dir / "D3A3_R2_POSTCHECK_REPLAY_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    if not failures:
        (out_dir / "D3A3_R2_COMPILE.ok").write_text(CLASSIFICATION + "\n", encoding="utf-8")
    return 0 if not failures else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--extract-path", type=Path, help="Only reconstruct and print runtime-H path from this .msg file.")
    parser.add_argument(
        "--evidence-dir",
        type=Path,
        default=Path("runs/hpc/stage_d3/interrupted_transfer/target_ingestion_compile_r2_r2"),
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("runs/hpc/stage_d3/interrupted_transfer/target_ingestion_compile_r2_r2_replay"),
    )
    parser.add_argument("--expected-path", default=EXPECTED_PATH)
    args = parser.parse_args()
    if args.extract_path:
        print(reconstruct_runtime_h_path(args.extract_path)["reconstructed_path"])
        return 0
    return replay(args.evidence_dir, args.out_dir, args.expected_path)


if __name__ == "__main__":
    raise SystemExit(main())

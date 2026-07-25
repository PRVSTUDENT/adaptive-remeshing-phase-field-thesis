#!/usr/bin/env python3
"""Consume Mode-II H0 datacheck or solver authorization after valid qsub."""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
from pathlib import Path

from validate_mode_ii_h0_submission_preflight import REQUIRED_FALSE, validate_authorization

JOB_ID_RE = re.compile(r"^[0-9]+(?:\.[A-Za-z0-9_-]+)?$")


def consume(path: Path, job_id: str, revision: str, kind: str) -> dict:
    if not JOB_ID_RE.fullmatch(job_id):
        raise ValueError("invalid PBS job ID; authorization not consumed")
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("invalid revision; authorization not consumed")
    if kind == "datacheck":
        data = validate_authorization(path, require_datacheck=True, require_solver=False)
        data.update(
            {
                "classification": "stage_f_mode_ii_h0_datacheck_submitted",
                "datacheck_authorized": False,
                "datacheck_submissions_used": 1,
                "datacheck_job_id": job_id,
                "datacheck_submitted_revision": revision,
            }
        )
    elif kind == "solver":
        data = validate_authorization(path, require_datacheck=False, require_solver=True)
        data.update(
            {
                "classification": "stage_f_mode_ii_h0_solver_submitted",
                "solver_authorized": False,
                "solver_submissions_used": 1,
                "solver_job_id": job_id,
                "solver_submitted_revision": revision,
            }
        )
    else:
        raise ValueError("kind must be datacheck or solver")
    for key in REQUIRED_FALSE:
        data[key] = False
    data["automatic_retry_authorized"] = False
    descriptor, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authorization", type=Path, required=True)
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--kind", choices=("datacheck", "solver"), required=True)
    args = parser.parse_args()
    try:
        result = consume(args.authorization, args.job_id, args.revision, args.kind)
    except ValueError as exc:
        print(f"Mode-II H0 authorization consumption blocked: {exc}")
        return 20
    print(f"Mode-II H0 {args.kind} authorization consumed: {result.get(args.kind + '_job_id')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

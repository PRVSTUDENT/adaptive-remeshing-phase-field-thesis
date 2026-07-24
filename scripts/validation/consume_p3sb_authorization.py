#!/usr/bin/env python3
"""Atomically consume P3-SB authorization after a valid qsub response."""
from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
from pathlib import Path

from validate_p3sb_submission_preflight import REQUIRED_FALSE, validate_authorization


JOB_ID_RE = re.compile(r"^[0-9]+(?:\.[A-Za-z0-9_-]+)?$")


def consume(path: Path, job_id: str, revision: str) -> dict[str, object]:
    if not JOB_ID_RE.fullmatch(job_id):
        raise ValueError("invalid PBS job ID; authorization not consumed")
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("invalid revision; authorization not consumed")
    data = validate_authorization(path, require_submit=True)
    data.update({
        "classification": "stage_p3sb_baseline_serial_submitted",
        "p3sb_submission_authorized": False,
        "p3sb_submissions_used": 1,
        "p3sb_job_id": job_id,
        "p3sb_submitted_revision": revision,
    })
    for key in REQUIRED_FALSE:
        data[key] = False
    descriptor, temporary = tempfile.mkstemp(
        prefix=path.name + ".", suffix=".tmp", dir=str(path.parent)
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--authorization", type=Path, required=True)
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--revision", required=True)
    args = parser.parse_args()
    try:
        result = consume(args.authorization, args.job_id, args.revision)
    except ValueError as exc:
        print(f"P3-SB authorization consumption blocked: {exc}")
        return 20
    print(f"P3-SB authorization consumed: {result['p3sb_job_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

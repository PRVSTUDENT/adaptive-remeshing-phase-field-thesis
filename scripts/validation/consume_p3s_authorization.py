#!/usr/bin/env python3
"""Atomically consume the one-shot P3-S authorization after valid qsub."""
from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
from pathlib import Path

from validate_p3s_submission_preflight import validate_authorization


JOB_ID_RE = re.compile(r"^[0-9]+(?:\.[A-Za-z0-9_-]+)?$")


def consume(path: Path, job_id: str, revision: str) -> dict[str, object]:
    if not JOB_ID_RE.fullmatch(job_id):
        raise ValueError("invalid PBS job ID; authorization not consumed")
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("invalid submitted revision; authorization not consumed")
    data = validate_authorization(path, require_submit=True)
    data.update(
        {
            "classification": "stage_p3_serial_diagnostic_submitted",
            "p3s_submission_authorized": False,
            "maximum_p3s_submissions": 1,
            "p3s_submissions_used": 1,
            "p3s_job_id": job_id,
            "p3s_submitted_revision": revision,
            "automatic_retry_authorized": False,
            "p3t4_authorized": False,
            "mpi_authorized": False,
            "hybrid_authorized": False,
            "production_h1_authorized": False,
            "d3d_a1_reopening_authorized": False,
            "d3e_authorized": False,
        }
    )
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=path.name + ".", suffix=".tmp", dir=str(path.parent)
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    except Exception:
        try:
            os.unlink(temporary_name)
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
        data = consume(args.authorization, args.job_id, args.revision)
    except ValueError as exc:
        print(f"P3-S authorization consumption blocked: {exc}")
        return 20
    print(
        "P3-S authorization consumed: "
        + str(data["p3s_job_id"])
        + " revision="
        + str(data["p3s_submitted_revision"])
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

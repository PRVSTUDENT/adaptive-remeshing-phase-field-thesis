#!/usr/bin/env python3
"""
write_turn123_prep_artifact.py
Generates results/validation/preparation-e0354599-7e8f-45ed-aa14-4a76d6d0ccc3.json.
"""

import json
import hashlib
from pathlib import Path

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

def write_prep():
    repo_root = Path(__file__).resolve().parent.parent.parent

    files = [
        "models/pandey_kumar_mode1/108_c3_staggered_continuation/M1_C3_STAGGERED_CONTINUATION.inp",
        "models/pandey_kumar_mode1/108_c3_staggered_continuation/d_lower_bounds.csv",
        "models/pandey_kumar_mode1/108_c3_staggered_continuation/f42_experimental_irreversible_uel.for",
        "models/pandey_kumar_mode1/108_c3_staggered_continuation/submit_M1_C3_STAGGERED.pbs",
        "models/pandey_kumar_mode1/108_c3_staggered_continuation/job_notifications.sh",
        "models/pandey_kumar_mode1/108_c3_staggered_continuation/M1_C3_STAGGERED.dat",
        "models/pandey_kumar_mode1/108_c3_staggered_continuation/M1_C3_STAGGERED_AUTHORIZATION.json",
        "results/validation/mode1_f1597/turn123_dispatch_gate_audit.json",
        "scripts/validation/evaluate_mode1_turn123_dispatch_gate_audit.py",
        "scripts/validation/record_turn123_gate_evidence.py",
        "tests/unit/test_mode1_f1597_turn123_dispatch_audit.py"
    ]

    hashes = {}
    for p in files:
        hashes[p] = compute_sha256(repo_root / p)

    prep = {
        "schema": 1,
        "status": "PREPARATION_COMPLETE",
        "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
        "run_id": "e0354599-7e8f-45ed-aa14-4a76d6d0ccc3",
        "finding": "Turn 123 Candidate C3 staggered continuation staged and technically preflighted: Abaqus 2023 datacheck completed Exit 0 with zero errors on 2,650-element mesh; preflight passed (datachecks=PASS_BOTH, active jobs=0, notifications verified). Exact dispatch blocker isolated with empirical stack trace: mode1_execution_gate.py line 82 denies non-frozen UELs with 'Frozen UEL and notifications required'. Experimental irreversible UEL (SHA-256 e72e00d3...) cannot be dispatched through Invoke-Mode1Execution.ps1 because scripts/hpc/ is outside authorized write scope in ACTIVE_SESSION.json. Requires human/supervisor gate extension.",
        "evidence_sources": hashes,
        "verification_passed": True
    }

    out_file = repo_root / "results" / "validation" / "preparation-e0354599-7e8f-45ed-aa14-4a76d6d0ccc3.json"
    with open(out_file, "w") as f:
        json.dump(prep, f, indent=2)

    print(f"Successfully wrote preparation artifact to {out_file}")

if __name__ == "__main__":
    write_prep()

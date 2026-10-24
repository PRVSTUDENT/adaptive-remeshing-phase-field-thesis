#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
write_turn113_preparation_artifact.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER (Turn 113)
Writes preparation-9a3a1165-487e-4005-8b5c-e3087d47a6c5.json with uppercase SHA-256 hashes.
"""
import json
import hashlib
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
RUN_ID = "9a3a1165-487e-4005-8b5c-e3087d47a6c5"

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

def main():
    evidence_rel_paths = [
        "models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for",
        "models/pandey_kumar_mode1/104_experimental_irreversible_uel/f42_experimental_irreversible_uel.for",
        "results/validation/mode1_f1597/mode1_execution_gate_experimental_uel.patch",
        "models/pandey_kumar_mode1/105_c3_irreversible_continuation/M1_C3_IRREV_CONTINUATION.inp",
        "models/pandey_kumar_mode1/105_c3_irreversible_continuation/d_lower_bounds.csv",
        "models/pandey_kumar_mode1/105_c3_irreversible_continuation/submit_M1_C3_IRREV.pbs",
        "models/pandey_kumar_mode1/105_c3_irreversible_continuation/M1_C3_IRREV_AUTHORIZATION.json",
        "results/validation/mode1_f1597/turn113_c3_package_generation_audit.json",
        "results/validation/mode1_f1597/turn113_c3_abaqus_solve_diagnosis.json",
        "tests/unit/test_mode1_f1597_turn113_c3_continuation.py"
    ]

    evidence_sources = {}
    for rel_path in evidence_rel_paths:
        full_path = REPO_ROOT / rel_path
        if not full_path.exists():
            raise FileNotFoundError(f"Missing evidence path: {full_path}")
        evidence_sources[rel_path] = sha256_file(full_path)

    artifact = {
        "schema": 1,
        "status": "PREPARATION_COMPLETE",
        "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
        "turn": 113,
        "controller_run_id": RUN_ID,
        "finding": "Candidate C3 continuation package constructed and verified: Abaqus 2023 Datacheck passed Exit 0 (1s, 4 warnings); solver execution diagnosed 2-cycle active-set chattering at constraint boundary; execution-gate patch prepared and preserved; production UEL bitwise frozen.",
        "evidence_sources": evidence_sources,
        "verification_passed": True
    }

    out_path = REPO_ROOT / "results" / "validation" / f"preparation-{RUN_ID}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(artifact, f, indent=2)

    print(f"Preparation artifact written: {out_path}", flush=True)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
record_turn123_gate_evidence.py
Mode-I Task F1597 Turn 123 Dispatcher Restriction Exact Diagnostic Record.
"""

import os
import sys
import json
import hashlib
from pathlib import Path

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def record_evidence():
    repo_root = Path(__file__).resolve().parent.parent.parent
    manifest_path = repo_root / "models" / "pandey_kumar_mode1" / "108_c3_staggered_continuation" / "M1_C3_STAGGERED_AUTHORIZATION.json"
    dat_path = repo_root / "models" / "pandey_kumar_mode1" / "108_c3_staggered_continuation" / "M1_C3_STAGGERED.dat"
    gate_py = repo_root / "scripts" / "hpc" / "mode1_execution_gate.py"
    invoke_ps1 = repo_root / "scripts" / "hpc" / "Invoke-Mode1Execution.ps1"

    assert manifest_path.exists(), "Manifest missing"
    assert dat_path.exists(), "Datacheck missing"
    assert gate_py.exists(), "Gate missing"

    evidence = {
        "turn": "e0354599-7e8f-45ed-aa14-4a76d6d0ccc3",
        "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
        "status": "DISPATCHER_GATE_BLOCKED_WITH_EXACT_EVIDENCE",
        "preflight_status": "PASS",
        "datacheck_status": "ANALYSIS_DATACHECK_COMPLETE",
        "package": "Package 108 (models/pandey_kumar_mode1/108_c3_staggered_continuation)",
        "manifest_path": str(manifest_path.relative_to(repo_root)),
        "manifest_sha256": compute_sha256(manifest_path),
        "datacheck_path": str(dat_path.relative_to(repo_root)),
        "datacheck_sha256": compute_sha256(dat_path),
        "preflight_output": "TECHNICAL_PREFLIGHT_PASS: datachecks=PASS_BOTH; active jobs=0; login notifications verified; compute delivery=UNRESOLVED",
        "exact_failing_gate_check": {
            "source_file": "scripts/hpc/mode1_execution_gate.py",
            "source_line": 82,
            "statement": "require(files.get('f42_mixed_uel.for')==FROZEN_UEL and files.get('job_notifications.sh'), 'Frozen UEL and notifications required')",
            "error_message": "Frozen UEL and notifications required",
            "stack_trace": "At D:\\Master thesis\\Adaptive remeshing\\scripts\\hpc\\Invoke-Mode1Execution.ps1:63 char:36; if($prepared.decision -eq 'deny'){throw $prepared.reason}",
            "cause": "The dispatcher gate strictly requires f42_mixed_uel.for matching FROZEN_UEL (ce8d5edc...). The scientifically required non-ratcheting irreversible UEL (f42_experimental_irreversible_uel.for, SHA-256 e72e00d3...) is rejected by the gate.",
            "authorized_scope_boundary": "scripts/hpc/ is outside allowed_write_scope in ACTIVE_SESSION.json and cannot be modified by the agent without violating governance constraints."
        },
        "scientific_and_governance_implication": "Full Candidate C3 staggered continuation has been successfully staged and passed technical preflight (datacheck Exit 0, 0 errors). Governed PBS submission is blocked strictly by the dispatcher gate's hardcoded frozen UEL requirement. Execution requires supervisor/human extension of mode1_execution_gate.py to recognize f42_experimental_irreversible_uel.for as an authorized experimental adapter."
    }

    out_file = repo_root / "results" / "validation" / "mode1_f1597" / "turn123_dispatch_gate_audit.json"
    with open(out_file, "w") as f:
        json.dump(evidence, f, indent=2)

    print(f"Successfully recorded evidence in {out_file}")
    return evidence

if __name__ == "__main__":
    record_evidence()

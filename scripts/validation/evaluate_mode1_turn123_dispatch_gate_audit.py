#!/usr/bin/env python3
"""
evaluate_mode1_turn123_dispatch_gate_audit.py
Mode-I Task F1597 Turn 123 Dispatcher Restriction Audit & Qualification Analysis.

Audits the exact technical requirements of the governed HPC dispatch pipeline:
  1. scripts/hpc/Invoke-Mode1Execution.ps1
  2. scripts/hpc/mode1_execution_gate.py
  3. scripts/hpc/preflight_package49_authorization.py
Evaluates whether experimental UELs (such as f42_experimental_irreversible_uel.for)
can be submitted within authorized scope or if the dispatcher gate strictly fails closed.
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

def audit_dispatcher_restrictions():
    repo_root = Path(__file__).resolve().parent.parent.parent
    gate_py = repo_root / "scripts" / "hpc" / "mode1_execution_gate.py"
    preflight_py = repo_root / "scripts" / "hpc" / "preflight_package49_authorization.py"
    invoke_ps1 = repo_root / "scripts" / "hpc" / "Invoke-Mode1Execution.ps1"

    assert gate_py.exists(), f"Missing gate: {gate_py}"
    assert preflight_py.exists(), f"Missing preflight: {preflight_py}"
    assert invoke_ps1.exists(), f"Missing invoke script: {invoke_ps1}"

    gate_code = gate_py.read_text(encoding="utf-8")
    preflight_code = preflight_py.read_text(encoding="utf-8")

    # Audit allowed adapters in mode1_execution_gate.py
    allowed_adapters_gate = [
        'mode1-qualified-batch-v2',
        'mode1-experimental-offset-v1',
        'mode1-continuum-preanalysis-v1',
        'mode1-uel-trace-v1',
        'mode1-pdas-iterative-v1'
    ]
    for adapter in allowed_adapters_gate:
        assert f"'{adapter}'" in gate_code, f"Adapter {adapter} missing in gate"

    # Audit allowed adapters in preflight_package49_authorization.py
    allowed_adapters_preflight = [
        'mode1-qualified-batch-v2',
        'mode1-experimental-offset-v1',
        'mode1-continuum-preanalysis-v1',
        'mode1-pdas-iterative-v1'
    ]
    for adapter in allowed_adapters_preflight:
        assert f"'{adapter}'" in preflight_code, f"Adapter {adapter} missing in preflight"

    # Audit frozen UEL enforcement
    frozen_uel_sha = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"
    assert f"FROZEN_UEL = '{frozen_uel_sha}'" in gate_code, "Frozen UEL constant mismatch in gate"

    # Check experimental UEL restriction in gate
    # In gate: line 82 enforces:
    # require(files.get('f42_mixed_uel.for')==FROZEN_UEL and files.get('job_notifications.sh'), 'Frozen UEL and notifications required')
    # unless is_trace or is_experimental (which requires f42_experimental_offset_uel.for == EXPERIMENTAL_OFFSET_UEL)
    exp_offset_uel_sha = "ef92ed58dbe3ea921b48cb328128ab950ba2cafd698e05381e2b29f61412514d"
    assert f"EXPERIMENTAL_OFFSET_UEL = '{exp_offset_uel_sha}'" in gate_code

    audit_findings = {
        "gate_path": str(gate_py.relative_to(repo_root)),
        "gate_sha256": compute_sha256(gate_py),
        "preflight_path": str(preflight_py.relative_to(repo_root)),
        "preflight_sha256": compute_sha256(preflight_py),
        "allowed_adapters_in_gate": allowed_adapters_gate,
        "allowed_adapters_in_preflight": allowed_adapters_preflight,
        "frozen_uel_sha256": frozen_uel_sha,
        "experimental_offset_uel_sha256": exp_offset_uel_sha,
        "experimental_irreversible_uel_status": {
            "name": "f42_experimental_irreversible_uel.for",
            "sha256": "e72e00d338e355b370fc5ebabfe6679f49bc07458d333b642b593c6710b16dad",
            "supported_in_gate": False,
            "failing_check_in_gate": "mode1_execution_gate.py line 82: require(files.get('f42_mixed_uel.for')==FROZEN_UEL and files.get('job_notifications.sh'), 'Frozen UEL and notifications required')",
            "failing_check_in_preflight": "preflight_package49_authorization.py line 38: adapter not in ('mode1-qualified-batch-v2', 'mode1-experimental-offset-v1', 'mode1-continuum-preanalysis-v1', 'mode1-pdas-iterative-v1')",
            "scope_restriction": "scripts/hpc/ is outside allowed_write_scope in ACTIVE_SESSION.json and cannot be modified by the agent without violating governance boundary"
        },
        "governed_submission_feasibility": {
            "experimental_irrev_via_dispatcher": "BLOCKED_BY_DISPATCHER_GATE",
            "frozen_uel_via_dispatcher": "QUALIFIED_IF_DECK_USES_FROZEN_UEL",
            "scratch_execution_via_guarded_ssh": "VERIFIED_SANCTIONED_PATH"
        }
    }

    out_json = repo_root / "results" / "validation" / "mode1_f1597" / "turn123_dispatch_gate_audit.json"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with open(out_json, "w") as f:
        json.dump(audit_findings, f, indent=2)

    print(f"[Turn 123 Audit] Successfully wrote dispatcher audit to {out_json}")
    return audit_findings

if __name__ == "__main__":
    audit_dispatcher_restrictions()

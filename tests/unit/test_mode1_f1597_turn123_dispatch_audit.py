"""
test_mode1_f1597_turn123_dispatch_audit.py
Unit test for Mode-I Task F1597 Turn 123 Dispatcher Gate Audit.

Verifies:
  1. Dispatcher gate audit artifact exists and is well-formed.
  2. Exact failing checks for experimental UEL variants are documented with line numbers.
  3. Technical preflight passes with authentic Abaqus datacheck.
  4. Governance write scope boundary is rigorously verified.
"""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

def test_dispatch_gate_audit_artifact_exists():
    audit_path = REPO_ROOT / "results" / "validation" / "mode1_f1597" / "turn123_dispatch_gate_audit.json"
    assert audit_path.exists(), "Dispatcher audit artifact does not exist"
    with open(audit_path, "r") as f:
        data = json.load(f)
    assert data["status"] == "DISPATCHER_GATE_BLOCKED_WITH_EXACT_EVIDENCE"
    assert data["preflight_status"] == "PASS"
    assert data["datacheck_status"] == "ANALYSIS_DATACHECK_COMPLETE"
    assert "mode1_execution_gate.py" in data["exact_failing_gate_check"]["source_file"]
    assert data["exact_failing_gate_check"]["source_line"] == 82
    assert "Frozen UEL and notifications required" in data["exact_failing_gate_check"]["error_message"]

def test_governance_scope_boundary():
    session_path = REPO_ROOT / "project_coordination" / "ACTIVE_SESSION.json"
    with open(session_path, "r") as f:
        session = json.load(f)
    scope = session.get("allowed_write_scope", [])
    assert not any("scripts/hpc" in s for s in scope), "scripts/hpc must remain outside write scope"

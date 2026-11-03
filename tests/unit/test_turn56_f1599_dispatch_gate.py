"""
Unit tests for Turn 56: Dispatch F1599 Independent Scientific Review.
Tests verification of review packet SHA-256, review dispatch registry inspection,
frozen production UEL preservation, and the DEFINITION_REVIEW_REQUIRED verdict.
"""

import json
from pathlib import Path
import pytest
import subprocess
import sys

WORKSPACE = Path(__file__).resolve().parents[2]
VERIFY_SCRIPT = WORKSPACE / "scripts" / "validation" / "verify_turn56_f1599_dispatch_gate.py"
AUDIT_JSON = WORKSPACE / "results" / "validation" / "f1599_dispatch_gate_audit.json"
PACKET_PATH = WORKSPACE / "results" / "validation" / "c6_package171_r1_definition_review_packet.json"
EXPECTED_PACKET_SHA = "33F58E71FDF8E2F2DFDA1CF9978D09DF329F5A9E32E2ADA1D7760E968AA39341"
FROZEN_UEL_SHA = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"


def test_verify_script_execution():
    """Verify script runs with exit code 0."""
    res = subprocess.run([sys.executable, str(VERIFY_SCRIPT)], capture_output=True, text=True)
    assert res.returncode == 0, f"Script failed: {res.stderr}\n{res.output if hasattr(res, 'output') else ''}"
    assert "Verification passed: True" in res.stdout


def test_audit_json_structure():
    """Verify that audit JSON exists and has valid structure."""
    assert AUDIT_JSON.is_file(), "Audit JSON not created"
    with open(AUDIT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data.get("schema") == 1
    assert data.get("verification_passed") is True
    assert data.get("candidate_task_id") == "F1599-PACKAGE171-R1-C6-CONVERGENCE-ACCEPTANCE"
    assert data.get("candidate_operation_id") == "evaluate_mode1_package171_r1_c6_coupled_convergence"


def test_review_packet_hash():
    """Verify review packet hash matches expected SHA-256."""
    with open(AUDIT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    rv = data["review_packet_verification"]
    assert rv["sha256_matches"] is True
    assert rv["actual_sha256"] == EXPECTED_PACKET_SHA


def test_frozen_uel_preservation():
    """Verify frozen production UEL SHA-256 is preserved."""
    with open(AUDIT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    uel = data["frozen_uel_verification"]
    assert uel["matches"] is True
    assert uel["actual_sha256"] == FROZEN_UEL_SHA


def test_review_dispatch_status():
    """Verify review dispatch directory audit reports no existing F1599 approvals."""
    with open(AUDIT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    rda = data["review_dispatch_audit"]
    assert len(rda["matching_f1599_records"]) == 0
    assert rda["authenticated_decision_exists"] is False
    assert rda["pending_request_exists"] is False


def test_closeout_verdict_and_prerequisites():
    """Verify closeout verdict is DEFINITION_REVIEW_REQUIRED with clear prerequisites."""
    with open(AUDIT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    verdict = data["closeout_verdict"]
    assert verdict["review_status"] == "DEFINITION_REVIEW_REQUIRED"
    assert verdict["new_pbs_submissions"] == 0
    assert verdict["no_fabricated_approvals"] is True
    assert len(verdict["missing_prerequisites"]) >= 3

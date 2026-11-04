#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit test suite for Candidate Package 171-R8 Independent Review Intake & Attestation
Task: F1607-PACKAGE171-R8-C6-COUPLED-REEQUILIBRATION
"""

import base64
import hashlib
import json
from pathlib import Path
import sys
import pytest

WORKSPACE = Path(__file__).resolve().parents[2]
EXPECTED_OPERATION = "execute_mode1_package171_r8_c6_coupled_reequilibration"
EXPECTED_FINGERPRINT = "8D0545A3A733B1368DBA705880C71FD8E2D797B09AF4920FDB1E76688EA52D1F"
EXPECTED_CORRELATION = "HND-F1607-R8-REVIEW-8D0545A3"
FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def test_r8_candidate_definition_integrity():
    cand_path = WORKSPACE / f"project_coordination/candidate_definitions/{EXPECTED_OPERATION}.json"
    assert cand_path.exists()
    cand = json.loads(cand_path.read_text(encoding="utf-8"))
    assert cand["operation_id"] == EXPECTED_OPERATION
    assert cand["candidate_job"] == "M1_C6_P171_R8_ADAPTIVE_DAMPED"
    assert cand["task_id"] == "F1607-PACKAGE171-R8-C6-COUPLED-REEQUILIBRATION"
    assert cand["registration_status"] == "PROPOSED_FOR_INDEPENDENT_REVIEW"
    assert cand["acceptance_criteria"]["frozen_uel_sha256"] == FROZEN_UEL_SHA256


def test_r8_request_fingerprint_matching():
    req_path = WORKSPACE / f"project_coordination/review_dispatch/{EXPECTED_OPERATION}-{EXPECTED_FINGERPRINT}.request.json"
    assert req_path.exists()
    req = json.loads(req_path.read_text(encoding="utf-8"))
    assert req["correlation_id"] == EXPECTED_CORRELATION
    assert req["fingerprint"] == EXPECTED_FINGERPRINT

    # Verify canonical packet computation
    sys.path.insert(0, str(WORKSPACE / "scripts/controller"))
    from review_dispatcher import packet
    pkt = packet(WORKSPACE, EXPECTED_OPERATION)
    assert pkt["fingerprint"] == EXPECTED_FINGERPRINT


def test_r8_dispatch_state_tracking():
    state_path = WORKSPACE / f"project_coordination/review_dispatch/{EXPECTED_OPERATION}-no-manifest.json"
    assert state_path.exists()
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["operation_id"] == EXPECTED_OPERATION
    assert state["correlation_id"] == EXPECTED_CORRELATION
    assert state["fingerprint"] == EXPECTED_FINGERPRINT
    assert state["status"] in ("REVIEW_PENDING", "REVIEWED", "BLOCKED", "REJECTED")


def test_audit_r8_independent_review_intake_execution():
    sys.path.insert(0, str(WORKSPACE / "scripts/validation"))
    from audit_r8_independent_review_intake import audit_r8_review_intake
    success = audit_r8_review_intake()
    assert success is True

    audit_out_path = WORKSPACE / "results/validation/r8_independent_review_intake_audit.json"
    assert audit_out_path.exists()
    audit = json.loads(audit_out_path.read_text(encoding="utf-8"))
    assert audit["schema"] == 1
    assert audit["task_id"] == "F1607-PACKAGE171-R8-C6-COUPLED-REEQUILIBRATION"
    assert audit["correlation_id"] == EXPECTED_CORRELATION
    assert audit["fingerprint"] == EXPECTED_FINGERPRINT
    assert audit["verification_passed"] is True
    assert "evidence_sources" in audit
    assert len(audit["evidence_sources"]) >= 3

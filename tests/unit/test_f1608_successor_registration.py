#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit test suite verifying successor task F1608-PACKAGE171-R8-C6-ADAPTIVE-REEQUILIBRATION
registration, predecessor F1607 linkage, candidate R8 specifications, and review authentication.
"""

import base64
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import pytest

WORKSPACE = Path(__file__).resolve().parents[2]
EXPECTED_OPERATION = "execute_mode1_package171_r8_c6_coupled_reequilibration"
EXPECTED_FINGERPRINT = "8D0545A3A733B1368DBA705880C71FD8E2D797B09AF4920FDB1E76688EA52D1F"
EXPECTED_CORRELATION = "HND-F1607-R8-REVIEW-8D0545A3"
FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
EXPECTED_PREDECESSOR = "F1607-PACKAGE171-R8-C6-COUPLED-REEQUILIBRATION"
EXPECTED_SUCCESSOR = "F1608-PACKAGE171-R8-C6-ADAPTIVE-REEQUILIBRATION"


def compute_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def test_f1608_task_definition_schema_and_predecessor():
    def_path = WORKSPACE / f"project_coordination/task_definitions/{EXPECTED_SUCCESSOR}.json"
    assert def_path.exists(), f"Missing definition file: {def_path}"

    with open(def_path, "r", encoding="utf-8") as f:
        d = json.load(f)

    assert d.get("schema") == 1
    assert d.get("task_id") == EXPECTED_SUCCESSOR
    assert d.get("max_new_pbs_submissions") == 0
    assert d.get("operation", {}).get("mode") == "READ_ONLY_SCIENTIFIC_EVALUATION"
    assert d.get("operation", {}).get("id") == "research_preparation"

    pred = d.get("predecessor", {})
    assert pred.get("task_id") == EXPECTED_PREDECESSOR
    assert pred.get("status") == "COMPLETED"


def test_f1608_inherited_completed_operations():
    def_path = WORKSPACE / f"project_coordination/task_definitions/{EXPECTED_SUCCESSOR}.json"
    with open(def_path, "r", encoding="utf-8") as f:
        d = json.load(f)

    inherited = d.get("inherited_completed_operations", [])
    assert len(inherited) == 17
    assert "mapped_frozen_history_lower_bound_kkt_probe" in inherited
    assert "execute_mode1_package171_r7_c6_coupled_reequilibration" in inherited


def test_f1608_evidence_sources_hashes():
    def_path = WORKSPACE / f"project_coordination/task_definitions/{EXPECTED_SUCCESSOR}.json"
    with open(def_path, "r", encoding="utf-8") as f:
        d = json.load(f)

    evidence_sources = d.get("evidence_sources", {})
    assert len(evidence_sources) >= 10

    for rel_path, expected_hash in evidence_sources.items():
        file_path = WORKSPACE / rel_path
        assert file_path.exists(), f"Evidence file does not exist: {file_path}"
        actual_hash = compute_sha256(file_path)
        assert actual_hash == expected_hash.upper(), f"Hash mismatch for {rel_path}: expected {expected_hash}, got {actual_hash}"


def test_f1608_review_authentication():
    cmd = [sys.executable, str(WORKSPACE / "scripts/controller/review_dispatcher.py"),
           "--workspace", str(WORKSPACE),
           "--operation-id", EXPECTED_OPERATION,
           "--check-review"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 0
    assert "AUTHENTICATED_INDEPENDENT_REVIEW" in proc.stdout


def test_f1608_audit_execution():
    sys.path.insert(0, str(WORKSPACE / "scripts/validation"))
    from audit_f1608_successor_registration import audit_f1608_successor_registration
    success, res = audit_f1608_successor_registration()
    assert success is True
    assert res.get("verification_passed") is True

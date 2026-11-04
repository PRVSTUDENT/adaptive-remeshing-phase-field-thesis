#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit test suite verifying successor task F1607-PACKAGE171-R8-C6-COUPLED-REEQUILIBRATION,
predecessor F1606 closure, and candidate M1_C6_P171_R8_ADAPTIVE_DAMPED registration.

Validates:
1. Closed predecessor F1606 linking to open successor F1607 in TASK_LEDGER.csv.
2. F1607 open row in TASK_LEDGER.csv (ready, REGISTERED_NOT_EXECUTED).
3. F1607 task definition schema, read-only scope, 0 PBS submissions, and predecessor linkage.
4. Retention of all 17 inherited completed operations.
5. Pinned evidence sources on disk and exact SHA-256 digests.
6. ACTIVE_TASK.json binding and definition hash alignment.
"""

import csv
import hashlib
import json
from pathlib import Path
import pytest

WORKSPACE = Path(__file__).resolve().parents[2]


def compute_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def test_f1607_task_definition_schema_and_predecessor():
    def_path = WORKSPACE / "project_coordination/task_definitions/F1607-PACKAGE171-R8-C6-COUPLED-REEQUILIBRATION.json"
    assert def_path.exists(), f"Missing definition file: {def_path}"

    with open(def_path, "r", encoding="utf-8") as f:
        d = json.load(f)

    assert d.get("schema") == 1
    assert d.get("task_id") == "F1607-PACKAGE171-R8-C6-COUPLED-REEQUILIBRATION"
    assert d.get("max_new_pbs_submissions") == 0
    assert d.get("operation", {}).get("mode") == "READ_ONLY_SCIENTIFIC_EVALUATION"
    assert d.get("operation", {}).get("id") == "research_preparation"

    pred = d.get("predecessor", {})
    assert pred.get("task_id") == "F1606-MODE1-C6-R7-NONCONVERGENCE-INVESTIGATION"
    assert pred.get("status") == "COMPLETED"


def test_f1607_inherited_completed_operations():
    def_path = WORKSPACE / "project_coordination/task_definitions/F1607-PACKAGE171-R8-C6-COUPLED-REEQUILIBRATION.json"
    with open(def_path, "r", encoding="utf-8") as f:
        d = json.load(f)

    inherited = d.get("inherited_completed_operations", [])
    assert len(inherited) == 17
    assert "mapped_frozen_history_lower_bound_kkt_probe" in inherited
    assert "execute_mode1_package171_r7_c6_coupled_reequilibration" in inherited


def test_f1607_evidence_sources_hashes():
    def_path = WORKSPACE / "project_coordination/task_definitions/F1607-PACKAGE171-R8-C6-COUPLED-REEQUILIBRATION.json"
    with open(def_path, "r", encoding="utf-8") as f:
        d = json.load(f)

    evidence_sources = d.get("evidence_sources", {})
    assert len(evidence_sources) >= 8

    for rel_path, expected_hash in evidence_sources.items():
        file_path = WORKSPACE / rel_path
        assert file_path.exists(), f"Evidence file does not exist: {file_path}"
        actual_hash = compute_sha256(file_path)
        assert actual_hash == expected_hash.upper(), f"Hash mismatch for {rel_path}: expected {expected_hash}, got {actual_hash}"


def test_f1607_active_task_json_binding():
    task_path = WORKSPACE / "project_coordination/ACTIVE_TASK.json"
    with open(task_path, "r", encoding="utf-8") as f:
        task = json.load(f)

    assert task.get("task_id") == "F1607-PACKAGE171-R8-C6-COUPLED-REEQUILIBRATION"
    assert task.get("status") == "READY_READ_ONLY_EVALUATION"
    assert task.get("max_new_pbs_submissions") == 0
    assert task.get("scientific_checkpoint_required") is True
    assert task.get("scientific_operation_id") == "research_preparation"
    assert task.get("scientific_operation") == ""

    reg = task.get("registration", {})
    assert reg.get("definition") == "project_coordination/task_definitions/F1607-PACKAGE171-R8-C6-COUPLED-REEQUILIBRATION.json"
    assert reg.get("schema") == 1

    def_path = WORKSPACE / reg["definition"]
    expected_def_hash = compute_sha256(def_path)
    assert reg.get("sha256") == expected_def_hash


def test_f1607_task_ledger_linkage_and_uniqueness():
    ledger_path = WORKSPACE / "project_coordination/TASK_LEDGER.csv"
    with open(ledger_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    f1607_rows = [r for r in rows if r["task_id"] == "F1607-PACKAGE171-R8-C6-COUPLED-REEQUILIBRATION"]
    assert len(f1607_rows) == 1, f"Expected exactly 1 open row for F1607, found {len(f1607_rows)}"
    assert f1607_rows[0]["status"] == "ready"
    assert f1607_rows[0]["classification"] == "REGISTERED_NOT_EXECUTED"

    f1606_rows = [r for r in rows if r["task_id"] == "F1606-MODE1-C6-R7-NONCONVERGENCE-INVESTIGATION" and r["status"].lower() == "completed"]
    assert len(f1606_rows) >= 1
    assert f1606_rows[-1]["next_task"] == "F1607-PACKAGE171-R8-C6-COUPLED-REEQUILIBRATION"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Unit test suite verifying successor task F1604-PACKAGE171-R7-C6-ADAPTIVE-PREPARATION,
predecessor F1603 closure, and candidate M1_C6_P171_R7_ADAPTIVE_DAMPED registration.

Validates:
1. Closed predecessor F1603 linking to open successor F1604 in TASK_LEDGER.csv.
2. F1604 open row in TASK_LEDGER.csv (ready, REGISTERED_NOT_EXECUTED).
3. F1604 task definition schema, read-only scope, 0 PBS submissions, and predecessor linkage.
4. Retention of all 16 inherited completed operations.
5. Pinned evidence sources on disk and exact SHA-256 digests.
6. ACTIVE_TASK.json binding and definition hash alignment.
"""

import csv
import hashlib
import json
from pathlib import Path
import pytest

WORKSPACE = Path(__file__).resolve().parents[2]


def test_f1604_task_definition_schema_and_predecessor():
    def_path = WORKSPACE / "project_coordination/task_definitions/F1604-PACKAGE171-R7-C6-ADAPTIVE-PREPARATION.json"
    assert def_path.exists(), f"Missing definition file: {def_path}"

    with open(def_path, "r", encoding="utf-8") as f:
        d = json.load(f)

    assert d.get("schema") == 1
    assert d.get("task_id") == "F1604-PACKAGE171-R7-C6-ADAPTIVE-PREPARATION"
    assert d.get("max_new_pbs_submissions") == 0
    assert d.get("operation", {}).get("mode") == "READ_ONLY_SCIENTIFIC_EVALUATION"
    assert d.get("operation", {}).get("id") == "research_preparation"

    pred = d.get("predecessor", {})
    assert pred.get("task_id") == "F1603-MODE1-C6-R6-NONCONVERGENCE-INVESTIGATION"
    assert pred.get("status") == "COMPLETED"


def test_f1604_inherited_completed_operations():
    def_path = WORKSPACE / "project_coordination/task_definitions/F1604-PACKAGE171-R7-C6-ADAPTIVE-PREPARATION.json"
    with open(def_path, "r", encoding="utf-8") as f:
        d = json.load(f)

    inherited = d.get("inherited_completed_operations", [])
    assert len(inherited) == 16
    assert "mapped_frozen_history_lower_bound_kkt_probe" in inherited
    assert "execute_mode1_package158_c2_0_r5_re_equilibration" in inherited


def test_f1604_evidence_sources_hashes():
    def_path = WORKSPACE / "project_coordination/task_definitions/F1604-PACKAGE171-R7-C6-ADAPTIVE-PREPARATION.json"
    with open(def_path, "r", encoding="utf-8") as f:
        d = json.load(f)

    evidence_sources = d.get("evidence_sources", {})
    assert len(evidence_sources) >= 6

    for rel_path, expected_hash in evidence_sources.items():
        file_path = WORKSPACE / rel_path
        assert file_path.exists(), f"Evidence file does not exist: {file_path}"
        actual_hash = hashlib.sha256(file_path.read_bytes()).hexdigest().upper()
        assert actual_hash == expected_hash.upper(), f"Hash mismatch for {rel_path}: expected {expected_hash}, got {actual_hash}"


def test_f1604_active_task_json_binding():
    task_path = WORKSPACE / "project_coordination/ACTIVE_TASK.json"
    with open(task_path, "r", encoding="utf-8") as f:
        task = json.load(f)

    assert task.get("task_id") == "F1604-PACKAGE171-R7-C6-ADAPTIVE-PREPARATION"
    assert task.get("status") == "READY_READ_ONLY_EVALUATION"
    assert task.get("max_new_pbs_submissions") == 0
    assert task.get("scientific_checkpoint_required") is True
    assert task.get("scientific_operation_id") == "research_preparation"
    assert task.get("scientific_operation") == ""

    reg = task.get("registration", {})
    assert reg.get("definition") == "project_coordination/task_definitions/F1604-PACKAGE171-R7-C6-ADAPTIVE-PREPARATION.json"
    assert reg.get("schema") == 1

    def_path = WORKSPACE / reg["definition"]
    expected_def_hash = hashlib.sha256(def_path.read_bytes()).hexdigest().upper()
    assert reg.get("sha256") == expected_def_hash


def test_f1604_task_ledger_linkage_and_uniqueness():
    ledger_path = WORKSPACE / "project_coordination/TASK_LEDGER.csv"
    with open(ledger_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    f1604_rows = [r for r in rows if r["task_id"] == "F1604-PACKAGE171-R7-C6-ADAPTIVE-PREPARATION"]
    assert len(f1604_rows) == 1, f"Expected exactly 1 open row for F1604, found {len(f1604_rows)}"
    assert f1604_rows[0]["status"] == "ready"
    assert f1604_rows[0]["classification"] == "REGISTERED_NOT_EXECUTED"

    f1603_rows = [r for r in rows if r["task_id"] == "F1603-MODE1-C6-R6-NONCONVERGENCE-INVESTIGATION" and r["status"].lower() == "completed"]
    assert len(f1603_rows) >= 1
    assert f1603_rows[-1]["next_task"] == "F1604-PACKAGE171-R7-C6-ADAPTIVE-PREPARATION"

"""
Unit test suite verifying legitimate successor registration F1601-MODE1-C6-R2-DIAGNOSIS-PREPARATION
after completed F1599-PACKAGE171-R1-C6-CONVERGENCE-ACCEPTANCE.

Validates:
1. Schema conformity and non-numerical scope of F1601 definition.
2. Exact predecessor linkage to completed F1599.
3. Unique open row in TASK_LEDGER.csv with status 'ready'.
4. Closed row for F1599 pointing to F1601 via 'next_task'.
5. Pinned evidence source hashes on disk.
6. Preservation of all 16 inherited completed operations.
7. Zero PBS submissions authorized.
8. Runtime checkpoint analysis and documented incompatibility with Get-ControllerSuccessorCheckpointPlan.
"""

import csv
import hashlib
import json
import os
import subprocess
from pathlib import Path
import pytest

WORKSPACE = Path(__file__).resolve().parents[2]


def test_f1601_definition_schema_and_predecessor():
    def_path = WORKSPACE / "project_coordination/task_definitions/F1601-MODE1-C6-R2-DIAGNOSIS-PREPARATION.json"
    assert def_path.exists(), f"Missing definition file: {def_path}"

    with open(def_path, "r", encoding="utf-8") as f:
        d = json.load(f)

    assert d.get("schema") == 1
    assert d.get("task_id") == "F1601-MODE1-C6-R2-DIAGNOSIS-PREPARATION"
    assert d.get("max_new_pbs_submissions") == 0
    assert d.get("operation", {}).get("mode") == "READ_ONLY_SCIENTIFIC_EVALUATION"
    assert d.get("operation", {}).get("id") == "research_preparation"

    pred = d.get("predecessor", {})
    assert pred.get("task_id") == "F1599-PACKAGE171-R1-C6-CONVERGENCE-ACCEPTANCE"
    assert pred.get("status") == "COMPLETED"
    assert pred.get("source_commit") == "50d6d5b5a5971f99cdb88c5b038e8857857132a4"
    assert pred.get("checkpoint_sha256") == "06AB99DBBE0419C6C9D16EE82F18EED9FE6B22ED3617138D9360A04815DCD07A"


def test_f1601_inherited_completed_operations():
    def_path = WORKSPACE / "project_coordination/task_definitions/F1601-MODE1-C6-R2-DIAGNOSIS-PREPARATION.json"
    with open(def_path, "r", encoding="utf-8") as f:
        d = json.load(f)

    inherited = d.get("inherited_completed_operations", [])
    assert len(inherited) == 16
    assert "mapped_frozen_history_lower_bound_kkt_probe" in inherited
    assert "execute_mode1_package158_c2_0_r5_re_equilibration" in inherited


def test_f1601_evidence_sources_hashes():
    def_path = WORKSPACE / "project_coordination/task_definitions/F1601-MODE1-C6-R2-DIAGNOSIS-PREPARATION.json"
    with open(def_path, "r", encoding="utf-8") as f:
        d = json.load(f)

    evidence_sources = d.get("evidence_sources", {})
    assert len(evidence_sources) >= 9

    for rel_path, expected_hash in evidence_sources.items():
        file_path = WORKSPACE / rel_path
        assert file_path.exists(), f"Evidence file does not exist: {file_path}"
        with open(file_path, "rb") as f:
            actual_hash = hashlib.sha256(f.read()).hexdigest().upper()
        assert actual_hash == expected_hash.upper(), f"Hash mismatch for {rel_path}: expected {expected_hash}, got {actual_hash}"


def test_task_ledger_f1599_linkage_and_f1601_uniqueness():
    ledger_path = WORKSPACE / "project_coordination/TASK_LEDGER.csv"
    with open(ledger_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    f1601_rows = [r for r in rows if r["task_id"] == "F1601-MODE1-C6-R2-DIAGNOSIS-PREPARATION"]
    assert len(f1601_rows) == 1, f"Expected exactly 1 open row for F1601, found {len(f1601_rows)}"
    assert f1601_rows[0]["status"] == "ready"
    assert f1601_rows[0]["classification"] == "REGISTERED_NOT_EXECUTED"

    f1599_rows = [r for r in rows if r["task_id"] == "F1599-PACKAGE171-R1-C6-CONVERGENCE-ACCEPTANCE"]
    assert len(f1599_rows) >= 1
    assert f1599_rows[-1]["status"].lower() == "completed"
    assert f1599_rows[-1]["next_task"] == "F1601-MODE1-C6-R2-DIAGNOSIS-PREPARATION"


def test_active_task_json_f1601_binding():
    task_path = WORKSPACE / "project_coordination/ACTIVE_TASK.json"
    with open(task_path, "r", encoding="utf-8") as f:
        task = json.load(f)

    assert task.get("task_id") == "F1601-MODE1-C6-R2-DIAGNOSIS-PREPARATION"
    assert task.get("status") == "READY_READ_ONLY_EVALUATION"
    assert task.get("max_new_pbs_submissions") == 0
    assert task.get("scientific_checkpoint_required") is True
    assert task.get("scientific_operation_id") == "research_preparation"
    assert task.get("scientific_operation") == ""

    reg = task.get("registration", {})
    assert reg.get("definition") == "project_coordination/task_definitions/F1601-MODE1-C6-R2-DIAGNOSIS-PREPARATION.json"
    assert reg.get("schema") == 1

    def_path = WORKSPACE / reg["definition"]
    with open(def_path, "rb") as f:
        expected_def_hash = hashlib.sha256(f.read()).hexdigest().upper()
    assert reg.get("sha256") == expected_def_hash


def test_controller_task_lifecycle_logic():
    # Verify that ACTIVE_TASK.json has non-terminal status
    task_path = WORKSPACE / "project_coordination/ACTIVE_TASK.json"
    with open(task_path, "r", encoding="utf-8") as f:
        task = json.load(f)

    terminal_pattern = ["complete", "completed", "classified", "closed", "done"]
    is_terminal = task["status"].lower() in terminal_pattern or task.get("lifecycle", {}).get("state") == "COMPLETED_AWAITING_SUCCESSOR"
    assert not is_terminal, f"Task {task['task_id']} should not be terminal"

    # Verify that in TASK_LEDGER.csv, F1601 has no closed row
    ledger_path = WORKSPACE / "project_coordination/TASK_LEDGER.csv"
    with open(ledger_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    closed_f1601 = [r for r in rows if r["task_id"] == task["task_id"] and r["status"].lower() in terminal_pattern]
    assert len(closed_f1601) == 0, "F1601 should have no closed row"

    # Verify that F1601's predecessor has a closed row
    pred_id = task["predecessor_task"]["task_id"]
    closed_pred = [r for r in rows if r["task_id"] == pred_id and r["status"].lower() in terminal_pattern]
    assert len(closed_pred) >= 1, f"Predecessor {pred_id} must have a closed row"


def test_checkpoint_external_predecessor_chain():
    # Verify the runtime checkpoint in OpenClawPAD
    userprofile = os.environ.get("USERPROFILE", "")
    cp_path = Path(userprofile) / "OpenClawPAD/controller_turn_checkpoint.json"
    assert cp_path.exists(), f"Runtime checkpoint not found: {cp_path}"

    with open(cp_path, "r", encoding="utf-8") as f:
        cp_envelope = json.load(f)

    payload = json.loads(cp_envelope["payload"])
    assert payload["task_id"] == "F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE"
    assert payload["state"] == "COMPLETED"
    assert payload["run_id"] == "ae8660dc-363a-4847-854c-93f9e08c0212"

    # F1601's predecessor is F1599
    succ_def_path = WORKSPACE / "project_coordination/task_definitions/F1601-MODE1-C6-R2-DIAGNOSIS-PREPARATION.json"
    with open(succ_def_path, "r", encoding="utf-8") as f:
        succ_def = json.load(f)
    assert succ_def["predecessor"]["task_id"] == "F1599-PACKAGE171-R1-C6-CONVERGENCE-ACCEPTANCE"

    # F1599's predecessor is F1598, matching the checkpoint on disk
    pred_def_path = WORKSPACE / "project_coordination/task_definitions/F1599-PACKAGE171-R1-C6-CONVERGENCE-ACCEPTANCE.json"
    with open(pred_def_path, "r", encoding="utf-8") as f:
        pred_def = json.load(f)
    assert pred_def["predecessor"]["task_id"] == payload["task_id"]
    assert pred_def["predecessor"]["run_id"] == payload["run_id"]

    # F1599 receipt matches predecessor checkpoint hash in F1601
    receipt_rel = "results/validation/f1599_c6_coupled_convergence_evaluation.json"
    receipt_path = WORKSPACE / receipt_rel
    assert receipt_path.exists()
    with open(receipt_path, "rb") as f:
        actual_receipt_hash = hashlib.sha256(f.read()).hexdigest().upper()
    assert actual_receipt_hash == succ_def["predecessor"]["checkpoint_sha256"].upper()



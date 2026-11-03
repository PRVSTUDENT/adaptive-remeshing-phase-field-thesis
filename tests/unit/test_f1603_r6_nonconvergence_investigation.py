"""
Unit test suite verifying successor task F1603-MODE1-C6-R6-NONCONVERGENCE-INVESTIGATION
and the quantitative active-set contraction analysis for Package 171-R6.

Validates:
1. Integrity and quantitative metrics of results/validation/r6_active_set_contraction_analysis.json.
2. Schema, read-only scope, and predecessor linkage of F1603 task definition.
3. Pinned evidence sources on disk and exact SHA-256 digests.
4. Retention of all 16 inherited completed operations.
5. Strict zero PBS submission authorization.
6. ACTIVE_TASK.json binding and task definition hash alignment.
7. TASK_LEDGER.csv closed predecessor F1601 pointing to open successor F1603.
"""

import csv
import hashlib
import json
from pathlib import Path
import pytest

WORKSPACE = Path(__file__).resolve().parents[2]


def test_r6_active_set_contraction_analysis_artifact():
    artifact_path = WORKSPACE / "results/validation/r6_active_set_contraction_analysis.json"
    assert artifact_path.exists(), f"Missing analysis artifact: {artifact_path}"

    with open(artifact_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data.get("schema") == 1
    assert data.get("pbs_job_id") == "1419807.mmaster02"
    assert data.get("total_outer_iterations") == 100
    assert data.get("verification_passed") is True

    metrics = data.get("active_set_metrics", {})
    assert metrics.get("initial_pdas_active_count") == 13803
    assert metrics.get("final_pdas_active_count") == 160
    assert metrics.get("pdas_active_reduction_pct") > 98.0
    assert metrics.get("is_active_set_substantially_contracted") is True

    term = data.get("terminal_metrics", {})
    assert abs(term.get("last_delta_d") - 0.0083084) < 1e-5
    assert abs(term.get("last_delta_u_mm") - 5.6421e-5) < 1e-7
    assert abs(term.get("last_delta_h_MPa") - 378.74) < 0.1
    assert term.get("last_kkt_free_error") <= 1.0e-6
    assert term.get("last_kkt_dual_error") <= 1.0e-6

    diag = data.get("scientific_diagnosis", {})
    assert diag.get("classification") == "LOCALIZED_NONLINEAR_REDISTRIBUTION_PLATEAU"


def test_f1603_task_definition_schema_and_predecessor():
    def_path = WORKSPACE / "project_coordination/task_definitions/F1603-MODE1-C6-R6-NONCONVERGENCE-INVESTIGATION.json"
    assert def_path.exists(), f"Missing definition file: {def_path}"

    with open(def_path, "r", encoding="utf-8") as f:
        d = json.load(f)

    assert d.get("schema") == 1
    assert d.get("task_id") == "F1603-MODE1-C6-R6-NONCONVERGENCE-INVESTIGATION"
    assert d.get("max_new_pbs_submissions") == 0
    assert d.get("operation", {}).get("mode") == "READ_ONLY_SCIENTIFIC_EVALUATION"
    assert d.get("operation", {}).get("id") == "research_preparation"

    pred = d.get("predecessor", {})
    assert pred.get("task_id") == "F1601-MODE1-C6-R2-DIAGNOSIS-PREPARATION"
    assert pred.get("status") == "COMPLETED"


def test_f1603_inherited_completed_operations():
    def_path = WORKSPACE / "project_coordination/task_definitions/F1603-MODE1-C6-R6-NONCONVERGENCE-INVESTIGATION.json"
    with open(def_path, "r", encoding="utf-8") as f:
        d = json.load(f)

    inherited = d.get("inherited_completed_operations", [])
    assert len(inherited) == 16
    assert "mapped_frozen_history_lower_bound_kkt_probe" in inherited
    assert "execute_mode1_package158_c2_0_r5_re_equilibration" in inherited


def test_f1603_evidence_sources_hashes():
    def_path = WORKSPACE / "project_coordination/task_definitions/F1603-MODE1-C6-R6-NONCONVERGENCE-INVESTIGATION.json"
    with open(def_path, "r", encoding="utf-8") as f:
        d = json.load(f)

    evidence_sources = d.get("evidence_sources", {})
    assert len(evidence_sources) >= 6

    for rel_path, expected_hash in evidence_sources.items():
        file_path = WORKSPACE / rel_path
        assert file_path.exists(), f"Evidence file does not exist: {file_path}"
        with open(file_path, "rb") as f:
            actual_hash = hashlib.sha256(f.read()).hexdigest().upper()
        assert actual_hash == expected_hash.upper(), f"Hash mismatch for {rel_path}: expected {expected_hash}, got {actual_hash}"


def test_f1603_active_task_json_binding():
    task_path = WORKSPACE / "project_coordination/ACTIVE_TASK.json"
    with open(task_path, "r", encoding="utf-8") as f:
        task = json.load(f)

    # Validates either active F1603 or successor F1604 preserving F1603 predecessor
    if task.get("task_id") == "F1603-MODE1-C6-R6-NONCONVERGENCE-INVESTIGATION":
        assert task.get("status") == "READY_READ_ONLY_EVALUATION"
        assert task.get("max_new_pbs_submissions") == 0
        assert task.get("scientific_checkpoint_required") is True
        assert task.get("scientific_operation_id") == "research_preparation"
        assert task.get("scientific_operation") == ""

        reg = task.get("registration", {})
        assert reg.get("definition") == "project_coordination/task_definitions/F1603-MODE1-C6-R6-NONCONVERGENCE-INVESTIGATION.json"
        assert reg.get("schema") == 1

        def_path = WORKSPACE / reg["definition"]
        with open(def_path, "rb") as f:
            expected_def_hash = hashlib.sha256(f.read()).hexdigest().upper()
        assert reg.get("sha256") == expected_def_hash
    else:
        assert task.get("task_id") == "F1604-PACKAGE171-R7-C6-ADAPTIVE-PREPARATION"
        assert task.get("predecessor_task", {}).get("task_id") == "F1603-MODE1-C6-R6-NONCONVERGENCE-INVESTIGATION"
        assert task.get("preserved_predecessor", {}).get("task_id") == "F1603-MODE1-C6-R6-NONCONVERGENCE-INVESTIGATION"


def test_f1603_task_ledger_linkage_and_uniqueness():
    ledger_path = WORKSPACE / "project_coordination/TASK_LEDGER.csv"
    with open(ledger_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    f1603_rows = [r for r in rows if r["task_id"] == "F1603-MODE1-C6-R6-NONCONVERGENCE-INVESTIGATION"]
    assert len(f1603_rows) == 1, f"Expected exactly 1 parent row for F1603, found {len(f1603_rows)}"
    assert f1603_rows[0]["status"] in ("ready", "completed")

    f1601_rows = [r for r in rows if r["task_id"] == "F1601-MODE1-C6-R2-DIAGNOSIS-PREPARATION" and r["status"].lower() == "completed"]
    assert len(f1601_rows) >= 1
    assert f1601_rows[-1]["next_task"] == "F1603-MODE1-C6-R6-NONCONVERGENCE-INVESTIGATION"

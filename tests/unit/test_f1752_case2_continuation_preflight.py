"""
Unit test suite for Task F1752: Case 2 Method A Controlled-Only Continuation Execution Preflight.
Verifies input deck integrity, frozen UEL hash, 1-line diff isolation, datacheck exit 0 receipt,
predeclared stop conditions, physical acceptance gates, and zero-PBS governance.
"""

import json
import hashlib
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
F1752_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "234_f1752_case2_continuation"
PARENT_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "224_f1734_case2_distal_refinement"
MANIFEST_PATH = REPO_ROOT / "results" / "validation" / "f1752_case2_continuation_manifest.json"
REPORT_PATH = REPO_ROOT / "docs" / "validation" / "F1752_CASE2_CONTINUATION_PREFLIGHT_REPORT.md"

EXPECTED_UEL_HASH = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"
EXPECTED_DECK_HASH = "ccb35b34bfae015ea4846d3d0765fc2646e6c9af47958f8c21a0a4f25a14cc4a"
PARENT_DECK_HASH = "805af9d80126588c1a3e39fe3b5f7a0f53db606106f2dbfe6260f1e1fbddbf94"


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()


def test_frozen_uel_sha256():
    """Verify bitwise frozen UEL f42_mixed_uel.for matches the canonical hash."""
    uel_path = F1752_DIR / "f42_mixed_uel.for"
    assert uel_path.is_file(), f"Missing UEL file: {uel_path}"
    actual_hash = compute_sha256(uel_path)
    assert actual_hash == EXPECTED_UEL_HASH, f"UEL hash mismatch: {actual_hash} != {EXPECTED_UEL_HASH}"


def test_continuation_deck_sha256():
    """Verify PK_F1752_CASE_2_CONTINUATION.inp matches expected hash."""
    deck_path = F1752_DIR / "PK_F1752_CASE_2_CONTINUATION.inp"
    assert deck_path.is_file(), f"Missing continuation deck: {deck_path}"
    actual_hash = compute_sha256(deck_path)
    assert actual_hash == EXPECTED_DECK_HASH, f"Deck hash mismatch: {actual_hash} != {EXPECTED_DECK_HASH}"


def test_exact_one_line_diff():
    """Verify continuation deck differs from parent deck by exactly 1 line (min_increment)."""
    parent_path = PARENT_DIR / "PK_F1728_CASE_2_PROD.inp"
    cont_path = F1752_DIR / "PK_F1752_CASE_2_CONTINUATION.inp"
    assert parent_path.is_file(), f"Missing parent deck: {parent_path}"
    assert cont_path.is_file(), f"Missing continuation deck: {cont_path}"

    with open(parent_path, "r", encoding="utf-8") as f:
        parent_lines = f.readlines()
    with open(cont_path, "r", encoding="utf-8") as f:
        cont_lines = f.readlines()

    assert len(parent_lines) == len(cont_lines), f"Line count mismatch: {len(parent_lines)} != {len(cont_lines)}"

    diff_indices = [i for i, (p, c) in enumerate(zip(parent_lines, cont_lines)) if p != c]
    assert len(diff_indices) == 1, f"Expected exactly 1 differing line, found {len(diff_indices)}: {diff_indices}"

    diff_idx = diff_indices[0]
    assert diff_idx == 96208, f"Expected difference at line 96209 (index 96208), found index {diff_idx}"
    assert "1.0e-8" in parent_lines[diff_idx], f"Parent line missing 1.0e-8: {parent_lines[diff_idx]}"
    assert "1.0e-11" in cont_lines[diff_idx], f"Continuation line missing 1.0e-11: {cont_lines[diff_idx]}"


def test_manifest_structure_and_datacheck():
    """Verify f1752_case2_continuation_manifest.json contains required keys and Exit 0 datacheck."""
    assert MANIFEST_PATH.is_file(), f"Missing manifest: {MANIFEST_PATH}"
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["task_id"] == "F1752-CASE2-CONTROL-ONLY-CONTINUATION-EXECUTION-PREFLIGHT"
    assert data["continuation_architecture"] == "FULL_RERUN_ON_UNCHANGED_23965_ELEMENT_MESH"
    assert data["restart_audit"]["status"] == "DISQUALIFIED"
    assert "COMMON" in data["restart_audit"]["technical_reason"]

    # Datacheck verification
    dc = data["datacheck_receipt"]
    assert dc["exit_code"] == 0, f"Datacheck exit code is not 0: {dc['exit_code']}"
    assert dc["errors"] == 0, f"Datacheck errors is not 0: {dc['errors']}"
    assert dc["warnings"] == 8, f"Unexpected warning count: {dc['warnings']}"

    # Resource verification
    res = data["resource_request"]
    assert res["queue"] == "normal_imfdfkmq"
    assert res["ncpus"] == 1
    assert res["memory_gb"] == 8
    assert res["walltime_sec"] == 10800

    # Stop conditions
    stop = data["predeclared_stop_conditions"]
    assert "50" in stop["condition_1_cutbacks"]
    assert "1.0e-7" in stop["condition_2_rate_stagnation"]
    assert "10,800" in stop["condition_3_walltime"]

    # Acceptance gates
    gates = data["predeclared_physical_acceptance_gates"]
    assert "gate_1_energy_monotonicity" in gates
    assert "gate_2_damage_bounds" in gates
    assert "gate_3_secondary_propagation" in gates
    assert "gate_4_load_drop" in gates
    assert "gate_5_resolution_classification" in gates

    # Governance
    gov = data["governance"]
    assert gov["pbs_jobs_consumed_under_f1752"] == 0
    assert gov["cumulative_historical_pbs_submissions"] == 25
    assert gov["pbs_submissions_requested_for_continuation"] == 1


def test_preflight_report_sections():
    """Verify F1752_CASE2_CONTINUATION_PREFLIGHT_REPORT.md exists and covers all core findings."""
    assert REPORT_PATH.is_file(), f"Missing report: {REPORT_PATH}"
    content = REPORT_PATH.read_text(encoding="utf-8")

    assert "COMMON" in content
    assert "SV_H_COMMITTED" in content
    assert "96209" in content
    assert "1.0e-11" in content
    assert "Exit Code 0" in content
    assert "10,800" in content
    assert "Stop Condition 1" in content
    assert "Gate 1" in content
    assert "HND-F1751-CASE2-READINESS-001" in content

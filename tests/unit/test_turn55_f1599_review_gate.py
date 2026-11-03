"""
Unit test for Turn 55: F1599 Independent Scientific Review and Registration Gate.
Verifies the recovery prerequisite, Package 171-R1 terminal failure evidence,
review packet integrity, and the strict separation between review and registration.
"""

import hashlib
import json
from pathlib import Path
import pytest

WORKSPACE = Path(__file__).resolve().parents[2]
PACKET_PATH = WORKSPACE / "results" / "validation" / "c6_package171_r1_definition_review_packet.json"
FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()


def test_turn54_recovery_prerequisite_explicit():
    """Verify Turn 54 controller recovery and self-repair status."""
    recovery_ps1 = WORKSPACE / "scripts" / "controller" / "Controller-Recovery.ps1"
    assert recovery_ps1.is_file(), "Controller-Recovery.ps1 must exist"

    # Check that basis_sources matching exists in Controller-Recovery.ps1
    content = recovery_ps1.read_text(encoding="utf-8")
    assert "basis_sources" in content, "Controller-Recovery.ps1 must contain basis_sources matching fix"
    assert "Test-ControllerResponseFinished" in content, "Test-ControllerResponseFinished must be defined"


def test_package171_r1_terminal_failure_evidence():
    """Verify authentic failure numbers for Package 171-R1 (Job 1419643.mmaster02)."""
    assert PACKET_PATH.is_file(), "Review packet must exist"
    with open(PACKET_PATH, "r", encoding="utf-8") as f:
        packet = json.load(f)

    sched = packet["scheduler_reconciliation"]
    assert sched["pbs_job_id"] == "1419643.mmaster02"
    assert sched["pbs_state"] == "F"
    assert sched["exit_status"] == 1
    assert sched["time_use"] == "00:39:48"

    # Terminal log finding values
    assert "Outer 100" in sched["terminal_log_finding"]
    assert "delta_d = 7.1663e-3" in sched["terminal_log_finding"]
    assert "dual_error = 9.7824e-10" in sched["terminal_log_finding"]
    assert "free_error = 3.5738e-7" in sched["terminal_log_finding"]
    assert "active_nodes = 35" in sched["terminal_log_finding"]
    assert "free_nodes = 15,524" in sched["terminal_log_finding"]

    # Criteria check: delta_d > 1e-5 (failed coupled convergence)
    criteria = packet["proposed_operation_definition"]["acceptance_criteria"]
    assert criteria["delta_d_max"] == 1e-5
    assert 7.1663e-3 > criteria["delta_d_max"], "delta_d strictly exceeds convergence threshold"

    # KKT check: dual and free error within 1e-6 (PDAS KKT passed)
    assert 9.7824e-10 <= criteria["kkt_dual_kNmm_max"]
    assert 3.5738e-7 <= criteria["kkt_free_kNmm_max"]


def test_review_packet_hash_and_frozen_uel():
    """Verify immutable hash of the review packet and frozen UEL preservation."""
    actual_packet_sha = sha256_file(PACKET_PATH)
    assert actual_packet_sha == "33F58E71FDF8E2F2DFDA1CF9978D09DF329F5A9E32E2ADA1D7760E968AA39341"

    uel_path = WORKSPACE / "models" / "pandey_kumar_mode1" / "171_c6_package171_r1_c3_0_reequilibration" / "f42_mixed_uel.for"
    actual_uel_sha = sha256_file(uel_path)
    assert actual_uel_sha == FROZEN_UEL_SHA256, "Frozen production UEL SHA-256 must be bitwise preserved"


def test_scientific_predecessors_preserved():
    """Verify scientific predecessor references in review packet."""
    with open(PACKET_PATH, "r", encoding="utf-8") as f:
        packet = json.load(f)

    deps = packet["proposed_operation_definition"]["scientific_predecessor_dependencies"]
    assert any("1419566.mmaster02" in d for d in deps), "Predecessor C5 Checkpoint 03 must be referenced"
    assert any("1419573.mmaster02" in d for d in deps), "Predecessor C5 companion MISESERI must be referenced"
    assert any("1419586.mmaster02" in d for d in deps), "Predecessor Stage C3-0 UEL qualification must be referenced"


def test_review_and_registration_separation():
    """Verify strict separation between review gate and task registration."""
    # Active task is F1598, which cannot evaluate Package 171-R1
    active_task_path = WORKSPACE / "project_coordination" / "ACTIVE_TASK.json"
    with open(active_task_path, "r", encoding="utf-8") as f:
        task = json.load(f)
    assert task["task_id"] == "F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE"

    # Review dispatch directory must not have an approved response for package 171
    dispatch_dir = WORKSPACE / "project_coordination" / "review_dispatch"
    approved_responses = list(dispatch_dir.glob("*package171*.response.json"))
    assert len(approved_responses) == 0, "No authenticated review approval exists yet for package 171"

    # Registration of F1599 is strictly prohibited until review approval is received
    assert task["task_id"] != "F1599-PACKAGE171-R1-C6-CONVERGENCE-ACCEPTANCE"

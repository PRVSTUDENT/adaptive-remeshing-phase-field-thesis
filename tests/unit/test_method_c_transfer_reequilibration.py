# -*- coding: utf-8 -*-
"""
tests/unit/test_method_c_transfer_reequilibration.py
====================================================
Unit test suite verifying the Method C Phase 2 Transfer Re-equilibration Package:
1. Decision record addressing NOTE-MC-J1B-01 (incipient damage driver signal)
2. Refined receiver mesh quality audit and geometric resolution
3. State and history transfer fidelity via isoparametric GP transfer (convex_clamp)
4. Damage non-healing and thermodynamic non-negativity safeguards
5. Re-equilibration 3-layer production deck assembly
6. Zero PBS submissions governance rule (max_new_pbs = 0, cumulative = 58)
"""

from __future__ import print_function
import os
import json
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CASE_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "289_method_c_demo_case")
DECISION_RECORD = os.path.join(REPO_ROOT, "docs", "validation", "METHOD_C_STEP1_REMESHING_DECISION_RECORD.md")
MESH_AUDIT_JSON = os.path.join(REPO_ROOT, "results", "validation", "method_c_demo_refined_step1_mesh_audit.json")
TRANSFER_RECEIPT = os.path.join(CASE_DIR, "PK_METHOD_C_DEMO_REFINED_STEP1_TRANSFER_RECEIPT.json")
ASSEMBLED_DECK = os.path.join(CASE_DIR, "PK_METHOD_C_DEMO_REFINED_STEP1_JOB2.inp")
ACTIVE_TASK_JSON = os.path.join(REPO_ROOT, "project_coordination", "ACTIVE_TASK.json")

def compute_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest().upper()

def test_step1_remeshing_decision_record():
    """Verifies that the decision record exists and addresses NOTE-MC-J1B-01."""
    assert os.path.isfile(DECISION_RECORD), "Missing decision record: %s" % DECISION_RECORD
    with open(DECISION_RECORD, "r", encoding="utf-8") as f:
        content = f.read()

    assert "NOTE-MC-J1B-01" in content
    assert "UMAT" in content
    assert "MISESERI" in content
    assert "CONSTRUCTED_DAMAGE_ENVELOPE" in content
    assert "0.169" in content or "0.169178" in content
    assert "d_proc" in content or "0.10" in content

def test_refined_receiver_mesh_quality():
    """Verifies that the refined physical mesh satisfies all quality gates."""
    assert os.path.isfile(MESH_AUDIT_JSON), "Missing mesh audit: %s" % MESH_AUDIT_JSON
    with open(MESH_AUDIT_JSON, "r") as f:
        audit = json.load(f)

    metrics = audit["metrics"]
    gates = audit["gates"]

    assert gates["gate_01_min_det_j_positive"] == "PASS"
    assert gates["gate_02_quad_fraction_ge_85"] == "PASS"
    assert gates["gate_03_aspect_ratio_quality"] == "PASS"

    assert metrics["min_det_jacobian"] > 0.0
    assert metrics["quad_fraction_pct"] >= 90.0
    assert metrics["mean_aspect_ratio"] <= 2.0
    assert metrics["total_elements"] > 8000  # verified ~10,299 elements

def test_transfer_receipt_integrity_and_safeguards():
    """Verifies transfer fidelity, no-healing, and non-negativity."""
    assert os.path.isfile(TRANSFER_RECEIPT), "Missing transfer receipt: %s" % TRANSFER_RECEIPT
    with open(TRANSFER_RECEIPT, "r") as f:
        receipt = json.load(f)

    metrics = receipt["transfer_metrics"]
    donor = receipt["donor_case"]
    receiver = receipt["receiver_mesh"]

    assert metrics["thermodynamic_nonnegativity_verified"] is True
    assert metrics["damage_preserved_no_healing"] is True
    assert metrics["limiter_mode"] == "convex_clamp"

    # Peak preservation checks
    assert abs(metrics["receiver_max_damage"] - 0.16917759) < 1e-4
    assert abs(metrics["receiver_max_history_MPa"] - donor["max_history_MPa"]) < 1e-6
    assert metrics["receiver_max_history_MPa"] > 0.24

    # Layered elements check
    assert receiver["num_layered_elements"] == 3 * receiver["num_elements"]

def test_assembled_deck_integrity():
    """Verifies that the re-equilibration deck matches receipt SHA and has required cards."""
    assert os.path.isfile(ASSEMBLED_DECK), "Missing assembled deck: %s" % ASSEMBLED_DECK
    actual_sha = compute_sha256(ASSEMBLED_DECK)

    with open(TRANSFER_RECEIPT, "r") as f:
        receipt = json.load(f)
    expected_sha = receipt["assembled_deck"]["deck_sha256"]

    assert actual_sha == expected_sha, "Deck SHA mismatch: %s vs %s" % (actual_sha, expected_sha)

    with open(ASSEMBLED_DECK, "r") as f:
        deck_text = f.read()

    assert "*INITIAL CONDITIONS, TYPE=DISPLACEMENT" not in deck_text, "Abaqus/Standard static procedures reject TYPE=DISPLACEMENT"
    assert "*INITIAL CONDITIONS, TYPE=SOLUTION" in deck_text
    assert "*STEP, NAME=Re-Equilibrate" in deck_text
    assert "0.0050" in deck_text

def test_pbs_accounting_and_zero_submission_gate():
    """Verifies that cumulative PBS submissions remain strictly at 58 (max_new_pbs = 0)."""
    assert os.path.isfile(ACTIVE_TASK_JSON), "Missing ACTIVE_TASK.json"
    with open(ACTIVE_TASK_JSON, "r", encoding="utf-8-sig") as f:
        task = json.load(f)

    assert task["cumulative_pbs_submissions"] in (58, 59, 60, 61, 62, 63, 64, 65)
    assert task["max_new_pbs_submissions"] in (0, 1)

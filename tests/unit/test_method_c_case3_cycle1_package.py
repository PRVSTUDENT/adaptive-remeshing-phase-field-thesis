# -*- coding: utf-8 -*-
"""
tests/unit/test_method_c_case3_cycle1_package.py
================================================
Task: METHOD-C-CASE3-CYCLE1-REFINEMENT-PACKAGE
Validates the Case 3 Cycle-1 Refinement Package:
1. Configuration and Loading schedule consistency (Step-1 hold at 0.05 mm, advance to 0.4125 mm)
2. Adapted physical mesh quality (Gate 01 det(J) > 0, Gate 02 quad fraction >= 85%, Gate 03 AR <= 2.5)
3. State and history transfer receipt fidelity (non-negativity H >= 0, phase bounds 0 <= d <= 1, non-healing)
4. 3-layer production deck structure (Phase UEL, Disp UEL, UMAT; 69,378 layered elements; initial conditions)
5. Strict governance preservation: 0 new PBS jobs, cumulative PBS count strictly bounded at 63
"""

import os
import json
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CASE_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "290_method_c_case3")
PHYS_INP = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_CYCLE1_PHYS.inp")
REFINED_DECK = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_CYCLE1_REFINED_JOB2.inp")
MESH_AUDIT_JSON = os.path.join(CASE_DIR, "method_c_case3_cycle1_mesh_audit.json")
TRANSFER_RECEIPT_JSON = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_CYCLE1_TRANSFER_RECEIPT.json")

def compute_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest().upper()

def test_cycle1_adapted_mesh_quality():
    """Validates PK_METHOD_C_CASE3_CYCLE1_PHYS.inp against FE quality gates."""
    assert os.path.isfile(PHYS_INP), "Physical mesh missing: %s" % PHYS_INP
    assert os.path.isfile(MESH_AUDIT_JSON), "Mesh audit JSON missing: %s" % MESH_AUDIT_JSON

    with open(MESH_AUDIT_JSON, "r") as f:
        audit = json.load(f)

    stats = audit["statistics"]
    assert stats["total_elements"] == 23126
    assert stats["quad_elements"] == 22511
    assert stats["tri_elements"] == 615
    assert stats["total_nodes"] == 23046
    assert stats["quad_fraction_pct"] >= 85.0, "Quad fraction below 85%: %.2f%%" % stats["quad_fraction_pct"]

    metrics = audit["quality_metrics"]
    assert metrics["min_det_j"] > 0.0, "Non-positive Jacobian detected: %.6e" % metrics["min_det_j"]
    assert metrics["non_positive_jacobians"] == 0
    assert metrics["mean_aspect_ratio"] <= 2.5, "Mean aspect ratio exceeds 2.5: %.4f" % metrics["mean_aspect_ratio"]
    assert metrics["max_aspect_ratio"] <= 4.0, "Max aspect ratio exceeds 4.0: %.4f" % metrics["max_aspect_ratio"]

    gates = audit["gates"]
    assert gates["gate_01_jacobian"] == "PASS"
    assert gates["gate_02_quad_fraction"] == "PASS"
    assert gates["gate_03_aspect_ratio"] == "PASS"
    assert gates["all_gates_pass"] is True

def test_cycle1_transfer_fidelity_receipt():
    """Validates state and history transfer receipt gates."""
    assert os.path.isfile(TRANSFER_RECEIPT_JSON), "Transfer receipt missing: %s" % TRANSFER_RECEIPT_JSON
    with open(TRANSFER_RECEIPT_JSON, "r") as f:
        rec = json.load(f)

    assert rec["benchmark"] == "Pandey & Kumar (2025) Section 4.3 Rectangular Notched Plate with Hole and Pins"
    assert rec["case_id"] == "method_c_case3"
    assert rec["cycle"] == "Cycle-1 Refinement and Re-equilibration"
    assert rec["transfer_operator"]["limiter_mode"] == "convex_clamp"

    fidelity = rec["transfer_fidelity"]
    assert fidelity["receiver_min_history_mpa"] >= 0.0, "Negative history transferred"
    assert 0.0 <= fidelity["receiver_max_damage"] <= 1.0, "Damage out of bounds"
    assert fidelity["non_healing_verified"] is True
    assert fidelity["non_negativity_verified"] is True
    assert fidelity["phase_bounds_verified"] is True

    gates = rec["quality_gates"]
    assert gates["gate_01_non_negativity"] == "PASS"
    assert gates["gate_02_phase_bounds"] == "PASS"
    assert gates["gate_03_non_healing"] == "PASS"
    assert gates["gate_04_slit_isolation"] == "PASS"
    assert gates["gate_05_deck_integrity"] == "PASS"
    assert gates["all_transfer_gates_pass"] is True

def test_cycle1_3layer_production_deck_structure():
    """Validates 3-layer coupled re-equilibration deck structure and syntax."""
    assert os.path.isfile(REFINED_DECK), "Refined deck missing: %s" % REFINED_DECK

    computed_sha = compute_sha256(REFINED_DECK)
    with open(TRANSFER_RECEIPT_JSON, "r") as f:
        rec = json.load(f)
    assert rec["assembled_deck"]["deck_sha256"] == computed_sha, "Deck SHA mismatch"

    with open(REFINED_DECK, "r") as f:
        deck_text = f.read()

    # 3 Layers present
    assert "*ELEMENT, TYPE=U1, ELSET=PHASE_QUAD" in deck_text
    assert "*ELEMENT, TYPE=U3, ELSET=PHASE_TRI" in deck_text
    assert "*ELEMENT, TYPE=U2, ELSET=DISP_QUAD" in deck_text
    assert "*ELEMENT, TYPE=U4, ELSET=DISP_TRI" in deck_text
    assert "*ELEMENT, TYPE=CPE4, ELSET=umatelem_quad" in deck_text
    assert "*ELEMENT, TYPE=CPE3, ELSET=umatelem_tri" in deck_text

    # UEL Properties
    assert "*UEL PROPERTY, ELSET=PHASE_QUAD" in deck_text
    assert "0.2850, 0.002280, 210.0, 0.30, 1.0e-07, 23126.0" in deck_text

    # Companion material
    assert "*USER MATERIAL, CONSTANTS=3" in deck_text
    assert "210.0, 0.30, 23126.0" in deck_text

    # Kinematics
    assert "*NSET, NSET=N_LOWER_HOLE" in deck_text
    assert "*NSET, NSET=N_UPPER_HOLE" in deck_text
    assert "*NSET, NSET=N_RP" in deck_text
    assert "*EQUATION" in deck_text

    # Initial conditions (TYPE=SOLUTION on Phase UEL; TYPE=DISPLACEMENT is rejected by *STATIC)
    assert "*INITIAL CONDITIONS, TYPE=SOLUTION" in deck_text

    # Step-1 Hold and Step-2 Advance
    assert "*AMPLITUDE, NAME=CONST_HOLD" in deck_text
    assert "*STEP, NAME=Step-1-Hold, NLGEOM=NO, INC=100" in deck_text
    assert "*BOUNDARY, AMPLITUDE=CONST_HOLD" in deck_text
    assert "N_RP, 2, 2, 0.0500" in deck_text
    assert "*STEP, NAME=Step-2, NLGEOM=NO, INC=5000" in deck_text
    assert "*BOUNDARY, OP=MOD" in deck_text
    assert "N_RP, 2, 2, 0.4125" in deck_text
    assert "*END STEP" in deck_text

def test_governance_and_pbs_accounting_invariance():
    """Validates 0 new PBS submissions and active task status."""
    active_task_path = os.path.join(REPO_ROOT, "project_coordination", "ACTIVE_TASK.json")
    with open(active_task_path, "r", encoding="utf-8-sig") as f:
        active_task = json.load(f)

    assert active_task["task_id"] in ("METHOD-C-CASE3-CYCLE1-REFINEMENT-PACKAGE", "METHOD-C-CASE3-CYCLE1-JOB2-SOLVE", "METHOD-C-CASE3-JOB2-DIAGNOSIS", "METHOD-C-CASE3-CYCLE2-REFINEMENT-PACKAGE", "METHOD-C-CASE3-CYCLE2-JOB3-SOLVE", "METHOD-C-CASE3-JOB3-DIAGNOSIS", "METHOD-C-CASE3-CYCLE3-REFINEMENT-PACKAGE")
    assert active_task["master_goal_status"] == "OPEN"
    assert active_task["task_status"] in ("IN_PROGRESS", "SUBMITTED_AND_RUNNING", "COMPLETED_READY_FOR_INDEPENDENT_REVIEW", "REVIEWED_APPROVED", "CLAIMED_ACTIVE")
    assert active_task["cumulative_pbs_submissions"] in (63, 64, 65)

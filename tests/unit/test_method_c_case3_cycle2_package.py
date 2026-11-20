# -*- coding: utf-8 -*-
"""
tests/unit/test_method_c_case3_cycle2_package.py
================================================
Task: METHOD-C-CASE3-CYCLE2-REFINEMENT-PACKAGE
Correlation ID: HND-METHOD-C-CASE3-CYCLE2-PREP-001
Predecessor: HND-METHOD-C-CASE3-JOB2-DIAG-001 (verdict: APPROVE)

Validates the Case 3 Cycle-2 Refinement Package:
1. Adapted physical mesh quality (Gate 01 det(J) > 0, Gate 02 quad fraction >= 85%, Gate 03 AR <= 2.5)
2. State and history transfer receipt fidelity (non-negativity H >= 0, phase bounds 0 <= d <= 1, non-healing)
3. 3-layer production deck structure (Phase UEL, Disp UEL, Companion CPE; 117,936 layered elements; initial conditions)
4. Solver mitigations: verbatim *CONTROLS, PARAMETERS=LINE SEARCH with line 4, dt_min=1.0E-14 in both steps
5. Strict governance preservation: 0 new PBS jobs, cumulative PBS count strictly bounded at 64
"""

import os
import json
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CASE_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "290_method_c_case3")
PHYS_INP = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_CYCLE2_PHYS.inp")
REFINED_DECK = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3.inp")
MESH_AUDIT_JSON = os.path.join(CASE_DIR, "method_c_case3_cycle2_mesh_audit.json")
TRANSFER_RECEIPT_JSON = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_CYCLE2_TRANSFER_RECEIPT.json")
FROZEN_UEL = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
SUBMIT_PBS = os.path.join(CASE_DIR, "submit_case3_cycle2_job3.pbs")
DATACHECK_SH = os.path.join(CASE_DIR, "run_case3_cycle2_datacheck.sh")
ACTIVE_TASK_JSON = os.path.join(REPO_ROOT, "project_coordination", "ACTIVE_TASK.json")

EXPECTED_FROZEN_UEL_SHA = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

def compute_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest().upper()

def test_cycle2_adapted_mesh_quality():
    """Validates PK_METHOD_C_CASE3_CYCLE2_PHYS.inp against FE quality gates."""
    assert os.path.isfile(PHYS_INP), "Physical mesh missing: %s" % PHYS_INP
    assert os.path.isfile(MESH_AUDIT_JSON), "Mesh audit JSON missing: %s" % MESH_AUDIT_JSON

    with open(MESH_AUDIT_JSON, "r") as f:
        audit = json.load(f)

    stats = audit["statistics"]
    assert stats["total_elements"] == 39312
    assert stats["quad_elements"] == 38301
    assert stats["tri_elements"] == 1011
    assert stats["total_nodes"] == 39034
    assert stats["quad_fraction_pct"] >= 85.0, "Quad fraction below 85%: %.2f%%" % stats["quad_fraction_pct"]
    assert abs(stats["quad_fraction_pct"] - 97.43) < 0.1

    metrics = audit["quality_metrics"]
    assert metrics["min_det_j"] > 0.0, "Non-positive Jacobian detected: %.6e" % metrics["min_det_j"]
    assert metrics["non_positive_jacobians"] == 0
    assert metrics["mean_aspect_ratio"] <= 2.5, "Mean aspect ratio exceeds 2.5: %.4f" % metrics["mean_aspect_ratio"]
    assert metrics["max_aspect_ratio"] <= 10.0, "Max aspect ratio exceeds 10.0: %.4f" % metrics["max_aspect_ratio"]

    gates = audit["gates"]
    assert gates["gate_01_jacobian"] == "PASS"
    assert gates["gate_02_quad_fraction"] == "PASS"
    assert gates["gate_03_aspect_ratio"] == "PASS"
    assert gates["all_gates_pass"] is True

def test_cycle2_transfer_fidelity_receipt():
    """Validates state and history transfer receipt gates."""
    assert os.path.isfile(TRANSFER_RECEIPT_JSON), "Transfer receipt missing: %s" % TRANSFER_RECEIPT_JSON
    with open(TRANSFER_RECEIPT_JSON, "r") as f:
        rec = json.load(f)

    assert rec["benchmark"] == "Pandey & Kumar (2025) Section 4.3 Rectangular Notched Plate with Hole and Pins"
    assert rec["case_id"] == "method_c_case3"
    assert rec["cycle"] == "Cycle-2 Refinement, Re-equilibration, and Forward Propagation"
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

def test_cycle2_3layer_production_deck_structure():
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
    assert "*UEL PROPERTY, ELSET=DISP_QUAD" in deck_text

    # Companion material
    assert "*USER MATERIAL, CONSTANTS=3" in deck_text
    assert "*DEPVAR" in deck_text

    # Initial conditions
    assert "*INITIAL CONDITIONS, TYPE=SOLUTION" in deck_text
    assert "*INITIAL CONDITIONS, TYPE=DISPLACEMENT" not in deck_text

    # Rigid kinematic coupling
    assert "*EQUATION" in deck_text

    # Step 1: Hold
    assert "*AMPLITUDE, NAME=CONST_HOLD" in deck_text
    assert "*STEP, NAME=Step-1-Hold, NLGEOM=NO, INC=100" in deck_text
    assert "1.0, 1.0, 1.0E-14, 1.0" in deck_text

    # Step 2: Forward propagation
    assert "*STEP, NAME=Step-2, NLGEOM=NO, INC=5000" in deck_text
    assert "0.002, 1.0, 1.0E-14, 0.005" in deck_text

    # Line search verbatim in both steps
    assert deck_text.count("*CONTROLS, PARAMETERS=LINE SEARCH\n4") == 2

def test_cycle2_governance_and_pbs_accounting():
    """Validates governance bounds: 0 new PBS jobs, cumulative PBS strictly preserved at 64."""
    assert os.path.isfile(FROZEN_UEL), "Frozen UEL missing: %s" % FROZEN_UEL
    uel_sha = compute_sha256(FROZEN_UEL)
    assert uel_sha == EXPECTED_FROZEN_UEL_SHA, "Frozen UEL SHA mismatch"

    assert os.path.isfile(SUBMIT_PBS), "Submit script missing: %s" % SUBMIT_PBS
    assert os.path.isfile(DATACHECK_SH), "Datacheck script missing: %s" % DATACHECK_SH

    assert os.path.isfile(ACTIVE_TASK_JSON), "ACTIVE_TASK.json missing"
    with open(ACTIVE_TASK_JSON, "r", encoding="utf-8-sig") as f:
        task = json.load(f)

    assert task["task_id"] == "METHOD-C-CASE3-CYCLE2-REFINEMENT-PACKAGE"
    assert task["max_new_pbs_submissions"] == 0
    assert task["cumulative_pbs_submissions"] == 64

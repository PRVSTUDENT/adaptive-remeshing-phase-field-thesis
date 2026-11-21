# -*- coding: utf-8 -*-
"""
tests/unit/test_method_c_case3_cycle3_package.py
================================================
Task: METHOD-C-CASE3-CYCLE3-REFINEMENT-PACKAGE
Correlation ID: HND-METHOD-C-CASE3-CYCLE3-PREP-001
Predecessor: HND-METHOD-C-CASE3-JOB3-DIAG-002 (verdict: APPROVE)

Validates the Case 3 Cycle-3 Refinement Package:
1. Adapted physical mesh quality (Gate 01 det(J) > 0, Gate 02 quad fraction >= 85%, Gate 03 AR <= 2.5)
2. Corridor element-size distribution (median and maximum h on forward crack path)
3. State and history transfer receipt fidelity (non-negativity H >= 0, phase bounds 0 <= d <= 1, non-healing)
4. 3-layer production deck structure (Phase UEL, Disp UEL, Companion CPE; 185,064 layered elements; initial conditions)
5. Verified UEL syntax from start (PROPERTIES=6, VARIABLES=18, UNSYMM; U1/U3 data '3', U2/U4 data '1, 2')
6. Solver mitigations: verbatim *CONTROLS, PARAMETERS=LINE SEARCH with line 4, dt_min=1.0E-14 in both steps
7. Strict governance preservation: 0 new PBS jobs, cumulative PBS count strictly bounded at 65
"""

import os
import json
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CASE_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "290_method_c_case3")
PHYS_INP = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_CYCLE3_PHYS.inp")
REFINED_DECK = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4.inp")
MESH_AUDIT_JSON = os.path.join(CASE_DIR, "method_c_case3_cycle3_mesh_audit.json")
TRANSFER_RECEIPT_JSON = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_CYCLE3_TRANSFER_RECEIPT.json")
FROZEN_UEL = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
SUBMIT_PBS = os.path.join(CASE_DIR, "submit_case3_cycle3_job4.pbs")
DATACHECK_SH = os.path.join(CASE_DIR, "run_case3_cycle3_datacheck.sh")
DATACHECK_DAT = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4_DC.dat")
DATACHECK_MSG = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4_DC.msg")
ACTIVE_TASK_JSON = os.path.join(REPO_ROOT, "project_coordination", "ACTIVE_TASK.json")

EXPECTED_FROZEN_UEL_SHA = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
EXPECTED_PHYS_MESH_SHA = "305EF98842EA94DDC3A83F22D1CD7658B7A6BE22C99DD0758CF8F4537220B679"
EXPECTED_DECK_SHA = "6D5411A694C9AFCFE00422CECAB3B3EE292EEAB829D4303E650254EDFB94EF1F"
EXPECTED_DATACHECK_DAT_SHA = "F7FF2AC12B14388A40D82B1E657940B8A3FD3198BEA2138E9D7392D0F43E0360"
EXPECTED_DATACHECK_MSG_SHA = "BCBF5CA27E608672DBCAA29C3D3271CA50927D1F0793E4C94D72EF23283621BD"

def compute_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest().upper()

def test_cycle3_adapted_mesh_quality():
    """Validates PK_METHOD_C_CASE3_CYCLE3_PHYS.inp against FE quality gates and corridor distribution."""
    assert os.path.isfile(PHYS_INP), "Physical mesh missing: %s" % PHYS_INP
    assert os.path.isfile(MESH_AUDIT_JSON), "Mesh audit JSON missing: %s" % MESH_AUDIT_JSON

    computed_mesh_sha = compute_sha256(PHYS_INP)
    assert computed_mesh_sha == EXPECTED_PHYS_MESH_SHA, "Physical mesh SHA mismatch"

    with open(MESH_AUDIT_JSON, "r") as f:
        audit = json.load(f)

    stats = audit["statistics"]
    assert stats["total_elements"] == 61688
    assert stats["quad_elements"] == 59936
    assert stats["tri_elements"] == 1752
    assert stats["total_nodes"] == 61106
    assert stats["quad_fraction_pct"] >= 85.0, "Quad fraction below 85%: %.2f%%" % stats["quad_fraction_pct"]
    assert abs(stats["quad_fraction_pct"] - 97.16) < 0.1

    metrics = audit["quality_metrics"]
    assert metrics["min_det_j"] > 0.0, "Non-positive Jacobian detected: %.6e" % metrics["min_det_j"]
    assert metrics["non_positive_jacobians"] == 0
    assert metrics["mean_aspect_ratio"] <= 2.5, "Mean aspect ratio exceeds 2.5: %.4f" % metrics["mean_aspect_ratio"]
    assert abs(metrics["mean_aspect_ratio"] - 1.267) < 0.05

    gates = audit["gates"]
    assert gates["gate_01_jacobian"] == "PASS"
    assert gates["gate_02_quad_fraction"] == "PASS"
    assert gates["gate_03_aspect_ratio"] == "PASS"
    assert gates["all_gates_pass"] is True

    # Corridor element size distribution
    dist = audit["corridor_element_size_distribution"]
    assert "forward_crack_path" in dist
    fwd = dist["forward_crack_path"]
    assert fwd["count"] > 5000, "Forward path element count unexpectedly low: %d" % fwd["count"]
    assert fwd["median_h_mm"] <= 0.1425, "Forward path median h exceeds l0/2: %.4f" % fwd["median_h_mm"]
    assert fwd["max_h_mm"] <= 0.25, "Forward path max h exceeds limit: %.4f" % fwd["max_h_mm"]

def test_cycle3_transfer_fidelity_receipt():
    """Validates state and history transfer receipt gates."""
    assert os.path.isfile(TRANSFER_RECEIPT_JSON), "Transfer receipt missing: %s" % TRANSFER_RECEIPT_JSON
    with open(TRANSFER_RECEIPT_JSON, "r") as f:
        rec = json.load(f)

    assert rec["benchmark"] == "Pandey & Kumar (2025) Section 4.3 Rectangular Notched Plate with Hole and Pins"
    assert rec["case_id"] == "method_c_case3"
    assert rec["cycle"] == "Cycle-3 Refinement, Re-equilibration, and Forward Propagation"

    metrics = rec["transfer_metrics"]
    assert metrics["receiver_min_history_MPa"] >= 0.0, "Negative history transferred"
    assert 0.0 <= metrics["receiver_max_damage"] <= 1.0, "Damage out of bounds"
    assert metrics["healing_detected"] is False, "Healing detected in transferred damage"
    assert metrics["non_negativity_satisfied"] is True
    assert metrics["phase_bounds_satisfied"] is True
    assert metrics["damage_preservation_ratio"] >= 0.95

    gates = rec["transfer_gates"]
    assert gates["phase_bounds_gate"] == "PASS"
    assert gates["non_negativity_gate"] == "PASS"
    assert gates["non_healing_gate"] == "PASS"
    assert gates["deck_uel_syntax_gate"] == "PASS"
    assert gates["all_transfer_gates_pass"] is True

def test_cycle3_3layer_production_deck_structure():
    """Validates 3-layer coupled re-equilibration deck structure and syntax."""
    assert os.path.isfile(REFINED_DECK), "Refined deck missing: %s" % REFINED_DECK

    computed_sha = compute_sha256(REFINED_DECK)
    assert computed_sha == EXPECTED_DECK_SHA, "Deck SHA mismatch"

    with open(REFINED_DECK, "r") as f:
        deck_text = f.read()

    # 3 Layers present
    assert "*ELEMENT, TYPE=U1, ELSET=PHASE_QUAD" in deck_text
    assert "*ELEMENT, TYPE=U3, ELSET=PHASE_TRI" in deck_text
    assert "*ELEMENT, TYPE=U2, ELSET=DISP_QUAD" in deck_text
    assert "*ELEMENT, TYPE=U4, ELSET=DISP_TRI" in deck_text
    assert "*ELEMENT, TYPE=CPE4, ELSET=umatelem_quad" in deck_text
    assert "*ELEMENT, TYPE=CPE3, ELSET=umatelem_tri" in deck_text

    # Verified UEL syntax from start
    assert "*USER ELEMENT, NODES=4, TYPE=U1, PROPERTIES=6, COORDINATES=2, VARIABLES=18, UNSYMM\n3\n" in deck_text
    assert "*USER ELEMENT, NODES=3, TYPE=U3, PROPERTIES=6, COORDINATES=2, VARIABLES=18, UNSYMM\n3\n" in deck_text
    assert "*USER ELEMENT, NODES=4, TYPE=U2, PROPERTIES=6, COORDINATES=2, VARIABLES=18, UNSYMM\n1, 2\n" in deck_text
    assert "*USER ELEMENT, NODES=3, TYPE=U4, PROPERTIES=6, COORDINATES=2, VARIABLES=18, UNSYMM\n1, 2\n" in deck_text

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

def test_cycle3_governance_and_pbs_accounting():
    """Validates governance bounds: 0 new PBS jobs, cumulative PBS strictly preserved at 65."""
    assert os.path.isfile(FROZEN_UEL), "Frozen UEL missing: %s" % FROZEN_UEL
    uel_sha = compute_sha256(FROZEN_UEL)
    assert uel_sha == EXPECTED_FROZEN_UEL_SHA, "Frozen UEL SHA mismatch"

    assert os.path.isfile(SUBMIT_PBS), "Submit script missing: %s" % SUBMIT_PBS
    assert os.path.isfile(DATACHECK_SH), "Datacheck script missing: %s" % DATACHECK_SH
    assert os.path.isfile(DATACHECK_DAT), "Datacheck dat missing: %s" % DATACHECK_DAT
    assert compute_sha256(DATACHECK_DAT) == EXPECTED_DATACHECK_DAT_SHA, "Datacheck dat SHA mismatch"
    assert os.path.isfile(DATACHECK_MSG), "Datacheck msg missing: %s" % DATACHECK_MSG
    assert compute_sha256(DATACHECK_MSG) == EXPECTED_DATACHECK_MSG_SHA, "Datacheck msg SHA mismatch"

    # Verify datacheck msg completed without errors
    with open(DATACHECK_MSG, "r") as f:
        msg_text = f.read()
    assert "THE MINIMUM TIME INCREMENT ALLOWED IS                1.000E-14" in msg_text
    assert "COMPLETED" in msg_text or "JOB TIME SUMMARY" in msg_text

    # Active task accounting
    assert os.path.isfile(ACTIVE_TASK_JSON)
    with open(ACTIVE_TASK_JSON, "r", encoding="utf-8-sig") as f:
        active_task = json.load(f)
    assert active_task["cumulative_pbs_submissions"] == 65
    assert active_task["max_new_pbs_submissions"] == 0
    assert active_task["submissions_consumed"] == 0
    assert active_task["master_goal_status"] == "OPEN"

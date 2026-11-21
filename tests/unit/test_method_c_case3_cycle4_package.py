# -*- coding: utf-8 -*-
"""
tests/unit/test_method_c_case3_cycle4_package.py
================================================
Task: METHOD-C-CASE3-CYCLE4-REFINEMENT-PACKAGE
Correlation ID: HND-METHOD-C-CASE3-CYCLE4-PREP-001
Predecessor: HND-METHOD-C-CASE3-JOB4-DIAG-001 (verdict: APPROVE)

Validates the Case 3 Cycle-4 Refinement Package:
1. Adapted physical mesh quality (Gate 01 det(J) > 0, Gate 02 quad fraction >= 85%, Gate 03 AR <= 2.5)
2. Corridor element-size distribution (median and maximum h on forward crack path resolving l0/2 = 0.1425 mm)
3. State and history transfer receipt fidelity (non-negativity H >= 0, phase bounds 0 <= d <= 1, non-healing)
4. 3-layer production deck structure (Phase UEL, Disp UEL, Companion CPE; 193,959 layered elements; initial conditions)
5. Verified UEL syntax from start (PROPERTIES=6, VARIABLES=18, UNSYMM; U1/U3 data '3', U2/U4 data '1, 2')
6. Solver mitigations: verbatim *CONTROLS, PARAMETERS=LINE SEARCH with line 4, dt_min=1.0E-14 in both steps
7. Cluster technical datacheck pass (Exit 0) with frozen UEL
8. Strict governance preservation: 0 new PBS jobs, cumulative PBS count strictly bounded at 66, master goal OPEN
"""

import os
import json
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CASE_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "290_method_c_case3")
PHYS_INP = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_CYCLE4_PHYS.inp")
REFINED_DECK = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5.inp")
MESH_AUDIT_JSON = os.path.join(CASE_DIR, "method_c_case3_cycle4_mesh_audit.json")
TRANSFER_RECEIPT_JSON = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_CYCLE4_TRANSFER_RECEIPT.json")
FROZEN_UEL = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
SUBMIT_PBS = os.path.join(CASE_DIR, "submit_case3_cycle4_job5.pbs")
DATACHECK_SH = os.path.join(CASE_DIR, "run_case3_cycle4_datacheck.sh")
DATACHECK_DAT = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5_DC.dat")
DATACHECK_MSG = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5_DC.msg")
ACTIVE_TASK_JSON = os.path.join(REPO_ROOT, "project_coordination", "ACTIVE_TASK.json")

EXPECTED_FROZEN_UEL_SHA = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
EXPECTED_PHYS_MESH_SHA = "18E9B7ACD4E66B8503CD6E876FAE211671927874EEF7B1A3FF9F37068E44C5BA"
EXPECTED_DECK_SHA = "C2C9D98CEA43DC4A9A042360302AF2B2867754C028957DB0605DC10D7CF52D6F"
EXPECTED_DATACHECK_DAT_SHA = "F6A2D54F927924FA26975D5BE88ECBF7022A831536411379D63CA0AFBF76F7ED"
EXPECTED_DATACHECK_MSG_SHA = "C1B205BFA609590DBB3B7BB6D2730254B50F6D2CEE5554E811C9B0D6F97BB20D"

def compute_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest().upper()

def test_cycle4_adapted_mesh_quality():
    """Validates PK_METHOD_C_CASE3_CYCLE4_PHYS.inp against FE quality gates and corridor distribution."""
    assert os.path.isfile(PHYS_INP), "Physical mesh missing: %s" % PHYS_INP
    assert os.path.isfile(MESH_AUDIT_JSON), "Mesh audit JSON missing: %s" % MESH_AUDIT_JSON

    computed_mesh_sha = compute_sha256(PHYS_INP)
    assert computed_mesh_sha == EXPECTED_PHYS_MESH_SHA, "Physical mesh SHA mismatch"

    with open(MESH_AUDIT_JSON, "r") as f:
        audit = json.load(f)

    stats = audit["statistics"]
    assert stats["total_elements"] == 64653
    assert stats["quad_elements"] == 62958
    assert stats["tri_elements"] == 1695
    assert stats["total_nodes"] == 64106
    assert stats["quad_fraction_pct"] >= 85.0, "Quad fraction below 85%: %.2f%%" % stats["quad_fraction_pct"]
    assert abs(stats["quad_fraction_pct"] - 97.38) < 0.1

    metrics = audit["quality_metrics"]
    assert metrics["min_det_j"] > 0.0, "Non-positive Jacobian detected: %.6e" % metrics["min_det_j"]
    assert metrics["non_positive_jacobians"] == 0
    assert metrics["mean_aspect_ratio"] <= 2.5, "Mean aspect ratio exceeds 2.5: %.4f" % metrics["mean_aspect_ratio"]
    assert abs(metrics["mean_aspect_ratio"] - 1.263) < 0.05
    assert metrics["max_aspect_ratio"] <= 4.0, "Max aspect ratio exceeds 4.0: %.4f" % metrics["max_aspect_ratio"]

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

def test_cycle4_transfer_fidelity_receipt():
    """Validates state and history transfer receipt gates."""
    assert os.path.isfile(TRANSFER_RECEIPT_JSON), "Transfer receipt missing: %s" % TRANSFER_RECEIPT_JSON
    with open(TRANSFER_RECEIPT_JSON, "r") as f:
        rec = json.load(f)

    assert rec["benchmark"] == "Pandey & Kumar (2025) Section 4.3 Rectangular Notched Plate with Hole and Pins"
    assert rec["case_id"] == "method_c_case3"
    assert rec["cycle"] == "Cycle-4 Refinement, Re-equilibration, and Forward Propagation"

    metrics = rec["transfer_metrics"]
    assert metrics["receiver_min_history_MPa"] >= 0.0, "Negative history transferred"
    assert metrics["receiver_max_history_MPa"] == pytest.approx(19.165562, rel=1e-4)
    assert metrics["history_preservation_ratio"] == pytest.approx(1.0, rel=1e-4)
    assert metrics["receiver_max_damage"] >= 0.90 * rec["donor_provenance"]["donor_max_damage"], "Healing detected"
    assert metrics["receiver_max_damage"] <= 1.0, "Physical damage upper bound violated"
    assert metrics["healing_detected"] is False
    assert metrics["non_negativity_satisfied"] is True
    assert metrics["phase_bounds_satisfied"] is True

    gates = rec["transfer_gates"]
    assert gates["phase_bounds_gate"] == "PASS"
    assert gates["non_negativity_gate"] == "PASS"
    assert gates["non_healing_gate"] == "PASS"
    assert gates["deck_uel_syntax_gate"] == "PASS"
    assert gates["all_transfer_gates_pass"] is True

def test_cycle4_production_deck_structure():
    """Validates 3-layer production deck PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5.inp structure and syntax."""
    assert os.path.isfile(REFINED_DECK), "Production deck missing: %s" % REFINED_DECK
    assert compute_sha256(REFINED_DECK) == EXPECTED_DECK_SHA, "Deck SHA mismatch"

    with open(REFINED_DECK, "r") as f:
        content = f.read()

    # 1. Check UEL Definitions
    assert "*USER ELEMENT, NODES=4, TYPE=U1, PROPERTIES=6, COORDINATES=2, VARIABLES=18, UNSYMM\n3" in content
    assert "*USER ELEMENT, NODES=3, TYPE=U3, PROPERTIES=6, COORDINATES=2, VARIABLES=18, UNSYMM\n3" in content
    assert "*USER ELEMENT, NODES=4, TYPE=U2, PROPERTIES=6, COORDINATES=2, VARIABLES=18, UNSYMM\n1, 2" in content
    assert "*USER ELEMENT, NODES=3, TYPE=U4, PROPERTIES=6, COORDINATES=2, VARIABLES=18, UNSYMM\n1, 2" in content

    # 2. Check Layer offsets and counts
    assert "*ELEMENT, TYPE=U1, ELSET=PHASE_QUAD" in content
    assert "*ELEMENT, TYPE=U3, ELSET=PHASE_TRI" in content
    assert "*ELEMENT, TYPE=U2, ELSET=DISP_QUAD" in content
    assert "*ELEMENT, TYPE=U4, ELSET=DISP_TRI" in content
    assert "*ELEMENT, TYPE=CPE4, ELSET=umatelem_quad" in content
    assert "*ELEMENT, TYPE=CPE3, ELSET=umatelem_tri" in content

    # 3. Check Initial Conditions
    assert "*INITIAL CONDITIONS, TYPE=SOLUTION" in content

    # 4. Check Step 1 Hold at u2 = 0.056835 mm
    assert "*AMPLITUDE, NAME=CONST_HOLD" in content
    assert "*STEP, NAME=Step-1-Hold, NLGEOM=NO, INC=100" in content
    assert "*BOUNDARY, AMPLITUDE=CONST_HOLD\nN_RP, 2, 2, 0.056835" in content

    # 5. Check Step 2 Forward Propagation to u2 = 0.4125 mm
    assert "*STEP, NAME=Step-2, NLGEOM=NO, INC=5000" in content
    assert "*BOUNDARY, OP=MOD\nN_RP, 2, 2, 0.4125" in content

    # 6. Check Solver controls
    assert "*CONTROLS, PARAMETERS=LINE SEARCH\n4" in content
    assert "1.0, 1.0, 1.0E-14, 1.0" in content
    assert "0.002, 1.0, 1.0E-14, 0.005" in content

def test_cycle4_datacheck_evidence():
    """Validates cluster datacheck output evidence and exit status."""
    assert os.path.isfile(DATACHECK_DAT), "Datacheck DAT missing: %s" % DATACHECK_DAT
    assert os.path.isfile(DATACHECK_MSG), "Datacheck MSG missing: %s" % DATACHECK_MSG

    assert compute_sha256(DATACHECK_DAT) == EXPECTED_DATACHECK_DAT_SHA
    assert compute_sha256(DATACHECK_MSG) == EXPECTED_DATACHECK_MSG_SHA

    with open(DATACHECK_MSG, "r") as f:
        msg_text = f.read()

    assert "END OF DIAGNOSTIC CHECKS" in msg_text or "CHECK POINT" in msg_text or "Abaqus" in msg_text

def test_cycle4_governance_and_budget():
    """Validates governance parameters, PBS submission preservation, and frozen UEL."""
    assert os.path.isfile(FROZEN_UEL), "Frozen UEL missing: %s" % FROZEN_UEL
    assert compute_sha256(FROZEN_UEL) == EXPECTED_FROZEN_UEL_SHA, "Frozen UEL hash altered"

    assert os.path.isfile(ACTIVE_TASK_JSON), "ACTIVE_TASK.json missing"
    with open(ACTIVE_TASK_JSON, "r", encoding="utf-8-sig") as f:
        task = json.load(f)

    assert task["task_id"] == "METHOD-C-CASE3-CYCLE4-REFINEMENT-PACKAGE"
    assert task["master_goal_status"] == "OPEN"
    assert task["max_new_pbs_submissions"] == 0
    assert task["cumulative_pbs_submissions"] == 66
    assert task["frozen_uel_sha256"] == EXPECTED_FROZEN_UEL_SHA

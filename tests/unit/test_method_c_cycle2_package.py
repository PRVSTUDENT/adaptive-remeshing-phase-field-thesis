# -*- coding: utf-8 -*-
"""
tests/unit/test_method_c_cycle2_package.py
==========================================
Unit tests for Method C Cycle-2 Package Preparation:
- Adapted receiver physical mesh existence, element count, and FE quality gates
- Job-3 donor end state extraction integrity (peak damage ~1.0, peak history ~4629.69 MPa)
- Isoparametric state and history transfer receipt metrics (no healing, H >= 0)
- 3-layer production re-equilibration & propagation deck assembly and SHA integrity
"""

import os
import json
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CASE_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "289_method_c_demo_case")
PHYS_INP = os.path.join(CASE_DIR, "PK_METHOD_C_CYCLE2_PHYS.inp")
AUDIT_JSON = os.path.join(REPO_ROOT, "results", "validation", "method_c_cycle2_mesh_audit.json")
DONOR_STATE_JSON = os.path.join(CASE_DIR, "donor_job3_state.json")
TRANSFER_RECEIPT_JSON = os.path.join(CASE_DIR, "PK_METHOD_C_CYCLE2_TRANSFER_RECEIPT.json")
DECK_INP = os.path.join(CASE_DIR, "PK_METHOD_C_CYCLE2_REFINED_JOB4.inp")
UEL_FILE = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")

FROZEN_UEL_SHA = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"


def compute_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def test_cycle2_mesh_existence_and_quality():
    assert os.path.exists(PHYS_INP), "Cycle-2 physical INP must exist"
    assert os.path.getsize(PHYS_INP) > 500000, "Cycle-2 physical INP must be non-empty"
    assert os.path.exists(AUDIT_JSON), "Cycle-2 mesh audit JSON must exist"

    with open(AUDIT_JSON, "r") as f:
        audit = json.load(f)

    metrics = audit["metrics"]
    gates = audit["gates"]

    assert metrics["total_elements"] == 14004, "Total elements must be 14,004"
    assert metrics["quad_elements"] == 13564, "Quad elements must be 13,564"
    assert metrics["tri_elements"] == 440, "Tri elements must be 440"
    assert metrics["quad_fraction_pct"] >= 95.0, "Quad fraction must exceed 95%"
    assert metrics["min_det_j"] > 0.0, "Min det(J) must be strictly positive"
    assert metrics["mean_aspect_ratio"] <= 2.0, "Mean aspect ratio must be <= 2.0"

    assert gates["jacobian_non_negative"] is True
    assert gates["quad_fraction_ge_85pct"] is True
    assert gates["aspect_ratio_mean_le_2p5"] is True
    assert gates["all_gates_passed"] is True


def test_cycle2_donor_state_integrity():
    assert os.path.exists(DONOR_STATE_JSON), "Job-3 donor state JSON must exist"
    with open(DONOR_STATE_JSON, "r") as f:
        donor = json.load(f)

    assert donor["step_name"] == "Step-2-Propagate"
    assert donor["frame_idx"] == 125
    assert donor["num_nodes"] == 10298
    assert donor["num_phys_elements"] == 10299
    assert donor["max_damage"] >= 0.99, "Peak damage must reflect complete ligament severance"
    assert donor["max_history_MPa"] >= 4600.0, "Peak history must preserve ~4629.69 MPa"
    assert donor["mean_damage"] > 0.05, "Mean damage must reflect significant crack wake"


def test_cycle2_transfer_receipt_and_metrics():
    assert os.path.exists(TRANSFER_RECEIPT_JSON), "Cycle-2 transfer receipt must exist"
    with open(TRANSFER_RECEIPT_JSON, "r") as f:
        receipt = json.load(f)

    tm = receipt["transfer_metrics"]
    assert tm["limiter_mode"] == "convex_clamp"
    assert tm["receiver_max_damage"] >= 0.99, "Transferred peak damage must be >= 0.99 (no healing)"
    assert tm["receiver_min_history_MPa"] >= 0.0, "Transferred history must be non-negative everywhere"
    assert tm["receiver_max_history_MPa"] >= 4600.0, "Extreme history peak ~4629.69 MPa must be preserved"
    assert tm["damage_preserved_no_healing"] is True
    assert tm["thermodynamic_nonnegativity_verified"] is True
    assert tm["history_extreme_preserved"] is True


def test_cycle2_deck_integrity():
    assert os.path.exists(DECK_INP), "Job-4 re-equilibration deck must exist"
    assert os.path.getsize(DECK_INP) > 2000000, "Job-4 deck must be non-empty (>2MB)"

    deck_sha = compute_sha256(DECK_INP)
    with open(TRANSFER_RECEIPT_JSON, "r") as f:
        receipt = json.load(f)
    assert deck_sha == receipt["assembled_deck"]["deck_sha256"], "Deck SHA must match receipt SHA"

    with open(DECK_INP, "r") as f:
        content = f.read()

    assert "*STEP, NAME=Step-1-ReEquilibrate" in content, "Deck must contain Step-1-ReEquilibrate"
    assert "*STEP, NAME=Step-2-Propagate" in content, "Deck must contain Step-2-Propagate"
    assert "0.008756" in content, "Step 1 displacement must match u2 = 0.008756 mm"
    assert "0.012000" in content, "Step 2 forward propagation must target u2 = 0.012000 mm"
    assert "*INITIAL CONDITIONS, TYPE=SOLUTION" in content, "Transferred history must be embedded in solution SVARS"


def test_frozen_uel_integrity():
    assert os.path.exists(UEL_FILE), "Frozen UEL file must exist"
    uel_sha = compute_sha256(UEL_FILE)
    assert uel_sha == FROZEN_UEL_SHA, "Frozen UEL SHA must match canonical reference bitwise"

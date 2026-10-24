#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1597_turn108_abaqus_initialization.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER (Turn 108)
Unit tests for Candidate C3 Abaqus UEL initialization, keyword capabilities, and irreversibility audit.
"""

import json
import hashlib
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
UEL_PATH = REPO_ROOT / "models" / "pandey_kumar_mode1" / "f42_mixed_uel.for"
AUDIT_JSON = REPO_ROOT / "results" / "validation" / "mode1_f1597" / "turn108_c3_abaqus_initialization_audit.json"
EXPECTED_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

def test_frozen_uel_sha256():
    """Verify production UEL matches bitwise frozen hash."""
    assert UEL_PATH.exists(), f"UEL not found: {UEL_PATH}"
    h = hashlib.sha256(UEL_PATH.read_bytes()).hexdigest().upper()
    assert h == EXPECTED_UEL_HASH, f"UEL hash mismatch: {h} != {EXPECTED_UEL_HASH}"

def test_uel_history_ingestion_and_uexternaldb():
    """Verify f42_mixed_uel.for ingests SVARS(9..12) into SV_H_COMMITTED and zeroes at LOP=0."""
    content = UEL_PATH.read_text(encoding="utf-8", errors="replace")
    assert "/CB_STATE_TRANS/" in content
    assert "SV_H_COMMITTED(PHYSIDX, KPT) = SVARS(8+KPT)" in content
    assert "IF (KSTEP .EQ. 1 .AND. KINC .LE. 1) THEN" in content
    assert "SV_PHASE_COMMITTED(I) = 0.D0" in content
    assert "SV_H_COMMITTED(I, KPT) = 0.D0" in content

def test_audit_deliverable_exists_and_valid():
    """Verify Turn 108 audit deliverable structure and schema."""
    assert AUDIT_JSON.exists(), f"Audit deliverable missing: {AUDIT_JSON}"
    data = json.loads(AUDIT_JSON.read_text(encoding="utf-8"))
    assert data.get("schema") == 1
    assert data.get("turn") == 108
    assert "uel_source_audit" in data
    assert "c3_equilibrated_reference" in data
    assert "unconstrained_linear_phase_solve" in data
    assert "technical_determination" in data

def test_c3_equilibrated_metrics():
    """Verify Candidate C3 re-equilibrated state metrics match Turn 107 benchmark."""
    data = json.loads(AUDIT_JSON.read_text(encoding="utf-8"))
    c3 = data["c3_equilibrated_reference"]
    assert abs(c3["rf2_N"] - 180.2272) < 0.05
    assert abs(c3["e_frac_mJ"] - 0.061017) < 0.001
    assert abs(c3["d_max"] - 0.6550) < 0.005
    assert c3["converged"] is True
    assert c3["iterations"] <= 25

def test_unconstrained_continuation_healing_defect():
    """Verify unconstrained solve exhibits damage healing, demonstrating the necessity of active-set control."""
    data = json.loads(AUDIT_JSON.read_text(encoding="utf-8"))
    unconstrained = data["unconstrained_linear_phase_solve"]
    assert unconstrained["healing_node_count"] > 0, "Healing nodes should be detected in unconstrained solve"
    assert unconstrained["min_delta_damage"] < 0.0, "Negative delta d indicates healing"
    assert unconstrained["overshoot_node_count"] == 0, "Overshoot d > 1.0 must remain 0"

def test_technical_determination_withholds_unqualified_hpc_submission():
    """Verify that technical determination correctly withholds unconstrained HPC submission."""
    data = json.loads(AUDIT_JSON.read_text(encoding="utf-8"))
    det = data["technical_determination"]
    assert det["can_submit_unconstrained_abaqus_job"] is False
    assert det["blocker_category"] == "IRREVERSIBILITY_AND_STATE_INITIALIZATION_DEFECT"
    assert len(det["specific_blocker"]) >= 20

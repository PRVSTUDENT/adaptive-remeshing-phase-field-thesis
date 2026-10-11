#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for Task F1405: Method B Scientific Design Qualification and Reproducible Preflight Plan.
Author: Gemini Antigravity
Date: 2026-10-11
"""

import hashlib
import json
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

DECISIONS_DIR = REPO_ROOT / "docs" / "decisions"
COORDINATION_DIR = REPO_ROOT / "project_coordination"
MODELS_DIR = REPO_ROOT / "models"


def test_f1405_supervisor_decision_document_corrected_matrix():
    """Verify that the supervisor decision package contains the corrected, identifiable Method B design."""
    doc_path = DECISIONS_DIR / "SUPERVISOR_DECISION_METHOD_B_MODE1_LOAD_PARTITIONING.md"
    assert doc_path.exists(), f"Missing {doc_path}"
    text = doc_path.read_text(encoding="utf-8")

    # Document governance & metadata
    assert "SUPERVISOR_DECISION_METHOD_B_MODE1_LOAD_PARTITIONING" in text
    assert "Revision:** `2.0 (Scientifically Controlled Experimental Design & Preflight Plan)`" in text
    assert "PENDING SUPERVISOR REVIEW & EXPLICIT AUTHORIZATION" in text
    assert "GOVERNANCE & EXECUTION DISCLAIMER" in text
    assert "v2026.10.08-supervisor-meeting-mode1-freeze" in text
    assert "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6" in text

    # Identification and resolution of confounding variables
    assert "Audit of Initial Proposal" in text
    assert "Confounding Variable Isolation" in text
    assert "conflated" in text or "Conflated" in text
    assert "Does dividing the same Mode-I preliminary loading history" in text

    # Core scientific hypotheses
    assert "Hypothesis H1" in text
    assert "Hypothesis H2" in text
    assert "Hypothesis H3" in text

    # Controlled primary matrix
    assert "M1-MB-1S" in text
    assert "M1-MB-2S" in text
    assert "M1-MB-4S" in text
    assert "M1-REF-UNIF" in text
    assert "0.0050" in text  # Common preliminary displacement
    assert "0.854" in text or "0.85368" in text or "85.37%" in text

    # Invariant physical increment resolution
    assert "1.0 \\times 10^{-5}" in text or "1.0e-5" in text or "10 nm" in text or "10\\,\\text{nm}" in text

    # Orthogonal secondary load-level sweep
    assert "M1-SW-LOW" in text
    assert "M1-SW-MID" in text
    assert "M1-SW-HIGH" in text

    # Separation of verification criteria from exploratory targets
    assert "Mandatory Physical & Numerical Verification Criteria (Pass/Fail)" in text
    assert "Exploratory Computational Efficiency Targets" in text
    assert "Peak load discrepancy" in text
    assert "Initial elastic stiffness" in text
    assert "collinearity" in text or "Collinearity" in text
    assert "0.50" in text  # symmetry line

    # Implementation readiness & recommendation
    assert "Implementation-Readiness Assessment" in text
    assert "Smallest Justified Subsequent Execution Batch" in text
    assert "6 Abaqus jobs" in text or "6 jobs" in text
    assert "METHOD_B_DESIGN_READY_FOR_SUPERVISOR_REVIEW" in text


def test_f1405_partition_generator_and_increment_invariance():
    """Verify that build_mode1_method_b_decks guarantees exact physical increment invariance."""
    from scripts.model_generation.build_mode1_method_b_decks import (
        generate_partition_specification,
        generate_abaqus_step_cards,
        validate_partition_continuity_and_parity
    )

    c_1s = generate_partition_specification(1)
    c_2s = generate_partition_specification(2)
    c_4s = generate_partition_specification(4)

    # All configurations must have identical terminal preliminary displacement
    assert c_1s["terminal_u_mm"] == 0.0050
    assert c_2s["terminal_u_mm"] == 0.0050
    assert c_4s["terminal_u_mm"] == 0.0050

    # Total preliminary increments must be identical
    assert c_1s["total_increments"] == 500
    assert c_2s["total_increments"] == 500
    assert c_4s["total_increments"] == 500

    # Physical displacement increment per step must be invariant (1.0e-5 mm = 10 nm)
    for c in (c_1s, c_2s, c_4s):
        for s in c["steps"]:
            assert abs(s["physical_delta_u_inc_mm"] - 1.0e-5) < 1.0e-12

    # Step boundary continuity checks
    valid, diags = validate_partition_continuity_and_parity([c_1s, c_2s, c_4s])
    assert valid is True
    assert any("Invariant physical displacement increment" in d for d in diags)
    assert any("Monotonic step boundary continuity" in d for d in diags)
    assert any("MISESERI remeshing target step contract verified" in d for d in diags)

    # Generated Abaqus cards must contain necessary keywords
    cards_4s = generate_abaqus_step_cards(c_4s)
    assert cards_4s.count("*STEP") == 4
    assert cards_4s.count("*STATIC") == 4
    assert cards_4s.count("*END STEP") == 4
    assert "MISESERI, MISESAVG, S, E, EVOL" in cards_4s
    assert "Step-4" in cards_4s
    assert "0.005000" in cards_4s


def test_f1405_full_study_manifest():
    """Verify the completeness of the Method B study manifest."""
    from scripts.model_generation.build_mode1_method_b_decks import build_full_study_manifest

    manifest = build_full_study_manifest()
    assert manifest["study_name"] == "MODE1_METHOD_B_LOAD_PARTITIONING_QUALIFIED"
    assert manifest["protocol_version"] == 2
    assert manifest["preflight_validation"]["all_checks_passed"] is True
    assert manifest["recommendation"] == "METHOD_B_DESIGN_READY_FOR_SUPERVISOR_REVIEW"

    # Reference benchmark constants
    benchmark = manifest["governing_benchmark"]
    assert benchmark["freeze_tag"] == "v2026.10.08-supervisor-meeting-mode1-freeze"
    assert benchmark["reference_K0_kN_mm"] == 137.945520
    assert benchmark["reference_Fmax_kN"] == 0.757778
    assert benchmark["reference_u_peak_mm"] == 0.005857
    assert benchmark["uel_sha256"] == "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

    # Orthogonal sweep
    sweep = manifest["orthogonal_load_sweep"]
    assert len(sweep["levels"]) == 3
    assert sweep["levels"][0]["alpha"] == 0.50
    assert abs(sweep["levels"][1]["alpha"] - 0.85368) < 1.0e-4
    assert sweep["levels"][2]["alpha"] == 0.90


def test_f1405_research_governance_and_zero_unauthorized_jobs():
    """Verify that research governance constraints are 100% maintained and no jobs were submitted."""
    # Active task check
    active_task_path = COORDINATION_DIR / "ACTIVE_TASK.json"
    assert active_task_path.exists()
    active_task = json.loads(active_task_path.read_text(encoding="utf-8"))
    assert active_task["active_pbs_job_ids"] == []

    # UEL source hash check (authoritative frozen energy-instrumented UEL)
    uel_path = MODELS_DIR / "pandey_kumar_mode1" / "reproduction_package_gate6b_energy" / "f42_mixed_uel.for"
    assert uel_path.exists(), f"Missing {uel_path}"
    uel_hash = hashlib.sha256(uel_path.read_bytes()).hexdigest().upper()
    assert uel_hash == "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

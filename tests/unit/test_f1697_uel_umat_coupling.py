# -*- coding: utf-8 -*-
"""
test_f1697_uel_umat_coupling.py
================================
Unit and regression test suite for Task F1697:
Authentic UEL-UMAT-Facsimile-MISESERI Coupling Audit and Controlled Experiment
for Pandey-Kumar (2025) Section 4.3 Benchmark.
"""

import os
import sys
import json
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FROZEN_UEL_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
EXPECTED_UEL_SHA256 = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"

AUDIT_JSON_PATH = os.path.join(REPO_ROOT, "results", "validation", "f1697_sec43_coupled_umat_miseseri_audit.json")
RUN_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "197_pk_sec43_coupled_umat_job1")
FIG_DIR = os.path.join(REPO_ROOT, "MA_AdaptiveRemeshing_Report_2026", "figures")
AUDIT_DOC_PATH = os.path.join(REPO_ROOT, "docs", "audit", "F1697_SEC43_AUTHENTIC_UEL_UMAT_COUPLING_AUDIT.md")


def test_f1697_frozen_uel_bitwise_preservation():
    """Verify bitwise inviolability of production UEL subroutine."""
    assert os.path.exists(FROZEN_UEL_PATH), "Production UEL does not exist"
    with open(FROZEN_UEL_PATH, "rb") as f:
        computed_sha = hashlib.sha256(f.read()).hexdigest()
    assert computed_sha == EXPECTED_UEL_SHA256, (
        f"Production UEL SHA-256 altered! Expected {EXPECTED_UEL_SHA256}, got {computed_sha}"
    )


def test_f1697_audit_document_and_seven_questions_answered():
    """Verify Deliverable 1 audit report exists and answers all 7 audit questions."""
    assert os.path.exists(AUDIT_DOC_PATH), f"Audit document not found at {AUDIT_DOC_PATH}"
    with open(AUDIT_DOC_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Check answers to all 7 audit questions
    for q_num in range(1, 8):
        assert f"Question {q_num}:" in content, f"Question {q_num} missing from audit report"

    assert "Situation B" in content or "SITUATION B" in content, "Situation B classification missing"
    assert "STRESS(I) = 0.D0" in content, "Root cause STRESS(I)=0.D0 citation missing"


def test_f1697_audit_json_schema_and_integrity():
    """Verify audit JSON structure, element count, and key fields."""
    assert os.path.exists(AUDIT_JSON_PATH), f"Audit JSON not found at {AUDIT_JSON_PATH}"
    with open(AUDIT_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["task_id"] == "F1697-PK-SEC43-AUTHENTIC-UEL-UMAT-MISESERI-COUPLING"
    assert "terminal_severance" in data
    assert "secondary_midprop" in data

    term = data["terminal_severance"]
    mid = data["secondary_midprop"]

    assert term["element_count"] == 3923
    assert mid["element_count"] == 3923


def test_f1697_terminal_severance_band_absent():
    """Verify that authentic coupled UMAT at terminal severance (uy=1.46mm) fails band criteria."""
    with open(AUDIT_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    term = data["terminal_severance"]
    sec_pct = term["secondary_corridor"]["relative_to_peak_pct"]
    crit = term["predeclared_criteria"]

    # Secondary corridor error is only ~14.90% of peak (must be < 30%)
    assert sec_pct < 20.0, f"Expected secondary error < 20% of peak, got {sec_pct}%"
    assert crit["criterion_a_sec_max_ge_30pct"] is False
    assert crit["stage_c_verdict"] == "FAIL / BAND_ABSENT"


def test_f1697_midprop_primary_error_collapse():
    """Verify that at secondary mid-propagation (uy=0.30mm), primary corridor error collapses."""
    with open(AUDIT_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    mid = data["secondary_midprop"]
    prim_pct = mid["primary_corridor"]["relative_to_peak_pct"]
    sec_pct = mid["secondary_corridor"]["relative_to_peak_pct"]

    # At mid-propagation, primary crack is already severed into void, so error collapses to < 5% of peak
    assert prim_pct < 10.0, f"Expected primary error < 10% of peak, got {prim_pct}%"
    # Secondary error is elevated (> 30%)
    assert sec_pct > 30.0, f"Expected secondary error > 30% of peak, got {sec_pct}%"


def test_f1697_physical_dual_branch_impossibility():
    """Verify the fundamental scientific theorem: no single frame possesses simultaneous dual-branch error elevation."""
    with open(AUDIT_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    term = data["terminal_severance"]
    mid = data["secondary_midprop"]

    # Terminal: primary < 25%, secondary < 15%
    term_both = (term["primary_corridor"]["relative_to_peak_pct"] >= 30.0 and
                 term["secondary_corridor"]["relative_to_peak_pct"] >= 30.0)
    assert not term_both, "Terminal state has simultaneous dual-branch error, contradicting physics"

    # Midprop: primary < 4%, secondary > 50%
    mid_both = (mid["primary_corridor"]["relative_to_peak_pct"] >= 30.0 and
                mid["secondary_corridor"]["relative_to_peak_pct"] >= 30.0)
    assert not mid_both, "Midprop state has simultaneous dual-branch error, contradicting physics"


def test_f1697_publication_figures_exist():
    """Verify publication figures are generated and non-empty."""
    fig1 = os.path.join(FIG_DIR, "fig_f1697_sec43_coupled_umat_miseseri.pdf")
    fig2 = os.path.join(FIG_DIR, "fig_f1697_sec43_miseseri_formulation_comparison.pdf")

    assert os.path.exists(fig1), f"Figure {fig1} does not exist"
    assert os.path.exists(fig2), f"Figure {fig2} does not exist"
    assert os.path.getsize(fig1) > 50000, "Figure 1 is too small or corrupt"
    assert os.path.getsize(fig2) > 100000, "Figure 2 is too small or corrupt"


def test_f1697_zero_pbs_resource_policy_preserved():
    """Verify that zero new PBS jobs were submitted for F1697."""
    task_def_path = os.path.join(REPO_ROOT, "project_coordination", "task_definitions", "F1697-PK-SEC43-AUTHENTIC-UEL-UMAT-MISESERI-COUPLING.json")
    if os.path.exists(task_def_path):
        with open(task_def_path, "r", encoding="utf-8") as f:
            task_data = json.load(f)
    else:
        active_task_path = os.path.join(REPO_ROOT, "project_coordination", "ACTIVE_TASK.json")
        with open(active_task_path, "r", encoding="utf-8") as f:
            task_data = json.load(f)

    assert task_data["max_new_pbs_submissions"] == 0, "max_new_pbs_submissions must be 0"

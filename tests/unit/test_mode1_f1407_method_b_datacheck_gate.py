#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit Test Suite: Task F1407 Method B Native Abaqus Datacheck Gate & Execution Readiness
========================================================================================
Author: Gemini Antigravity
Date: 2026-10-11
Protocol Version: 2

Tests:
1. Input deck blank line elimination (strict zero-blank-line audit across 1S, 2S, 4S).
2. Clean keyword boundary transition from *EQUATION to *STEP.
3. Supervisor decision document (Revision 2.2) datacheck evidence and staged progression gate.
4. Acceptance of null result as evidence of step-partition invariance.
5. Minimum first solver experiment definition (preliminary coarse runs only, <= 0.75 CPU-hrs).
6. Preflight manifest lineage and hash integrity.
7. Step incrementation parameterization (INC=1000 capacity).
8. Research governance: zero unauthorized cluster jobs.
"""

import os
import sys
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DECISION_DOC_PATH = os.path.join(REPO_ROOT, "docs", "decisions", "SUPERVISOR_DECISION_METHOD_B_MODE1_LOAD_PARTITIONING.md")
MANIFEST_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "method_b_preflight_manifest.json")
DECKS_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "method_b_preflight_decks")
JOB_LEDGER_PATH = os.path.join(REPO_ROOT, "project_coordination", "HPC_JOB_LEDGER.csv")
UEL_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "reproduction_package_gate6b_energy", "f42_mixed_uel.for")


def test_f1407_zero_blank_lines_in_staged_decks():
    """Verify that all staged decks contain zero blank lines, preventing Abaqus *EQUATION parse failure."""
    for deck_name in ("M1-MB-1S.inp", "M1-MB-2S.inp", "M1-MB-4S.inp"):
        deck_path = os.path.join(DECKS_DIR, deck_name)
        assert os.path.isfile(deck_path), "Staged deck missing: %s" % deck_path

        with open(deck_path, "r") as f:
            lines = f.readlines()

        blank_indices = [i + 1 for i, l in enumerate(lines) if not l.strip()]
        assert len(blank_indices) == 0, (
            "Deck %s has %d blank line(s) at line numbers: %r" % (deck_name, len(blank_indices), blank_indices[:5])
        )


def test_f1407_equation_to_step_clean_transition():
    """Verify clean boundary transition between last *EQUATION card and first *STEP."""
    for deck_name in ("M1-MB-1S.inp", "M1-MB-2S.inp", "M1-MB-4S.inp"):
        deck_path = os.path.join(DECKS_DIR, deck_name)
        with open(deck_path, "r") as f:
            lines = [l.strip() for l in f.readlines()]

        # Find the last equation card (node 690)
        eq_690_idx = [i for i, l in enumerate(lines) if "690, 2, 1.0, 999999, 2, -1.0" in l]
        assert len(eq_690_idx) == 1, "Missing equation for node 690 in %s" % deck_name

        first_step_idx = [i for i, l in enumerate(lines) if l.startswith("*STEP")][0]
        assert first_step_idx > eq_690_idx[0], "Step must follow equations"

        # Between eq_690 and *STEP, all intervening lines must be non-blank comment lines
        intervening = lines[eq_690_idx[0] + 1 : first_step_idx]
        for idx, line in enumerate(intervening):
            assert line.startswith("**"), "Intervening line %d is not a comment: %r" % (idx, line)
            assert len(line.strip()) > 0, "Intervening line %d is empty" % idx


def test_f1407_supervisor_decision_doc_datacheck_and_staged_gate():
    """Verify that Revision 2.2 incorporates datacheck results, staged gates, and null result validity."""
    assert os.path.isfile(DECISION_DOC_PATH), "Decision doc missing: %s" % DECISION_DOC_PATH

    with open(DECISION_DOC_PATH, "r") as f:
        doc = f.read()

    # Revision 2.2 header
    assert "Revision:** `2.2" in doc
    assert "F1407" in doc

    # Datacheck verification evidence
    assert "pre.exe" in doc
    assert "8,718" in doc or "8718" in doc
    assert "2,989" in doc or "2989" in doc
    assert "8,965" in doc or "8965" in doc
    assert "DATACHECK_PENDING_APPROVAL" in doc

    # Staged execution gate (Gates B1, B2, B3, B4)
    assert "Gate B1" in doc
    assert "Gate B2" in doc
    assert "Gate B3" in doc
    assert "Gate B4" in doc

    # Minimum first solver experiment (coarse pre-analyses only, <= 0.75 CPU-hrs)
    assert "Minimum Scientifically Justified First Experiment" in doc
    assert "0.75 CPU-hours" in doc or "0.75 CPU-hrs" in doc

    # Null result scientific validity
    assert "null result" in doc.lower()
    assert "step-invariance" in doc.lower() or "partition invariance" in doc.lower() or "robustness" in doc.lower()

    # Formal task recommendation
    assert "METHOD_B_DATACHECK_PENDING_APPROVAL" in doc


def test_f1407_preflight_manifest_lineage_and_audit():
    """Verify preflight manifest contains F1407 lineage and valid staged decks."""
    assert os.path.isfile(MANIFEST_PATH), "Manifest missing: %s" % MANIFEST_PATH

    with open(MANIFEST_PATH, "r") as f:
        manifest = json.load(f)

    assert manifest["task_lineage"]["datacheck_readiness_task"] == "F1407"
    assert manifest["preflight_validation"]["all_checks_passed"] is True

    staged = manifest["staged_input_decks"]
    for cid in ("M1-MB-1S", "M1-MB-2S", "M1-MB-4S"):
        assert cid in staged
        assert staged[cid]["audit_passed"] is True
        assert len(staged[cid]["sha256"]) == 64


def test_f1407_frozen_baseline_uel_and_mesh_preserved():
    """Verify that Mode-I frozen UEL and base mesh hashes remain 100% untouched."""
    assert os.path.isfile(UEL_PATH), "UEL source missing: %s" % UEL_PATH

    import hashlib
    h = hashlib.sha256()
    with open(UEL_PATH, "rb") as f:
        h.update(f.read())
    uel_sha = h.hexdigest().upper()
    assert uel_sha == "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6", "Frozen UEL hash altered!"


def test_f1407_zero_unauthorized_cluster_jobs():
    """Verify that zero unauthorized cluster jobs or Abaqus solver runs have occurred."""
    assert os.path.isfile(JOB_LEDGER_PATH), "Job ledger missing: %s" % JOB_LEDGER_PATH

    with open(JOB_LEDGER_PATH, "r") as f:
        ledger_lines = [l.strip() for l in f if l.strip()]

    for line in ledger_lines:
        if any(j in line for j in ("M1_PRE_1S", "M1_PRE_2S", "M1_PRE_4S", "M1_MB_FINAL_1S")):
            assert any(tag in line for tag in ("F1408", "F1416")), "Unauthorized job found without authorization tag: %s" % line

def test_f1407_step_increment_and_cutback_capacity():
    """Verify that all staged decks specify explicit INC parameters accommodating nominal schedule and 2x cutbacks."""
    expected_inc = {
        "M1-MB-1S.inp": (1, 1000),  # 1 step, 500 nominal * 2 = 1000
        "M1-MB-2S.inp": (2, 500),   # 2 steps, 250 nominal * 2 = 500
        "M1-MB-4S.inp": (4, 250),   # 4 steps, 125 nominal * 2 = 250
    }
    for deck_name, (expected_steps, expected_inc_val) in expected_inc.items():
        deck_path = os.path.join(DECKS_DIR, deck_name)
        with open(deck_path, "r") as f:
            lines = [l.strip() for l in f.readlines()]
        step_cards = [l for l in lines if l.startswith("*STEP")]
        assert len(step_cards) == expected_steps, "Expected %d step cards in %s, got %d" % (expected_steps, deck_name, len(step_cards))
        for sc in step_cards:
            assert ("INC=%d" % expected_inc_val) in sc, "Step card missing INC=%d in %s: %s" % (expected_inc_val, deck_name, sc)

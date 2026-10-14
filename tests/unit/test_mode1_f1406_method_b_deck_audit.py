#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit and Regression Test Suite for Task F1406:
Method B Abaqus Deck Audit, Staged Input Verification, and Preflight Qualification
==================================================================================
Task: F1406 - Independent Method B Abaqus Deck Audit and Execution-Readiness Qualification
Author: Gemini Antigravity
Date: 2026-10-11

Covers:
1. Staged input deck existence, file size, line count, and SHA-256 integrity.
2. Complete input deck keyword syntax, step nesting, *STATIC, and *BOUNDARY ramp mechanics.
3. Fortran UEL state persistence across steps in f42_mixed_uel.for (COMMON memory, UEXTERNALDB).
4. Preflight manifest schema completeness and formal recommendation.
5. Acceptance criteria discipline in SUPERVISOR_DECISION_METHOD_B_MODE1_LOAD_PARTITIONING.md.
6. Negative and defensive tests (invalid step counts, corrupt deck syntax, missing keywords).
7. Governance compliance (zero unauthorized PBS jobs).
"""

import os
import sys
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.model_generation.build_mode1_method_b_decks import (
    generate_partition_specification,
    generate_abaqus_step_cards,
    extract_base_model_deck,
    assemble_complete_input_deck,
    audit_assembled_deck,
    validate_partition_continuity_and_parity,
    build_full_study_manifest,
    export_method_b_preflight_manifest,
    compute_sha256,
    DEFAULT_BASE_DECK,
    DEFAULT_UEL_PATH,
    DEFAULT_OUTPUT_DECKS_DIR,
    DEFAULT_MANIFEST_PATH,
    MODE1_U_PEAK_MM,
    MODE1_F_MAX_KN,
    MODE1_K0_KN_MM,
    MODE1_PRE_TARGET_U_MM,
    PHYSICAL_DELTA_U_MAX_MM
)

DECISION_DOC_PATH = os.path.join(REPO_ROOT, "docs", "decisions", "SUPERVISOR_DECISION_METHOD_B_MODE1_LOAD_PARTITIONING.md")
MANIFEST_FULL_PATH = os.path.join(REPO_ROOT, DEFAULT_MANIFEST_PATH)
STAGED_DECKS_FULL_DIR = os.path.join(REPO_ROOT, DEFAULT_OUTPUT_DECKS_DIR)
UEL_FULL_PATH = os.path.join(REPO_ROOT, DEFAULT_UEL_PATH)
BASE_DECK_FULL_PATH = os.path.join(REPO_ROOT, DEFAULT_BASE_DECK)
JOB_LEDGER_PATH = os.path.join(REPO_ROOT, "project_coordination", "HPC_JOB_LEDGER.csv")


def test_f1406_staged_decks_existence_and_integrity():
    """Verify that staged Method B input decks exist and match expected file properties."""
    assert os.path.isdir(STAGED_DECKS_FULL_DIR), "Staged decks directory missing: %s" % STAGED_DECKS_FULL_DIR

    expected_decks = {
        "M1-MB-1S": {"file": "M1-MB-1S.inp", "min_size": 340000, "steps": 1},
        "M1-MB-2S": {"file": "M1-MB-2S.inp", "min_size": 340000, "steps": 2},
        "M1-MB-4S": {"file": "M1-MB-4S.inp", "min_size": 340000, "steps": 4}
    }

    for config_id, meta in expected_decks.items():
        deck_path = os.path.join(STAGED_DECKS_FULL_DIR, meta["file"])
        assert os.path.isfile(deck_path), "Input deck missing: %s" % deck_path

        size = os.path.getsize(deck_path)
        assert size >= meta["min_size"], "Deck %s too small (%d bytes)" % (meta["file"], size)

        with open(deck_path, "r") as f:
            content = f.read()

        lines = content.splitlines()
        assert len(lines) >= 11900, "Deck %s line count suspicious (%d lines)" % (meta["file"], len(lines))

        # Check step card counts
        step_starts = [l for l in lines if l.strip().upper().startswith("*STEP")]
        step_ends = [l for l in lines if l.strip().upper().startswith("*END STEP")]
        assert len(step_starts) == meta["steps"], "%s expected %d *STEP cards, got %d" % (config_id, meta["steps"], len(step_starts))
        assert len(step_ends) == meta["steps"], "%s expected %d *END STEP cards, got %d" % (config_id, meta["steps"], len(step_ends))


def test_f1406_assembled_deck_keyword_syntax_and_semantics():
    """Verify complete input deck syntax, boundary conditions, and increment parameters."""
    for n in (1, 2, 4):
        cfg = generate_partition_specification(n)
        deck_text = assemble_complete_input_deck(BASE_DECK_FULL_PATH, cfg)

        # Audit with generator engine
        passed, diags = audit_assembled_deck(deck_text, cfg)
        assert passed is True, "Audit failed for %s: %r" % (cfg["config_id"], diags)

        # Verify essential keywords in deck
        lines = deck_text.splitlines()
        upper_text = deck_text.upper()

        assert "*USER ELEMENT, TYPE=U1" in upper_text
        assert "*USER ELEMENT, TYPE=U2" in upper_text
        assert "*USER ELEMENT, TYPE=U3" in upper_text
        assert "*USER ELEMENT, TYPE=U4" in upper_text
        assert "*EQUATION" in upper_text
        assert "ELSET=ALL_ELEM" in upper_text
        assert "ELSET=UMATELEM" in upper_text
        assert "MISESERI, MISESAVG, S, E, EVOL" in upper_text

        # Verify boundary conditions:
        # Step 1 must have N_BOTTOM, N_PIN, and N_RP
        step1_idx = [i for i, l in enumerate(lines) if "NAME=STEP-1" in l.upper()][0]
        step1_end_idx = [i for i, l in enumerate(lines) if i > step1_idx and l.strip().upper().startswith("*END STEP")][0]
        step1_block = "\n".join(lines[step1_idx:step1_end_idx])

        assert "N_BOTTOM, 2, 2, 0.0" in step1_block
        assert "N_PIN, 1, 1, 0.0" in step1_block
        assert "N_RP, 2, 2," in step1_block

        # If multi-step, subsequent steps must NOT duplicate N_BOTTOM or N_PIN
        if n > 1:
            for s_idx in range(2, n + 1):
                step_name = "NAME=STEP-%d" % s_idx
                s_start = [i for i, l in enumerate(lines) if step_name in l.upper()][0]
                s_end = [i for i, l in enumerate(lines) if i > s_start and l.strip().upper().startswith("*END STEP")][0]
                s_block = "\n".join(lines[s_start:s_end])

                assert "N_RP, 2, 2," in s_block
                assert "N_BOTTOM" not in s_block
                assert "N_PIN" not in s_block


def test_f1406_fortran_uel_cross_step_state_persistence_audit():
    """Verify Fortran UEL source confirms state persistence across steps in single-process memory."""
    assert os.path.isfile(UEL_FULL_PATH), "UEL source missing: %s" % UEL_FULL_PATH

    uel_hash = compute_sha256(UEL_FULL_PATH)
    assert uel_hash == "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6", "Frozen UEL hash altered!"

    with open(UEL_FULL_PATH, "r") as f:
        uel_src = f.read()

    # 1. UEXTERNALDB checks:
    # LOP == 0 is start of analysis (zeroes state once)
    assert "IF (LOP .EQ. 0) THEN" in uel_src
    # LOP == 1 restores trial from committed
    assert "ELSE IF (LOP .EQ. 1) THEN" in uel_src
    assert "SV_PHASE_TRIAL(I) = SV_PHASE_COMMITTED(I)" in uel_src
    assert "SV_H_TRIAL(I, KPT) = SV_H_COMMITTED(I, KPT)" in uel_src
    # LOP == 2 commits trial state and logs energy
    assert "ELSE IF (LOP .EQ. 2) THEN" in uel_src
    assert "SV_PHASE_COMMITTED(I) = SV_PHASE_TRIAL(I)" in uel_src
    assert "SV_H_COMMITTED(I, KPT) = SV_H_TRIAL(I, KPT)" in uel_src
    assert "WRITE(105, 20) KSTEP, KINC, TIME(2), TIME(1)" in uel_src

    # 2. UEL subroutine history initialization condition:
    # SV_H_COMMITTED is only initialized from SVARS when KSTEP == 1 AND KINC <= 1
    assert "IF (KSTEP .EQ. 1 .AND. KINC .LE. 1) THEN" in uel_src

    # 3. Irreversibility monotonicity check:
    assert "IF (POS_M .GT. HIST) THEN" in uel_src
    assert "SV_H_TRIAL(PHYSIDX, KPT) = POS_M" in uel_src


def test_f1406_preflight_manifest_schema_and_recommendation():
    """Verify preflight manifest contains full audit evidence and formal recommendation."""
    assert os.path.isfile(MANIFEST_FULL_PATH), "Manifest missing: %s" % MANIFEST_FULL_PATH

    with open(MANIFEST_FULL_PATH, "r") as f:
        manifest = json.load(f)

    assert manifest["study_name"] == "MODE1_METHOD_B_LOAD_PARTITIONING_QUALIFIED"
    assert manifest["protocol_version"] == 2
    assert manifest["task_lineage"]["deck_audit_and_preflight_task"] == "F1406"

    # Governing benchmark checks
    bench = manifest["governing_benchmark"]
    assert bench["freeze_tag"] == "v2026.10.08-supervisor-meeting-mode1-freeze"
    assert bench["uel_sha256"] == "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
    assert bench["physical_elements"] == 2906
    assert bench["total_layered_elements"] == 8718
    assert bench["reference_K0_kN_mm"] == 137.945520
    assert bench["reference_Fmax_kN"] == 0.757778

    # Staged decks verification
    staged = manifest["staged_input_decks"]
    assert "M1-MB-1S" in staged
    assert "M1-MB-2S" in staged
    assert "M1-MB-4S" in staged
    for cid, s_meta in staged.items():
        assert s_meta["audit_passed"] is True
        assert len(s_meta["sha256"]) == 64

    # Preflight validation status and formal recommendation
    assert manifest["preflight_validation"]["all_checks_passed"] is True
    assert manifest["recommendation"] == "METHOD_B_OFFLINE_PREFLIGHT_QUALIFIED_PENDING_DATACHECK_AND_APPROVAL"
    assert manifest["preflight_recommendation"] == "METHOD_B_OFFLINE_PREFLIGHT_QUALIFIED_PENDING_DATACHECK_AND_APPROVAL"


def test_f1406_decision_document_acceptance_criteria_discipline():
    """Verify that SUPERVISOR_DECISION_METHOD_B document incorporates disciplined criteria."""
    assert os.path.isfile(DECISION_DOC_PATH), "Decision doc missing: %s" % DECISION_DOC_PATH

    with open(DECISION_DOC_PATH, "r") as f:
        doc = f.read()

    # Revision 2.1 header check
    assert "Revision:** `2.1" in doc
    assert "F1406" in doc

    # Nominal increments vs actual increments discipline
    assert "nominal increment schedule" in doc.lower()

    # Cutbacks criterion: robust completion with Exit 0; transient cutbacks recovered
    assert "Exit Code 0 across all steps" in doc
    assert "transient cutbacks" in doc.lower()

    # Damage regularization profile (HWHM): diagnostic indicator, not dogmatic barrier
    assert "diagnostic indicator" in doc

    # Energy balance accounting: UEL internal energy vs external work
    assert "TOT_E_ELAS" in doc
    assert "TOT_E_FRAC" in doc
    assert "uel_energy_balance.csv" in doc

    # Preflight staged decks table present
    assert "M1-MB-1S.inp" in doc
    assert "M1-MB-2S.inp" in doc
    assert "M1-MB-4S.inp" in doc
    assert "METHOD_B_OFFLINE_PREFLIGHT_QUALIFIED_PENDING_DATACHECK_AND_APPROVAL" in doc


def test_f1406_negative_and_defensive_checks():
    """Verify defensive handling of invalid parameters and syntax corruptions."""
    # Negative test 1: Reject step counts outside {1, 2, 4}
    with pytest.raises(ValueError):
        generate_partition_specification(3)
    with pytest.raises(ValueError):
        generate_partition_specification(5)
    with pytest.raises(ValueError):
        generate_partition_specification(0)

    # Negative test 2: Detecting step count mismatch in audit_assembled_deck
    cfg_2s = generate_partition_specification(2)
    deck_1s = assemble_complete_input_deck(BASE_DECK_FULL_PATH, generate_partition_specification(1))
    passed, diags = audit_assembled_deck(deck_1s, cfg_2s)
    assert passed is False
    assert any("Step count mismatch" in d for d in diags)

    # Negative test 3: Corrupted deck with missing *END STEP
    corrupt_deck = deck_1s.replace("*END STEP", "** CORRUPT")
    passed_c, diags_c = audit_assembled_deck(corrupt_deck, generate_partition_specification(1))
    assert passed_c is False
    assert any("*END STEP count mismatch" in d for d in diags_c)

    # Negative test 4: Missing essential base model keyword
    corrupt_base = deck_1s.replace("*USER ELEMENT, TYPE=U1", "** REMOVED")
    passed_b, diags_b = audit_assembled_deck(corrupt_base, generate_partition_specification(1))
    assert passed_b is False
    assert any("Base model missing required keyword" in d for d in diags_b)


def test_f1406_research_governance_and_zero_unauthorized_jobs():
    """Verify that zero unauthorized cluster jobs or Abaqus solver runs have occurred."""
    assert os.path.isfile(JOB_LEDGER_PATH), "Job ledger missing: %s" % JOB_LEDGER_PATH

    with open(JOB_LEDGER_PATH, "r") as f:
        ledger_lines = [l.strip() for l in f if l.strip()]

    # Ensure no active/running jobs and no Method B jobs in ledger
    for line in ledger_lines:
        if any(j in line for j in ("M1_PRE_1S", "M1_PRE_2S", "M1_PRE_4S", "M1_MB_FINAL_1S")):
            assert any(tag in line for tag in ("F1408", "F1416")), "Unauthorized job found without authorization tag: %s" % line

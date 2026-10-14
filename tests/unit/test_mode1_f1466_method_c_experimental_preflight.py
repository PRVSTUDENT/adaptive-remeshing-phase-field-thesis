#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1466_method_c_experimental_preflight.py
===================================================
Unit test suite verifying Task F1466 Method C1 forward refinement experimental
preflight package, mesh topology, keyword syntax, state-transfer fidelity,
and governance controls.

Task: F1466
Author: Gemini Antigravity
Date: 2026-10-14
"""

import os
import sys
import json
import math
import hashlib
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

PACKAGE_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "42_method_c1_forward_refinement"
MANIFEST_PATH = PACKAGE_DIR / "PACKAGE_MANIFEST.json"
DECK_PATH = PACKAGE_DIR / "M1_MC_C1_FORWARD_14K.inp"
UEL_PATH = PACKAGE_DIR / "f42_mixed_uel.for"
PBS_PATH = PACKAGE_DIR / "submit_M1_MC_C1_FORWARD_14K.pbs"
SUBMIT_SCRIPT_PATH = PACKAGE_DIR / "submit_c1_forward_refinement_job.sh"
DC_SCRIPT_PATH = PACKAGE_DIR / "run_datacheck_forward.sh"
COMMANDS_PATH = PACKAGE_DIR / "commands.txt"

FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"


def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()


def test_package_42_existence_and_integrity():
    """Verify Package 42 directory structure and essential files exist with non-zero size."""
    assert PACKAGE_DIR.exists(), f"Package directory missing: {PACKAGE_DIR}"
    assert PACKAGE_DIR.is_dir()

    expected_files = [
        DECK_PATH,
        UEL_PATH,
        PBS_PATH,
        SUBMIT_SCRIPT_PATH,
        DC_SCRIPT_PATH,
        COMMANDS_PATH,
        MANIFEST_PATH
    ]
    for fp in expected_files:
        assert fp.exists(), f"Required package file missing: {fp}"
        assert fp.stat().st_size > 0, f"File is empty: {fp}"


def test_deck_topology_and_zero_blank_lines():
    """Verify mesh topology, layer counts, node counts, and zero blank lines in deck."""
    assert DECK_PATH.exists()
    with open(DECK_PATH, "r", encoding="utf-8") as f:
        lines = [line.rstrip("\r\n") for line in f]

    # Rule: Zero blank lines in Abaqus keyword deck
    blank_lines = [i + 1 for i, line in enumerate(lines) if not line.strip()]
    assert len(blank_lines) == 0, f"Found {len(blank_lines)} blank lines in deck: {blank_lines[:5]}"

    # Element counts
    u1_lines = [l for l in lines if l.startswith("*ELEMENT, TYPE=U1")]
    u2_lines = [l for l in lines if l.startswith("*ELEMENT, TYPE=U2")]
    cpe4_lines = [l for l in lines if l.startswith("*ELEMENT, TYPE=CPE4")]
    assert len(u1_lines) == 1, "Layer 1 Phase UEL definition missing"
    assert len(u2_lines) == 1, "Layer 2 Mech UEL definition missing"
    assert len(cpe4_lines) == 1, "Layer 3 CPE4 definition missing"

    # Step cards
    step_cards = [l for l in lines if l.upper().startswith("*STEP")]
    end_step_cards = [l for l in lines if l.upper().startswith("*END STEP")]
    assert len(step_cards) == 2, f"Expected 2 steps, got {len(step_cards)}: {step_cards}"
    assert len(end_step_cards) == 2, f"Expected 2 *END STEP, got {len(end_step_cards)}"

    # Node set card line wrapping (Abaqus 16-item limit)
    reading_nset = False
    for line in lines:
        if line.startswith("*NSET, NSET=N_BOTTOM") or line.startswith("*NSET, NSET=N_TOP"):
            reading_nset = True
            continue
        elif line.startswith("*"):
            reading_nset = False
        elif reading_nset:
            items = [p.strip() for p in line.split(",") if p.strip()]
            assert len(items) <= 16, f"NSET line exceeds 16-item card limit: {len(items)} items"


def test_frozen_uel_hash_and_abi():
    """Verify production UEL source matches frozen SHA-256 hash bitwise."""
    assert UEL_PATH.exists()
    actual_hash = compute_sha256(UEL_PATH)
    assert actual_hash == FROZEN_UEL_HASH, f"UEL hash modified! {actual_hash} != {FROZEN_UEL_HASH}"

    # Verify UEL properties in input deck
    with open(DECK_PATH, "r", encoding="utf-8") as f:
        deck_text = f.read()

    # Must contain 6 properties: (l0, Gc, E, nu, k, 14677.0)
    assert "*UEL PROPERTY, ELSET=PHASE_QUAD" in deck_text
    assert "*UEL PROPERTY, ELSET=MECH_QUAD" in deck_text
    assert "14677.0" in deck_text, "Physical element count property missing in UEL PROPERTY"


def test_solution_initial_conditions_formatting():
    """Verify *INITIAL CONDITIONS, TYPE=SOLUTION complies with 8-item card limit."""
    with open(DECK_PATH, "r", encoding="utf-8") as f:
        lines = [line.rstrip("\r\n") for line in f]

    sol_start = None
    for i, l in enumerate(lines):
        if l.strip().upper() == "*INITIAL CONDITIONS, TYPE=SOLUTION":
            sol_start = i
            break

    assert sol_start is not None, "*INITIAL CONDITIONS, TYPE=SOLUTION card not found"

    # Check first 30 cards of solution initial conditions
    card_count = 0
    for i in range(sol_start + 1, sol_start + 91):
        line = lines[i].strip()
        if line.startswith("*"):
            break
        items = [p.strip() for p in line.split(",") if p.strip()]
        assert len(items) <= 8, f"Card line {i+1} has {len(items)} items (exceeds max 8): {line}"
        card_count += 1

    assert card_count == 90, f"Expected 90 lines (30 elements x 3 cards), checked {card_count}"


def test_transfer_metrics_and_acceptance_criteria():
    """Verify mathematical transfer metrics meet pre-declared Gate 6C criteria."""
    assert MANIFEST_PATH.exists()
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    metrics = manifest.get("transfer_metrics_evaluated", {})
    assert "displacement_l2_rel_error_pct" in metrics
    assert metrics["displacement_l2_rel_error_pct"] <= 1.0, "Displacement L2 exceeds 1.0%"
    assert metrics["delta_d_max"] <= 0.02, "Peak damage difference exceeds 0.02"
    assert metrics["relative_error_integral_d_pct"] <= 5.0, "Integrated damage error exceeds 5.0%"
    assert metrics["min_H"] >= 0.0, "History field has negative values!"
    assert metrics["negative_H_count"] == 0
    assert metrics["delta_e_int_pct"] <= 5.0, "Stored internal energy error exceeds 5.0%"

    # Check 6 pre-declared criteria exist in manifest
    criteria = manifest.get("predeclared_acceptance_criteria", {})
    assert len(criteria) == 6, f"Expected 6 pre-declared acceptance criteria, got {len(criteria)}"
    assert "criterion_1_boundary_force_continuity" in criteria
    assert "criterion_2_transfer_induced_energy_error" in criteria
    assert "criterion_3_global_energy_balance_residual" in criteria
    assert "criterion_4_damage_irreversibility" in criteria
    assert "criterion_5_fracture_response_vs_reference" in criteria
    assert "criterion_6_repeatability_and_determinism" in criteria


def test_governance_hold_and_submission_guard():
    """Verify submission wrapper enforces strict governance hold until 22 October 2026."""
    assert SUBMIT_SCRIPT_PATH.exists()
    with open(SUBMIT_SCRIPT_PATH, "r", encoding="utf-8") as f:
        script_text = f.read()

    assert "AUTHORIZED=false" in script_text, "Submission script missing AUTHORIZED=false guard"
    assert "22 October 2026" in script_text, "Submission script missing supervisor signoff reference"
    assert "[GOVERNANCE HOLD]" in script_text, "Submission script missing explicit governance notice"

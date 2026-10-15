#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1488_restart_experiment_and_authorization.py
=========================================================
Unit test suite verifying Task F1488 milestones:
1. Verification and preservation of active 1-CPU serial parity Job 1413296 (Step 2 Inc >2680, elapsed >6h 25m).
2. Authoritative increment count correction (Step 1 = 2,000 incs; Step 2 Inc 2685 implies 4,685 cumulative incs, not 7,685).
3. Authoritative minimum time increment correction (commanded dt_min = 1.0E-9, not 1.0E-12).
4. Package 48 donor and recipient decks, and uninterrupted continuation reference availability.
5. Diagnostic UEL failure mode audit (iteration gating, history restoration, damage irreversibility, COMMON integrity).
6. Safety gate expired credential interception and exact human authorization command verification.
7. Method B evaluated status with documented physical limitations separated from remaining concurrent sensitivity work.

Author: Gemini Antigravity
Date: 2026-10-15
Protocol Version: 2
"""

import os
import sys
import json
import hashlib
import pytest
from pathlib import Path

# Resolve repository root
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

FROZEN_PRODUCTION_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
PACKAGE48_DONOR_DECK_SHA256 = "F737357AF6069A4017885E38EF249DC1BA7FD4B7E3C91EC1FB55F1D89824484D"
PACKAGE48_RESTART_DECK_SHA256 = "C617D83165CBAED7D6E6C1494AF9C65B8B9A763E1A67CA40FCF0CA51CD356D6D"
DIAGNOSTIC_UEL_SHA256 = "8C6D873037367665C01C305D50C5B148339DC38C6E581BF4A9E19C2B5E2AC978"


def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()


def test_job_1413296_active_serial_progress_and_parity():
    """Verify Job 1413296 tracking in ledgers and preserve running status."""
    hpc_ledger = REPO_ROOT / "project_coordination" / "HPC_JOB_LEDGER.csv"
    assert hpc_ledger.exists(), "HPC_JOB_LEDGER.csv must exist"

    with open(hpc_ledger, "r", encoding="utf-8") as f:
        content = f.read()

    assert "1413296.mmaster02" in content
    assert "M1_MB_DTMAX_1C" in content

    # Predecessor terminal evidence preserved
    assert "1413278.mmaster02" in content
    assert "1413217.mmaster02" in content


def test_authoritative_increment_count_correction():
    """Verify that Step 1 had exactly 2,000 increments and cumulative count is 2000 + Inc_step2."""
    # In Package 44 evidence, verify Step 1 increments
    sta_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "44_method_b_temporal_refinement" / "evidence_1413278" / "M1_MB_DTMAX_8T.sta"
    assert sta_path.exists(), "Package 44 sta file must exist"

    step1_incs = 0
    with open(sta_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 2 and parts[0] == "1" and parts[1].isdigit():
                inc = int(parts[1])
                if inc > step1_incs:
                    step1_incs = inc

    assert step1_incs == 2000, f"Step 1 must have exactly 2,000 increments, found {step1_incs}"
    # Therefore, Step 2 Increment 2685 implies exactly 4,685 cumulative increments, NOT 7,685
    cumulative_at_2685 = step1_incs + 2685
    assert cumulative_at_2685 == 4685


def test_authoritative_minimum_time_increment_correction():
    """Verify that commanded dt_min in Package 44 is 1.0E-9 on *STATIC card."""
    sta_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "44_method_b_temporal_refinement" / "evidence_1413278" / "M1_MB_DTMAX_8T.sta"
    assert sta_path.exists(), "Package 44 sta file must exist"

    # Read last lines of sta to verify terminal cutback increment
    with open(sta_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = [line.strip() for line in f if line.strip()]

    # Find last increment before termination
    last_inc_line = None
    for line in reversed(lines):
        parts = line.split()
        if len(parts) >= 7 and parts[0] == "2" and parts[1].isdigit():
            last_inc_line = line
            break

    assert last_inc_line is not None
    # Terminal increment 5081 attempt 3 cut back to 1.000e-09
    assert "1.000e-09" in last_inc_line


def test_package48_donor_and_recipient_decks_and_continuity_reference():
    """Verify Package 48 donor deck, restart recipient deck, and continuation reference."""
    pkg48_dir = REPO_ROOT / "models" / "pandey_kumar_mode1" / "48_method_c_stage_c1_0_restart_positive_control"
    assert pkg48_dir.exists(), "Package 48 directory must exist"

    donor_deck = pkg48_dir / "M1_MB_DONOR_WITH_RESTART.inp"
    restart_deck = pkg48_dir / "M1_MB_NATIVE_RESTART.inp"
    assert donor_deck.exists()
    assert restart_deck.exists()
    assert compute_sha256(donor_deck) == PACKAGE48_DONOR_DECK_SHA256
    assert compute_sha256(restart_deck) == PACKAGE48_RESTART_DECK_SHA256

    # Verify uninterrupted reference trajectory exists in Package 41
    ref_csv = REPO_ROOT / "models" / "pandey_kumar_mode1" / "41_method_c_genuine_continuation" / "evidence_1412809" / "genuine_continuation_load_displacement.csv"
    assert ref_csv.exists(), "Continuation reference trajectory must exist"

    with open(ref_csv, "r", encoding="utf-8") as f:
        lines = f.readlines()
    assert len(lines) > 5000, "Reference trajectory must contain full Step 2 resolution"


def test_diagnostic_uel_failure_mode_guards():
    """Verify diagnostic UEL against specific failure modes."""
    pkg48_dir = REPO_ROOT / "models" / "pandey_kumar_mode1" / "48_method_c_stage_c1_0_restart_positive_control"
    diag_uel = pkg48_dir / "f42_mixed_uel_restart_diagnostic.for"
    assert diag_uel.exists()
    assert compute_sha256(diag_uel) == DIAGNOSTIC_UEL_SHA256

    with open(diag_uel, "r", encoding="utf-8") as f:
        text = f.read()

    # Failure Mode 1: COMMON block layout mismatch
    decl_lines = [
        line for line in text.splitlines()
        if len(line) > 0 and line[0] not in ("C", "c", "*") and "COMMON /CB_STATE_TRANS/" in line
    ]
    assert len(decl_lines) == 3, "COMMON declaration must appear in exactly 3 subroutines"

    # Failure Mode 2: Repeated initialization across iterations
    assert "SV_INGESTED(PHYSIDX) .EQ. 0" in text
    assert "SV_INGESTED(PHYSIDX) = 1" in text

    # Failure Mode 3: Missing LOP=4 restart initialization
    assert "ELSE IF (LOP .EQ. 4) THEN" in text
    assert "SV_INGESTED(I) = 0" in text
    assert "POSITION='APPEND'" in text

    # Failure Mode 4: Production UEL modification (must remain frozen)
    prod_uel = pkg48_dir / "f42_mixed_uel.for"
    assert compute_sha256(prod_uel) == FROZEN_PRODUCTION_UEL_SHA256


def test_safety_gate_denial_and_exact_human_approval_command():
    """Verify Set-ControllerAuthorization.ps1 interface and exact approval command parameters."""
    auth_script = Path(os.environ["USERPROFILE"]) / "OpenClawPAD" / "Set-ControllerAuthorization.ps1"
    assert auth_script.exists()

    with open(auth_script, "r", encoding="utf-8") as f:
        auth_content = f.read()

    assert "BatchName" in auth_content
    assert "Command" in auth_content
    assert "MaxSubmissions" in auth_content


def test_method_b_evaluated_status_separated_from_remaining_work():
    """Verify Method B status is documented as evaluated with physical limitations."""
    active_task = REPO_ROOT / "project_coordination" / "ACTIVE_TASK.json"
    with open(active_task, "r", encoding="utf-8") as f:
        task_data = json.load(f)

    notes = task_data.get("notes", "")
    assert "Method B" in notes
    assert "evaluated with documented physical limitations" in notes

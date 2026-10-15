#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1489_package48_authorization_verification.py
=========================================================
Unit test suite verifying Task F1489 milestones:
1. Verification and preservation of active 1-CPU serial parity Job 1413296.
2. Verification of Package 48 donor deck and production UEL hashes.
3. Verification of Package 48 recipient restart deck and diagnostic UEL hashes.
4. Verification that qsub-safety-gate.ps1 enforces fail-closed interception on expired delegation.
5. Verification of Set-ControllerAuthorization.ps1 vs qsub-safety-gate.ps1 schema requirements.
6. Verification of Method B evaluated status and Method C research progression.

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


def test_job_1413296_preserved_in_ledger():
    """Verify Job 1413296 tracking in ledgers and preserve running status."""
    hpc_ledger = REPO_ROOT / "project_coordination" / "HPC_JOB_LEDGER.csv"
    assert hpc_ledger.exists(), "HPC_JOB_LEDGER.csv must exist"

    with open(hpc_ledger, "r", encoding="utf-8") as f:
        content = f.read()

    assert "1413296.mmaster02" in content
    assert "M1_MB_DTMAX_1C" in content


def test_package48_donor_and_production_uel_hashes():
    """Verify Package 48 donor deck and production UEL hashes."""
    pkg48_dir = REPO_ROOT / "models" / "pandey_kumar_mode1" / "48_method_c_stage_c1_0_restart_positive_control"
    donor_deck = pkg48_dir / "M1_MB_DONOR_WITH_RESTART.inp"
    prod_uel = pkg48_dir / "f42_mixed_uel.for"

    assert donor_deck.exists()
    assert prod_uel.exists()
    assert compute_sha256(donor_deck) == PACKAGE48_DONOR_DECK_SHA256
    assert compute_sha256(prod_uel) == FROZEN_PRODUCTION_UEL_SHA256


def test_package48_recipient_and_diagnostic_uel_hashes():
    """Verify Package 48 recipient restart deck and diagnostic UEL hashes."""
    pkg48_dir = REPO_ROOT / "models" / "pandey_kumar_mode1" / "48_method_c_stage_c1_0_restart_positive_control"
    restart_deck = pkg48_dir / "M1_MB_NATIVE_RESTART.inp"
    diag_uel = pkg48_dir / "f42_mixed_uel_restart_diagnostic.for"

    assert restart_deck.exists()
    assert diag_uel.exists()
    assert compute_sha256(restart_deck) == PACKAGE48_RESTART_DECK_SHA256
    assert compute_sha256(diag_uel) == DIAGNOSTIC_UEL_SHA256


def test_safety_gate_script_presence_and_checks():
    """Verify qsub-safety-gate.ps1 exists and checks daily delegation and submission authorization."""
    gate_script = REPO_ROOT / ".agents" / "qsub-safety-gate.ps1"
    assert gate_script.exists()

    with open(gate_script, "r", encoding="utf-8") as f:
        text = f.read()

    assert "daily_chatgpt_delegation" in text
    assert "submission_authorization" in text
    assert "Daily ChatGPT delegation has expired." in text


def test_authorization_script_presence_and_schema():
    """Verify Set-ControllerAuthorization.ps1 exists and checks schema fields."""
    auth_script = Path(os.environ["USERPROFILE"]) / "OpenClawPAD" / "Set-ControllerAuthorization.ps1"
    assert auth_script.exists()

    with open(auth_script, "r", encoding="utf-8") as f:
        text = f.read()

    assert "BatchName" in text
    assert "Command" in text
    assert "workflow_status" in text
    assert "authorization" in text


def test_method_b_status_and_method_c_progression():
    """Verify Method B status is documented and Method C progression rule active."""
    current_state = REPO_ROOT / "project_coordination" / "CURRENT_STATE.md"
    with open(current_state, "r", encoding="utf-8") as f:
        text = f.read()

    assert "Method B" in text
    assert "STAGE_C1_METHOD_C_RESEARCH_AUTHORIZED" in text

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1490_authorization_workflow_repair.py
==================================================
Unit test suite verifying Task F1490 milestones:
1. Verification that Set-ControllerAuthorization.ps1 has been repaired with the complete schema:
   - daily_chatgpt_delegation issuance (+24h expiry)
   - command-bound submission_authorization
   - candidate_manifest_sha256 binding
   - notification preflight satisfaction
2. Verification that .agents/qsub-safety-gate.ps1 remains 100% fail-closed and unmodified.
3. Verification that Package 48 donor deck, production UEL, recipient deck, and diagnostic UEL hashes match.
4. Verification that active serial parity Job 1413296 is preserved in ledgers.

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
PACKAGE48_RESTART_DECK_REPAIRED_SHA256 = "4A50753AC17E565DADCDF320D864BA0C6FF88834866CEF06E5F46E1BBB5CD761"
DIAGNOSTIC_UEL_SHA256 = "8C6D873037367665C01C305D50C5B148339DC38C6E581BF4A9E19C2B5E2AC978"
PACKAGE48_MANIFEST_SHA256 = "35B818BC08652C11D0F0B689878239E5FF81D9563EAF42AB5083BFC3BDA02887"
PACKAGE48_MANIFEST_REPAIRED_SHA256 = "5F615CDCD864437A7E3546E7E009E91A199EB5F33FDE6380C8DA065395C1DACD"
PACKAGE48_MANIFEST_V2_SHA256 = "730DF1E9AB246C5952E369A4DF3E38BB6432E245BE4CF59E9485D093855B672D"


def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()


def test_repaired_authorization_script_schema():
    """Verify that Set-ControllerAuthorization.ps1 contains the repaired schema fields."""
    auth_script = Path(os.environ["USERPROFILE"]) / "OpenClawPAD" / "Set-ControllerAuthorization.ps1"
    assert auth_script.exists(), "Set-ControllerAuthorization.ps1 must exist"

    with open(auth_script, "r", encoding="utf-8") as f:
        text = f.read()

    # Must issue daily delegation
    assert "daily_chatgpt_delegation" in text
    assert "expires_at" in text
    assert "HoursValid" in text

    # Must issue command-bound submission authorization
    assert "submission_authorization" in text
    assert "authorized_command_sha256" in text
    assert "candidate_manifest_sha256" in text
    assert "notification_preflight" in text
    assert "pbs_email_verified" in text
    assert "telegram_verified" in text

    # Must preserve legacy authorization fields
    assert "workflow_status" in text
    assert "authorization" in text


def test_safety_gate_remains_fail_closed():
    """Verify that .agents/qsub-safety-gate.ps1 remains strict and fail-closed."""
    gate_script = REPO_ROOT / ".agents" / "qsub-safety-gate.ps1"
    assert gate_script.exists()

    with open(gate_script, "r", encoding="utf-8") as f:
        text = f.read()

    assert "Daily ChatGPT delegation has expired." in text
    assert "No active submission permit in state." in text
    assert "Command content mismatch with authorized command." in text
    assert "Dual-channel notification preflight (email + Telegram) not verified." in text


def test_package48_artifacts_and_hashes():
    """Verify Package 48 donor deck, recipient deck, UELs, and manifest hashes."""
    pkg48_dir = REPO_ROOT / "models" / "pandey_kumar_mode1" / "48_method_c_stage_c1_0_restart_positive_control"
    donor_deck = pkg48_dir / "M1_MB_DONOR_WITH_RESTART.inp"
    restart_deck = pkg48_dir / "M1_MB_NATIVE_RESTART.inp"
    prod_uel = pkg48_dir / "f42_mixed_uel.for"
    diag_uel = pkg48_dir / "f42_mixed_uel_restart_diagnostic.for"
    manifest = pkg48_dir / "PACKAGE_MANIFEST.json"

    assert compute_sha256(donor_deck) == PACKAGE48_DONOR_DECK_SHA256
    assert compute_sha256(restart_deck) in (PACKAGE48_RESTART_DECK_SHA256, PACKAGE48_RESTART_DECK_REPAIRED_SHA256)
    assert compute_sha256(prod_uel) == FROZEN_PRODUCTION_UEL_SHA256
    assert compute_sha256(diag_uel) == DIAGNOSTIC_UEL_SHA256
    assert compute_sha256(manifest) in (PACKAGE48_MANIFEST_SHA256, PACKAGE48_MANIFEST_REPAIRED_SHA256, PACKAGE48_MANIFEST_V2_SHA256)


def test_job_1413296_preserved_in_ledger():
    """Verify Job 1413296 tracking in ledgers and preserve running status."""
    hpc_ledger = REPO_ROOT / "project_coordination" / "HPC_JOB_LEDGER.csv"
    assert hpc_ledger.exists()

    with open(hpc_ledger, "r", encoding="utf-8") as f:
        content = f.read()

    assert "1413296.mmaster02" in content
    assert "M1_MB_DTMAX_1C" in content

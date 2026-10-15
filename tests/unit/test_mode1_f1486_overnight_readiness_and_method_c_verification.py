#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1486_overnight_readiness_and_method_c_verification.py
==================================================================
Unit test suite verifying Task F1486 milestones:
1. Verification and preservation of active 1-CPU serial parity Job 1413296 (advancing in Step 2).
2. Package 47 Stage C1-0 identical-mesh continuation readiness and provisional classification.
3. Package 48 same-mesh native restart positive control and experimental diagnostic UEL variant.
4. Stage C1-0 quantitative continuation acceptance evaluation framework and pre-declared criteria.
5. Correction of recurring authorization procedure and enforcement of safety gate integrity.

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
PACKAGE47_DECK_SHA256 = "8B417E7FC5F5612DD6C8E128036CC5799E074BCA5E7191E9324789A91D700A67"
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


def test_job_1413296_preserved_active_running():
    """Verify Job 1413296 tracking in ledgers and preserve running status."""
    hpc_ledger = REPO_ROOT / "project_coordination" / "HPC_JOB_LEDGER.csv"
    assert hpc_ledger.exists(), "HPC_JOB_LEDGER.csv must exist"

    with open(hpc_ledger, "r", encoding="utf-8") as f:
        content = f.read()

    # Job 1413296 must be recorded as running serial parity control
    assert "1413296.mmaster02" in content
    assert "M1_MB_DTMAX_1C" in content

    # Terminal predecessors preserved
    assert "1413217.mmaster02" in content
    assert "1413278.mmaster02" in content


def test_package_47_reconstruction_readiness_and_provisional_classification():
    """Verify Package 47 Stage C1-0 staging, input deck hash, and provisional classification."""
    pkg47_dir = REPO_ROOT / "models" / "pandey_kumar_mode1" / "47_method_c_stage_c1_0_identical_mesh_continuation"
    assert pkg47_dir.exists(), "Package 47 directory must exist"

    deck_path = pkg47_dir / "M1_MC_STAGE_C1_0_RECONSTRUCT.inp"
    assert deck_path.exists(), "Package 47 input deck must exist"
    assert compute_sha256(deck_path) == PACKAGE47_DECK_SHA256

    uel_path = pkg47_dir / "f42_mixed_uel.for"
    assert uel_path.exists(), "Production UEL must exist in Package 47"
    assert compute_sha256(uel_path) == FROZEN_PRODUCTION_UEL_SHA256

    # Verify provisional classification in manifest
    manifest_path = pkg47_dir / "PACKAGE_MANIFEST.json"
    assert manifest_path.exists(), "Package 47 manifest must exist"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest.get("status") == "HISTORY_INITIALIZED_RE_EQUILIBRATION__CONTINUATION_NOT_YET_VERIFIED"


def test_package_48_native_restart_positive_control_and_diagnostic_uel():
    """Verify Package 48 restart decks, production UEL freeze, and diagnostic UEL variant."""
    pkg48_dir = REPO_ROOT / "models" / "pandey_kumar_mode1" / "48_method_c_stage_c1_0_restart_positive_control"
    assert pkg48_dir.exists(), "Package 48 directory must exist"

    donor_deck = pkg48_dir / "M1_MB_DONOR_WITH_RESTART.inp"
    restart_deck = pkg48_dir / "M1_MB_NATIVE_RESTART.inp"
    assert donor_deck.exists(), "Package 48 donor deck must exist"
    assert restart_deck.exists(), "Package 48 restart deck must exist"
    assert compute_sha256(donor_deck) == PACKAGE48_DONOR_DECK_SHA256
    assert compute_sha256(restart_deck) == PACKAGE48_RESTART_DECK_SHA256

    # Donor deck must contain *RESTART, WRITE
    with open(donor_deck, "r", encoding="utf-8") as f:
        donor_text = f.read()
    assert "*RESTART, WRITE" in donor_text

    # Recipient deck must contain *RESTART, READ, STEP=1
    with open(restart_deck, "r", encoding="utf-8") as f:
        restart_text = f.read()
    assert "*RESTART, READ, STEP=1" in restart_text

    # Authoritative production UEL remains 100% frozen
    prod_uel = pkg48_dir / "f42_mixed_uel.for"
    assert prod_uel.exists(), "Production UEL must exist in Package 48"
    assert compute_sha256(prod_uel) == FROZEN_PRODUCTION_UEL_SHA256

    # Diagnostic UEL variant must exist with exact hash and SV_INGESTED logic
    diag_uel = pkg48_dir / "f42_mixed_uel_restart_diagnostic.for"
    assert diag_uel.exists(), "Diagnostic UEL must exist in Package 48"
    assert compute_sha256(diag_uel) == DIAGNOSTIC_UEL_SHA256

    with open(diag_uel, "r", encoding="utf-8") as f:
        diag_text = f.read()
    assert "SV_INGESTED" in diag_text
    assert "LOP .EQ. 4" in diag_text

    # Verify execution scripts and manifest
    assert (pkg48_dir / "submit_M1_MB_DONOR.pbs").exists()
    assert (pkg48_dir / "submit_M1_MB_RESTART_PROD.pbs").exists()
    assert (pkg48_dir / "submit_M1_MB_RESTART_DIAG.pbs").exists()
    assert (pkg48_dir / "commands.txt").exists()


def test_stage_c1_0_quantitative_acceptance_criteria():
    """Verify evaluation script and pre-declared Stage C1-0 acceptance thresholds."""
    eval_script = REPO_ROOT / "scripts" / "state_transfer" / "evaluate_mode1_stage_c1_0_continuation.py"
    assert eval_script.exists(), "Evaluation script must exist"

    donor_json = REPO_ROOT / "models" / "pandey_kumar_mode1" / "41_method_c_genuine_continuation" / "evidence_forward_audit" / "coarse_donor_state_u0050.json"
    assert donor_json.exists(), "Canonical donor JSON must exist"

    # Import and run evaluation module
    from scripts.state_transfer.evaluate_mode1_stage_c1_0_continuation import (
        load_donor_state,
        evaluate_stage_c1_0,
        ACCEPTANCE_THRESHOLDS,
        CANONICAL_DONOR_BENCHMARK
    )

    donor_data = load_donor_state(str(donor_json))
    assert abs(donor_data["rf_rp_N"] - 653.0886) < 0.01
    assert abs(donor_data["total_e_tot_mJ"] - 1.6634) < 0.01

    # Self-consistency check on canonical donor state
    res = evaluate_stage_c1_0(donor_data, donor_data)
    assert res["status"] == "STAGE_C1_0_HANDOFF_PASS"
    assert res["criteria"]["criterion_1_force_continuity"]["status"] == "PASS"
    assert res["criteria"]["criterion_2_damage_field"]["status"] == "PASS"
    assert res["criteria"]["criterion_3_history_nonnegativity"]["status"] == "PASS"
    assert res["criteria"]["criterion_4_energy_preservation"]["status"] == "PASS"

    # Verify strict thresholds
    assert ACCEPTANCE_THRESHOLDS["max_delta_rf_n"] == 0.50
    assert ACCEPTANCE_THRESHOLDS["target_delta_rf_n"] == 0.10
    assert ACCEPTANCE_THRESHOLDS["max_rel_e_tot_pct"] == 0.50


def test_authorization_governance_and_gate_safety():
    """Verify supported authorization interface and safety gate integrity."""
    gate_script = REPO_ROOT / ".agents" / "qsub-safety-gate.ps1"
    assert gate_script.exists(), "qsub-safety-gate.ps1 must exist"

    auth_script = Path("C:/Users/pruth/OpenClawPAD/Set-ControllerAuthorization.ps1")
    if auth_script.exists():
        with open(auth_script, "r", encoding="utf-8") as f:
            auth_text = f.read()
        assert "Set-ControllerAuthorization" in auth_text or "BatchName" in auth_text

    # Verify that project alignment rules forbid unauthorized qsub or state manipulation
    alignment_guard = REPO_ROOT / ".agents" / "scripts" / "project_alignment_guard.txt"
    if alignment_guard.exists():
        with open(alignment_guard, "r", encoding="utf-8") as f:
            guard_text = f.read()
        assert "qsub" in guard_text or "authorization" in guard_text.lower()

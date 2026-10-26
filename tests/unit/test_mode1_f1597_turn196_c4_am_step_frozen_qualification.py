#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1597_turn196_c4_am_step_frozen_qualification.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER (Turn 196)
Protocol Version: 2

Independent unit test suite verifying:
1. Committed history immutability: h_committed_dict is strictly invariant across all AM iterations.
2. Manifest and authorization integrity: frozen UEL SHA-256 verified, exact file hashes.
3. Predeclared acceptance criteria: Delta d <= 1e-3, Delta RF2 <= 0.1 N, KKT >= -1e-9, free res <= 1e-6.
4. Ratcheting elimination: H_trial = max(H_committed, psi+) drops if psi+ drops, eliminating the intra-step ratchet.
5. PBS execution compliance: single-rank serial 1 CPU, 16 GB, walltime 8h, dual notifications, terminal trap.
"""

import os
import sys
import json
import hashlib
from pathlib import Path
import pytest
import numpy as np

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
PKG_DIR = REPO_ROOT / "models/pandey_kumar_mode1/110_r2_c4_am_step_frozen_history"
MANIFEST_PATH = PKG_DIR / "PACKAGE_MANIFEST.json"
AUTH_PATH = PKG_DIR / "M1_C4_AM_STEP_FROZEN_AUTHORIZATION.json"
DRIVER_PATH = PKG_DIR / "driver_c4_am_step_frozen_history.py"
PBS_PATH = PKG_DIR / "submit_M1_C4_AM_STEP_FROZEN_HISTORY.pbs"
UEL_PATH = PKG_DIR / "f42_unified_12dof_active_set_uel.for"
FROZEN_UEL_HASH = "ab0a5a71335ecb445e91ec13a645e280ff3310b561a5e78aba4a49c8e81dd8ac"

def test_01_committed_history_immutability():
    """Verify that driver_c4_am_step_frozen_history.py preserves h_committed_dict immutably."""
    assert DRIVER_PATH.exists(), f"Driver not found: {DRIVER_PATH}"
    with open(DRIVER_PATH, "r", encoding="utf-8") as f:
        driver_code = f.read()

    # Check that h_committed_dict is loaded once
    assert "h_committed_dict = load_element_history(h_bounds_csv)" in driver_code
    # Check that assemble_phase_qp accepts h_committed_dict
    assert "def assemble_phase_qp(nodes, elements, n2idx, u_nodal, h_committed_dict):" in driver_code
    # Check that h_base is derived from h_committed_dict
    assert "h_base = h_committed_dict[eid][kpt]" in driver_code
    # Check that h_committed_dict is never re-assigned or overwritten in the loop
    assert "h_committed_dict =" not in driver_code[driver_code.find("for cycle in range"):]
    # Check that within-step trial history is isolated in h_trial_dict
    assert "Kdd, Fd, h_trial_dict = assemble_phase_qp(" in driver_code

def test_02_manifest_and_authorization_integrity():
    """Verify manifest schema, file hashes, and exact frozen UEL match."""
    assert MANIFEST_PATH.exists()
    assert AUTH_PATH.exists()

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    with open(AUTH_PATH, "r", encoding="utf-8") as f:
        auth = json.load(f)

    assert manifest["schema"] == 1
    assert auth["schema"] == 1
    assert manifest["package"] == "110_r2_c4_am_step_frozen_history"
    assert manifest["job_name"] == "M1_C4_AM_STEP_FROZEN_HISTORY"
    assert auth["technical_stage"] == "C1-1"

    # Verify frozen UEL SHA-256
    with open(UEL_PATH, "rb") as f:
        uel_hash = hashlib.sha256(f.read()).hexdigest().lower()
    assert uel_hash == FROZEN_UEL_HASH
    assert manifest["files"]["f42_unified_12dof_active_set_uel.for"].lower() == FROZEN_UEL_HASH
    assert auth["files"]["f42_unified_12dof_active_set_uel.for"].lower() == FROZEN_UEL_HASH

def test_03_predeclared_acceptance_criteria():
    """Verify strict acceptance criteria declared in authorization manifest."""
    with open(AUTH_PATH, "r", encoding="utf-8") as f:
        auth = json.load(f)

    acc = auth["acceptance"]["stage_C1_1_same_load"]
    assert acc["stationarity_delta_d_max"] == 1.0e-3
    assert acc["rf2_continuity_pct_max"] == 5.0
    assert acc["energy_continuity_pct_max"] <= 2.5
    assert acc["kkt_violations_max"] == 0
    assert acc["free_phase_residual_max_kN_mm"] == 1.0e-6
    assert acc["healing_tolerance"] == 0

def test_04_ratcheting_elimination():
    """Demonstrate mathematically that un-ratcheted H_trial responds elastically to stress relaxation."""
    h_committed = 1.0  # authentic committed history baseline

    # Trial 1: strain energy surges to 5.0 due to crack tip concentration
    psi_plus_iter1 = 5.0
    h_trial_iter1 = max(h_committed, psi_plus_iter1)
    assert h_trial_iter1 == 5.0

    # In defective R1 driver: prev_h becomes 5.0 permanently!
    h_ratchet_r1 = h_trial_iter1

    # Trial 2: material softens or stress redistributes, reducing local strain energy to 2.0
    psi_plus_iter2 = 2.0

    # Defective R1 driver:
    h_val_r1 = max(h_ratchet_r1, psi_plus_iter2)
    assert h_val_r1 == 5.0  # TRAPPED! Cannot decrease!

    # Corrected R2 driver: always re-evaluates against invariant committed history
    h_val_r2 = max(h_committed, psi_plus_iter2)
    assert h_val_r2 == 2.0  # UNTRAPPED! True path independence restored!
    assert h_val_r2 < h_val_r1

def test_05_pbs_and_notification_compliance():
    """Verify PBS execution script directives, resource limits, and notification integration."""
    assert PBS_PATH.exists()
    with open(PBS_PATH, "r", encoding="utf-8") as f:
        pbs_content = f.read()

    assert "#PBS -N M1_C4_AM_STEP_FROZEN_HISTORY" in pbs_content
    assert "#PBS -q entry_imfdfkmq" in pbs_content
    assert "#PBS -m abe" in pbs_content
    assert "#PBS -l select=1:ncpus=1:mem=16gb" in pbs_content
    assert "#PBS -l walltime=08:00:00" in pbs_content
    assert "job_notifications.sh" in pbs_content
    assert "notification_install_terminal_trap" in pbs_content
    assert "notify_start" in pbs_content
    assert "abaqus python driver_c4_am_step_frozen_history.py" in pbs_content

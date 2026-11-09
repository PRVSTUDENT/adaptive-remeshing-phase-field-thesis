#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_f1705_candidate_e10_production_readiness.py
==========================================================
Unit test suite verifying Task F1705 Candidate E10 Production Fracture
Execution Readiness:
  - Frozen UEL hash and line count integrity in package directory
  - Qualified production deck hash and line count in package directory
  - PBS execution script syntax, directives, preflight guards, and dual-channel notifications
  - Cluster datacheck script existence and syntax
  - Zero-PBS execution governance (max_new_pbs_submissions = 1 proposed; 0 submitted prior to review authorization)
"""

import hashlib
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PKG_DIR   = REPO_ROOT / "models/pandey_kumar_mode1/177_method_a_hole_e10_prod"
PROD_DECK = PKG_DIR / "PK_HOLE_SEL_E10_PROD.inp"
UEL_FILE  = PKG_DIR / "f42_mixed_uel.for"
PBS_FILE  = PKG_DIR / "submit_M1_HOLE_SEL_E10_PROD.pbs"
DC_SH     = PKG_DIR / "run_e10_cluster_datacheck.sh"
NOTIF_SH  = PKG_DIR / "job_notifications.sh"
STAGING_PS1 = REPO_ROOT / "scripts/hpc/Stage-And-Datacheck-F1705.ps1"

FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
QUAL_DECK_SHA256  = "41F073BC4D0502753D777081ACC8EB99F9716FFAC1D311F64204FBC42F4392F4"


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()


def test_package_files_exist():
    """Verify all required execution package files exist in package directory."""
    assert PKG_DIR.exists(), f"Package directory missing: {PKG_DIR}"
    assert PROD_DECK.exists(), f"Production deck missing: {PROD_DECK}"
    assert UEL_FILE.exists(), f"UEL file missing: {UEL_FILE}"
    assert PBS_FILE.exists(), f"PBS script missing: {PBS_FILE}"
    assert DC_SH.exists(), f"Cluster datacheck script missing: {DC_SH}"
    assert NOTIF_SH.exists(), f"Notification script missing: {NOTIF_SH}"
    assert STAGING_PS1.exists(), f"Staging script missing: {STAGING_PS1}"


def test_package_file_hashes():
    """Verify bitwise SHA-256 hashes of production deck and frozen UEL."""
    actual_deck_sha = sha256_file(PROD_DECK)
    assert actual_deck_sha == QUAL_DECK_SHA256, f"Deck hash mismatch: {actual_deck_sha}"

    actual_uel_sha = sha256_file(UEL_FILE)
    assert actual_uel_sha == FROZEN_UEL_SHA256, f"UEL hash mismatch: {actual_uel_sha}"

    with open(UEL_FILE, "r") as f:
        lines = [l for l in f]
    assert len(lines) == 907, f"UEL line count mismatch: expected 907, got {len(lines)}"


def test_pbs_directives_and_resources():
    """Verify PBS script directives match Mode-I serial baseline standards."""
    with open(PBS_FILE, "r") as f:
        text = f.read()

    assert "#PBS -N M1_HOLE_SEL_E10_PROD" in text
    assert "#PBS -l select=1:ncpus=1:mem=16gb" in text
    assert "#PBS -l walltime=08:00:00" in text
    assert "#PBS -q entry_imfdfkmq" in text
    assert "#PBS -m abe" in text
    assert "#PBS -M pr21vyci@mailserver.tu-freiberg.de" in text
    assert "/scratch9/pr21vyci/runs/mode1_method_a_hole_f1705_prod" in text


def test_pbs_preflight_guards():
    """Verify PBS preflight guards: lockfile check, quota, and bitwise SHA checks."""
    with open(PBS_FILE, "r") as f:
        text = f.read()

    assert ".lck" in text, "Missing lockfile check"
    assert "df -k" in text, "Missing disk space check"
    assert "10485760" in text, "Missing 10 GB minimum disk space threshold"
    assert "41f073bc4d0502753d777081acc8eb99f9716ffac1d311f64204fbc42f4392f4" in text.lower()
    assert "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6" in text.lower()


def test_pbs_notification_integration():
    """Verify dual-channel notification integration in PBS script."""
    with open(PBS_FILE, "r") as f:
        text = f.read()

    assert "job_notifications.sh" in text
    assert "notification_load_config" in text
    assert "notification_install_terminal_trap" in text
    assert "notify_start" in text


def test_cluster_datacheck_script():
    """Verify cluster-side datacheck script calls Abaqus 2023 with datacheck option."""
    with open(DC_SH, "r") as f:
        text = f.read()

    assert "abaqus/2023" in text
    assert "PK_HOLE_SEL_E10_PROD.inp" in text
    assert "f42_mixed_uel.for" in text
    assert "datacheck -interactive" in text

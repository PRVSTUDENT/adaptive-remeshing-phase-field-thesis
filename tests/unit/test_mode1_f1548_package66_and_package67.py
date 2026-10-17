#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for Task F1548: Package 66 Uninterrupted Control & Package 67 Fine dt Diagnostic.
"""

import json
import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PKG66_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "66_method_c_propagation_uninterrupted_control"
PKG67_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "67_method_c_propagation_stage2_fine_dt"
FROZEN_UEL_SHA = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"

def test_frozen_uel_integrity():
    for pkg_dir, pkg_name in [(PKG66_DIR, "Package 66"), (PKG67_DIR, "Package 67")]:
        uel_path = pkg_dir / "f42_mixed_uel.for"
        assert uel_path.is_file(), f"f42_mixed_uel.for missing from {pkg_name}"
        actual_sha = hashlib.sha256(uel_path.read_bytes()).hexdigest().lower()
        assert actual_sha == FROZEN_UEL_SHA, f"Frozen UEL hash mismatch in {pkg_name}: {actual_sha}"

def test_package66_manifest_and_hashes():
    auth_path = PKG66_DIR / "METHOD_C_PROP_CTRL_29K_AUTHORIZATION.json"
    assert auth_path.is_file(), "Package 66 authorization manifest missing"
    with open(auth_path, "r", encoding="utf-8") as f:
        auth = json.load(f)
    assert auth["adapter"] == "mode1-qualified-batch-v2"
    assert auth["batch_name"] == "MODE1_METHOD_C_PROP_CTRL_29K"
    assert auth["scientific_scope"] == "MODE1"
    assert auth["technical_stage"] == "C1-2"
    assert auth["max_submissions"] == 1
    assert auth["automatic_retry"] is False

    for fname, expected_hash in auth["files"].items():
        fpath = PKG66_DIR / fname
        assert fpath.is_file(), f"Package 66 file missing on disk: {fname}"
        actual_hash = hashlib.sha256(fpath.read_bytes()).hexdigest().lower()
        assert actual_hash == expected_hash, f"Hash mismatch for {fname}: {actual_hash} vs {expected_hash}"

def test_package67_manifest_and_hashes():
    auth_path = PKG67_DIR / "METHOD_C_PROP_S2_FINE_DT_AUTHORIZATION.json"
    assert auth_path.is_file(), "Package 67 authorization manifest missing"
    with open(auth_path, "r", encoding="utf-8") as f:
        auth = json.load(f)
    assert auth["adapter"] == "mode1-qualified-batch-v2"
    assert auth["batch_name"] == "MODE1_METHOD_C_PROP_S2_FINE_DT"
    assert auth["scientific_scope"] == "MODE1"
    assert auth["technical_stage"] == "C1-2"
    assert auth["max_submissions"] == 1
    assert auth["automatic_retry"] is False

    for fname, expected_hash in auth["files"].items():
        fpath = PKG67_DIR / fname
        assert fpath.is_file(), f"Package 67 file missing on disk: {fname}"
        actual_hash = hashlib.sha256(fpath.read_bytes()).hexdigest().lower()
        assert actual_hash == expected_hash, f"Hash mismatch for {fname}: {actual_hash} vs {expected_hash}"

def test_package66_deck_structure():
    inp_path = PKG66_DIR / "M1_MC_PROP_CTRL_29K.inp"
    assert inp_path.is_file(), "Package 66 input deck missing"
    text = inp_path.read_text(encoding="utf-8")
    assert "*STEP, NAME=Step-1-To-u0010" in text
    assert "*STEP, NAME=Step-2-To-u0018" in text
    assert "*STEP, NAME=Step-3-To-u0021" in text
    assert "*STEP, NAME=Step-4-To-u0050" in text
    assert "*STEP, NAME=Step-5-To-u0055" in text
    assert "*STEP, NAME=Step-6-To-u0060" in text
    assert "N_RP, 2, 2, 6.0000000000e-03" in text

def test_package67_deck_structure():
    inp_path = PKG67_DIR / "M1_MC_PROP_S2_FINE_DT.inp"
    assert inp_path.is_file(), "Package 67 input deck missing"
    text = inp_path.read_text(encoding="utf-8")
    assert "*STEP, NAME=Step-1-Equilibrate" in text
    assert "*STEP, NAME=Step-2-Continue, NLGEOM=NO, INC=800" in text
    assert "2.50000000e-03, 1.0, 1.0e-12, 2.50000000e-03" in text
    assert "*OUTPUT, FIELD, FREQUENCY=10" in text
    assert "N_RP, 2, 2, 6.0000000000e-03" in text

def test_pbs_submission_scripts():
    for pkg_dir, pbs_name in [(PKG66_DIR, "submit_M1_MC_PROP_CTRL_29K.pbs"), (PKG67_DIR, "submit_M1_MC_PROP_S2_FINE_DT.pbs")]:
        pbs_path = pkg_dir / pbs_name
        assert pbs_path.is_file(), f"PBS script missing: {pbs_name}"
        text = pbs_path.read_text(encoding="utf-8")
        assert "#PBS -q entry_imfdfkmq" in text
        assert "#PBS -l select=1:ncpus=1:mem=16gb" in text
        assert "#PBS -l walltime=04:00:00" in text
        assert "#PBS -m abe" in text
        assert "notification_install_terminal_trap" in text
        assert "\r" not in text, f"CRLF line endings detected in {pbs_name}"

if __name__ == "__main__":
    test_frozen_uel_integrity()
    test_package66_manifest_and_hashes()
    test_package67_manifest_and_hashes()
    test_package66_deck_structure()
    test_package67_deck_structure()
    test_pbs_submission_scripts()
    print("ALL F1548 UNIT TESTS PASSED.")

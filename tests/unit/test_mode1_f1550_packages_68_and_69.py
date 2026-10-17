#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for Task F1550: Package 68 (Consistent L2 Reconstruction Diagnostic)
and Package 69 (Uninterrupted 17,913-element control to u=0.0060 mm).
"""

import json
import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PKG68_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "68_method_c_propagation_s2_recon_diag"
PKG69_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "69_method_c_propagation_17k_uninterrupted_control"
FROZEN_UEL_SHA = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"

def test_package68_frozen_uel_integrity():
    uel_path = PKG68_DIR / "f42_mixed_uel.for"
    assert uel_path.is_file(), "f42_mixed_uel.for missing from Package 68"
    actual_sha = hashlib.sha256(uel_path.read_bytes()).hexdigest().lower()
    assert actual_sha == FROZEN_UEL_SHA, f"Frozen UEL hash mismatch in Pkg 68: {actual_sha}"

def test_package68_manifest_integrity():
    auth_path = PKG68_DIR / "METHOD_C_PROP_S2_RECON_DIAG_AUTHORIZATION.json"
    assert auth_path.is_file(), "Package 68 manifest missing"
    with open(auth_path, "r", encoding="utf-8") as f:
        auth = json.load(f)
    assert auth["adapter"] == "mode1-qualified-batch-v2"
    assert auth["batch_name"] == "MODE1_METHOD_C_PROP_S2_RECON_DIAG"
    assert auth["scientific_scope"] == "MODE1"
    assert auth["technical_stage"] == "C1-2"
    assert auth["max_submissions"] == 1
    assert auth["automatic_retry"] is False

    for fname, expected_hash in auth["files"].items():
        fpath = PKG68_DIR / fname
        assert fpath.is_file(), f"Manifest file missing on disk: {fname}"
        actual_hash = hashlib.sha256(fpath.read_bytes()).hexdigest().lower()
        assert actual_hash == expected_hash, f"Hash mismatch for {fname}: {actual_hash} vs {expected_hash}"

def test_package69_frozen_uel_integrity():
    uel_path = PKG69_DIR / "f42_mixed_uel.for"
    assert uel_path.is_file(), "f42_mixed_uel.for missing from Package 69"
    actual_sha = hashlib.sha256(uel_path.read_bytes()).hexdigest().lower()
    assert actual_sha == FROZEN_UEL_SHA, f"Frozen UEL hash mismatch in Pkg 69: {actual_sha}"

def test_package69_manifest_integrity():
    auth_path = PKG69_DIR / "METHOD_C_PROP_CTRL_17K_AUTHORIZATION.json"
    assert auth_path.is_file(), "Package 69 manifest missing"
    with open(auth_path, "r", encoding="utf-8") as f:
        auth = json.load(f)
    assert auth["adapter"] == "mode1-qualified-batch-v2"
    assert auth["batch_name"] == "MODE1_METHOD_C_PROP_CTRL_17K"
    assert auth["scientific_scope"] == "MODE1"
    assert auth["technical_stage"] == "C1-2"
    assert auth["max_submissions"] == 1
    assert auth["automatic_retry"] is False

    for fname, expected_hash in auth["files"].items():
        fpath = PKG69_DIR / fname
        assert fpath.is_file(), f"Manifest file missing on disk: {fname}"
        actual_hash = hashlib.sha256(fpath.read_bytes()).hexdigest().lower()
        assert actual_hash == expected_hash, f"Hash mismatch for {fname}: {actual_hash} vs {expected_hash}"

def test_package69_step_schedule():
    inp_path = PKG69_DIR / "M1_MC_PROP_CTRL_17K.inp"
    assert inp_path.is_file(), "Package 69 .inp deck missing"
    content = inp_path.read_text(encoding="utf-8", errors="replace")
    assert "*STEP, NAME=Step-1-To-u0010" in content
    assert "*STEP, NAME=Step-2-To-u0018" in content
    assert "*STEP, NAME=Step-3-To-u0021" in content
    assert "*STEP, NAME=Step-4-To-u0050" in content
    assert "*STEP, NAME=Step-5-To-u0055" in content
    assert "*STEP, NAME=Step-6-To-u0060" in content
    assert "6.0000000000e-03" in content

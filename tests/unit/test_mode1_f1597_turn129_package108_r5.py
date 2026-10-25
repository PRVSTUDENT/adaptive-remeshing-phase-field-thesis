#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1597_turn129_package108_r5.py
Unit Test Suite for Turn 129: Package 108 Revision 5 (5x1nm Multi-Increment Continuation).
Protocol Version: 2
"""

import sys
import json
import hashlib
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PKG_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "108_r5_c3_multi_increment_continuation"
AUTH_JSON = PKG_DIR / "M1_C3_STAGGERED_R5_AUTHORIZATION.json"
INP_FILE = PKG_DIR / "M1_C3_STAGGERED_R5_CONTINUATION.inp"
DAT_FILE = PKG_DIR / "M1_C3_STAGGERED_R5.dat"
PROD_UEL = REPO_ROOT / "models" / "pandey_kumar_mode1" / "15_energy_qualification_small" / "f42_mixed_uel.for"

EXPECTED_PROD_UEL = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
EXPECTED_EXP_UEL = "E72E00D338E355B370FC5EBABFE6679F49BC07458D333B642B593C6710B16DAD"

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

def test_production_uel_frozen():
    assert compute_sha256(PROD_UEL) == EXPECTED_PROD_UEL

def test_experimental_uel_hash():
    uel_file = PKG_DIR / "f42_experimental_irreversible_uel.for"
    assert uel_file.exists()
    assert compute_sha256(uel_file) == EXPECTED_EXP_UEL

def test_package108_r5_manifest_integrity():
    assert AUTH_JSON.exists()
    with open(AUTH_JSON, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest["schema"] == 1
    assert manifest["adapter"] == "mode1-experimental-irrev-v1"
    assert manifest["batch_name"] == "MODE1_C3_STAGGERED_CONTINUATION_R5"
    assert manifest["jobs"][0]["id"] == "M1_C3_STAGGERED_R5"
    assert manifest["jobs"][0]["cpus"] == 1
    assert manifest["jobs"][0]["memory_gb"] == 16
    for fname, recorded_hash in manifest["files"].items():
        actual = compute_sha256(PKG_DIR / fname)
        assert actual == recorded_hash.upper(), f"Hash mismatch for {fname}"

def test_package108_r5_step_structure():
    assert INP_FILE.exists()
    text = INP_FILE.read_text(encoding="utf-8")
    steps = [line.strip() for line in text.splitlines() if line.strip().lower().startswith("*step,")]
    assert len(steps) == 16, f"Expected 16 steps, found {len(steps)}"
    expected_step_names = [
        "Stage-A",
        "Inc1-Mech1", "Inc1-Phase1", "Inc1-Mech2",
        "Inc2-Mech1", "Inc2-Phase1", "Inc2-Mech2",
        "Inc3-Mech1", "Inc3-Phase1", "Inc3-Mech2",
        "Inc4-Mech1", "Inc4-Phase1", "Inc4-Mech2",
        "Inc5-Mech1", "Inc5-Phase1", "Inc5-Mech2"
    ]
    for name in expected_step_names:
        assert any(name.lower() in s.lower() for s in steps), f"Missing step {name}"

def test_package108_r5_displacement_targets():
    text = INP_FILE.read_text(encoding="utf-8")
    targets = [
        "0.00196510735",
        "0.001966107",
        "0.001967107",
        "0.001968107",
        "0.001969107",
        "0.001970107"
    ]
    for target in targets:
        assert f"N_RP, 2, 2, {target}" in text, f"Missing boundary target {target}"

def test_package108_r5_datacheck_clean():
    assert DAT_FILE.exists()
    text = DAT_FILE.read_text(encoding="utf-8", errors="ignore")
    assert "***ERROR" not in text
    assert "ANALYSIS DATACHECK COMPLETE" in text or "ANALYSIS COMPLETE" in text

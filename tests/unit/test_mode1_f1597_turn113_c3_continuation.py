#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1597_turn113_c3_continuation.py
Unit test suite for Turn 113: Candidate C3 State Reconstruction and Continuation Package.
Protocol Version: 2
"""
import json
import hashlib
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PROD_UEL = REPO_ROOT / "models" / "pandey_kumar_mode1" / "15_energy_qualification_small" / "f42_mixed_uel.for"
EXP_UEL = REPO_ROOT / "models" / "pandey_kumar_mode1" / "104_experimental_irreversible_uel" / "f42_experimental_irreversible_uel.for"

PACKAGE_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "105_c3_irreversible_continuation"
PATCH_FILE = REPO_ROOT / "results" / "validation" / "mode1_f1597" / "mode1_execution_gate_experimental_uel.patch"
AUDIT_JSON = REPO_ROOT / "results" / "validation" / "mode1_f1597" / "turn113_c3_package_generation_audit.json"

EXPECTED_PROD_UEL_SHA = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
EXPECTED_EXP_UEL_SHA = "9D6877F36F88457E9EACB06D5F6C7E112A8865D2A1DB1CC95F00DF28AA2448B8"
TURN113_EXP_UEL_SHA = "55FF5D097F207340291BB1A26603B70AB1F105BE8458914809AF08476A8FA195"

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

def test_uel_hashes():
    assert PROD_UEL.exists(), f"Production UEL missing: {PROD_UEL}"
    assert sha256_file(PROD_UEL) == EXPECTED_PROD_UEL_SHA, "Production UEL hash modified!"
    assert EXP_UEL.exists(), f"Experimental UEL missing: {EXP_UEL}"
    assert sha256_file(EXP_UEL) == EXPECTED_EXP_UEL_SHA, "Experimental UEL hash modified!"

def test_execution_gate_patch_proposal():
    assert PATCH_FILE.exists(), f"Execution gate patch missing: {PATCH_FILE}"
    patch_text = PATCH_FILE.read_text(encoding="utf-8")
    assert "mode1_execution_gate.py" in patch_text
    assert "EXPERIMENTAL_IRREV_UEL = '55ff5d097f207340291bb1a26603b70ab1f105be8458914809af08476a8fa195'" in patch_text
    assert "mode1-experimental-irrev-v1" in patch_text
    assert "f42_experimental_irreversible_uel.for" in patch_text

def test_c3_package_files():
    assert PACKAGE_DIR.exists(), f"Package dir missing: {PACKAGE_DIR}"
    inp_file = PACKAGE_DIR / "M1_C3_IRREV_CONTINUATION.inp"
    assert inp_file.exists(), "Input deck missing"
    
    text = inp_file.read_text(encoding="utf-8")
    assert "*Step, name=Stage-A" in text
    assert "*Step, name=Stage-B" in text
    assert "N_RP, 2, 2, 0.00196510735" in text
    assert "N_RP, 2, 2, 0.00197010735" in text
    assert "ELSET=PHASE_QUADS" in text
    assert "ELSET=MECH_QUADS" in text
    assert "elset=VIS_QUADS" in text or "ELSET=VIS_QUADS" in text

    # Check d_lower_bounds.csv
    csv_file = PACKAGE_DIR / "d_lower_bounds.csv"
    assert csv_file.exists(), "d_lower_bounds.csv missing"
    lines = [line.strip() for line in csv_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) == 2651, f"Expected 2651 lines (header + 2650 quads), got {len(lines)}"

    # Check packaged UEL matches
    pkg_uel = PACKAGE_DIR / "f42_experimental_irreversible_uel.for"
    assert pkg_uel.exists()
    assert sha256_file(pkg_uel) == EXPECTED_EXP_UEL_SHA

    # Check authorization manifest
    manifest_file = PACKAGE_DIR / "M1_C3_IRREV_AUTHORIZATION.json"
    assert manifest_file.exists()
    with open(manifest_file, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest["automatic_retry"] is False
    assert manifest["max_submissions"] == 1
    job = manifest["jobs"][0]
    assert job["cpus"] == 1
    assert job["memory_gb"] <= 16
    assert job["walltime_hours"] <= 8

def test_c3_package_generation_audit():
    assert AUDIT_JSON.exists(), f"Audit file missing: {AUDIT_JSON}"
    with open(AUDIT_JSON, "r", encoding="utf-8") as f:
        audit = json.load(f)
    assert audit["status"] == "PACKAGE_GENERATION_COMPLETE"
    metrics = audit["candidate_c3_metrics"]
    assert metrics["n_nodes"] == 2769
    assert metrics["n_quads"] == 2650
    assert abs(metrics["u_step1_mm"] - 0.00196510735) < 1e-9
    assert 178.0 <= metrics["rf2_step1_N"] <= 182.0
    assert 0.059 <= metrics["ef_step1_mJ"] <= 0.063
    assert 0.650 <= metrics["d_max_step1"] <= 0.660

def test_gate_governance():
    # Verify Gate C1-1 and Gate C1-2 status
    cur_state_file = REPO_ROOT / "project_coordination" / "CURRENT_STATE.md"
    text = cur_state_file.read_text(encoding="utf-8")
    assert "GATE_C1_1" in text
    assert "GATE_C1_2" in text

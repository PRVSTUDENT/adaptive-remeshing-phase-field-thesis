"""
Unit test for Task F1574:
Resolve Coupled Equilibrium Across Snap-Through and Qualify Same-Mesh Cracked-State Continuation
"""

import os
import json
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

PRODUCTION_UEL_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
EXPECTED_PROD_HASH = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"

EXPERIMENTAL_UEL_PATH = os.path.join(
    REPO_ROOT, "models", "pandey_kumar_mode1", "experimental_offset_uel", "f42_experimental_offset_uel.for"
)
EXPECTED_EXP_HASH = "ef92ed58dbe3ea921b48cb328128ab950ba2cafd698e05381e2b29f61412514d"

EVIDENCE_DIR = os.path.join(
    REPO_ROOT, "models", "pandey_kumar_mode1", "experimental_offset_uel", "evidence_f1574"
)

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()

def test_production_uel_remains_frozen():
    assert os.path.exists(PRODUCTION_UEL_PATH), "Production UEL not found"
    actual_hash = sha256_file(PRODUCTION_UEL_PATH)
    assert actual_hash == EXPECTED_PROD_HASH, f"Production UEL modified! {actual_hash} != {EXPECTED_PROD_HASH}"

def test_experimental_offset_uel_hash_invariant():
    assert os.path.exists(EXPERIMENTAL_UEL_PATH), "Experimental UEL not found"
    actual_hash = sha256_file(EXPERIMENTAL_UEL_PATH)
    assert actual_hash == EXPECTED_EXP_HASH, f"Experimental UEL modified! {actual_hash} != {EXPECTED_EXP_HASH}"

def test_plateau_reaction_force_continuity():
    plateau_parity_path = os.path.join(EVIDENCE_DIR, "plateau_continuation_parity.json")
    assert os.path.exists(plateau_parity_path), "plateau_continuation_parity.json missing"
    with open(plateau_parity_path, "r") as f:
        data = json.load(f)
    
    # Assert zero-increment discontinuity is less than 0.01% (observed 0.0032%)
    rel_err = data["zero_increment_rel_error_pct"]
    assert rel_err < 0.01, f"Zero-increment discontinuity too high: {rel_err}%"
    assert abs(data["zero_increment_case_a_rf2_N"] - 5.0857) < 0.001
    assert abs(data["zero_increment_case_b_rf2_N"] - 5.0855) < 0.001

def test_plateau_forward_continuation_parity():
    plateau_parity_path = os.path.join(EVIDENCE_DIR, "plateau_continuation_parity.json")
    with open(plateau_parity_path, "r") as f:
        data = json.load(f)
    
    rows = data["step2_continuation_rows"]
    assert len(rows) == 3, f"Expected 3 continuation rows, got {len(rows)}"
    for row in rows:
        err = row["rel_error_pct"]
        assert err < 4.0, f"Continuation error too high at inc {row['increment']}: {err}%"

def test_plateau_energy_continuity():
    plateau_energy_path = os.path.join(EVIDENCE_DIR, "plateau_energy_parity.json")
    assert os.path.exists(plateau_energy_path), "plateau_energy_parity.json missing"
    with open(plateau_energy_path, "r") as f:
        data = json.load(f)
    
    se_err = data["strain_energy_rel_error_pct"]
    assert se_err < 0.01, f"Strain energy error too high: {se_err}%"
    
    allie_a = data["allie_case_a_plateau"]
    allie_b = data["allie_case_b_step1"]
    allie_err = abs(allie_b - allie_a) / allie_a * 100.0
    assert allie_err < 0.001, f"Internal energy error too high: {allie_err}%"

def test_postsnap_forward_continuation_parity():
    postsnap_parity_path = os.path.join(EVIDENCE_DIR, "postsnap_continuation_parity.json")
    assert os.path.exists(postsnap_parity_path), "postsnap_continuation_parity.json missing"
    with open(postsnap_parity_path, "r") as f:
        data = json.load(f)
    
    rows = data["step2_continuation_rows"]
    assert len(rows) == 4, f"Expected 4 continuation rows, got {len(rows)}"
    for row in rows:
        err = row["rel_error_pct"]
        assert err < 3.5, f"Continuation error too high at inc {row['increment']}: {err}%"

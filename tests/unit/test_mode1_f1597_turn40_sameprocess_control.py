"""
Unit test suite for Turn 40: Package 86 Same-Process Staggered Donor Control.
Verifies input deck structure, 4-step sequence, boundary condition semantics,
frozen UEL preservation, and authorization governance.
"""
import os
import json
import hashlib
import pytest

PKG86_DIR = os.path.abspath("models/pandey_kumar_mode1/86_donor_sameprocess_staggered_control")
FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

def get_file_hash(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest().upper()

def test_package86_files_exist_and_hashes():
    assert os.path.isdir(PKG86_DIR), f"Package 86 dir missing: {PKG86_DIR}"
    inp_path = os.path.join(PKG86_DIR, "M1_DONOR_SAMEPROCESS_STAGGERED.inp")
    uel_path = os.path.join(PKG86_DIR, "f42_mixed_uel.for")
    manifest_path = os.path.join(PKG86_DIR, "PACKAGE_MANIFEST.json")
    auth_path = os.path.join(PKG86_DIR, "PACKAGE86_AUTHORIZATION.json")
    pbs_path = os.path.join(PKG86_DIR, "submit_M1_DONOR_SAMEPROCESS_STAGGERED.pbs")
    
    for p in [inp_path, uel_path, manifest_path, auth_path, pbs_path]:
        assert os.path.isfile(p), f"Required file missing: {p}"
        
    uel_hash = get_file_hash(uel_path)
    assert uel_hash == FROZEN_UEL_HASH, f"UEL hash mismatch! Expected {FROZEN_UEL_HASH}, got {uel_hash}"

def test_package86_input_deck_steps_and_semantics():
    inp_path = os.path.join(PKG86_DIR, "M1_DONOR_SAMEPROCESS_STAGGERED.inp")
    with open(inp_path, "r") as f:
        content = f.read()
        
    # Check that no restart read is present
    assert "*restart, read" not in content.lower(), "Package 86 must not contain *RESTART, READ"
    
    # Check that the 4 steps are present
    assert "*step, name=donor_loading" in content.lower()
    assert "*step, name=phase_subproblem" in content.lower()
    assert "*step, name=mechanical_subproblem" in content.lower()
    assert "*step, name=coupled_check" in content.lower()
    
    # Check Step 1 target endpoint and rate
    assert "0.50802148" in content
    assert "0.00254010735" in content
    
    # Check node set definitions
    assert "*nset, nset=n_all_physical" in content.lower()
    assert "*nset, nset=n_interior_and_bottom" in content.lower()
    
    # Check Step 2 mechanical hold
    step2_idx = content.lower().find("*step, name=phase_subproblem")
    step3_idx = content.lower().find("*step, name=mechanical_subproblem")
    step4_idx = content.lower().find("*step, name=coupled_check")
    
    step2_text = content[step2_idx:step3_idx].lower()
    assert "n_all_physical, 1, 1" in step2_text
    assert "n_interior_and_bottom, 2, 2" in step2_text
    # Damage must not be held in Step 2
    assert "n_all_physical, 3, 3" not in step2_text
    
    # Check Step 3 damage hold and mechanical release
    step3_text = content[step3_idx:step4_idx].lower()
    assert "n_all_physical, 3, 3" in step3_text
    # Mechanical DOFs must not be fixed in Step 3
    assert "n_all_physical, 1, 1" not in step3_text
    
    # Check Step 4 coupled check (interior released)
    step4_text = content[step4_idx:].lower()
    assert "n_all_physical, 1, 1" not in step4_text
    assert "n_all_physical, 3, 3" not in step4_text
    assert "n_rp, 2, 2, 0.00254010735" in step4_text

def test_package86_manifest_and_authorization():
    manifest_path = os.path.join(PKG86_DIR, "PACKAGE_MANIFEST.json")
    auth_path = os.path.join(PKG86_DIR, "PACKAGE86_AUTHORIZATION.json")
    
    with open(manifest_path, "r") as f:
        manifest = json.load(f)
    with open(auth_path, "r") as f:
        auth = json.load(f)
        
    assert manifest["package_id"] == "PACKAGE_86_DONOR_SAMEPROCESS_STAGGERED_CONTROL"
    assert auth["batch_name"] == "MODE1_PACKAGE86_DONOR_SAMEPROCESS_STAGGERED"
    assert auth["adapter"] == "mode1-qualified-batch-v2"
    assert auth["files"]["f42_mixed_uel.for"].lower() == FROZEN_UEL_HASH.lower()
    assert auth["jobs"][0]["id"] == "M1_DONOR_SAMEPROCESS_STAGGERED"
    assert auth["jobs"][0]["cpus"] == 1
    assert auth["jobs"][0]["memory_gb"] <= 16
    assert auth["jobs"][0]["walltime_hours"] <= 8

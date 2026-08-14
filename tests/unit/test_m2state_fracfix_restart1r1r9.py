#!/usr/bin/env python3
"""
Unit Test Suite for Production Candidate M2STATE_FRACFIX_RESTART1R1R9.
Task ID: F91STATE-M2-INSTRUMENTED-RESTART1-R1R9-PREP-AND-QUALIFICATION1
"""

import os
import sys
import json
import hashlib
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PKG_DIR = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R9"

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def test_manifest_and_files_integrity():
    manifest_path = PKG_DIR / "PACKAGE_MANIFEST.json"
    assert manifest_path.exists(), "PACKAGE_MANIFEST.json missing"
    
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert "files" in manifest, "Canonical 'files' key missing"
    assert manifest["candidate"] == "M2STATE_FRACFIX_RESTART1R1R9"
    assert manifest["task_id"] == "F91STATE-M2-INSTRUMENTED-RESTART1-R1R9-PREP-AND-QUALIFICATION1"
    
    files_list = manifest["files"]
    files_dict = {f["filename"]: f["sha256"] for f in files_list}
    required_files = [
        "M2STATE_FRACFIX_RESTART1R1R9.inp",
        "f42_mixed_uel.for",
        "STATE_TRANSFER_ARTIFACT.json",
        "TRANSFER_MANIFEST.json",
        "RESTART_ACCEPTANCE_CONTRACT.json",
        "job_notifications.sh",
        "validate_package_manifest.py",
        "M2STATE_FRACFIX_RESTART1R1R9.pbs",
        "submit_m2state_fracfix_restart1r1r9.sh"
    ]
    for rf in required_files:
        assert rf in files_dict, f"File {rf} missing from manifest mapping"
        f_p = PKG_DIR / rf
        assert f_p.exists(), f"File {rf} missing on disk"
        actual_hash = sha256_file(f_p)
        assert actual_hash.lower() == files_dict[rf].lower(), f"Hash mismatch for {rf}"

def test_deck_structure_and_property_abi():
    inp_path = PKG_DIR / "M2STATE_FRACFIX_RESTART1R1R9.inp"
    text = inp_path.read_text(encoding="utf-8")
    
    # Check UEL declarations have PROPERTIES=6
    for t in ["U1", "U2", "U3", "U4"]:
        pattern = rf"\*USER ELEMENT,\s*TYPE={t},.*PROPERTIES=6"
        assert re.search(pattern, text), f"TYPE={t} does not declare PROPERTIES=6"
        
    # Check UEL PROPERTY cards have 6 values
    for elset in ["E_U1", "E_U2", "E_U3", "E_U4"]:
        pattern = rf"\*UEL PROPERTY,\s*ELSET={elset}\s*\n\s*([\d\.\s,eE+-]+)"
        m = re.search(pattern, text)
        assert m, f"UEL PROPERTY for {elset} not found"
        props = [float(p.strip()) for p in m.group(1).split(",") if p.strip()]
        assert len(props) == 6, f"Expected 6 properties for {elset}, got {len(props)}"
        assert props[0] == 0.015, f"l0 mismatch: {props[0]}"
        assert props[1] == 0.0027, f"Gc mismatch: {props[1]}"
        assert props[2] == 210.0, f"E mismatch: {props[2]}"
        assert props[3] == 0.3, f"nu mismatch: {props[3]}"
        assert props[4] == 1.0e-7, f"k mismatch: {props[4]}"
        assert props[5] == 4894.0, f"Nphys mismatch: {props[5]}"

def test_instrumented_output_requests():
    inp_path = PKG_DIR / "M2STATE_FRACFIX_RESTART1R1R9.inp"
    text = inp_path.read_text(encoding="utf-8")
    
    # Verify NSET N_RP exists
    assert "*NSET, NSET=N_RP" in text, "Missing *NSET, NSET=N_RP"
    
    # Verify *EL PRINT for SDV14, SDV15, SDV16
    assert "*EL PRINT, FREQ=1, ELSET=E_MECH_UEL" in text, "Missing *EL PRINT for E_MECH_UEL"
    assert "SDV14, SDV15, SDV16" in text, "Missing SDV14, SDV15, SDV16 in EL PRINT"
    
    # Verify *NODE OUTPUT for N_PHYSICAL, N_RP, N_BOTTOM
    assert "*NODE OUTPUT, NSET=N_PHYSICAL" in text
    assert "*NODE OUTPUT, NSET=N_RP" in text
    assert "*NODE OUTPUT, NSET=N_BOTTOM" in text


def test_uel_safe_jacobian_inversion_contract():
    uel_path = PKG_DIR / "f42_mixed_uel.for"
    text = uel_path.read_text(encoding="utf-8")
    
    # Verify JAC(2,2) forward declaration and DETJ computation
    assert "JAC(2,2)" in text
    assert "INVJ(2,2)" in text
    
    # Verify no unsafe in-place overwrite
    assert "INVJ(1,1) =  JAC(2,2) / DETJ" in text
    assert "INVJ(1,2) = -JAC(1,2) / DETJ" in text
    assert "INVJ(2,1) = -JAC(2,1) / DETJ" in text
    assert "INVJ(2,2) =  JAC(1,1) / DETJ" in text
    
    # Verify unsafe pattern is NOT present
    assert "INVJ(1,1) =  INVJ(2,2) / DETJ" not in text
    assert "INVJ(2,2) =  INVJ(1,1) / DETJ" not in text
    
    # Verify consistent phase residual RHS = F_H - K_phase * d
    assert "RHS(I,1) = RHS(I,1) - AMATRX(I,J)*U(J)" in text

def test_pbs_and_wrapper_contract():
    pbs_path = PKG_DIR / "M2STATE_FRACFIX_RESTART1R1R9.pbs"
    pbs_text = pbs_path.read_text(encoding="utf-8")
    assert "#PBS -N M2STATE_FRACFIX_RESTART1R1R9" in pbs_text
    assert "#PBS -q entry_imfdfkmq" in pbs_text
    assert "#PBS -l select=1:ncpus=1:mpiprocs=1:mem=16gb" in pbs_text
    assert "#PBS -l walltime=24:00:00" in pbs_text
    assert "#PBS -m abe" in pbs_text
    assert "#PBS -M pr21vyci@mailserver.tu-freiberg.de" in pbs_text
    
    sh_path = PKG_DIR / "submit_m2state_fracfix_restart1r1r9.sh"
    sh_text = sh_path.read_text(encoding="utf-8")
    assert "validate_package_manifest.py" in sh_text
    assert "--dry-run" in sh_text
    assert "--execute" in sh_text

if __name__ == "__main__":
    print("Running test_manifest_and_files_integrity...")
    test_manifest_and_files_integrity()
    print("PASS")
    print("Running test_deck_structure_and_property_abi...")
    test_deck_structure_and_property_abi()
    print("PASS")
    print("Running test_instrumented_output_requests...")
    test_instrumented_output_requests()
    print("PASS")
    print("Running test_uel_safe_jacobian_inversion_contract...")
    test_uel_safe_jacobian_inversion_contract()
    print("PASS")
    print("Running test_pbs_and_wrapper_contract...")
    test_pbs_and_wrapper_contract()
    print("PASS")
    print("ALL 5 UNIT TESTS PASSED SUCCESSFULLY!")


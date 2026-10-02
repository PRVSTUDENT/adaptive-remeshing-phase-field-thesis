#!/usr/bin/env python3
"""
Unit Test Suite & Regression Test for Candidate M2STATE_FRACFIX_RESTART1R1R10.
Task ID: F93RECOVER-M2-INSTRUMENTED-RESTART1-R1R10-TECHNICAL-REPLACEMENT1
"""

import os
import sys
import json
import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG_DIR = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R10"
R1R9_DIR = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R9"

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
    assert manifest["candidate"] == "M2STATE_FRACFIX_RESTART1R1R10"
    assert manifest["task_id"] == "F93RECOVER-M2-INSTRUMENTED-RESTART1-R1R10-TECHNICAL-REPLACEMENT1"
    
    files_list = manifest["files"]
    files_dict = {f["filename"]: f["sha256"] for f in files_list}
    required_files = [
        "M2STATE_FRACFIX_RESTART1R1R10.inp",
        "f42_mixed_uel.for",
        "STATE_TRANSFER_ARTIFACT.json",
        "TRANSFER_MANIFEST.json",
        "RESTART_ACCEPTANCE_CONTRACT.json",
        "job_notifications.sh",
        "validate_package_manifest.py",
        "M2STATE_FRACFIX_RESTART1R1R10.pbs",
        "submit_m2state_fracfix_restart1r1r10.sh"
    ]
    for rf in required_files:
        assert rf in files_dict, f"File {rf} missing from manifest mapping"
        f_p = PKG_DIR / rf
        assert f_p.exists(), f"File {rf} missing on disk"
        actual_hash = sha256_file(f_p)
        assert actual_hash.lower() == files_dict[rf].lower(), f"Hash mismatch for {rf}"

def test_deck_structure_and_property_abi():
    inp_path = PKG_DIR / "M2STATE_FRACFIX_RESTART1R1R10.inp"
    text = inp_path.read_text(encoding="utf-8")
    
    for t in ["U1", "U2", "U3", "U4"]:
        pattern = rf"\*USER ELEMENT,\s*TYPE={t},.*PROPERTIES=6"
        assert re.search(pattern, text), f"TYPE={t} does not declare PROPERTIES=6"
        
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
    inp_path = PKG_DIR / "M2STATE_FRACFIX_RESTART1R1R10.inp"
    text = inp_path.read_text(encoding="utf-8")
    
    assert "*NSET, NSET=N_RP" in text, "Missing *NSET, NSET=N_RP"
    assert "*EL PRINT, FREQ=1, ELSET=E_MECH_UEL" in text, "Missing *EL PRINT for E_MECH_UEL"
    assert "SDV14, SDV15, SDV16" in text, "Missing SDV14, SDV15, SDV16 in EL PRINT"
    assert "*NODE OUTPUT, NSET=N_PHYSICAL" in text
    assert "*NODE OUTPUT, NSET=N_RP" in text
    assert "*NODE OUTPUT, NSET=N_BOTTOM" in text

def test_uel_safe_jacobian_inversion_contract():
    uel_path = PKG_DIR / "f42_mixed_uel.for"
    text = uel_path.read_text(encoding="utf-8")
    
    assert "JAC(2,2)" in text
    assert "INVJ(2,2)" in text
    assert "INVJ(1,1) =  JAC(2,2) / DETJ" in text
    assert "INVJ(1,2) = -JAC(1,2) / DETJ" in text
    assert "INVJ(2,1) = -JAC(2,1) / DETJ" in text
    assert "INVJ(2,2) =  JAC(1,1) / DETJ" in text
    assert "INVJ(1,1) =  INVJ(2,2) / DETJ" not in text
    assert "INVJ(2,2) =  INVJ(1,1) / DETJ" not in text
    assert "RHS(I,1) = RHS(I,1) - AMATRX(I,J)*U(J)" in text

def test_pbs_and_wrapper_contract():
    pbs_path = PKG_DIR / "M2STATE_FRACFIX_RESTART1R1R10.pbs"
    pbs_text = pbs_path.read_text(encoding="utf-8")
    assert "#PBS -N M2STATE_FRACFIX_RESTART1R1R10" in pbs_text
    assert "#PBS -q entry_imfdfkmq" in pbs_text
    assert "#PBS -l select=1:ncpus=1:mpiprocs=1:mem=16gb" in pbs_text
    assert "#PBS -l walltime=24:00:00" in pbs_text
    assert "#PBS -m abe" in pbs_text
    assert "#PBS -M pr21vyci@mailserver.tu-freiberg.de" in pbs_text
    
    sh_path = PKG_DIR / "submit_m2state_fracfix_restart1r1r10.sh"
    sh_text = sh_path.read_text(encoding="utf-8")
    assert "validate_package_manifest.py" in sh_text
    assert "--dry-run" in sh_text
    assert "--execute" in sh_text

def test_notification_function_name_regression():
    # 1. Verify R1R9 failed because it invoked load_notification_config
    if R1R9_DIR.exists():
        r1r9_pbs = (R1R9_DIR / "M2STATE_FRACFIX_RESTART1R1R9.pbs").read_text(encoding="utf-8")
        assert "load_notification_config" in r1r9_pbs, "R1R9 was expected to contain bad function name"
        assert "notification_load_config" not in r1r9_pbs, "R1R9 unexpectedly had corrected function name"
        
    # 2. Verify R1R10 PBS script invokes notification_load_config (and NOT load_notification_config)
    r1r10_pbs = (PKG_DIR / "M2STATE_FRACFIX_RESTART1R1R10.pbs").read_text(encoding="utf-8")
    assert "notification_load_config" in r1r10_pbs, "R1R10 PBS script missing notification_load_config"
    # Ensure the erroneous call is NOT present as an isolated word
    assert not re.search(r"\bload_notification_config\b", r1r10_pbs), "Erroneous load_notification_config still present in R1R10 PBS"

    # 3. Verify R1R10 submission wrapper invokes notification_load_config
    r1r10_sh = (PKG_DIR / "submit_m2state_fracfix_restart1r1r10.sh").read_text(encoding="utf-8")
    assert "notification_load_config" in r1r10_sh, "R1R10 wrapper missing notification_load_config"
    assert not re.search(r"\bload_notification_config\b", r1r10_sh), "Erroneous load_notification_config still present in R1R10 wrapper"

    # 4. Verify job_notifications.sh defines notification_load_config
    notif_sh = (PKG_DIR / "job_notifications.sh").read_text(encoding="utf-8")
    assert "notification_load_config()" in notif_sh, "job_notifications.sh does not define notification_load_config()"
    assert "load_notification_config()" not in notif_sh, "job_notifications.sh unexpectedly defines load_notification_config()"

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
    print("Running test_notification_function_name_regression...")
    test_notification_function_name_regression()
    print("PASS")
    print("ALL 6 UNIT & REGRESSION TESTS PASSED SUCCESSFULLY!")

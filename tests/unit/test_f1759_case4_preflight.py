# -*- coding: utf-8 -*-
"""
test_f1759_case4_preflight.py
Unit tests verifying the Case 4 Five-Hole Plate (Pandey & Kumar 2025 Sec. 4.5)
technical preflight qualification under Task F1759.
"""
import hashlib
import os
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PHYS_INP = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "217_f1725_physics_study", "F1725_S2_COARSEN_ET315.inp")
PROD_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "235_f1759_case4_adapted_fracture")
PROD_INP = os.path.join(PROD_DIR, "PK_F1759_CASE_4_PROD.inp")
PBS_SCRIPT = os.path.join(PROD_DIR, "submit_f1759_case4_fracture.pbs")
DC_SCRIPT = os.path.join(PROD_DIR, "run_f1759_datacheck.sh")
UEL_SRC = os.path.join(PROD_DIR, "f42_mixed_uel.for")

EXPECTED_UEL_SHA = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
PUBLISHED_ELEMENT_COUNT = 12944

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

def test_frozen_uel_integrity():
    assert os.path.isfile(UEL_SRC), f"Missing UEL source at {UEL_SRC}"
    actual_sha = sha256_file(UEL_SRC)
    assert actual_sha == EXPECTED_UEL_SHA, f"UEL SHA mismatch: {actual_sha} vs {EXPECTED_UEL_SHA}"

def test_physical_mesh_and_benchmark_parity():
    assert os.path.isfile(PHYS_INP), f"Missing physical input deck {PHYS_INP}"
    assert os.path.isfile(PROD_INP), f"Missing production input deck {PROD_INP}"
    
    with open(PROD_INP, "r") as f:
        content = f.read()
    
    # Check physical element count in UEL property
    assert "13017.0" in content, "Expected 13017.0 physical element count declaration in UEL property"
    parity_pct = (13017 - PUBLISHED_ELEMENT_COUNT) / PUBLISHED_ELEMENT_COUNT * 100.0
    assert abs(parity_pct - 0.563968) < 0.01, f"Expected +0.56% parity, got {parity_pct:.2f}%"

def test_layered_production_deck_structure():
    with open(PROD_INP, "r") as f:
        lines = f.readlines()
    
    in_el = False
    counts = {"U1": 0, "U2": 0, "U3": 0, "U4": 0, "CPE4": 0, "CPE3": 0}
    current_type = None
    
    for l in lines:
        s = l.strip()
        if s.startswith("*ELEMENT") and not s.startswith("*ELEMENT OUTPUT"):
            in_el = True
            for t in counts.keys():
                if f"TYPE={t}" in s:
                    current_type = t
            continue
        if s.startswith("*"):
            in_el = False
            current_type = None
            continue
        if in_el and current_type:
            counts[current_type] += 1
            
    assert counts["U1"] == 12696, f"Expected 12696 U1 quad elements, got {counts['U1']}"
    assert counts["U2"] == 12696, f"Expected 12696 U2 quad elements, got {counts['U2']}"
    assert counts["CPE4"] == 12696, f"Expected 12696 CPE4 quad elements, got {counts['CPE4']}"
    assert counts["U3"] == 321, f"Expected 321 U3 tri elements, got {counts['U3']}"
    assert counts["U4"] == 321, f"Expected 321 U4 tri elements, got {counts['U4']}"
    assert counts["CPE3"] == 321, f"Expected 321 CPE3 tri elements, got {counts['CPE3']}"
    
    total_layered = sum(counts.values())
    assert total_layered == 39051, f"Expected 39051 total layered elements, got {total_layered}"

def test_sdv_field_output_and_card_wrapping():
    with open(PROD_INP, "r") as f:
        lines = f.readlines()
    
    # 1. Check card wrapping on NSET lines
    in_nset = False
    max_items = 0
    for l in lines:
        s = l.strip()
        if s.startswith("*NSET"):
            in_nset = True
            continue
        if s.startswith("*"):
            in_nset = False
            continue
        if in_nset:
            items = [x.strip() for x in s.split(",") if x.strip()]
            if len(items) > max_items:
                max_items = len(items)
    
    assert max_items <= 16, f"Found NSET line exceeding 16 items: {max_items}"
    
    # 2. Check SDV field output request
    content = "".join(lines)
    assert "*ELEMENT OUTPUT, ELSET=All_elem\nS, SDV" in content, "Missing complete S, SDV field output request"
    assert "*OUTPUT, FIELD, FREQUENCY=1" in content, "Missing FREQUENCY=1 field output request"
    assert "0.0080, 0.0027, 210.0, 0.3, 1.0e-7" in content, "Missing exact Five-Hole UEL material constants (l0=0.0080)"

def test_pbs_and_datacheck_script_integrity():
    assert os.path.isfile(PBS_SCRIPT), f"Missing PBS script {PBS_SCRIPT}"
    assert os.path.isfile(DC_SCRIPT), f"Missing datacheck script {DC_SCRIPT}"
    
    with open(PBS_SCRIPT, "r") as f:
        pbs_content = f.read()
    assert "PK_F1759_CASE_4_PROD.inp" in pbs_content
    assert "f42_mixed_uel.for" in pbs_content
    assert "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6" in pbs_content
    assert "#PBS -q entry_imfdfkmq" in pbs_content
    assert "#PBS -l select=1:ncpus=1:mem=16gb" in pbs_content

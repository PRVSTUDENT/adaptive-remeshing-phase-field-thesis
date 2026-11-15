# -*- coding: utf-8 -*-
"""
test_f1758_case1_preflight.py
Unit test suite verifying technical preflight for Task F1758:
Case 1 Mode-I Notched Plate Coupled Phase-Field Fracture Production Deck.
"""
import os
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

EXPECTED_FROZEN_UEL_SHA256 = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"

def get_file_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()

def test_frozen_uel_source_integrity():
    uel_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
    assert os.path.isfile(uel_path), f"Frozen UEL source missing: {uel_path}"
    sha = get_file_sha256(uel_path)
    assert sha == EXPECTED_FROZEN_UEL_SHA256, f"Frozen UEL hash mismatch: got {sha}, expected {EXPECTED_FROZEN_UEL_SHA256}"

def test_f1758_case1_production_deck_structure():
    prod_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "227_f1739_case1_adapted_fracture", "PK_F1758_CASE_1_PROD.inp")
    assert os.path.isfile(prod_path), f"Production deck missing: {prod_path}"
    
    with open(prod_path, "r") as f:
        lines = f.readlines()
    
    assert len(lines) > 50000, f"Deck appears truncated: {len(lines)} lines"
    
    # Audit ELEMENT OUTPUT requests
    element_output_indices = [i for i, line in enumerate(lines) if "*ELEMENT OUTPUT" in line.upper()]
    assert len(element_output_indices) >= 2, f"Expected at least 2 *ELEMENT OUTPUT requests, got {len(element_output_indices)}"
    
    for idx in element_output_indices:
        # Check next line for S, SDV
        next_line = lines[idx + 1].strip().upper()
        assert "SDV" in next_line, f"Line {idx+2} does not contain SDV: {next_line}"
        assert "S" in next_line, f"Line {idx+2} does not contain S: {next_line}"

    # Audit FIELD FREQUENCY requests
    field_output_lines = [line.strip().upper() for line in lines if "*OUTPUT, FIELD" in line.upper()]
    assert len(field_output_lines) >= 2, "Expected at least 2 *OUTPUT, FIELD requests"
    for fol in field_output_lines:
        assert "FREQUENCY=1" in fol, f"FREQUENCY=1 not set: {fol}"

def test_f1758_case1_nset_line_wrapping():
    prod_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "227_f1739_case1_adapted_fracture", "PK_F1758_CASE_1_PROD.inp")
    with open(prod_path, "r") as f:
        in_nset = False
        for line_no, line in enumerate(f, 1):
            l = line.strip()
            if not l or l.startswith("**"):
                continue
            if l.startswith("*"):
                in_nset = l.upper().startswith("*NSET")
                continue
            if in_nset:
                items = [x.strip() for x in l.split(",") if x.strip()]
                assert len(items) <= 16, f"NSET line {line_no} exceeds 16 items: {len(items)} items"

def test_f1758_case1_element_layering_counts():
    prod_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "227_f1739_case1_adapted_fracture", "PK_F1758_CASE_1_PROD.inp")
    num_u1 = 0
    num_u2 = 0
    num_u3 = 0
    num_u4 = 0
    num_cpe4 = 0
    num_cpe3 = 0
    
    current_type = None
    with open(prod_path, "r") as f:
        for line in f:
            l = line.strip()
            if not l or l.startswith("**"):
                continue
            if l.startswith("*"):
                if l.upper().startswith("*ELEMENT"):
                    if "TYPE=U1" in l.upper():
                        current_type = "U1"
                    elif "TYPE=U2" in l.upper():
                        current_type = "U2"
                    elif "TYPE=U3" in l.upper():
                        current_type = "U3"
                    elif "TYPE=U4" in l.upper():
                        current_type = "U4"
                    elif "TYPE=CPE4" in l.upper():
                        current_type = "CPE4"
                    elif "TYPE=CPE3" in l.upper():
                        current_type = "CPE3"
                    else:
                        current_type = None
                else:
                    current_type = None
                continue
            if current_type == "U1":
                num_u1 += 1
            elif current_type == "U2":
                num_u2 += 1
            elif current_type == "U3":
                num_u3 += 1
            elif current_type == "U4":
                num_u4 += 1
            elif current_type == "CPE4":
                num_cpe4 += 1
            elif current_type == "CPE3":
                num_cpe3 += 1
                
    assert num_u1 == 13611, f"Expected 13,611 U1 quads, got {num_u1}"
    assert num_u2 == 13611, f"Expected 13,611 U2 quads, got {num_u2}"
    assert num_cpe4 == 13611, f"Expected 13,611 CPE4 quads, got {num_cpe4}"
    assert num_u3 == 349, f"Expected 349 U3 tris, got {num_u3}"
    assert num_u4 == 349, f"Expected 349 U4 tris, got {num_u4}"
    assert num_cpe3 == 349, f"Expected 349 CPE3 tris, got {num_cpe3}"
    total = num_u1 + num_u2 + num_u3 + num_u4 + num_cpe4 + num_cpe3
    assert total == 41880, f"Expected 41,880 total layered elements, got {total}"

def test_f1758_pbs_script_directives_and_integrity():
    pbs_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "227_f1739_case1_adapted_fracture", "submit_f1758_case1_fracture.pbs")
    assert os.path.isfile(pbs_path), f"PBS script missing: {pbs_path}"
    with open(pbs_path, "r") as f:
        content = f.read()
    assert "#PBS -N PK_F1758_C1_FRAC" in content
    assert "#PBS -l select=1:ncpus=1:mem=16gb" in content
    assert "#PBS -q entry_imfdfkmq" in content
    assert "PK_F1758_CASE_1_PROD.inp" in content
    assert "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6" in content
    assert "job_notifications.sh" in content
    assert "trap" in content

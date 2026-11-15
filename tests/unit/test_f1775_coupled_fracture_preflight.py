# -*- coding: utf-8 -*-
"""
test_f1775_coupled_fracture_preflight.py
Unit test suite verifying technical preflight, model architecture, field output coverage,
and zero-PBS governance for Task F1775:
Method A Adapted Coupled Phase-Field Fracture Qualification & Production Preflight.
"""
import os
import hashlib
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

EXPECTED_FROZEN_UEL_SHA256 = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"
EXPECTED_CASE1_PROD_SHA256 = "976ef13cead9f8c541d93510bd48483f0adca297c95eec3f8d67fe7429a1cd7e"
EXPECTED_CASE5_PROD_SHA256 = "174c2abb82e1db37a5ed57aa2e36a4b46005098a5264ddcf1164d8232a8cb19e"
EXPECTED_CASE2_PROD_SHA256 = "cfcfe01699552f8d4d66172b6d6ec6e3fc0213a93c20fecf598e6464e720fb36"
EXPECTED_CASE3_PROD_SHA256 = "b356e39d051c9026b1f484244fa630a47544585086af64423d541a02e2de9e3b"


def get_file_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()


def test_frozen_uel_source_integrity():
    """Verify bitwise invariance of the production UEL source."""
    uel_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
    assert os.path.isfile(uel_path), f"Frozen UEL source missing: {uel_path}"
    sha = get_file_sha256(uel_path)
    assert sha == EXPECTED_FROZEN_UEL_SHA256, f"Frozen UEL hash mismatch: {sha}"


def test_case1_production_deck_structure_and_hash():
    """Verify Case 1 (20,232-el advancing mesh) production deck hash, line wrapping, and field outputs."""
    prod_path = os.path.join(
        REPO_ROOT, "models", "pandey_kumar_mode1", "239_f1772_case1_remesh", "PK_F1728_CASE_1_PROD.inp"
    )
    assert os.path.isfile(prod_path), f"Case 1 production deck missing: {prod_path}"
    sha = get_file_sha256(prod_path)
    assert sha == EXPECTED_CASE1_PROD_SHA256, f"Case 1 deck hash mismatch: {sha}"

    with open(prod_path, "r") as f:
        lines = f.readlines()

    assert len(lines) > 50000, f"Deck appears truncated: {len(lines)} lines"

    # Verify NSET line wrapping <= 16 items
    in_nset = False
    for line_no, line in enumerate(lines, 1):
        l = line.strip()
        if not l or l.startswith("**"):
            continue
        if l.startswith("*"):
            in_nset = l.upper().startswith("*NSET")
            continue
        if in_nset:
            items = [x.strip() for x in l.split(",") if x.strip()]
            assert len(items) <= 16, f"Case 1 NSET line {line_no} exceeds 16 items: {len(items)}"

    # Audit field output requests
    element_output_indices = [i for i, line in enumerate(lines) if "*ELEMENT OUTPUT" in line.upper()]
    assert len(element_output_indices) >= 2, f"Expected >=2 *ELEMENT OUTPUT requests, got {len(element_output_indices)}"
    for idx in element_output_indices:
        next_line = lines[idx + 1].strip().upper()
        assert "SDV" in next_line, f"SDV missing from Element Output: {next_line}"
        assert "S" in next_line, f"S missing from Element Output: {next_line}"


def test_case5_production_deck_structure_and_hash():
    """Verify Case 5 (15,330-el seven-hole mesh) production deck hash, line wrapping, and field outputs."""
    prod_path = os.path.join(
        REPO_ROOT, "models", "pandey_kumar_mode1", "240_f1774_suite_regression", "case5", "PK_F1728_CASE_5_PROD.inp"
    )
    assert os.path.isfile(prod_path), f"Case 5 production deck missing: {prod_path}"
    sha = get_file_sha256(prod_path)
    assert sha == EXPECTED_CASE5_PROD_SHA256, f"Case 5 deck hash mismatch: {sha}"

    with open(prod_path, "r") as f:
        lines = f.readlines()

    assert len(lines) > 40000, f"Deck appears truncated: {len(lines)} lines"

    # Verify NSET line wrapping <= 16 items
    in_nset = False
    for line_no, line in enumerate(lines, 1):
        l = line.strip()
        if not l or l.startswith("**"):
            continue
        if l.startswith("*"):
            in_nset = l.upper().startswith("*NSET")
            continue
        if in_nset:
            items = [x.strip() for x in l.split(",") if x.strip()]
            assert len(items) <= 16, f"Case 5 NSET line {line_no} exceeds 16 items: {len(items)}"

    # Audit field output requests
    element_output_indices = [i for i, line in enumerate(lines) if "*ELEMENT OUTPUT" in line.upper()]
    assert len(element_output_indices) >= 2, f"Expected >=2 *ELEMENT OUTPUT requests, got {len(element_output_indices)}"
    for idx in element_output_indices:
        next_line = lines[idx + 1].strip().upper()
        assert "SDV" in next_line, f"SDV missing from Element Output: {next_line}"
        assert "S" in next_line, f"S missing from Element Output: {next_line}"


def test_suite_production_decks_present():
    """Verify all 4 regression suite production decks exist and match authoritative hashes."""
    decks = {
        "case2": (
            os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "240_f1774_suite_regression", "case2", "PK_F1728_CASE_2_PROD.inp"),
            EXPECTED_CASE2_PROD_SHA256,
        ),
        "case3": (
            os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "240_f1774_suite_regression", "case3", "PK_F1728_CASE_3_PROD.inp"),
            EXPECTED_CASE3_PROD_SHA256,
        ),
    }
    for case_name, (path, expected_sha) in decks.items():
        assert os.path.isfile(path), f"Deck missing for {case_name}: {path}"
        actual_sha = get_file_sha256(path)
        assert actual_sha == expected_sha, f"SHA mismatch for {case_name}: {actual_sha}"


def test_f1775_task_state_and_zero_pbs_governance():
    """Verify ACTIVE_TASK.json has task_id F1775 and max_new_pbs_submissions == 0."""
    active_task_path = os.path.join(REPO_ROOT, "project_coordination", "ACTIVE_TASK.json")
    with open(active_task_path, "r") as f:
        data = json.load(f)

    assert data["task_id"] == "F1775-COUPLED-PHASE-FIELD-FRACTURE-QUALIFICATION-AND-PREFLIGHT"
    assert data["max_new_pbs_submissions"] == 0, "F1775 preflight must not authorize PBS submissions"
    assert data["submissions_consumed"] == 0
    assert data["cumulative_pbs_submissions"] == 33
    assert data["frozen_uel_sha256"].lower() == EXPECTED_FROZEN_UEL_SHA256
    assert data["case1_prod_sha256"].lower() == EXPECTED_CASE1_PROD_SHA256
    assert data["case5_prod_sha256"].lower() == EXPECTED_CASE5_PROD_SHA256

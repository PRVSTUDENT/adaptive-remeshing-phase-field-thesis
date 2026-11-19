"""Unit test suite for Method C Phase 3: Step-2 Forward Crack Propagation Package on Refined Mesh.
Verifies Job-3 continuation deck generation, multi-step loading schedule (Step-1 re-equilibration,
Step-2 forward propagation to u2=0.0100 mm), initial state preservation, authorization manifest,
crack propagation path towards central hole, and package report integrity.
"""
import os
import sys
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CASE_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "289_method_c_demo_case")
sys.path.insert(0, CASE_DIR)

import build_demo_propagation_job3_deck


def test_job3_deck_generation_and_integrity():
    deck_path, deck_sha, file_size = build_demo_propagation_job3_deck.build_job3_deck()
    assert os.path.isfile(deck_path), f"Job-3 deck missing: {deck_path}"
    assert file_size > 4000000, f"Deck file size too small: {file_size}"
    assert len(deck_sha) == 64

    with open(deck_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Model and heading assertions
    assert "PK_METHOD_C_DEMO_PROPAGATION_JOB3" in content
    assert "Step-2 Forward Crack Propagation" in content

    # 3-Layer element assertions
    assert "*USER ELEMENT, TYPE=U1" in content
    assert "*USER ELEMENT, TYPE=U2" in content
    assert "*USER ELEMENT, TYPE=U3" in content
    assert "*USER ELEMENT, TYPE=U4" in content
    assert "*ELEMENT, TYPE=CPE4, ELSET=UMAT_QUADS" in content
    assert "*ELEMENT, TYPE=CPE3, ELSET=UMAT_TRIS" in content

    # Initial conditions
    assert "*INITIAL CONDITIONS, TYPE=SOLUTION" in content
    # Ensure TYPE=DISPLACEMENT is NOT present (prevents Fatal Error 144)
    assert "*INITIAL CONDITIONS, TYPE=DISPLACEMENT" not in content

    # Step 1: Re-equilibration at u2 = 0.0050 mm
    assert "*STEP, NAME=Step-1-ReEquilibrate" in content
    assert "N_RP, 2, 2, 0.0050" in content

    # Step 2: Forward crack propagation to u2 = 0.0100 mm
    assert "*STEP, NAME=Step-2-Propagate" in content
    assert "*BOUNDARY, OP=MOD" in content
    assert "N_RP, 2, 2, 0.0100" in content
    assert "0.10, 1.0, 1.0E-08, 0.20" in content


def test_job3_manifest_and_authorization():
    manifest_path = os.path.join(CASE_DIR, "METHOD_C_DEMO_JOB3_AUTHORIZATION.json")
    assert os.path.isfile(manifest_path), f"Manifest missing: {manifest_path}"

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["task_id"] == "METHOD-C-PHASE3-FORWARD-PROPAGATION-PACKAGE"
    assert manifest["max_new_pbs_submissions"] == 0
    assert manifest["cumulative_pbs_submissions"] == 59
    assert manifest["frozen_uel_sha256"] == "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
    assert manifest["resource_limits"]["ncpus"] == 16
    assert manifest["resource_limits"]["mem_gb"] == 48


def test_job3_package_report_integrity():
    report_path = os.path.join(
        REPO_ROOT, "docs", "validation", "METHOD_C_PHASE3_FORWARD_PROPAGATION_PACKAGE_REPORT.md"
    )
    assert os.path.isfile(report_path), f"Report missing: {report_path}"

    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "PK_METHOD_C_DEMO_PROPAGATION_JOB3" in content
    assert "0.0050" in content
    assert "0.0100" in content
    assert "0.75" in content
    assert "NOTE-MC-J2-01" in content
    assert "530a0abb" in content
    assert "E75B82FC" in content
    assert "10,299" in content
    assert "30,897" in content

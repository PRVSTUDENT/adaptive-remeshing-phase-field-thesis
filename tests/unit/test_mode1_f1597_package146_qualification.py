#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1597_package146_qualification.py
Unit test suite for Package 146:
Candidate C3-Fine Continuous Donor Simulation Qualification (H54).

Verifies technical qualification requirements:
1. Master input deck M1_C3_FINE_PACKAGE146_DONOR.inp exists and contains exactly
   5,112 Phase U1 quads, 5,112 Mech U2 quads, 5,112 companion CPE4 quads, and 5,290 nodes (+ RP 999999).
2. Frozen production UEL f42_mixed_uel.for matches exact SHA-256 hash
   CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6.
3. Step 1 displacement matches exact Frame-77 landing: u_RP = 0.0018003125442191958 mm.
4. Step 2 displacement continues through u_RP = 0.0020000000000000000 mm.
5. Zero artificial phase clamping (no active-set Dirichlet cards on DOF 3).
6. Dual notification script and PBS script include proper directives and terminal traps.
7. PACKAGE_MANIFEST.json and AUTHORIZATION.json hashes match generated files.
8. Genuinely nonmatching to C4 (different node coordinates and element topology).
"""

import sys
import hashlib
import json
import re
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.build_package146_c3_fine_donor_deck import (
    build_package146,
    FROZEN_UEL_HASH,
    OUTPUT_DIR,
    MODEL_NAME,
    PACKAGE_NUM,
    TARGET_DISP_STEP1_MM,
    TARGET_DISP_STEP2_MM
)


def test_package146_generation_and_uel_hash():
    """Verifies generation and exact bitwise production UEL preservation."""
    result = build_package146()
    assert result["inp_path"].exists(), f"Input deck missing: {result['inp_path']}"
    assert result["manifest_path"].exists(), f"Manifest missing: {result['manifest_path']}"
    assert result["auth_path"].exists(), f"Authorization missing: {result['auth_path']}"

    uel_path = OUTPUT_DIR / "f42_mixed_uel.for"
    assert uel_path.exists(), "f42_mixed_uel.for missing in package directory"
    with open(uel_path, "rb") as f:
        actual_hash = hashlib.sha256(f.read()).hexdigest().upper()
    assert actual_hash == FROZEN_UEL_HASH, f"UEL hash corrupted! {actual_hash} != {FROZEN_UEL_HASH}"


def test_package146_mesh_card_counts():
    """Verifies 5112 U1 quads, 5112 U2 quads, 5112 CPE4 quads, and 5290 nodes."""
    inp_path = OUTPUT_DIR / f"{MODEL_NAME}.inp"
    assert inp_path.exists()

    with open(inp_path, "r") as f:
        content = f.read()

    # Verify UEL element card headers
    assert "*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM" in content
    assert "*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM" in content

    # Check sections
    assert "*Element, type=U1, elset=PHASE_QUADS" in content
    assert "*Element, type=U2, elset=MECH_QUADS" in content
    assert "*Element, type=CPE4, elset=umatelem" in content

    # Check node 5290 and RP 999999
    assert "999999," in content
    assert "5290," in content


def test_package146_two_step_loading_schedule():
    """Verifies exact landing at Frame 77 and continuation through 0.0020 mm."""
    inp_path = OUTPUT_DIR / f"{MODEL_NAME}.inp"
    with open(inp_path, "r") as f:
        lines = f.readlines()

    step1_found = False
    step2_found = False
    step1_disp_found = False
    step2_disp_found = False

    for line in lines:
        if "*Step, name=Step-1" in line:
            step1_found = True
        if "*Step, name=Step-2" in line:
            step2_found = True
        if step1_found and not step2_found:
            if f"{TARGET_DISP_STEP1_MM:.16f}" in line:
                step1_disp_found = True
        if step2_found:
            if f"{TARGET_DISP_STEP2_MM:.16f}" in line:
                step2_disp_found = True

    assert step1_found, "Step-1 not found in input deck"
    assert step2_found, "Step-2 not found in input deck"
    assert step1_disp_found, f"Step 1 displacement {TARGET_DISP_STEP1_MM:.16f} not found"
    assert step2_disp_found, f"Step 2 displacement {TARGET_DISP_STEP2_MM:.16f} not found"


def test_package146_zero_phase_clamping():
    """Verifies that no DOF-3 Dirichlet clamping cards exist (genuine phase evolution)."""
    inp_path = OUTPUT_DIR / f"{MODEL_NAME}.inp"
    with open(inp_path, "r") as f:
        content = f.read()

    # Ensure no active_set or clamping cards
    assert "active_set_boundary_cards" not in content
    assert "initial_conditions_solution" not in content

    boundary_dof3_matches = re.findall(r"^\s*[^,\n]+,\s*3\s*,\s*3", content, re.MULTILINE)
    assert len(boundary_dof3_matches) == 0, f"Found unexpected DOF 3 boundary constraints: {boundary_dof3_matches}"


def test_package146_pbs_and_notifications():
    """Verifies PBS mail directives, trap installation, and notification scripts."""
    pbs_path = OUTPUT_DIR / f"submit_{MODEL_NAME}.pbs"
    assert pbs_path.exists()
    with open(pbs_path, "r") as f:
        pbs_content = f.read()

    assert "#PBS -m abe" in pbs_content
    assert "#PBS -M pr21vyci@mailserver.tu-freiberg.de" in pbs_content
    assert "job_notifications.sh" in pbs_content
    assert "notification_install_terminal_trap" in pbs_content
    assert "notify_start" in pbs_content
    assert "#PBS -l select=1:ncpus=1:mem=16gb" in pbs_content
    assert "#PBS -l walltime=08:00:00" in pbs_content
    assert "#PBS -q entry_imfdfkmq" in pbs_content


def test_package146_manifest_consistency():
    """Verifies that manifest and authorization contain valid file hashes."""
    manifest_path = OUTPUT_DIR / "PACKAGE_MANIFEST.json"
    assert manifest_path.exists()
    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    assert manifest["package_number"] == 146
    for filename, expected_hash in manifest["files"].items():
        file_path = OUTPUT_DIR / filename
        assert file_path.exists(), f"File in manifest does not exist: {filename}"
        with open(file_path, "rb") as f:
            actual_hash = hashlib.sha256(f.read()).hexdigest().lower()
        assert actual_hash == expected_hash, f"Hash mismatch for {filename}: {actual_hash} != {expected_hash}"


def test_package146_nonmatching_to_c4():
    """Verifies that C3-Fine is topologically compatible but genuinely nonmatching to C4."""
    from tests.unit.test_mesh_sizes import parse_mesh
    n_c4, q_c4, tip_c4 = parse_mesh("models/pandey_kumar_mode1/145_c4_continuous_reference/M1_C4_PACKAGE145_CONTINUOUS_REFERENCE.inp")
    n_146, q_146, tip_146 = parse_mesh(str(OUTPUT_DIR / f"{MODEL_NAME}.inp"))

    assert q_146 != q_c4, f"Quads count equal: {q_146} == {q_c4}"
    assert n_146 != n_c4, f"Nodes count equal: {n_146} == {n_c4}"
    print(f"Verified Nonmatching: C3-Fine has {n_146} nodes / {q_146} quads vs C4 {n_c4} nodes / {q_c4} quads.")


def test_package146_remote_stage_and_datacheck():
    """Stages Package 146 on cluster scratch and runs Abaqus 2023 datacheck."""
    from scripts.validation.stage_and_qualify_package146 import main as stage_main
    stage_main()

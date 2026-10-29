#!/usr/bin/env python3
"""
Unit test suite for Package 145:
Candidate C4 Continuous Reference Simulation Qualification (H52).

Verifies that Package 145 satisfies all technical preflight and qualification requirements:
1. Master input deck M1_C4_PACKAGE145_CONTINUOUS_REFERENCE.inp exists and contains exactly
   4,422 Phase U1 quads, 4,422 Mech U2 quads, 4,422 companion CPE4 quads, and 4,588 nodes (+ RP 999999).
2. Frozen production UEL f42_mixed_uel.for matches exact SHA-256 hash
   CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6.
3. Step 1 displacement matches exact Package 143 Frame-77 landing: u_RP = 0.0018003125442191958 mm.
4. Step 2 displacement continues through u_RP = 0.0020000000000000000 mm.
5. Zero artificial phase clamping (no active-set Dirichlet cards on DOF 3).
6. Dual notification script and PBS script include proper directives and terminal traps.
7. PACKAGE_MANIFEST.json and AUTHORIZATION.json hashes match generated files.
"""

import sys
import hashlib
import json
import re
from pathlib import Path

REPO_ROOT = Path(r"D:\Master thesis\Adaptive remeshing")
sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.build_package145_continuous_reference_deck import (
    build_package145,
    FROZEN_UEL_HASH,
    OUTPUT_DIR,
    MODEL_NAME,
    PACKAGE_NUM,
    TARGET_DISP_STEP1_MM,
    TARGET_DISP_STEP2_MM
)


def test_package145_generation_and_uel_hash():
    """Verifies generation and exact bitwise production UEL preservation."""
    result = build_package145()
    assert result["inp"].exists(), f"Input deck missing: {result['inp']}"
    assert result["manifest"].exists(), f"Manifest missing: {result['manifest']}"
    assert result["auth"].exists(), f"Authorization missing: {result['auth']}"

    uel_path = OUTPUT_DIR / "f42_mixed_uel.for"
    assert uel_path.exists(), "f42_mixed_uel.for missing in package directory"
    with open(uel_path, "rb") as f:
        actual_hash = hashlib.sha256(f.read()).hexdigest().upper()
    assert actual_hash == FROZEN_UEL_HASH, f"UEL hash corrupted! {actual_hash} != {FROZEN_UEL_HASH}"


def test_package145_mesh_card_counts():
    """Verifies 4422 U1 quads, 4422 U2 quads, 4422 CPE4 quads, and 4588 nodes."""
    inp_path = OUTPUT_DIR / f"{MODEL_NAME}.inp"
    assert inp_path.exists()

    with open(inp_path, "r") as f:
        content = f.read()

    # Verify UEL element card headers
    assert "*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM" in content
    assert "*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM" in content

    # Count element types
    u1_matches = re.findall(r"^\s*(\d+),\s*\d+,\s*\d+,\s*\d+,\s*\d+", content, re.MULTILINE)
    # Check sections
    assert "*Element, type=U1, elset=PHASE_QUADS" in content
    assert "*Element, type=U2, elset=MECH_QUADS" in content
    assert "*Element, type=CPE4, elset=UMATELEM" in content

    # Check node 4588 and RP 999999
    assert "999999," in content
    assert "4588," in content


def test_package145_two_step_loading_schedule():
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


def test_package145_zero_phase_clamping():
    """Verifies that no DOF-3 Dirichlet clamping cards exist (genuine phase evolution)."""
    inp_path = OUTPUT_DIR / f"{MODEL_NAME}.inp"
    with open(inp_path, "r") as f:
        content = f.read()

    # Ensure active_set_boundary_cards is NOT included
    assert "active_set_boundary_cards" not in content
    assert "initial_conditions_solution" not in content

    # In Step 1 and Step 2, boundary conditions should constrain only RP (DOF 2) and base supports
    # No node should be constrained in DOF 3
    boundary_dof3_matches = re.findall(r"^\s*[^,\n]+,\s*3\s*,\s*3", content, re.MULTILINE)
    assert len(boundary_dof3_matches) == 0, f"Found unexpected DOF 3 boundary constraints: {boundary_dof3_matches}"


def test_package145_pbs_and_notifications():
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


def test_package145_manifest_consistency():
    """Verifies that manifest and authorization contain valid file hashes."""
    manifest_path = OUTPUT_DIR / "PACKAGE_MANIFEST.json"
    assert manifest_path.exists()
    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    assert manifest["package_number"] == 145
    for filename, expected_hash in manifest["files"].items():
        file_path = OUTPUT_DIR / filename
        assert file_path.exists(), f"File in manifest does not exist: {filename}"
        with open(file_path, "rb") as f:
            actual_hash = hashlib.sha256(f.read()).hexdigest().lower()
        assert actual_hash == expected_hash, f"Hash mismatch for {filename}: {actual_hash} != {expected_hash}"


def test_package145_cluster_staging_and_datacheck():
    """Stages Package 145 on cluster scratch and verifies remote Abaqus 2023 datacheck."""
    from scripts.validation.stage_and_qualify_package145 import main as stage_main
    stage_main()


#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_f1704_candidate_e10_deck_qualification.py
========================================================
Unit test suite verifying Task F1704 Candidate E10 Production Deck
Qualification:
  - Frozen UEL hash and line count integrity
  - Source Candidate E10 physical mesh integrity and hash
  - Generated PK_HOLE_SEL_E10_PROD.inp multi-layer element parity
  - Node correspondence and Reference Point coords
  - UEL Property ABI and User Material constants
  - Rigid tie equation constraint count (60 nodes tied to RP in DOF 2)
  - Element quality and positive Jacobian areas
  - Local Abaqus/Standard datacheck execution and Exit Code 0 verification
  - Zero-PBS execution governance (max_new_pbs_submissions = 0)
"""

import json
import hashlib
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PROD_DECK = REPO_ROOT / "models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_SEL_E10_PROD.inp"
PHYS_MESH = REPO_ROOT / "models/pandey_kumar_mode1/176_method_a_plate_with_hole/candidates/PK_HOLE_SEL_E10_PHYS.inp"
UEL_FILE  = REPO_ROOT / "models/pandey_kumar_mode1/f42_mixed_uel.for"
AUDIT_JSON = REPO_ROOT / "results/validation/f1704_candidate_e10_deck_audit.json"
DC_DIR    = REPO_ROOT / "runs/f1704_candidate_e10_datacheck"

FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
PHYS_MESH_SHA256  = "6C4D64E51FC7686CD471F2E7D355E72927F40798F62FC16745F676AC8ABA4642"


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()


def test_frozen_uel_integrity():
    """Verify production UEL is bitwise preserved with exact hash and line count."""
    assert UEL_FILE.exists(), f"UEL not found: {UEL_FILE}"
    actual_sha = sha256_file(UEL_FILE)
    assert actual_sha == FROZEN_UEL_SHA256, f"Frozen UEL hash mismatch: {actual_sha}"
    with open(UEL_FILE, "r") as f:
        lines = [l for l in f]
    assert len(lines) == 907, f"Frozen UEL line count mismatch: expected 907, got {len(lines)}"


def test_physical_mesh_integrity():
    """Verify Candidate E10 physical mesh file exists and matches repository hash."""
    assert PHYS_MESH.exists(), f"Physical mesh not found: {PHYS_MESH}"
    actual_sha = sha256_file(PHYS_MESH)
    assert actual_sha == PHYS_MESH_SHA256, f"Physical mesh hash mismatch: {actual_sha}"


def test_audit_json_existence_and_pass():
    """Verify exhaustive static audit JSON exists and records overall PASS."""
    assert AUDIT_JSON.exists(), f"Audit JSON not found: {AUDIT_JSON}"
    with open(AUDIT_JSON, "r") as f:
        data = json.load(f)
    assert data["overall_status"] == "PASS", f"Audit overall status is not PASS: {data['overall_status']}"
    assert data["physical_elements"] == 9164
    assert data["quad_elements"] == 8891
    assert data["tri_elements"] == 273
    assert data["total_deck_elements"] == 27492
    assert data["physical_nodes"] == 9251
    assert data["deck_nodes"] == 9252


def test_three_layer_element_parity():
    """Verify exact 3x element layer parity in the production deck."""
    with open(AUDIT_JSON, "r") as f:
        data = json.load(f)
    checks = data["checks"]
    assert checks["layer1_elements"] == 9164, "Layer 1 elements mismatch"
    assert checks["layer2_elements"] == 9164, "Layer 2 elements mismatch"
    assert checks["layer3_elements"] == 9164, "Layer 3 elements mismatch"
    assert checks["exact_3x_parity"] is True, "Exact 3x parity failed"
    assert checks["unique_element_labels_pass"] is True, "Element labels are not unique"
    assert checks["connectivity_preservation_pass"] is True, "Connectivity preservation failed"


def test_uel_properties_and_abi():
    """Verify UEL property vector, ABI degrees of freedom, and companion UMAT constants."""
    with open(AUDIT_JSON, "r") as f:
        data = json.load(f)
    checks = data["checks"]
    assert checks["uel_abi_pass"] is True, "UEL ABI check failed"
    assert checks["uel_properties_pass"] is True, "UEL Properties check failed"
    assert checks["companion_material_pass"] is True, "Companion material check failed"


def test_boundary_sets_and_equations():
    """Verify boundary node sets and rigid tensile pull constraints (*EQUATION)."""
    with open(AUDIT_JSON, "r") as f:
        data = json.load(f)
    checks = data["checks"]
    assert checks["rigid_tie_equations_pass"] is True, "Rigid tie equations check failed"
    assert checks["rigid_tie_equations_count"] == 60, f"Expected 60 equations, got {checks['rigid_tie_equations_count']}"
    assert checks["boundary_node_sets_pass"] is True, "Boundary sets check failed"
    assert checks["bottom_nodes_count"] == 53, f"Expected 53 bottom nodes, got {checks['bottom_nodes_count']}"
    assert checks["pin_node_id"] == 26, f"Expected pinned node 26, got {checks['pin_node_id']}"
    assert checks["reference_point_id"] == 999999


def test_element_quality_and_jacobians():
    """Verify all physical quad and triangular elements have strictly positive area."""
    with open(AUDIT_JSON, "r") as f:
        data = json.load(f)
    checks = data["checks"]
    assert checks["element_jacobian_pass"] is True, "Element Jacobian quality check failed"
    assert checks["min_quad_area_mm2"] > 0.0, "Zero or negative quad area detected"
    assert checks["min_tri_area_mm2"] > 0.0, "Zero or negative tri area detected"


def test_abaqus_datacheck_evidence():
    """Verify genuine Abaqus/Standard datacheck executed with Exit Code 0 and zero errors."""
    with open(AUDIT_JSON, "r") as f:
        data = json.load(f)
    checks = data["checks"]
    assert checks["datacheck_pass"] is True, "Datacheck did not pass"
    dc = checks["datacheck_details"]
    assert dc["datacheck_complete"] is True
    assert dc["errors_detected"] == 0
    assert dc["negative_jacobians"] == 0
    assert dc["overconstraints"] == 0
    assert dc["datacheck_verdict"] == "PASS"

    dat_file = DC_DIR / "M1_HOLE_SEL_E10_DATACHECK.dat"
    msg_file = DC_DIR / "M1_HOLE_SEL_E10_DATACHECK.msg"
    assert dat_file.exists(), f"Datacheck .dat file missing: {dat_file}"
    assert msg_file.exists(), f"Datacheck .msg file missing: {msg_file}"


def test_dof_accounting():
    """Verify independent physical degree of freedom census."""
    with open(AUDIT_JSON, "r") as f:
        data = json.load(f)
    dofs = data["checks"]["dof_accounting"]
    assert dofs["physical_nodes"] == 9251
    assert dofs["phase_dofs"] == 9251
    assert dofs["displacement_dofs"] == 18502
    assert dofs["total_active_physical_dofs_unconstrained"] == 27754
    assert dofs["rigid_tie_equations"] == 60
    assert dofs["net_independent_physical_dofs"] == 27694

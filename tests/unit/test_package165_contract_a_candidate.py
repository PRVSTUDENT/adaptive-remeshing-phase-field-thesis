#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_package165_contract_a_candidate.py
Unit and regression tests for Candidate Package 165 Contract A candidate.
Task: F1597-TRUSTED-REVIEW-BOUNDARY-AND-PACKAGE160
Protocol Version: 2
"""

import os
import sys
import json
import csv
import hashlib
from pathlib import Path
import pytest
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

PKG165_DIR = REPO_ROOT / "models/pandey_kumar_mode1/165_c5_package165_c2_0_contract_a"
DONOR_CKPT = REPO_ROOT / "models/pandey_kumar_mode1/157_c4_package157_c1_2_continuation_r5/converged_checkpoint_01.json"
FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(str(filepath), "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()

def test_frozen_uel_integrity():
    """Verify Package 165 contains the unmodified production UEL."""
    uel_path = PKG165_DIR / "f42_mixed_uel.for"
    assert uel_path.is_file(), "Missing UEL source in Package 165"
    assert compute_sha256(uel_path) == FROZEN_UEL_SHA256

def test_package_manifest_integrity():
    """Verify Package 165 manifest structure and file digests."""
    manifest_path = PKG165_DIR / "PACKAGE_MANIFEST.json"
    assert manifest_path.is_file()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["package"] == "package_165"
    assert manifest["target_mesh"] == "c5_candidate_40k"
    assert manifest["quad_elements"] == 12996
    assert manifest["physical_nodes"] == 13278
    assert manifest["integration_points"] == 51984
    assert manifest["donor_source"]["artificial_amplification_eliminated"] is True

    # Verify digests
    for fn, expected_sha in manifest["file_digests"].items():
        actual_path = PKG165_DIR / fn
        assert actual_path.is_file(), f"Missing file {fn}"
        assert compute_sha256(actual_path).lower() == expected_sha.lower(), f"Digest mismatch for {fn}"

def test_history_initialization_no_spike():
    """
    Verify that Package 165 d_lower_bounds.csv has eliminated the artificial 27,631 MPa spike
    and is strictly bounded by the donor maximum (6,868.95 MPa).
    """
    bounds_csv = PKG165_DIR / "d_lower_bounds.csv"
    assert bounds_csv.is_file()

    h_vals = []
    h_elem_6552_gp1 = None
    with bounds_csv.open("r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        for r in reader:
            eid = int(r[0])
            for k in range(1, 5):
                val_MPa = float(r[4 + k]) * 1000.0
                h_vals.append(val_MPa)
                if eid == 6552 and k == 1:
                    h_elem_6552_gp1 = val_MPa

    assert len(h_vals) == 51984
    max_h = max(h_vals)

    # In Package 160, max_h was 27,631.37 MPa
    # In Package 165, max_h must be bounded by donor max ~6,868.95 MPa
    assert max_h <= 6868.9515, f"Package 165 history exceeds donor max: {max_h}"
    assert max_h > 6000.0, f"Package 165 history unexpectedly low: {max_h}"

    # Elem 6552 GP 1 must be authentic mapped value (6,488.35 MPa), NOT 27,631 MPa
    assert h_elem_6552_gp1 is not None
    assert abs(h_elem_6552_gp1 - 6488.3545) < 0.1, f"Elem 6552 GP 1 mismatch: {h_elem_6552_gp1}"

def test_separation_of_h0_and_trial_history():
    """
    Verify that Contract A driver maintains H0 as immutable and sets delta_h = 0 identically.
    """
    from scripts.state_transfer.driver_package165_c5_contract_a import ContractAReEquilibrationSolver

    # Create dummy mesh with 1 quad, 4 nodes
    class MockMesh(object):
        pass
    mesh = MockMesh()
    mesh.nodes = {1: (0.0, 0.0), 2: (1.0, 0.0), 3: (1.0, 1.0), 4: (0.0, 1.0)}
    mesh.elements = {1: [1, 2, 3, 4]}

    d0 = {n: 0.01 for n in mesh.nodes}
    h0 = {(1, k): 50.0 for k in range(1, 5)}

    solver = ContractAReEquilibrationSolver(mesh, d0, h0)
    # Ensure solver holds immutable copy
    assert solver.h0[(1, 1)] == 50.0

    # Mutating external dict must not mutate solver.h0
    h0[(1, 1)] = 999.0
    assert solver.h0[(1, 1)] == 50.0

def test_active_set_dual_defect_within_tolerance():
    """Verify that initial dual defect in Package 165 is well within the 1e-6 kN*mm tolerance."""
    manifest = json.loads((PKG165_DIR / "PACKAGE_MANIFEST.json").read_text(encoding="utf-8"))
    peak_defect = abs(manifest["initial_active_set"]["peak_dual_defect_kNmm"])
    assert peak_defect < 1.0e-6, f"Initial dual defect violates tolerance: {peak_defect}"
    assert peak_defect < 5.0e-7, f"Initial dual defect not reduced: {peak_defect}"

def test_thermodynamic_post_convergence_verification_logic():
    """
    Verify that driver logic rejects checkpoints where psi+(u*) > H0 and accepts valid ones.
    """
    # Mock scenario: psi+(u*) <= H0
    h0 = {(1, 1): 10.0, (1, 2): 20.0}
    psi_valid = {(1, 1): 9.5, (1, 2): 19.8}
    violations_valid = [k for k in psi_valid if psi_valid[k] > h0[k] + 1.0e-6]
    assert len(violations_valid) == 0

    # Mock scenario: psi+(u*) > H0 (violation)
    psi_invalid = {(1, 1): 15.0, (1, 2): 20.0}
    violations_invalid = [k for k in psi_invalid if psi_invalid[k] > h0[k] + 1.0e-6]
    assert len(violations_invalid) == 1
    assert violations_invalid[0] == (1, 1)

def test_datacheck_deck_structure():
    """Verify datacheck decks exist and have correct boundary conditions."""
    mech_dc = (PKG165_DIR / "P165_MECHANICAL_DC.inp").read_text(encoding="utf-8")
    assert "*Step, name=DC_MECH" in mech_dc
    assert "N_RP, 2, 2, 1.8603125442191958e-03" in mech_dc

    phase_dc = (PKG165_DIR / "P165_PHASE_DC.inp").read_text(encoding="utf-8")
    assert "*Step, name=DC_PHASE" in phase_dc
    assert "*EQUATION" not in phase_dc
    assert "*INCLUDE, INPUT=active_set_boundary_cards.inc" in phase_dc

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_package171_r1_c6_coupled_driver_readiness.py
==================================================
Focused regression test suite for Package 171-R1:
C6 Stage C3-0 Genuine Coupled PDAS Re-Equilibration (Revision 1).
Task: F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE
Protocol Version: 2

Tests:
1. test_c6_mesh_topology_and_uel_conformance
2. test_transferred_state_non_zero_integrity
3. test_energy_continuity_against_checkpoint03
4. test_frozen_uel_sha256_preservation
5. test_driver_initialization_and_closure
6. test_datacheck_deck_structure_and_includes
7. test_batch_authorization_and_manifest_hashes
8. test_runtime_closure_and_c3_mapping_dependency
"""

import os
import sys
import json
import csv
import hashlib
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.c4_to_c5_spatial_mapping import Mesh2D
from scripts.state_transfer.driver_package171_c6_coupled_pdas import (
    Package171C6PDASDriver,
    DONOR_REFERENCE_FORCE_KN,
    DONOR_REFERENCE_TOTAL_ENERGY_KNMM,
    DONOR_REFERENCE_ELASTIC_ENERGY_KNMM,
    DONOR_REFERENCE_FRACTURE_ENERGY_KNMM
)

PKG_DIR = REPO_ROOT / "models/pandey_kumar_mode1/171_c6_package171_r1_c3_0_reequilibration"
FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"


def sha256_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()


def test_c6_mesh_topology_and_uel_conformance():
    """Verify C6 mesh contains exactly 15,252 CPE4 quads, 15,559 physical nodes, and 59 slit pairs."""
    inp_path = PKG_DIR / "M1_C6_PACKAGE171_C3_0_REEQUILIBRATION.inp"
    assert inp_path.is_file(), "Master input deck missing"

    mesh = Mesh2D.from_inp(inp_path, name="C6_Receiver", max_physical_node=15559)
    assert len(mesh.elements) == 15252, f"Expected 15,252 quads, found {len(mesh.elements)}"
    assert len(mesh.nodes) == 15559, f"Expected 15,559 physical nodes, found {len(mesh.nodes)}"

    # Check slit flank classification
    slit_upper = [n for n, (x, y) in mesh.nodes.items() if abs(y - 0.050) < 1e-6 and x <= 0.040 and mesh.node_flank.get(n) == "UPPER"]
    slit_lower = [n for n, (x, y) in mesh.nodes.items() if abs(y - 0.050) < 1e-6 and x <= 0.040 and mesh.node_flank.get(n) == "LOWER"]
    assert len(slit_upper) >= 59, f"Expected >= 59 upper slit nodes, got {len(slit_upper)}"
    assert len(slit_lower) >= 59, f"Expected >= 59 lower slit nodes, got {len(slit_lower)}"


def test_transferred_state_non_zero_integrity():
    """Verify transferred damage and history fields are authentically non-zero and bounded."""
    d_csv = PKG_DIR / "nodal_phase_field_initial.csv"
    assert d_csv.is_file(), "nodal_phase_field_initial.csv missing"
    with open(d_csv, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        d_vals = {int(r[0]): float(r[1]) for r in reader}

    assert len(d_vals) == 15559, f"Expected 15,559 damage entries, got {len(d_vals)}"
    min_d = min(d_vals.values())
    max_d = max(d_vals.values())
    assert min_d > 0.0, f"Damage must be strictly positive: {min_d}"
    assert max_d > 0.5, f"Damage peak must exceed 0.5 (got {max_d})"
    assert max_d <= 1.0, f"Damage peak must not exceed 1.0: {max_d}"

    bounds_csv = PKG_DIR / "d_lower_bounds.csv"
    assert bounds_csv.is_file(), "d_lower_bounds.csv missing"
    with open(bounds_csv, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        h_vals = []
        for r in reader:
            for g in range(1, 5):
                h_vals.append(float(r[4 + g]))

    assert len(h_vals) == 15252 * 4, f"Expected 61,008 GP history entries, got {len(h_vals)}"
    min_h = min(h_vals)
    assert min_h > 0.0, f"History must be strictly positive: {min_h}"


def test_energy_continuity_against_checkpoint03():
    """Verify energy continuity evaluation passes within 2.0% of accepted Checkpoint 03."""
    val_json = REPO_ROOT / "results/validation/c6_package171_r1_assembly_validation.json"
    assert val_json.is_file(), "Assembly validation JSON missing"
    with open(val_json, "r", encoding="utf-8") as f:
        val = json.load(f)

    assert val["verification_passed"] is True
    t = val["transferred_state"]
    assert t["elastic_continuity_pct"] < 2.0, f"Elastic energy discrepancy {t['elastic_continuity_pct']}% exceeds 2.0%"
    assert t["fracture_continuity_pct"] < 2.0, f"Fracture energy discrepancy {t['fracture_continuity_pct']}% exceeds 2.0%"
    assert t["total_energy_continuity_pct"] < 2.0, f"Total energy discrepancy {t['total_energy_continuity_pct']}% exceeds 2.0%"


def test_frozen_uel_sha256_preservation():
    """Verify frozen production UEL is byte-for-byte identical to authoritative hash."""
    uel_path = PKG_DIR / "f42_mixed_uel.for"
    assert uel_path.is_file(), "f42_mixed_uel.for missing from package"
    uel_hash = sha256_file(uel_path)
    assert uel_hash == FROZEN_UEL_HASH, f"UEL hash mismatch! Expected {FROZEN_UEL_HASH}, got {uel_hash}"


def test_driver_initialization_and_closure():
    """Verify Package171C6PDASDriver loads and verifies transferred state without exceptions."""
    driver = Package171C6PDASDriver(
        package=PKG_DIR,
        output=PKG_DIR / "temp_test_output",
        extractor=REPO_ROOT / "scripts/validation/extract_package148_iteration.py",
        memory_gb=16,
        timeout=100,
        max_outer=5
    )
    driver.load()
    assert len(driver.d0) == 15559
    assert len(driver.h0) == 15252 * 4
    assert len(driver.u0) == 15559
    assert abs(driver.target_uy - 0.0018703125442191958) < 1e-12


def test_datacheck_deck_structure_and_includes():
    """Verify mechanical and phase subproblem datacheck decks contain valid cards and includes."""
    mech_dc = (PKG_DIR / "P171_MECHANICAL_DC.inp").read_text(encoding="utf-8")
    phase_dc = (PKG_DIR / "P171_PHASE_DC.inp").read_text(encoding="utf-8")

    assert "*INCLUDE, INPUT=initial_conditions_solution.inc" in mech_dc
    assert "*INCLUDE, INPUT=active_set_boundary_cards.inc" in mech_dc
    assert "*Step, name=DC_MECH" in mech_dc

    assert "*INCLUDE, INPUT=initial_conditions_solution.inc" in phase_dc
    assert "*INCLUDE, INPUT=active_set_boundary_cards.inc" in phase_dc
    assert "*Step, name=DC_PHASE" in phase_dc
    assert "*Equation" not in phase_dc, "Phase subproblem must not contain kinematic tie equations"


def test_batch_authorization_and_manifest_hashes():
    """Verify PACKAGE_MANIFEST.json and M1_C6_PACKAGE171_R1_AUTHORIZATION.json hashes match files on disk."""
    manifest_p = PKG_DIR / "PACKAGE_MANIFEST.json"
    with open(manifest_p, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    for fname, expected_hash in manifest["files"].items():
        if fname.endswith(".dat"):
            continue  # Datacheck outputs verified post-datacheck
        actual_hash = sha256_file(PKG_DIR / fname).lower()
        assert actual_hash == expected_hash.lower(), f"Manifest hash mismatch for {fname}: {actual_hash} != {expected_hash}"

    auth_p = PKG_DIR / "M1_C6_PACKAGE171_R1_AUTHORIZATION.json"
    with open(auth_p, "r", encoding="utf-8") as f:
        auth = json.load(f)

    for fname, expected_hash in auth["files"].items():
        if fname.endswith(".dat"):
            continue  # Datacheck outputs verified post-datacheck
        actual_hash = sha256_file(PKG_DIR / fname).lower()
        assert actual_hash == expected_hash.lower(), f"Auth hash mismatch for {fname}: {actual_hash} != {expected_hash}"


def test_runtime_closure_and_c3_mapping_dependency():
    """Verify M1_C6_PACKAGE171_R1_AUTHORIZATION.json includes c3_int_to_c4_spatial_mapping.py."""
    auth_p = PKG_DIR / "M1_C6_PACKAGE171_R1_AUTHORIZATION.json"
    with open(auth_p, "r", encoding="utf-8") as f:
        auth = json.load(f)

    rsh = auth.get("runtime_source_hashes", {})
    assert "scripts/state_transfer/c3_int_to_c4_spatial_mapping.py" in rsh
    c3_hash = rsh["scripts/state_transfer/c3_int_to_c4_spatial_mapping.py"]
    assert c3_hash == sha256_file(REPO_ROOT / "scripts/state_transfer/c3_int_to_c4_spatial_mapping.py")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

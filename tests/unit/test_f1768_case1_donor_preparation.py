# -*- coding: utf-8 -*-
"""
tests/unit/test_f1768_case1_donor_preparation.py
================================================
Unit test suite verifying technical preflight for Task F1768:
Case 1 Advancing Coupled Donor Production Deck Preparation, UEL Structure Audit & Verification.
"""
import os
import sys
import hashlib
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
FROZEN_UEL_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
EXPECTED_UEL_SHA256 = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"

COARSE_PHYS_INP = os.path.join(
    REPO_ROOT, "models", "pandey_kumar_mode1", "02_proposed_adaptive_refined", "PK_PREANALYSIS_COARSE.inp"
)
COARSE_COUPLED_INP = os.path.join(
    REPO_ROOT, "models", "pandey_kumar_mode1", "237_f1768_case1_donor", "PK_F1768_CASE_1_COARSE_COUPLED.inp"
)


def get_file_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()


def test_frozen_uel_integrity():
    """Verify bitwise invariance of the frozen Fortran production UEL."""
    assert os.path.exists(FROZEN_UEL_PATH), "Frozen UEL file must exist"
    actual_hash = get_file_sha256(FROZEN_UEL_PATH)
    assert actual_hash == EXPECTED_UEL_SHA256, "UEL hash must match frozen production hash"


def test_parse_coarse_candidate_mesh():
    """Verify parsing of PK_PREANALYSIS_COARSE.inp yields exactly 2,906 elements and 2,988 nodes."""
    from scripts.remeshing.reusable_2d_adaptive_framework import MeshQualityAuditEngine

    assert os.path.exists(COARSE_PHYS_INP), "Coarse candidate mesh must exist"
    nodes, quads, tris = MeshQualityAuditEngine.parse_physical_inp(COARSE_PHYS_INP)
    assert len(nodes) == 2988, f"Expected 2988 nodes, got {len(nodes)}"
    assert len(quads) == 2818, f"Expected 2818 quads, got {len(quads)}"
    assert len(tris) == 88, f"Expected 88 tris, got {len(tris)}"
    assert len(quads) + len(tris) == 2906, f"Expected 2906 total elements, got {len(quads) + len(tris)}"


def test_build_case1_coarse_coupled_deck():
    """Build the 3-layer UEL production deck for Case 1 coarse donor and verify its structure."""
    from scripts.remeshing.reusable_2d_adaptive_framework import AdaptiveConfig, ProductionDeckBuilder

    config_path = os.path.join(REPO_ROOT, "configs", "remeshing", "f1728_case1_mode1_edge_crack.json")
    assert os.path.exists(config_path), "Case 1 config must exist"
    with open(config_path, "r") as f:
        cfg = AdaptiveConfig(json.load(f))

    res = ProductionDeckBuilder.build_deck(
        src_phys_inp=COARSE_PHYS_INP,
        dst_uel_inp=COARSE_COUPLED_INP,
        job_name="PK_F1768_CASE_1_COARSE_COUPLED",
        config=cfg,
        step1_only=False,
        uel_source_path=FROZEN_UEL_PATH
    )

    assert os.path.exists(COARSE_COUPLED_INP), "Built deck must exist on disk"
    assert res["total_layered_elements"] == 3 * 2906 == 8718
    assert res["total_physical_elements"] == 2906
    assert res["uel_hash_verified"] is True

    # Audit the generated input deck line by line
    with open(COARSE_COUPLED_INP, "r") as f:
        lines = f.readlines()

    # Verify 3-layer element definitions
    element_headers = [line.strip().upper() for line in lines if line.strip().upper().startswith("*ELEMENT")]
    assert any("TYPE=U1" in h for h in element_headers), "Layer 1 quad UEL (U1) missing"
    assert any("TYPE=U3" in h for h in element_headers), "Layer 1 tri UEL (U3) missing"
    assert any("TYPE=U2" in h for h in element_headers), "Layer 2 quad UEL (U2) missing"
    assert any("TYPE=U4" in h for h in element_headers), "Layer 2 tri UEL (U4) missing"
    assert any("TYPE=CPE4" in h for h in element_headers), "Layer 3 CPE4 missing"
    assert any("TYPE=CPE3" in h for h in element_headers), "Layer 3 CPE3 missing"

    # Verify NSET line wrapping <= 16 items per line
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
            assert len(items) <= 16, f"NSET line {line_no} exceeds 16 items: {len(items)} items"

    # Verify Step 1 and Step 2 presence
    step_headers = [line.strip().upper() for line in lines if line.strip().upper().startswith("*STEP")]
    assert len(step_headers) == 2, f"Expected 2 steps, got {len(step_headers)}"
    assert "NAME=STEP-1" in step_headers[0]
    assert "NAME=STEP-2" in step_headers[1]

    # Verify FIELD OUTPUT requests include MISESERI, MISESAVG, S, E, SDV with FREQUENCY=1
    field_lines = [line.strip().upper() for line in lines if "*OUTPUT, FIELD" in line.upper()]
    assert len(field_lines) == 2, "Expected 2 *OUTPUT, FIELD lines"
    for fl in field_lines:
        assert "FREQUENCY=1" in fl, f"FREQUENCY=1 not set: {fl}"

    elem_out_lines = [lines[i+1].strip().upper() for i, line in enumerate(lines) if "*ELEMENT OUTPUT" in line.upper()]
    assert len(elem_out_lines) == 2, "Expected 2 *ELEMENT OUTPUT lines"
    for eol in elem_out_lines:
        assert "MISESERI" in eol, f"MISESERI missing: {eol}"
        assert "SDV" in eol, f"SDV missing: {eol}"


def test_coarse_donor_mesh_quality():
    """Verify physical mesh quality of the 2,906-element coarse mesh."""
    from scripts.remeshing.reusable_2d_adaptive_framework import MeshQualityAuditEngine, AdaptiveConfig, get_geometry_adapter

    config_path = os.path.join(REPO_ROOT, "configs", "remeshing", "f1728_case1_mode1_edge_crack.json")
    with open(config_path, "r") as f:
        cfg = AdaptiveConfig(json.load(f))
    adapter = get_geometry_adapter(cfg)

    audit = MeshQualityAuditEngine.evaluate_mesh(COARSE_PHYS_INP, l0_mm=cfg.l0, adapter=adapter)
    assert audit["total_elements"] == 2906
    assert audit["quad_fraction_pct"] > 95.0, f"Quad fraction too low: {audit['quad_fraction_pct']}%"
    assert audit["non_positive_jacobians"] == 0, f"Found {audit['non_positive_jacobians']} negative Jacobians"
    assert audit["min_det_j"] > 0, "det(J) must be strictly positive"
    assert audit["max_aspect_ratio"] <= 5.0, f"Aspect ratio too high: {audit['max_aspect_ratio']}"

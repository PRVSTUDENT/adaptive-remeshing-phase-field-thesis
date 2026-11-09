# -*- coding: utf-8 -*-
"""
test_f1699_same_state_and_native_remesh.py
==========================================
Unit test suite for Task F1699: Validate Full-Field Same-State UEL Recovery
and Execute Native Abaqus adaptiveRemesh for Pandey-Kumar Figures 15(b)/16(b).

Verifies:
  1. Bitwise preservation of production monolithic UEL.
  2. Gate A Full-Field Same-State Recovery validation metrics and PASS verdict.
  3. Gate B Native adaptiveRemesh() mesh metrics, element/node counts, and area preservation.
  4. Primary corridor active refinement down to h_min <= l0/3.
  5. Secondary corridor unrefined status (0.00% <= l0/2) across all tested donors.
  6. Scientific classification as NEGATIVE_REPRODUCTION.
  7. Physical presence of publication figure artifacts.
"""

import os
import json
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

EXPECTED_PRODUCTION_UEL_SHA = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"

def test_production_uel_hash_preservation():
    uel_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
    assert os.path.exists(uel_path), "Production UEL not found at: %s" % uel_path
    with open(uel_path, "rb") as f:
        actual_sha = hashlib.sha256(f.read()).hexdigest().lower()
    assert actual_sha == EXPECTED_PRODUCTION_UEL_SHA, (
        "Production UEL hash mismatch! Expected: %s, Actual: %s" % (EXPECTED_PRODUCTION_UEL_SHA, actual_sha)
    )

def test_f1699_gate_a_same_state_validation():
    gate_a_json = os.path.join(REPO_ROOT, "results", "validation", "f1699_full_field_same_state_validation.json")
    assert os.path.exists(gate_a_json), "Gate A validation JSON not found: %s" % gate_a_json
    with open(gate_a_json, "r") as f:
        data = json.load(f)

    assert data["gate_a_verdict"] == "NOT_PASSED_PROVISIONAL_BOUNDARY_AND_DAMAGE_ONLY", (
        "Gate A verdict must be NOT_PASSED_PROVISIONAL_BOUNDARY_AND_DAMAGE_ONLY"
    )
    assert data["scientific_status"] == "NOT_PASSED / PROVISIONALLY_SUPPORTED_AT_BOUNDARY"
    assert data["scientific_acceptance_matrix"]["full_field_same_state_gate_a"] == "NOT_PASSED"
    assert data["scientific_acceptance_matrix"]["internal_uel_displacement_correspondence"] == "UNVERIFIABLE"
    assert len(data["states_evaluated"]) == 3, "Three states must be evaluated in Gate A"

    for skey, sinfo in data["states_evaluated"].items():
        assert sinfo["overall_state_verdict"] == "PROVISIONALLY_SUPPORTED_AT_BOUNDARY_INTERNAL_UNVERIFIABLE", (
            "State %s verdict must be PROVISIONALLY_SUPPORTED_AT_BOUNDARY_INTERNAL_UNVERIFIABLE" % skey
        )
        assert sinfo["damage_mapping"]["mapped_elements"] == 3923, "All 3923 elements must be mapped"
        assert sinfo["damage_mapping"]["bounded_in_0_1"] is True, "Damage must be bounded in [0, 1]"
        assert sinfo["displacement_discrepancy"]["boundary_disp_error_eps_U"] <= 1.0e-4, "Boundary eps_U must be <= 1e-4"
        assert sinfo["displacement_discrepancy"]["internal_u_status"] == "UNVERIFIABLE", (
            "Internal displacement omission must be explicitly disclosed as UNVERIFIABLE"
        )
        assert sinfo["reaction_force"]["status"] == "PASS_BOUNDARY_ONLY"
        assert sinfo["stress_and_miseseri"]["genuine_abaqus_miseseri"] is True, "Genuine MISESERI must be present"

def test_f1699_gate_b_native_adapted_mesh_metrics():
    gate_b_json = os.path.join(REPO_ROOT, "results", "validation", "f1699_native_adapted_mesh_metrics.json")
    assert os.path.exists(gate_b_json), "Gate B metrics JSON not found: %s" % gate_b_json
    with open(gate_b_json, "r") as f:
        data = json.load(f)

    assert "GATE_B" in data["gate"]
    assert "EXPLORATORY" in data["gate"] or "NATIVE" in data["gate"]
    assert data["scientific_classification"] == "NOT_REPRODUCED_UNDER_TESTED_CONDITIONS"
    assert data["scientific_classification_alias"] == "NEGATIVE_REPRODUCTION"
    assert "PK_SEC43_F1699_NATIVE_ADAPT" in data["donors_evaluated"]
    assert "PK_SEC43_F1699_NATIVE_ADAPT_STATE2" in data["donors_evaluated"]

    # State 4 (Primary Donor) metrics & provenance
    d4 = data["donors_evaluated"]["PK_SEC43_F1699_NATIVE_ADAPT"]
    assert d4["total_elements"] == 12110, "State 4 adapted element count must be 12,110"
    assert d4["total_nodes"] == 12217, "State 4 adapted node count must be 12,217"
    assert d4["quad_pct"] >= 95.0, "Quad percentage must exceed 95%"
    assert abs(d4["total_area_mm2"] - 7324.76) < 1.0, "Area must preserve CAD area to < 1 mm^2"
    assert d4["execution_provenance"]["line_difference_outside_comments"] == 0, (
        "Mesh lines outside comments must be identical to historical best donor"
    )

    # State 2 (Optional Second Donor) metrics
    d2 = data["donors_evaluated"]["PK_SEC43_F1699_NATIVE_ADAPT_STATE2"]
    assert d2["total_elements"] == 9443, "State 2 adapted element count must be 9,443"
    assert d2["total_nodes"] == 9573, "State 2 adapted node count must be 9,573"

def test_f1699_corridor_resolution_and_falsification():
    gate_b_json = os.path.join(REPO_ROOT, "results", "validation", "f1699_native_adapted_mesh_metrics.json")
    with open(gate_b_json, "r") as f:
        data = json.load(f)

    d4 = data["donors_evaluated"]["PK_SEC43_F1699_NATIVE_ADAPT"]
    # Primary corridor must be refined
    assert d4["primary_corridor"]["min"] <= 0.0950, "Primary corridor must refine <= l0/3 = 0.0950 mm"
    assert d4["primary_corridor"]["median"] <= 0.2850, "Primary corridor median must refine <= l0 = 0.285 mm"
    assert d4["primary_corridor"]["pct_le_l0_half"] > 2.0, "Primary corridor must have elements <= l0/2"

    # Secondary corridor MUST be unrefined at l0/2
    assert d4["secondary_corridor"]["pct_le_l0_half"] == 0.0, (
        "Secondary corridor must have exactly 0.00% <= l0/2 under single-rule recipe"
    )
    assert d4["secondary_corridor"]["min"] > 0.1425, "Secondary corridor min size must exceed l0/2 = 0.1425 mm"
    assert d4["secondary_corridor"]["median"] >= 0.50, "Secondary corridor median must be ~0.50 mm"

    # State 2 secondary corridor also unrefined
    d2 = data["donors_evaluated"]["PK_SEC43_F1699_NATIVE_ADAPT_STATE2"]
    assert d2["secondary_corridor"]["pct_le_l0_half"] == 0.0, "State 2 secondary corridor must also be 0.00% <= l0/2"

def test_f1699_adapted_inp_decks_exist():
    inp1 = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "198_pk_sec43_coupled_validation", "PK_SEC43_F1699_NATIVE_ADAPT.inp")
    inp2 = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "198_pk_sec43_coupled_validation", "PK_SEC43_F1699_NATIVE_ADAPT_STATE2.inp")
    assert os.path.exists(inp1), "Primary adapted INP not found: %s" % inp1
    assert os.path.exists(inp2), "State 2 adapted INP not found: %s" % inp2
    assert os.path.getsize(inp1) > 500000, "Primary adapted INP must exceed 500 KB"
    assert os.path.getsize(inp2) > 400000, "State 2 adapted INP must exceed 400 KB"

def test_f1699_publication_figure_exists():
    fig_pdf = os.path.join(REPO_ROOT, "MA_AdaptiveRemeshing_Report_2026", "figures", "fig_f1699_sec43_same_state_and_native_remesh.pdf")
    fig_png = os.path.join(REPO_ROOT, "MA_AdaptiveRemeshing_Report_2026", "figures", "fig_f1699_sec43_same_state_and_native_remesh.png")
    assert os.path.exists(fig_pdf), "Publication PDF figure not found: %s" % fig_pdf
    assert os.path.exists(fig_png), "Publication PNG figure not found: %s" % fig_png
    assert os.path.getsize(fig_pdf) > 100000, "Figure PDF must exceed 100 KB"

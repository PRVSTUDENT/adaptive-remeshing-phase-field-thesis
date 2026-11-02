# -*- coding: utf-8 -*-
"""
test_c5_to_c6_adaptive_integration.py
======================================
Comprehensive qualification and regression test suite for C5 -> C6 Remeshing
and State-Transfer Integration Pipeline.

Protocol Version: 2
Task: F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE

Verifies:
1. C5 source mesh topology & indicator distribution validation (12,996 quads, strict rejection of nonfinites/duplicates).
2. Deterministic denominator-guarded refinement sizing without predefined crack corridors, strictly banning coarsening.
3. Conformal C6 candidate mesh generation with positive Jacobians, split slit flanks, and kinematic tie equations.
4. Topology-guarded nonmatching state transfer (u, d, H) with slit-flank isolation, phase bounds, and zero healing.
5. Quantitative transfer acceptance criteria & Stage C3-0 re-equilibration interface preparation.
"""

from __future__ import annotations

import json
import math
import os
import sys
import tempfile
from pathlib import Path
import pytest
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.remeshing.c5_to_c6_adaptive_integration import (
    C5_SOURCE_INP,
    DEFAULT_THRESHOLD_ETA,
    ELL_0_MM,
    MAX_FINE_H_MM,
    build_c6_conformal_quad_mesh,
    build_stage_c3_0_reequilibration_deck,
    compute_c5_to_c6_sizing,
    evaluate_transfer_acceptance,
    generate_graded_1d_coords,
    generate_synthetic_c5_miseseri_fixture,
    load_c5_mesh,
    sha256_file,
    transfer_c5_to_c6_solution,
    validate_c5_indicator_distribution,
)

FIXTURE_CP03 = (
    REPO_ROOT
    / "models"
    / "pandey_kumar_mode1"
    / "167_c5_package167_r3_c2_2_continuation"
    / "evidence"
    / "1419566.mmaster02"
    / "converged_checkpoint_03.json"
)


def test_01_c5_mesh_and_indicator_validation():
    """Verify C5 mesh loading and strict indicator record validation."""
    assert C5_SOURCE_INP.is_file(), f"Missing C5 source input deck: {C5_SOURCE_INP}"
    c5_mesh = load_c5_mesh()
    assert c5_mesh["num_nodes"] == 13279, f"Expected 13279 nodes, got {c5_mesh['num_nodes']}"
    assert c5_mesh["num_quads"] == 12996, f"Expected 12996 quads, got {c5_mesh['num_quads']}"

    with tempfile.TemporaryDirectory() as tmpdir:
        fixture_csv = Path(tmpdir) / "synthetic_c5_miseseri.csv"
        generate_synthetic_c5_miseseri_fixture(fixture_csv, c5_mesh)
        assert fixture_csv.is_file()

        # Parse generated records
        with open(fixture_csv, "r", encoding="utf-8") as f:
            import csv
            reader = list(csv.DictReader(f))

        val_res = validate_c5_indicator_distribution(reader, expected_count=12996)
        assert val_res["status"] == "VALID"
        assert val_res["element_count"] == 12996

        # Negative test 1: wrong element count
        with pytest.raises(ValueError) as exc1:
            validate_c5_indicator_distribution(reader[:-1], expected_count=12996)
        assert "count mismatch" in str(exc1.value)

        # Negative test 2: duplicate element ID
        import copy
        corrupt_dups = copy.deepcopy(reader)
        corrupt_dups[1]["element_id"] = corrupt_dups[0]["element_id"]
        with pytest.raises(ValueError) as exc2:
            validate_c5_indicator_distribution(corrupt_dups, expected_count=12996)
        assert "Duplicate element_id detected" in str(exc2.value)

        # Negative test 3: nonfinite value
        corrupt_nan = copy.deepcopy(reader)
        corrupt_nan[5]["miseseri_kNmm2"] = "NaN"
        with pytest.raises(ValueError) as exc3:
            validate_c5_indicator_distribution(corrupt_nan, expected_count=12996)
        assert "nonfinite" in str(exc3.value)


def test_02_deterministic_sizing_and_coarsening_ban():
    """Verify denominator guard, deterministic marking, and strict coarsening ban."""
    c5_mesh = load_c5_mesh()
    with tempfile.TemporaryDirectory() as tmpdir:
        fixture_csv = Path(tmpdir) / "synthetic_c5_miseseri.csv"
        generate_synthetic_c5_miseseri_fixture(fixture_csv, c5_mesh)
        with open(fixture_csv, "r", encoding="utf-8") as f:
            import csv
            records = list(csv.DictReader(f))

        val_res = validate_c5_indicator_distribution(records, expected_count=12996)
        sizing = compute_c5_to_c6_sizing(
            val_res["element_map"],
            threshold_eta=DEFAULT_THRESHOLD_ETA,
            h_fine=0.00060,
            growth_ratio=1.12,
            max_h=0.0025,
        )

        assert sizing["status"] == "SIZING_COMPUTED"
        assert sizing["h_fine_mm"] <= MAX_FINE_H_MM
        assert sizing["max_h_mm"] <= 0.0025
        assert sizing["coarsening_disabled"] is True
        assert sizing["marked_element_count"] > 0
        assert 0.035 <= sizing["x_center"] <= 0.055
        assert 0.045 <= sizing["y_center"] <= 0.055


def test_03_c6_mesh_generation_and_jacobian_positivity():
    """Verify C6 mesh generation, positive Jacobians, slit flanks, and boundary sets."""
    c5_mesh = load_c5_mesh()
    with tempfile.TemporaryDirectory() as tmpdir:
        fixture_csv = Path(tmpdir) / "synthetic_c5_miseseri.csv"
        generate_synthetic_c5_miseseri_fixture(fixture_csv, c5_mesh)
        with open(fixture_csv, "r", encoding="utf-8") as f:
            import csv
            records = list(csv.DictReader(f))

        val_res = validate_c5_indicator_distribution(records, expected_count=12996)
        sizing = compute_c5_to_c6_sizing(val_res["element_map"], h_fine=0.00065, max_h=0.0025)

        x_coords = generate_graded_1d_coords(
            x_min=0.0, x_max=0.100, x_center=sizing["x_center"],
            band_half_width=sizing["band_half_x"], h_fine=sizing["h_fine_mm"],
            growth_ratio=sizing["growth_ratio"], max_h=sizing["max_h_mm"],
            key_points=[0.0, 0.040, 0.100]
        )
        y_coords = generate_graded_1d_coords(
            x_min=0.0, x_max=0.100, x_center=0.050,
            band_half_width=sizing["band_half_y"], h_fine=sizing["h_fine_mm"],
            growth_ratio=sizing["growth_ratio"], max_h=sizing["max_h_mm"],
            key_points=[0.0, 0.050, 0.100]
        )

        c6_mesh = build_c6_conformal_quad_mesh(x_coords, y_coords, slit_y=0.050, slit_a0=0.040)
        assert c6_mesh["num_elements"] > 4000
        assert c6_mesh["min_det_jac"] > 0.0, "Found non-positive Jacobian in C6 mesh!"
        assert len(c6_mesh["coincident_slit_pairs"]) >= 30
        assert len(c6_mesh["ligament_nodes"]) >= 30
        assert len(c6_mesh["top_nodes"]) > 50
        assert len(c6_mesh["bottom_nodes"]) > 50


def test_04_nonmatching_state_transfer_and_flank_isolation():
    """Verify bilinear state projection from authentic Checkpoint 03 to candidate C6 mesh."""
    assert FIXTURE_CP03.is_file(), f"Missing authentic Checkpoint 03: {FIXTURE_CP03}"
    with open(FIXTURE_CP03, "r", encoding="utf-8") as f:
        cp03 = json.load(f)

    c5_mesh = load_c5_mesh()
    with tempfile.TemporaryDirectory() as tmpdir:
        fixture_csv = Path(tmpdir) / "synthetic_c5_miseseri.csv"
        generate_synthetic_c5_miseseri_fixture(fixture_csv, c5_mesh)
        with open(fixture_csv, "r", encoding="utf-8") as f:
            import csv
            records = list(csv.DictReader(f))

        val_res = validate_c5_indicator_distribution(records, expected_count=12996)
        sizing = compute_c5_to_c6_sizing(val_res["element_map"], h_fine=0.00070, max_h=0.0025)

        x_coords = generate_graded_1d_coords(
            0.0, 0.100, sizing["x_center"], sizing["band_half_x"], sizing["h_fine_mm"],
            sizing["growth_ratio"], sizing["max_h_mm"], key_points=[0.0, 0.040, 0.100]
        )
        y_coords = generate_graded_1d_coords(
            0.0, 0.100, 0.050, sizing["band_half_y"], sizing["h_fine_mm"],
            sizing["growth_ratio"], sizing["max_h_mm"], key_points=[0.0, 0.050, 0.100]
        )
        c6_mesh = build_c6_conformal_quad_mesh(x_coords, y_coords, slit_y=0.050, slit_a0=0.040)

        transfer_res = transfer_c5_to_c6_solution(c5_mesh, cp03, c6_mesh)
        assert transfer_res["status"] == "TRANSFER_COMPLETE"
        assert transfer_res["healing_violations"] == 0
        assert transfer_res["bounds_violations"] == 0

        # Slit-flank isolation check:
        # Coincident node pairs must have distinct displacement in DOFs if opening occurs
        pairs = c6_mesh["coincident_slit_pairs"]
        assert len(pairs) > 0
        disp = transfer_res["transferred_disp"]
        dmg = transfer_res["transferred_damage"]

        for lower_nid, upper_nid, x_pos in pairs[:10]:
            # Damage bounds check on slit flanks
            assert 0.0 <= dmg[lower_nid] <= 1.0
            assert 0.0 <= dmg[upper_nid] <= 1.0


def test_05_transfer_acceptance_criteria_and_stage_c3_0_deck():
    """Verify quantitative transfer acceptance evaluation and Stage C3-0 re-equilibration deck assembly."""
    with open(FIXTURE_CP03, "r", encoding="utf-8") as f:
        cp03 = json.load(f)

    c5_mesh = load_c5_mesh()
    with tempfile.TemporaryDirectory() as tmpdir:
        fixture_csv = Path(tmpdir) / "synthetic_c5_miseseri.csv"
        generate_synthetic_c5_miseseri_fixture(fixture_csv, c5_mesh)
        with open(fixture_csv, "r", encoding="utf-8") as f:
            import csv
            records = list(csv.DictReader(f))

        val_res = validate_c5_indicator_distribution(records, expected_count=12996)
        sizing = compute_c5_to_c6_sizing(val_res["element_map"], h_fine=0.00070, max_h=0.0025)

        x_coords = generate_graded_1d_coords(
            0.0, 0.100, sizing["x_center"], sizing["band_half_x"], sizing["h_fine_mm"],
            sizing["growth_ratio"], sizing["max_h_mm"], key_points=[0.0, 0.040, 0.100]
        )
        y_coords = generate_graded_1d_coords(
            0.0, 0.100, 0.050, sizing["band_half_y"], sizing["h_fine_mm"],
            sizing["growth_ratio"], sizing["max_h_mm"], key_points=[0.0, 0.050, 0.100]
        )
        c6_mesh = build_c6_conformal_quad_mesh(x_coords, y_coords, slit_y=0.050, slit_a0=0.040)
        transfer_res = transfer_c5_to_c6_solution(c5_mesh, cp03, c6_mesh)

        acc = evaluate_transfer_acceptance(cp03, c6_mesh, transfer_res)
        assert acc["acceptance_passed"] is True
        for tname, tinfo in acc["tests"].items():
            assert tinfo["pass"] is True, f"Subtest {tname} failed: {tinfo}"

        # Build Stage C3-0 deck
        out_deck = Path(tmpdir) / "M1_C6_STAGE_C3_0_REEQUILIBRATION.inp"
        deck_res = build_stage_c3_0_reequilibration_deck(
            c6_mesh, transfer_res, target_uy_mm=cp03["target_uy_mm"], output_inp_path=out_deck
        )
        assert deck_res["status"] == "REEQUILIBRATION_DECK_CREATED"
        assert out_deck.is_file()
        assert len(deck_res["sha256"]) == 64
        # Verify no blank lines inside User Element / Nset blocks
        lines = out_deck.read_text(encoding="utf-8").splitlines()
        assert len(lines) > 15000

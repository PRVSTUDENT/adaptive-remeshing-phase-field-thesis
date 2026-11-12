# -*- coding: utf-8 -*-
"""
Unit test suite for Task F1726:
Reusable 2D Adaptive-Remeshing Framework and Seven-Hole Benchmark Validation
"""

import os
import sys
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

STUDY_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "218_f1726_seven_hole_study")
CONFIG_JSON = os.path.join(REPO_ROOT, "configs", "method_a", "seven_hole_benchmark.json")
COARSE_PHYS_INP = os.path.join(STUDY_DIR, "PK_F1726_SEVEN_HOLE_COARSE_PHYS.inp")
COARSE_AUDIT_JSON = os.path.join(STUDY_DIR, "f1726_coarse_odb_audit.json")
ADAPTED_PHYS_INP = os.path.join(STUDY_DIR, "PK_F1726_SEVEN_HOLE_ADAPTED_PHYS.inp")
FINE_PARITY_JSON = os.path.join(STUDY_DIR, "f1726_fine_parity_results.json")
PROD_DECK_INP = os.path.join(STUDY_DIR, "PK_F1726_SEVEN_HOLE_ADAPTED_PROD.inp")
FIG_DIR = os.path.join(REPO_ROOT, "MA_AdaptiveRemeshing_Report_2026", "figures")


def test_reusable_framework_geometry_adapter():
    """Verify that the generalized multi-hole adapter parses and classifies points correctly."""
    from scripts.remeshing.reusable_2d_adaptive_framework import MultiHolePlateAdapter, AdaptiveConfig

    assert os.path.exists(CONFIG_JSON), "Missing benchmark configuration JSON"
    config = AdaptiveConfig.from_json(CONFIG_JSON)
    assert len(config.voids) == 7
    assert abs(config.l0 - 0.008) < 1e-6

    adapter = MultiHolePlateAdapter(config)
    # Check regional classifications
    assert adapter.classify_region(0.50, 0.56) == "UPPER_CRACK_CORRIDOR"
    assert adapter.classify_region(0.40, 0.35 + 0.05 + 0.01) == "LOWER_SHIELDED_HOLES"
    assert adapter.classify_region(0.10, 0.90) == "FAR_FIELD"

    # Check void containment: points inside holes are outside solid domain
    assert adapter.is_inside_domain(0.15, 0.40) is False  # Inside hole 1
    assert adapter.is_inside_domain(0.10, 0.90) is True   # In solid plate


def test_coarse_physical_mesh_quality():
    """Verify coarse physical mesh element count, topology, and node sets."""
    assert os.path.exists(COARSE_PHYS_INP), "Missing coarse physical mesh INP"
    
    num_nodes = 0
    num_elems = 0
    num_quads = 0
    num_tris = 0
    in_nodes = False
    in_elems = False

    with open(COARSE_PHYS_INP, "r") as f:
        for line in f:
            l = line.strip()
            if not l or l.startswith("**"):
                continue
            if l.startswith("*"):
                in_nodes = False
                in_elems = False
                u = l.upper()
                if u.startswith("*NODE"):
                    in_nodes = True
                elif u.startswith("*ELEMENT"):
                    in_elems = True
                continue
            parts = [p.strip() for p in l.split(",") if p.strip()]
            if in_nodes and len(parts) >= 3:
                num_nodes += 1
            elif in_elems and len(parts) >= 4:
                num_elems += 1
                if len(parts) == 5:
                    num_quads += 1
                elif len(parts) == 4:
                    num_tris += 1

    assert num_nodes == 2688, f"Expected 2,688 coarse nodes, got {num_nodes}"
    assert num_elems == 2566, f"Expected 2,566 coarse elements, got {num_elems}"
    quad_pct = 100.0 * num_quads / float(num_elems)
    assert quad_pct >= 96.0, f"Quad percentage {quad_pct:.2f}% < 96.0%"


def test_coarse_odb_audit_and_error_contrast():
    """Verify coarse ODB audit metrics: terminal displacement, step counts, and error contrast."""
    assert os.path.exists(COARSE_AUDIT_JSON), "Missing coarse ODB audit JSON"
    with open(COARSE_AUDIT_JSON, "r") as f:
        audit = json.load(f)

    assert audit["step1_frames"] >= 10
    assert audit["step2_frames"] >= 150
    assert abs(audit["terminal_displacement_mm"] - 0.006558) < 1e-4

    upper = audit["upper_corridor"]
    bulk = audit["bulk_far_field"]
    h6 = audit["lower_hole_h6"]
    h7 = audit["lower_hole_h7"]

    # Upper corridor has high damage d > 0.45
    assert upper["max_damage"] >= 0.45, f"Upper corridor max damage {upper['max_damage']} < 0.45"
    # Lower holes are shielded (d < 0.10)
    assert h6["max_damage"] < 0.10, f"Lower hole h6 damage {h6['max_damage']} >= 0.10"
    assert h7["max_damage"] < 0.10, f"Lower hole h7 damage {h7['max_damage']} >= 0.10"

    # Error contrast ratio (Upper Corridor vs Bulk) >= 5.0
    contrast = upper["mean_miseseri"] / bulk["mean_miseseri"]
    assert contrast >= 5.0, f"Error contrast ratio {contrast:.2f} < 5.0"


def test_adapted_physical_mesh_and_benchmark_parity():
    """Verify that optimal candidate F1726_S2_ET568 achieves exact benchmark parity (-0.04%)."""
    assert os.path.exists(FINE_PARITY_JSON), "Missing fine parity JSON"
    with open(FINE_PARITY_JSON, "r") as f:
        fine = json.load(f)

    assert "F1726_S2_ET568" in fine
    opt = fine["F1726_S2_ET568"]
    
    # 15,708 elements (-0.04% difference vs 15,714 benchmark, within 6 elements)
    n_elems = opt["num_elements"]
    assert n_elems == 15708, f"Expected 15,708 elements, got {n_elems}"
    diff = abs(n_elems - 15714)
    assert diff <= 10, f"Element count difference {diff} exceeds 10 elements"
    parity_pct = 100.0 * (n_elems - 15714) / 15714.0
    assert abs(parity_pct) < 0.10, f"Parity error {parity_pct:.3f}% exceeds 0.1%"

    # Quality metrics
    assert opt["quad_percentage"] >= 97.0, f"Quad percentage {opt['quad_percentage']}% < 97.0%"
    assert opt["positive_jacobians"] is True
    assert opt["ar_max"] < 10.0


def test_spatial_selectivity_and_phase_field_resolution():
    """Verify that the adapted mesh achieves 100% h <= l0 along the fracture corridor and coarse shielding elsewhere."""
    with open(FINE_PARITY_JSON, "r") as f:
        fine = json.load(f)

    opt = fine["F1726_S2_ET568"]
    upper = opt["upper_corridor"]
    h6 = opt["lower_h6"]
    bulk = opt["bulk"]

    # 100% of upper fracture corridor elements must satisfy h <= l0 (8.0 um)
    assert upper["pct_le_l0"] == 100.0, f"Upper corridor compliance {upper['pct_le_l0']}% < 100.0%"
    # Mean element size in fracture corridor should be approximately l0/3 (2.67 um)
    assert upper["mean"] <= 3.0, f"Upper corridor mean size {upper['mean']} um > 3.0 um"

    # Lower holes are significantly coarser (mean size >= 4.5 um)
    assert h6["mean"] >= 4.5, f"Lower hole h6 mean size {h6['mean']} um < 4.5 um"

    # Far-field bulk is coarse (mean size >= 6.5 um)
    assert bulk["mean"] >= 6.5, f"Bulk mean size {bulk['mean']} um < 6.5 um"


def test_production_deck_structure():
    """Verify production 3-layer deck structure, layered counts, and boundary definitions."""
    assert os.path.exists(PROD_DECK_INP), "Missing production deck INP"

    has_uel = False
    has_umat = False
    has_equation = False
    num_equations = 0

    with open(PROD_DECK_INP, "r") as f:
        for line in f:
            u = line.strip().upper()
            if u.startswith("*USER ELEMENT"):
                has_uel = True
            elif "NAME=DUMMY_MAT" in u or "NAME=UMAT_MAT" in u:
                has_umat = True
            elif u.startswith("*EQUATION"):
                has_equation = True
                num_equations += 1

    assert has_uel, "Production deck missing *USER ELEMENT definition"
    assert has_umat, "Production deck missing UMAT material definition"
    assert has_equation, "Production deck missing *EQUATION coupling"
    assert num_equations >= 50, f"Expected >= 50 equations, found {num_equations}"


def test_publication_figures_existence():
    """Verify that all 4 publication figure sets exist in vector PDF and PNG formats."""
    expected_stems = [
        "fig_f1726_figure_1_full_domain_mesh_comparison",
        "fig_f1726_figure_2_hole_neighborhood_zooms",
        "fig_f1726_figure_3_spatial_allocation_and_selectivity",
        "fig_f1726_figure_4_parity_convergence_curve"
    ]
    for stem in expected_stems:
        pdf_path = os.path.join(FIG_DIR, f"{stem}.pdf")
        png_path = os.path.join(FIG_DIR, f"{stem}.png")
        assert os.path.exists(pdf_path), f"Missing figure PDF: {pdf_path}"
        assert os.path.exists(png_path), f"Missing figure PNG: {png_path}"
        assert os.path.getsize(pdf_path) > 10000, f"Figure PDF too small: {pdf_path}"
        assert os.path.getsize(png_path) > 50000, f"Figure PNG too small: {png_path}"

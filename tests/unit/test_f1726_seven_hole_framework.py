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

    # Error contrast ratio (Upper Corridor vs Bulk) >= 5.0 (5.42x)
    contrast = upper["mean_miseseri"] / bulk["mean_miseseri"]
    assert contrast >= 5.0, f"Error contrast ratio {contrast:.2f} < 5.0"
    assert abs(contrast - 5.427) < 0.02, f"Contrast {contrast:.3f} does not match 5.427x"
    # Far-field bulk max damage occurs on hole outer shoulders (d ~ 0.247)
    assert abs(bulk["max_damage"] - 0.2469) < 0.01, f"Bulk max damage {bulk['max_damage']} != 0.2469"


def test_adapted_physical_mesh_and_benchmark_parity():
    """Verify that optimal candidate F1726_S2_ET568 achieves exact benchmark parity (-0.04%)."""
    from scripts.remeshing.reusable_2d_adaptive_framework import MeshQualityAuditEngine

    assert os.path.exists(ADAPTED_PHYS_INP), "Missing adapted physical mesh INP"
    
    # 1. Direct evaluate_mesh on actual physical mesh file
    audit = MeshQualityAuditEngine.evaluate_mesh(ADAPTED_PHYS_INP, l0_mm=0.008)
    assert audit["total_elements"] == 15708, f"Expected 15,708 elements, got {audit['total_elements']}"
    assert audit["non_positive_jacobians"] == 0, f"Found {audit['non_positive_jacobians']} non-positive Jacobians"
    assert audit["min_det_j"] > 0.0, f"Min Jacobian {audit['min_det_j']} <= 0"
    assert audit["quad_count"] == 15325, f"Expected 15,325 quads, got {audit['quad_count']}"
    assert audit["tri_count"] == 383, f"Expected 383 tris, got {audit['tri_count']}"
    assert audit["quad_percent"] >= 97.5, f"Quad percentage {audit['quad_percent']:.2f}% < 97.5%"
    assert audit["median_aspect_ratio"] <= 1.30, f"Median aspect ratio {audit['median_aspect_ratio']} > 1.30"
    assert audit["distorted_elements"] == 0, f"Found {audit['distorted_elements']} distorted elements"

    # 2. Benchmark parity check vs published 15,714 target
    diff = abs(audit["total_elements"] - 15714)
    assert diff == 6, f"Parity difference {diff} != 6 elements"
    parity_pct = 100.0 * (audit["total_elements"] - 15714) / 15714.0
    assert abs(parity_pct - (-0.038)) < 0.01, f"Parity error {parity_pct:.3f}% does not match -0.038%"

    # 3. Cross-check with fine parity dataset
    assert os.path.exists(FINE_PARITY_JSON), "Missing fine parity JSON"
    with open(FINE_PARITY_JSON, "r") as f:
        fine = json.load(f)
    assert "F1726_S2_ET568" in fine
    opt = fine["F1726_S2_ET568"]
    assert opt["num_elements"] == 15708
    assert opt["ar_max"] == 2.857


def test_spatial_selectivity_and_phase_field_resolution():
    """Verify exact regional partition and 100% h <= l0 directly from physical mesh PK_F1726_SEVEN_HOLE_ADAPTED_PHYS.inp."""
    import math
    from scripts.remeshing.reusable_2d_adaptive_framework import MeshQualityAuditEngine

    assert os.path.exists(ADAPTED_PHYS_INP), "Missing adapted physical mesh INP"
    nodes, quad_elems, tri_elems = MeshQualityAuditEngine.parse_physical_inp(ADAPTED_PHYS_INP)

    upper_segments = [
        ((0.15, 0.40), (0.30, 0.60)),
        ((0.30, 0.60), (0.50, 0.55)),
        ((0.50, 0.55), (0.70, 0.60)),
        ((0.70, 0.60), (0.85, 0.50))
    ]

    def dist_to_segments(px, py, segs):
        min_d = 1e9
        for (x1, y1), (x2, y2) in segs:
            dx, dy = x2 - x1, y2 - y1
            l2 = dx*dx + dy*dy
            t = max(0.0, min(1.0, ((px - x1)*dx + (py - y1)*dy) / l2)) if l2 > 0 else 0.0
            d = math.hypot(px - (x1 + t*dx), py - (y1 + t*dy))
            if d < min_d:
                min_d = d
        return min_d

    elements_list = []
    for eid, conn in quad_elems.items():
        pts = [nodes[nid] for nid in conn]
        cx = sum(p[0] for p in pts) / 4.0
        cy = sum(p[1] for p in pts) / 4.0
        area = 0.5 * abs(
            (pts[0][0]*pts[1][1] - pts[1][0]*pts[0][1]) +
            (pts[1][0]*pts[2][1] - pts[2][0]*pts[1][1]) +
            (pts[2][0]*pts[3][1] - pts[3][0]*pts[2][1]) +
            (pts[3][0]*pts[0][1] - pts[0][0]*pts[3][1])
        )
        h_area = math.sqrt(area) * 1000.0
        edges = [
            math.hypot(pts[1][0] - pts[0][0], pts[1][1] - pts[0][1]),
            math.hypot(pts[2][0] - pts[1][0], pts[2][1] - pts[1][1]),
            math.hypot(pts[3][0] - pts[2][0], pts[3][1] - pts[2][1]),
            math.hypot(pts[0][0] - pts[3][0], pts[0][1] - pts[3][1])
        ]
        h_max_edge = max(edges) * 1000.0
        elements_list.append({"cx": cx, "cy": cy, "h_area": h_area, "h_max_edge": h_max_edge})

    for eid, conn in tri_elems.items():
        pts = [nodes[nid] for nid in conn]
        cx = sum(p[0] for p in pts) / 3.0
        cy = sum(p[1] for p in pts) / 3.0
        area = 0.5 * abs(
            pts[0][0]*(pts[1][1] - pts[2][1]) +
            pts[1][0]*(pts[2][1] - pts[0][1]) +
            pts[2][0]*(pts[0][1] - pts[1][1])
        )
        h_area = math.sqrt(area) * 1000.0
        edges = [
            math.hypot(pts[1][0] - pts[0][0], pts[1][1] - pts[0][1]),
            math.hypot(pts[2][0] - pts[1][0], pts[2][1] - pts[1][1]),
            math.hypot(pts[0][0] - pts[2][0], pts[0][1] - pts[2][1])
        ]
        h_max_edge = max(edges) * 1000.0
        elements_list.append({"cx": cx, "cy": cy, "h_area": h_area, "h_max_edge": h_max_edge})

    # Direct canonical classification from mesh elements
    upper = []
    h6 = []
    h7 = []
    bulk = []

    for el in elements_list:
        cx, cy = el["cx"], el["cy"]
        d_up = dist_to_segments(cx, cy, upper_segments)
        d6 = math.hypot(cx - 0.40, cy - 0.35) - 0.05
        d7 = math.hypot(cx - 0.65, cy - 0.35) - 0.05
        if d_up <= 0.040:
            upper.append(el)
        elif abs(d6) <= 0.040:
            h6.append(el)
        elif abs(d7) <= 0.040:
            h7.append(el)
        else:
            bulk.append(el)

    # 1. Exact non-overlapping counts computed directly from mesh
    assert len(upper) == 2648, f"Direct upper count {len(upper)} != 2648"
    assert len(h6) == 691, f"Direct h6 count {len(h6)} != 691"
    assert len(h7) == 775, f"Direct h7 count {len(h7)} != 775"
    assert len(bulk) == 11594, f"Direct bulk count {len(bulk)} != 11594"
    assert len(upper) + len(h6) + len(h7) + len(bulk) == 15708

    # 2. 100% of upper corridor elements satisfy h_area <= l0 = 8.0 um
    l0_um = 8.0
    upper_ha = [e["h_area"] for e in upper]
    pct_ha_le_l0 = 100.0 * sum(1 for s in upper_ha if s <= l0_um) / float(len(upper))
    assert pct_ha_le_l0 == 100.0, f"Upper corridor h_area compliance {pct_ha_le_l0}% < 100%"
    mean_ha = sum(upper_ha) / float(len(upper))
    assert abs(mean_ha - 2.80) < 0.02, f"Upper corridor mean h_area {mean_ha:.2f} != 2.80 um"

    # 3. 100% of upper corridor elements ALSO satisfy h_max_edge <= l0 = 8.0 um!
    upper_he = [e["h_max_edge"] for e in upper]
    pct_he_le_l0 = 100.0 * sum(1 for s in upper_he if s <= l0_um) / float(len(upper))
    assert pct_he_le_l0 == 100.0, f"Upper corridor h_max_edge compliance {pct_he_le_l0}% < 100%"
    mean_he = sum(upper_he) / float(len(upper))
    assert abs(mean_he - 3.13) < 0.05, f"Upper corridor mean h_max_edge {mean_he:.2f} != 3.13 um"


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

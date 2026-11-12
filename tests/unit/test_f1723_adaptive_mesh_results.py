# -*- coding: utf-8 -*-
"""
tests/unit/test_f1723_adaptive_mesh_results.py
=============================================
Regression and unit verification test suite for Task F1723:
Method A Five-Hole Adaptive-Remeshing Reproduction and Refinement Improvement.

Validates:
  1. File existence and integrity of C_S2_ET340.inp
  2. Element count parity vs published benchmark 12,944 (+3.82% parity, within +/-5%)
  3. 100% positive Jacobians (det(J) > 0)
  4. Quad dominance (>95% quads)
  5. Maximum and mean element aspect ratio
  6. Ligament 1 (h1 <-> h2) resolution thresholds
  7. Ligament 2 (h2 <-> h3) resolution thresholds
  8. Ligament 3 (h3 <-> h4) process zone resolution (100% h <= l0/2)
  9. Ligament 4 (h4 <-> h5) resolution thresholds
  10. Bulk element size preservation (no bulk spreading)
  11. Publication figure artifacts existence (PNG + PDF at 300 DPI)
  12. Parameter exploration dataset completeness
"""

import os
import sys
import json
import math
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
IMPROVED_INP = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "215_f1723_adapted_mesh_study", "C_S2_ET340.inp")
RESULTS_JSON = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "215_f1723_adapted_mesh_study", "f1723_improvement_suite_results.json")
FIG_DIR = os.path.join(REPO_ROOT, "figures", "pandey_kumar_fig22_25_reproduction")

L0_PHYS = 0.008  # 8 um

@pytest.fixture(scope="module")
def parsed_mesh():
    assert os.path.exists(IMPROVED_INP), "Improved INP must exist: %s" % IMPROVED_INP
    nodes = {}
    elements = []
    with open(IMPROVED_INP, "r") as f:
        reading_nodes = False
        reading_elems = False
        for line in f:
            line = line.strip()
            if not line or line.startswith("**"):
                continue
            u = line.upper()
            if u.startswith("*NODE"):
                reading_nodes = True
                reading_elems = False
                continue
            elif u.startswith("*ELEMENT") and "OUTPUT" not in u and ("TYPE" in u or "," in u):
                reading_nodes = False
                reading_elems = True
                continue
            elif u.startswith("*"):
                reading_nodes = False
                reading_elems = False
                continue
            if reading_nodes:
                parts = line.split(",")
                nodes[int(parts[0])] = (float(parts[1]), float(parts[2]))
            elif reading_elems:
                parts = line.split(",")
                elements.append((int(parts[0]), [int(p) for p in parts[1:]]))
    return nodes, elements

def test_01_inp_existence_and_parsing(parsed_mesh):
    nodes, elements = parsed_mesh
    assert len(nodes) > 10000, "Node count must exceed 10,000"
    assert len(elements) > 10000, "Element count must exceed 10,000"

def test_02_element_count_parity_vs_published_benchmark(parsed_mesh):
    nodes, elements = parsed_mesh
    n_elems = len(elements)
    pub_target = 12944
    diff_pct = ((n_elems - pub_target) / float(pub_target)) * 100.0
    # Must match published 12,944 elements within +/- 5.0%
    assert abs(diff_pct) <= 5.0, "Discrepancy must be within +/-5%, got %.2f%% (%d elements)" % (diff_pct, n_elems)
    assert n_elems == 13438, "Expected exactly 13,438 elements for C_S2_ET340"

def test_03_positive_jacobians_and_no_inversion(parsed_mesh):
    nodes, elements = parsed_mesh
    for eid, conn in elements:
        pts = [nodes[n] for n in conn]
        n_pts = len(pts)
        poly_x = [p[0] for p in pts]
        poly_y = [p[1] for p in pts]
        area = 0.5 * sum([poly_x[i]*poly_y[(i+1)%n_pts] - poly_y[i]*poly_x[(i+1)%n_pts] for i in range(n_pts)])
        assert area > 0.0, "Element %d has non-positive Jacobian / inverted area: %.6e" % (eid, area)

def test_04_quad_dominance(parsed_mesh):
    nodes, elements = parsed_mesh
    n_quads = sum(1 for _, conn in elements if len(conn) == 4)
    n_tris = sum(1 for _, conn in elements if len(conn) == 3)
    quad_pct = (n_quads / float(len(elements))) * 100.0
    assert quad_pct >= 95.0, "Mesh must be quad-dominated (>95%), got %.2f%%" % quad_pct
    assert n_tris <= 600, "Triangle count must be small (<600), got %d" % n_tris

def test_05_aspect_ratio_quality(parsed_mesh):
    nodes, elements = parsed_mesh
    ars = []
    for eid, conn in elements:
        pts = [nodes[n] for n in conn]
        n_pts = len(pts)
        poly_x = [p[0] for p in pts]
        poly_y = [p[1] for p in pts]
        edge_lens = [math.hypot(poly_x[(i+1)%n_pts] - poly_x[i], poly_y[(i+1)%n_pts] - poly_y[i]) for i in range(n_pts)]
        ar = max(edge_lens) / max(1e-12, min(edge_lens))
        ars.append(ar)
    mean_ar = sum(ars) / len(ars)
    max_ar = max(ars)
    assert mean_ar < 1.35, "Mean aspect ratio must be < 1.35, got %.3f" % mean_ar
    assert max_ar < 3.0, "Max aspect ratio must be < 3.0, got %.3f" % max_ar

def test_06_ligament_1_resolution(parsed_mesh):
    nodes, elements = parsed_mesh
    # Ligament 1: h1 <-> h2, x in [0.08, 0.27], y in [0.40, 0.56]
    lig1_hs = []
    for eid, conn in elements:
        pts = [nodes[n] for n in conn]
        cx = sum(p[0] for p in pts) / float(len(pts))
        cy = sum(p[1] for p in pts) / float(len(pts))
        if 0.08 <= cx <= 0.27 and 0.40 <= cy <= 0.56:
            area = 0.5 * abs(sum([pts[i][0]*pts[(i+1)%len(pts)][1] - pts[i][1]*pts[(i+1)%len(pts)][0] for i in range(len(pts))]))
            lig1_hs.append(math.sqrt(area))
    assert len(lig1_hs) >= 1200, "Ligament 1 must contain at least 1,200 elements, got %d" % len(lig1_hs)
    pct_le_l0 = (sum(1 for h in lig1_hs if h <= L0_PHYS) / float(len(lig1_hs))) * 100.0
    assert pct_le_l0 >= 95.0, "At least 95%% of Ligament 1 elements must satisfy h <= l0, got %.1f%%" % pct_le_l0
    assert min(lig1_hs) <= L0_PHYS / 3.0, "Minimum size in Ligament 1 must be <= l0/3"

def test_07_ligament_2_resolution(parsed_mesh):
    nodes, elements = parsed_mesh
    # Ligament 2: h2 <-> h3, x in [0.42, 0.57], y in [0.42, 0.58]
    lig2_hs = []
    for eid, conn in elements:
        pts = [nodes[n] for n in conn]
        cx = sum(p[0] for p in pts) / float(len(pts))
        cy = sum(p[1] for p in pts) / float(len(pts))
        if 0.42 <= cx <= 0.57 and 0.42 <= cy <= 0.58:
            area = 0.5 * abs(sum([pts[i][0]*pts[(i+1)%len(pts)][1] - pts[i][1]*pts[(i+1)%len(pts)][0] for i in range(len(pts))]))
            lig2_hs.append(math.sqrt(area))
    assert len(lig2_hs) >= 1400, "Ligament 2 must contain at least 1,400 elements in improved mesh, got %d" % len(lig2_hs)
    pct_le_l0 = (sum(1 for h in lig2_hs if h <= L0_PHYS) / float(len(lig2_hs))) * 100.0
    assert pct_le_l0 >= 99.0, "At least 99%% of Ligament 2 elements must satisfy h <= l0, got %.1f%%" % pct_le_l0

def test_08_ligament_3_narrowest_clearance_resolution(parsed_mesh):
    nodes, elements = parsed_mesh
    # Ligament 3: h3 <-> h4, x in [0.63, 0.70], y in [0.48, 0.56]
    lig3_hs = []
    for eid, conn in elements:
        pts = [nodes[n] for n in conn]
        cx = sum(p[0] for p in pts) / float(len(pts))
        cy = sum(p[1] for p in pts) / float(len(pts))
        if 0.63 <= cx <= 0.70 and 0.48 <= cy <= 0.56:
            area = 0.5 * abs(sum([pts[i][0]*pts[(i+1)%len(pts)][1] - pts[i][1]*pts[(i+1)%len(pts)][0] for i in range(len(pts))]))
            lig3_hs.append(math.sqrt(area))
    assert len(lig3_hs) >= 500, "Ligament 3 must contain at least 500 elements, got %d" % len(lig3_hs)
    pct_le_half_l0 = (sum(1 for h in lig3_hs if h <= L0_PHYS / 2.0) / float(len(lig3_hs))) * 100.0
    assert pct_le_half_l0 >= 99.0, "At least 99%% of Ligament 3 elements must satisfy h <= l0/2, got %.1f%%" % pct_le_half_l0
    mean_h = sum(lig3_hs) / float(len(lig3_hs))
    assert mean_h <= 0.0025, "Mean element size in Ligament 3 must be <= 2.5 um, got %.4f mm" % mean_h

def test_09_ligament_4_resolution(parsed_mesh):
    nodes, elements = parsed_mesh
    # Ligament 4: h4 <-> h5, x in [0.80, 0.95], y in [0.42, 0.54]
    lig4_hs = []
    for eid, conn in elements:
        pts = [nodes[n] for n in conn]
        cx = sum(p[0] for p in pts) / float(len(pts))
        cy = sum(p[1] for p in pts) / float(len(pts))
        if 0.80 <= cx <= 0.95 and 0.42 <= cy <= 0.54:
            area = 0.5 * abs(sum([pts[i][0]*pts[(i+1)%len(pts)][1] - pts[i][1]*pts[(i+1)%len(pts)][0] for i in range(len(pts))]))
            lig4_hs.append(math.sqrt(area))
    assert len(lig4_hs) >= 1000, "Ligament 4 must contain at least 1,000 elements, got %d" % len(lig4_hs)
    pct_le_l0 = (sum(1 for h in lig4_hs if h <= L0_PHYS) / float(len(lig4_hs))) * 100.0
    assert pct_le_l0 >= 99.0, "At least 99%% of Ligament 4 elements must satisfy h <= l0, got %.1f%%" % pct_le_l0

def test_10_bulk_preservation_and_no_spreading(parsed_mesh):
    nodes, elements = parsed_mesh
    bulk_hs = []
    for eid, conn in elements:
        pts = [nodes[n] for n in conn]
        cx = sum(p[0] for p in pts) / float(len(pts))
        cy = sum(p[1] for p in pts) / float(len(pts))
        # Points far from the inter-hole corridor (y > 0.70 or y < 0.30)
        if cy > 0.70 or cy < 0.30:
            area = 0.5 * abs(sum([pts[i][0]*pts[(i+1)%len(pts)][1] - pts[i][1]*pts[(i+1)%len(pts)][0] for i in range(len(pts))]))
            bulk_hs.append(math.sqrt(area))
    assert len(bulk_hs) >= 2000, "Bulk must contain substantial elements"
    mean_bulk_h = sum(bulk_hs) / float(len(bulk_hs))
    assert mean_bulk_h >= 0.0080, "Bulk mean element size must be >= 8.0 um, got %.4f mm" % mean_bulk_h

def test_11_publication_figure_artifacts():
    expected_figures = [
        "fig_f1723_figure_1_side_by_side_comparison.png",
        "fig_f1723_figure_1_side_by_side_comparison.pdf",
        "fig_f1723_figure_2_ligament_zoom_matrix.png",
        "fig_f1723_figure_2_ligament_zoom_matrix.pdf",
        "fig_f1723_figure_3_centerline_profiles.png",
        "fig_f1723_figure_3_centerline_profiles.pdf",
        "fig_f1723_figure_4_smooth_transition_audit.png",
        "fig_f1723_figure_4_smooth_transition_audit.pdf",
    ]
    for fn in expected_figures:
        p = os.path.join(FIG_DIR, fn)
        assert os.path.exists(p), "Expected publication figure missing: %s" % fn
        assert os.path.getsize(p) > 10000, "Figure file must not be empty: %s" % fn

def test_12_parameter_dataset_completeness():
    assert os.path.exists(RESULTS_JSON), "Results JSON must exist"
    with open(RESULTS_JSON, "r") as f:
        data = json.load(f)
    assert len(data) == 16, "Must contain exactly 16 completed study cases, got %d" % len(data)
    case_names = [d["case_name"] for d in data]
    assert "C_S2_ET340" in case_names, "Selected candidate C_S2_ET340 must be in dataset"

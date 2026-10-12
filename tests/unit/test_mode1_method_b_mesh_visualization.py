"""
test_mode1_method_b_mesh_visualization.py
-----------------------------------------
Unit tests verifying the Method B native adaptive mesh visualization package,
geometry parsing, topological integrity, crack seam duplicate node pairs,
refinement density contrast, and generated publication figure artifacts.

Task: F1427-MODE1-METHOD-B-MESH-VISUALIZATION-AND-C1-SUBMISSION
"""

import os
import sys
import math
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.visualization.plot_mode1_method_b_adaptive_mesh import (
    parse_abaqus_mesh,
    compute_mesh_statistics,
    find_crack_seam_nodes,
    polygon_area
)

ADAPTED_INP = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "38_method_b_native_final_14k", "M1_MB_NATIVE_FINAL_1S.inp")
COARSE_INP = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "method_b_preflight_decks", "M1-MB-1S.inp")
FIGURES_DIR = os.path.join(REPO_ROOT, "results", "figures", "mode1_method_b_mesh")
README_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "38_method_b_native_final_14k", "README_MESH_VISUALIZATION.md")
SCRIPT_PATH = os.path.join(REPO_ROOT, "scripts", "visualization", "plot_mode1_method_b_adaptive_mesh.py")


def test_adapted_mesh_topology_and_element_counts():
    """Verifies that Method B adapted mesh parses exactly 14,646 nodes and 14,677 unique elements."""
    assert os.path.exists(ADAPTED_INP), f"Missing input deck: {ADAPTED_INP}"
    nodes, quads, tris = parse_abaqus_mesh(ADAPTED_INP)
    
    assert len(nodes) == 14646, f"Expected 14,646 mesh nodes, got {len(nodes)}"
    assert len(quads) == 14244, f"Expected 14,244 quad elements, got {len(quads)}"
    assert len(tris) == 433, f"Expected 433 triangle elements, got {len(tris)}"
    assert len(quads) + len(tris) == 14677, "Expected 14,677 total physical elements"
    
    # Bounding box verification
    xs = [c[0] for c in nodes.values()]
    ys = [c[1] for c in nodes.values()]
    assert min(xs) == pytest.approx(0.0, abs=1e-6)
    assert max(xs) == pytest.approx(1.0, abs=1e-6)
    assert min(ys) == pytest.approx(0.0, abs=1e-6)
    assert max(ys) == pytest.approx(1.0, abs=1e-6)


def test_coarse_mesh_topology_and_element_counts():
    """Verifies that coarse baseline mesh parses exactly 2,988 nodes and 2,906 unique elements."""
    assert os.path.exists(COARSE_INP), f"Missing input deck: {COARSE_INP}"
    nodes, quads, tris = parse_abaqus_mesh(COARSE_INP)
    
    assert len(nodes) == 2988, f"Expected 2,988 mesh nodes, got {len(nodes)}"
    assert len(quads) == 2818, f"Expected 2,818 quad elements, got {len(quads)}"
    assert len(tris) == 88, f"Expected 88 triangle elements, got {len(tris)}"
    assert len(quads) + len(tris) == 2906, "Expected 2,906 total physical elements"
    
    # Bounding box verification
    xs = [c[0] for c in nodes.values()]
    ys = [c[1] for c in nodes.values()]
    assert min(xs) == pytest.approx(0.0, abs=1e-6)
    assert max(xs) == pytest.approx(1.0, abs=1e-6)
    assert min(ys) == pytest.approx(0.0, abs=1e-6)
    assert max(ys) == pytest.approx(1.0, abs=1e-6)


def test_crack_seam_flank_and_tip_topology():
    """Verifies duplicate node pairs along crack slit and singleton tip node for both meshes."""
    # Adapted mesh
    nodes_a, _, _ = parse_abaqus_mesh(ADAPTED_INP)
    seam_a, pairs_a, single_a, tip_a = find_crack_seam_nodes(nodes_a)
    assert len(seam_a) == 125, f"Expected 125 seam nodes in adapted mesh, got {len(seam_a)}"
    assert len(pairs_a) == 62, f"Expected 62 duplicate pairs in adapted mesh, got {len(pairs_a)}"
    assert len(tip_a) == 1, f"Expected 1 tip node in adapted mesh, got {len(tip_a)}"
    assert tip_a[0] == 135, f"Expected tip node ID 135 in adapted mesh, got {tip_a[0]}"
    
    # Coarse mesh
    nodes_c, _, _ = parse_abaqus_mesh(COARSE_INP)
    seam_c, pairs_c, single_c, tip_c = find_crack_seam_nodes(nodes_c)
    assert len(seam_c) == 51, f"Expected 51 seam nodes in coarse mesh, got {len(seam_c)}"
    assert len(pairs_c) == 25, f"Expected 25 duplicate pairs in coarse mesh, got {len(pairs_c)}"
    assert len(tip_c) == 1, f"Expected 1 tip node in coarse mesh, got {len(tip_c)}"
    assert tip_c[0] == 97, f"Expected tip node ID 97 in coarse mesh, got {tip_c[0]}"


def test_element_sizing_and_refinement_contrast():
    """Verifies that crack-tip element sizing achieves >= 10x spatial refinement and >= 100x area density contrast."""
    nodes_a, quads_a, tris_a = parse_abaqus_mesh(ADAPTED_INP)
    elems_a = compute_mesh_statistics(nodes_a, quads_a, tris_a)
    elems_a.sort(key=lambda x: x['d_tip'])
    tip_elem_a = elems_a[0]
    h_tip_a = tip_elem_a['h'] * 1000.0  # um
    area_tip_a = tip_elem_a['area'] * 1e6  # um^2
    
    nodes_c, quads_c, tris_c = parse_abaqus_mesh(COARSE_INP)
    elems_c = compute_mesh_statistics(nodes_c, quads_c, tris_c)
    elems_c.sort(key=lambda x: x['d_tip'])
    tip_elem_c = elems_c[0]
    h_tip_c = tip_elem_c['h'] * 1000.0  # um
    area_tip_c = tip_elem_c['area'] * 1e6  # um^2
    
    # Adapted tip size must be ~1.91-1.98 um (well below l0 = 7.5 um)
    assert 1.5 <= h_tip_a <= 2.2, f"Adapted tip h expected in [1.5, 2.2] um, got {h_tip_a:.3f}"
    # Coarse tip size must be ~20 um
    assert 18.0 <= h_tip_c <= 22.0, f"Coarse tip h expected in [18, 22] um, got {h_tip_c:.3f}"
    
    # Ratios
    h_ratio = h_tip_c / h_tip_a
    area_ratio = area_tip_c / area_tip_a
    assert h_ratio >= 10.0, f"Expected >= 10x spatial sizing refinement, got {h_ratio:.2f}x"
    assert area_ratio >= 100.0, f"Expected >= 100x area density contrast, got {area_ratio:.1f}x"
    
    # Total domain area conservation
    total_area_a = sum(el['area'] for el in elems_a)
    total_area_c = sum(el['area'] for el in elems_c)
    assert total_area_a == pytest.approx(1.0, abs=1e-6)
    assert total_area_c == pytest.approx(1.0, abs=1e-6)


def test_generated_figures_existence_and_integrity():
    """Verifies that all 8 publication figure files (PNG + PDF) exist and are non-empty."""
    expected_files = [
        ("fig_mode1_method_b_native_full_mesh.png", 500_000),
        ("fig_mode1_method_b_native_full_mesh.pdf", 50_000),
        ("fig_mode1_method_b_native_crack_tip_zoom.png", 500_000),
        ("fig_mode1_method_b_native_crack_tip_zoom.pdf", 50_000),
        ("fig_mode1_method_b_vs_coarse_comparison.png", 500_000),
        ("fig_mode1_method_b_vs_coarse_comparison.pdf", 50_000),
        ("fig_mode1_method_b_element_size_distribution.png", 500_000),
        ("fig_mode1_method_b_element_size_distribution.pdf", 50_000),
    ]
    
    for filename, min_bytes in expected_files:
        path = os.path.join(FIGURES_DIR, filename)
        assert os.path.exists(path), f"Expected figure file missing: {path}"
        file_size = os.path.getsize(path)
        assert file_size >= min_bytes, f"Figure {filename} size {file_size} < expected minimum {min_bytes}"


def test_readme_and_standalone_script_consistency():
    """Verifies that README documentation and standalone visualization script exist and are valid."""
    assert os.path.exists(README_PATH), f"Missing README: {README_PATH}"
    with open(README_PATH, 'r') as f:
        readme_content = f.read()
    assert "14,677" in readme_content
    assert "2,906" in readme_content
    assert "44,031" in readme_content
    assert "1.91" in readme_content
    assert "105" in readme_content
    
    assert os.path.exists(SCRIPT_PATH), f"Missing script: {SCRIPT_PATH}"
    with open(SCRIPT_PATH, 'r') as f:
        script_content = f.read()
    assert "PolyCollection" in script_content
    assert "parse_abaqus_mesh" in script_content

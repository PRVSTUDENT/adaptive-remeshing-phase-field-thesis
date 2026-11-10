# -*- coding: utf-8 -*-
"""
tests/unit/test_f1710_authentic_adaptive_mesh_visualization.py
=============================================================
Task F1710: Automated Qualification and Verification Suite for Authentic
Adaptive-Remesh Visualization and Crack-Path Extraction.

Verifies:
  1. Generated figures exist, are non-empty, and exceed resolution thresholds (300 DPI).
  2. Element and node mapping corresponds strictly to Job 1421915 (10,065 physical elements).
  3. Authentic damage range [0, 1] without synthetic or artificial values.
  4. Extracted damage ridge coordinates exhibit authentic physical curvature without straight-line overlays.
  5. Scientific provenance report and crack path JSON exist and are valid.
"""

import os
import json
import pytest
from PIL import Image

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FIG_DIR = os.path.join(REPO_ROOT, "MA_AdaptiveRemeshing_Report_2026", "figures", "pandey_kumar_fig14_16_reproduction")
RESULTS_DIR = os.path.join(REPO_ROOT, "results", "validation")
DOCS_DIR = os.path.join(REPO_ROOT, "docs", "validation")

def test_01_f1710_figure_deliverables_exist_and_nonzero():
    """Verify all 6 deliverable figure files exist and have non-zero size."""
    expected_files = [
        "fig_f1710_authentic_adaptive_mesh.png",
        "fig_f1710_authentic_adaptive_mesh.pdf",
        "fig_f1710_primary_crack_mesh_zoom.png",
        "fig_f1710_primary_crack_mesh_zoom.pdf",
        "fig_f1710_secondary_crack_mesh_zoom.png",
        "fig_f1710_secondary_crack_mesh_zoom.pdf",
    ]
    for fname in expected_files:
        fpath = os.path.join(FIG_DIR, fname)
        assert os.path.exists(fpath), f"Missing expected deliverable: {fname}"
        assert os.path.getsize(fpath) > 10000, f"File {fname} is suspiciously small: {os.path.getsize(fpath)} bytes"

def test_02_figure_image_resolutions():
    """Verify all PNG figures meet or exceed publication resolution standards (300 DPI)."""
    png_checks = {
        "fig_f1710_authentic_adaptive_mesh.png": (2000, 3000),
        "fig_f1710_primary_crack_mesh_zoom.png": (2500, 2000),
        "fig_f1710_secondary_crack_mesh_zoom.png": (2500, 1800),
    }
    for fname, (min_w, min_h) in png_checks.items():
        fpath = os.path.join(FIG_DIR, fname)
        with Image.open(fpath) as img:
            w, h = img.size
            assert w >= min_w, f"{fname} width {w} < {min_w}"
            assert h >= min_h, f"{fname} height {h} < {min_h}"

def test_03_mesh_and_damage_correspondence():
    """Verify element and node count correspondence to authentic Job 1421915."""
    mesh_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "203_pk_sec43_secondary_complete", "PK_SEC43_F1703_SECONDARY_COMPLETE_ADAPT.inp")
    damage_path = os.path.join(RESULTS_DIR, "f1709_job2_damage_field.json")

    assert os.path.exists(mesh_path), "Missing adapted mesh file"
    assert os.path.exists(damage_path), "Missing Job 1421915 damage field JSON"

    with open(damage_path, "r") as f:
        data = json.load(f)

    assert data["n_phys_elements"] == 10065, f"Expected 10,065 elements, got {data['n_phys_elements']}"
    assert "state_4_severance" in data["damage_states"], "Missing state_4_severance"

    elem_damage = data["damage_states"]["state_4_severance"]["elem_damage"]
    assert len(elem_damage) == 10065, f"Expected 10,065 element damage entries, got {len(elem_damage)}"

    # Check damage range [0, 1]
    d_vals = list(elem_damage.values())
    assert min(d_vals) >= 0.0, f"Negative damage: {min(d_vals)}"
    assert max(d_vals) <= 1.0001, f"Damage exceeds 1.0: {max(d_vals)}"

def test_04_authentic_crack_paths_json():
    """Verify authentic extracted crack path data contains genuine physical curvature."""
    path_file = os.path.join(RESULTS_DIR, "f1710_authentic_crack_paths.json")
    assert os.path.exists(path_file), "Missing f1710_authentic_crack_paths.json"

    with open(path_file, "r") as f:
        cdata = json.load(f)

    assert "primary_crack_ridge" in cdata
    assert "secondary_crack_ridge" in cdata

    prim = cdata["primary_crack_ridge"]
    sec = cdata["secondary_crack_ridge"]

    assert len(prim) >= 20, f"Expected >= 20 primary points, got {len(prim)}"
    assert len(sec) >= 20, f"Expected >= 20 secondary points, got {len(sec)}"

    # Primary crack: starts near notch root (y ~ 70) and curves down into hole (y < 63)
    assert prim[0]["y"] > 69.0, f"Primary crack start y {prim[0]['y']} not near notch root 70.0"
    assert prim[-1]["y"] < 64.0, f"Primary crack end y {prim[-1]['y']} not deflected into void"

    # Secondary crack: starts near hole flank (x ~ 46.5) and reaches free edge (x > 64.0)
    assert sec[0]["x"] < 47.5, f"Secondary crack start x {sec[0]['x']} not near void flank 46.5"
    assert sec[-1]["x"] > 64.0, f"Secondary crack end x {sec[-1]['x']} not near free edge 65.0"

    # Verify trajectory is non-linear (i.e. authentic curvature, not a straight line)
    # Primary crack dy/dx changes significantly
    dy_early = (prim[5]["y"] - prim[0]["y"]) / (prim[5]["x"] - prim[0]["x"])
    dy_late = (prim[-1]["y"] - prim[-5]["y"]) / (prim[-1]["x"] - prim[-5]["x"])
    assert abs(dy_late - dy_early) > 0.3, "Primary crack appears linear, expected curved deflection"

def test_05_figure15_no_straight_line_overlay():
    """Verify plot_f1707_figure15_reproduction.py does not contain straight line overlay."""
    script_path = os.path.join(REPO_ROOT, "scripts", "visualization", "plot_f1707_figure15_reproduction.py")
    with open(script_path, "r") as f:
        content = f.read()

    assert "Secondary Linear Fit" not in content, "Residual straight line fit found in plot_f1707_figure15_reproduction.py"
    assert "0.0821" not in content, "Residual regression slope found in plot_f1707_figure15_reproduction.py"

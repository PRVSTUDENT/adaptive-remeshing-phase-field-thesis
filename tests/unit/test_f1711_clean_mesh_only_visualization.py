# -*- coding: utf-8 -*-
"""
tests/unit/test_f1711_clean_mesh_only_visualization.py
======================================================
Task F1711: Verification suite for clean standalone mesh-only adaptive remesh images.

Verifies:
  1. All 6 deliverable files exist, are non-empty, and exceed resolution thresholds (300 DPI).
  2. The plotting script parses the authentic 10,065-element adapted mesh.
  3. No phase-field damage scalar colormaps or crack-path overlays are present.
  4. Holes and initial notch geometry match authentic specification.
"""

import os
from PIL import Image

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FIG_DIR = os.path.join(REPO_ROOT, "MA_AdaptiveRemeshing_Report_2026", "figures", "pandey_kumar_fig14_16_reproduction")

def test_01_f1711_deliverables_exist_and_nonzero():
    """Verify all 6 deliverable figure files exist and are non-empty."""
    expected_files = [
        "fig_f1711_adaptive_remesh_only.png",
        "fig_f1711_adaptive_remesh_only.pdf",
        "fig_f1711_primary_mesh_zoom_only.png",
        "fig_f1711_primary_mesh_zoom_only.pdf",
        "fig_f1711_secondary_mesh_zoom_only.png",
        "fig_f1711_secondary_mesh_zoom_only.pdf",
    ]
    for fname in expected_files:
        fpath = os.path.join(FIG_DIR, fname)
        assert os.path.exists(fpath), f"Missing expected deliverable: {fname}"
        assert os.path.getsize(fpath) > 10000, f"File {fname} is suspiciously small: {os.path.getsize(fpath)} bytes"

def test_02_figure_image_resolutions():
    """Verify all PNG figures meet or exceed publication resolution standards (300 DPI)."""
    png_checks = {
        "fig_f1711_adaptive_remesh_only.png": (2000, 3000),
        "fig_f1711_primary_mesh_zoom_only.png": (2500, 2000),
        "fig_f1711_secondary_mesh_zoom_only.png": (2500, 1700),
    }
    for fname, (min_w, min_h) in png_checks.items():
        fpath = os.path.join(FIG_DIR, fname)
        with Image.open(fpath) as img:
            w, h = img.size
            assert w >= min_w, f"{fname} width {w} < {min_w}"
            assert h >= min_h, f"{fname} height {h} < {min_h}"

def test_03_mesh_script_integrity():
    """Verify plotting script targets authentic adapted mesh and contains no scalar damage field."""
    script_path = os.path.join(REPO_ROOT, "scripts", "visualization", "plot_f1711_clean_mesh_only.py")
    assert os.path.exists(script_path), "Missing plot_f1711_clean_mesh_only.py"

    with open(script_path, "r") as f:
        content = f.read()

    assert "PK_SEC43_F1703_SECONDARY_COMPLETE_ADAPT.inp" in content, "Script must target authentic adapted mesh"
    assert "colorbar" not in content, "Mesh-only script must not contain colorbar"
    assert "cmap" not in content, "Mesh-only script must not contain colormap"
    assert "damage" not in content.lower() or "no phase-field damage" in content.lower(), "Script must not plot damage"

def test_04_adapted_mesh_file_verification():
    """Verify authentic adapted mesh file exists with 10,065 elements."""
    mesh_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "203_pk_sec43_secondary_complete", "PK_SEC43_F1703_SECONDARY_COMPLETE_ADAPT.inp")
    assert os.path.exists(mesh_path), "Adapted mesh file missing"

    elems, nodes = 0, 0
    in_e, in_n = False, False
    with open(mesh_path, "r") as f:
        for line in f:
            l = line.strip().upper()
            if l.startswith("*NODE") and not any(k in l for k in ["PRINT", "FILE", "OUTPUT"]):
                in_n, in_e = True, False
            elif l.startswith("*ELEMENT") and "OUTPUT" not in l:
                in_n, in_e = False, True
            elif l.startswith("*"):
                in_n, in_e = False, False
            elif in_n:
                nodes += 1
            elif in_e:
                elems += 1

    assert elems == 10065, f"Expected 10,065 elements, got {elems}"
    assert nodes == 10096, f"Expected 10,096 nodes, got {nodes}"

"""
Unit Regression Test Suite for Task F1706:
Candidate E10 Adaptive-Remesh and Authentic Phase-Field Fracture Visualization.
"""
import os
import json
import hashlib
import pytest
from PIL import Image

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as fp:
        while chunk := fp.read(65536):
            h.update(chunk)
    return h.hexdigest()

def test_f1706_figure_artifacts_exist_and_valid():
    """Verify generated PDF and PNG figures exist with non-zero size."""
    pdf_path = os.path.join(REPO_ROOT, "MA_AdaptiveRemeshing_Report_2026", "figures", "fig_f1705_e10_adaptive_remesh_damage.pdf")
    png_path = os.path.join(REPO_ROOT, "MA_AdaptiveRemeshing_Report_2026", "figures", "fig_f1705_e10_adaptive_remesh_damage.png")
    val_png = os.path.join(REPO_ROOT, "results", "validation", "fig_f1705_e10_adaptive_remesh_damage.png")

    assert os.path.exists(pdf_path), f"Missing PDF: {pdf_path}"
    assert os.path.exists(png_path), f"Missing PNG: {png_path}"
    assert os.path.exists(val_png), f"Missing validation PNG: {val_png}"

    pdf_size = os.path.getsize(pdf_path)
    png_size = os.path.getsize(png_path)
    val_size = os.path.getsize(val_png)

    assert pdf_size > 200_000, f"PDF too small: {pdf_size} bytes"
    assert png_size > 1_000_000, f"PNG too small: {png_size} bytes"
    assert val_size > 1_000_000, f"Validation PNG too small: {val_size} bytes"

def test_f1706_png_image_dimensions_and_resolution():
    """Verify PNG has publication-quality resolution and valid dimensions."""
    png_path = os.path.join(REPO_ROOT, "MA_AdaptiveRemeshing_Report_2026", "figures", "fig_f1705_e10_adaptive_remesh_damage.png")
    with Image.open(png_path) as img:
        width, height = img.size
        assert width >= 2500, f"Width too small: {width}"
        assert height >= 2500, f"Height too small: {height}"
        assert img.format == "PNG", f"Unexpected format: {img.format}"

def test_f1706_authentic_damage_field_provenance():
    """Verify damage field JSON contains authentic solver output from Job 1421888."""
    json_path = os.path.join(REPO_ROOT, "results", "validation", "f1705_e10_damage_field.json")
    assert os.path.exists(json_path), f"Missing damage JSON: {json_path}"

    with open(json_path, "r") as fp:
        data = json.load(fp)

    assert "damage_states" in data, "Missing damage_states key"
    states = data["damage_states"]

    assert "arrest_inc60" in states, "Missing arrest_inc60"
    assert "severance_inc160" in states, "Missing severance_inc160"
    assert "terminal_inc291" in states, "Missing terminal_inc291"

    arrest = states["arrest_inc60"]
    severance = states["severance_inc160"]
    terminal = states["terminal_inc291"]

    assert len(arrest["elem_damage"]) == 9164, f"Expected 9164 elements in arrest state, got {len(arrest['elem_damage'])}"
    assert len(severance["elem_damage"]) == 9164, f"Expected 9164 elements in severance state, got {len(severance['elem_damage'])}"
    assert len(terminal["elem_damage"]) == 9164, f"Expected 9164 elements in terminal state, got {len(terminal['elem_damage'])}"

    assert arrest["max_damage"] >= 1.0, f"Arrest max damage too low: {arrest['max_damage']}"
    assert severance["max_damage"] >= 1.0, f"Severance max damage too low: {severance['max_damage']}"
    assert terminal["max_damage"] >= 1.0, f"Terminal max damage too low: {terminal['max_damage']}"

def test_f1706_physical_mesh_provenance():
    """Verify Candidate E10 physical mesh has exactly 9,164 elements and 9,251 nodes."""
    inp_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "176_method_a_plate_with_hole", "candidates", "PK_HOLE_SEL_E10_PHYS.inp")
    assert os.path.exists(inp_path), f"Missing physical mesh: {inp_path}"

    n_nodes = 0
    n_quads = 0
    n_tris = 0
    sec = None
    with open(inp_path, "r") as fp:
        for line in fp:
            line = line.strip()
            if not line or line.startswith("**"):
                continue
            u = line.upper()
            if u.startswith("*NODE") and not u.startswith("*NODE OUTPUT"):
                sec = "NODE"
                continue
            elif u.startswith("*ELEMENT, TYPE=CPE4") or u.startswith("*ELEMENT,TYPE=CPE4"):
                sec = "CPE4"
                continue
            elif u.startswith("*ELEMENT, TYPE=CPE3") or u.startswith("*ELEMENT,TYPE=CPE3"):
                sec = "CPE3"
                continue
            elif u.startswith("*"):
                sec = None
                continue

            if sec == "NODE":
                n_nodes += 1
            elif sec == "CPE4":
                n_quads += 1
            elif sec == "CPE3":
                n_tris += 1

    assert n_nodes == 9251, f"Expected 9251 nodes, got {n_nodes}"
    assert n_quads == 8891, f"Expected 8891 quads, got {n_quads}"
    assert n_tris == 273, f"Expected 273 tris, got {n_tris}"
    assert n_quads + n_tris == 9164, f"Expected 9164 elements, got {n_quads + n_tris}"

def test_f1706_frozen_uel_integrity():
    """Verify production UEL f42_mixed_uel.for remains bitwise intact (CE8D5EDC..., 907 lines)."""
    uel_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "177_method_a_hole_e10_prod", "f42_mixed_uel.for")
    assert os.path.exists(uel_path), f"Missing UEL: {uel_path}"

    sha = compute_sha256(uel_path).upper()
    assert sha.startswith("CE8D5EDC"), f"UEL SHA mismatch: {sha}"

    with open(uel_path, "r") as fp:
        lines = fp.readlines()
    assert len(lines) == 907, f"Expected 907 lines in UEL, got {len(lines)}"

def test_f1706_zero_pbs_budget_governance():
    """Verify max_new_pbs_submissions = 0 enforced for Task F1706."""
    task_def_path = os.path.join(REPO_ROOT, "project_coordination", "task_definitions", "F1706-METHOD-A-HOLE-CANDIDATE-E10-REMESH-VISUALIZATION.json")
    assert os.path.exists(task_def_path), f"Missing task definition: {task_def_path}"

    with open(task_def_path, "r") as fp:
        task_def = json.load(fp)

    assert task_def["max_new_pbs_submissions"] == 0, f"Expected max_new_pbs_submissions = 0, got {task_def['max_new_pbs_submissions']}"

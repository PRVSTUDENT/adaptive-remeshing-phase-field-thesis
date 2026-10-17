"""
Unit tests for Task F1540: Method C Authentic Mesh Figures Export & Packaging.
Verifies mesh provenance, exact element counts, figure existence, file integrity,
and zip package contents across all five adaptive-remeshing stages.
"""

import os
import sys
import zipfile
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "state_transfer"))
from mode1_state_transfer_engine import parse_mode1_input_deck

FIGURES_DIR = REPO_ROOT / "method_c_mesh_figures"
PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'

STAGE_SPECS = [
    {
        "stage": 0,
        "name": "Stage 0 (Initial Coarse)",
        "deck": REPO_ROOT / "models/pandey_kumar_mode1/89_mode1_preanalysis_uel_canonical_2906/PK_M1_JOB1_UEL_2906.inp",
        "expected_elements": 2906,
        "full_png": "mesh_stage0_coarse_2906.png",
        "closeup_png": "closeup_stage0_coarse_2906.png",
    },
    {
        "stage": 1,
        "name": "Stage 1 (Cycle 1)",
        "deck": REPO_ROOT / "models/pandey_kumar_mode1/57_method_c_stage_c1_2_cycle1_continuation/M1_MC_STAGE_C1_2_CYCLE1_CONT.inp",
        "expected_elements": 17913,
        "full_png": "mesh_stage1_cycle1_17913.png",
        "closeup_png": "closeup_stage1_cycle1_17913.png",
    },
    {
        "stage": 2,
        "name": "Stage 2 (Cycle 2)",
        "deck": REPO_ROOT / "models/pandey_kumar_mode1/59_method_c_stage_c1_2_cycle2_continuation/M1_MC_STAGE_C1_2_CYCLE2_CONT.inp",
        "expected_elements": 21546,
        "full_png": "mesh_stage2_cycle2_21546.png",
        "closeup_png": "closeup_stage2_cycle2_21546.png",
    },
    {
        "stage": 3,
        "name": "Stage 3 (Cycle 3)",
        "deck": REPO_ROOT / "models/pandey_kumar_mode1/61_method_c_stage_c1_2_cycle3_continuation/M1_MC_STAGE_C1_2_CYCLE3_CONT.inp",
        "expected_elements": 25085,
        "full_png": "mesh_stage3_cycle3_25085.png",
        "closeup_png": "closeup_stage3_cycle3_25085.png",
    },
    {
        "stage": 4,
        "name": "Stage 4 (Cycle 4)",
        "deck": REPO_ROOT / "models/pandey_kumar_mode1/62_method_c_stage_c1_2_cycle4_continuation/M1_MC_STAGE_C1_2_CYCLE4_CONT.inp",
        "expected_elements": 29293,
        "full_png": "mesh_stage4_cycle4_29293.png",
        "closeup_png": "closeup_stage4_cycle4_29293.png",
    },
]

def test_deck_existence_and_element_counts():
    """Verify that all five authentic input decks exist and parse to exact element counts."""
    for spec in STAGE_SPECS:
        deck_path = spec["deck"]
        assert deck_path.exists(), f"Input deck missing: {deck_path}"
        mesh = parse_mode1_input_deck(str(deck_path))
        num_physical_elements = len(mesh.elements_u1)
        assert num_physical_elements == spec["expected_elements"], (
            f"{spec['name']}: expected {spec['expected_elements']} elements, got {num_physical_elements}"
        )

def test_individual_full_mesh_figures():
    """Verify that all 5 individual full-specimen figures exist, are non-empty, and are valid PNGs."""
    for spec in STAGE_SPECS:
        fig_path = FIGURES_DIR / spec["full_png"]
        assert fig_path.exists(), f"Full mesh figure missing: {fig_path}"
        assert fig_path.stat().st_size > 500_000, f"Full mesh figure {fig_path.name} unexpectedly small ({fig_path.stat().st_size} bytes)"
        with open(fig_path, "rb") as f:
            header = f.read(8)
            assert header == PNG_SIGNATURE, f"File {fig_path.name} is not a valid PNG"

def test_individual_crack_tip_closeup_figures():
    """Verify that all 5 individual crack-tip closeup figures exist, are non-empty, and are valid PNGs."""
    for spec in STAGE_SPECS:
        fig_path = FIGURES_DIR / spec["closeup_png"]
        assert fig_path.exists(), f"Closeup figure missing: {fig_path}"
        assert fig_path.stat().st_size > 300_000, f"Closeup figure {fig_path.name} unexpectedly small ({fig_path.stat().st_size} bytes)"
        with open(fig_path, "rb") as f:
            header = f.read(8)
            assert header == PNG_SIGNATURE, f"File {fig_path.name} is not a valid PNG"

def test_multi_panel_comparison_figures():
    """Verify that both composite multi-panel comparison figures exist and are high-resolution."""
    full_comp = FIGURES_DIR / "method_c_full_meshes_comparison.png"
    assert full_comp.exists(), f"Full comparison figure missing: {full_comp}"
    assert full_comp.stat().st_size > 2_000_000, f"Full comparison figure unexpectedly small: {full_comp.stat().st_size} bytes"
    with open(full_comp, "rb") as f:
        assert f.read(8) == PNG_SIGNATURE

    closeup_comp = FIGURES_DIR / "method_c_crack_tip_closeups_comparison.png"
    assert closeup_comp.exists(), f"Closeup comparison figure missing: {closeup_comp}"
    assert closeup_comp.stat().st_size > 2_000_000, f"Closeup comparison figure unexpectedly small: {closeup_comp.stat().st_size} bytes"
    with open(closeup_comp, "rb") as f:
        assert f.read(8) == PNG_SIGNATURE

def test_zip_archive_packaging():
    """Verify that the zip archive contains all 12 authentic PNG figures."""
    zip_path = FIGURES_DIR / "method_c_mesh_figures.zip"
    assert zip_path.exists(), f"Zip package missing: {zip_path}"
    assert zip_path.stat().st_size > 10_000_000, f"Zip package unexpectedly small: {zip_path.stat().st_size} bytes"

    expected_files = set()
    for spec in STAGE_SPECS:
        expected_files.add(spec["full_png"])
        expected_files.add(spec["closeup_png"])
    expected_files.add("method_c_full_meshes_comparison.png")
    expected_files.add("method_c_crack_tip_closeups_comparison.png")

    with zipfile.ZipFile(zip_path, 'r') as zf:
        archive_files = set(zf.namelist())
        assert expected_files == archive_files, (
            f"Zip contents mismatch. Expected: {expected_files}, Got: {archive_files}"
        )

    # Root mirror check
    root_zip = REPO_ROOT / "method_c_mesh_figures.zip"
    assert root_zip.exists(), f"Root mirror zip missing: {root_zip}"
    assert root_zip.stat().st_size == zip_path.stat().st_size, "Root mirror zip size mismatch"

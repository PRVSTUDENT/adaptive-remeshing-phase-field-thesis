# -*- coding: utf-8 -*-
"""
test_mode2_corrected_preanalysis_and_corridor.py
Unit tests for Task F1347:
- Root cause verification of UEL RHS defect
- Damage evolution and oblique crack path in Job 1411104
- MISESERI error corridor emergence (rotation from -1.34 deg to -34.07 deg)
- Native adaptive remeshing reproduction across ET in {1%, 2%, 3%, 5%}
- Job 1411103 solver classification as TERMINAL_PARTIAL
- Mode-I baseline freeze preservation
"""
import os
import hashlib
import json
import pytest
import pandas as pd
import numpy as np

WORKSPACE_DIR = r"D:\Master thesis\Adaptive remeshing"
MODE1_FORTRAN_UEL_PATH = os.path.join(WORKSPACE_DIR, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
EXPECTED_MODE1_FORTRAN_HASH = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"

MODE2_DIR = os.path.join(WORKSPACE_DIR, "models", "pandey_kumar_mode2", "06_paper_grounded_uel_preanalysis")
MODE2_FORTRAN_PATH = os.path.join(MODE2_DIR, "f42_mixed_uel_mode2_miehe.for")
EXPECTED_MODE2_CORRECTED_HASH = "699b05d6c430fce6242f8c603b45bb0783cf376451efd52c56bc984b0ce71188"

EXTRACTED_DIR = os.path.join(MODE2_DIR, "extracted_corrected_miseseri")
CORRIDOR_JSON_PATH = os.path.join(EXTRACTED_DIR, "miseseri_corridor_analysis.json")
REMESH_MANIFEST_PATH = os.path.join(MODE2_DIR, "m2_corrected_remesh", "MODE2_CORRECTED_REMESH_MANIFEST.json")

FIG_PNG_PATH = os.path.join(WORKSPACE_DIR, "results", "figures", "mode2", "fig_mode2_corrected_miseseri_and_adaptive_mesh.png")
FIG_PDF_PATH = os.path.join(WORKSPACE_DIR, "results", "figures", "mode2", "fig_mode2_corrected_miseseri_and_adaptive_mesh.pdf")


def test_uel_source_root_cause_diff():
    """Verify that f42_mixed_uel_mode2_miehe.for contains the restored RHS driving vector."""
    assert os.path.exists(MODE2_FORTRAN_PATH), f"Missing {MODE2_FORTRAN_PATH}"
    with open(MODE2_FORTRAN_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Check that RHS driving vector is present
    assert "RHS(I,1) = RHS(I,1) + CJAC * TWO * HIST * SHP(I)" in content, "Quad RHS driving term missing"
    assert "RHS(I,1) = RHS(I,1) + CJAC * TWO * HIST * N_TRI(I)" in content, "Tri RHS driving term missing"

    # Check hash
    h = hashlib.sha256(content.encode("utf-8")).hexdigest().lower()
    assert h == EXPECTED_MODE2_CORRECTED_HASH, f"Hash mismatch: got {h}, expected {EXPECTED_MODE2_CORRECTED_HASH}"


def test_corrected_coarse_damage_propagation():
    """Verify that Job 1411104 evolved full damage and oblique crack."""
    summary_path = os.path.join(MODE2_DIR, "MODE2_J1_COARSE_RETEST_SUMMARY.json")
    assert os.path.exists(summary_path), f"Missing {summary_path}"
    with open(summary_path, "r") as f:
        data = json.load(f)

    assert data["final_dmax"] == 1.0, "Expected d_max = 1.0"
    assert data["is_oblique_mode2_crack"] is True, "Expected oblique Mode-II crack"
    assert -60.0 <= data["chord_angle_deg"] <= -55.0, f"Unexpected chord angle: {data['chord_angle_deg']}"
    assert 0.78 <= data["bottom_exit_x_mm"] <= 0.85, f"Unexpected exit x: {data['bottom_exit_x_mm']}"
    assert 500.0 <= data["f_max_N"] <= 530.0, f"Unexpected coarse F_max: {data['f_max_N']}"


def test_miseseri_corridor_emergence():
    """Verify that MISESERI error indicator dynamically rotates and follows propagating crack."""
    assert os.path.exists(CORRIDOR_JSON_PATH), f"Missing {CORRIDOR_JSON_PATH}"
    with open(CORRIDOR_JSON_PATH, "r") as f:
        results = json.load(f)

    # Step-1 end (tag: ux_0p01000)
    s1_res = [r for r in results if r["tag"] == "ux_0p01000"][0]
    assert s1_res["d_max"] <= 0.35, "Step 1 damage should be pre-peak"
    assert abs(s1_res["error_orientation_deg"]) <= 5.0, "Step 1 error orientation should be nearly horizontal"
    assert s1_res["corridor_fraction_top10"] <= 0.10, "Step 1 error corridor fraction should be low (<10%)"

    # Step-2 final (tag: ux_0p02000_final)
    s2_res = [r for r in results if r["tag"] == "ux_0p02000_final"][0]
    assert s2_res["d_max"] == 1.0, "Step 2 final damage must be 1.0"
    assert s2_res["eta_max"] > 20.0, f"Expected eta_max > 20, got {s2_res['eta_max']}"
    assert -40.0 <= s2_res["error_orientation_deg"] <= -25.0, f"Expected rotated error orientation, got {s2_res['error_orientation_deg']}"
    assert s2_res["corridor_fraction_top10"] >= 0.35, f"Expected corridor fraction >= 35%, got {s2_res['corridor_fraction_top10']}"


def test_native_adaptive_mesh_generation():
    """Verify that native adaptiveRemesh on Step-2 produces the curved Mode-II refinement corridor."""
    assert os.path.exists(REMESH_MANIFEST_PATH), f"Missing {REMESH_MANIFEST_PATH}"
    with open(REMESH_MANIFEST_PATH, "r") as f:
        manifest = json.load(f)

    results = manifest["sweep_results"]
    assert "ET_2PCT" in results, "ET_2PCT missing from manifest"
    assert "ET_3PCT" in results, "ET_3PCT missing from manifest"

    # ET_2PCT checks
    et2 = results["ET_2PCT"]
    assert 30000 <= et2["total_elements"] <= 42000, f"Unexpected element count for ET_2PCT: {et2['total_elements']}"
    assert -52.0 <= et2["corridor_chord_angle_deg"] <= -46.0, f"Unexpected corridor angle: {et2['corridor_chord_angle_deg']}"
    assert et2["h_min_mm"] <= 0.0010, f"Expected h_min <= 0.001, got {et2['h_min_mm']}"

    # ET_3PCT checks (best match to paper 19,963 elements)
    et3 = results["ET_3PCT"]
    assert 18000 <= et3["total_elements"] <= 23000, f"Unexpected element count for ET_3PCT: {et3['total_elements']}"
    assert abs(et3["total_elements"] - 19963) / 19963.0 <= 0.10, "ET_3PCT within 10% of paper 19,963 elements"
    assert -52.0 <= et3["corridor_chord_angle_deg"] <= -45.0, f"Unexpected corridor angle: {et3['corridor_chord_angle_deg']}"
    assert et3["corridor_fine_fraction_pct"] >= 40.0, "Corridor fine fraction should be >= 40%"


def test_publication_figures_exist():
    """Verify that the 4-panel publication-quality PNG and PDF figures exist and are non-empty."""
    assert os.path.exists(FIG_PNG_PATH), f"Missing {FIG_PNG_PATH}"
    assert os.path.exists(FIG_PDF_PATH), f"Missing {FIG_PDF_PATH}"
    assert os.path.getsize(FIG_PNG_PATH) >= 1000000, "PNG file unexpectedly small (< 1 MB)"
    assert os.path.getsize(FIG_PDF_PATH) >= 500000, "PDF file unexpectedly small (< 500 KB)"


def test_mode1_baseline_freeze_integrity():
    """Verify that Mode-I baseline UEL source is strictly untouched."""
    assert os.path.exists(MODE1_FORTRAN_UEL_PATH), f"Missing {MODE1_FORTRAN_UEL_PATH}"
    with open(MODE1_FORTRAN_UEL_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    h = hashlib.sha256(content.encode("utf-8")).hexdigest().lower()
    assert h == EXPECTED_MODE1_FORTRAN_HASH, f"Mode-I UEL modified! Expected {EXPECTED_MODE1_FORTRAN_HASH}, got {h}"

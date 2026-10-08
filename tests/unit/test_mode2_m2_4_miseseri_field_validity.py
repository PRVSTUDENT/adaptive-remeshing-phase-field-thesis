#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode2_m2_4_miseseri_field_validity.py
Unit tests for Task F1336 Mode-II Gate M2-4 MISESERI Field Validity & Scale-Invariance.
"""

import os
import sys
import json
import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODE2_PRE_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode2", "06_paper_grounded_uel_preanalysis")
FIGURES_DIR = os.path.join(REPO_ROOT, "results", "figures", "mode2")

def test_deep_audit_summary_exists_and_valid():
    """Verify mode2_miseseri_deep_audit_summary.json exists and contains complete Step-1/Step-2 data."""
    summary_path = os.path.join(MODE2_PRE_DIR, "mode2_miseseri_deep_audit_summary.json")
    assert os.path.exists(summary_path), f"Summary JSON not found: {summary_path}"

    with open(summary_path, 'r') as f:
        summary = json.load(f)

    assert "Step-1" in summary
    assert "Step-2" in summary
    assert "ratios_step2_to_step1" in summary

    s1 = summary["Step-1"]
    s2 = summary["Step-2"]
    ratios = summary["ratios_step2_to_step1"]

    assert s1["num_elements"] == 2960
    assert s2["num_elements"] == 2960
    assert s1["u_top_mm"] == 0.0100
    assert s2["u_top_mm"] == 0.0200

def test_passive_modulus_scaling_and_physical_stress():
    """Verify passive layer compliance scaling and physical stress recovery."""
    summary_path = os.path.join(MODE2_PRE_DIR, "mode2_miseseri_deep_audit_summary.json")
    with open(summary_path, 'r') as f:
        summary = json.load(f)

    s1 = summary["Step-1"]
    
    # E_phys = 210 GPa, E_UMAT = 10^-8 MPa -> scale factor = 2.10e13
    assert s1["miseseri_max"] < 1.0e-12, "Raw Layer 3 MISESERI should be ~10^-14 kN/mm^2 due to E_UMAT"
    assert s1["s_phys_MPa_max"] > 4000.0, "Reconstructed physical Mises stress at notch tip should exceed 4000 MPa"
    assert s1["dynamic_range_miseseri"] > 2500.0, "MISESERI dynamic range should be >2500x across domain"
    assert s1["dynamic_range_s_phys"] > 900.0, "Physical stress dynamic range should be >900x"

def test_relative_error_indicator_scale_invariance():
    """Verify mathematical scale-invariance of eta_e = MISESERI / MISESAVG between Step 1 and Step 2."""
    summary_path = os.path.join(MODE2_PRE_DIR, "mode2_miseseri_deep_audit_summary.json")
    with open(summary_path, 'r') as f:
        summary = json.load(f)

    ratios = summary["ratios_step2_to_step1"]
    assert pytest.approx(ratios["ratio_miseseri_max"], rel=1e-5) == 2.0
    assert pytest.approx(ratios["ratio_misesavg_mean"], rel=1e-5) == 2.0
    assert pytest.approx(ratios["ratio_eta_max"], rel=1e-5) == 1.0
    assert ratios["mathematical_scale_invariance_verified"] is True

def test_csv_audit_records_integrity():
    """Verify elementwise CSV audit data files exist and have 2,960 elements."""
    for step_name in ["step1", "step2"]:
        csv_path = os.path.join(MODE2_PRE_DIR, f"mode2_miseseri_deep_audit_{step_name}.csv")
        assert os.path.exists(csv_path), f"CSV audit file missing: {csv_path}"
        with open(csv_path, 'r') as f:
            lines = f.readlines()
        assert len(lines) == 2961, f"Expected 2960 data rows + 1 header, found {len(lines)}"

def test_publication_figures_exist():
    """Verify publication figures exist and have valid file sizes."""
    png_path = os.path.join(FIGURES_DIR, "fig_mode2_miseseri_field_validity.png")
    pdf_path = os.path.join(FIGURES_DIR, "fig_mode2_miseseri_field_validity.pdf")

    assert os.path.exists(png_path), f"PNG figure missing: {png_path}"
    assert os.path.exists(pdf_path), f"PDF figure missing: {pdf_path}"

    assert os.path.getsize(png_path) > 100_000, "PNG file too small"
    assert os.path.getsize(pdf_path) > 50_000, "PDF file too small"

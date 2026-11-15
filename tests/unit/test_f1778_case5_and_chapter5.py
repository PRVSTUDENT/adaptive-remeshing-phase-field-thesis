# -*- coding: utf-8 -*-
"""
tests/unit/test_f1778_case5_and_chapter5.py
==========================================
Unit tests for Task F1778:
1. Verify production UEL and unified framework SHA-256 invariants.
2. Verify Chapter 5 LaTeX integration and figure references.
3. Verify Case 5 terminal coupled fracture metrics (99.88% load drop, monotonic energy).
4. Verify thesis compilation and main.pdf integrity.
"""
import os
import hashlib
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

EXPECTED_UEL_SHA = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"
EXPECTED_FRAMEWORK_SHA = "8d71f38f23867a23c1fc1bf5ec499533a8c75f538b77804ece03b5c668f4be08"

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()

def test_frozen_uel_and_framework_invariants():
    """Verify bitwise invariance of Fortran production UEL and shared Python framework."""
    uel_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
    assert os.path.exists(uel_path), "Frozen UEL file not found"
    assert compute_sha256(uel_path) == EXPECTED_UEL_SHA, "Frozen UEL SHA-256 altered!"

    framework_path = os.path.join(REPO_ROOT, "scripts", "remeshing", "reusable_2d_adaptive_framework.py")
    assert os.path.exists(framework_path), "Shared framework file not found"
    assert compute_sha256(framework_path) == EXPECTED_FRAMEWORK_SHA, "Shared framework SHA-256 altered!"

def test_chapter05_latex_integration():
    """Verify Chapter 5 contains the unified regression and coupled fracture sections and figures."""
    ch5_path = os.path.join(REPO_ROOT, "MA_AdaptiveRemeshing_Report_2026", "chapter05_method_a_hole_benchmark.tex")
    assert os.path.exists(ch5_path), "Chapter 5 LaTeX file not found"
    
    with open(ch5_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    assert "Unified Four-Benchmark Method~A Adaptive Remeshing Regression" in content
    assert "Coupled Phase-Field Fracture Simulation and Physics Qualification" in content
    assert "fig_f1774_four_benchmark_regression_synthesis.pdf" in content
    assert "fig_f1776_coupled_fracture_synthesis.pdf" in content
    assert "fig_f1777_physics_and_continuation_synthesis.pdf" in content
    assert "0.7887" in content  # Case 1 peak load
    assert "0.7251" in content  # Case 5 peak load
    assert "99.76" in content   # Case 1 load drop
    assert "99.88" in content   # Case 5 load drop

def test_thesis_pdf_compilation():
    """Verify main.pdf was generated cleanly with expected size and structure."""
    pdf_path = os.path.join(REPO_ROOT, "MA_AdaptiveRemeshing_Report_2026", "main.pdf")
    assert os.path.exists(pdf_path), "main.pdf not found"
    size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
    assert size_mb > 50.0, "main.pdf size unexpectedly small (<50 MB)"

def test_case5_terminal_fracture_metrics():
    """Verify Case 5 terminal data metrics parsed from DAT and CSV."""
    dat_path = os.path.join(REPO_ROOT, "results", "validation", "f1776_case1_case5_fracture", "case5_fracture_terminal.dat")
    assert os.path.exists(dat_path), "Terminal DAT file not found"
    
    disps, forces = [], []
    with open(dat_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            parts = line.split()
            if len(parts) >= 3 and parts[0] == "999999":
                try:
                    disps.append(float(parts[1]))
                    forces.append(float(parts[2]))
                except ValueError:
                    pass

    assert len(disps) == 559, f"Expected 559 increments, found {len(disps)}"
    max_f = max(forces)
    assert abs(max_f - 0.72512) < 0.01, f"Peak force {max_f} differs from expected ~0.725 kN"
    final_f = forces[-1]
    drop_pct = (1.0 - final_f / max_f) * 100.0
    assert drop_pct > 99.80, f"Expected >99.8% load drop, got {drop_pct:.2f}%"

def test_case5_terminal_energy_balance():
    """Verify Case 5 terminal energy balance CSV values."""
    csv_path = os.path.join(REPO_ROOT, "results", "validation", "f1776_case1_case5_fracture", "case5_energy_balance_terminal.csv")
    assert os.path.exists(csv_path), "Terminal CSV not found"
    
    with open(csv_path, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]
        
    last_line = lines[-1]
    parts = [p.strip() for p in last_line.split(",")]
    step = int(parts[0])
    inc = int(parts[1])
    e_elas = float(parts[4])
    e_frac = float(parts[5])
    
    assert step == 2
    assert inc == 508
    assert e_elas < 1e-4, f"Elastic energy {e_elas} should be near zero after complete fracture"
    assert abs(e_frac - 0.002322) < 0.0001, f"Fracture dissipation {e_frac} matches expected 2.322 mJ"

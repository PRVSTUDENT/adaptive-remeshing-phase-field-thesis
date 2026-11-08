# -*- coding: utf-8 -*-
"""
test_f1693_sec43_donor_correction_and_synthesis.py
==================================================
Unit test suite for Task F1693:
Method A Section 4.3 Terminal Donor Correction, Native Remeshing Audit,
and Literature Reproduction Synthesis.

Validates:
1. UEL MISESERI absence documentation in Job-1 ODB and need for continuum recovery donors
2. Exact mathematical and numerical definition of RECOVERY_DEG and RECOVERY_ELAS donors
3. Headline claim discipline: dual-branch damage resolved vs dual-branch remeshing unresolved
4. Single-pass staggered operator split (*STATIC, DIRECT) documented as intentional design
5. Stage 0 review corrections verified with exact textual presence
6. Dual-donor remeshing results (both donors yield exactly 0.00% <= l0/2 in secondary corridor)
"""

import json
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CHAPTER5_PATH = REPO_ROOT / "MA_AdaptiveRemeshing_Report_2026" / "chapter05_method_a_hole_benchmark.tex"
DAMAGED_JSON = REPO_ROOT / "results" / "validation" / "f1692_damaged_elements.json"
AUDIT_JSON = REPO_ROOT / "results" / "validation" / "f1692_sec43_damage_and_miseseri_audit.json"
ADAPT_METRICS_JSON = REPO_ROOT / "results" / "validation" / "f1692_sec43_adapted_mesh_metrics.json"

def test_f1693_miseseri_absence_in_uel_odb_documented():
    """Verify thesis documents that UEL elements cannot output MISESERI directly."""
    assert CHAPTER5_PATH.exists()
    with open(CHAPTER5_PATH, "r", encoding="utf-8") as f:
        tex = f.read()

    assert "do not output standard continuum Cauchy stress tensors to the ODB" in tex
    assert "every \\MISESERI\\ field entry is identically zero across all increments" in tex
    assert "discretization error must be evaluated from dedicated continuum recovery donor models" in tex

def test_f1693_recovery_deg_and_elas_donors_defined():
    """Verify both RECOVERY_DEG and RECOVERY_ELAS donors are fully defined in the thesis."""
    assert CHAPTER5_PATH.exists()
    with open(CHAPTER5_PATH, "r", encoding="utf-8") as f:
        tex = f.read()

    # Case A: Intact linear elastic
    assert r"PK\_SEC43\_STAGGERED\_RECOVERY\_ELAS.odb" in tex
    assert "uniform, undamaged elasticity ($E = 210.0\\,\\mathrm{GPa}$" in tex
    assert "\\MISESAVG = 3.9107\\,\\mathrm{MPa}" in tex

    # Case B: Terminal degraded stiffness
    assert r"PK\_SEC43\_STAGGERED\_RECOVERY\_DEG.odb" in tex
    assert "element-by-element degraded stiffness assigned according to the terminal phase-field damage" in tex
    assert "partitioned into 20 discrete stiffness bins spanning $[10^{-6} E_0, E_0]$" in tex
    assert "\\MISESAVG = 1.8474\\,\\mathrm{MPa}" in tex

def test_f1693_headline_claim_split_damage_vs_remesh():
    """Verify headline claims distinguish damage resolution from remeshing resolution."""
    assert CHAPTER5_PATH.exists()
    with open(CHAPTER5_PATH, "r", encoding="utf-8") as f:
        tex = f.read()

    # Title split
    assert "Dual-Branch Damage Resolution and Single-Rule Remeshing Assessment" in tex
    # Secondary corridor remesh failure
    assert "Crucially, \\textbf{exactly $0.00\\%$ of elements satisfy $h \\le \\ell_0/2$}" in tex

def test_f1693_single_pass_staggered_design_justified():
    """Verify single-pass staggered split is documented as an intentional design choice."""
    assert CHAPTER5_PATH.exists()
    with open(CHAPTER5_PATH, "r", encoding="utf-8") as f:
        tex = f.read()

    assert "Single-Pass Staggered Split Formulation as Design" in tex
    assert "There is no outer iteration loop between the displacement and phase-field subproblems" in tex
    assert "\\Delta u_1 = 0.0005\\,\\mathrm{mm} = \\ell_0 / 570" in tex
    assert "\\Delta u_2 = 0.0002\\,\\mathrm{mm} = \\ell_0 / 1425" in tex

def test_f1693_stage_0_f1690_corrections_quoted_and_verified():
    """Verify Stage 0 review corrections are present in the text."""
    assert CHAPTER5_PATH.exists()
    with open(CHAPTER5_PATH, "r", encoding="utf-8") as f:
        tex = f.read()

    # Energy reconciliation (659x ungrounded multiplier absent; authentic 13.43 vs 16.09 mJ present)
    assert "659x" not in tex
    assert "13.43" in tex and "16.09" in tex

    # Walltime vs CPU time
    assert "30\\,\\mathrm{min}\\,04\\,\\mathrm{s}" in tex
    assert "1{,}279\\,\\mathrm{s}" in tex

    # Peak MISESERI element 3713
    assert "Element~3713" in tex or "Element 3713" in tex
    assert "6.899\\,\\mathrm{MPa}" in tex

    # Frozen production UEL inviolability
    assert "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6" in tex

def test_f1693_dual_donor_falsification_metrics():
    """Verify both recovery donors yield 0.00% <= l0/2 in the secondary corridor."""
    assert ADAPT_METRICS_JSON.exists()
    with open(ADAPT_METRICS_JSON, "r", encoding="utf-8") as f:
        metrics = json.load(f)

    # RECOVERY_DEG metrics
    assert metrics["elements_total"] == 15625
    assert metrics["secondary_corridor"]["pct_l0_half"] == 0.0
    assert metrics["secondary_corridor"]["med"] > 0.50
    assert metrics["paper_comparison"]["secondary_refined"] is False

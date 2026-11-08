# -*- coding: utf-8 -*-
"""
test_f1689_method_a_synthesis.py

Unit test suite for Task F1689: Method A Thesis Synthesis and Cost-Accuracy Comparison.
Validates:
1. Tripartite scientific classification: validated, falsified, and unproven claims.
2. Comprehensive cost-accuracy comparison metrics across coarse, uniform, and adapted discretizations.
3. Candidate E10 and E12 performance and DOF reduction parity (-57.13% and -62.29%).
4. Characterized F1685 solver limitations (pointwise healing and quasi-static energy residual).
5. Strict scientific governance: zero new PBS submissions, frozen UEL unchanged.
"""

import os
import json
import hashlib
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATION_DIR = REPO_ROOT / "results" / "validation"
REPORT_DIR = REPO_ROOT / "MA_AdaptiveRemeshing_Report_2026"
CHAPTER5_PATH = REPORT_DIR / "chapter05_method_a_hole_benchmark.tex"
UEL_PATH = REPO_ROOT / "models" / "pandey_kumar_mode1" / "f42_mixed_uel.for"
FROZEN_UEL_SHA256 = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"


def compute_sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            digest.update(chunk)
    return digest.hexdigest().lower()


def test_f1689_tripartite_classification_in_thesis():
    """Verify Chapter 5 contains the tripartite classification with all validated, falsified, and unproven claims."""
    assert CHAPTER5_PATH.exists(), f"Chapter 5 missing: {CHAPTER5_PATH}"
    with open(CHAPTER5_PATH, "r", encoding="utf-8") as f:
        tex = f.read()

    # Section exists
    assert "Comprehensive Method~A Synthesis and Cost--Accuracy Assessment" in tex
    assert "tab:method_a_tripartite_classification" in tex

    # Validated claims
    assert "Primary candidate E10 achieves $9{,}164$ elements ($27{,}753$ DOFs, $-57.13\\%$" in tex
    assert "Completed 506 increments to $u_y = 0.01329\\,\\mathrm{mm}$ with zero divergence" in tex
    assert "Monolithic UEL diverges at Inc 64 ($u_y = 0.081\\,\\mathrm{mm}$" in tex

    # Falsified claims
    assert "Single-Rule Dual-Branch on Literature Geometry" in tex
    assert "Terminal ENDENERI Control: Hypothesis H1" in tex
    assert "$51{,}712$ elements ($154{,}953$ DOFs, $2.4\\times$ inflation)" in tex
    assert "Blind Generalization of 5\\%/10\\% Rule: Hypothesis H2" in tex
    assert "open-boundary flaring expands $W_{90\\%} = 229.56" in tex

    # Unproven claims
    assert "E10 / E12 Fracture Response" in tex
    assert "Section 4.3 Terminal Single-Rule Test" in tex


def test_f1689_cost_accuracy_comparison_table_metrics():
    """Verify Master Table 5.14 cost-accuracy comparison metrics against underlying data."""
    with open(CHAPTER5_PATH, "r", encoding="utf-8") as f:
        tex = f.read()

    assert "tab:method_a_cost_accuracy_comparison" in tex
    # Coarse reference
    assert "Coarse Reference (F1642) & $2{,}906$ & $8{,}724$" in tex
    # Baseline adapted models
    assert "Method~A Baseline (F1678) & $20{,}213$ & $60{,}645$ & $197.10$ & $86.52$" in tex
    assert "Method~A Combined (F1685) & $21{,}569$ & $64{,}746$ & $197.10$ & $86.52$" in tex
    # Optimized selective models
    assert "Method~A E10 (F1686)" in tex
    assert "$\\mathbf{9{,}164}$ & $\\mathbf{27{,}753}$ & $\\mathbf{36.81}$ & $\\mathbf{65.35}$" in tex
    assert "Method~A E12 (F1686)" in tex
    assert "$\\mathbf{8{,}046}$ & $\\mathbf{24{,}414}$ & $\\mathbf{33.69}$ & $\\mathbf{59.29}$" in tex


def test_f1689_e10_e12_reconciliation_audit():
    """Verify candidate E10 and E12 numerical properties from f1686_reconciliation_summary.csv."""
    csv_path = VALIDATION_DIR / "f1686_reconciliation_summary.csv"
    assert csv_path.exists(), f"Missing reconciliation summary: {csv_path}"
    with open(csv_path, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]

    header = lines[0].split(",")
    e10_row = None
    e12_row = None
    e05_row = None

    for line in lines[1:]:
        parts = line.split(",")
        if parts[0] == "PK_HOLE_SEL_E10_PHYS":
            e10_row = dict(zip(header, parts))
        elif parts[0] == "PK_HOLE_SEL_E12_PHYS":
            e12_row = dict(zip(header, parts))
        elif parts[0] == "PK_HOLE_SEL_E05_PHYS":
            e05_row = dict(zip(header, parts))

    assert e10_row is not None
    assert int(e10_row["n_elements"]) == 9164
    assert int(e10_row["n_dofs"]) == 27753
    assert float(e10_row["w90_um"]) == pytest.approx(36.81, rel=1e-2)
    assert float(e10_row["waste_pct_rel"]) == pytest.approx(65.35, rel=1e-2)
    assert float(e10_row["prim_h_med_equiv"]) <= 2.50
    assert float(e10_row["sec_h_med_equiv"]) <= 2.50
    assert e10_row["overall_pass"] == "True"

    assert e12_row is not None
    assert int(e12_row["n_elements"]) == 8046
    assert int(e12_row["n_dofs"]) == 24414
    assert float(e12_row["w90_um"]) == pytest.approx(33.69, rel=1e-2)
    assert float(e12_row["waste_pct_rel"]) == pytest.approx(59.29, rel=1e-2)
    assert e12_row["overall_pass"] == "True"

    # DOF reductions
    base_dofs = int(e05_row["n_dofs"])
    e10_reduction = (base_dofs - int(e10_row["n_dofs"])) / base_dofs * 100.0
    e12_reduction = (base_dofs - int(e12_row["n_dofs"])) / base_dofs * 100.0
    assert e10_reduction == pytest.approx(57.13, abs=0.05)
    assert e12_reduction == pytest.approx(62.29, abs=0.05)


def test_f1689_characterized_limitations_stated():
    """Verify that F1685 healing and quasi-static energy residual are explicitly stated in thesis text."""
    with open(CHAPTER5_PATH, "r", encoding="utf-8") as f:
        tex = f.read()

    assert "Characterized Limitations of the Production Fracture Simulation (F1685)" in tex
    assert "Pointwise Damage Irreversibility and Healing Audit" in tex
    assert "-0.001375" in tex
    assert "Quasi-Static Thermodynamic Residual Accumulation" in tex
    assert "0.3686" in tex
    assert "12.30\\%" in tex


def test_f1689_scientific_governance_and_resource_limits():
    """Verify Task F1689 registration, zero PBS authorization, and frozen UEL hash."""
    assert UEL_PATH.exists(), f"UEL source missing: {UEL_PATH}"
    actual_sha = compute_sha256(UEL_PATH)
    assert actual_sha == FROZEN_UEL_SHA256, f"Frozen UEL corrupted! Got {actual_sha}"

    # Verify task definition and active task have max_new_pbs_submissions == 0
    task_def_path = REPO_ROOT / "project_coordination" / "task_definitions" / "F1689-METHOD-A-THESIS-SYNTHESIS-AND-COST-ACCURACY-COMPARISON.json"
    assert task_def_path.exists(), f"Task definition missing: {task_def_path}"
    with open(task_def_path, "r", encoding="utf-8") as f:
        d = json.load(f)
    assert d["max_new_pbs_submissions"] == 0
    assert d["predecessor"] == "F1688-PANDEY-KUMAR-SEC43-REPRODUCTION-CONTROL"

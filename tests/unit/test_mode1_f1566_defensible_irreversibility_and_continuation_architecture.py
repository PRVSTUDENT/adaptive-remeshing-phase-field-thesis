#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for Task F1566:
- Mathematical incompatibility claim retraction (convexity/secant error).
- Candidate 2 independent revalidation (exact unclipped d > 1.0, 4/4 conservation pass, 0 nodal violations, retained interior deficits).
- Native crack-front spatial band orientation (Band 4 behind front, Band 5 straddling front and virgin ligament).
- Comprehensive commercial Abaqus continuation architecture audit.
- Binding governance invariants.
"""

import json
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

F1565_CERT_PATH = (
    REPO_ROOT
    / "runs"
    / "hpc"
    / "mode1_stage_c1_2_cycle5_continuation"
    / "F1565_FEASIBILITY_CERTIFICATE_AND_INITIALIZATION_PROOF.json"
)

F1566_REVAL_PATH = (
    REPO_ROOT
    / "runs"
    / "hpc"
    / "mode1_stage_c1_2_cycle5_continuation"
    / "F1566_CANDIDATE2_INDEPENDENT_REVALIDATION.json"
)

FIGURE_PNG_PATH = (
    REPO_ROOT
    / "results"
    / "figures"
    / "mode1_method_c_forward_refinement"
    / "fig_mode1_cycle5_crack_front_refinement_and_miseseri.png"
)

DOC_PATH = (
    REPO_ROOT
    / "docs"
    / "reports"
    / "MODE1_METHOD_C1_STATE_INITIALIZATION_AND_CONTINUATION_ARCHITECTURE.md"
)


def test_f1566_mathematical_incompatibility_retraction():
    """Verify formal retraction of convexity-based mathematical incompatibility theorem."""
    assert F1565_CERT_PATH.exists(), f"Missing certificate at {F1565_CERT_PATH}"
    with open(F1565_CERT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Executive verdict records retraction
    assert data["executive_verdict"]["false_incompatibility_retraction"].startswith("FORMALLY_RETRACTED")

    # Certificate contains retraction statement and 4 true mechanisms
    cert = data["mathematical_analysis_and_retraction_certificate"]
    assert "FORMALLY RETRACTED" in cert["retraction_statement"]
    assert "ABOVE the graph" in cert["retraction_statement"]

    mechanisms = cert["true_mathematical_mechanisms"]
    assert len(mechanisms) == 4
    # Mechanism 1: Mesh non-alignment
    assert any("Piecewise-linear" in m for m in mechanisms)
    # Mechanism 2: Transverse cusp concavity
    assert any("Transverse cusp" in m or "peak" in m for m in mechanisms)
    # Mechanism 3: Gradient non-monotonicity
    assert any("Gradient energy" in m or "spatial gradients" in m for m in mechanisms)
    # Mechanism 4: Candidate 3 heuristic failure
    assert any("Candidate 3 heuristic failure" in m for m in mechanisms)

    # Document contains warning alert
    assert DOC_PATH.exists(), f"Missing doc at {DOC_PATH}"
    with open(DOC_PATH, "r", encoding="utf-8") as f:
        doc_text = f.read()

    assert "Retraction of False Convexity/Secant Mathematical Incompatibility Claim" in doc_text
    assert "formally retracted as mathematically erroneous" in doc_text


def test_f1566_candidate2_independent_revalidation():
    """Verify Candidate 2 independent revalidation with unclipped d > 1.0 handling."""
    assert F1566_REVAL_PATH.exists(), f"Missing revalidation at {F1566_REVAL_PATH}"
    with open(F1566_REVAL_PATH, "r", encoding="utf-8") as f:
        rev = json.load(f)

    # Explicit handling of d > 1.0
    assert rev["d_max_donor"] > 1.0008
    assert rev["d_max_recip"] > 1.0008

    # All 4 scalar conservation criteria PASS
    assert abs(rev["delta_RF2_N"]) <= 5.0
    assert abs(rev["delta_elas_pct"]) <= 0.50
    assert abs(rev["delta_frac_pct"]) <= 0.50
    assert abs(rev["delta_tot_pct"]) <= 0.10

    # Specifically:
    assert abs(rev["delta_RF2_N"] - 0.1902) < 0.05
    assert abs(rev["delta_elas_pct"] - 0.0336) < 0.02
    assert abs(rev["delta_frac_pct"] - 0.1290) < 0.02
    assert abs(rev["delta_tot_pct"] - 0.0616) < 0.02

    # Nodal irreversibility is strictly 0 violations across 33,975 nodes
    assert rev["nodal_violations_count"] == 0
    assert rev["nodal_violations_pct"] == 0.0
    assert rev["max_nodal_deficit"] == 0.0

    # Interior sub-element deficits on Dataset D are explicitly retained (not swept under rug)
    assert rev["dataset_D_violations_count"] > 200
    assert rev["dataset_D_violations_count"] < 300
    assert abs(rev["max_dataset_D_deficit"] - 0.055) < 0.01


def test_f1566_crack_front_spatial_band_orientation():
    """Verify spatial band orientation: Band 4 is behind front, Band 5 straddles front and ligament."""
    assert FIGURE_PNG_PATH.exists(), f"Missing figure at {FIGURE_PNG_PATH}"
    pdf_path = FIGURE_PNG_PATH.with_suffix(".pdf")
    assert pdf_path.exists(), f"Missing PDF at {pdf_path}"

    with open(DOC_PATH, "r", encoding="utf-8") as f:
        doc_text = f.read()

    # Section 9.3 explicitly marks Band 4 as behind front and Band 5 as front & ligament
    assert "Band 4 (Process Zone Behind Front, $x \\in [0.60, 0.65]$)" in doc_text
    assert "Band 5 (Crack Front & Virgin Ligament, $x \\in [0.65, 0.70]$)" in doc_text
    assert "Crack-Front Spatial Band Correction" in doc_text
    assert "strictly behind the crack front" in doc_text


def test_f1566_abaqus_continuation_architectures():
    """Verify Section 9.4 assessment of commercial Abaqus continuation architectures."""
    with open(DOC_PATH, "r", encoding="utf-8") as f:
        doc_text = f.read()

    assert "9.4 Comprehensive Audit of Commercial Abaqus Continuation Architectures" in doc_text
    assert "*INITIAL CONDITIONS, TYPE=DISPLACEMENT" in doc_text
    assert "*MAP SOLUTION" in doc_text
    assert "*RESTART, READ" in doc_text
    assert "*INITIAL CONDITIONS, TYPE=SOLUTION" in doc_text
    assert "f42_experimental_offset_uel.for" in doc_text


def test_f1566_governing_invariants():
    """Verify mandatory zero self-grading and execution governance invariants."""
    with open(F1565_CERT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    gov = data["governing_execution_action"]
    assert gov["package71_receiver_submission"] == "WITHHELD_BY_POLICY"
    assert gov["cycle5_loaded_propagation"] == "ON_HOLD"
    assert gov["method_c_overall"] == "NOT_YET_QUALIFIED"
    assert gov["active_cluster_jobs"] == 0

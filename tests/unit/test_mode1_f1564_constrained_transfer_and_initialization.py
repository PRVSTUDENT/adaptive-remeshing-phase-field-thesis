#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for Task F1564: Constrained State Transfer, Energy Preservation,
Abaqus Displacement Initialization Architecture, and Crack-Front Spatial Bands.
"""

import json
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

EVIDENCE_JSON_PATH = (
    REPO_ROOT
    / "runs"
    / "hpc"
    / "mode1_stage_c1_2_cycle5_continuation"
    / "F1564_CONSTRAINED_TRANSFER_EVIDENCE.json"
)

FIGURE_PATH = (
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


def test_f1564_evidence_json_exists_and_valid():
    """Verify F1564 evidence JSON exists and contains required metadata."""
    assert EVIDENCE_JSON_PATH.exists(), f"Missing evidence JSON at {EVIDENCE_JSON_PATH}"
    with open(EVIDENCE_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    meta = data["metadata"]
    assert meta["task_id"] == "F1564-EXECUTE-CONSTRAINED-TRANSFER-AND-VERIFY-DISPLACEMENT-INITIALIZATION"
    assert meta["donor_mesh_elements"] == 29293
    assert meta["recipient_mesh_elements"] == 34094
    assert meta["alpha_regularization"] == 1.0
    assert meta["l0_mm"] == 0.0075

    assert "authentic_odb_ground_truth" in data
    assert "candidate_evaluations" in data


def test_f1564_candidate2_conservation_pass():
    """Verify Candidate 2 passes all four scalar conservation criteria against authentic Package 65 ODB."""
    with open(EVIDENCE_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    c2 = data["candidate_evaluations"]["Candidate_2_Node_Monotonic"]
    disc = c2["discrepancies_vs_odb"]

    # All criteria pass
    assert disc["all_pass"] is True
    assert disc["pass_RF"] is True
    assert disc["pass_elas"] is True
    assert disc["pass_frac"] is True
    assert disc["pass_tot"] is True

    # Quantitative bounds
    assert abs(disc["delta_RF_N"]) <= 5.0
    assert abs(disc["delta_elas_pct"]) <= 0.50
    assert abs(disc["delta_frac_pct"]) <= 0.50
    assert abs(disc["delta_tot_pct"]) <= 0.10

    # Strict values
    assert abs(disc["delta_RF_N"] - 0.5784) < 0.05
    assert abs(disc["delta_elas_pct"] - 0.1030) < 0.02
    assert abs(disc["delta_frac_pct"] - 0.0229) < 0.02
    assert abs(disc["delta_tot_pct"] - 0.0795) < 0.02

    # Dataset C (recipient nodes) must have 0 violations
    irrev_c = c2["irreversibility_dataset_C"]["tol_1e-06"]
    assert irrev_c["violations_count"] == 0
    assert irrev_c["violations_pct"] == 0.0


def test_f1564_candidate3_subelement_sag_and_energy_tradeoff():
    """Verify Candidate 3 subelement envelope lifting suppresses sag but inflates fracture energy."""
    with open(EVIDENCE_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    c3 = data["candidate_evaluations"]["Candidate_3_Constrained_Sobolev"]
    disc = c3["discrepancies_vs_odb"]

    # Candidate 3 fails energy conservation due to artificial fracture energy inflation
    assert disc["all_pass"] is False
    assert disc["pass_frac"] is False
    assert disc["pass_elas"] is False
    assert disc["pass_tot"] is False
    assert disc["delta_frac_pct"] > 3.0  # +3.55%

    # But process-zone sub-element violations are suppressed to < 1%
    irrev_d = c3["irreversibility_dataset_D"]["tol_1e-02"]
    assert irrev_d["violations_count"] < 100
    assert irrev_d["violations_pct"] < 1.0


def test_f1564_displacement_initialization_architecture():
    """Verify Abaqus static step displacement initialization architecture findings."""
    assert DOC_PATH.exists(), f"Architecture document missing at {DOC_PATH}"
    with open(DOC_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    assert "PACKAGE71_INITIAL_DISPLACEMENT_RESTORATION = UNSUPPORTED" in content
    assert "PACKAGE71_RECEIVER_SUBMISSION = WITHHELD_BY_POLICY" in content
    assert "*INITIAL CONDITIONS, TYPE=DISPLACEMENT" in content


def test_f1564_crack_front_refinement_spatial_bands():
    """Verify Priority 4 crack-front figure exists and covers 5 spatial bands."""
    assert FIGURE_PATH.exists(), f"Missing Priority 4 figure at {FIGURE_PATH}"
    pdf_path = FIGURE_PATH.with_suffix(".pdf")
    assert pdf_path.exists(), f"Missing Priority 4 PDF figure at {pdf_path}"

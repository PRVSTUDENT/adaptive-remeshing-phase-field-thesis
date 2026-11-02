#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_r8_energy_root_cause.py
============================
Unit test suite verifying the quantitative root-cause investigation for Package 157-R8
energy discrepancy.
Task: F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE
Protocol Version: 2
"""

import json
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT = REPO_ROOT / "results" / "validation" / "r8_energy_failure_root_cause.json"


def test_r8_energy_root_cause_artifact_structure():
    assert ARTIFACT.is_file(), f"Missing artifact {ARTIFACT}"
    data = json.loads(ARTIFACT.read_text(encoding="utf-8"))

    assert data["schema"] == 1
    assert data["job_id"] == "1419490.mmaster02"
    assert data["investigation"] == "R8_ENERGY_FAILURE_ROOT_CAUSE"
    assert "component_wise_comparison_vs_c3_donor" in data
    assert "discretization_comparability_evidence" in data
    assert "root_cause_analysis" in data
    assert "authoritative_gate_decision" in data


def test_strict_unrelaxed_criteria_enforced():
    data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    gate = data["authoritative_gate_decision"]

    # Threshold must NOT be relaxed
    assert gate["threshold_relaxed"] is False
    assert gate["gate_energy_tol_pct"] == 2.0

    # Decision must be FAIL
    assert gate["decision"] == "FAIL"
    assert gate["predecessor_status"] == "PHYSICALLY_REJECTED"
    assert gate["package167_gate_status"] == "BLOCKED_PENDING_VALID_C4_REFERENCE"
    assert gate["observed_discrepancy_pct"] > 2.0


def test_component_wise_accounting_consistency():
    data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    comp = data["component_wise_comparison_vs_c3_donor"]

    # Total energy must equal elastic + fracture for R8
    e_el = comp["elastic_energy"]["r8_observed_kNmm"]
    e_fr = comp["fracture_energy"]["r8_observed_kNmm"]
    e_tot = comp["total_energy"]["r8_observed_kNmm"]
    assert pytest.approx(e_el + e_fr, rel=1e-12) == e_tot

    # RF2 passes under 5% gate
    assert comp["reaction_force"]["pass"] is True
    assert comp["reaction_force"]["discrepancy_pct"] < 5.0

    # Total energy fails 2% gate
    assert comp["total_energy"]["pass"] is False
    assert comp["total_energy"]["discrepancy_pct"] > 2.0


def test_c4_continuous_evidence_consistency():
    data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    evidence = data["discretization_comparability_evidence"]

    # C4 continuous solve vs C3 donor has elevated fracture energy
    c4_vs_donor = evidence["c4_continuous_solve_vs_c3_donor_at_1860nm"]
    assert c4_vs_donor["fracture_energy_discrepancy_pct"] > 20.0

    # R5 continuation on C4 matches C4 continuous solve with < 0.01% total energy discrepancy
    r5_vs_c4 = evidence["r5_continuation_solve_vs_c4_continuous_at_1860nm"]
    assert r5_vs_c4["total_energy_discrepancy_pct"] < 0.01
    assert r5_vs_c4["rf2_discrepancy_pct"] < 0.5

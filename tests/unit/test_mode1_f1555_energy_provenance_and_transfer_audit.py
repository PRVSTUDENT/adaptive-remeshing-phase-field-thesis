#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit test suite for Task F1555:
Audit and reconciliation of Cycle 5 donor energy provenance,
isolation of offline quadrature coding defects vs authentic Abaqus solver,
and verification of strict transfer conservation evaluation.
"""

import sys
import os
import json
import hashlib
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

def test_01_donor_energy_provenance_reconciliation():
    c5_dir = REPO_ROOT / "runs" / "hpc" / "mode1_stage_c1_2_cycle5_continuation"
    metrics_file = c5_dir / "STAGE_C1_2_CYCLE5_TRANSFER_METRICS.json"
    assert metrics_file.exists(), f"Metrics file missing: {metrics_file}"

    with open(metrics_file, "r", encoding="utf-8") as f:
        m = json.load(f)

    prov = m.get("donor_energy_provenance_reconciliation", {})
    solver = prov.get("authentic_abaqus_solver_uel_energy_balance", {})

    # Authentic Abaqus solver ground truth
    assert abs(solver["E_elas_mJ"] - 1.678941) < 1e-4
    assert abs(solver["E_frac_uJ"] - 697.1766) < 1e-2
    assert abs(solver["E_total_mJ"] - 2.376118) < 1e-4

    # Corrected quadrature comparison
    calc = prov.get("corrected_fortran_identical_donor_quadrature", {})
    assert abs(calc["E_elas_mJ"] - 1.720474) < 1e-3
    assert abs(calc["E_frac_uJ"] - 683.0884) < 1e-1
    assert abs(calc["E_total_mJ"] - 2.403562) < 1e-3

    # Discrepancy vs solver is <= 2.5% across all components
    disc = calc.get("discrepancy_vs_solver_pct", {})
    assert abs(disc["E_elas"]) < 2.5
    assert abs(disc["E_frac"]) < 2.5
    assert abs(disc["E_total"]) < 1.5

def test_02_corrected_transfer_conservation_metrics():
    c5_dir = REPO_ROOT / "runs" / "hpc" / "mode1_stage_c1_2_cycle5_continuation"
    metrics_file = c5_dir / "STAGE_C1_2_CYCLE5_TRANSFER_METRICS.json"
    with open(metrics_file, "r", encoding="utf-8") as f:
        m = json.load(f)

    # Criterion 1: Displacement L2
    assert m["criterion_1_displacement_l2"]["verdict"] == "PASS"
    assert m["criterion_1_displacement_l2"]["value"] <= 1.0

    # Criterion 2: Peak damage
    assert m["criterion_2_peak_damage"]["verdict"] == "PASS"
    assert m["criterion_2_peak_damage"]["delta"] <= 1e-5

    # Criterion 3: Integrated damage
    assert m["criterion_3_integrated_damage"]["verdict"] == "PASS"
    assert m["criterion_3_integrated_damage"]["relative_error_pct"] <= 5.0

    # Criterion 4: History non-negativity
    assert m["criterion_4_history_non_negativity"]["verdict"] == "PASS"
    assert m["criterion_4_history_non_negativity"]["min_H"] >= 0.0

    # Criterion 5: Force continuity
    assert m["criterion_5_boundary_force_continuity"]["verdict"] == "PASS"
    assert m["criterion_5_boundary_force_continuity"]["value"] <= 5.0

    # Criterion 6: Fracture energy preservation (<= 0.50%)
    c6 = m["criterion_6_fracture_energy_preservation"]
    assert c6["delta_E_frac_pct"] <= 0.50
    assert c6["verdict"] == "PASS"

    # Criterion 7: Elastic energy preservation (<= 0.50%)
    c7 = m["criterion_7_elastic_energy_preservation"]
    assert c7["delta_E_elas_pct"] <= 0.50
    assert c7["verdict"] == "PASS"

    # Criterion 8: Total energy preservation (<= 0.10%)
    # Delta E_total is +0.2189%, which exceeds 0.10%, so it is strictly FAIL
    c8 = m["criterion_8_total_energy_preservation"]
    assert c8["delta_E_total_pct"] > 0.10
    assert c8["verdict"] == "FAIL"

def test_03_strict_governance_and_zero_self_grading():
    c5_dir = REPO_ROOT / "runs" / "hpc" / "mode1_stage_c1_2_cycle5_continuation"
    metrics_file = c5_dir / "STAGE_C1_2_CYCLE5_TRANSFER_METRICS.json"
    with open(metrics_file, "r", encoding="utf-8") as f:
        m = json.load(f)

    verdict = m.get("verdict", {})
    assert verdict.get("cycle5_nonmatching_transfer_conservation") == "FAIL"
    assert verdict.get("method_c_overall") == "NOT_YET_QUALIFIED"
    assert verdict.get("package_70_solver_continuation") == "ON_HOLD"

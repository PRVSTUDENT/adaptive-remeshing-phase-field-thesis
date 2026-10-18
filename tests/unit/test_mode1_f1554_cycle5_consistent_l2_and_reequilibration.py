#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit test suite for Task F1554:
Method C Cycle 5 Consistent-L2 Transfer, Multi-Component Energy Preservation,
Dynamic Crack-Front Tracking, and Package 70 Re-Equilibration Candidate Qualification.
"""

import sys
import os
import json
import hashlib
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

F42_CANONICAL_SHA = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"

def test_01_consistent_l2_transfer_metrics_and_energies():
    c5_dir = REPO_ROOT / "runs" / "hpc" / "mode1_stage_c1_2_cycle5_continuation"
    metrics_file = c5_dir / "STAGE_C1_2_CYCLE5_TRANSFER_METRICS.json"
    assert metrics_file.exists(), f"Cycle 5 metrics file missing: {metrics_file}"

    with open(metrics_file, "r", encoding="utf-8") as f:
        metrics = json.load(f)

    # 1. Consistent L2 formulation verification
    assert metrics.get("transfer_method") == "CONSISTENT_L2_GALERKIN_RECONSTRUCTION_AND_HOST_NEAREST_GP"

    # 2. Gate 6C criteria that PASS
    passing_criteria = [
        "criterion_1_displacement_l2",
        "criterion_2_peak_damage",
        "criterion_3_integrated_damage",
        "criterion_4_history_non_negativity",
        "criterion_5_boundary_force_continuity",
        "criterion_6_fracture_energy_preservation",
        "criterion_7_elastic_energy_preservation",
    ]
    for c in passing_criteria:
        assert metrics[c]["verdict"] == "PASS", f"Criterion {c} failed: {metrics[c]}"

    # Exact peak damage preservation
    assert metrics["criterion_2_peak_damage"]["delta"] <= 1e-5
    assert abs(metrics["criterion_2_peak_damage"]["donor_value"] - 1.0009) < 1e-3
    assert abs(metrics["criterion_2_peak_damage"]["recipient_value"] - 1.0009) < 1e-3

    # History non-negativity
    c4 = metrics["criterion_4_history_non_negativity"]
    assert c4["min_H"] >= 0.0
    assert c4["negative_H_count"] == 0

    # Multi-component energy verification
    c6 = metrics["criterion_6_fracture_energy_preservation"]
    assert abs(c6["delta_E_frac_pct"]) <= 0.50, f"Fracture energy discrepancy exceeds 0.50%: {c6['delta_E_frac_pct']}"
    assert c6["verdict"] == "PASS"

    c7 = metrics["criterion_7_elastic_energy_preservation"]
    assert abs(c7["delta_E_elas_pct"]) <= 0.50, f"Elastic energy discrepancy exceeds 0.50%: {c7['delta_E_elas_pct']}"
    assert c7["verdict"] == "PASS"

    # Total energy criterion: recorded honestly as FAIL since +0.2189% > 0.10%
    c8 = metrics["criterion_8_total_energy_preservation"]
    assert c8["verdict"] == "FAIL"

def test_02_dynamic_crack_front_tracking():
    c5_dir = REPO_ROOT / "runs" / "hpc" / "mode1_stage_c1_2_cycle5_continuation"
    metrics_file = c5_dir / "STAGE_C1_2_CYCLE5_TRANSFER_METRICS.json"
    with open(metrics_file, "r", encoding="utf-8") as f:
        metrics = json.load(f)

    # Dynamic crack front coordinate x(d >= 0.5)
    cf_data = metrics.get("crack_front_tracking", {})
    cf_x = cf_data.get("recomputed_crack_front_x_d05_mm", 0.0)
    assert cf_x > 0.65, f"Expected crack front advance > 0.65 mm, got {cf_x}"
    assert abs(cf_x - 0.656302) < 0.001

    # Advance Delta x from notch tip (x = 0.50 mm)
    delta_x_um = (cf_x - 0.50) * 1000.0
    assert abs(delta_x_um - 156.30) < 1.0  # ~156.3 um advance

    # In terms of regularization length scale l0 = 7.5 um
    l0_ratio = delta_x_um / 7.5
    assert abs(l0_ratio - 20.84) < 0.2

def test_03_package70_candidate_integrity():
    pkg70_dir = REPO_ROOT / "models" / "pandey_kumar_mode1" / "70_method_c_cycle5_reequilibration"
    assert pkg70_dir.exists(), f"Package 70 directory missing: {pkg70_dir}"

    inp_file = pkg70_dir / "M1_MC_CYCLE5_RECON_EQUIL.inp"
    assert inp_file.exists(), f"Input deck missing: {inp_file}"
    assert inp_file.stat().st_size > 15_000_000, "Input deck size unexpectedly small"

    # Frozen UEL subroutine check
    uel_file = pkg70_dir / "f42_mixed_uel.for"
    assert uel_file.exists()
    uel_sha = hashlib.sha256(uel_file.read_bytes()).hexdigest()
    assert uel_sha == F42_CANONICAL_SHA, f"Subroutine SHA mismatch: {uel_sha}"

    # PBS script check
    pbs_file = pkg70_dir / "submit_M1_MC_CYCLE5_RECON_EQUIL.pbs"
    assert pbs_file.exists()
    pbs_text = pbs_file.read_text(encoding="utf-8")
    assert "#PBS -m abe" in pbs_text
    assert "job_notifications.sh" in pbs_text

def test_04_governance_and_gate_status():
    c5_dir = REPO_ROOT / "runs" / "hpc" / "mode1_stage_c1_2_cycle5_continuation"
    audit_file = c5_dir / "CYCLE5_PROPAGATION_REMESH_AUDIT.json"
    assert audit_file.exists(), f"Cycle 5 audit missing: {audit_file}"

    with open(audit_file, "r", encoding="utf-8") as f:
        audit = json.load(f)

    # Strict governance: no solver continuation until independent ChatGPT review
    assert audit.get("submission_authorized") is False
    assert audit.get("continuation_job_submitted") is False
    assert audit.get("candidate_package") == "models/pandey_kumar_mode1/70_method_c_cycle5_reequilibration"
    assert audit.get("verdict", {}).get("cycle5_nonmatching_transfer_conservation") == "FAIL"
    assert audit.get("verdict", {}).get("package_70_solver_continuation") == "ON_HOLD"

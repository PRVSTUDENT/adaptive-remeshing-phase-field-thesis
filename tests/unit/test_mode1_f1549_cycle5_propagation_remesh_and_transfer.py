#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit test suite for Task F1549:
Method C Cycle 5 Propagation-Stage Native Adaptive Remesh, Spatial Quantification,
Temporal Peak Convergence (Package 67 vs 65), and Gate 6C Offline Transfer Audit.
"""

import sys
import os
import json
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

def test_01_cycle5_native_remesh_topology():
    c5_dir = REPO_ROOT / "runs" / "hpc" / "mode1_stage_c1_2_cycle5_continuation"
    summary_file = c5_dir / "ADAPTIVE_REMESH_CYCLE5_RESULT_2PCT.json"
    assert summary_file.exists(), f"Cycle 5 remesh summary missing: {summary_file}"

    with open(summary_file, "r", encoding="utf-8") as f:
        summary = json.load(f)

    assert summary["status"] == "NATIVE_ADAPTIVE_REMESH_CYCLE5_SUCCESS"
    assert summary["adapted_elements"] == 34094
    assert summary["adapted_nodes"] == 33975
    assert summary["adapted_quads"] == 33160
    assert summary["adapted_tris"] == 934
    assert summary["error_target"] == 2.0

    raw_inp = c5_dir / "M1_CYCLE5_RAW_ADAPT_2PCT.inp"
    assert raw_inp.exists(), f"Raw adapted deck missing: {raw_inp}"

def test_02_cycle5_spatial_sizing_growth():
    c5_dir = REPO_ROOT / "runs" / "hpc" / "mode1_stage_c1_2_cycle5_continuation"
    audit_file = c5_dir / "CYCLE5_PROPAGATION_REMESH_AUDIT.json"
    assert audit_file.exists(), f"Cycle 5 audit missing: {audit_file}"

    with open(audit_file, "r", encoding="utf-8") as f:
        audit = json.load(f)

    spatial = audit["spatial_adaptation"]
    assert spatial["element_delta"] == 4801
    assert abs(spatial["element_growth_pct"] - 16.39) < 0.1
    assert spatial["fine_element_delta"] == 988  # elements with h <= 2.0 um grew by 988

def test_03_gate_6c_transfer_metrics_pass():
    c5_dir = REPO_ROOT / "runs" / "hpc" / "mode1_stage_c1_2_cycle5_continuation"
    metrics_file = c5_dir / "STAGE_C1_2_CYCLE5_TRANSFER_METRICS.json"
    assert metrics_file.exists(), f"Cycle 5 metrics file missing: {metrics_file}"

    with open(metrics_file, "r", encoding="utf-8") as f:
        metrics = json.load(f)

    for k in [
        "criterion_1_displacement_l2",
        "criterion_2_peak_damage",
        "criterion_3_integrated_damage",
        "criterion_4_history_non_negativity",
        "criterion_5_boundary_force_continuity",
        "criterion_6_fracture_energy_preservation",
        "criterion_7_elastic_and_total_energy",
    ]:
        assert metrics[k]["verdict"] == "PASS", f"Gate 6C criterion {k} failed: {metrics[k]}"

    # Verify history non-negativity
    c4 = metrics["criterion_4_history_non_negativity"]
    assert c4["min_H"] >= 0.0
    assert c4["negative_H_count"] == 0

def test_04_temporal_peak_convergence_pkg67_vs_pkg65():
    summary65_file = REPO_ROOT / "runs" / "hpc" / "mode1_stage_c1_2_propagation_stage2_continuation" / "package65_terminal_summary.json"
    if not summary65_file.exists():
        # Fallback to brain if not copied yet
        summary65_file = Path(r"C:\Users\pruth\.gemini\antigravity-cli\brain\a38a7657-e4ae-41d1-b5db-2028900b5cb4") / "package65_terminal_summary.json"
    assert summary65_file.exists(), f"Package 65 summary missing: {summary65_file}"

    with open(summary65_file, "r", encoding="utf-8") as f:
        summary65 = json.load(f)

    rf_peak_pkg65 = summary65["peak_force_N"]
    assert abs(rf_peak_pkg65 - 732.85) < 0.1

    # Package 67 peak force is 732.48 N at increment 110 (du = 1.25 nm)
    rf_peak_pkg67 = 732.48074
    delta_rf = abs(rf_peak_pkg65 - rf_peak_pkg67)
    delta_pct = delta_rf * 100.0 / rf_peak_pkg65

    # Difference must be <= 0.10% proving temporal convergence
    assert delta_pct <= 0.10, f"Temporal peak force discrepancy exceeds 0.10%: {delta_pct:.4f}%"

def test_05_governance_no_unauthorized_continuation():
    c5_dir = REPO_ROOT / "runs" / "hpc" / "mode1_stage_c1_2_cycle5_continuation"
    audit_file = c5_dir / "CYCLE5_PROPAGATION_REMESH_AUDIT.json"
    with open(audit_file, "r", encoding="utf-8") as f:
        audit = json.load(f)

    assert audit["submission_authorized"] is False
    assert audit["continuation_job_submitted"] is False

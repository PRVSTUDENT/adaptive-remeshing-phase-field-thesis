# -*- coding: utf-8 -*-
"""
tests/unit/test_f1701_pointwise_and_history_aware_remesh.py
===========================================================
Unit tests for Task F1701:
Pointwise UEL Stress Consistency, History-Aware Native Adaptive Remeshing,
and Dual-Crack Refinement Validation.
"""

import os
import sys
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts", "validation"))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts", "visualization"))

from evaluate_f1701_pointwise_stress_recovery import evaluate_pointwise_vs_20bin
from audit_f1701_corridor_connectivity import audit_connectivity
import plot_f1701_pointwise_and_history_aware_synthesis as plotter

def test_f1701_gate_b_pointwise_stress_consistency():
    results = evaluate_pointwise_vs_20bin()
    assert "STATE2" in results
    assert "STATE4" in results
    assert "STATE5" in results

    s2 = results["STATE2"]
    assert s2["gate_b_consistency_verdict"] == "POINTWISE_CONSISTENT_WITHIN_BINNING_BOUNDS"
    assert s2["pointwise_stress_stats"]["max_von_mises_MPa"] > 900.0

    s4 = results["STATE4"]
    assert s4["gate_b_consistency_verdict"] == "POINTWISE_CONSISTENT_WITHIN_BINNING_BOUNDS"
    assert s4["pointwise_stress_stats"]["max_von_mises_MPa"] > 900.0

    s5 = results["STATE5"]
    assert s5["gate_b_consistency_verdict"] == "PHYSICAL_UNLOADING_VS_BIN_STIFFNESS_FLOOR"
    assert s5["pointwise_stress_stats"]["max_von_mises_MPa"] < 1.0, "Reconstructed continuous-degradation stress reflects unloading (peak < 1 MPa)"
    print("\nGate B tests passed: States 2 & 4 consistent; State 5 correctly reflects physical unloading in continuous model.")

def test_f1701_corridor_connectivity_audit():
    audit_res = audit_connectivity()
    assert "primary_corridor" in audit_res
    assert "secondary_corridor" in audit_res

    prim = audit_res["primary_corridor"]
    sec = audit_res["secondary_corridor"]

    # Verify primary corridor statistics
    assert prim["elements_le_l0_count"] == 33
    assert prim["elements_le_l0_half_count"] == 2
    assert prim["max_uncovered_gap_le_l0_mm"] > 0.0

    # Verify secondary corridor statistics
    assert sec["elements_le_l0_count"] == 201
    assert sec["elements_le_l0_half_count"] == 33
    assert sec["elements_le_l0_pct"] > 80.0

    print(f"\nConnectivity audit passed: Primary gap = {prim['max_uncovered_gap_le_l0_mm']} mm, Secondary gap = {sec['max_uncovered_gap_le_l0_mm']} mm")

def test_f1701_generate_synthesis_figure():
    plotter.main()
    pdf_path = os.path.join(REPO_ROOT, "MA_AdaptiveRemeshing_Report_2026", "figures", "fig_f1701_history_aware_remesh_synthesis.pdf")
    png_path = os.path.join(REPO_ROOT, "MA_AdaptiveRemeshing_Report_2026", "figures", "fig_f1701_history_aware_remesh_synthesis.png")
    assert os.path.exists(pdf_path)
    assert os.path.exists(png_path)
    assert os.path.getsize(pdf_path) > 100000

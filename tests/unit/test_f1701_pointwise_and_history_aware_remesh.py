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
import plot_f1701_pointwise_and_history_aware_synthesis as plotter

def test_f1701_gate_b_pointwise_stress_consistency():
    results = evaluate_pointwise_vs_20bin()
    assert "STATE2" in results
    assert "STATE4" in results
    assert "STATE5" in results

    # State 2 (Hole arrest): Active propagation, 20-bin agrees with pointwise within ~3.5%
    s2 = results["STATE2"]
    assert s2["gate_b_consistency_verdict"] == "POINTWISE_CONSISTENT_WITHIN_BINNING_BOUNDS"
    assert s2["pointwise_stress_stats"]["max_von_mises_MPa"] > 900.0

    # State 4 (Secondary mid-prop): Active secondary zone, 20-bin agrees with pointwise within ~4.0%
    s4 = results["STATE4"]
    assert s4["gate_b_consistency_verdict"] == "POINTWISE_CONSISTENT_WITHIN_BINNING_BOUNDS"
    assert s4["pointwise_stress_stats"]["max_von_mises_MPa"] > 900.0

    # State 5 (Terminal dual severance): True UEL is completely unloaded (peak Mises = 0.52 MPa)
    # The 20-bin model had an artificial stiffness floor in the crack gap.
    s5 = results["STATE5"]
    assert s5["gate_b_consistency_verdict"] == "PHYSICAL_UNLOADING_VS_BIN_STIFFNESS_FLOOR"
    assert s5["pointwise_stress_stats"]["max_von_mises_MPa"] < 1.0, "Pointwise stress must reflect complete physical unloading (peak < 1 MPa)"
    print("\nGate B tests passed: States 2 & 4 consistent; State 5 correctly reflects complete physical unloading.")

def test_f1701_gate_e_f_history_aware_adapted_mesh_metrics():
    res_path = os.path.join(REPO_ROOT, "results", "validation", "f1701_history_aware_mesh_metrics.json")
    assert os.path.exists(res_path), "f1701_history_aware_mesh_metrics.json must exist"
    with open(res_path, "r") as f:
        data = json.load(f)

    mm = data["mesh_metrics"]
    assert mm["total_elements"] > 9000, "History-aware adapted mesh must exceed 9000 elements"
    assert mm["quad_pct"] > 95.0, "Quad percentage must exceed 95%"
    assert 99.9 <= mm["area_preservation_pct"] <= 100.1, "Area must be preserved within 0.1%"

    prim = data["corridors"]["primary"]
    sec = data["corridors"]["secondary"]

    # Primary corridor must preserve resolution from State 2 (h <= l0/2 and >= 40% <= l0)
    assert prim["pct_le_l0"] >= 40.0, f"Primary corridor pct <= l0 must be >= 40%, got {prim['pct_le_l0']}%"
    assert prim["min"] <= 0.1425, f"Primary corridor h_min must be <= l0/2 (0.1425 mm), got {prim['min']} mm"

    # Secondary corridor must acquire refinement from State 4 (h <= l0/3 and >= 75% <= l0)
    assert sec["pct_le_l0"] >= 75.0, f"Secondary corridor pct <= l0 must be >= 75%, got {sec['pct_le_l0']}%"
    assert sec["pct_le_l0_half"] >= 10.0, f"Secondary corridor pct <= l0/2 must be >= 10%, got {sec['pct_le_l0_half']}%"
    assert sec["min"] <= 0.0950, f"Secondary corridor h_min must be <= l0/3 (0.0950 mm), got {sec['min']} mm"

    # Dual corridor evaluation verdict
    eval_res = data["dual_corridor_evaluation"]
    assert eval_res["primary_corridor_preserved"] is True
    assert eval_res["secondary_corridor_refined"] is True
    assert eval_res["simultaneous_dual_corridor_refinement"] is True
    assert eval_res["verdict"] == "SIMULTANEOUS_DUAL_CORRIDOR_REFINEMENT_ACHIEVED"
    print("\nGate E & F tests passed: History-aware dual-corridor refinement achieved!")

def test_f1701_generate_synthesis_figure():
    plotter.main()
    pdf_path = os.path.join(REPO_ROOT, "MA_AdaptiveRemeshing_Report_2026", "figures", "fig_f1701_history_aware_remesh_synthesis.pdf")
    png_path = os.path.join(REPO_ROOT, "MA_AdaptiveRemeshing_Report_2026", "figures", "fig_f1701_history_aware_remesh_synthesis.png")
    assert os.path.exists(pdf_path), "Synthesis PDF figure must exist"
    assert os.path.exists(png_path), "Synthesis PNG figure must exist"
    assert os.path.getsize(pdf_path) > 100000, "PDF figure must be substantial"
    print(f"\nFigure generated successfully: {pdf_path} ({os.path.getsize(pdf_path)} bytes)")

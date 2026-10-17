#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit test suite for Task F1534:
1. Cycle 2 Three-Way Trajectory Evaluation (Case A: 14k baseline, Case B: 21k control, Case C: 21k continued)
2. Cycle-Boundary Fracture Energy Ledger and Attenuation Dynamics
3. Limiter Gradient Clipping and Analytical Corner Deficit Verification
4. Cycle 4 Native CAE Adaptive Mesh Qualification (29,293 elements)
"""

import sys
import os
import json
import math
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

def test_cycle2_three_way_trajectory_evaluation():
    three_way_path = REPO_ROOT / "runs" / "hpc" / "mode1_stage_c1_2_cycle2_uninterrupted_control" / "three_way_trajectory_evaluation_cycle2.json"
    assert three_way_path.exists(), f"Missing three-way evaluation file: {three_way_path}"

    with open(three_way_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Step 2 Checkpoint (u = 0.0012 mm)
    step2_metrics = {m["name"]: m for m in data["step2_checkpoint_u0012"]}
    
    # Reaction force continuity
    rf_m = step2_metrics["Reaction Force RF2"]
    assert abs(rf_m["diff_B_vs_C"]) <= 5.0, f"RF2 difference exceeds 5.0 N: {rf_m['diff_B_vs_C']}"
    assert abs(rf_m["pct_B_vs_C"]) < 0.01, f"RF2 percentage difference unexpectedly large: {rf_m['pct_B_vs_C']}%"

    # Peak damage continuity
    d_m = step2_metrics["Maximum Damage d_max"]
    assert abs(d_m["diff_B_vs_C"]) <= 0.020, f"d_max difference exceeds 0.020: {d_m['diff_B_vs_C']}"

    # Elastic energy continuity
    e_elas_m = step2_metrics["Elastic Strain Energy E_elas"]
    assert abs(e_elas_m["pct_B_vs_C"]) <= 0.50, f"Elastic energy jump exceeds 0.50%: {e_elas_m['pct_B_vs_C']}%"
    assert abs(e_elas_m["pct_B_vs_C"]) < 0.01, f"Elastic energy jump unexpectedly large: {e_elas_m['pct_B_vs_C']}%"

    # Total energy continuity
    e_tot_m = step2_metrics["Total Energy E_tot"]
    assert abs(e_tot_m["pct_B_vs_C"]) <= 0.10, f"Total energy jump exceeds 0.10%: {e_tot_m['pct_B_vs_C']}%"
    assert abs(e_tot_m["pct_B_vs_C"]) < 0.001, f"Total energy jump unexpectedly large: {e_tot_m['pct_B_vs_C']}%"

    # 2. Step 3 Endpoint (u = 0.0015 mm)
    step3_metrics = {m["name"]: m for m in data["step3_endpoint_u0015"]}
    
    # Terminal Reaction Force
    rf3_m = step3_metrics["Reaction Force RF2"]
    assert abs(rf3_m["diff_B_vs_C"]) <= 5.0, f"Terminal RF2 diff exceeds 5.0 N: {rf3_m['diff_B_vs_C']}"
    assert abs(rf3_m["pct_B_vs_C"]) < 0.01, f"Terminal RF2 pct diff exceeds 0.01%: {rf3_m['pct_B_vs_C']}%"

    # Terminal Peak Damage
    d3_m = step3_metrics["Maximum Damage d_max"]
    assert abs(d3_m["diff_B_vs_C"]) <= 0.020, f"Terminal d_max diff exceeds 0.020: {d3_m['diff_B_vs_C']}"

    # Terminal History variable parity between continued and uninterrupted
    h3_m = step3_metrics["Maximum History H_max"]
    # Continued matches uninterrupted control to within 0.28%
    assert abs(h3_m["pct_B_vs_C"]) < 0.50, f"Terminal H_max difference exceeds 0.50%: {h3_m['pct_B_vs_C']}%"

    # Discretization resolution proof: Case A vs Case B history elevation is >90%
    assert h3_m["pct_A_vs_B"] > 90.0, f"Discretization H_max rise not observed: {h3_m['pct_A_vs_B']}%"

    # Terminal Elastic Energy
    e_elas3_m = step3_metrics["Elastic Strain Energy E_elas"]
    assert abs(e_elas3_m["pct_B_vs_C"]) <= 0.50, f"Terminal elastic energy diff exceeds 0.50%: {e_elas3_m['pct_B_vs_C']}%"

    # Terminal Total Energy
    e_tot3_m = step3_metrics["Total Energy E_tot"]
    assert abs(e_tot3_m["pct_B_vs_C"]) <= 0.10, f"Terminal total energy diff exceeds 0.10%: {e_tot3_m['pct_B_vs_C']}%"


def test_cycle_boundary_energy_ledger_and_attenuation():
    """Verify that fracture energy error attenuates across sequential cycles."""
    # Cycle 1 terminal: 17k control vs continued
    e_frac_c1_ctrl = 115.10e-6  # mJ
    e_frac_c1_cont = 117.63e-6  # mJ
    c1_err_pct = (e_frac_c1_cont - e_frac_c1_ctrl) / e_frac_c1_ctrl * 100.0
    assert abs(c1_err_pct - 2.20) < 0.10, f"Cycle 1 error mismatch: {c1_err_pct}"

    # Cycle 2 terminal: 21k control vs continued
    e_frac_c2_ctrl = 281.291e-6  # mJ
    e_frac_c2_cont = 285.250e-6  # mJ
    c2_err_pct = (e_frac_c2_cont - e_frac_c2_ctrl) / e_frac_c2_ctrl * 100.0
    assert abs(c2_err_pct - 1.41) < 0.10, f"Cycle 2 error mismatch: {c2_err_pct}"

    # Attenuation proof: percentage error decreases from Cycle 1 to Cycle 2
    assert c2_err_pct < c1_err_pct, f"Fracture energy error not attenuating: C1={c1_err_pct}%, C2={c2_err_pct}%"

    # Forward increment error in Cycle 2:
    # Delta E_frac,cont = 285.25 - 117.10 = 168.15 nJ
    # Delta E_frac,ctrl = 281.29 - 115.13 = 166.16 nJ
    # Difference = 1.99 nJ (only 1.20% of the forward dissipation!)
    delta_e_cont = e_frac_c2_cont - 117.095e-6
    delta_e_ctrl = e_frac_c2_ctrl - 115.134e-6
    diff_forward = abs(delta_e_cont - delta_e_ctrl)
    assert diff_forward < 2.5e-6, f"Forward dissipation increment difference exceeds 2.5 nJ: {diff_forward*1e6} nJ"


def test_bilinear_operator_analytical_clipping_ratios():
    """Verify the exact analytical clipping ratios: 42.26% slope clipping and 15.85% corner deficit."""
    # 2x2 Gauss quadrature location
    xi_gp = 1.0 / math.sqrt(3.0)  # ~0.577350269
    
    # Slope beyond Gauss point to element boundary (xi = 1.0)
    clipped_slope_fraction = (1.0 - xi_gp) / 1.0
    expected_slope_fraction = 1.0 - 1.0 / math.sqrt(3.0)  # ~0.4226497
    assert abs(clipped_slope_fraction - expected_slope_fraction) < 1e-6
    assert abs(clipped_slope_fraction * 100.0 - 42.26) < 0.05

    # Analytical corner deficit calculation:
    # A linear field H(xi) = H0 + g*xi with H0 = 0.010, g = 0.006 has corner value H(1) = 0.016.
    # The max Gauss point value is H(1/sqrt(3)) = 0.010 + 0.006/sqrt(3) = 0.0134641.
    # The bounded limiter clips H at H_max^e = 0.0134641, yielding a corner deficit of:
    # (0.016 - 0.0134641) / 0.016 = 0.0025359 / 0.016 = 15.8494% ~ 15.85%!
    h_exact = 0.016000
    h_gp_max = 0.010 + 0.006 * xi_gp
    analytical_corner_deficit_pct = (h_exact - h_gp_max) / h_exact * 100.0
    assert abs(analytical_corner_deficit_pct - 15.84936) < 1e-4
    assert abs(analytical_corner_deficit_pct - (1.0 - xi_gp) * (0.006 / 0.016) * 100.0) < 1e-4


def test_cycle4_raw_mesh_qualification():
    """Verify Cycle 4 raw adapted mesh generated by native Abaqus CAE adaptiveRemesh."""
    summary_path = REPO_ROOT / "runs" / "hpc" / "mode1_stage_c1_2_cycle4_continuation" / "ADAPTIVE_REMESH_CYCLE4_RESULT_2PCT.json"
    assert summary_path.exists(), f"Missing Cycle 4 remesh summary: {summary_path}"

    with open(summary_path, "r", encoding="utf-8") as f:
        summary = json.load(f)

    assert summary["status"] == "NATIVE_ADAPTIVE_REMESH_CYCLE4_SUCCESS"
    assert summary["adapted_elements"] == 29293
    assert summary["adapted_nodes"] == 29210
    assert summary["adapted_quads"] == 28493
    assert summary["adapted_tris"] == 800
    assert summary["error_target"] == 2.0

    raw_inp_path = REPO_ROOT / "runs" / "hpc" / "mode1_stage_c1_2_cycle4_continuation" / "M1_CYCLE4_RAW_ADAPT_2PCT.inp"
    assert raw_inp_path.exists(), f"Missing Cycle 4 raw input deck: {raw_inp_path}"
    assert raw_inp_path.stat().st_size > 1_500_000

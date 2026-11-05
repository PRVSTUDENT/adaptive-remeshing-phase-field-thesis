#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_f1629_evaluation_engine.py
==========================================
Unit tests for the F1629 comparative evaluation engine.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.validation.evaluate_f1629_paired_execution import (
    calculate_contraction_factors,
    analyze_arm,
    compare_arms,
    generate_markdown_report,
    evaluate,
    DONOR_CHECKPOINT03,
    GATES,
)


def test_calculate_contraction_factors():
    # Synthetic decaying sequence with constant rho = 0.5
    history = [
        {"delta_d": 1.0, "delta_u": 1.0, "delta_history": 1.0},
        {"delta_d": 0.5, "delta_u": 0.5, "delta_history": 0.5},
        {"delta_d": 0.25, "delta_u": 0.25, "delta_history": 0.25},
    ]
    res = calculate_contraction_factors(history, window_size=5)
    assert pytest.approx(res["avg_rho_d"], rel=1e-5) == 0.5
    assert pytest.approx(res["avg_rho_u"], rel=1e-5) == 0.5
    assert pytest.approx(res["avg_rho_h"], rel=1e-5) == 0.5


def test_analyze_arm_converged():
    # Synthetic converged arm
    history = [
        {"outer": 1, "pdas_active_count": 1000, "delta_d": 1e-2, "delta_u": 1e-6, "delta_history": 1.0},
        {"outer": 50, "pdas_active_count": 20, "delta_d": 5e-6, "delta_u": 5e-10, "delta_history": 5e-5, "anderson_applied": True},
    ]
    endpoint = {
        "reaction_force_kN": DONOR_CHECKPOINT03["reaction_force_kN"] * 1.005,  # 0.5% drift
        "total_energy_kNmm": DONOR_CHECKPOINT03["total_energy_kNmm"] * 0.998, # 0.2% drift
        "healing_violations": 0,
    }
    res = analyze_arm("Arm B", "pkg175", "1420392.mmaster02", history, endpoint)

    assert res["iterations_completed"] == 2
    assert res["initial_active_set"] == 1000
    assert res["final_active_set"] == 20
    assert res["active_set_reduction_pct"] == 98.0
    assert res["anderson_steps_applied"] == 1
    assert res["gates"]["delta_d_pass"] is True
    assert res["gates"]["delta_u_pass"] is True
    assert res["gates"]["delta_h_pass"] is True
    assert res["gates"]["coupled_convergence_pass"] is True
    assert res["gates"]["reaction_force_continuity_pass"] is True
    assert res["gates"]["total_energy_continuity_pass"] is True
    assert res["gates"]["damage_healing_pass"] is True
    assert res["gates"]["overall_physical_acceptance_pass"] is True


def test_analyze_arm_nonconverged():
    # Synthetic nonconverged arm
    history = [
        {"outer": 1, "pdas_active_count": 1000, "delta_d": 1e-2, "delta_u": 1e-6, "delta_history": 1.0},
        {"outer": 140, "pdas_active_count": 35, "delta_d": 7e-3, "delta_u": 5e-5, "delta_history": 50.0},
    ]
    endpoint = {
        "reaction_force_kN": DONOR_CHECKPOINT03["reaction_force_kN"],
        "total_energy_kNmm": DONOR_CHECKPOINT03["total_energy_kNmm"],
        "healing_violations": 0,
    }
    res = analyze_arm("Arm A", "pkg174", "1420391.mmaster02", history, endpoint)

    assert res["iterations_completed"] == 2
    assert res["gates"]["delta_d_pass"] is False
    assert res["gates"]["delta_u_pass"] is False
    assert res["gates"]["delta_h_pass"] is False
    assert res["gates"]["coupled_convergence_pass"] is False
    assert res["gates"]["overall_physical_acceptance_pass"] is False


def test_compare_arms_speedup():
    arm_a = {
        "iterations_completed": 140,
        "final_delta_d": 7e-3,
        "final_delta_u_mm": 5e-5,
        "final_delta_h_mpa": 50.0,
        "active_set_reduction_pct": 95.0,
        "gates": {"coupled_convergence_pass": False},
    }
    arm_b = {
        "iterations_completed": 85,
        "final_delta_d": 7e-6,
        "final_delta_u_mm": 5e-10,
        "final_delta_h_mpa": 5e-5,
        "active_set_reduction_pct": 99.0,
        "gates": {"coupled_convergence_pass": True},
    }
    cmp = compare_arms(arm_a, arm_b)
    assert cmp["comparison_valid"] is True
    assert pytest.approx(cmp["anderson_over_picard_ratio_delta_d"], rel=1e-3) == 1000.0
    assert pytest.approx(cmp["anderson_over_picard_ratio_delta_u"], rel=1e-3) == 100000.0
    assert pytest.approx(cmp["anderson_over_picard_ratio_delta_h"], rel=1e-3) == 1000000.0
    assert cmp["arm_b_accelerated_convergence"] is True


def test_end_to_end_evaluate(tmp_path: Path):
    d174 = tmp_path / "174"
    d175 = tmp_path / "175"
    d174.mkdir()
    d175.mkdir()

    # Write telemetry
    t_a = [{"outer": 1, "delta_d": 1e-2, "delta_u": 1e-4, "delta_history": 1.0, "pdas_active_count": 500}]
    t_b = [{"outer": 1, "delta_d": 1e-2, "delta_u": 1e-4, "delta_history": 1.0, "pdas_active_count": 500, "anderson_applied": True}]
    with open(d174 / "live_iteration_telemetry.json", "w", encoding="utf-8") as f:
        json.dump(t_a, f)
    with open(d175 / "live_iteration_telemetry.json", "w", encoding="utf-8") as f:
        json.dump(t_b, f)

    out = tmp_path / "out"
    summary = evaluate(d174, d175, "1420391.mmaster02", "1420392.mmaster02", out_dir=out)

    assert (out / "f1629_paired_execution_summary.json").is_file()
    assert (out / "f1629_paired_execution_report.md").is_file()
    assert summary["arm_a_picard"]["iterations_completed"] == 1
    assert summary["arm_b_anderson"]["iterations_completed"] == 1

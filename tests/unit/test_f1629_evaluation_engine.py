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
    # Synthetic converged arm with explicit positive evidence on every required gate
    history = [
        {
            "outer": 1,
            "pdas_active_count": 1000,
            "delta_d": 1e-2,
            "raw_delta_d": 1e-2,
            "delta_u": 1e-6,
            "delta_u_raw": 1e-6,
            "delta_history": 1.0,
            "free_error": 1e-7,
            "dual_error": 1e-8,
            "complementarity": 1e-8,
            "kkt_post_passed": True,
        },
        {
            "outer": 50,
            "pdas_active_count": 20,
            "delta_d": 5e-6,
            "raw_delta_d": 5e-6,
            "delta_u": 5e-10,
            "delta_u_raw": 5e-10,
            "delta_history": 5e-5,
            "anderson_applied": True,
            "free_error": 5e-8,
            "dual_error": 1e-9,
            "complementarity": 2e-8,
            "kkt_post_passed": True,
        },
    ]
    endpoint = {
        "reaction_force_kN": DONOR_CHECKPOINT03["reaction_force_kN"] * 1.005,  # 0.5% drift
        "total_energy_kNmm": DONOR_CHECKPOINT03["total_energy_kNmm"] * 0.998, # 0.2% drift
        "healing_violations": 0,
        "history_monotonicity": True,
        "thermodynamic_consistency": True,
        "coupled_field_consistency_u_pass": True,
        "coupled_field_consistency_h_pass": True,
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
    assert res["gates"]["kkt_pass"] is True
    assert res["gates"]["coupled_convergence_pass"] is True
    assert res["gates"]["reaction_force_continuity_pass"] is True
    assert res["gates"]["total_energy_continuity_pass"] is True
    assert res["gates"]["damage_healing_pass"] is True
    assert res["gates"]["history_monotonicity_pass"] is True
    assert res["gates"]["thermodynamic_consistency_pass"] is True
    assert res["gates"]["mechanical_consistency_pass"] is True
    assert res["gates"]["overall_physical_acceptance_pass"] is True


def test_fail_closed_missing_or_null_evidence_gates():
    """
    Negative regression tests for INC-2026-11-06-03:
    Missing or None consistency, monotonicity, thermodynamic, or KKT components must fail closed.
    """
    base_iter = {
        "outer": 50,
        "pdas_active_count": 20,
        "delta_d": 5e-6,
        "raw_delta_d": 5e-6,
        "delta_u": 5e-10,
        "delta_u_raw": 5e-10,
        "delta_history": 5e-5,
        "free_error": 5e-8,
        "dual_error": 1e-9,
        "complementarity": 2e-8,
        "kkt_post_passed": True,
    }
    base_state = {
        "reaction_force_kN": DONOR_CHECKPOINT03["reaction_force_kN"],
        "total_energy_kNmm": DONOR_CHECKPOINT03["total_energy_kNmm"],
        "healing_violations": 0,
        "history_monotonicity": True,
        "thermodynamic_consistency": True,
        "coupled_field_consistency_u_pass": True,
        "coupled_field_consistency_h_pass": True,
    }

    # 1. Missing/None coupled_field_consistency_u_pass or coupled_field_consistency_h_pass
    s_no_mech = {**base_state, "coupled_field_consistency_u_pass": None, "coupled_field_consistency_h_pass": None}
    r1 = analyze_arm("Arm A", "pkg174", "1420429.mmaster02", [base_iter], s_no_mech)
    assert r1["gates"]["mechanical_consistency_pass"] is False
    assert r1["gates"]["overall_physical_acceptance_pass"] is False

    s_partial_mech = {**base_state, "coupled_field_consistency_u_pass": True, "coupled_field_consistency_h_pass": None}
    r1b = analyze_arm("Arm A", "pkg174", "1420429.mmaster02", [base_iter], s_partial_mech)
    assert r1b["gates"]["mechanical_consistency_pass"] is False
    assert r1b["gates"]["overall_physical_acceptance_pass"] is False

    # 2. Missing/None history_monotonicity
    s_no_mono = {k: v for k, v in base_state.items() if k != "history_monotonicity"}
    r2 = analyze_arm("Arm A", "pkg174", "1420429.mmaster02", [base_iter], s_no_mono)
    assert r2["history_monotonicity_pass"] is None
    assert r2["gates"]["history_monotonicity_pass"] is False
    assert r2["gates"]["overall_physical_acceptance_pass"] is False

    # 3. Missing/None thermodynamic_consistency
    s_no_thermo = {k: v for k, v in base_state.items() if k != "thermodynamic_consistency"}
    r3 = analyze_arm("Arm A", "pkg174", "1420429.mmaster02", [base_iter], s_no_thermo)
    assert r3["thermodynamic_consistency_pass"] is None
    assert r3["gates"]["thermodynamic_consistency_pass"] is False
    assert r3["gates"]["overall_physical_acceptance_pass"] is False

    # 4. Missing KKT residual components (free_error, dual_error, or complementarity)
    for kkt_key in ("free_error", "dual_error", "complementarity"):
        iter_missing_kkt = {**base_iter, kkt_key: None}
        r4 = analyze_arm("Arm A", "pkg174", "1420429.mmaster02", [iter_missing_kkt], base_state)
        assert r4["gates"]["kkt_pass"] is False, f"Expected kkt_pass=False when {kkt_key} is None"
        assert r4["gates"]["coupled_convergence_pass"] is False
        assert r4["gates"]["overall_physical_acceptance_pass"] is False

    # 5. Missing healing_violations evidence
    s_no_heal = {k: v for k, v in base_state.items() if k != "healing_violations"}
    r5 = analyze_arm("Arm A", "pkg174", "1420429.mmaster02", [base_iter], s_no_heal)
    assert r5["damage_healing_violations"] is None
    assert r5["gates"]["damage_healing_pass"] is False
    assert r5["gates"]["overall_physical_acceptance_pass"] is False


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
        "final_raw_delta_d": 7e-3,
        "final_delta_u_mm": 5e-5,
        "final_delta_u_raw_mm": 5e-5,
        "final_delta_h_mpa": 50.0,
        "active_set_reduction_pct": 95.0,
        "gates": {"coupled_convergence_pass": False},
    }
    arm_b = {
        "iterations_completed": 85,
        "anderson_steps_applied": 12,
        "final_delta_d": 7e-6,
        "final_raw_delta_d": 7e-6,
        "final_delta_u_mm": 5e-10,
        "final_delta_u_raw_mm": 5e-10,
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


def test_authentic_f1630_terminal_evaluation_verdict():
    summary_path = REPO_ROOT / "results" / "validation" / "f1630_paired_execution_summary.json"
    report_path = REPO_ROOT / "results" / "validation" / "f1630_paired_execution_report.md"
    assert summary_path.is_file()
    assert report_path.is_file()

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["task_id"] == "F1630-METHOD-C-C6-R12-REPAIRED-DRIVER-PAIRED-EXECUTION"
    arm_a = summary["arm_a_picard"]
    arm_b = summary["arm_b_anderson"]
    comp = summary["comparison"]

    # 1. Strict coupled convergence (both FAIL after 140 outer iterations)
    assert arm_a["pbs_job_id"] == "1420429.mmaster02"
    assert arm_b["pbs_job_id"] == "1420430.mmaster02"
    assert arm_a["iterations_completed"] == 140
    assert arm_b["iterations_completed"] == 140
    assert arm_a["exit_status"] == 0
    assert arm_b["exit_status"] == 0
    assert arm_a["gates"]["coupled_convergence_pass"] is False
    assert arm_b["gates"]["coupled_convergence_pass"] is False

    # 2. Final raw and relaxed Delta d, Delta u, Delta H
    assert pytest.approx(arm_a["final_delta_d"], rel=1e-5) == 7.623741e-3
    assert pytest.approx(arm_a["final_raw_delta_d"], rel=1e-5) == 8.969107e-3
    assert pytest.approx(arm_a["final_delta_u_mm"], rel=1e-5) == 5.477445e-5
    assert pytest.approx(arm_a["final_delta_u_raw_mm"], rel=1e-5) == 6.444053e-5
    assert pytest.approx(arm_a["final_delta_h_mpa"], rel=1e-5) == 311.39484

    # 3. Signed KKT and active-set status
    assert arm_a["gates"]["kkt_pass"] is True
    assert arm_b["gates"]["kkt_pass"] is True
    assert arm_a["initial_active_set"] == 14088
    assert arm_a["final_active_set"] == 66
    assert arm_a["stage2_iterations"] == 46
    assert arm_a["rollback_events"] == 0

    # 4. Anderson acceleration status
    assert arm_b["anderson_steps_applied"] == 0
    assert arm_b["anderson_fallbacks"] == 19
    assert arm_b["anderson_resets"] == 114
    assert comp["matching_iterations"]["identical_across_all_common_iterations"] is True
    assert comp["matching_iterations"]["first_divergence_outer"] is None

    # 5. Final force, energy, irreversibility, checkpoint acceptance (fail-closed on missing post-convergence gates)
    assert arm_a["gates"]["reaction_force_continuity_pass"] is False
    assert arm_a["gates"]["total_energy_continuity_pass"] is False
    assert arm_a["max_raw_healing_violations"] == 3
    assert arm_a["history_monotonicity_pass"] is None
    assert arm_a["thermodynamic_consistency_pass"] is None
    assert arm_a["coupled_field_consistency_u_pass"] is None
    assert arm_a["coupled_field_consistency_h_pass"] is None
    assert arm_a["gates"]["history_monotonicity_pass"] is False
    assert arm_a["gates"]["thermodynamic_consistency_pass"] is False
    assert arm_a["gates"]["mechanical_consistency_pass"] is False
    assert arm_a["gates"]["overall_physical_acceptance_pass"] is False

    # 6. Dominant cause of nonconvergence
    assert comp["bottleneck_arm_a"]["dominant_residual"] == "delta_h"
    assert comp["bottleneck_arm_b"]["dominant_residual"] == "delta_h"


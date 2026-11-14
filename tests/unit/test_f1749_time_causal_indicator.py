# -*- coding: utf-8 -*-
"""
tests/unit/test_f1749_time_causal_indicator.py
Task F1749: Unit Test Suite for Time-Causal Damage-Aware Refinement Indicator Module,
Temporal Causality Validation, Case 2 Provenance Reconciliation, and Zero-PBS Governance.
"""

import os
import json
import pytest
import numpy as np

from scripts.remeshing.time_causal_damage_indicator import (
    TimeCausalDamageIndicator,
    run_causal_case3_audit
)

def test_f1749_deliverables_exist():
    """Verify all F1749 artifacts exist and are non-empty."""
    expected_files = [
        "scripts/remeshing/time_causal_damage_indicator.py",
        "scripts/remeshing/run_f1749_validation.py",
        "scripts/remeshing/plot_f1749_time_causal_synthesis.py",
        "results/validation/f1749_time_causal_indicator_summary.json",
        "results/figures/fig_f1749_time_causal_synthesis.png",
        "results/figures/fig_f1749_time_causal_synthesis.pdf",
        "docs/validation/F1749_TIME_CAUSAL_DAMAGE_INDICATOR_REPORT.md"
    ]
    for rel_path in expected_files:
        assert os.path.exists(rel_path), f"Missing deliverable: {rel_path}"
        assert os.path.getsize(rel_path) > 100, f"Empty or truncated deliverable: {rel_path}"

def test_f1749_case2_reconciled_provenance():
    """Verify Case 2 provenance is correctly reconciled against Job 1423271."""
    summary_path = "results/validation/f1749_time_causal_indicator_summary.json"
    with open(summary_path, "r", encoding="utf-8") as f:
        summary = json.load(f)
    
    c2 = summary["case2_provenance_reconciliation"]
    assert c2["authoritative_solver_job_id"] == "1423271.mmaster02"
    assert c2["coarse_recovery_job_id"] == "1423235.mmaster02"
    
    geom = c2["geometry_and_notch_reconciliation"]
    assert geom["initial_notch_presence"] is True
    assert geom["notch_length_mm"] == pytest.approx(0.50, abs=1e-4)
    assert "107 duplicate coincident node pairs" in geom["seam_implementation"]
    assert "Center (0.65, 0.65) mm" in geom["off_axis_hole"]
    
    incs = c2["increment_count_reconciliation"]
    assert incs["total_converged_increments"] == 252
    assert incs["step1_increments"] == 50
    assert incs["step2_increments"] == 202
    assert incs["solver_exit_status"] == 1
    
    disp = c2["displacement_and_reaction_reconciliation"]
    assert disp["terminal_displacement_at_exit_mm"] == pytest.approx(0.007677, abs=1e-6)
    assert disp["terminal_reaction_force_N"] == pytest.approx(244.42, abs=0.1)
    assert disp["post_peak_softening_drop_pct"] == pytest.approx(57.25, abs=0.1)
    
    h_rec = summary["history_variable_reconciliation"]
    assert h_rec["crack_initiation_threshold_H0"] == pytest.approx(0.180, abs=1e-3)
    assert h_rec["max_history_H_max"] == pytest.approx(3955.22, abs=0.1)
    assert h_rec["distribution_evidence"]["elements_with_H_ge_1000_kN_mm2"] == 39
    assert "d >= 0.9994" in h_rec["distribution_evidence"]["all_top_39_elements_damage_state"]

def test_f1749_analytical_sizing_law_guarantees():
    """Verify analytical sizing law provides mathematical guarantees for process zone."""
    l0 = 0.285
    h_bg = 1.367
    indicator = TimeCausalDamageIndicator(char_length_l0=l0, coarse_elem_size_h_bg=h_bg)

    # 1. Crack core (d >= exp(-0.5) ~ 0.6065): h = l0 / 3 = 0.0950 mm
    assert indicator.compute_element_target_size(1.0) == pytest.approx(l0 / 3.0, abs=1e-4)
    assert indicator.compute_element_target_size(0.8) == pytest.approx(l0 / 3.0, abs=1e-4)
    assert indicator.compute_element_target_size(0.6065) == pytest.approx(l0 / 3.0, abs=1e-3)

    # 2. Process zone limit (d = exp(-1) ~ 0.3679): h <= l0 / 2 = 0.1425 mm
    h_pz = indicator.compute_element_target_size(np.exp(-1.0))
    assert h_pz <= (l0 / 2.0 + 1e-5)
    assert h_pz == pytest.approx(l0 / 2.0, abs=1e-4)

    # 3. Diffuse tail transition (d = 0.1): l0/2 < h < h_bg
    h_mid = indicator.compute_element_target_size(0.10)
    assert l0 / 2.0 < h_mid < h_bg

    # 4. Far-field bulk (d < 0.05): h = h_bg
    assert indicator.compute_element_target_size(0.04) == pytest.approx(h_bg, abs=1e-4)
    assert indicator.compute_element_target_size(0.00) == pytest.approx(h_bg, abs=1e-4)

def test_f1749_strict_temporal_causality():
    """Verify zero future-solution leakage at early initiation states."""
    summary_path = "results/validation/f1749_time_causal_indicator_summary.json"
    with open(summary_path, "r", encoding="utf-8") as f:
        summary = json.load(f)

    prog = summary["case3_time_causal_progression"]
    # prog is a list of 5 states
    assert len(prog) == 5
    
    # State a (u_y = 0.10 mm, index 0): Primary active, Secondary STRICTLY 0% active
    st_a = prog[0]
    assert st_a["state_id"] == "state_a"
    assert st_a["primary_corridor_active_count"] == 35
    assert st_a["primary_corridor_active_pct"] == pytest.approx(100.0, abs=1e-2)
    
    assert st_a["secondary_corridor_active_count"] == 0
    assert st_a["secondary_corridor_active_pct"] == pytest.approx(0.0, abs=1e-2)

    # State b (u_y = 0.20 mm, index 1): Secondary corridor has 4 active elements out of 21 (~19%)
    st_b = prog[1]
    assert st_b["state_id"] == "state_b"
    assert st_b["primary_corridor_active_count"] == 35

    # State e (u_y = 1.50 mm, index 4): Both corridors 100% active
    st_e = prog[4]
    assert st_e["state_id"] == "state_e"
    assert st_e["primary_corridor_active_pct"] == pytest.approx(100.0, abs=1e-2)
    assert st_e["secondary_corridor_active_pct"] == pytest.approx(100.0, abs=1e-2)

    # Monotonic growth in total active elements across states
    active_counts = [st["active_elements_count"] for st in prog]
    for i in range(len(active_counts) - 1):
        assert active_counts[i] <= active_counts[i+1]

def test_f1749_zero_pbs_governance():
    """Verify strict zero-PBS governance and cumulative submission preservation."""
    with open("project_coordination/ACTIVE_TASK.json", "r", encoding="utf-8") as f:
        task = json.load(f)
    assert task["max_new_pbs_submissions"] == 0
    assert task["submissions_consumed"] == 0
    assert task["cumulative_pbs_submissions"] == 25
    assert len(task["historical_pbs_job_ids"]) == 25
    assert task["frozen_uel_sha256"] == "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

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
        "scripts/remeshing/run_f1749_source_aligned_correction.py",
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
    """Verify Case 2 provenance and solver controls are correctly reconciled against Job 1423271."""
    summary_path = "results/validation/f1749_time_causal_indicator_summary.json"
    with open(summary_path, "r", encoding="utf-8") as f:
        summary = json.load(f)
    
    c2 = summary["case2_provenance_reconciliation"]
    assert c2["authoritative_solver_job_id"] == "1423271.mmaster02"
    assert c2["coarse_recovery_job_id"] == "1423235.mmaster02"
    
    geom = c2["geometry_features"]
    assert geom["initial_crack_seam_present"] is True
    assert geom["notch_length_mm"] == pytest.approx(0.50, abs=1e-4)
    assert geom["coincident_node_pairs_count"] == 107
    assert geom["off_axis_hole_present"] is True
    assert geom["hole_radius_mm"] == pytest.approx(0.10, abs=1e-4)
    
    ctrls = c2["increment_and_solver_controls"]
    assert ctrls["total_converged_increments"] == 252
    assert ctrls["step_1_increments"] == 50
    assert ctrls["step_2_increments"] == 202
    assert ctrls["step_1_min_increment_parameter"] == pytest.approx(1.0e-7, abs=1e-9)
    assert ctrls["step_2_min_increment_parameter"] == pytest.approx(1.0e-8, abs=1e-10)
    
    disp = c2["displacement_and_reaction_reconciliation"]
    assert disp["terminal_displacement_mm"] == pytest.approx(0.007677, abs=1e-5)
    assert disp["final_reaction_force_N"] == pytest.approx(244.42, abs=0.1)
    assert disp["post_peak_softening_drop_pct"] == pytest.approx(57.25, abs=0.1)
    
    h_rec = c2["history_variable_reconciliation"]
    assert h_rec["crack_initiation_threshold_H0"] == pytest.approx(0.180, abs=1e-3)
    assert h_rec["H_max_kN_per_mm2"] == pytest.approx(3955.22, abs=0.1)

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

def test_f1749_strict_temporal_causality_and_reconstructed_lineage():
    """Verify source-aligned temporal causality across canonical checkpoints."""
    summary_path = "results/validation/f1749_time_causal_indicator_summary.json"
    with open(summary_path, "r", encoding="utf-8") as f:
        summary = json.load(f)

    prog = summary["case3_canonical_checkpoint_progression"]
    assert len(prog) == 5

    # Checkpoint displacements
    disps = [st["uy_mm"] for st in prog]
    assert disps == [0.10, 0.20, 0.25, 0.30, 1.50]

    # Global active element counts
    active_counts = [st["global_active_elements_d_ge_005"] for st in prog]
    assert active_counts == [342, 540, 575, 616, 667]

    # Global max damage values
    max_damages = [st["max_damage_global"] for st in prog]
    assert max_damages[0] == pytest.approx(0.984607, abs=1e-5)
    assert max_damages[4] == pytest.approx(0.999989, abs=1e-5)

    # State a (u_y = 0.10 mm): Primary active, Secondary STRICTLY 0% active
    st_a = prog[0]
    assert st_a["state_id"] == "state_a"
    assert st_a["primary_corridor"]["damage_active_count_d_ge_005"] == 35
    assert st_a["primary_corridor"]["damage_active_pct"] == pytest.approx(100.0, abs=1e-2)
    assert st_a["primary_corridor"]["process_target_count_h_le_half"] == 3
    assert st_a["primary_corridor"]["process_target_pct"] == pytest.approx(8.5714, abs=1e-2)
    
    assert st_a["secondary_corridor"]["damage_active_count_d_ge_005"] == 0
    assert st_a["secondary_corridor"]["damage_active_pct"] == pytest.approx(0.0, abs=1e-2)
    assert st_a["secondary_corridor"]["process_target_count_h_le_half"] == 0

    # Secondary causal progression across states
    sec_active = [st["secondary_corridor"]["damage_active_count_d_ge_005"] for st in prog]
    assert sec_active == [0, 4, 5, 11, 21]

    sec_proc = [st["secondary_corridor"]["process_target_count_h_le_half"] for st in prog]
    assert sec_proc == [0, 0, 1, 5, 21]

    # Native mapping interface presence
    mapping = summary["native_abaqus_interface_mapping"]
    assert "UNIFORM_ERROR" in mapping["framework"]
    assert "eta_hat_e = errorTarget * (h_old / h_target(d))" in mapping["inversion_derivation"]

def test_f1749_zero_pbs_governance():
    """Verify strict zero-PBS governance and cumulative submission preservation."""
    with open("project_coordination/ACTIVE_TASK.json", "r", encoding="utf-8") as f:
        task = json.load(f)
    assert task["max_new_pbs_submissions"] == 0
    assert task["submissions_consumed"] == 0
    assert task["cumulative_pbs_submissions"] == 25
    assert len(task["historical_pbs_job_ids"]) == 25
    assert task["frozen_uel_sha256"] == "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

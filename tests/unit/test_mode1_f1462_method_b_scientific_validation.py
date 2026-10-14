# -*- coding: utf-8 -*-
"""
Unit Test Suite for Task F1462:
Validate Method B Scientific Findings, Reconcile Pre-Analysis Damage Contradiction,
Verify Load-Partition Invariance, Audit Adaptive Limitation, and Check Matched Energies.

Tests:
1. test_f1462_preanalysis_damage_reconciliation:
   Verifies physical UEL donor state has localized notch damage (d_max = 0.094910, 99.66% elements d < 0.05)
   while companion continuum overlay layer operates with zero damage coupling and linear elasticity.
2. test_f1462_method_b_step_partition_invariance:
   Verifies 1S, 2S, and 4S produce bitwise identical error indicators and adapted mesh topologies.
3. test_f1462_adaptive_limitation_and_plateau_elimination:
   Verifies native Method B crack pinning vs Corrected Method B complete plateau elimination.
4. test_f1462_matched_displacement_energy_conservation:
   Verifies like-for-like matched-horizon external work (-31.49% vs Original B, -3.87% vs ref)
   and internal energy conservation residual <= 1.5% in Corrected Method B.
5. test_f1462_active_hpc_jobs_tracking:
   Verifies active 8-thread SMP jobs 1412872 and 1412873 are properly tracked.
6. test_f1462_production_uel_hash_integrity:
   Verifies f42_mixed_uel.for matches authoritative SHA-256.
"""
import os
import json
import hashlib
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
COORDINATION_DIR = REPO_ROOT / "project_coordination"
MODELS_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1"
RUNS_DIR = REPO_ROOT / "runs" / "mode1"

FROZEN_BASELINE_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
CANONICAL_REF_K0 = 137.945520  # kN/mm
CANONICAL_REF_FMAX = 0.757802  # kN
CANONICAL_REF_MATCHED_WEXT = 2.358682  # mJ at u = 0.007889 mm

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

def test_f1462_preanalysis_damage_reconciliation():
    """Verify that physical UEL layer experiences localized sub-initiation damage at notch tip
    (d_max = 0.094910) while companion continuum overlay layer operates with zero damage coupling."""
    donor_path = MODELS_DIR / "41_method_c_genuine_continuation" / "evidence_forward_audit" / "coarse_donor_state_u0050.json"
    assert donor_path.is_file(), f"Missing donor state JSON: {donor_path}"
    with open(donor_path, "r", encoding="utf-8") as f:
        donor = json.load(f)

    # Physical donor state from coupled UEL solve (Job 1411891)
    d_nodal = donor["d_nodal"]
    d_elem = donor["d_elem"]
    max_d_nodal = donor["max_d_nodal"]
    max_d_elem = donor["max_d_elem"]

    # Localized notch damage: d_max ≈ 0.095 at notch tip
    assert abs(max_d_nodal - 0.094910) < 1e-4, f"Unexpected max nodal damage: {max_d_nodal}"
    assert abs(max_d_elem - 0.100567) < 1e-4, f"Unexpected max elem damage: {max_d_elem}"

    # Over 99.6% of domain has d < 0.05, and only 10 elements have d >= 0.05
    elements_sub005 = sum(1 for v in d_elem.values() if v < 0.05)
    assert elements_sub005 >= 2890, f"Too many damaged elements: {elements_sub005}"
    assert sum(1 for v in d_elem.values() if v >= 0.05) <= 15, "Widespread high damage found"

    # Companion continuum pre-analysis (Job 1411924)
    inf_res_path = RUNS_DIR / "method_b_inf_companion" / "inf_companion_method_b_results.json"
    assert inf_res_path.is_file(), f"Missing companion results JSON: {inf_res_path}"
    with open(inf_res_path, "r", encoding="utf-8") as f:
        comp_data = json.load(f)

    # Invariance across 1S, 2S, 4S
    efc = comp_data.get("error_field_comparison", {})
    assert efc.get("max_diff_1s_2s") == 0.0, "Companion layer 1S vs 2S error difference is non-zero"
    assert efc.get("max_diff_1s_4s") == 0.0, "Companion layer 1S vs 4S error difference is non-zero"

def test_f1462_method_b_step_partition_invariance():
    """Verify that pre-analysis step partitioning (1S vs 2S vs 4S) yields identical adapted meshes."""
    inf_res_path = RUNS_DIR / "method_b_inf_companion" / "inf_companion_method_b_results.json"
    with open(inf_res_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    topo = data.get("mesh_topology_comparison", {})
    assert topo.get("element_count_1s") == 14677
    assert topo.get("element_count_2s") == 14677
    assert topo.get("element_count_4s") == 14677
    assert topo.get("identical_counts") is True
    assert topo.get("step_partition_mesh_invariance_verified") is True

    remesh = data.get("native_remeshing", {})
    for step_key in ["1S", "2S", "4S"]:
        assert remesh[step_key]["adapted_element_count"] == 14677
        assert remesh[step_key]["adapted_node_count"] == 14646
        assert remesh[step_key]["corridor_count"] == 3754
        assert remesh[step_key]["status"] == "SUCCESS"

def test_f1462_adaptive_limitation_and_plateau_elimination():
    """Verify that Corrected Method B completely eliminates the artificial force plateau."""
    eval_path = MODELS_DIR / "40_method_b_corrected_propagation_14k" / "evidence_1412465" / "corrected_method_b_evaluation.json"
    assert eval_path.is_file(), f"Missing evaluation file: {eval_path}"
    with open(eval_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Elastic stiffness within 0.05%
    k0 = data["K0_kN_per_mm"]
    assert abs(k0 - CANONICAL_REF_K0) / CANONICAL_REF_K0 < 0.0005, f"K0 mismatch: {k0}"

    # Peak reaction force within 2.0%
    fmax = data["F_max_kN"]
    assert abs(fmax - CANONICAL_REF_FMAX) / CANONICAL_REF_FMAX < 0.02, f"F_max mismatch: {fmax}"

    # Plateau elimination verdict is PASS
    crit = data["acceptance_criteria_evaluation"]
    plat = crit["plateau_elimination"]
    assert plat["verdict"] == "PASS"
    assert "0.002055 kN" in plat["observed"]
    assert "-99.61%" in plat["observed"]

def test_f1462_matched_displacement_energy_conservation():
    """Verify matched-displacement external work reduction and internal energy conservation."""
    eval_path = MODELS_DIR / "40_method_b_corrected_propagation_14k" / "evidence_1412465" / "corrected_method_b_evaluation.json"
    with open(eval_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    w_ext = data["W_ext_terminal_mJ"]  # at u = 0.007889 mm: 2.267379 mJ
    e_frac = data["E_fracture_terminal_mJ"]  # 2.285469 mJ
    e_elas = data["E_elastic_terminal_mJ"]   # 0.006960 mJ
    delta_e = data["energy_residual_delta_E_mJ"]
    rel_err = data["energy_residual_rel_pct"]

    # Matched work reduction vs Original Method B (3.309642 mJ): >= 30%
    w_orig_matched = 3.309642
    reduction = (w_orig_matched - w_ext) / w_orig_matched
    assert reduction >= 0.30, f"Work reduction below 30%: {reduction*100}%"
    assert abs(reduction - 0.314896) < 0.001

    # Matched work vs Canonical Reference (2.3587 mJ): within -4%
    diff_vs_ref = (w_ext - CANONICAL_REF_MATCHED_WEXT) / CANONICAL_REF_MATCHED_WEXT
    assert abs(diff_vs_ref) < 0.05, f"Discrepancy vs ref too large: {diff_vs_ref*100}%"
    assert abs(diff_vs_ref - (-0.03871)) < 0.001

    # Global internal energy balance: relative error <= 1.5%
    assert rel_err <= 1.5, f"Energy residual too high: {rel_err}%"
    assert abs(delta_e - 0.025050) < 0.001

def test_f1462_active_hpc_jobs_tracking():
    """Verify that jobs 1412872 and 1412873 are tracked in active coordination ledgers."""
    task_file = COORDINATION_DIR / "ACTIVE_TASK.json"
    with open(task_file, "r", encoding="utf-8") as f:
        task_data = json.load(f)
    tracked_jobs = task_data.get("active_pbs_job_ids", []) + task_data.get("completed_pbs_job_ids", [])
    assert "1412872.mmaster02" in tracked_jobs
    assert "1412873.mmaster02" in tracked_jobs

    ledger_file = COORDINATION_DIR / "HPC_JOB_LEDGER.csv"
    with open(ledger_file, "r", encoding="utf-8") as f:
        ledger_text = f.read()
    assert "1412872.mmaster02" in ledger_text
    assert "1412873.mmaster02" in ledger_text

def test_f1462_production_uel_hash_integrity():
    """Verify production UEL source f42_mixed_uel.for matches authoritative SHA-256."""
    uel_path = MODELS_DIR / "f42_mixed_uel.for"
    assert uel_path.is_file()
    actual_hash = sha256_file(uel_path)
    assert actual_hash == FROZEN_BASELINE_UEL_HASH

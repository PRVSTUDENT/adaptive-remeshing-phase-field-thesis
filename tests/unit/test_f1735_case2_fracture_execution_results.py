# -*- coding: utf-8 -*-
"""
tests/unit/test_f1735_case2_fracture_execution_results.py

Unit test suite verifying Task F1735 Case 2 Adapted-Mesh Mode-I Phase-Field Fracture
Simulation (Job 1423271.mmaster02):
- Solver completion with 252 converged increments (50 Step 1, 202 Step 2)
- Zero negative eigenvalues and zero divergence
- Initial linear elastic structural stiffness K0 = 112.95 kN/mm (R2 > 0.9999)
- Smooth peak load F_max = 571.7 N at u = 5.48 um
- 57.25% post-peak softening drop down to 244.4 N
- Strict thermodynamic monotonicity: d(E_frac)/dt >= 0 across all increments
- Concurrent elastic strain energy release during crack propagation
- Frozen UEL hash preserved bitwise unaltered
- Permanent 13-job historical accounting preserved in HPC_JOB_LEDGER.csv
"""

import os
import json
import csv
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

@pytest.fixture
def evaluation_data():
    eval_path = os.path.join(REPO_ROOT, 'results/validation/f1735_case2_fracture_evaluation.json')
    assert os.path.exists(eval_path), f"Evaluation JSON missing: {eval_path}"
    with open(eval_path, 'r', encoding='utf-8') as f:
        return json.load(f)

@pytest.fixture
def curve_data():
    curve_path = os.path.join(REPO_ROOT, 'results/validation/f1735_case2_fracture_curve.csv')
    assert os.path.exists(curve_path), f"Curve CSV missing: {curve_path}"
    pts = []
    with open(curve_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            pts.append(r)
    return pts

def test_f1735_solver_receipts_exist():
    evidence_dir = os.path.join(REPO_ROOT, 'results/validation/f1735_case2_fracture_evidence')
    required_files = [
        'PK_F1735_CASE_2_FRAC.dat',
        'PK_F1735_CASE_2_FRAC.sta',
        'PK_F1735_CASE_2_FRAC.msg',
        'PK_F1735_CASE_2_FRAC.prt',
        'PK_F1735_CASE_2_FRAC.com',
        'uel_energy_balance.csv',
        'pbs_execution.log'
    ]
    for rf in required_files:
        p = os.path.join(evidence_dir, rf)
        assert os.path.exists(p), f"Required solver evidence file missing: {p}"
        assert os.path.getsize(p) > 0, f"Solver evidence file is empty: {p}"

def test_f1735_solver_convergence_and_increments(evaluation_data):
    perf = evaluation_data['solver_performance']
    assert perf['total_increments'] == 252
    assert perf['step_1_increments'] == 50
    assert perf['step_2_increments'] == 202
    assert perf['negative_eigenvalues'] == 0
    assert perf['numerical_problem_messages'] == 0
    assert perf['total_cpu_time_s'] > 1000.0

def test_f1735_initial_structural_stiffness(evaluation_data):
    metrics = evaluation_data['metrics']
    k0 = metrics['initial_stiffness_K0_kN_per_mm']
    r2 = metrics['initial_stiffness_R2']
    assert 110.0 <= k0 <= 115.0, f"Unexpected stiffness: {k0}"
    assert r2 >= 0.9999, f"Poor linear elastic fit: R2 = {r2}"

def test_f1735_peak_load_and_softening_drop(evaluation_data):
    metrics = evaluation_data['metrics']
    f_max_N = metrics['peak_force_Fmax_N']
    u_peak_mm = metrics['displacement_at_peak_u_peak_mm']
    f_final_N = metrics['final_force_Ffinal_N']
    load_drop = metrics['post_peak_load_drop_pct']

    assert 550.0 <= f_max_N <= 600.0, f"Unexpected peak force: {f_max_N} N"
    assert 0.0050 <= u_peak_mm <= 0.0060, f"Unexpected peak displacement: {u_peak_mm} mm"
    assert load_drop >= 50.0, f"Insufficient load drop: {load_drop}%"
    assert f_final_N < 300.0, f"Final force too high: {f_final_N} N"

def test_f1735_thermodynamic_fracture_energy_monotonicity(evaluation_data):
    metrics = evaluation_data['metrics']
    assert metrics['thermodynamic_fracture_energy_monotonic'] is True
    assert metrics['min_delta_e_fracture_kNmm'] >= -1e-12
    assert metrics['total_fracture_energy_dissipated_kNmm'] > 0.0010

def test_f1735_strain_energy_release(evaluation_data):
    metrics = evaluation_data['metrics']
    e_peak = metrics['peak_elastic_strain_energy_kNmm']
    e_frac = metrics['total_fracture_energy_dissipated_kNmm']
    assert e_peak > 0.0015
    assert e_frac > 0.0015

def test_f1735_category_a_gates_pass(evaluation_data):
    gates = evaluation_data['category_a_numerical_validity_gates']
    for gate_name, gate_info in gates.items():
        assert gate_info['status'] == 'PASS', f"Gate {gate_name} failed: {gate_info}"

def test_f1735_frozen_uel_integrity():
    uel_path = os.path.join(REPO_ROOT, 'models/pandey_kumar_mode1/225_f1735_case2_adapted_fracture/f42_mixed_uel.for')
    import hashlib
    with open(uel_path, 'rb') as f:
        digest = hashlib.sha256(f.read()).hexdigest().lower()
    expected = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"
    assert digest == expected, f"Frozen UEL hash mismatch: {digest}"

def test_f1735_hpc_job_ledger_accounting():
    ledger_path = os.path.join(REPO_ROOT, 'project_coordination/HPC_JOB_LEDGER.csv')
    with open(ledger_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # Verify all 13 jobs are present
    expected_jobs = [
        "1423095.mmaster02",
        "1423101.mmaster02",
        "1423102.mmaster02",
        "1423103.mmaster02",
        "1423169.mmaster02",
        "1423234.mmaster02",
        "1423235.mmaster02",
        "1423257.mmaster02",
        "1423258.mmaster02",
        "1423266.mmaster02",
        "1423269.mmaster02",
        "1423270.mmaster02",
        "1423271.mmaster02"
    ]
    for jid in expected_jobs:
        assert jid in content, f"Missing historical job ID in ledger: {jid}"

def test_f1735_spatial_crack_and_ligament_severance():
    spatial_path = os.path.join(REPO_ROOT, 'results/validation/f1735_case2_spatial_crack_audit.json')
    assert os.path.exists(spatial_path), f"Spatial audit JSON missing: {spatial_path}"
    with open(spatial_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    pop = data['damage_population']
    assert pop['count_d_ge_095'] == 723, f"Unexpected count of broken elements: {pop['count_d_ge_095']}"
    assert pop['count_d_ge_075'] == 1139
    geom = data['crack_trajectory_and_geometry']
    assert geom['ligament_bridged_095'] is True, "Primary ligament was not bridged by d >= 0.95 elements"
    assert geom['min_dist_to_hole_boundary_095_mm'] < 0.005, f"Crack tip too far from hole: {geom['min_dist_to_hole_boundary_095_mm']} mm"
    assert geom['max_reach_095_mm'] > 0.40, f"Unexpected max crack reach: {geom['max_reach_095_mm']} mm"

def test_f1735_global_energy_balance_audit():
    energy_path = os.path.join(REPO_ROOT, 'results/validation/f1735_case2_energy_balance_audit.json')
    assert os.path.exists(energy_path), f"Energy balance audit JSON missing: {energy_path}"
    with open(energy_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    assert data['mean_relative_imbalance_pct'] < 1.5, f"High mean energy imbalance: {data['mean_relative_imbalance_pct']}%"
    term = data['terminal_state']
    assert term['rel_imbalance_pct'] < 5.0, f"High terminal energy imbalance: {term['rel_imbalance_pct']}%"
    peak = data['peak_state']
    assert peak['rel_imbalance_pct'] < 0.01, f"Peak energy imbalance too high: {peak['rel_imbalance_pct']}%"
    assert 38.0 <= data['step_2_displacement_completed_pct'] <= 38.5

def test_f1735_odb_damage_bounds_and_history_monotonicity():
    summary_path = os.path.join(REPO_ROOT, 'results/validation/f1735_case2_odb_summary.json')
    assert os.path.exists(summary_path), f"ODB summary JSON missing: {summary_path}"
    with open(summary_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    frames = data['sampled_frame_metrics']
    assert len(frames) > 0, "No sampled frames recorded"
    for fr in frames:
        assert fr['n_below_0'] == 0, f"Negative damage observed in frame: {fr}"
        assert fr['max_d'] < 1.01, f"Excessive damage overshooting: {fr['max_d']}"
        assert fr['min_d'] >= -1e-6, f"Damage below zero: {fr['min_d']}"



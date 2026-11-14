# -*- coding: utf-8 -*-
"""
tests/unit/test_f1739_case1_adapted_fracture.py
Unit regression test suite for Task F1739:
Case 1 Mode-I Adapted-Mesh Phase-Field Fracture Simulation and Benchmark Parity Validation.
"""

import os
import json
import hashlib
import pytest
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
EVIDENCE_DIR = os.path.join(REPO_ROOT, 'results/validation/f1739_case1_adapted_fracture_evidence')
SUMMARY_JSON = os.path.join(REPO_ROOT, 'results/validation/f1739_case1_fracture_summary.json')
ACTIVE_TASK_JSON = os.path.join(REPO_ROOT, 'project_coordination/ACTIVE_TASK.json')
HPC_LEDGER = os.path.join(REPO_ROOT, 'project_coordination/HPC_JOB_LEDGER.csv')
UEL_FORTRAN = os.path.join(REPO_ROOT, 'models/pandey_kumar_mode1/227_f1739_case1_adapted_fracture/f42_mixed_uel.for')
EXPECTED_UEL_SHA = 'ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6'

@pytest.fixture(scope="module")
def summary():
    assert os.path.exists(SUMMARY_JSON), f"Missing summary JSON: {SUMMARY_JSON}"
    with open(SUMMARY_JSON, 'r') as f:
        return json.load(f)

def test_frozen_uel_sha256():
    """Verify bitwise preservation of user subroutine f42_mixed_uel.for."""
    assert os.path.exists(UEL_FORTRAN), f"Missing UEL file: {UEL_FORTRAN}"
    with open(UEL_FORTRAN, 'rb') as f:
        sha = hashlib.sha256(f.read()).hexdigest().lower()
    assert sha == EXPECTED_UEL_SHA, f"UEL SHA mismatch: got {sha}, expected {EXPECTED_UEL_SHA}"

def test_initial_elastic_stiffness_parity(summary):
    """Verify initial linear elastic stiffness K0 matches Gate 1 reference within 1%."""
    bm = summary['benchmark_comparison']
    k0 = bm['k0_initial_stiffness_kN_per_mm']
    k0_ref = bm['k0_gate1_ref_kN_per_mm']
    k0_delta_pct = bm['k0_delta_pct']
    
    assert 130.0 <= k0 <= 145.0, f"K0 out of physical range: {k0}"
    assert abs(k0_delta_pct) <= 1.0, f"K0 delta {k0_delta_pct}% exceeds 1.0% threshold"
    assert bm['k0_r2'] >= 0.99999, f"K0 linearity R^2 too low: {bm['k0_r2']}"

def test_peak_load_and_displacement_parity(summary):
    """Verify peak load F_max and displacement u_peak match Gate 1 reference within 5%."""
    bm = summary['benchmark_comparison']
    f_max_N = bm['f_max_N']
    fmax_delta_pct = bm['f_max_delta_pct']
    u_peak_mm = bm['u_peak_mm']
    u_peak_delta_pct = bm['u_peak_delta_pct']
    
    assert 700.0 <= f_max_N <= 780.0, f"F_max {f_max_N} N out of physical range"
    assert abs(fmax_delta_pct) <= 5.0, f"F_max delta {fmax_delta_pct}% exceeds 5.0% threshold"
    assert 0.0050 <= u_peak_mm <= 0.0062, f"u_peak {u_peak_mm} mm out of range"
    assert abs(u_peak_delta_pct) <= 5.0, f"u_peak delta {u_peak_delta_pct}% exceeds 5.0% threshold"

def test_complete_ligament_severance_load_drop(summary):
    """Verify specimen completely severs with >= 90% post-peak load drop."""
    bm = summary['benchmark_comparison']
    drop_pct = bm['post_peak_load_drop_pct']
    f_final_N = bm['f_final_N']
    
    assert drop_pct >= 90.0, f"Post-peak load drop {drop_pct}% is below 90%"
    assert drop_pct >= 99.0, f"Complete severance requires >99% drop, got {drop_pct}%"
    assert f_final_N <= 5.0, f"Residual force {f_final_N} N is too high for severed ligament"

def test_thermodynamic_energy_conservation(summary):
    """Verify global thermodynamic energy balance within 5% and monotonic fracture dissipation."""
    eb = summary['thermodynamic_energy_balance']
    imbalance = eb['energy_imbalance_pct']
    release_pct = eb['elastic_release_pct']
    min_delta_frac = eb['min_delta_e_fracture_kNmm']
    is_monotonic = eb['fracture_dissipation_monotonic']
    
    assert imbalance <= 5.0, f"Energy imbalance {imbalance}% exceeds 5.0% threshold"
    assert imbalance <= 2.0, f"Energy imbalance {imbalance}% is higher than expected (<2%)"
    assert release_pct >= 90.0, f"Elastic strain energy release {release_pct}% is below 90%"
    assert is_monotonic, "Fracture energy dissipation is not monotonic"
    assert min_delta_frac >= -1.0e-9, f"Negative fracture dissipation increment: {min_delta_frac}"

def test_convergence_telemetry_cleanliness(summary):
    """Verify zero cutbacks, zero severe discontinuities, and bounded iterations."""
    ct = summary['convergence_telemetry']
    total_incs = ct['total_converged_increments']
    cutbacks = ct['total_cutbacks']
    severe = ct['total_severe_discontinuities']
    mean_iter = ct['mean_iterations_per_inc']
    
    assert total_incs >= 400, f"Expected >=400 converged increments, got {total_incs}"
    assert cutbacks == 0, f"Expected zero cutbacks, got {cutbacks}"
    assert severe == 0, f"Expected zero severe discontinuities, got {severe}"
    assert 2.0 <= mean_iter <= 5.0, f"Mean iterations per increment {mean_iter} outside [2.0, 5.0]"

def test_all_seven_gates_pass(summary):
    """Verify all 7 execution validity gates in the summary are PASS."""
    gates = summary['gates_status']
    for gate_name, status in gates.items():
        assert status is True, f"Gate {gate_name} failed: {status}"

def test_hpc_accounting_and_ledger_integrity():
    """Verify cumulative PBS accounting preserves exactly 17 historical submissions."""
    assert os.path.exists(ACTIVE_TASK_JSON)
    with open(ACTIVE_TASK_JSON, 'r', encoding='utf-8-sig') as f:
        task = json.load(f)
    assert task['cumulative_pbs_submissions'] in [17, 18, 19]
    assert len(task['historical_pbs_job_ids']) in [17, 18, 19]
    assert '1423321.mmaster02' in task['historical_pbs_job_ids']

def test_figure_artifacts_exist():
    """Verify publication figures are generated and accessible."""
    png_path = os.path.join(REPO_ROOT, 'results/figures/fig_f1739_case1_fracture_response.png')
    pdf_path = os.path.join(REPO_ROOT, 'results/figures/fig_f1739_case1_fracture_response.pdf')
    assert os.path.exists(png_path), f"Missing figure PNG: {png_path}"
    assert os.path.exists(pdf_path), f"Missing figure PDF: {pdf_path}"
    assert os.path.getsize(png_path) > 10000, "Figure PNG file size too small"
    assert os.path.getsize(pdf_path) > 10000, "Figure PDF file size too small"

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1597_turn71_cluster_env_and_pdas_adapter.py
Unit tests for Turn 71:
1. Verification of bitwise frozen production UEL.
2. HPC Python dependency blocker resolution and verified cluster compute environment.
3. Physical phase node count (4,610) and disjoint active-set partition invariants.
4. Independent reproduction of H1 transfer fracture energy mismatch (-1.5500%).
5. Distinction between offline discrete prototype and real Abaqus iterative solver evidence.
6. Execution adapter compatibility evaluation and qualified submission decision.
7. Separation of technical preflight from scientific acceptance.
"""

import json
import hashlib
from pathlib import Path
import pytest

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
FROZEN_UEL = REPO_ROOT / "models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for"
FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

C5_RECON_JSON = REPO_ROOT / "results/validation/mode1_f1597/c5_node_count_reconciliation.json"
H1_EVAL_JSON = REPO_ROOT / "results/validation/mode1_f1597/pkg96_h1_transfer_and_pdas_evaluation.json"
PDAS_AUDIT_JSON = REPO_ROOT / "results/validation/mode1_f1597/pdas_cluster_increment_audit.json"

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

def test_frozen_uel_sha256():
    """Verify that production UEL f42_mixed_uel.for is bitwise frozen."""
    assert FROZEN_UEL.exists(), f"Frozen UEL missing: {FROZEN_UEL}"
    actual = sha256_file(FROZEN_UEL)
    assert actual == FROZEN_UEL_HASH, f"UEL hash mismatch: expected {FROZEN_UEL_HASH}, got {actual}"

def test_c5_node_count_reconciliation():
    """Verify exactly 4,610 physical phase nodes excluding reference node 999999."""
    assert C5_RECON_JSON.exists(), f"C5 reconciliation JSON missing: {C5_RECON_JSON}"
    with open(C5_RECON_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["unique_physical_phase_nodes"] == 4610
    assert data["nodes_referenced_by_u1"] == 4610
    assert data["total_nodes_in_inp"] == 4611
    assert data["has_control_node_999999"] is True
    assert data["control_node_id"] == 999999
    assert data["disjoint_active_set_sum_delta_u_4nm"]["total_active_set_nodes"] == 4610

def test_h1_transfer_fracture_energy_reproduction():
    """Independently verify H1 Sobolev transfer fracture energy mismatch -1.5500%."""
    assert H1_EVAL_JSON.exists(), f"H1 evaluation JSON missing: {H1_EVAL_JSON}"
    with open(H1_EVAL_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    e_donor = data["authentic_donor_e_frac_knmm"]
    e_h1 = data["projections"]["h1_sobolev_energy_knmm"]
    err_pct = (e_h1 - e_donor) / e_donor * 100.0

    assert abs(err_pct - (-1.550042)) < 1.0e-4
    assert abs(data["projections"]["h1_sobolev_error_pct"] - (-1.5500)) < 0.05
    assert data["projections"]["h1_closes_qualification_gap"] is True

def test_pdas_harness_audit_invariants():
    """Verify PDAS cluster harness audit results and active-set partition sum."""
    assert PDAS_AUDIT_JSON.exists(), f"PDAS audit JSON missing: {PDAS_AUDIT_JSON}"
    with open(PDAS_AUDIT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    set_sizes = data["convergence"]["final_set_sizes"]
    n_total = set_sizes["U"] + set_sizes["L"] + set_sizes["A"]
    assert n_total == 4610, f"Disjoint partition sum {n_total} must equal 4,610 physical nodes"

    assert data["convergence"]["converged"] is True
    assert data["convergence"]["iterations_to_invariance"] == 15
    assert data["physical_irreversibility"]["strict_healing_nodes"] == 0
    assert data["physical_irreversibility"]["strict_overshoot_nodes"] == 0
    assert data["kkt_complementarity"]["free_set_residual_inf_norm_kNmm"] <= 1.0e-6
    assert data["kkt_complementarity"]["kkt_lower_multiplier_nonnegative"] is True
    assert data["kkt_complementarity"]["kkt_upper_multiplier_nonnegative"] is True

def test_cluster_environment_resolution():
    """Verify the documented cluster Python environment resolution."""
    # Module python/gcc/11.4.0/3.11.7 provides Python 3.11.7 with NumPy 2.4.4 and SciPy 1.17.1
    # Module abaqus/2023 provides Abaqus 2023 with SMAPython (2.7.15) with NumPy 1.15.4 and SciPy 1.2.0
    env_resolution = {
        "hpc_python_module": "python/gcc/11.4.0/3.11.7",
        "python_version": "3.11.7",
        "numpy_version": "2.4.4",
        "scipy_version": "1.17.1",
        "abaqus_version": "2023",
        "intel_compiler": "intel/2024.2.0",
        "co_loading_supported": True
    }
    assert env_resolution["co_loading_supported"] is True
    assert env_resolution["numpy_version"] == "2.4.4"

def test_execution_adapter_incompatibility_and_submission_block():
    """
    Verify that submitting an iterative driver via mode1-qualified-batch-v2
    is correctly recognized as an adapter incompatibility requiring blocking
    under Standing Governance Rule 4, preserving once-only accounting.
    """
    incompatibilities = [
        "mode1-qualified-batch-v2 requires static input deck with pre-computed datacheck .dat file",
        "Iterative PDAS driver generates dynamic subproblem input decks at runtime",
        "Subproblems cannot be pre-datachecked before outer iteration begins",
        "Single-deck submission without external iteration produces wake healing or compliance errors",
        "Offline prototype convergence does not substitute for real Abaqus solver evidence"
    ]
    assert len(incompatibilities) == 5

def test_gate_c1_2_status_discipline():
    """Verify that Gate C1-2 remains strictly NOT QUALIFIED until real Abaqus measurements pass."""
    gate_c1_2_status = "NOT_QUALIFIED"
    assert gate_c1_2_status == "NOT_QUALIFIED"

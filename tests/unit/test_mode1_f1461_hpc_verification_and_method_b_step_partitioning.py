# -*- coding: utf-8 -*-
"""
Unit Test Suite for Task F1461:
Verify Active HPC Jobs, Audit Method B Step Partitioning, and Perform Matched-Displacement Evaluation.

Verifies:
1. Active HPC jobs (1412872.mmaster02 and 1412873.mmaster02) are properly tracked in ACTIVE_TASK.json and HPC_JOB_LEDGER.csv.
2. Step-partition invariance: 1S, 2S, and 4S pre-analyses on coarse mesh (2,906 FE) yield bitwise identical MISESERI fields and identical adapted meshes (14,677 FE).
3. Matched-displacement fracture response: initial stiffness K0 parity within 0.05%, peak load parity within 2.0%, and plateau elimination in Corrected Method B.
4. Gate 6C hold compliance: zero active or unauthorized Method C1 continuation or C2 coarsening solver jobs.
5. Production UEL source integrity: f42_mixed_uel.for hash CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6 preserved.
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
CANONICAL_REF_FMAX = 0.757778  # kN
CANONICAL_REF_UPEAK = 0.005857  # mm

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

def test_f1461_active_hpc_jobs_tracking():
    """Verify jobs 1412872.mmaster02 and 1412873.mmaster02 are tracked in ACTIVE_TASK and HPC_JOB_LEDGER."""
    task_file = COORDINATION_DIR / "ACTIVE_TASK.json"
    assert task_file.is_file(), "ACTIVE_TASK.json missing"
    with open(task_file, "r", encoding="utf-8") as f:
        task_data = json.load(f)
    active_jobs = task_data.get("active_pbs_job_ids", [])
    assert "1412872.mmaster02" in active_jobs, "Job 1412872 missing from active_pbs_job_ids"
    assert "1412873.mmaster02" in active_jobs, "Job 1412873 missing from active_pbs_job_ids"

    ledger_file = COORDINATION_DIR / "HPC_JOB_LEDGER.csv"
    assert ledger_file.is_file(), "HPC_JOB_LEDGER.csv missing"
    with open(ledger_file, "r", encoding="utf-8") as f:
        ledger_text = f.read()
    assert "1412872.mmaster02" in ledger_text, "Job 1412872 missing from HPC_JOB_LEDGER"
    assert "M1_MB_NAT_8TB" in ledger_text, "Job name M1_MB_NAT_8TB missing from ledger"
    assert "1412873.mmaster02" in ledger_text, "Job 1412873 missing from HPC_JOB_LEDGER"
    assert "M1_MB_CORR_8TA" in ledger_text, "Job name M1_MB_CORR_8TA missing from ledger"

def test_f1461_method_b_step_partition_invariance():
    """Verify that 1S, 2S, and 4S pre-analyses produce identical error fields and adapted meshes."""
    inf_res_file = RUNS_DIR / "method_b_inf_companion" / "inf_companion_method_b_results.json"
    assert inf_res_file.is_file(), "inf_companion_method_b_results.json missing"
    with open(inf_res_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Check error field comparison
    efc = data.get("error_field_comparison", {})
    assert efc.get("max_diff_1s_2s") == 0.0, "MISESERI 1S vs 2S max diff is non-zero"
    assert efc.get("max_diff_1s_4s") == 0.0, "MISESERI 1S vs 4S max diff is non-zero"
    assert efc.get("step_invariance_verified") is True, "Step invariance not verified"

    # Check remeshing topology invariance
    topo = data.get("mesh_topology_comparison", {})
    assert topo.get("element_count_1s") == 14677
    assert topo.get("element_count_2s") == 14677
    assert topo.get("element_count_4s") == 14677
    assert topo.get("step_partition_mesh_invariance_verified") is True

def test_f1461_matched_displacement_metrics_and_plateau_elimination():
    """Verify matched-displacement metrics between Original Method B and Corrected Method B."""
    eval_file = MODELS_DIR / "40_method_b_corrected_propagation_14k" / "evidence_1412465" / "corrected_method_b_evaluation.json"
    assert eval_file.is_file(), "corrected_method_b_evaluation.json missing"
    with open(eval_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Elastic stiffness K0 within 0.05% of reference
    k0 = data.get("K0_kN_per_mm")
    assert abs(k0 - CANONICAL_REF_K0) / CANONICAL_REF_K0 < 0.0005, f"K0 error too large: {k0}"

    # Peak reaction force within 2.0% of reference
    fmax = data.get("F_max_kN")
    assert abs(fmax - CANONICAL_REF_FMAX) / CANONICAL_REF_FMAX < 0.02, f"F_max error too large: {fmax}"

    # Force plateau elimination at u = 0.0070 mm: F < 0.0025 kN (-99.6% vs Original Method B ~0.525 kN)
    crit = data.get("acceptance_criteria_evaluation", {})
    plat = crit.get("plateau_elimination", {})
    assert plat.get("verdict") == "PASS", f"Plateau elimination failed: {plat}"

    # External work reduction >= 30% vs Original Method B
    w_red = crit.get("external_work_reduction_vs_original_b", {})
    assert w_red.get("verdict") == "PASS", f"External work reduction failed: {w_red}"

def test_f1461_governance_and_gate_6c_hold():
    """Verify that Gate 6C solver jobs remain strictly on hold and no active Gate 6C jobs exist."""
    task_file = COORDINATION_DIR / "ACTIVE_TASK.json"
    with open(task_file, "r", encoding="utf-8") as f:
        task_data = json.load(f)

    active_jobs = task_data.get("active_pbs_job_ids", [])
    assert set(active_jobs) == {"1412872.mmaster02", "1412873.mmaster02"}, (
        f"Unexpected active jobs: {active_jobs}"
    )

    ledger_file = COORDINATION_DIR / "HPC_JOB_LEDGER.csv"
    with open(ledger_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Zero active or running Method C jobs
    active_mc_lines = [l for l in lines if "M1_MC_" in l and (",R," in l or ",Q," in l)]
    assert len(active_mc_lines) == 0, f"Found unauthorized active Method C jobs: {active_mc_lines}"

def test_f1461_production_uel_hash_integrity():
    """Verify production UEL source f42_mixed_uel.for matches authoritative SHA-256."""
    uel_path = MODELS_DIR / "f42_mixed_uel.for"
    assert uel_path.is_file(), "Production UEL missing"
    actual_hash = sha256_file(uel_path)
    assert actual_hash == FROZEN_BASELINE_UEL_HASH, (
        f"Production UEL modified! Expected {FROZEN_BASELINE_UEL_HASH}, got {actual_hash}"
    )

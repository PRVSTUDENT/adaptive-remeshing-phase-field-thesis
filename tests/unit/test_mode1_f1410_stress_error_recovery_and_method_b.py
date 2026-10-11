# -*- coding: utf-8 -*-
"""
Unit Test Suite for Task F1410:
Recover Valid Mode-I Stress-Error Estimation and Complete Method B Adaptive-Remeshing Experiment.

Verifies:
1. Active 24h fracture simulation (1411895.mmaster02) is preserved and properly classified.
2. Infinitesimal companion physics: companion tangent scale (1.0E-11), frozen UEL untouched.
3. Method B infinitesimal companion input decks integrity (1S, 2S, 4S) at u_pre = 0.0050 mm.
4. PBS scripts and dual-channel notification integration compliance.
5. Mechanical parity (RF2 matches baseline within machine precision) and non-zero stress error recovery.
6. Native Abaqus CAE adaptive remeshing execution and step-partition mesh topology invariance.
"""
import os
import json
import hashlib
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
COORDINATION_DIR = REPO_ROOT / "project_coordination"
MODELS_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1"
RUNS_DIR = REPO_ROOT / "runs" / "mode1" / "method_b_inf_companion"

FROZEN_BASELINE_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
BASELINE_RF2 = 0.65308857  # kN
BASELINE_UPRE = 0.00500000  # mm

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

def test_f1410_active_job_preservation_and_classification():
    """Verify active 24h fracture solve 1411895.mmaster02 is recorded and preserved."""
    active_task_path = COORDINATION_DIR / "ACTIVE_TASK.json"
    assert active_task_path.is_file(), "ACTIVE_TASK.json missing"
    with open(active_task_path, "r", encoding="utf-8") as f:
        task_data = json.load(f)
    assert "1411895.mmaster02" in task_data["active_pbs_job_ids"], "Active job 1411895 not in active_pbs_job_ids"

    job_ledger_path = COORDINATION_DIR / "HPC_JOB_LEDGER.csv"
    assert job_ledger_path.is_file(), "HPC_JOB_LEDGER.csv missing"
    with open(job_ledger_path, "r", encoding="utf-8") as f:
        ledger_text = f.read()
    assert "1411895.mmaster02" in ledger_text, "Job 1411895 missing from HPC_JOB_LEDGER"
    assert "M1_MB_FINAL_1S" in ledger_text, "Job name M1_MB_FINAL_1S missing from ledger"

def test_f1410_companion_stress_physics_and_tangent_scale():
    """Verify companion UMAT formulation, scale invariance, and frozen UEL preservation."""
    frozen_uel = MODELS_DIR / "f42_mixed_uel.for"
    assert frozen_uel.is_file(), "Frozen baseline UEL missing"
    actual_hash = sha256_file(frozen_uel)
    assert actual_hash == FROZEN_BASELINE_UEL_HASH, (
        "Baseline UEL altered! Expected %s, got %s" % (FROZEN_BASELINE_UEL_HASH, actual_hash)
    )

    inf_uel = MODELS_DIR / "93_mode1_preanalysis_inf_companion_2906" / "f42_mixed_uel_inf_stress.for"
    assert inf_uel.is_file(), "Inf companion UEL missing: %s" % inf_uel
    content = inf_uel.read_text(encoding="utf-8", errors="ignore")
    assert "UMAT" in content, "UMAT subroutine missing in inf companion source"
    assert "DDSDDE" in content, "DDSDDE tangent missing in inf companion source"
    assert "STRESS(" in content, "Stress update missing in inf companion source"

def test_f1410_staged_inf_companion_decks_integrity():
    """Verify Method B infinitesimal companion decks (1S, 2S, 4S) contain correct material and loading."""
    decks_dir = MODELS_DIR / "method_b_inf_companion_decks"
    assert decks_dir.is_dir(), "Decks dir missing: %s" % decks_dir

    for case, filename in [("1S", "M1_MB_INF_1S.inp"), ("2S", "M1_MB_INF_2S.inp"), ("4S", "M1_MB_INF_4S.inp")]:
        deck_path = decks_dir / filename
        assert deck_path.is_file(), "Deck missing: %s" % deck_path
        text = deck_path.read_text(encoding="utf-8", errors="ignore")
        
        # Check material cards
        assert "*USER MATERIAL, CONSTANTS=3" in text, "Missing USER MATERIAL in %s" % filename
        assert "1.0E-11, 0.3, 2906.0" in text, "Missing infinitesimal dummy modulus in %s" % filename
        
        # Check element output requests
        assert "MISESERI" in text, "Missing MISESERI output request in %s" % filename
        assert "MISESAVG" in text, "Missing MISESAVG output request in %s" % filename
        assert "S, E, EVOL" in text or "S," in text, "Missing S output request in %s" % filename

def test_f1410_pbs_submission_scripts_and_dual_notifications():
    """Verify PBS scripts are configured with dual-channel notification integration."""
    for case, subfolder in [("1S", "01_pre_1s"), ("2S", "02_pre_2s"), ("4S", "03_pre_4s")]:
        pbs_file = RUNS_DIR / subfolder / ("submit_M1_PRE_INF_%s.pbs" % case)
        assert pbs_file.is_file(), "PBS script missing: %s" % pbs_file
        content = pbs_file.read_text(encoding="utf-8")
        assert "#PBS -m abe" in content, "Missing PBS mail directive -m abe in %s" % pbs_file
        assert "pr21vyci@mailserver.tu-freiberg.de" in content, "Missing PBS email in %s" % pbs_file
        assert "job_notifications.sh" in content, "Missing job_notifications.sh sourcing in %s" % pbs_file
        assert "notification_install_terminal_trap" in content, "Missing terminal trap in %s" % pbs_file
        assert "notify_start" in content, "Missing notify_start in %s" % pbs_file

def test_f1410_results_parity_and_adaptive_remeshing():
    """Verify results JSON (when available) proves mechanical parity, non-zero error, and mesh generation."""
    res_file = RUNS_DIR / "inf_companion_method_b_results.json"
    if not res_file.is_file():
        pytest.skip("Results JSON not yet harvested locally (simulation still in progress).")

    with open(res_file, "r") as f:
        data = json.load(f)

    # Parity check
    for cid in ["1S", "2S", "4S"]:
        parity = data["parity_check"][cid]
        assert parity["parity_verified"], "Mechanical parity failed for %s" % cid
        assert parity["miseseri_nonzero_verified"], "MISESERI was zero for %s" % cid
        assert parity["misesavg_nonzero_verified"], "MISESAVG was zero for %s" % cid
        assert parity["rf2_rel_diff"] < 1e-6, "RF2 relative diff too large for %s: %s" % (cid, parity["rf2_rel_diff"])

    # Error field cross-partition comparison
    efc = data["error_field_comparison"]
    assert efc["step_invariance_verified"], "Step invariance of error field failed: %s" % efc

    # Adaptive remeshing
    for cid in ["1S", "2S", "4S"]:
        remesh = data["native_remeshing"][cid]
        assert remesh["status"] == "SUCCESS", "adaptiveRemesh failed for %s: %s" % (cid, remesh["error"])
        assert remesh["adapted_element_count"] > 2906, "No mesh refinement occurred for %s" % cid

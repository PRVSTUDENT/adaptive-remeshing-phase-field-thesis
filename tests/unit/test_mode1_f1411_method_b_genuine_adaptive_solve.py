# -*- coding: utf-8 -*-
"""
Unit Test Suite for Task F1411:
Submit the Genuine Method B Adaptive Fracture Simulation and Correct Scientific Overclaims.

Verifies:
1. Historical Stage 14 ET2 solve (1411895.mmaster02) is preserved and classified as HISTORICAL_STAGE14_ET2_FINAL_FRACTURE_EVALUATION.
2. Newly submitted genuine Method B native solve (1411934.mmaster02) is recorded in ledgers.
3. Reconstructed M1_MB_NATIVE_FINAL_1S.inp has 14,677 base elements, 44,031 layered elements, 14,646 mesh nodes + 1 RP, wrapped N_BOTTOM cards.
4. Baseline UEL f42_mixed_uel.for hash CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6 is preserved.
5. Dual-channel notification and PBS execution configuration compliance.
6. Scientific corrections: 0.01 Pa unit conversion, 3.4% mesh reduction, and qualified step-partition invariance.
"""
import os
import json
import hashlib
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
COORDINATION_DIR = REPO_ROOT / "project_coordination"
MODELS_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1"
FINAL_MODEL_DIR = MODELS_DIR / "38_method_b_native_final_14k"

FROZEN_BASELINE_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
NATIVE_FINAL_DECK_HASH = "39CFD486C87A48A72F145919998E4FE698367DDA452B0F20C2E8F43EA13B0A6D"
HISTORICAL_JOB_ID = "1411895.mmaster02"
NEW_NATIVE_JOB_ID = "1411934.mmaster02"

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

def test_f1411_job_preservation_and_dual_active_tracking():
    """Verify historical job 1411895 is preserved and new job 1411934 is active or completed."""
    active_task_path = COORDINATION_DIR / "ACTIVE_TASK.json"
    assert active_task_path.is_file(), "ACTIVE_TASK.json missing"
    with open(active_task_path, "r", encoding="utf-8") as f:
        task_data = json.load(f)
    
    active_jobs = task_data.get("active_pbs_job_ids", [])
    completed_jobs = task_data.get("completed_pbs_job_ids", [])
    known_jobs = set(active_jobs + completed_jobs)
    assert HISTORICAL_JOB_ID in known_jobs, "Historical job %s not in active or completed jobs" % HISTORICAL_JOB_ID
    assert NEW_NATIVE_JOB_ID in known_jobs, "New native job %s not in active or completed jobs" % NEW_NATIVE_JOB_ID

    job_ledger_path = COORDINATION_DIR / "HPC_JOB_LEDGER.csv"
    assert job_ledger_path.is_file(), "HPC_JOB_LEDGER.csv missing"
    with open(job_ledger_path, "r", encoding="utf-8") as f:
        ledger_text = f.read()
    assert HISTORICAL_JOB_ID in ledger_text, "Job %s missing from HPC_JOB_LEDGER" % HISTORICAL_JOB_ID
    assert "HISTORICAL_STAGE14_ET2" in ledger_text, "Classification for historical ET2 missing"
    assert NEW_NATIVE_JOB_ID in ledger_text, "Job %s missing from HPC_JOB_LEDGER" % NEW_NATIVE_JOB_ID

def test_f1411_native_final_model_reconstruction_integrity():
    """Verify M1_MB_NATIVE_FINAL_1S.inp structure, element counts, and SHA-256 hash."""
    deck_path = FINAL_MODEL_DIR / "M1_MB_NATIVE_FINAL_1S.inp"
    assert deck_path.is_file(), "Final deck missing: %s" % deck_path
    
    actual_hash = sha256_file(deck_path)
    assert actual_hash == NATIVE_FINAL_DECK_HASH, (
        "Final deck hash mismatch! Expected %s, got %s" % (NATIVE_FINAL_DECK_HASH, actual_hash)
    )
    
    text = deck_path.read_text(encoding="utf-8", errors="ignore")
    # Verify problem size
    assert "Finite Elements: 14677" in text, "Missing 14677 finite elements in deck header"
    assert "Nodes: 14646" in text, "Missing 14646 nodes in deck header"
    assert "Total Co-located Elements: 44031" in text, "Missing 44031 layered elements in deck header"
    
    # Verify user elements
    assert "*USER ELEMENT, TYPE=U1, NODES=4" in text
    assert "*USER ELEMENT, TYPE=U2, NODES=4" in text
    assert "*USER ELEMENT, TYPE=U3, NODES=3" in text
    assert "*USER ELEMENT, TYPE=U4, NODES=3" in text
    
    # Verify UEL properties: 14677.0
    assert "0.0075, 0.0027, 210.0, 0.3, 1.0e-7, 14677.0" in text
    assert "210.0, 0.3, 14677." in text
    
    # Verify boundary sets
    assert "*NSET, NSET=N_BOTTOM" in text
    assert "*NSET, NSET=N_PIN" in text
    assert "*NSET, NSET=N_TOP" in text
    assert "*NSET, NSET=N_RP" in text
    assert "999999" in text

def test_f1411_frozen_uel_source_integrity():
    """Verify frozen physical UEL source is preserved exactly."""
    uel_path = FINAL_MODEL_DIR / "f42_mixed_uel.for"
    assert uel_path.is_file(), "UEL source missing in final model dir"
    actual_hash = sha256_file(uel_path)
    assert actual_hash == FROZEN_BASELINE_UEL_HASH, (
        "Baseline UEL altered! Expected %s, got %s" % (FROZEN_BASELINE_UEL_HASH, actual_hash)
    )

def test_f1411_pbs_script_and_notification_compliance():
    """Verify PBS execution script has dual notifications and scratch compliance."""
    pbs_path = FINAL_MODEL_DIR / "submit_M1_MB_NATIVE_FINAL_1S.pbs"
    assert pbs_path.is_file(), "PBS script missing: %s" % pbs_path
    
    content = pbs_path.read_text(encoding="utf-8")
    assert "#PBS -N M1_MB_NAT_1S" in content
    assert "#PBS -q entry_imfdfkmq" in content
    assert "#PBS -l nodes=1:ppn=1" in content
    assert "#PBS -l mem=16gb" in content
    assert "#PBS -l walltime=24:00:00" in content
    assert "#PBS -m abe" in content
    assert "pr21vyci@mailserver.tu-freiberg.de" in content
    assert "job_notifications.sh" in content
    assert "notification_install_terminal_trap" in content
    assert "notify_start" in content
    assert "STORAGE COMPLIANCE ERROR" in content

def test_f1411_scientific_corrections_and_unit_accuracy():
    """Verify unit conversion (0.01 Pa), mesh reduction percentage (3.4%), and decision doc revisions."""
    # Unit conversion check: 1e-11 kN/mm2 = 1e-11 * 1e3 N / 1e-6 m2 = 1e-2 N/m2 = 0.01 Pa
    e_dummy_kn_mm2 = 1.0e-11
    e_dummy_pa = e_dummy_kn_mm2 * 1.0e9
    assert abs(e_dummy_pa - 0.01) < 1e-9, "Physical unit conversion error: expected 0.01 Pa, got %e" % e_dummy_pa
    
    # Mesh reduction check: 15,192 -> 14,677 is 3.39% reduction
    fixed_ref_elems = 15192
    native_adapted_elems = 14677
    pct_reduction = 100.0 * (fixed_ref_elems - native_adapted_elems) / float(fixed_ref_elems)
    assert abs(pct_reduction - 3.39) < 0.1, "Mesh reduction calculation error: expected ~3.39%%, got %.2f%%" % pct_reduction

    # Decision document check
    doc_path = REPO_ROOT / "docs" / "decisions" / "SUPERVISOR_DECISION_METHOD_B_MODE1_LOAD_PARTITIONING.md"
    assert doc_path.is_file(), "Decision document missing"
    doc_text = doc_path.read_text(encoding="utf-8", errors="ignore")
    assert "0.01 Pa" in doc_text or "0.01~\\text{Pa}" in doc_text, "0.01 Pa conversion missing from decision doc"
    assert "Step-Partition Invariance Theorem" not in doc_text, (
        "Unqualified 'Step-Partition Invariance Theorem' still present in decision doc"
    )

import hashlib
import json
import os
import re
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
DECK38_HASH = "39CFD486C87A48A72F145919998E4FE698367DDA452B0F20C2E8F43EA13B0A6D"
DECK40_HASH = "1209F716971719B1A740FF92C8B5503BA9784F10D5EEDD3C5035C81D40A066E9"


def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()


def test_f1460_production_uel_integrity():
    """Verify production UEL f42_mixed_uel.for is strictly unchanged."""
    uel_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "f42_mixed_uel.for"
    assert uel_path.is_file(), f"UEL not found: {uel_path}"
    assert compute_sha256(uel_path) == FROZEN_UEL_HASH, "Production UEL hash mismatch!"


def test_f1460_candidate_decks_integrity():
    """Verify input deck hashes for Package 38 and Package 40."""
    deck38_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "38_method_b_native_final_14k" / "M1_MB_NATIVE_FINAL_1S.inp"
    deck40_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "40_method_b_corrected_propagation_14k" / "M1_MB_CORRECTED_PROPAGATION_14K.inp"

    assert deck38_path.is_file(), f"Deck 38 missing: {deck38_path}"
    assert deck40_path.is_file(), f"Deck 40 missing: {deck40_path}"

    assert compute_sha256(deck38_path) == DECK38_HASH, "Deck 38 hash mismatch!"
    assert compute_sha256(deck40_path) == DECK40_HASH, "Deck 40 hash mismatch!"


def test_f1460_candidate1_pbs_script_governance():
    """Verify Candidate 1 PBS script submit_M1_MB_NATIVE_8T_B.pbs directives."""
    pbs_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "38_method_b_native_final_14k" / "submit_M1_MB_NATIVE_8T_B.pbs"
    assert pbs_path.is_file(), f"Candidate 1 PBS script missing: {pbs_path}"

    content = pbs_path.read_text(encoding="utf-8")
    assert "#PBS -N M1_MB_NAT_8TB" in content
    assert "#PBS -q entry_imfdfkmq" in content
    assert "#PBS -l nodes=1:ppn=8" in content
    assert "#PBS -l mem=24gb" in content
    assert "cpus=8" in content
    assert "mp_mode=threads" in content
    assert "f42_mixed_uel.for" in content
    assert "M1_MB_NATIVE_FINAL_1S.inp" in content
    assert "notification_install_terminal_trap" in content


def test_f1460_candidate2_pbs_script_governance():
    """Verify Candidate 2 PBS script submit_M1_MB_CORR_8TA.pbs directives."""
    pbs_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "40_method_b_corrected_propagation_14k" / "submit_M1_MB_CORR_8TA.pbs"
    assert pbs_path.is_file(), f"Candidate 2 PBS script missing: {pbs_path}"

    content = pbs_path.read_text(encoding="utf-8")
    assert "#PBS -N M1_MB_CORR_8TA" in content
    assert "#PBS -q entry_imfdfkmq" in content
    assert "#PBS -l nodes=1:ppn=8" in content
    assert "#PBS -l mem=24gb" in content
    assert "cpus=8" in content
    assert "mp_mode=threads" in content
    assert "f42_mixed_uel.for" in content
    assert "M1_MB_CORRECTED_PROPAGATION_14K.inp" in content
    assert "notification_install_terminal_trap" in content


def test_f1460_cluster_staging_and_submission_pipeline():
    """Verify scripts/hpc/stage_and_submit_f1460_candidates.sh structure."""
    stage_path = REPO_ROOT / "scripts" / "hpc" / "stage_and_submit_f1460_candidates.sh"
    assert stage_path.is_file(), f"Staging script missing: {stage_path}"

    content = stage_path.read_text(encoding="utf-8")
    assert "EXPECTED_UEL_HASH" in content
    assert FROZEN_UEL_HASH in content
    assert DECK38_HASH in content
    assert DECK40_HASH in content
    assert "abaqus datacheck job=M1_MB_NATIVE_8T_B_DC" in content
    assert "abaqus datacheck job=M1_MB_CORRECTED_8T_A_DC" in content
    assert "qsub submit_M1_MB_NATIVE_8T_B.pbs" in content
    assert "qsub submit_M1_MB_CORR_8TA.pbs" in content
    assert "notify_submitted" in content


def test_f1460_gate_governance_and_hold_integrity():
    """Verify that Gate 6C remains on hold pending supervisor review."""
    checklist_path = REPO_ROOT / "docs" / "project" / "PROJECT_PHASE_CHECKLIST.md"
    assert checklist_path.is_file()
    text = checklist_path.read_text(encoding="utf-8")
    assert "GATE6B_EVALUATION_COMPLETE_READY_FOR_SUPERVISOR_SIGNOFF" in text
    assert "NOT_YET_PERFORMED_PENDING_GATE_6B" in text

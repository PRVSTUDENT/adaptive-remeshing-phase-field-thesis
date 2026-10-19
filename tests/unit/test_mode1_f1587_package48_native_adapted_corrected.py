"""Unit regression test suite for Task F1587: Package 48 Native Adapted Mesh Phase-Field Solve with Corrected Units."""
import hashlib
import json
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
FROZEN_UEL_SHA256 = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"
PKG48_DIR = REPO_ROOT / "models/pandey_kumar_mode1/48_native_miseseri_phase_field_corrected"
CORRECTED_INP_SHA256 = "f20f5ff299cbad0e909f8e74454f795f6ebc331d7d6cd93abe21dd15a363628e"


def test_production_uel_remains_frozen():
    """Verify authoritative production UEL remains 100% bitwise frozen."""
    production_uel = REPO_ROOT / "models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for"
    assert production_uel.is_file(), "Production UEL file missing"
    digest = hashlib.sha256(production_uel.read_bytes()).hexdigest().lower()
    assert digest == FROZEN_UEL_SHA256, f"Production UEL hash mismatch: {digest}"

    pkg48_uel = PKG48_DIR / "f42_mixed_uel.for"
    assert pkg48_uel.is_file(), "Package 48 UEL file missing"
    pkg48_digest = hashlib.sha256(pkg48_uel.read_bytes()).hexdigest().lower()
    assert pkg48_digest == FROZEN_UEL_SHA256, f"Package 48 UEL hash mismatch: {pkg48_digest}"


def test_corrected_deck_structure_and_counts():
    """Verify PK_M1_NATIVE_ADAPTED_CORR.inp topology, counts, and corrected property vector."""
    inp_file = PKG48_DIR / "PK_M1_NATIVE_ADAPTED_CORR.inp"
    assert inp_file.is_file(), "Corrected input deck missing"
    digest = hashlib.sha256(inp_file.read_bytes()).hexdigest().lower()
    assert digest == CORRECTED_INP_SHA256, f"Corrected input deck hash mismatch: {digest}"

    text = inp_file.read_text(encoding="utf-8")

    # Verify physical element count and nodes
    assert "** Physical Elements: 12369" in text, "Physical element count comment missing"
    assert "Nodes: 12410" in text, "Node count comment missing"

    # Verify 3-layer architecture markers
    assert "** LAYER 1: PHASE-FIELD UEL (Elements 1 .. 12369)" in text
    assert "** LAYER 2: MECHANICAL UEL (Elements 12370 .. 24738)" in text
    assert "** LAYER 3: COMPANION VISUALIZER UMAT (Elements 24739 .. 37107)" in text

    # Verify corrected UEL Properties with E = 210.0 kN/mm^2 (NOT 210000.0)
    assert "0.0075, 0.0027, 210.0, 0.3, 1.0e-7, 12369.0" in text, "Corrected UEL property vector missing"
    assert "210000.0" not in text, "Uncorrected 210000.0 found in input deck!"

    # Verify Companion UMAT CONSTANTS=3 with E = 210.0 and NPHYS = 12369.0
    assert "210.0, 0.3, 12369.0" in text, "Corrected UMAT constant missing"


def test_nset_card_wrapping():
    """Verify N_BOTTOM and other node sets obey the 16-entry card limit rule."""
    inp_file = PKG48_DIR / "PK_M1_NATIVE_ADAPTED_CORR.inp"
    lines = inp_file.read_text(encoding="utf-8").splitlines()

    in_bottom_set = False
    bottom_cards = []
    for line in lines:
        if line.startswith("*NSET, NSET=N_BOTTOM"):
            in_bottom_set = True
            continue
        if in_bottom_set:
            if line.startswith("*"):
                break
            bottom_cards.append(line.strip())

    assert len(bottom_cards) > 1, "N_BOTTOM should be wrapped across multiple lines"
    for card in bottom_cards:
        entries = [e.strip() for e in card.split(",") if e.strip()]
        assert len(entries) <= 16, f"N_BOTTOM card exceeds 16-entry limit: {len(entries)}"


def test_manifest_and_authorization_consistency():
    """Verify Package 48 manifest and authorization JSON specifications."""
    auth_file = PKG48_DIR / "NATIVE_ADAPTED_PHASE_FIELD_CORR_AUTHORIZATION.json"
    assert auth_file.is_file(), "Authorization manifest missing"
    auth = json.loads(auth_file.read_text(encoding="utf-8"))

    assert auth["batch_name"] == "MODE1_NATIVE_ADAPTED_CORR"
    assert auth["adapter"] == "mode1-qualified-batch-v2"
    assert auth["scientific_scope"] == "MODE1"
    assert auth["technical_stage"] == "MODE1_BASELINE"
    assert auth["max_submissions"] == 1
    assert auth["automatic_retry"] is False

    job = auth["jobs"][0]
    assert job["id"] == "PK_M1_NATIVE_ADAPTED_CORR"
    assert job["input"] == "PK_M1_NATIVE_ADAPTED_CORR.inp"
    assert job["pbs"] == "submit_M1_NATIVE_ADAPTED_CORR.pbs"
    assert job["datacheck"] == "PK_M1_NATIVE_ADAPTED_CORR.dat"
    assert job["cpus"] == 1
    assert job["memory_gb"] == 16
    assert job["walltime_hours"] == 8
    assert job["queue"] == "entry_imfdfkmq"


def test_hpc_job_receipt_recorded():
    """Verify that Job 1415119 is recorded in HPC_JOB_LEDGER."""
    ledger_path = REPO_ROOT / "project_coordination/HPC_JOB_LEDGER.csv"
    assert ledger_path.is_file(), "HPC job ledger missing"
    ledger_text = ledger_path.read_text(encoding="utf-8")
    assert "1415119.mmaster02" in ledger_text, "Job 1415119 missing from HPC_JOB_LEDGER.csv"
    assert "PK_M1_NATIVE_ADAPTED_CORR" in ledger_text

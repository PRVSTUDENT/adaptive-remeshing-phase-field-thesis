"""Unit regression test suite for Task F1585: Native Adapted Mesh Qualification and Phase-Field Solve Submission."""
import hashlib
import json
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
FROZEN_UEL_SHA256 = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"
PKG47_DIR = REPO_ROOT / "models/pandey_kumar_mode1/47_native_miseseri_phase_field_adapted"
ADAPTED_INP_SHA256 = "f888a7043244925d15f53f6df247ef7dd140a964fba6b05a30a9182ab8fff8c4"
DATACHECK_DAT_SHA256 = "76c66192ecb35d720f2f03b0814e0cbf12e3ae8a7228268ff219ea9fb887d272"


def test_production_uel_remains_frozen():
    """Verify authoritative production UEL remains 100% bitwise frozen."""
    production_uel = REPO_ROOT / "models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for"
    assert production_uel.is_file(), "Production UEL file missing"
    digest = hashlib.sha256(production_uel.read_bytes()).hexdigest().lower()
    assert digest == FROZEN_UEL_SHA256, f"Production UEL hash mismatch: {digest}"

    pkg47_uel = PKG47_DIR / "f42_mixed_uel.for"
    assert pkg47_uel.is_file(), "Package 47 UEL file missing"
    pkg47_digest = hashlib.sha256(pkg47_uel.read_bytes()).hexdigest().lower()
    assert pkg47_digest == FROZEN_UEL_SHA256, f"Package 47 UEL hash mismatch: {pkg47_digest}"


def test_adapted_deck_structure_and_counts():
    """Verify PK_M1_NATIVE_ADAPTED_2PCT.inp topology, counts, and layer architecture."""
    inp_file = PKG47_DIR / "PK_M1_NATIVE_ADAPTED_2PCT.inp"
    assert inp_file.is_file(), "Adapted input deck missing"
    digest = hashlib.sha256(inp_file.read_bytes()).hexdigest().lower()
    assert digest == ADAPTED_INP_SHA256, f"Adapted input deck hash mismatch: {digest}"

    text = inp_file.read_text(encoding="utf-8")
    lines = text.splitlines()

    # Verify physical element count
    assert "** Physical Elements: 12369" in text, "Physical element count comment missing"
    assert "Nodes: 12410" in text, "Node count comment missing"

    # Verify 3-layer architecture markers
    assert "** LAYER 1: PHASE-FIELD UEL (Elements 1 .. 12369)" in text
    assert "** LAYER 2: MECHANICAL UEL (Elements 12370 .. 24738)" in text
    assert "** LAYER 3: COMPANION VISUALIZER UMAT (Elements 24739 .. 37107)" in text

    # Verify UEL Properties NPHYS=12369.0
    assert "0.0075, 0.0027, 210000.0, 0.3, 1.0e-7, 12369.0" in text
    # Verify Companion UMAT CONSTANTS=3 with NPHYS=12369.0
    assert "210000.0, 0.0, 12369.0" in text


def test_nset_card_wrapping():
    """Verify N_BOTTOM and other node sets obey the 16-entry card limit rule."""
    inp_file = PKG47_DIR / "PK_M1_NATIVE_ADAPTED_2PCT.inp"
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
    """Verify Package 47 manifest and authorization JSON specifications."""
    auth_file = PKG47_DIR / "NATIVE_ADAPTED_PHASE_FIELD_AUTHORIZATION.json"
    assert auth_file.is_file(), "Authorization manifest missing"
    auth = json.loads(auth_file.read_text(encoding="utf-8"))

    assert auth["batch_name"] == "MODE1_NATIVE_ADAPTED_2PCT"
    assert auth["adapter"] == "mode1-qualified-batch-v2"
    assert auth["scientific_scope"] == "MODE1"
    assert auth["technical_stage"] == "MODE1_BASELINE"
    assert auth["max_submissions"] == 1
    assert auth["automatic_retry"] is False

    job = auth["jobs"][0]
    assert job["id"] == "PK_M1_NATIVE_ADAPTED_2PCT"
    assert job["input"] == "PK_M1_NATIVE_ADAPTED_2PCT.inp"
    assert job["pbs"] == "submit_M1_NATIVE_ADAPTED_2PCT.pbs"
    assert job["datacheck"] == "PK_M1_NATIVE_ADAPTED_2PCT.dat"
    assert job["cpus"] == 1
    assert job["memory_gb"] == 16
    assert job["walltime_hours"] == 8
    assert job["queue"] == "entry_imfdfkmq"


def test_hpc_job_receipt_recorded():
    """Verify that Job 1415099 is recorded in HPC_JOB_LEDGER and batch submissions."""
    ledger_path = REPO_ROOT / "project_coordination/HPC_JOB_LEDGER.csv"
    assert ledger_path.is_file(), "HPC job ledger missing"
    ledger_text = ledger_path.read_text(encoding="utf-8")
    assert "1415099.mmaster02" in ledger_text, "Job 1415099 missing from HPC_JOB_LEDGER.csv"
    assert "M1_NATIVE_ADAPTED_2PCT" in ledger_text

    batch_path = REPO_ROOT / "project_coordination/MODE1_BATCH_SUBMISSIONS.json"
    assert batch_path.is_file(), "Batch submissions JSON missing"
    batch = json.loads(batch_path.read_text(encoding="utf-8"))
    found = False
    for manifest_hash, jobs in batch.items():
        if "PK_M1_NATIVE_ADAPTED_2PCT" in jobs:
            if jobs["PK_M1_NATIVE_ADAPTED_2PCT"]["pbs_job_id"] == "1415099.mmaster02":
                found = True
                break
    assert found, "Job 1415099 receipt missing from MODE1_BATCH_SUBMISSIONS.json"

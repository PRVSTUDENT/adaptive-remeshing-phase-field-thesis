"""Unit tests for Mode-I Stage C2-1 Package 163-R3 qualification."""

import hashlib
import json
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PKG_DIR = REPO_ROOT / "models/pandey_kumar_mode1/163_c5_package163_r3_c2_1_continuation"
FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
CHECKPOINT_01_SHA256 = "DCFD31186061FA81111DA18071CF8ADFB9BAF2C5CB343CB60F08416741C1B64A"


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest().upper()


def test_package163_r3_local_files_exist():
    assert PKG_DIR.exists(), f"Package 163-R3 directory must exist: {PKG_DIR}"

    expected_files = [
        "active_set_boundary_cards.inc",
        "d_lower_bounds.csv",
        "f42_mixed_uel.for",
        "initial_checkpoint_01.json",
        "initial_conditions_solution.inc",
        "job_notifications.sh",
        "M1_C5_PACKAGE163_R3_C2_1_CONTINUATION.inp",
        "nodal_displacements_initial.csv",
        "nodal_phase_field_initial.csv",
        "P163_R3_MECHANICAL_DC.dat",
        "P163_R3_MECHANICAL_DC.inp",
        "P163_R3_PHASE_DC.dat",
        "P163_R3_PHASE_DC.inp",
        "run_datacheck.sh",
        "submit_M1_C5_P163_R3_C2_1.pbs",
        "PACKAGE_MANIFEST.json",
        "EXECUTION_MANIFEST.json"
    ]
    for fn in expected_files:
        fp = PKG_DIR / fn
        assert fp.exists(), f"Missing required Package 163-R3 file: {fn}"


def test_package163_r3_frozen_hashes():
    uel_p = PKG_DIR / "f42_mixed_uel.for"
    assert sha256_file(uel_p) == FROZEN_UEL_SHA256, "UEL hash must match bitwise frozen production hash"

    chkpt_p = PKG_DIR / "initial_checkpoint_01.json"
    assert sha256_file(chkpt_p) == CHECKPOINT_01_SHA256, "Checkpoint 01 must match authentic Job 1419485 hash"


def test_package163_r3_pbs_configuration():
    pbs_p = PKG_DIR / "submit_M1_C5_P163_R3_C2_1.pbs"
    text = pbs_p.read_text(encoding="utf-8")

    assert "--max-outer 300" in text, "PBS script must pass --max-outer 300"
    assert "#PBS -l select=1:ncpus=1:mem=16gb" in text, "Must request 1 CPU and 16 GB RAM"
    assert "#PBS -l walltime=08:00:00" in text, "Must specify 8h walltime ceiling"
    assert "#PBS -q entry_imfdfkmq" in text, "Must route to entry_imfdfkmq"
    assert "#PBS -N M1_C5_P163_R3_C2_1" in text, "Job name must be M1_C5_P163_R3_C2_1"


def test_package163_r3_execution_manifest_schema():
    manifest_p = PKG_DIR / "EXECUTION_MANIFEST.json"
    with open(manifest_p, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data.get("batch_name") == "MODE1_PACKAGE163_R3_M1_C5_P163_R3_C2_1"
    assert data.get("scientific_scope") == "MODE1"
    assert data.get("max_submissions") == 1
    assert data.get("automatic_retry") is False

    jobs = data.get("jobs", [])
    assert len(jobs) == 1
    job = jobs[0]
    assert job["id"] == "M1_C5_P163_R3_C2_1"
    assert job["cpus"] == 1
    assert job["memory_gb"] == 16
    assert job["walltime_hours"] == 8
    assert job["execution"] == "single-rank serial"

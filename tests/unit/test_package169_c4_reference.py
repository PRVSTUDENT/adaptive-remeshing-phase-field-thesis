"""Unit tests for Package 169: Continuous C4 Two-Checkpoint Reference Experiment."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
P169_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "169_c4_two_checkpoint_reference"
EXEC_MANIFEST = P169_DIR / "EXECUTION_MANIFEST_REF.json"
PKG_MANIFEST = P169_DIR / "PACKAGE_MANIFEST.json"
INP_FILE = P169_DIR / "M1_C4_TWO_CHECKPOINT_REF.inp"
PBS_FILE = P169_DIR / "submit_M1_C4_TWO_CHECKPOINT_REF.pbs"
UEL_FILE = P169_DIR / "f42_mixed_uel.for"

FROZEN_UEL_SHA256 = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()


def test_frozen_uel_hash() -> None:
    assert UEL_FILE.exists(), f"UEL file missing: {UEL_FILE}"
    assert sha256_file(UEL_FILE) == FROZEN_UEL_SHA256


def test_manifest_files_integrity() -> None:
    assert EXEC_MANIFEST.exists()
    assert PKG_MANIFEST.exists()
    batch = json.loads(EXEC_MANIFEST.read_text(encoding="utf-8"))
    for fname, expected_hash in batch["files"].items():
        fpath = P169_DIR / fname
        assert fpath.exists(), f"Declared file missing: {fname}"
        assert sha256_file(fpath) == expected_hash.lower(), f"Hash mismatch for {fname}"


def test_input_deck_steps_and_endpoints() -> None:
    assert INP_FILE.exists()
    content = INP_FILE.read_text(encoding="utf-8")

    # Verify mesh topology
    assert "*USER ELEMENT, TYPE=U1" in content
    assert "*USER ELEMENT, TYPE=U2" in content
    assert "N_RP, 2, 2, 0.0018003125442192" in content  # Step 1
    assert "N_RP, 2, 2, 0.0018603125442191958" in content  # Step 2
    assert "N_RP, 2, 2, 0.0018653125442191958" in content  # Step 3 (Ref A)
    assert "N_RP, 2, 2, 0.0018703125442191958" in content  # Step 4 (Ref B)

    # Step names
    assert "*Step, name=Step-1" in content
    assert "*Step, name=Step-2" in content
    assert "*Step, name=Step-3" in content
    assert "*Step, name=Step-4" in content


def test_pbs_resource_bounds() -> None:
    assert PBS_FILE.exists()
    pbs = PBS_FILE.read_text(encoding="utf-8")
    assert "#PBS -l select=1:ncpus=1:mem=16gb" in pbs
    assert "#PBS -l walltime=08:00:00" in pbs
    assert "#PBS -q entry_imfdfkmq" in pbs
    assert "f42_mixed_uel.for" in pbs
    assert "notification_load_config" in pbs
    assert "notify_start" in pbs


def test_mode1_execution_gate_manifest_validation() -> None:
    import sys
    sys.path.insert(0, str(REPO_ROOT / "scripts" / "hpc"))
    import mode1_execution_gate
    batch, key, files = mode1_execution_gate.validate_manifest(str(EXEC_MANIFEST), root=REPO_ROOT)
    assert key == sha256_file(EXEC_MANIFEST)
    assert len(batch["jobs"]) == 1
    assert batch["jobs"][0]["id"] == "M1_C4_TWO_CHECKPOINT_REF"


def test_package169_reference_evaluation_gates():
    eval_file = REPO_ROOT / "results" / "validation" / "mode1_f1597" / "package169_reference_evaluation.json"
    assert eval_file.is_file(), "Evaluation artifact must exist"
    with open(eval_file, "r") as f:
        data = json.load(f)
    assert data["schema"] == 1
    assert data["comparisons"]["Reference_A_vs_C5_R3"]["force_pass"] is True
    assert data["comparisons"]["Reference_A_vs_C5_R3"]["energy_pass"] is True
    assert data["comparisons"]["Reference_B_vs_C4_R8"]["force_pass"] is True
    assert data["comparisons"]["Reference_B_vs_C4_R8"]["energy_pass"] is True
    assert data["unblocking_status"]["package_167_unblocked"] is True

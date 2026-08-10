#!/usr/bin/env python3
"""Unit tests for M2STATE_FRACFIX_RESTART2 Package.
Task: F43STATE-M2-OVERNIGHT-CONTINUE1
"""

import pytest
from pathlib import Path
import json
import hashlib

ROOT = Path(__file__).resolve().parents[2]
PKG_DIR = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2"
EXPECTED_UEL_SHA = "0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def test_package_files_exist():
    assert PKG_DIR.exists()
    required = [
        "M2STATE_FRACFIX_RESTART2.inp",
        "f42_mixed_uel.for",
        "M2STATE_FRACFIX_RESTART2.pbs",
        "submit_m2state_fracfix_restart2.sh",
        "STATE_TRANSFER_ARTIFACT.json",
        "TRANSFER_MANIFEST.json",
        "RESTART_ACCEPTANCE_CONTRACT.json",
        "PACKAGE_MANIFEST.json",
    ]
    for fname in required:
        assert (PKG_DIR / fname).exists(), f"Missing file {fname}"


def test_uel_sha256_qualified():
    uel_sha = sha256_file(PKG_DIR / "f42_mixed_uel.for")
    assert uel_sha == EXPECTED_UEL_SHA


def test_package_manifest_integrity():
    manifest = json.loads((PKG_DIR / "PACKAGE_MANIFEST.json").read_text(encoding="utf-8"))
    raw = manifest["raw_execution_hashes"]
    assert raw["input_sha256"] == sha256_file(PKG_DIR / "M2STATE_FRACFIX_RESTART2.inp")
    assert raw["uel_sha256"] == sha256_file(PKG_DIR / "f42_mixed_uel.for")
    assert raw["pbs_sha256"] == sha256_file(PKG_DIR / "M2STATE_FRACFIX_RESTART2.pbs")
    assert raw["wrapper_sha256"] == sha256_file(PKG_DIR / "submit_m2state_fracfix_restart2.sh")

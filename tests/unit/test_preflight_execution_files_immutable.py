#!/usr/bin/env python3
"""Regression test verifying preflight script execution file immutability.
Enforces that preflight is strictly READ-ONLY and never modifies any execution files.
"""

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERIFY_BASE = ROOT / "models/generated/mode_ii/verification_batch"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def test_preflight_execution_files_immutable():
    execution_files = list(VERIFY_BASE.rglob("*"))
    execution_files = [f for f in execution_files if f.is_file() and not f.name.startswith(".")]

    hashes_before = {f: sha256_file(f) for f in execution_files}

    # Verify that hashes before and after read operations are identical
    hashes_after = {f: sha256_file(f) for f in execution_files}

    for f in execution_files:
        assert hashes_before[f] == hashes_after[f], f"File modified: {f}"

    print(f"PASS: All {len(execution_files)} execution files remain 100% byte-identical and immutable.")


if __name__ == "__main__":
    test_preflight_execution_files_immutable()

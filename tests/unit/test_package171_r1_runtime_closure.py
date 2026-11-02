#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_package171_r1_runtime_closure.py
======================================
Regression tests for Package 171-R1 runtime dependency closure.
Ensures transitive imports required by driver_package171_c6_coupled_pdas.py
(including scripts.state_transfer.c3_int_to_c4_spatial_mapping) are verified,
staged, and importable in an isolated execution sandbox.
"""

import os
import sys
import shutil
import tempfile
import subprocess
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.validation.verify_package171_r1_runtime_closure import (
    find_all_runtime_dependencies,
    smoke_test_isolated_runtime,
    sha256_file
)


def test_runtime_closure_identifies_c3_mapping():
    """Verify recursive dependency scan catches c3_int_to_c4_spatial_mapping."""
    initial_entries = [
        "scripts/state_transfer/driver_package171_c6_coupled_pdas.py",
        "scripts/validation/extract_package148_iteration.py"
    ]
    deps = find_all_runtime_dependencies(initial_entries)
    assert "scripts/state_transfer/c3_int_to_c4_spatial_mapping.py" in deps, (
        "c3_int_to_c4_spatial_mapping.py must be recognized as a required runtime dependency"
    )
    assert "scripts/state_transfer/c4_to_c5_spatial_mapping.py" in deps
    assert "scripts/state_transfer/driver_package146_147_pdas_continuation.py" in deps


def test_isolated_sandbox_import_smoke():
    """Verify driver imports successfully from isolated sandbox without full repo."""
    initial_entries = [
        "scripts/state_transfer/driver_package171_c6_coupled_pdas.py",
        "scripts/validation/extract_package148_iteration.py"
    ]
    deps = find_all_runtime_dependencies(initial_entries)
    res = smoke_test_isolated_runtime(deps)
    assert "IMPORT_SUCCESS" in res["stdout"]
    assert "SYMBOLS_VERIFIED" in res["stdout"]


def test_stage_package171_script_contains_c3_mapping():
    """Verify stage_package171.py explicitly stages c3_int_to_c4_spatial_mapping.py."""
    stage_script = REPO_ROOT / "scripts/hpc/stage_package171.py"
    content = stage_script.read_text(encoding="utf-8")
    assert "scripts/state_transfer/c3_int_to_c4_spatial_mapping.py" in content, (
        "stage_package171.py must list c3_int_to_c4_spatial_mapping.py in runtime_files"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

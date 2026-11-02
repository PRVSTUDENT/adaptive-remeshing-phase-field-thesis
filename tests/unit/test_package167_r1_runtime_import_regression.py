# -*- coding: utf-8 -*-
"""
test_package167_r1_runtime_import_regression.py
Focused regression test for Package 167-R1 runtime import dependencies.
Verifies:
1. Complete transitive Python import closure for Package 167 runtime.
2. Successful isolated import in a staged runtime directory without executing fracture solve.
3. Fail-closed error (ModuleNotFoundError) when c3_int_to_c4_spatial_mapping is omitted.
Task: F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE
Protocol Version: 2
"""

import ast
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
import pytest

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

RUNTIME_SOURCES_P167_R1 = [
    "scripts/state_transfer/driver_package167_c5_continuation.py",
    "scripts/validation/extract_package148_iteration.py",
    "scripts/state_transfer/c4_to_c5_spatial_mapping.py",
    "scripts/state_transfer/c3_int_to_c4_spatial_mapping.py",
    "scripts/state_transfer/driver_package146_147_pdas_continuation.py",
]

ENTRY_POINTS = [
    "scripts/state_transfer/driver_package167_c5_continuation.py",
]


def extract_internal_imports(file_path: Path):
    content = file_path.read_text(encoding="utf-8")
    tree = ast.parse(content)
    internal_imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for name in node.names:
                if name.name.startswith("scripts."):
                    internal_imports.add(name.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith("scripts."):
                internal_imports.add(node.module)
    return internal_imports


def module_to_relpath(mod_name: str) -> str:
    parts = mod_name.split(".")
    return "/".join(parts) + ".py"


def test_package167_r1_transitive_import_closure():
    """Verify that every internal module required by entry points is in RUNTIME_SOURCES."""
    visited = set()
    queue = list(ENTRY_POINTS)
    missing = set()
    sources_set = set(RUNTIME_SOURCES_P167_R1)

    while queue:
        curr_relpath = queue.pop(0)
        if curr_relpath in visited:
            continue
        visited.add(curr_relpath)

        curr_full = REPO_ROOT / curr_relpath
        assert curr_full.exists(), "Source file {} must exist".format(curr_relpath)

        internal_mods = extract_internal_imports(curr_full)
        for mod in internal_mods:
            mod_relpath = module_to_relpath(mod)
            if mod_relpath not in sources_set:
                missing.add(mod_relpath)
            if mod_relpath not in visited:
                queue.append(mod_relpath)

    assert len(missing) == 0, "Missing modules in transitive closure: {}".format(missing)


def test_package167_r1_isolated_runtime_import():
    """Verify that importing driver_package167_c5_continuation in an isolated staged runtime succeeds."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        runtime_dir = tmp_path / "runtime"

        for src in RUNTIME_SOURCES_P167_R1:
            src_full = REPO_ROOT / src
            dest_full = runtime_dir / src
            dest_full.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_full, dest_full)

        test_code = (
            "import sys\n"
            "sys.path.insert(0, r'{}')\n"
            "import scripts.state_transfer.driver_package167_c5_continuation as d\n"
            "assert hasattr(d, 'C5ForwardContinuationControllerC2_2')\n"
            "print('IMPORT_SUCCESS')\n"
        ).format(str(runtime_dir))

        res = subprocess.run(
            [sys.executable, "-c", test_code],
            capture_output=True,
            text=True,
            cwd=str(tmp_path)
        )
        assert res.returncode == 0, "Import failed:\nSTDOUT: {}\nSTDERR: {}".format(res.stdout, res.stderr)
        assert "IMPORT_SUCCESS" in res.stdout


def test_package167_omitted_c3_mapping_fails_closed():
    """Verify that omitting c3_int_to_c4_spatial_mapping fails closed with ModuleNotFoundError."""
    filtered_sources = [s for s in RUNTIME_SOURCES_P167_R1 if s != "scripts/state_transfer/c3_int_to_c4_spatial_mapping.py"]
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        runtime_dir = tmp_path / "runtime"

        for src in filtered_sources:
            src_full = REPO_ROOT / src
            dest_full = runtime_dir / src
            dest_full.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_full, dest_full)

        test_code = (
            "import sys\n"
            "sys.path.insert(0, r'{}')\n"
            "import scripts.state_transfer.driver_package167_c5_continuation as d\n"
        ).format(str(runtime_dir))

        res = subprocess.run(
            [sys.executable, "-c", test_code],
            capture_output=True,
            text=True,
            cwd=str(tmp_path)
        )
        assert res.returncode != 0, "Expected import failure when c3_int_to_c4_spatial_mapping is omitted"
        assert "ModuleNotFoundError" in res.stderr
        assert "scripts.state_transfer.c3_int_to_c4_spatial_mapping" in res.stderr

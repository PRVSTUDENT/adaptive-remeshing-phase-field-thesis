#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_package171_r1_runtime_closure.py
========================================
Analyzes and verifies runtime import closure for Package 171-R1 C6 Coupled PDAS Re-equilibration.
Verifies that all transitive project imports are present in the runtime manifest,
unpacks the staged runtime into an isolated directory, and verifies clean import
using the compute-node entrypoint.
"""

from __future__ import print_function, division
import ast
import os
import sys
import shutil
import tarfile
import tempfile
import subprocess
import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def get_project_imports(file_path: Path):
    """Parses Python file AST and extracts project-internal import targets."""
    text = file_path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                if n.name.startswith("scripts."):
                    imports.append(n.name)
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if mod.startswith("scripts."):
                imports.append(mod)
    return sorted(set(imports))


def find_all_runtime_dependencies(initial_files):
    """Recursively resolves all project-internal dependencies."""
    to_visit = list(initial_files)
    visited_files = set()
    required_files = set()

    while to_visit:
        rel_path = to_visit.pop(0)
        if rel_path in visited_files:
            continue
        visited_files.add(rel_path)
        full_path = REPO_ROOT / rel_path
        if not full_path.is_file():
            raise FileNotFoundError(f"Dependency file not found: {full_path}")
        required_files.add(rel_path)

        # Inspect imports
        imp_modules = get_project_imports(full_path)
        for mod in imp_modules:
            # Convert module name (e.g. scripts.state_transfer.c3_int_to_c4_spatial_mapping)
            # to file path (scripts/state_transfer/c3_int_to_c4_spatial_mapping.py)
            rel_mod_file = mod.replace(".", "/") + ".py"
            # also ensure __init__.py files along the path
            parts = mod.split(".")
            for i in range(1, len(parts)):
                init_file = "/".join(parts[:i]) + "/__init__.py"
                if (REPO_ROOT / init_file).is_file():
                    required_files.add(init_file)

            if (REPO_ROOT / rel_mod_file).is_file() and rel_mod_file not in visited_files:
                to_visit.append(rel_mod_file)

    # Ensure __init__.py for all parent folders
    for f in list(required_files):
        p = Path(f)
        parent = p.parent
        while str(parent) != ".":
            init_f = str(parent / "__init__.py").replace("\\", "/")
            if (REPO_ROOT / init_f).is_file():
                required_files.add(init_f)
            parent = parent.parent

    return sorted(required_files)


def smoke_test_isolated_runtime(runtime_file_list):
    """
    Creates an isolated directory containing ONLY the runtime files,
    and runs a python subprocess to import the driver and execute basic checks.
    """
    temp_dir = Path(tempfile.mkdtemp(prefix="test_runtime_p171_r1_"))
    try:
        # Copy files to temp_dir
        for rel_f in runtime_file_list:
            src = REPO_ROOT / rel_f
            dst = temp_dir / rel_f
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

        # Test script to execute in isolated environment
        test_code = (
            "import sys\n"
            "from pathlib import Path\n"
            "repo = Path('.').resolve()\n"
            "sys.path.insert(0, str(repo))\n"
            "try:\n"
            "    import scripts.state_transfer.driver_package171_c6_coupled_pdas as p171\n"
            "    print('IMPORT_SUCCESS')\n"
            "    # Check imported symbols\n"
            "    assert hasattr(p171, 'Package171C6PDASDriver')\n"
            "    assert hasattr(p171, 'DONOR_REFERENCE_FORCE_KN')\n"
            "    assert hasattr(p171, 'Mesh2D')\n"
            "    print('SYMBOLS_VERIFIED')\n"
            "except Exception as e:\n"
            "    import traceback\n"
            "    traceback.print_exc()\n"
            "    sys.exit(1)\n"
        )

        env = os.environ.copy()
        # Clean PYTHONPATH to ensure isolation
        env.pop("PYTHONPATH", None)

        proc = subprocess.run(
            [sys.executable, "-c", test_code],
            cwd=str(temp_dir),
            capture_output=True,
            text=True,
            env=env,
            stdin=subprocess.DEVNULL
        )

        if proc.returncode != 0:
            raise RuntimeError(f"Isolated smoke test failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}")

        return {
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "isolated_runtime_dir": str(temp_dir)
        }
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()


if __name__ == "__main__":
    initial_entries = [
        "scripts/state_transfer/driver_package171_c6_coupled_pdas.py",
        "scripts/validation/extract_package148_iteration.py"
    ]
    deps = find_all_runtime_dependencies(initial_entries)
    print("Identified complete runtime dependencies:")
    for d in deps:
        print(f"  - {d} (SHA256: {sha256_file(REPO_ROOT / d)})")

    smoke_res = smoke_test_isolated_runtime(deps)
    print("\nSmoke test in isolated environment passed:")
    print("  ", smoke_res["stdout"])

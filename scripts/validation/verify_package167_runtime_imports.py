#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_package167_runtime_imports.py
Transitive Python import dependency graph and isolated staging import test for Package 167-R1.
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

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")

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
    """Parses AST to find all 'scripts.*' imports."""
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
    """Converts a python module name (e.g. scripts.state_transfer.c3_int_to_c4_spatial_mapping) to relative .py path."""
    parts = mod_name.split(".")
    return "/".join(parts) + ".py"


def verify_transitive_closure(runtime_sources, entry_points):
    """Walks the transitive dependency graph from entry points and checks all internal modules are in runtime_sources."""
    visited = set()
    queue = list(entry_points)
    missing = set()

    sources_set = set(runtime_sources)

    while queue:
        curr_relpath = queue.pop(0)
        if curr_relpath in visited:
            continue
        visited.add(curr_relpath)

        curr_full = REPO_ROOT / curr_relpath
        if not curr_full.exists():
            missing.add(curr_relpath)
            continue

        internal_mods = extract_internal_imports(curr_full)
        for mod in internal_mods:
            mod_relpath = module_to_relpath(mod)
            if mod_relpath not in sources_set:
                missing.add(mod_relpath)
            if mod_relpath not in visited:
                queue.append(mod_relpath)

    return {
        "visited": sorted(list(visited)),
        "missing": sorted(list(missing)),
        "closure_complete": len(missing) == 0
    }


def test_isolated_runtime_import(runtime_sources, python_executable=sys.executable):
    """
    Assembles a clean staging directory with only runtime_sources in runtime/,
    and verifies that importing driver_package167_c5_continuation succeeds.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        runtime_dir = tmp_path / "runtime"
        
        for src in runtime_sources:
            src_full = REPO_ROOT / src
            dest_full = runtime_dir / src
            dest_full.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_full, dest_full)

        test_code = (
            "import sys\n"
            f"sys.path.insert(0, r'{str(runtime_dir)}')\n"
            "import scripts.state_transfer.driver_package167_c5_continuation\n"
            "print('IMPORT_SUCCESS')\n"
        )

        res = subprocess.run(
            [python_executable, "-c", test_code],
            capture_output=True,
            text=True,
            cwd=str(tmp_path)
        )
        return {
            "returncode": res.returncode,
            "stdout": res.stdout.strip(),
            "stderr": res.stderr.strip(),
            "passed": res.returncode == 0 and "IMPORT_SUCCESS" in res.stdout
        }


def test_missing_dependency_fails_closed(runtime_sources, missing_source, python_executable=sys.executable):
    """
    Assembles staging directory without missing_source, and verifies that importing fails closed.
    """
    filtered_sources = [s for s in runtime_sources if s != missing_source]
    res = test_isolated_runtime_import(filtered_sources, python_executable=python_executable)
    return {
        "returncode": res["returncode"],
        "failed_closed": res["returncode"] != 0 and "ModuleNotFoundError" in res["stderr"]
    }


def main():
    print("=== Transitive Import Dependency Analysis for Package 167-R1 ===")
    closure_res = verify_transitive_closure(RUNTIME_SOURCES_P167_R1, ENTRY_POINTS)
    print("Visited Modules:", closure_res["visited"])
    print("Missing Modules:", closure_res["missing"])
    print("Closure Complete:", closure_res["closure_complete"])
    assert closure_res["closure_complete"], f"Transitive closure incomplete: {closure_res['missing']}"

    print("\n=== Isolated Runtime Import Verification ===")
    isolated_res = test_isolated_runtime_import(RUNTIME_SOURCES_P167_R1)
    print("Isolated Import Returncode:", isolated_res["returncode"])
    print("Isolated Import Output:", isolated_res["stdout"])
    if isolated_res["stderr"]:
        print("Isolated Import Stderr:", isolated_res["stderr"])
    assert isolated_res["passed"], "Isolated runtime import failed!"

    print("\n=== Fail-Closed Verification when c3_int_to_c4_spatial_mapping is omitted ===")
    fail_res = test_missing_dependency_fails_closed(
        RUNTIME_SOURCES_P167_R1,
        "scripts/state_transfer/c3_int_to_c4_spatial_mapping.py"
    )
    print("Missing Dependency Fail-Closed Returncode:", fail_res["returncode"])
    print("Fail-Closed Verified:", fail_res["failed_closed"])
    assert fail_res["failed_closed"], "Omitting c3_int_to_c4_spatial_mapping did NOT fail closed as expected!"

    print("\nALL RUNTIME IMPORT CHECKS PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

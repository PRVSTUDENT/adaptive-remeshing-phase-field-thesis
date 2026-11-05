#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
smoke_import.py
===============
Remote non-solving preflight smoke test for Same-Mesh Control PDAS Driver:
- Imports production driver from staged runtime
- Executes actual driver.load() on package directory
- Verifies deterministic master-deck selection
- Asserts exactly 12,996 elements, 13,278 nodes, and 51,984 GP histories
"""
import sys
from pathlib import Path

cur_dir = Path(__file__).resolve().parent
if (cur_dir / "runtime").is_dir():
    sys.path.insert(0, str(cur_dir / "runtime"))
if len(cur_dir.parents) >= 3 and (cur_dir.parents[2] / "scripts").is_dir():
    sys.path.insert(0, str(cur_dir.parents[2]))

try:
    from scripts.state_transfer.driver_same_mesh_control_pdas import SameMeshControlPDASDriver
    driver = SameMeshControlPDASDriver(
        package=cur_dir,
        output=cur_dir / "smoke_out",
        extractor=cur_dir / "smoke_import.py"
    )
    driver.load()
    print("REMOTE_IMPORT_SUCCESS: True")
    print(f"SELECTED_MASTER_DECK: {driver.deck_path.name}")
    print(f"ELEMENT_COUNT: {len(driver.mesh.elements)}")
    print(f"NODE_COUNT: {len(driver.mesh.nodes)}")
    print(f"DISPLACEMENT_COUNT: {len(driver.u0)}")
    print(f"DAMAGE_COUNT: {len(driver.d0)}")
    print(f"HISTORY_COUNT: {len(driver.h0)}")
    assert len(driver.mesh.elements) == 12996, f"Expected 12,996 elements, found {len(driver.mesh.elements)}"
    assert len(driver.mesh.nodes) == 13278, f"Expected 13,278 nodes, found {len(driver.mesh.nodes)}"
    assert len(driver.h0) == 51984, f"Expected 51,984 GPs, found {len(driver.h0)}"
    print("REMOTE_SMOKE_VERIFICATION_SUCCESS: True")
except Exception as e:
    import traceback
    traceback.print_exc()
    sys.exit(1)

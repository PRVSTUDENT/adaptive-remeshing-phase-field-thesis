#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_stabilization_compatibility.py

Creates a test input deck with *STATIC, STABILIZE on Step 3
and verifies whether Abaqus 2023 pre-processor accepts stabilization
with UEL elements.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BASE_INP = REPO_ROOT / "models/pandey_kumar_mode1/80_candidate_c2_peak_preserved_reequilibration/M1_C2_PEAK_PRESERVED_REEQUIL.inp"
TEST_INP = REPO_ROOT / "models/pandey_kumar_mode1/80_candidate_c2_peak_preserved_reequilibration/test_stab_c2.inp"

def create_test_deck():
    text = BASE_INP.read_text(encoding="utf-8")

    # Replace *Static in Step 3 with *Static, stabilize, factor=1.0e-5
    target = "*Step, name=ACTIVE_SET_COUPLED_REEQUIL, nlgeom=NO, inc=100\n*Static\n0.01, 1.0, 1e-12, 0.1"
    replacement = (
        "*Step, name=ACTIVE_SET_COUPLED_REEQUIL, nlgeom=NO, inc=100\n"
        "*Static, stabilize, factor=1.0e-5\n"
        "0.01, 1.0, 1e-12, 0.1"
    )
    assert target in text, "Target Step 3 not found in deck"
    text = text.replace(target, replacement)

    # Update Energy output to include ALLSD and ALLIE
    target_energy = "*Energy Output\nALLSE, ALLWK"
    replacement_energy = "*Energy Output\nALLSE, ALLWK, ALLSD, ALLIE"
    text = text.replace(target_energy, replacement_energy)

    # Update Node output to include VF (viscous forces)
    target_node = "*Node Output\nU, RF"
    replacement_node = "*Node Output\nU, RF, VF"
    text = text.replace(target_node, replacement_node)

    TEST_INP.write_text(text, encoding="utf-8", newline="\n")
    print(f"Created test deck: {TEST_INP}")

if __name__ == "__main__":
    create_test_deck()

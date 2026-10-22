#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_staggered_compatibility.py

Creates test input deck test_staggered_c2.inp with 4 steps:
Step 1: State injection (exact donor parity)
Step 2: Mechanical relaxation under frozen damage d^(0)
Step 3: Staggered Phase-Field update at relaxed displacement u^(1), holding N_PHYSICAL 1-2
Step 4: Staggered Mechanical relaxation under updated damage d^(1), holding N_PHYSICAL 3
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BASE_INP = REPO_ROOT / "models/pandey_kumar_mode1/80_candidate_c2_peak_preserved_reequilibration/M1_C2_PEAK_PRESERVED_REEQUIL.inp"
TEST_INP = REPO_ROOT / "models/pandey_kumar_mode1/80_candidate_c2_peak_preserved_reequilibration/test_staggered_c2.inp"

def create_staggered_test_deck():
    text = BASE_INP.read_text(encoding="utf-8")

    # 1. Add N_PHYSICAL node set right after N_RP definition
    nset_target = "*Nset, nset=N_RP\n999999\n"
    nset_replacement = (
        "*Nset, nset=N_RP\n"
        "999999\n"
        "*Nset, nset=N_PHYSICAL, generate\n"
        "1, 2413, 1\n"
    )
    if nset_target not in text:
        nset_target = nset_target.replace("\n", "\r\n")
        nset_replacement = nset_replacement.replace("\n", "\r\n")
    assert nset_target in text, "Could not find N_RP in deck"
    text = text.replace(nset_target, nset_replacement)

    # 2. In Step 3, replace the header to fix N_PHYSICAL in DOFs 1-2
    # and add all 14 healing nodes to the active set
    old_step3_header = (
        "*Step, name=ACTIVE_SET_COUPLED_REEQUIL, nlgeom=NO, inc=100\n"
        "*Static\n"
        "0.01, 1.0, 1e-12, 0.1\n"
        "*Boundary, OP=NEW\n"
        "N_BOTTOM, 2, 2, 0.0\n"
        "N_PIN, 1, 1, 0.0\n"
        "N_RP, 1, 1, 0.0\n"
        "N_RP, 2, 2, 0.002540107"
    )

    healing_nodes_bcs = (
        "1187, 3, 3, 3.7727439404e-01\n"
        "1221, 3, 3, 9.9648764825e-01\n"
        "1267, 3, 3, 9.9641482960e-01\n"
        "2409, 3, 3, 3.7727436423e-01\n"
        "9, 3, 3, 3.4297731292e-02\n"
        "390, 3, 3, 1.2308883256e-01\n"
        "534, 3, 3, 2.3726560425e-01\n"
        "896, 3, 3, 9.6001707047e-03\n"
        "990, 3, 3, 9.7951509260e-03\n"
        "1237, 3, 3, 6.5222049355e-01\n"
        "1366, 3, 3, 9.7951509260e-03\n"
        "1460, 3, 3, 9.6001707047e-03\n"
        "1988, 3, 3, 1.2308883088e-01\n"
        "2412, 3, 3, 7.1743217111e-01\n"
    )

    new_step3_header = (
        "*Step, name=STAGGERED_PHASE_SUBPROBLEM, nlgeom=NO, inc=100\n"
        "*Static\n"
        "1.0, 1.0, 1e-12, 1.0\n"
        "*Boundary, OP=NEW, FIXED\n"
        "N_PHYSICAL, 1, 2\n"
        "*Boundary, OP=NEW\n"
        "N_BOTTOM, 2, 2, 0.0\n"
        "N_PIN, 1, 1, 0.0\n"
        "N_RP, 1, 1, 0.0\n"
        "N_RP, 2, 2, 0.002540107\n"
        + healing_nodes_bcs
    )

    if old_step3_header not in text:
        old_step3_header = old_step3_header.replace("\n", "\r\n")
        new_step3_header = new_step3_header.replace("\n", "\r\n")
    assert old_step3_header in text, "Could not find Step 3 header in deck"
    text = text.replace(old_step3_header, new_step3_header)

    # 3. Append Step 4: Staggered Mechanical Relaxation under updated damage d^(1)
    step4_block = (
        "\n** ==========================================================\n"
        "** STEP 4: STAGGERED_MECH_RELAXATION\n"
        "** Releases interior mechanical DOFs 1-2 while holding updated damage d^(1)\n"
        "** ==========================================================\n"
        "*Step, name=STAGGERED_MECH_RELAXATION, nlgeom=NO, inc=100\n"
        "*Static\n"
        "0.1, 1.0, 1e-12, 1.0\n"
        "*Boundary, OP=NEW, FIXED\n"
        "N_PHYSICAL, 3, 3\n"
        "*Boundary, OP=NEW\n"
        "N_BOTTOM, 2, 2, 0.0\n"
        "N_PIN, 1, 1, 0.0\n"
        "N_RP, 1, 1, 0.0\n"
        "N_RP, 2, 2, 0.002540107\n"
        "*Output, field, frequency=1\n"
        "*Node Output\n"
        "U, RF\n"
        "*Output, history, frequency=1\n"
        "*Energy Output\n"
        "ALLSE, ALLWK\n"
        "*Node Output, nset=N_RP\n"
        "RF, U\n"
        "*End Step\n"
    )

    text = text + step4_block

    TEST_INP.write_text(text, encoding="utf-8", newline="\n")
    print(f"Created 4-step staggered test deck: {TEST_INP}")

if __name__ == "__main__":
    create_staggered_test_deck()

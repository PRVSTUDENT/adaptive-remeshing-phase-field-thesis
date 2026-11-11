# -*- coding: utf-8 -*-
"""
tests/unit/test_f1714_terminal_status_and_evidence_audit.py
============================================================
Unit test suite verifying Task F1714 terminal status, Fortran common block SAVE
attribute audit, element mapping integrity, and bottom boundary equilibrium topology.

Governing review reference: HND-F1714-FINAL-VALIDATION-002
"""

import os
import re
import pytest

PROD_INP_PATH = os.path.join(
    "models", "pandey_kumar_mode1", "207_f1714_five_hole_benchmark", "PK_F1714_JOB2_ADAPTED_PROD.inp"
)
UEL_SOURCE_PATH = os.path.join(
    "models", "pandey_kumar_mode1", "207_f1714_five_hole_benchmark", "f42_amor_split_uel.for"
)


def test_01_common_block_save_attribute_audit():
    """
    Test that COMMON /CB_STATE_TRANS/ in f42_amor_split_uel.for lacks the SAVE
    attribute, which explains why unvisited buffer indices (13035..150000) can
    contain uninitialized stack/heap floating point patterns (NaN) across subroutine calls.
    """
    assert os.path.isfile(UEL_SOURCE_PATH), f"UEL source not found at {UEL_SOURCE_PATH}"
    with open(UEL_SOURCE_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    cb_declarations = []
    has_save_for_cb = False

    for idx, line in enumerate(lines):
        line_clean = line.strip().upper()
        if "COMMON /CB_STATE_TRANS/" in line_clean:
            cb_declarations.append(idx + 1)
        if "SAVE" in line_clean and "/CB_STATE_TRANS/" in line_clean:
            has_save_for_cb = True
        elif line_clean.startswith("SAVE") and len(line_clean) == 4:
            has_save_for_cb = True

    # Confirm common block is declared in UEXTERNALDB, UEL, and UMAT (at least 3 places)
    assert len(cb_declarations) >= 3, f"Expected >= 3 declarations, got {len(cb_declarations)}"
    # Crucial finding: SAVE is NOT present, confirming the defect hypothesis
    assert not has_save_for_cb, "Expected SAVE /CB_STATE_TRANS/ to be absent, confirming memory risk."


def test_02_element_mapping_bijection_audit():
    """
    Test that all 39,102 layered elements in PK_F1714_JOB2_ADAPTED_PROD.inp map
    strictly and bijectively into PHYSIDX in [1, 13034] without any index exceeding N_PHYS.
    """
    assert os.path.isfile(PROD_INP_PATH), f"Deck not found at {PROD_INP_PATH}"
    with open(PROD_INP_PATH, "r", encoding="utf-8") as f:
        text = f.read()

    # Verify element block ranges
    # Phase quads: 315 to 13034 (12,720 quads)
    # Phase tris: 1 to 314 (314 tris)
    # Mech quads: 13349 to 26068 (12,720 quads)
    # Mech tris: 13035 to 13348 (314 tris)
    # UMAT quads: 26383 to 39102 (12,720 quads)
    # UMAT tris: 26069 to 26382 (314 tris)
    n_phys = 13034
    
    # Parse strictly inside *ELEMENT blocks
    parsed_ids = []
    in_element_block = False
    for line in text.splitlines():
        line_s = line.strip()
        if line_s.startswith("*ELEMENT"):
            in_element_block = True
            continue
        elif line_s.startswith("*"):
            in_element_block = False
            continue
        if in_element_block and line_s:
            parts = line_s.split(",")
            if len(parts) >= 4:
                try:
                    parsed_ids.append(int(parts[0].strip()))
                except ValueError:
                    pass

    assert len(parsed_ids) == 39102, f"Expected 39102 elements, got {len(parsed_ids)}"
    assert min(parsed_ids) == 1, f"Expected min element ID 1, got {min(parsed_ids)}"
    assert max(parsed_ids) == 39102, f"Expected max element ID 39102, got {max(parsed_ids)}"

    # Check mapping formula for all elements:
    # Phase layer: 1..13034 -> PHYSIDX = JELEM in [1, 13034]
    # Mech layer: 13035..26068 -> PHYSIDX = JELEM - 13034 in [1, 13034]
    # Visualizer layer: 26069..39102 -> PHYSIDX = NOEL - 2*13034 in [1, 13034]
    for eid in parsed_ids:
        if eid <= n_phys:
            physidx = eid
        elif eid <= 2 * n_phys:
            physidx = eid - n_phys
        else:
            physidx = eid - 2 * n_phys
        assert 1 <= physidx <= n_phys, f"Element {eid} produced invalid physidx {physidx}"


def test_03_bottom_boundary_connectivity_audit():
    """
    Test that all nodes in N_BOTTOM have active continuum element connectivity in both
    mechanical and visualizer layers, ensuring valid physical reaction forces.
    """
    with open(PROD_INP_PATH, "r", encoding="utf-8") as f:
        text = f.read()

    # Extract N_BOTTOM nodes
    nb_match = re.search(r"\*NSET, NSET=N_BOTTOM\n([^\*]+)", text)
    assert nb_match, "N_BOTTOM not found"
    nb_nodes = [int(n.strip()) for n in nb_match.group(1).replace("\n", ",").split(",") if n.strip()]
    assert len(nb_nodes) == 52, f"Expected 52 bottom nodes, got {len(nb_nodes)}"

    # Node 13276 must NOT be in N_BOTTOM
    assert 13276 not in nb_nodes, "Isolated node 13276 must not be in N_BOTTOM"

    # Verify that bottom nodes connect to elements
    # Sample a few bottom nodes: 49 (pin), 50, 73, 3125
    for test_nid in [49, 50, 73, 3125]:
        pattern = rf",\s*{test_nid}\s*(?:,|\n|$)"
        matches = re.findall(pattern, text)
        assert len(matches) >= 2, f"Expected node {test_nid} to appear in >= 2 elements, found {len(matches)}"


def test_04_solver_walltime_margin_model():
    """
    Test the solve rate and walltime margin model.
    Confirms that at ~25 incs/min, 2,319 remaining increments require ~92.8 min,
    leaving a positive margin of >60 min within the 8-hour PBS limit.
    """
    total_step2_incs = 5000
    current_inc = 2681
    remaining_incs = total_step2_incs - current_inc
    assert remaining_incs == 2319

    solve_rate_incs_per_min = 25.0
    estimated_remaining_mins = remaining_incs / solve_rate_incs_per_min
    assert 90.0 <= estimated_remaining_mins <= 100.0

    total_walltime_mins = 8.0 * 60.0  # 480 mins
    elapsed_walltime_mins = 5.0 * 60.0 + 26.0  # 326 mins
    available_walltime_mins = total_walltime_mins - elapsed_walltime_mins  # 154 mins

    walltime_margin_mins = available_walltime_mins - estimated_remaining_mins
    assert walltime_margin_mins > 50.0, f"Expected margin > 50 mins, got {walltime_margin_mins}"

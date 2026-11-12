"""
tests/unit/test_f1720_stage5_adapted_simulation.py
==================================================
Unit tests for Task F1720 Stage 5: Adapted Five-Hole Phase-Field Simulation
Model Assembly, Structural Parity, and Forward Execution.
"""

import os
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ADAPTED_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "214_f1720_adapted_mesh")
PROD_INP = os.path.join(ADAPTED_DIR, "PK_F1720_ADAPTED_PFM.inp")
ODB_PATH = os.path.join(ADAPTED_DIR, "PK_F1720_ADAPTED_PFM.odb")


def test_production_adapted_inp_exists():
    """Verify that the 3-layer production adapted input deck exists and is > 1 MB."""
    assert os.path.exists(PROD_INP), f"Adapted PFM input deck missing: {PROD_INP}"
    assert os.path.getsize(PROD_INP) > 1024 * 1024, "Adapted PFM INP size too small (< 1 MB)"


def test_three_layer_architecture_parity():
    """
    Verify that the input deck contains exactly 3 element layers with
    13,163 physical elements each (39,489 total elements).
    """
    n_phase_elems = 0
    n_mech_elems = 0
    n_umat_elems = 0
    in_phase = False
    in_mech = False
    in_umat = False

    with open(PROD_INP, "r") as f:
        for line in f:
            l = line.strip()
            if not l or l.startswith("**"):
                continue
            if l.startswith("*ELEMENT"):
                u = l.upper()
                in_phase = ("TYPE=U1" in u or "TYPE=U3" in u)
                in_mech = ("TYPE=U2" in u or "TYPE=U4" in u)
                in_umat = ("TYPE=CPE4" in u or "TYPE=CPE3" in u)
                continue
            elif l.startswith("*"):
                in_phase = in_mech = in_umat = False
                continue

            if in_phase:
                n_phase_elems += 1
            elif in_mech:
                n_mech_elems += 1
            elif in_umat:
                n_umat_elems += 1

    assert n_phase_elems == 13163, f"Expected 13163 phase elements, got {n_phase_elems}"
    assert n_mech_elems == 13163, f"Expected 13163 mech elements, got {n_mech_elems}"
    assert n_umat_elems == 13163, f"Expected 13163 UMAT elements, got {n_umat_elems}"


def test_kinematic_coupling_and_rp_node():
    """Verify that the reference point node (13402) and *EQUATION coupling exist."""
    has_rp_node = False
    has_equation = False

    with open(PROD_INP, "r") as f:
        for line in f:
            if "13402, 0.50000000, 1.00000000" in line:
                has_rp_node = True
            if "*EQUATION" in line.upper():
                has_equation = True

    assert has_rp_node is True, "Reference point node 13402 missing from deck"
    assert has_equation is True, "*EQUATION constraint missing from deck"


def test_material_and_coupling_parameters():
    """Verify that UMAT CONSTANTS=4 with SCALE_MODE=1.0 and UEL PROPERTIES=6."""
    has_props6 = False
    has_constants4 = False
    has_scale_mode_1 = False

    with open(PROD_INP, "r") as f:
        for line in f:
            if "*USER ELEMENT" in line.upper() and "PROPERTIES=6" in line.upper():
                has_props6 = True
            if "*USER MATERIAL" in line.upper() and "CONSTANTS=4" in line.upper():
                has_constants4 = True
            if "210.0, 0.3, 13163.0, 1.0" in line:
                has_scale_mode_1 = True

    assert has_props6 is True, "UEL PROPERTIES=6 missing"
    assert has_constants4 is True, "UMAT CONSTANTS=4 missing"
    assert has_scale_mode_1 is True, "UMAT SCALE_MODE=1.0 missing"


def test_adapted_simulation_odb_exists():
    """Verify that the adapted simulation ODB exists and has non-zero size."""
    assert os.path.exists(ODB_PATH), f"Adapted ODB missing: {ODB_PATH}"
    assert os.path.getsize(ODB_PATH) > 1024 * 1024, "Adapted ODB size too small (< 1 MB)"

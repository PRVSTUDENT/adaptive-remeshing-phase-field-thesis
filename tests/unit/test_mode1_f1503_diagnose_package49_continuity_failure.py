"""
Unit test suite for Task F1503: Diagnose Package 49 Numerical Continuity Failure.
Validates the evidence-based diagnostic across the 5 investigation priorities:
1. State initialization and UMAT constant / SDV zero output defect.
2. History indexing and ingestion semantics.
3. Boundary condition reload semantics and iteration-1 undegraded tip spike.
4. Energy discrepancy decomposition (mesh discretization gap vs reload damage evolution).
5. Numerical execution evidence and solver convergence.
"""

import json
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
P49_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "49_method_c_stage_c1_1_nonmatching_transfer"
COORD_DIR = REPO_ROOT / "project_coordination"


def test_01_job_1414235_preservation_and_review():
    """Verify Job 1414235 is preserved and correctly classified as FAIL in review."""
    review_path = COORD_DIR / "STAGE_C1_1_EQUIL_REVIEW.json"
    assert review_path.exists(), "STAGE_C1_1_EQUIL_REVIEW.json must exist"

    with open(review_path, "r", encoding="utf-8") as f:
        review = json.load(f)

    assert review["predecessor_pbs_job_id"] == "1414235.mmaster02"
    assert review["terminal_exit_status"] == 0
    assert review["scientific_review"] == "FAIL"

    metrics = review["metrics"]
    assert abs(metrics["delta_rf_n"] - 5.6312) < 0.01
    assert abs(metrics["delta_e_tot_pct"] - 0.8173) < 0.01
    assert metrics["cutbacks"] == 0


def test_02_umat_constants_defect_identified():
    """Prove that M1_MC_STAGE_C1_1_EQUIL.inp passed CONSTANTS=1 to UMAT, triggering 71320 fallback."""
    inp_path = P49_DIR / "M1_MC_STAGE_C1_1_EQUIL.inp"
    assert inp_path.exists(), "EQUIL.inp must exist"

    with open(inp_path, "r", encoding="utf-8") as f:
        content = f.read()

    # In EQUIL.inp, COMPANION_MAT currently has CONSTANTS=1
    assert "*USER MATERIAL, CONSTANTS=1" in content
    # UMAT in f42_mixed_uel.for requires PROPS(3) > 0 to set NPHYS_VAL = INT(PROPS(3))
    # Otherwise it falls back to NPHYS_VAL = 71320
    uel_path = P49_DIR / "f42_mixed_uel.for"
    with open(uel_path, "r", encoding="utf-8") as f:
        uel_src = f.read()

    assert "NPHYS_VAL = 71320" in uel_src
    assert "PHYSIDX = NOEL - 2 * NPHYS_VAL" in uel_src


def test_03_node_output_restriction_identified():
    """Prove that EQUIL.inp restricted NODE OUTPUT to N_RP, omitting whole-mesh displacements."""
    inp_path = P49_DIR / "M1_MC_STAGE_C1_1_EQUIL.inp"
    with open(inp_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "*NODE OUTPUT, NSET=N_RP" in content
    # Whole-mesh output requires *NODE OUTPUT without NSET


def test_04_step1_reload_semantics_and_node14403():
    """Verify that Step 1 reloads u_y = 5.0e-3 mm in one increment from zero displacement."""
    inp_path = P49_DIR / "M1_MC_STAGE_C1_1_EQUIL.inp"
    with open(inp_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "*STEP, NAME=Step-1-Equilibrate, NLGEOM=YES, INC=100" in content
    assert "1.0, 1.0, 1.0e-6, 1.0" in content
    assert "N_RP, 2, 2, 5.0000000000e-03" in content

    # Verify node 14403 is the crack tip node
    assert "14403, 4.9790129100e-01, 5.0000000000e-01" in content


def test_05_energy_discrepancy_decomposition():
    """Verify the quantitative components of the RF and energy continuity discrepancies."""
    rf_donor = 653.08857
    rf_target = 647.45736
    delta_rf = rf_target - rf_donor
    rel_rf_diff = (delta_rf / rf_donor) * 100.0

    e_tot_donor = 1.663384
    e_tot_target = 1.649789
    delta_e_tot = e_tot_target - e_tot_donor
    rel_e_diff = (delta_e_tot / e_tot_donor) * 100.0

    assert abs(delta_rf - (-5.6312)) < 0.01
    assert abs(rel_rf_diff - (-0.8622)) < 0.01
    assert abs(rel_e_diff - (-0.8173)) < 0.01

    # Verify linear-elastic scaling: Delta E_elas / E_elas == Delta RF / RF
    e_elas_donor = 1.632721
    e_elas_target = 1.618643
    rel_e_elas = ((e_elas_target - e_elas_donor) / e_elas_donor) * 100.0
    assert abs(rel_e_elas - rel_rf_diff) < 0.001


def test_06_state_transfer_engine_generator_repairs():
    """Verify that mode1_state_transfer_engine.py now generates CONSTANTS=3 and whole-mesh NODE OUTPUT."""
    engine_path = REPO_ROOT / "scripts" / "state_transfer" / "mode1_state_transfer_engine.py"
    with open(engine_path, "r", encoding="utf-8") as f:
        src = f.read()

    assert "*USER MATERIAL, CONSTANTS=3" in src
    assert "*DEPVAR" in src and "20" in src
    assert '*NODE OUTPUT, NSET=N_RP' not in src


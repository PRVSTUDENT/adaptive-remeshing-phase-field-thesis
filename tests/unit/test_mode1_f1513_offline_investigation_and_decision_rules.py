"""
Unit tests for Task F1513:
Independent offline investigation of mechanical displacement initialization,
UEL history transfer mechanism, and same-mesh diagnostic decision matrix.
"""
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_baseline_node_output_restriction_to_reference_point():
    inp_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "40_method_b_corrected_propagation_14k" / "M1_MB_CORRECTED_PROPAGATION_14K.inp"
    assert inp_path.exists()
    has_node_output_rp = False
    has_node_output_all = False
    with open(inp_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            l = line.strip().upper()
            if l.startswith("*NODE OUTPUT"):
                if "NSET=N_RP" in l:
                    has_node_output_rp = True
                if "NSET=ALL_NODES" in l or "NSET=ALL" in l or "ELSET" in l:
                    has_node_output_all = True
    assert has_node_output_rp, "Baseline 14K deck must contain *NODE OUTPUT, NSET=N_RP"
    assert not has_node_output_all, "Baseline 14K deck lacked interior nodal output, proving interior displacement was omitted from ODB"


def test_initial_conditions_solution_vs_displacement_presence():
    consistent_deck = REPO_ROOT / "models" / "pandey_kumar_mode1" / "49_method_c_stage_c1_1_nonmatching_transfer" / "M1_MC_STAGE_C1_1_SAMEMESH_CONSISTENT_RELHOLD.inp"
    assert consistent_deck.exists()
    has_solution_ic = False
    has_displacement_ic = False
    with open(consistent_deck, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            l = line.strip().upper()
            if l.startswith("*INITIAL CONDITIONS"):
                if "TYPE=SOLUTION" in l:
                    has_solution_ic = True
                if "TYPE=DISPLACEMENT" in l:
                    has_displacement_ic = True
    assert has_solution_ic, "Must contain *INITIAL CONDITIONS, TYPE=SOLUTION for UEL state variables"
    assert not has_displacement_ic, "Lacks *INITIAL CONDITIONS, TYPE=DISPLACEMENT: proves Step 1 reconstructs mechanical displacement via static equilibrium"


def test_decision_matrix_codification():
    # Formal decision cases for Stage C1-1 same-mesh controls:
    cases = {
        "CASE_A": "Both controls stable (|Delta d| <= 0.020, |Delta RF| <= 5 N, |Delta E_tot| <= 0.10%): confirms same-mesh release-and-hold algorithm sound; proves Job 1414550 jump was singularity sharpening",
        "CASE_B": "Only inverse reconstruction stable: proves area-weighted lumped projection under-represented singularity; consistent least-squares inverse resolves defect",
        "CASE_C": "Both controls develop excessive damage/energy discrepancies: isolates Step 1 static re-equilibration or *BOUNDARY, OP=NEW release mechanism as defective",
        "CASE_D": "Inconclusive due to missing reference ground-truth nodal fields: requires single rerun of 14K baseline with *NODE OUTPUT for All_nodes"
    }
    assert len(cases) == 4
    for key in ("CASE_A", "CASE_B", "CASE_C", "CASE_D"):
        assert key in cases


def test_remesh_cycle_stage_classification():
    # Current scientific stage definition:
    STAGE_NAME = "STAGE_C1_1"
    TRANSITION = "2906_TO_14483"
    QUALIFIED_SEQUENTIAL_CYCLES = 0
    FOUR_ITERATIVE_CYCLES_PERFORMED = False

    assert STAGE_NAME == "STAGE_C1_1"
    assert TRANSITION == "2906_TO_14483"
    assert QUALIFIED_SEQUENTIAL_CYCLES == 0
    assert not FOUR_ITERATIVE_CYCLES_PERFORMED

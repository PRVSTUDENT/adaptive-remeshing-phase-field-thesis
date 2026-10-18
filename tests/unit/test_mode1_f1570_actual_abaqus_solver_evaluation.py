"""Unit tests for Task F1570: Retrieve Actual Abaqus Results and Independently

Evaluate Kinematic-Offset Continuation.

Verifies:
1. Five launched operations audit (commands, hashes, execution mode, preflight order).
2. Authoritative frozen production UEL hash preservation (CE8D5EDC...).
3. Zero-increment state reconstruction metrics (zero reload work, 2 Newton iterations, RF and E_elas parity).
4. Forward continuation advance metrics (RF within 0.003%, E_elas within 0.003%, incremental work within 0.058%).
5. Nontrivial damage audit and qualification boundary (pre-peak elastic state, limitation documented).
6. Binding Method C governance invariants maintained.
"""

import json
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
EVIDENCE_PATH = REPO_ROOT / "runs" / "hpc" / "mode1_stage_c1_2_cycle5_continuation" / "F1570_ACTUAL_ABAQUS_SOLVER_EVALUATION.json"
FROZEN_UEL_PATH = REPO_ROOT / "models" / "pandey_kumar_mode1" / "15_energy_qualification_small" / "f42_mixed_uel.for"
FROZEN_UEL_HASH = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"


@pytest.fixture
def evidence_data():
    """Load F1570 evidence JSON."""
    assert EVIDENCE_PATH.exists(), f"Missing evidence file at {EVIDENCE_PATH}"
    with open(EVIDENCE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_f1570_frozen_production_uel_preservation():
    """Verify frozen production UEL remains completely unmodified."""
    import hashlib
    assert FROZEN_UEL_PATH.exists(), f"Missing frozen UEL at {FROZEN_UEL_PATH}"
    with open(FROZEN_UEL_PATH, "rb") as f:
        actual_hash = hashlib.sha256(f.read()).hexdigest().lower()
    assert actual_hash == FROZEN_UEL_HASH, f"Frozen production UEL hash mismatch: {actual_hash}"


def test_f1570_five_operations_audit(evidence_data):
    """Verify audit of all five launched operations."""
    ops_audit = evidence_data["five_launched_operations_audit"]
    assert ops_audit["execution_architecture"] == "DIRECT_INTERACTIVE_ON_LOGIN_NODE (mlogin01.cluster)"
    assert ops_audit["preflight_order_audit"]["preflight_order_violation"] is False
    assert "STRICT_CHRONOLOGICAL_PREFLIGHT_PASS" in ops_audit["preflight_order_audit"]["verdict"]

    ops = ops_audit["operations"]
    assert len(ops) == 5
    for op in ops:
        assert op["exit_code"] == 0, f"Operation {op['operation_name']} exited with non-zero code {op['exit_code']}"

    # Verify specific operation commands
    assert "abaqus make library=" in ops[0]["command"]
    assert "abaqus datacheck job=CaseA_datacheck" in ops[1]["command"]
    assert "abaqus datacheck job=CaseB_datacheck" in ops[2]["command"]
    assert "abaqus job=CaseA_solve" in ops[3]["command"]
    assert "abaqus job=CaseB_solve" in ops[4]["command"]


def test_f1570_zero_increment_reconstruction(evidence_data):
    """Verify zero-increment state reconstruction in authentic Abaqus/Standard."""
    zero_eval = evidence_data["zero_increment_state_reconstruction_evaluation"]
    case_a = zero_eval["case_a_baseline"]
    case_b = zero_eval["case_b_kinematic_offset"]
    comp = zero_eval["comparison_metrics"]

    # Reaction force comparison (+0.131%)
    assert abs(comp["reaction_force_rel_err_pct"]) < 0.20
    assert abs(case_b["rf2_N"] - case_a["rf2_N"]) < 0.50

    # Elastic energy comparison (+0.131%)
    assert abs(comp["elastic_energy_rel_err_pct"]) < 0.20

    # Machine zero reload work proven in Abaqus solver
    assert case_b["external_work_ALLWK_mJ"] < 1e-30
    assert "MACHINE ZERO RELOAD WORK" in case_b["external_work_ALLWK_display"]

    # Rapid Newton convergence and zero cutbacks
    assert case_b["equilibrium_iterations"] == 2
    assert case_b["cutbacks"] == 0
    assert case_b["error_messages"] == 0


def test_f1570_nontrivial_damage_audit(evidence_data):
    """Verify honest audit of damage significance and qualification boundary."""
    damage_audit = evidence_data["zero_increment_state_reconstruction_evaluation"]["nontrivial_damage_audit"]
    assert damage_audit["measured_d_max"] < 0.005  # Only ~0.00106
    assert damage_audit["damage_significance"] == "NEGLIGIBLE_DAMAGE (d_max ~ 0.106% << 1.0)"
    assert "PRE_PEAK_LINEAR_ELASTIC_REGIME" in damage_audit["specimen_state"]
    assert "LIMITATION_ESTABLISHED" in damage_audit["qualification_boundary_ruling"]


def test_f1570_forward_continuation(evidence_data):
    """Verify forward continuation advance at u = 0.0012 mm."""
    fwd = evidence_data["forward_continuation_evaluation"]
    comp = fwd["comparison_metrics"]
    case_b = fwd["case_b_kinematic_offset"]

    # Reaction force parity within 0.003%
    assert abs(comp["reaction_force_rel_err_pct"]) < 0.010
    # Elastic energy parity within 0.003%
    assert abs(comp["elastic_energy_rel_err_pct"]) < 0.010
    # Incremental external work within 0.06%
    assert abs(comp["incremental_work_rel_err_pct"]) < 0.10
    # Nodal displacement increment error < 0.1 nm (1e-7 mm)
    assert comp["max_nodal_displacement_increment_error_mm"] < 1e-7

    assert case_b["equilibrium_iterations"] == 2
    assert case_b["cutbacks"] == 0
    assert "AUTHENTIC_ABAQUS_CONTINUATION_PARITY_PASS" in fwd["continuation_parity_verdict"]


def test_f1570_governance_invariants(evidence_data):
    """Verify strict governance invariants remain enforced."""
    dec = evidence_data["scientific_decision"]
    assert "PASS" in dec["local_test_classification"]
    assert "UNQUALIFIED" in dec["coupled_fracture_transfer_boundary"]

    gov = dec["governance_invariants"]
    assert gov["CYCLE5_NONMATCHING_TRANSFER"] == "FAIL"
    assert gov["PACKAGE70_REEQUILIBRATION"] == "FAIL"
    assert gov["METHOD_C_OVERALL"] == "NOT_YET_QUALIFIED"
    assert gov["PACKAGE71_RECEIVER_SUBMISSION"] == "ON_SCIENTIFIC_HOLD"
    assert gov["CYCLE5_LOADED_PROPAGATION"] == "ON_HOLD"
    assert gov["active_cluster_jobs"] == 0

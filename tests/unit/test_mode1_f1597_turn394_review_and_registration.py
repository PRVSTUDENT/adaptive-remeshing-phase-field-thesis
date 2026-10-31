import json
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
REVIEW_JSON = REPO_ROOT / "results/validation/package157_r4_scientific_review_and_registration_handoff.json"
ENDPOINT_JSON = REPO_ROOT / "results/validation/step1_equilibrium_checkpoint_1419113_endpoint.json"


def test_review_files_exist():
    assert REVIEW_JSON.exists(), f"Review file {REVIEW_JSON} must exist"
    assert ENDPOINT_JSON.exists(), f"Endpoint file {ENDPOINT_JSON} must exist"


def test_displacement_convention_resolution():
    with open(REVIEW_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    crit = data["critical_boundary_displacement_resolution"]
    assert abs(crit["step1_equilibrium_uy_mm"] - 0.0018503125442191958) < 1e-12
    assert abs(crit["step2_target_uy_mm"] - 0.0019003125442191958) < 1e-12
    assert abs(crit["failed_span_nm"] - 50.0) < 1e-6
    assert crit["verified_top_nodes_tied_count"] == 85


def test_sub_increment_schedule_monotonicity():
    with open(REVIEW_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    sched = data["corrected_r4_schedule"]["recommended_primary_schedule"]["sub_steps"]
    assert len(sched) == 5

    prev_u = data["critical_boundary_displacement_resolution"]["step1_equilibrium_uy_mm"]
    for s in sched:
        assert s["target_uy_mm"] > prev_u, "Each sub-step must advance strictly forward (no retraction)"
        assert s["delta_uy_nm"] == 10.0
        prev_u = s["target_uy_mm"]

    # Final sub-step reaches exact failed step 2 target
    assert abs(sched[-1]["target_uy_mm"] - 0.0019003125442191958) < 1e-12


def test_registration_decision_and_invariants():
    with open(REVIEW_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    decision = data["execution_registration_decision"]
    assert decision["action"] == "ROUTE_FOR_OPERATION_REGISTRATION"
    assert decision["registration_blocker"] == "CURRENT_TASK_OPERATION_IS_RESEARCH_PREPARATION"
    assert decision["readiness"] == "PACKAGE157_R4_SCIENTIFICALLY_REVIEWED_AND_READY"

    # Invariants
    inv = data["driver_and_governance_invariants"]
    assert inv["frozen_uel_sha256"] == "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
    assert inv["pdas_active_set_solver"] == "EXACT_REUSE_UNMODIFIED"
    assert inv["convergence_tolerances"]["delta_d"] == 1.0e-5
    assert inv["convergence_tolerances"]["delta_h_mpa"] == 1.0e-6
    assert inv["convergence_tolerances"]["delta_u_mm"] == 1.0e-9
    assert inv["convergence_tolerances"]["signed_kkt"] == 1.0e-6

import json
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

RECEIPT_JSON = REPO_ROOT / "results/validation/package157_r4_registration_status_receipt.json"
INC_PATH = REPO_ROOT / "results/validation/step1_committed_solution_initial.inc"


@pytest.fixture(scope="module", autouse=True)
def run_verification():
    from scripts.validation.verify_package157_r4_registration_handoff import main
    main()


def test_receipt_exists():
    assert RECEIPT_JSON.exists(), f"{RECEIPT_JSON} must exist"
    assert INC_PATH.exists(), f"{INC_PATH} must exist"


def test_registration_status_receipt_content():
    with open(RECEIPT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["registration_status"] == "REGISTRATION_PENDING_REVIEW"
    assert data["target_operation_id"] == "execute_mode1_package157_c1_2_r4_adaptive_continuation"
    assert data["present_in_controller_operations"] is False
    assert data["frozen_uel_verified"] is True
    assert data["authentic_solution_cards_sha256"] == "306ABF3C09FAA9CB9CEA37F48B8E93A8509C0FF0D0258E9B47667367D9808F60"


def test_locked_experiment_definition():
    with open(RECEIPT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    exp = data["locked_experiment_definition"]
    assert exp["candidate_experiment_id"] == "M1_C4_P150_C1_2_R4"
    assert abs(exp["baseline_displacement_uy_mm"] - 0.0018503125442191958) < 1e-12
    assert exp["initial_forward_substeps_nm"] == [10.0, 10.0, 10.0, 10.0, 10.0]
    assert exp["minimum_subdivision_increment_nm"] == 5.0

    crit = exp["acceptance_criteria"]
    assert crit["delta_H_tol_MPa"] == 1e-6
    assert crit["delta_d_tol"] == 1e-5
    assert crit["delta_u_tol_mm"] == 1e-9
    assert crit["signed_kkt_tol_MPa"] == 1e-6
    assert crit["zero_damage_healing_enforced"] is True
    assert crit["monotonic_history_enforced"] is True

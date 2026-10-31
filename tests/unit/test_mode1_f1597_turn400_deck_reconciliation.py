import json
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

RECON_JSON = REPO_ROOT / "results/validation/mode1_c4_deck_kinematics_and_coordinate_reconciliation.json"
RECEIPT_JSON = REPO_ROOT / "results/validation/package157_r4_registration_status_receipt.json"
DECK_PATH = REPO_ROOT / "models/pandey_kumar_mode1/150_c4_package150_c1_2_continuation/M1_C4_PACKAGE150_C1_2_CONTINUATION.inp"


@pytest.fixture(scope="module", autouse=True)
def ensure_audit_run():
    from scripts.validation.audit_mode1_c4_deck_coordinates_and_kinematics import main
    main()


def test_reconciliation_json_exists():
    assert RECON_JSON.exists(), f"{RECON_JSON} must exist"
    assert RECEIPT_JSON.exists(), f"{RECEIPT_JSON} must exist"
    assert DECK_PATH.exists(), f"{DECK_PATH} must exist"


def test_reference_point_reconciliation():
    with open(RECON_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    rp = data["reference_point_reconciliation"]
    assert rp["deck_reference_point_node_id"] == 999999
    assert rp["deck_reference_point_coordinates_mm"] == [0.05, 0.1]
    assert rp["tied_top_node_count"] == 85
    assert rp["narrative_claim_node_id"] == 1000001


def test_crack_tip_coordinate_reconciliation():
    with open(RECON_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    ct = data["crack_tip_coordinate_reconciliation"]
    assert ct["domain_dimensions_mm"] == [0.1, 0.1]
    assert ct["initial_slit_length_a0_mm"] == 0.04
    assert ct["slit_tip_node_7265_coords_mm"] == [0.04, 0.05]
    assert ct["peak_damage_node_3612_coords_mm"] == [0.04136, 0.05]
    assert abs(ct["distance_from_slit_tip_to_node_3612_mm"] - 0.00136) < 1e-8


def test_prerequisites_for_r4_dispatch():
    with open(RECON_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    prereq = data["prerequisites_for_r4_dispatch"]
    assert prereq["registration_status"] == "REGISTRATION_PENDING_REVIEW"
    assert prereq["operation_id"] == "execute_mode1_package157_c1_2_r4_adaptive_continuation"
    assert prereq["required_binding_file"] == "scripts/controller/Controller-Operations.ps1"
    assert prereq["scientific_baseline_reconciled"] is True

import json
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

CONTROLLER_OPS = REPO_ROOT / "scripts/controller/Controller-Operations.ps1"
RECEIPT_JSON = REPO_ROOT / "results/validation/package157_r4_registration_status_receipt.json"
REVIEW_JSON = REPO_ROOT / "results/validation/package157_r4_scientific_review_and_registration_handoff.json"
AUDIT_JSON = REPO_ROOT / "results/validation/authentic_step1_history_audit.json"
SOL_INC = REPO_ROOT / "results/validation/step1_committed_solution_initial.inc"
RECON_JSON = REPO_ROOT / "results/validation/mode1_c4_deck_kinematics_and_coordinate_reconciliation.json"


def test_authoritative_artifacts_exist():
    assert CONTROLLER_OPS.exists(), f"{CONTROLLER_OPS} must exist"
    assert RECEIPT_JSON.exists(), f"{RECEIPT_JSON} must exist"
    assert REVIEW_JSON.exists(), f"{REVIEW_JSON} must exist"
    assert AUDIT_JSON.exists(), f"{AUDIT_JSON} must exist"
    assert SOL_INC.exists(), f"{SOL_INC} must exist"
    assert RECON_JSON.exists(), f"{RECON_JSON} must exist"


def test_reviewed_registration_now_present_preserving_historical_blocker():
    text = CONTROLLER_OPS.read_text(encoding="utf-8")
    assert "execute_mode1_package157_c1_2_r4_adaptive_continuation" in text


def test_registration_blocker_status():
    with open(RECEIPT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["registration_status"] == "REGISTRATION_PENDING_REVIEW"
    assert data["target_operation_id"] == "execute_mode1_package157_c1_2_r4_adaptive_continuation"
    assert data["present_in_controller_operations"] is False
    assert data["frozen_uel_verified"] is True

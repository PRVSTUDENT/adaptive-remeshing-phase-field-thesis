"""Unit tests for F1597 HPC Offline Blocker Diagnosis and Candidate Donor Preflight."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest
from scripts.validation.audit_f1597_hpc_offline_blocker_and_donor_preflight import (
    diagnose_offline_blocker,
    verify_candidate_donor_preflight,
    run_full_offline_blocker_audit,
    EXPECTED_DONOR_SHA256,
    EXPECTED_UEL_SHA256,
    sha256_file,
    CANDIDATE_DONOR_PATH,
    PRODUCTION_UEL_PATH,
)


def test_offline_blocker_diagnosis():
    diag = diagnose_offline_blocker()
    assert "layer1_local_guard" in diag
    assert "layer2_network_gateway" in diag
    assert diag["blocker_classification"] == "PHYSICAL_VPN_GATEWAY_OUTAGE_AND_FAIL_CLOSED_GUARD"
    assert diag["layer2_network_gateway"]["vpn_host"] == "vpn.tu-freiberg.de"
    assert diag["layer2_network_gateway"]["vpn_ip"] == "139.20.202.130"


def test_candidate_donor_preflight():
    donor = verify_candidate_donor_preflight()
    assert donor["deck_hash_verified"] is True
    assert donor["uel_hash_verified"] is True
    assert donor["elements_count"] == 1600
    assert donor["nodes_count"] == 1698
    assert donor["nominal_h_um"] == 2.5
    assert donor["physical_length_scale_l0_um"] == 7.5
    assert abs(donor["resolution_ratio_l0_over_h"] - 3.0) < 1e-6
    assert abs(donor["coarse_donor_resolution_ratio_l0_over_h"] - 1.5) < 1e-6
    assert donor["preflight_passed"] is True


def test_production_uel_and_candidate_deck_hashes():
    assert sha256_file(PRODUCTION_UEL_PATH) == EXPECTED_UEL_SHA256
    assert sha256_file(CANDIDATE_DONOR_PATH) == EXPECTED_DONOR_SHA256


def test_full_offline_blocker_audit():
    import json
    res = run_full_offline_blocker_audit()
    assert res["schema"] == 1
    assert res["task_id"] == "F1597-CORRECT-PACKAGE72-STATE-TRANSFER"
    assert res["status"] == "PREPARATION_COMPLETE"
    assert res["verification_passed"] is True
    assert len(res["finding"]) >= 20
    assert res["classification"] == "HPC_BLOCKER_RESOLVED_TO_VPN_GATEWAY_OUTAGE__DONOR_PREFLIGHT_VERIFIED"
    assert res["candidate_donor_preflight"]["preflight_passed"] is True

    # Save to results/validation
    out_file = REPO_ROOT / "results/validation/f1597_hpc_offline_blocker_and_donor_preflight_audit.json"
    res["evidence_sources"]["scripts/validation/audit_f1597_hpc_offline_blocker_and_donor_preflight.py"] = sha256_file(REPO_ROOT / "scripts/validation/audit_f1597_hpc_offline_blocker_and_donor_preflight.py")
    res["evidence_sources"]["tests/unit/test_mode1_f1597_hpc_offline_blocker_and_donor_preflight.py"] = sha256_file(Path(__file__).resolve())
    out_text = json.dumps(res, indent=2).replace("\r\n", "\n") + "\n"
    out_file.write_bytes(out_text.encode("utf-8"))
    assert out_file.exists()

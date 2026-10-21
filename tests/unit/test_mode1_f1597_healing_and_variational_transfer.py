"""Unit tests for F1597 Healing Mechanism and PDAS State Transfer Audit."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest
from scripts.validation.audit_f1597_healing_and_variational_transfer import (
    diagnose_pkg72_healing_mechanism,
    verify_pdas_variational_remedy,
    verify_candidate_donor_physical_integrity,
    run_full_healing_and_variational_audit,
    EXPECTED_DONOR_SHA256,
    EXPECTED_UEL_SHA256,
    sha256_file,
    CANDIDATE_DONOR_PATH,
    PRODUCTION_UEL_PATH,
)


def test_package72_healing_mechanism_diagnosis():
    diag = diagnose_pkg72_healing_mechanism()
    assert diag["total_receiver_nodes"] == 713
    assert diag["healing_nodes_count"] == 291
    assert abs(diag["healing_fraction_pct"] - 40.813464) < 1e-4
    assert abs(diag["min_delta_d"] - (-0.0016612791)) < 1e-6
    assert diag["mechanism_classification"] == "UNCONSTRAINED_LINEAR_PHASE_SOLVE_RESIDUAL_DEFECT"


def test_pdas_variational_remedy():
    pdas = verify_pdas_variational_remedy()
    # Unconstrained has healing
    assert pdas["unconstrained_min_delta_d"] < -1e-6
    assert pdas["unconstrained_healing_nodes"] > 0
    # PDAS has ZERO healing
    assert pdas["pdas_min_delta_d"] >= -1e-12
    assert pdas["pdas_healing_nodes"] == 0
    assert pdas["pdas_enforcement_verified"] is True


def test_candidate_donor_physical_integrity():
    donor = verify_candidate_donor_physical_integrity()
    assert donor["deck_hash_verified"] is True
    assert donor["uel_hash_verified"] is True
    assert donor["elements_count"] == 1600
    assert donor["nodes_count"] == 1698
    assert donor["nominal_h_um"] == 2.5
    assert donor["physical_length_scale_l0_um"] == 7.5
    assert abs(donor["resolution_ratio_l0_over_h"] - 3.0) < 1e-6
    assert abs(donor["resolution_improvement_factor"] - 2.0) < 1e-6
    assert donor["physical_conformance_pass"] is True


def test_production_uel_bitwise_integrity():
    assert sha256_file(PRODUCTION_UEL_PATH) == EXPECTED_UEL_SHA256
    assert sha256_file(CANDIDATE_DONOR_PATH) == EXPECTED_DONOR_SHA256


def test_full_healing_and_variational_audit():
    import json
    audit = run_full_healing_and_variational_audit()
    assert audit["schema"] == 1
    assert audit["task_id"] == "F1597-CORRECT-PACKAGE72-STATE-TRANSFER"
    assert audit["status"] == "PREPARATION_COMPLETE"
    assert audit["verification_passed"] is True
    assert len(audit["finding"]) >= 20
    assert audit["classification"] == "PACKAGE72_HEALING_MECHANISM_PROVED_AND_PDAS_VERIFIED"
    assert audit["healing_diagnosis"]["healing_nodes_count"] == 291
    assert audit["pdas_remedy"]["pdas_enforcement_verified"] is True

    # Save to results/validation
    out_file = REPO_ROOT / "results/validation/f1597_healing_and_variational_transfer_audit.json"
    audit["evidence_sources"]["scripts/validation/audit_f1597_healing_and_variational_transfer.py"] = sha256_file(REPO_ROOT / "scripts/validation/audit_f1597_healing_and_variational_transfer.py")
    audit["evidence_sources"]["tests/unit/test_mode1_f1597_healing_and_variational_transfer.py"] = sha256_file(Path(__file__).resolve())
    out_text = json.dumps(audit, indent=2).replace("\r\n", "\n") + "\n"
    out_file.write_bytes(out_text.encode("utf-8"))
    assert out_file.exists()

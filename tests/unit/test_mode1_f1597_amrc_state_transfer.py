"""Unit tests for F1597 AMRC-informed Method C state transfer and re-equilibration.

Tests:
1. Production UEL f42_mixed_uel.for hash preservation (bitwise frozen).
2. Candidate donor and C2 receiver mesh file integrity.
3. AMRC KDTree active-zone tagging and process-band identification.
4. AMRC-adapted inequality bound transfer ensuring zero healing nodes.
5. Kuhn-Tucker history field non-negativity across all Gauss points.
6. Bourdin AT2 fracture energy continuity (|Delta Gamma| / Gamma <= 2.0%).
7. 2-step re-equilibration deck structure resolving Abaqus Section 34.2.1.
8. AMRC attribution and MIT license compliance.
"""
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.validation.audit_f1597_amrc_state_transfer import (
    execute_f1597_amrc_state_transfer_audit,
    sha256_file,
    PRODUCTION_UEL_PATH,
    EXPECTED_UEL_SHA256,
    CANDIDATE_DONOR_PATH,
    EXPECTED_DONOR_SHA256,
    CANDIDATE_C2_PATH,
    EXPECTED_C2_SHA256,
    AMRC_UPSTREAM_COMMIT,
    AMRC_LICENSE,
    REEQUILIBRATION_DECK_PATH
)


@pytest.fixture(scope="module")
def audit_results():
    return execute_f1597_amrc_state_transfer_audit()


def test_production_uel_hash_preservation():
    """Verify production UEL f42_mixed_uel.for remains 100% bitwise frozen."""
    assert PRODUCTION_UEL_PATH.exists(), f"Missing production UEL: {PRODUCTION_UEL_PATH}"
    uel_hash = sha256_file(PRODUCTION_UEL_PATH)
    assert uel_hash == EXPECTED_UEL_SHA256, f"UEL hash modified! Expected {EXPECTED_UEL_SHA256}, got {uel_hash}"


def test_mesh_file_integrity():
    """Verify donor and receiver mesh input decks are bitwise identical to qualified hashes."""
    assert CANDIDATE_DONOR_PATH.exists(), f"Missing donor deck: {CANDIDATE_DONOR_PATH}"
    assert CANDIDATE_C2_PATH.exists(), f"Missing C2 deck: {CANDIDATE_C2_PATH}"
    assert sha256_file(CANDIDATE_DONOR_PATH) == EXPECTED_DONOR_SHA256
    assert sha256_file(CANDIDATE_C2_PATH) == EXPECTED_C2_SHA256


def test_amrc_kdtree_active_zone_tagging(audit_results):
    """Verify AMRC KDTree identifies crack process band refinement elements."""
    metrics = audit_results["amrc_integration_metrics"]
    assert metrics["donor_active_points_count"] > 0
    assert metrics["tagged_refinement_elements_in_c2"] > 0
    # Process band elements must be significant fraction of C2
    assert metrics["tagged_refinement_elements_in_c2"] >= 1500
    assert metrics["c2_total_physical_elements"] == 2300


def test_inequality_bound_zero_healing(audit_results):
    """Verify inequality bound transfer strictly prevents damage healing."""
    metrics = audit_results["amrc_integration_metrics"]
    assert metrics["inequality_bound_healing_node_count"] == 0
    assert metrics["min_delta_damage"] >= 0.0


def test_kuhn_tucker_history_positivity(audit_results):
    """Verify Kuhn-Tucker strain history field H >= 0 across all Gauss points."""
    metrics = audit_results["amrc_integration_metrics"]
    assert metrics["negative_history_count"] == 0
    assert metrics["min_history_value"] >= 0.0


def test_fracture_energy_continuity(audit_results):
    """Verify Bourdin AT2 fracture energy continuity within 2.0%."""
    metrics = audit_results["amrc_integration_metrics"]
    assert metrics["fracture_energy_continuity_pass"] is True
    assert metrics["fracture_energy_relative_error_pct"] <= 2.0


def test_two_step_reequilibration_structure(audit_results):
    """Verify 2-step re-equilibration deck contains solution ICs and Step 1/Step 2."""
    assert REEQUILIBRATION_DECK_PATH.exists()
    content = REEQUILIBRATION_DECK_PATH.read_text(encoding="utf-8")
    assert "*INITIAL CONDITIONS, TYPE=SOLUTION" in content
    assert "*STEP, NAME=Step-1-ReEquilibrate" in content
    assert "*STEP, NAME=Step-2-ForwardContinue" in content
    assert "*BOUNDARY, OP=NEW" in content


def test_amrc_upstream_metadata(audit_results):
    """Verify AMRC upstream commit and MIT license attribution."""
    metrics = audit_results["amrc_integration_metrics"]
    assert metrics["amrc_upstream_commit"] == "71aaceac455cd3683682f61ae37f1b71d0cd5e6a"
    assert "MIT License" in metrics["amrc_license"]
    assert "Aarosh Dahal" in metrics["amrc_license"]

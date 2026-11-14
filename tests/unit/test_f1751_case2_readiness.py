"""
Unit and regression test suite for Task F1751:
Case 2 Method A Off-Axis Hole Damage Resolution and Continuation Readiness Diagnosis.

Verifies:
1. Zero PBS submissions consumed (0 new, 25 cumulative preserved).
2. Frozen UEL bitwise preserved (CE8D5EDC...).
3. Primary crack process-zone spatial resolution and hole bridging (>=85% area compliance h <= l0/2).
4. Secondary ligament damage activation and critical Node 8056 DOF 3 divergence.
5. Terminal cutback sequence (13 cutbacks) and dt_min = 1.0e-8 exhaustion.
6. Hypotheses evaluation and falsifiable continuation proposal.
"""

import os
import json
import pytest

SUMMARY_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "results", "validation", "f1751_case2_diagnosis_summary.json"
)


@pytest.fixture(scope="module")
def summary_data():
    assert os.path.exists(SUMMARY_PATH), f"Summary JSON not found: {SUMMARY_PATH}"
    with open(SUMMARY_PATH, "r") as f:
        return json.load(f)


def test_f1751_governance_and_zero_pbs(summary_data):
    """
    Verifies strict zero-PBS governance and frozen production UEL.
    """
    assert summary_data["task_id"] == "F1751-CASE2-METHOD-A-DAMAGE-RESOLUTION-AND-CONTINUATION-READINESS"
    assert summary_data["diagnostic_status"] == "COMPLETE"
    assert summary_data["scientific_classification"] == "CASE2_METHOD_A_READINESS_DIAGNOSIS_COMPLETE"
    
    gov = summary_data["governance"]
    assert gov["new_pbs_submissions"] == 0
    assert gov["cumulative_pbs_submissions"] == 25
    assert gov["frozen_uel_sha256"] == "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
    assert gov["total_physical_elements"] == 23965


def test_f1751_primary_crack_resolution_and_bridging(summary_data):
    """
    Verifies that the primary crack achieved >=85% area compliance with h <= l0/2
    and bridged all the way to intersect the off-axis hole boundary.
    """
    pz = summary_data["spatial_process_zone_resolution"]
    severed = pz["severed_channel_d90"]
    core = pz["core_failure_d95"]
    
    # Area compliance in severed channel exceeds the 85% qualification gate
    assert severed["area_compliance_l0_half_pct"] >= 85.0, (
        f"Severed area compliance ({severed['area_compliance_l0_half_pct']:.2f}%) below 85% gate"
    )
    assert severed["count_compliance_l0_half_pct"] >= 95.0
    assert core["area_compliance_l0_half_pct"] >= 85.0
    
    conn = summary_data["crack_connectivity_and_trajectory"]
    assert conn["primary_ligament_bridged"] is True
    assert conn["hole_intersecting_elements_count"] >= 5


def test_f1751_secondary_ligament_activation_and_node_8056(summary_data):
    """
    Verifies secondary ligament damage activation and local mesh gradient at Node 8056.
    """
    conn = summary_data["crack_connectivity_and_trajectory"]
    assert conn["secondary_ligament_max_damage"] >= 0.95
    assert conn["secondary_active_d50_count"] > 0
    
    n8056 = summary_data["critical_node_8056_investigation"]
    assert n8056["node_id"] == 8056
    assert 0.89 <= n8056["coordinates"][0] <= 0.92
    assert 0.62 <= n8056["coordinates"][1] <= 0.65
    
    # Connected elements are in process zone with h > l0/2 (local mesh gradient)
    for elem in n8056["connected_element_details"]:
        assert elem["damage_d"] >= 0.50
        assert elem["size_vs_l0_half"] >= 1.0


def test_f1751_terminal_cutback_and_dt_min(summary_data):
    """
    Verifies the terminal cutback sequence and dt_min exhaustion.
    """
    term = summary_data["terminal_cutback_and_convergence_analysis"]
    assert term["total_cutbacks_recorded"] == 13
    assert term["reached_dt_min"] is True
    assert term["terminal_dt"] == 1.0e-8


def test_f1751_hypotheses_and_continuation_decision(summary_data):
    """
    Verifies the root cause hypotheses verdicts and continuation readiness proposal.
    """
    hyp = summary_data["hypotheses_verdicts"]
    assert hyp["hypothesis_1_coarse_mesh_arrest"]["verdict"] == "SECONDARY_FACTOR"
    assert hyp["hypothesis_2_damaged_state_ill_conditioning"]["verdict"] == "CONTRIBUTING_FACTOR"
    assert hyp["hypothesis_3_time_stepping_cutback_exhaustion"]["verdict"] == "PRIMARY_DIRECT_CAUSE"
    
    decision = summary_data["continuation_decision"]
    assert decision["continuation_readiness"] == "CONDITIONAL_PASS_WITH_SOLVER_CONTROLS_RELAXATION"
    assert decision["recommended_action"] == "BOUNDED_CONTINUATION_WITH_RELAXED_DT_MIN"
    
    proposal = decision["proposed_falsifiable_experiment"]
    assert proposal["proposal_id"] == "EXP-F1752-CASE2-CONTINUATION-BOUNDED"
    assert proposal["frozen_uel"] == "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
    assert proposal["max_pbs_submissions"] == 1
    assert len(proposal["predeclared_success_gates"]) == 4

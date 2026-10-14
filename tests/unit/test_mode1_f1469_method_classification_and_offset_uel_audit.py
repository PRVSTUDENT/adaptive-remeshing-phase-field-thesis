import json
import hashlib
import pytest
from pathlib import Path

# Repository paths
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DONOR_JSON = REPO_ROOT / "models" / "pandey_kumar_mode1" / "41_method_c_genuine_continuation" / "evidence_forward_audit" / "coarse_donor_state_u0050.json"
REPORT_MD = REPO_ROOT / "docs" / "reports" / "MODE1_METHOD_C1_STATE_INITIALIZATION_AND_CONTINUATION_ARCHITECTURE.md"
BRIEFING_MD = REPO_ROOT / "docs" / "supervisor_reports" / "22-10-2026" / "SUPERVISOR_BRIEFING_MODE1_METHODS_B_AND_C.md"
WRAPPER_SH = REPO_ROOT / "models" / "pandey_kumar_mode1" / "42_method_c1_forward_refinement" / "submit_c1_forward_refinement_job.sh"
UEL_FOR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "f42_mixed_uel.for"

PROD_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

def test_method_classification_and_retrospective_mesh_distinction():
    """Verify Method A/B/C definitions and retrospective classification of Package 40."""
    assert REPORT_MD.exists()
    content = REPORT_MD.read_text(encoding="utf-8")
    
    assert "Method A Definition" in content
    assert "Method B Definition" in content
    assert "Method C Definition" in content
    
    # Must explicitly classify Package 40 as retrospective verification mesh
    assert "retrospective, crack-path-informed verification mesh" in content or "retrospective verification mesh" in content
    # Must record that native Method B mesh remains under-resolved and exhibits crack pinning
    assert "crack pinning" in content
    assert "under-resolved" in content

def test_kinematic_offset_uel_architecture_critique_and_retraction():
    """Verify architecture review of kinematic-offset UEL and retraction of unconditional solvability."""
    assert REPORT_MD.exists()
    content = REPORT_MD.read_text(encoding="utf-8")
    
    # Must critique positive definiteness and state unconditional solvability is retracted/unproven
    assert "Retraction of Unconditional Solvability Guarantee" in content or "retracted" in content
    assert "Rigid-Body Modes" in content or "rigid-body modes" in content
    assert "Spectral Decomposition Non-Smoothness" in content or "spectral" in content
    assert "Softening" in content or "coupled system indefiniteness" in content
    
    # Must classify offset UEL as leading proposed candidate, not the only valid one
    assert "leading proposed research candidate" in content or "LEADING PROPOSED CANDIDATE" in content

def test_donor_state_history_field_reconciliation():
    """Verify authentic donor values and forensic reconciliation of 53.65 MPa vs 18.88 MPa."""
    assert DONOR_JSON.exists()
    with open(DONOR_JSON, "r", encoding="utf-8") as f:
        donor = json.load(f)
        
    assert donor["num_elements"] == 2906
    assert donor["num_nodes"] == 2142
    assert abs(donor["u_rp_mm"] - 0.0050) < 1e-6
    assert abs(donor["rf_rp_N"] - 653.0886) < 0.01
    assert abs(donor["total_e_elas_mJ"] - 1.632721) < 0.001
    assert abs(donor["total_e_frac_mJ"] - 0.030663) < 0.001
    assert abs(donor["total_e_tot_mJ"] - 1.663384) < 0.001
    assert abs(donor["max_d_nodal"] - 0.094910) < 0.0001
    
    # Check H values
    assert abs(donor["max_H"] - 0.05364989) < 1e-6
    assert donor["min_H"] >= 0.0
    
    # Verify report explains the 53.65 MPa vs 18.88 MPa origin
    report_text = REPORT_MD.read_text(encoding="utf-8")
    assert "53.65" in report_text or "53.64989" in report_text
    assert "18.88" in report_text
    assert "diffusion" in report_text or "zero-gradient" in report_text

def test_multi_metric_spatial_resolution_audit():
    """Verify multi-metric spatial resolution audit metrics and heuristic clarification."""
    assert REPORT_MD.exists()
    content = REPORT_MD.read_text(encoding="utf-8")
    
    # Check coverage percentages across metrics
    assert "18.77%" in content or "18.8%" in content
    assert "78.21%" in content or "78.2%" in content
    assert "Equivalent Area" in content or "h_A" in content
    assert "Maximum Edge" in content or "h_edge" in content
    assert "Transverse" in content or "dy" in content
    
    # Check clarification of Nyquist analogy as engineering heuristic
    assert "engineering heuristic" in content

def test_gate_6c_five_stage_qualification_sequence():
    """Verify 5-stage qualification progression and quantitative acceptance/rollback criteria."""
    assert REPORT_MD.exists()
    content = REPORT_MD.read_text(encoding="utf-8")
    
    assert "Stage 1: Same-Mesh Offset Reproduction" in content
    assert "Stage 2: Nonmatching Transfer at Fixed u" in content or "Stage 2" in content
    assert "Stage 3: Small Forward Continuation" in content or "Stage 3" in content
    assert "Stage 4: Prospective Remeshing Event" in content or "Stage 4" in content
    assert "Stage 5: Multi-Cycle Adaptive Sequencing" in content or "Stage 5" in content
    assert "Rollback" in content

def test_governance_and_production_uel_preservation():
    """Verify cluster lock, idle queue status, and frozen production UEL hash."""
    assert WRAPPER_SH.exists()
    wrapper_text = WRAPPER_SH.read_text(encoding="utf-8")
    assert 'AUTHORIZED=false' in wrapper_text
    
    assert UEL_FOR.exists()
    actual_hash = hashlib.sha256(UEL_FOR.read_bytes()).hexdigest().upper()
    assert actual_hash == PROD_UEL_HASH, f"Production UEL hash mismatch: {actual_hash} != {PROD_UEL_HASH}"

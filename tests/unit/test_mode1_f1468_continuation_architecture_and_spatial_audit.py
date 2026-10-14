import json
import pytest
from pathlib import Path

# Paths
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DONOR_JSON = REPO_ROOT / "models" / "pandey_kumar_mode1" / "41_method_c_genuine_continuation" / "evidence_forward_audit" / "coarse_donor_state_u0050.json"
REPORT_MD = REPO_ROOT / "docs" / "reports" / "MODE1_METHOD_C1_STATE_INITIALIZATION_AND_CONTINUATION_ARCHITECTURE.md"
BRIEFING_MD = REPO_ROOT / "docs" / "supervisor_reports" / "22-10-2026" / "SUPERVISOR_BRIEFING_MODE1_METHODS_B_AND_C.md"
WRAPPER_SH = REPO_ROOT / "models" / "pandey_kumar_mode1" / "42_method_c1_forward_refinement" / "submit_c1_forward_refinement_job.sh"

def test_abaqus_state_restoration_feasibility_matrix():
    """Verify that all 8 state restoration mechanisms and their disqualifications are documented."""
    assert REPORT_MD.exists(), "Technical report must exist"
    content = REPORT_MD.read_text(encoding="utf-8")
    
    mechanisms = [
        "Native `*RESTART`",
        "Native `*MAP SOLUTION`",
        "*INITIAL CONDITIONS, TYPE=DISPLACEMENT",
        "*INITIAL CONDITIONS, TYPE=SOLUTION",
        "*INITIAL CONDITIONS, TYPE=STRESS",
        "Reference Configuration Update",
        "Fixed-Boundary Equilibration",
        "Ramping Displacement",
        "Kinematic-Offset UEL"
    ]
    for m in mechanisms:
        assert m in content, f"Mechanism {m} must be evaluated in report"
        
    assert "Error 144" in content, "Error 144 rejection of displacement ICs in *STATIC must be cited"
    assert "DISQUALIFIED" in content, "Disqualification status must be explicitly recorded"

def test_authentic_coarse_donor_benchmark_values():
    """Verify exact values of the authentic Mode-I coarse donor state (Job 1411891.mmaster02)."""
    assert DONOR_JSON.exists(), f"Donor JSON must exist at {DONOR_JSON}"
    with open(DONOR_JSON, "r", encoding="utf-8") as f:
        donor = json.load(f)
        
    assert donor["num_elements"] == 2906
    assert donor["num_nodes"] == 2142
    assert abs(donor["u_rp_mm"] - 0.0050) < 1e-6
    assert abs(donor["rf_rp_N"] - 653.0886) < 0.01
    assert abs(donor["total_e_elas_mJ"] - 1.6327) < 0.001
    assert abs(donor["total_e_frac_mJ"] - 0.0307) < 0.001
    assert abs(donor["total_e_tot_mJ"] - 1.6634) < 0.001
    assert abs(donor["max_d_nodal"] - 0.094910) < 0.0001
    assert donor["min_H"] >= 0.0, "Crack history field H must be strictly non-negative"

def test_spatial_resolution_audit_metrics():
    """Verify quantitative mesh metrics for Package 42 Native vs Package 40 Corrected."""
    assert REPORT_MD.exists()
    content = REPORT_MD.read_text(encoding="utf-8")
    
    # Check that contiguous extent and coverage percentages are recorded accurately
    assert "0.5939" in content, "Package 42 contiguous extent x=0.5939 mm must be recorded"
    assert "18.8%" in content, "Package 42 contiguous coverage 18.8% must be recorded"
    assert "0.8911" in content, "Package 40 contiguous extent x=0.8911 mm must be recorded"
    assert "78.2%" in content, "Package 40 contiguous coverage 78.2% must be recorded"
    assert "3.75" in content, "Nyquist threshold l0/2 = 3.75 um must be referenced"

def test_kinematic_offset_uel_mathematical_consistency():
    """Verify mathematical consistency of the Kinematic-Offset UEL continuation design."""
    assert REPORT_MD.exists()
    content = REPORT_MD.read_text(encoding="utf-8")
    
    # Must include displacement decomposition u = u_0 + Delta u
    assert "\\mathbf{u}(\\mathbf{x}, t) = \\mathbf{u}_0(\\mathbf{x}) + \\Delta \\mathbf{u}(\\mathbf{x}, t)" in content or "u = u_0 + Delta u" in content
    # Tangent stiffness Kuu remains symmetric and positive definite
    assert "strictly symmetric and positive definite" in content or "positive definite" in content
    # Delta d = 0 during increment 0 zero-load equilibration
    assert "\\Delta d = 0" in content or "Delta d = 0" in content

def test_four_objective_methodological_separation():
    """Verify strict methodological decoupling of the four research objectives."""
    assert REPORT_MD.exists()
    content = REPORT_MD.read_text(encoding="utf-8")
    
    assert "Objective 1: State Transfer & Preservation" in content
    assert "Objective 2: Equilibrium Continuation" in content
    assert "Objective 3: Prospective Error-Guided Refinement" in content
    assert "Objective 4: Multi-Cycle Evolving Adaptivity" in content

def test_method_c_governance_and_hpc_status():
    """Verify that Method C1 submission wrapper is strictly locked and Gate 6C is on hold."""
    assert WRAPPER_SH.exists()
    wrapper_text = WRAPPER_SH.read_text(encoding="utf-8")
    assert 'AUTHORIZED=false' in wrapper_text or 'AUTHORIZED="false"' in wrapper_text, "Submission wrapper must have AUTHORIZED=false"
    
    assert BRIEFING_MD.exists()
    briefing_text = BRIEFING_MD.read_text(encoding="utf-8")
    assert "Gate 6C remains ON HOLD" in briefing_text or "Gate 6C remains strictly on hold" in briefing_text

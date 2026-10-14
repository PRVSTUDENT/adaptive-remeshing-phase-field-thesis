import hashlib
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
VALIDATION_REPORT = REPO_ROOT / "docs" / "reports" / "MODE1_METHOD_C_CONTINUATION_ARCHITECTURE_VALIDATION.md"
SUPERVISOR_BRIEFING = REPO_ROOT / "docs" / "supervisor_reports" / "22-10-2026" / "SUPERVISOR_BRIEFING_MODE1_METHODS_B_AND_C.md"
PRODUCTION_UEL = REPO_ROOT / "models" / "pandey_kumar_mode1" / "f42_mixed_uel.for"
EXPECTED_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"


def test_f1459_tangent_definiteness_disambiguation():
    """Verify that validation report clearly distinguishes fixed-damage tangent from coupled softening tangent."""
    assert VALIDATION_REPORT.exists(), f"Missing report: {VALIDATION_REPORT}"
    content = VALIDATION_REPORT.read_text(encoding="utf-8")
    
    assert "Fixed-Damage Mechanical Tangent Operator" in content or "\\mathbf{K}_{uu}" in content
    assert "positive definite" in content.lower()
    assert "\\mathbf{K}_{\\text{coupled}}" in content or "Coupled Damage-Evolution Tangent" in content
    assert "negative eigenvalues" in content.lower()


def test_f1459_nonmatching_projection_residual_calculation():
    """Verify that nonmatching projection residual is quantitatively estimated and zero displacement disambiguated."""
    content = VALIDATION_REPORT.read_text(encoding="utf-8")
    
    assert "Quantitative Calculation for Candidate Transfer" in content or "\\mathcal{O}(10" in content or "10 - 15 N" in content
    assert "2,906" in content and "14,677" in content
    assert "1.64%" in content or "1.67%" in content or "compliance disparity" in content.lower()
    assert "Zero Prescribed Incremental Displacement" in content
    assert "Non-Zero Transfer-Induced Internal Residual" in content
    assert "Boundary Reaction-Force Discontinuity" in content


def test_f1459_c1_acceptance_metrics_and_coordinates():
    """Verify that C1 acceptance criteria require common physical coordinates, 8 fields, and stage separation."""
    content = VALIDATION_REPORT.read_text(encoding="utf-8")
    
    assert "common physical coordinates" in content.lower()
    # Check for fields
    assert "displacement" in content.lower()
    assert "phase-field damage" in content.lower()
    assert "history" in content.lower()
    assert "residual" in content.lower()
    assert "fracture surface energy" in content.lower()
    assert "elastic energy" in content.lower()
    
    # Check stage separation
    assert "Stage C1-A" in content
    assert "Stage C1-B" in content
    
    # Check incomplete bookkeeping warning
    assert "incomplete" in content.lower() and "bookkeeping" in content.lower()


def test_f1459_c2_criteria_and_wake_coarsening_prerequisites():
    """Verify that C2 criteria include 1D surrogate derivation, 2D reduction factor, and mandatory wake measurements."""
    content = VALIDATION_REPORT.read_text(encoding="utf-8")
    
    assert "\\coth" in content or "coth" in content
    assert "1D exponential decay" in content or "1D surrogate" in content
    assert "spatial averaging" in content.lower()
    
    # Mandatory wake measurements
    assert "crack opening displacement" in content.lower() or "COD" in content
    assert "bending compliance" in content.lower()
    assert "surface energy" in content.lower()


def test_f1459_smallest_c1_experiment_specification():
    """Verify smallest C1 experiment specification with 4-step sequence and solver hold."""
    content = VALIDATION_REPORT.read_text(encoding="utf-8")
    
    assert "Smallest C1 Experiment Specification" in content
    assert "Step 1: Offline Transfer Verification" in content
    assert "Step 2: Abaqus Datacheck" in content
    assert "Step 3: Single-Increment Equilibrium Solve" in content
    assert "Step 4: Short Forward Solve" in content
    assert "None of these solver steps are executed" in content or "pending supervisor" in content.lower()


def test_f1459_supervisor_briefing_and_decisions():
    """Verify supervisor briefing structure, 3 decisions, and PBS authorization guard."""
    assert SUPERVISOR_BRIEFING.exists(), f"Missing briefing: {SUPERVISOR_BRIEFING}"
    briefing = SUPERVISOR_BRIEFING.read_text(encoding="utf-8")
    
    # Check sequence
    assert "Problem Definition" in briefing
    assert "Expected Solution" in briefing or "Expected Physical Response" in briefing
    assert "Fixed-Mesh Reference Anchor" in briefing
    assert "Method B" in briefing
    assert "Method C" in briefing
    
    # Check formal decisions
    assert "Decision 1: Formal Sign-Off of Gate 6B" in briefing or "Formal Closure of Gate 6B" in briefing
    assert "Decision 2: Formal Governance Evaluation of Gate 6C" in briefing or "Formal Evaluation of Gate 6C" in briefing
    assert "Decision 3: Strategic Thesis Path Forward" in briefing
    
    # Check PBS permission guard
    assert "General PBS permission does NOT authorize" in briefing or "General PBS script presence do not constitute" in briefing or "Zero new solver jobs" in briefing


def test_f1459_traceable_evidence_matrix_schema():
    """Verify explicit evidence matrix schema and populated records."""
    briefing = SUPERVISOR_BRIEFING.read_text(encoding="utf-8")
    report = VALIDATION_REPORT.read_text(encoding="utf-8")
    
    for doc in [briefing, report]:
        assert "TRACEABLE EPISTEMIC EVIDENCE MATRIX" in doc
        assert "Evidence ID" in doc or "Evidence_ID" in doc
        assert "Epistemic Tier" in doc
        assert "Claim Statement" in doc
        assert "EVD-M1-001" in doc
        assert "EVD-M1-017" in doc


def test_f1459_provenance_and_frozen_uel():
    """Verify production UEL hash integrity."""
    assert PRODUCTION_UEL.exists(), f"Production UEL missing: {PRODUCTION_UEL}"
    sha256 = hashlib.sha256(PRODUCTION_UEL.read_bytes()).hexdigest().upper()
    assert sha256 == EXPECTED_UEL_HASH, f"UEL modified! Expected {EXPECTED_UEL_HASH}, got {sha256}"

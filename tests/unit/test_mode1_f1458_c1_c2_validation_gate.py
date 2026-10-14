"""Unit test suite for Task F1458: Correct Method C Scientific Claims and
Establish a Defensible C1-to-C2 Validation Gate.

Verifies:
1. Operational definition of Gate C1 (6 criteria) and Gate C2 (5 criteria) with
   explicit formulas, thresholds, and falsification conditions.
2. Mathematical reassessment of tangent definiteness (softening and negative eigenvalues)
   and strict distinction between zero prescribed displacement, non-zero transfer residual,
   and reaction force discontinuity.
3. Physical classification of the three material regimes in Method C2 (Intact Bulk,
   Active FPZ, Fully Fractured Wake) and documentation of wake coarsening pitfalls.
4. Demotion of the C2 resolution bound from a "theorem" to a candidate engineering guideline.
5. Existence of the standardized evidence-reporting template.
6. Supervisor briefing Section 4.5 integration and Gate 6C ON HOLD status reconciliation.
7. Uncompromised SHA-256 hash integrity of frozen production UEL f42_mixed_uel.for.
"""

import hashlib
import os
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

VALIDATION_REPORT_PATH = os.path.join(
    REPO_ROOT, "docs", "reports", "MODE1_METHOD_C_CONTINUATION_ARCHITECTURE_VALIDATION.md"
)
SUPERVISOR_BRIEFING_PATH = os.path.join(
    REPO_ROOT, "docs", "supervisor_reports", "22-10-2026", "SUPERVISOR_BRIEFING_MODE1_METHODS_B_AND_C.md"
)
PRODUCTION_UEL_PATH = os.path.join(
    REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for"
)

FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"


def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()


def test_f1458_c1_c2_operational_gates_definition():
    """Verify that Gate C1 and Gate C2 are operationalized with exact criteria, thresholds, and falsification rules."""
    assert os.path.isfile(VALIDATION_REPORT_PATH)

    with open(VALIDATION_REPORT_PATH, "r", encoding="utf-8") as f:
        text = f.read()

    # Gate C1 checks
    assert "GATE C1: OPERATIONAL ACCEPTANCE CRITERIA" in text
    assert "C1-1" in text
    assert "C1-2" in text
    assert "C1-3" in text
    assert "C1-4" in text
    assert "C1-5" in text
    assert "C1-6" in text
    assert "<= 5.0 N" in text
    assert "<= 5.0%" in text
    assert "<= 10.0%" in text
    assert ">=-1.0e-6" in text or ">= -1.0e-6" in text

    # Gate C2 checks
    assert "GATE C2: OPERATIONAL ACCEPTANCE CRITERIA" in text
    assert "C2-1" in text
    assert "C2-2" in text
    assert "C2-3" in text
    assert "C2-4" in text
    assert "C2-5" in text
    assert "activated **only after Gate C1 achieves formal PASS**" in text or "only after Gate C1" in text.lower()


def test_f1458_reassessment_of_tangent_definiteness():
    """Verify that tangent definiteness is reassessed and the three zero quantities are distinguished."""
    with open(VALIDATION_REPORT_PATH, "r", encoding="utf-8") as f:
        text = f.read()

    # Reassessment of tangent definiteness under softening
    assert "negative eigenvalues" in text.lower()
    assert "positive definite" in text.lower()
    assert "softening" in text.lower()

    # Three zero quantities
    assert "Zero Prescribed Incremental Displacement" in text
    assert "Transfer-Induced Internal Residual" in text
    assert "Boundary Reaction-Force Discontinuity" in text
    assert "rho_transfer" in text or "\\boldsymbol{\\rho}_{\\text{transfer}}" in text


def test_f1458_wake_coarsening_pitfalls_and_regimes():
    """Verify that the three material regimes and wake coarsening hazards are comprehensively analyzed."""
    with open(VALIDATION_REPORT_PATH, "r", encoding="utf-8") as f:
        text = f.read()

    # Three material regimes
    assert "THREE MATERIAL REGIMES IN METHOD C2" in text
    assert "Intact Far Field" in text
    assert "Active FPZ" in text
    assert "Fully Fractured Wake" in text

    # Wake hazards
    assert "Crack Opening Displacement" in text or "COD" in text
    assert "compliance" in text.lower()
    assert "bridging" in text.lower()
    assert "quadrature" in text.lower()

    # Trajectory-agnostic requirement
    assert "Trajectory-Agnostic" in text
    assert "never hardcode a geometric crack path" in text or "never hardcode" in text


def test_f1458_c2_resolution_guideline_demotion():
    """Verify that the resolution bound is framed as an engineering guideline, not a theorem."""
    with open(VALIDATION_REPORT_PATH, "r", encoding="utf-8") as f:
        text = f.read()

    assert "Candidate Mesh-Resolution Guideline" in text or "candidate engineering resolution guideline" in text
    assert "theorem" in text.lower()
    # Ensure it's not asserted as an absolute universal theorem
    assert "not a universal mathematical theorem" in text or "not a mathematical theorem" in text.lower()

    # Dimensional distinction
    assert "1D surrogate" in text or "surrogate" in text
    assert "53.25%" in text
    assert "5.0465%" in text


def test_f1458_evidence_reporting_template_exists():
    """Verify that the standardized evidence-reporting template is provided."""
    with open(VALIDATION_REPORT_PATH, "r", encoding="utf-8") as f:
        text = f.read()

    assert "Standardized Evidence-Reporting Template" in text
    assert "Method C Solver Execution Telemetry & Evidence Summary" in text
    assert "Cutback Diagnostics" in text
    assert "Boundary Reaction Continuity" in text
    assert "UEL Energy Balance Tracking" in text


def test_f1458_supervisor_briefing_section_4_5():
    """Verify that Section 4.5 is present in the supervisor briefing and Gate 6C is on hold."""
    with open(SUPERVISOR_BRIEFING_PATH, "r", encoding="utf-8") as f:
        text = f.read()

    assert "4.5 Technical Note: Defensible Progressive Progression from Gate C1 to Gate C2" in text
    assert "Gate C1 (Forward-Refinement Continuation Validation)" in text
    assert "Gate C2 (Selective Crack-Wake Coarsening Validation)" in text
    assert "Gate 6C remains ON HOLD PENDING SUPERVISOR REVIEW" in text


def test_f1458_provenance_and_frozen_uel():
    """Verify that production UEL f42_mixed_uel.for remains strictly frozen."""
    assert os.path.isfile(PRODUCTION_UEL_PATH)
    assert compute_sha256(PRODUCTION_UEL_PATH) == FROZEN_UEL_HASH
